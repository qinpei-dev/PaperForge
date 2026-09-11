from __future__ import annotations

import io
import zipfile
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

import db.session as db_session
import main
from db.base import Base
from db.models import Project, Quota, Task, Tenant, User, Workspace
from services.concurrency import TaskConcurrencyExceededError, check_task_concurrency
from services.rate_limit import reset_rate_limits


def valid_docx_bytes() -> bytes:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("word/document.xml", "<w:document/>")
    return stream.getvalue()


@pytest.fixture
def concurrency_db(tmp_path: Path) -> Generator[sessionmaker[Session], None, None]:
    engine = create_engine(f"sqlite:///{(tmp_path / 'day15.db').as_posix()}")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    db = sessions()
    try:
        tenant = Tenant(name="Day15 tenant", slug="day15-tenant")
        user = User(email="day15@example.com", password_hash="hash")
        db.add_all([tenant, user])
        db.flush()
        workspace = Workspace(owner_id=user.id, name="Day15 workspace")
        db.add(workspace)
        db.flush()
        db.add(Project(workspace_id=workspace.id, title="Day15 project"))
        db.add(Quota(tenant_id=tenant.id, monthly_limit=100))
        db.commit()
        yield sessions
    finally:
        db.close()
        engine.dispose()


def _seed_task(sessions: sessionmaker[Session], *, status: str = "running") -> tuple[str, str]:
    db = sessions()
    try:
        tenant = db.scalar(select(Tenant))
        user = db.scalar(select(User))
        project = db.scalar(select(Project))
        assert tenant and user and project
        db.add(Task(project_id=project.id, tenant_id=tenant.id, user_id=user.id, status=status, paper_name="paper.docx"))
        db.commit()
        return tenant.id, user.id
    finally:
        db.close()


def test_task_concurrency_is_enforced_per_user_and_tenant(concurrency_db: sessionmaker[Session], monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAX_ACTIVE_TASKS_PER_USER", "1")
    monkeypatch.setenv("MAX_ACTIVE_TASKS_PER_TENANT", "4")
    tenant_id, user_id = _seed_task(concurrency_db)
    db = concurrency_db()
    try:
        with pytest.raises(TaskConcurrencyExceededError) as error:
            check_task_concurrency(db, tenant_id, user_id)
        assert error.value.scope == "user"
        assert error.value.snapshot.user_active == 1
    finally:
        db.rollback()
        db.close()

    monkeypatch.setenv("MAX_ACTIVE_TASKS_PER_USER", "4")
    monkeypatch.setenv("MAX_ACTIVE_TASKS_PER_TENANT", "1")
    db = concurrency_db()
    try:
        with pytest.raises(TaskConcurrencyExceededError) as error:
            check_task_concurrency(db, tenant_id, user_id)
        assert error.value.scope == "tenant"
        assert error.value.snapshot.tenant_active == 1
    finally:
        db.rollback()
        db.close()


def test_global_api_rate_limit_protects_non_health_routes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_RATE_LIMIT_PER_MINUTE", "1")
    reset_rate_limits()
    client = TestClient(main.app)
    assert client.get("/health").status_code == 200
    assert client.get("/openapi.json").status_code == 200
    limited = client.get("/openapi.json")
    assert limited.status_code == 429
    assert limited.headers.get("Retry-After")
    reset_rate_limits()


def test_upload_rejects_duplicate_or_high_expansion_archive(monkeypatch: pytest.MonkeyPatch) -> None:
    duplicate = io.BytesIO()
    with zipfile.ZipFile(duplicate, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("word/document.xml", "<w:document/>")
    with pytest.raises(HTTPException) as duplicate_error:
        main.validate_docx_upload(
            main.UploadFile(filename="duplicate.docx", file=io.BytesIO(duplicate.getvalue())),
            maximum_size=main.MAX_UPLOAD_BYTES,
            label="论文",
        )
    assert duplicate_error.value.status_code == 422

    expanded = io.BytesIO()
    with zipfile.ZipFile(expanded, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("word/document.xml", "<w:document/>")
        archive.writestr("customXml/item.xml", "x" * 10000)
    monkeypatch.setattr(main, "MAX_DOCX_COMPRESSION_RATIO", 2.0)
    with pytest.raises(HTTPException) as expansion_error:
        main.validate_docx_upload(
            main.UploadFile(filename="bomb.docx", file=io.BytesIO(expanded.getvalue())),
            maximum_size=main.MAX_UPLOAD_BYTES,
            label="论文",
        )
    assert expansion_error.value.status_code == 422


def test_request_body_limit_is_enforced_before_route(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(main, "MAX_REQUEST_BODY_BYTES", 1)
    reset_rate_limits()
    response = TestClient(main.app).post("/openapi.json", content=b"too-large")
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    reset_rate_limits()


def test_db_dependency_rolls_back_on_request_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    engine = create_engine(f"sqlite:///{(tmp_path / 'rollback.db').as_posix()}")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    monkeypatch.setattr(db_session, "SessionLocal", sessions)
    generator = db_session.get_db()
    db = next(generator)
    db.add(User(email="rollback@example.com", password_hash="hash"))
    with pytest.raises(RuntimeError):
        generator.throw(RuntimeError("request failed"))
    check = sessions()
    try:
        assert check.scalar(select(User).where(User.email == "rollback@example.com")) is None
    finally:
        check.close()
        engine.dispose()


def test_production_files_wire_hardening_defaults() -> None:
    compose = Path("../../docker-compose.prod.yml").read_text(encoding="utf-8")
    assert 'AUTO_CREATE_DB: "false"' in compose
    assert "MAX_ACTIVE_TASKS_PER_TENANT" in compose
    assert Path("../../scripts/production_smoke_test.py").is_file()
    assert Path("../../scripts/verify_postgres_backup.ps1").is_file()
    assert Path("../../scripts/backup_files.ps1").is_file()
    assert Path("../../scripts/restore_files.ps1").is_file()
