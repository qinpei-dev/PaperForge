from __future__ import annotations

import json
import io
import time
import zipfile
from collections.abc import Generator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from auth import create_access_token
from db.base import Base
from db.models import Task, Template, Tenant, TenantMembership, User
from db.session import get_db
from main import app
from services.agent_pipeline import run_agent_pipeline
from services.task_worker import TaskWorker
from services.template_persistence import refresh_template_registry
from services.template_registry import BUILTIN_TEMPLATE_DEFINITIONS, TemplateNotFoundError, template_registry
from services.template_repository import TemplateRepository
from services.tenant_context import resolve_tenant_context


def valid_docx_bytes() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("word/document.xml", "<w:document/>")
    return buffer.getvalue()


@pytest.fixture(autouse=True)
def reset_registry() -> Generator[None, None, None]:
    template_registry.replace(BUILTIN_TEMPLATE_DEFINITIONS)
    yield
    template_registry.replace(BUILTIN_TEMPLATE_DEFINITIONS)


@pytest.fixture
def tenant_client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Generator[tuple[TestClient, sessionmaker[Session]], None, None]:
    monkeypatch.setenv("AUTH_REQUIRED", "true")
    monkeypatch.setenv("AUTO_CREATE_DB", "false")
    engine = create_engine(f"sqlite:///{(tmp_path / 'tenant-api.db').as_posix()}")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_get_db() -> Generator[Session, None, None]:
        db = sessions()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr("main.SessionLocal", sessions)
    worker = TaskWorker()
    monkeypatch.setattr("main.task_worker", worker)
    with TestClient(app) as client:
        try:
            yield client, sessions
        finally:
            worker.shutdown()
    app.dependency_overrides.clear()
    engine.dispose()


def register(client: TestClient, email: str) -> dict[str, object]:
    response = client.post("/auth/register", json={"email": email, "password": "password123"})
    assert response.status_code == 201, response.text
    return response.json()


def auth(payload: dict[str, object]) -> dict[str, str]:
    return {"Authorization": f"Bearer {payload['access_token']}"}


def membership_for(sessions: sessionmaker[Session], payload: dict[str, object]) -> TenantMembership:
    db = sessions()
    try:
        membership = db.scalar(select(TenantMembership).where(TenantMembership.user_id == payload["user"]["id"]))
        assert membership is not None
        db.expunge(membership)
        return membership
    finally:
        db.close()


def add_template(sessions: sessionmaker[Session], tenant_id: str, *, template_id: str = "shared-custom", version: str = "1.0") -> None:
    db = sessions()
    TemplateRepository(db).create(
        template_id=template_id,
        version=version,
        name="Tenant Custom",
        school="Tenant School",
        document_type="academic_paper",
        status="active",
        source="test",
        template_path=None,
        metadata={"custom": True},
        scope="tenant",
        tenant_id=tenant_id,
    )
    db.commit()
    refresh_template_registry(db)
    db.close()


def test_tenant_membership_constraints_and_disabled_context(tenant_client) -> None:
    client, sessions = tenant_client
    account = register(client, "tenant-model@example.com")
    membership = membership_for(sessions, account)
    db = sessions()
    assert db.get(Tenant, membership.tenant_id) is not None
    assert len(db.scalars(select(TenantMembership).where(TenantMembership.user_id == membership.user_id)).all()) == 1
    db.add(Tenant(name="Duplicate slug", slug=db.get(Tenant, membership.tenant_id).slug, status="active"))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()
    db.add(TenantMembership(tenant_id=membership.tenant_id, user_id=membership.user_id, role="member", status="active"))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()
    tenant = db.get(Tenant, membership.tenant_id)
    tenant.status = "disabled"
    db.commit()
    db.close()
    assert client.get("/tasks", headers=auth(account)).status_code == 403


def test_user_can_have_multiple_memberships_but_personal_context_is_stable(tenant_client) -> None:
    client, sessions = tenant_client
    account = register(client, "multi-tenant@example.com")
    personal = membership_for(sessions, account)
    db = sessions()
    extra = Tenant(name="Extra", slug="extra-tenant", status="active")
    db.add(extra)
    db.flush()
    db.add(TenantMembership(tenant_id=extra.id, user_id=personal.user_id, role="member", status="active"))
    db.commit()
    user = db.get(User, personal.user_id)
    assert user is not None and len(user.tenant_memberships) == 2
    assert resolve_tenant_context(db, user).tenant_id == personal.tenant_id
    db.close()


