from __future__ import annotations

import io
import os
import time
import zipfile
from collections.abc import Generator
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

import main
from db.base import Base
from db.models import Artifact, Project, Task, TenantMembership, Workspace
from db.session import get_db
from services.file_lifecycle import delete_candidates, find_orphan_files
from services.task_worker import TaskWorker


def valid_docx_bytes() -> bytes:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("word/document.xml", "<w:document/>")
    return stream.getvalue()


@pytest.fixture
def day16_client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Generator[tuple[TestClient, sessionmaker[Session]], None, None]:
    monkeypatch.setenv("AUTH_REQUIRED", "true")
    monkeypatch.setenv("AUTO_CREATE_DB", "false")
    engine = create_engine(f"sqlite:///{(tmp_path / 'day16.db').as_posix()}")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override() -> Generator[Session, None, None]:
        db = sessions()
        try:
            yield db
        finally:
            db.close()

    monkeypatch.setattr(main, "UPLOAD_DIR", tmp_path / "uploads")
    main.UPLOAD_DIR.mkdir()
    main.app.dependency_overrides[get_db] = override
    monkeypatch.setattr(main, "SessionLocal", sessions)
    worker = TaskWorker()
    monkeypatch.setattr(main, "task_worker", worker)
    with TestClient(main.app) as client:
        try:
            yield client, sessions
        finally:
            worker.shutdown()
    main.app.dependency_overrides.clear()
    engine.dispose()


def register(client: TestClient, email: str) -> dict[str, object]:
    response = client.post("/auth/register", json={"email": email, "password": "password123"})
    assert response.status_code == 201, response.text
    return response.json()


def auth(payload: dict[str, object]) -> dict[str, str]:
    return {"Authorization": f"Bearer {payload['access_token']}"}