def test_template_repository_and_registry_isolate_tenants(tenant_client) -> None:
    client, sessions = tenant_client
    tenant_a = register(client, "template-a@example.com")
    tenant_b = register(client, "template-b@example.com")
    membership_a = membership_for(sessions, tenant_a)
    membership_b = membership_for(sessions, tenant_b)
    add_template(sessions, membership_a.tenant_id)
    add_template(sessions, membership_b.tenant_id)

    db = sessions()
    repository = TemplateRepository(db)
    visible_a = repository.list_visible(membership_a.tenant_id, status="active")
    visible_b = repository.list_visible(membership_b.tenant_id, status="active")
    assert any(item.scope == "platform" for item in visible_a)
    assert any(item.scope == "platform" for item in visible_b)
    assert all(item.scope == "platform" or item.tenant_id == membership_a.tenant_id for item in visible_a)
    assert all(item.scope == "platform" or item.tenant_id == membership_b.tenant_id for item in visible_b)
    assert template_registry.resolve(template_id="shared-custom", version="1.0", tenant_id=membership_a.tenant_id).definition.tenant_id == membership_a.tenant_id
    with pytest.raises(TemplateNotFoundError):
        template_registry.resolve(template_id="shared-custom", version="1.0", tenant_id="unknown-tenant")
    with pytest.raises(IntegrityError):
        repository.create(template_id="shared-custom", version="1.0", name="Duplicate", school="X", document_type="academic_paper", status="active", source="test", template_path=None, metadata={}, scope="tenant", tenant_id=membership_a.tenant_id)
        db.commit()
    db.rollback()
    db.close()