def test_classification_upload_is_removed_after_request(day16_client: tuple[TestClient, sessionmaker[Session]], monkeypatch: pytest.MonkeyPatch) -> None:
    client, _ = day16_client
    owner = register(client, "day16-classify@example.com")
    observed: list[Path] = []

    def fake_classify(path: Path) -> dict[str, object]:
        observed.append(path)
        return {"document_type": "academic_paper"}

    monkeypatch.setattr(main, "classify_document", fake_classify)
    response = client.post("/document/classify", headers=auth(owner), files={"paper": ("paper.docx", valid_docx_bytes(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")})
    assert response.status_code == 200
    assert observed and not observed[0].exists()


def test_retry_requeues_failed_task_and_detail_explains_status(day16_client: tuple[TestClient, sessionmaker[Session]], monkeypatch: pytest.MonkeyPatch) -> None:
    client, sessions = day16_client
    owner = register(client, "day16-retry@example.com")
    submitted: list[tuple[object, ...]] = []
    monkeypatch.setattr(main.task_worker, "submit", lambda *args, **kwargs: submitted.append(args))
    created = client.post("/tasks", headers=auth(owner), files={"paper": ("paper.docx", valid_docx_bytes(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}, data={"mode": "local", "allow_non_paper": "true"})
    assert created.status_code == 201
    task_id = created.json()["task_id"]
    db = sessions()
    try:
        task = db.get(Task, task_id)
        assert task is not None
        task.status = "interrupted"
        task.workflow_stage = "interrupted"
        task.error_code = "backend_restart"
        task.error_message = "backend restart"
        db.commit()
    finally:
        db.close()

    detail = client.get(f"/tasks/{task_id}", headers=auth(owner))
    assert detail.status_code == 200
    assert detail.json()["retry_available"] is True
    assert "重启" in detail.json()["status_explanation"]
    response = client.post(f"/tasks/{task_id}/retry", headers=auth(owner))
    assert response.status_code == 200, response.text
    assert response.json()["retry_started"] is True
    assert submitted
    db = sessions()
    try:
        task = db.get(Task, task_id)
        assert task is not None and task.status == "pending"
        assert task.recovery_metadata["previous_status"] == "interrupted"
    finally:
        db.close()


def test_task_detail_exposes_verification_summary(day16_client: tuple[TestClient, sessionmaker[Session]], monkeypatch: pytest.MonkeyPatch) -> None:
    client, _ = day16_client
    owner = register(client, "day16-verification@example.com")
    monkeypatch.setattr(main, "run_agent_pipeline", lambda **_: {"status": "ok", "after_score": 91.0, "verification": {"verification_summary": {"total": 3, "verified": 2, "failed": 0, "unsupported": 1}}})
    created = client.post("/tasks", headers=auth(owner), files={"paper": ("paper.docx", valid_docx_bytes(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}, data={"mode": "local", "allow_non_paper": "true"})
    assert created.status_code == 201
    task_id = created.json()["task_id"]
    for _ in range(20):
        detail = client.get(f"/tasks/{task_id}", headers=auth(owner))
        if detail.json().get("status") == "completed":
            break
        time.sleep(0.05)
    assert detail.json()["verification_summary"] == {"total": 3, "verified": 2, "failed": 0, "unsupported": 1}


def test_artifact_download_requires_bearer_and_task_detail_keeps_old_rows_compatible(day16_client: tuple[TestClient, sessionmaker[Session]], tmp_path: Path) -> None:
    client, sessions = day16_client
    owner = register(client, "day16-artifact@example.com")
    db = sessions()
    artifact_path = tmp_path / "result.docx"
    artifact_path.write_bytes(b"docx-result")
    try:
        membership = db.scalar(select(TenantMembership).where(TenantMembership.user_id == owner["user"]["id"]))
        assert membership is not None
        project = db.scalar(select(Project).where(Project.workspace_id == owner["workspace_id"]))
        if project is None:
            project = Project(workspace_id=owner["workspace_id"], title="Day16")
            db.add(project)
            db.flush()
        task = Task(project_id=project.id, tenant_id=membership.tenant_id, user_id=membership.user_id, status="completed", uploaded_file=None, result_metadata={})
        task.artifacts.append(Artifact(file_path=str(artifact_path), file_type="docx"))
        db.add(task)
        db.commit()
        task_id = task.id
        artifact_id = task.artifacts[0].id
    finally:
        db.close()

    assert client.get(f"/artifacts/{artifact_id}/download").status_code == 401
    response = client.get(f"/artifacts/{artifact_id}/download", headers=auth(owner))
    assert response.status_code == 200
    detail = client.get(f"/tasks/{task_id}", headers=auth(owner))
    assert detail.status_code == 200
    assert detail.json()["verification_summary"] is None


def test_orphan_cleanup_is_dry_run_by_default_and_never_removes_formal_artifact(tmp_path: Path) -> None:
    engine = create_engine(f"sqlite:///{(tmp_path / 'files.db').as_posix()}")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    db = sessions()
    try:
        root = tmp_path / "outputs"
        root.mkdir()
        formal = root / "formal.docx"
        orphan = root / "orphan.tmp"
        formal.write_bytes(b"formal")
        orphan.write_bytes(b"orphan")
        old = (datetime.now(timezone.utc) - timedelta(days=5)).timestamp()
        os.utime(formal, (old, old))
        os.utime(orphan, (old, old))
        # A minimal artifact row is enough to mark the formal result protected.
        from db.models import Project, Tenant, TenantMembership, User, Workspace

        user = User(email="cleanup@example.com", password_hash="hash")
        tenant = Tenant(name="Cleanup", slug="cleanup")
        membership = TenantMembership(tenant=tenant, user=user, role="owner", status="active")
        workspace = Workspace(owner=user, name="Cleanup")
        project = Project(workspace=workspace, title="Cleanup")
        task = Task(project=project, tenant=tenant, user=user, status="completed")
        task.artifacts.append(Artifact(file_path=str(formal), file_type="docx"))
        db.add_all([membership, workspace, project, task])
        db.commit()
        candidates = find_orphan_files(db, roots=[root], older_than_days=1)
        assert [item.path for item in candidates] == [orphan.resolve()]
        assert orphan.exists()
        assert formal.exists()
        assert delete_candidates(candidates) == 1
        assert not orphan.exists()
        assert formal.exists()
    finally:
        db.close()
        engine.dispose()