def test_templates_api_and_task_template_resolution_are_tenant_aware(tenant_client, monkeypatch: pytest.MonkeyPatch) -> None:
    client, sessions = tenant_client
    tenant_a = register(client, "api-a@example.com")
    tenant_b = register(client, "api-b@example.com")
    membership_a = membership_for(sessions, tenant_a)
    membership_b = membership_for(sessions, tenant_b)
    add_template(sessions, membership_a.tenant_id, template_id="a-private")

    ids_a = {item["template_id"] for item in client.get("/templates", headers=auth(tenant_a)).json()["templates"]}
    ids_b = {item["template_id"] for item in client.get("/templates", headers=auth(tenant_b)).json()["templates"]}
    anonymous = client.get("/templates").json()["templates"]
    assert "a-private" in ids_a and "a-private" not in ids_b
    assert all(item["scope"] == "platform" and item["tenant_id"] is None for item in anonymous)

    monkeypatch.setattr("main.run_agent_pipeline", lambda **_: {"status": "ok", "agent_trace": []})
    files = {"paper": ("paper.docx", valid_docx_bytes(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    private_request = {"mode": "local", "allow_non_paper": "true", "template_id": "a-private", "template_version": "1.0"}
    assert client.post("/tasks", headers=auth(tenant_b), files=files, data=private_request).status_code == 404
    platform_request = {"mode": "local", "allow_non_paper": "true", "template_id": "paperforge-general-academic", "template_version": "2026.1"}
    assert client.post("/tasks", headers=auth(tenant_b), files=files, data=platform_request).status_code == 201
    assert membership_a.tenant_id != membership_b.tenant_id


def test_task_detail_sse_and_result_are_tenant_isolated(tenant_client, monkeypatch: pytest.MonkeyPatch) -> None:
    client, sessions = tenant_client
    tenant_a = register(client, "task-tenant-a@example.com")
    tenant_b = register(client, "task-tenant-b@example.com")

    def fake_pipeline(**kwargs: object) -> dict[str, object]:
        output = Path(kwargs["output_dir"]) / "tenant-result.docx"
        output.write_bytes(b"result")
        return {"status": "ok", "filename": output.name, "after_score": 90.0, "agent_trace": [], "modification_report": {"summary": "ok"}}

    monkeypatch.setattr("main.run_agent_pipeline", fake_pipeline)
    response = client.post("/tasks", headers=auth(tenant_a), files={"paper": ("paper.docx", valid_docx_bytes(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}, data={"mode": "local", "allow_non_paper": "true"})
    assert response.status_code == 201
    task_id = response.json()["task_id"]
    detail = None
    for _ in range(40):
        detail = client.get(f"/tasks/{task_id}", headers=auth(tenant_a))
        if detail.json().get("status") == "completed":
            break
        time.sleep(0.025)
    assert detail is not None and detail.status_code == 200
    body = detail.json()
    membership_a = membership_for(sessions, tenant_a)
    assert body["tenant_id"] == membership_a.tenant_id
    assert body["user_id"] == tenant_a["user"]["id"]
    artifact = next(item for item in body["artifacts"] if item["file_type"] == "docx")
    assert client.get(f"/tasks/{task_id}", headers=auth(tenant_b)).status_code == 404
    assert client.get(f"/tasks/{task_id}/events", headers=auth(tenant_b)).status_code == 404
    assert client.get(artifact["download_url"], headers=auth(tenant_b)).status_code == 404
    assert client.get("/download/tenant-result.docx", headers=auth(tenant_b)).status_code == 404
    assert client.get("/download/tenant-result.docx").status_code == 401


def test_task_state_records_tenant_user_and_template_provenance(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paper = tmp_path / "paper.docx"
    paper.write_bytes(b"paper")
    output = tmp_path / "outputs"
    output.mkdir()
    monkeypatch.setattr("services.agent_pipeline.run_paper_agent", lambda **_: {"status": "ok", "steps": []})
    result = run_agent_pipeline(paper, output, mode="local", tenant_id="tenant-provenance", user_id="user-provenance")
    state = json.loads(Path(result["task_state_path"]).read_text(encoding="utf-8"))
    assert state["tenant_id"] == "tenant-provenance"
    assert state["user_id"] == "user-provenance"
    assert state["template"]["id"] == "paperforge-general-academic"
    assert state["template"]["scope"] == "platform"


def test_0004_to_0007_migration_backfills_without_changing_template_identity(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    database = tmp_path / "migration.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database.as_posix()}")
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", f"sqlite:///{database.as_posix()}")
    command.upgrade(config, "0004_day9_template_persistence")
    engine = create_engine(f"sqlite:///{database.as_posix()}")
    with engine.begin() as connection:
        connection.execute(text("INSERT INTO users (id, email, password_hash) VALUES ('user-1', 'legacy@example.com', 'hash')"))
        connection.execute(text("INSERT INTO workspaces (id, owner_id, name) VALUES ('workspace-1', 'user-1', 'Legacy')"))
        connection.execute(text("INSERT INTO projects (id, workspace_id, title, status) VALUES ('project-1', 'workspace-1', 'Legacy', 'active')"))
        connection.execute(text("INSERT INTO tasks (id, project_id, status) VALUES ('task-1', 'project-1', 'completed')"))
        for index, definition in enumerate(BUILTIN_TEMPLATE_DEFINITIONS):
            connection.execute(
                text("INSERT INTO templates (id, template_id, version, name, school, document_type, status, source, template_path, metadata) VALUES (:id, :template_id, :version, :name, :school, :document_type, :status, :source, :template_path, :metadata)"),
                {"id": f"template-{index}", "template_id": definition.template_id, "version": definition.version, "name": definition.name, "school": definition.school, "document_type": definition.document_type, "status": definition.status, "source": definition.source, "template_path": str(definition.template_path) if definition.template_path else None, "metadata": json.dumps(definition.metadata)},
            )
    command.upgrade(config, "0007_day10_membership_rbac")
    with engine.connect() as connection:
        templates = connection.execute(text("SELECT template_id, version, scope, tenant_id FROM templates ORDER BY id")).mappings().all()
        assert {(item["template_id"], item["version"]) for item in templates} == {(item.template_id, item.version) for item in BUILTIN_TEMPLATE_DEFINITIONS}
        assert all(item["scope"] == "platform" and item["tenant_id"] is None for item in templates)
        membership = connection.execute(text("SELECT tenant_id, user_id FROM tenant_memberships WHERE user_id = 'user-1'")).mappings().one()
        task = connection.execute(text("SELECT tenant_id, user_id FROM tasks WHERE id = 'task-1'")).mappings().one()
        assert task == membership
    # The running application now maps Day11 columns; historical
    # backfill assertions above intentionally stop at 0007, then bring
    # the fixture to the current runtime schema before starting FastAPI.
    command.upgrade(config, "head")
    sessions = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_get_db() -> Generator[Session, None, None]:
        db = sessions()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setenv("AUTO_CREATE_DB", "false")
    monkeypatch.setattr("main.SessionLocal", sessions)
    try:
        with TestClient(app) as client:
            response = client.get("/tasks/task-1", headers={"Authorization": f"Bearer {create_access_token('user-1')}"})
            assert response.status_code == 200
            assert response.json()["tenant_id"] == membership["tenant_id"]
    finally:
        app.dependency_overrides.clear()
    engine.dispose()
