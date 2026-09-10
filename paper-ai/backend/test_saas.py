from __future__ import annotations

import io
import time
import zipfile

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from db.base import Base
from db.models import Artifact, Project, Task, Tenant, TenantMembership, User, Workspace
from db.session import get_db
from main import app
from services.task_worker import TaskWorker


def valid_docx_bytes(content: bytes = b"") -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("word/document.xml", "<w:document/>")
        archive.writestr("customXml/item.xml", content)
    return buffer.getvalue()


@pytest.fixture
def saas_client(monkeypatch: pytest.MonkeyPatch, tmp_path) -> Generator[tuple[TestClient, sessionmaker[Session]], None, None]:
    monkeypatch.setenv("AUTH_REQUIRED", "true")
    monkeypatch.setenv("AUTO_CREATE_DB", "false")
    engine = create_engine(f"sqlite:///{(tmp_path / 'test.db').as_posix()}")
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_get_db() -> Generator[Session, None, None]:
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr("main.SessionLocal", testing_session)
    worker = TaskWorker()
    monkeypatch.setattr("main.task_worker", worker)
    with TestClient(app) as client:
        try:
            yield client, testing_session
        finally:
            worker.shutdown()
    app.dependency_overrides.clear()
    engine.dispose()


def register(client: TestClient, email: str) -> dict[str, object]:
    response = client.post("/auth/register", json={"email": email, "password": "password123"})
    assert response.status_code == 201, response.text
    return response.json()


def auth_header(payload: dict[str, object]) -> dict[str, str]:
    return {"Authorization": f"Bearer {payload['access_token']}"}


def test_register_login_and_token_validation(saas_client: tuple[TestClient, sessionmaker[Session]]) -> None:
    client, _ = saas_client
    registered = register(client, "auth@example.com")
    assert registered["workspace_name"] == "auth的 PaperForge Space"
    assert client.get("/auth/me", headers=auth_header(registered)).json()["email"] == "auth@example.com"

    logged_in = client.post("/auth/login", json={"email": "auth@example.com", "password": "password123"})
    assert logged_in.status_code == 200
    assert client.get("/auth/me", headers=auth_header(logged_in.json())).status_code == 200
    assert client.get("/auth/me").status_code == 401


def test_database_crud(saas_client: tuple[TestClient, sessionmaker[Session]]) -> None:
    _, testing_session = saas_client
    db = testing_session()
    user = User(email="crud@example.com", password_hash="hash")
    tenant = Tenant(name="CRUD Tenant", slug="crud-tenant", status="active")
    membership = TenantMembership(tenant=tenant, user=user, role="owner", status="active")
    workspace = Workspace(name="CRUD Space", owner=user)
    project = Project(title="CRUD Project", workspace=workspace)
    task = Task(status="completed", score=88.5, uploaded_file="input.docx", project=project, tenant=tenant, user=user)
    artifact = Artifact(file_path="outputs/result.docx", file_type="docx", task=task)
    db.add_all([user, membership])
    db.commit()
    saved = db.scalar(select(Artifact).where(Artifact.id == artifact.id))
    assert saved is not None
    assert saved.task.project.workspace.owner.email == "crud@example.com"
    assert saved.task.score == 88.5
    db.delete(saved.task.project.workspace.owner)
    db.commit()
    assert db.scalar(select(User).where(User.email == "crud@example.com")) is None
    assert db.scalar(select(Artifact).where(Artifact.id == artifact.id)) is None
    db.close()


def test_task_isolation_between_users(saas_client: tuple[TestClient, sessionmaker[Session]]) -> None:
    client, testing_session = saas_client
    user_a = register(client, "user-a@example.com")
    user_b = register(client, "user-b@example.com")

    db = testing_session()
    workspace = db.scalar(select(Workspace).where(Workspace.id == user_a["workspace_id"]))
    membership = db.scalar(select(TenantMembership).where(TenantMembership.user_id == user_a["user"]["id"]))
    assert workspace is not None
    assert membership is not None
    project = Project(workspace_id=workspace.id, title="A Project", status="active")
    db.add(project)
    db.flush()
    task = Task(project_id=project.id, tenant_id=membership.tenant_id, user_id=membership.user_id, status="completed", score=91.0, uploaded_file="a.docx")
    db.add(task)
    db.commit()
    task_id = task.id
    db.close()

    assert client.get("/tasks", headers=auth_header(user_a)).json()[0]["id"] == task_id
    assert client.get("/tasks", headers=auth_header(user_b)).json() == []
    assert client.get(f"/tasks/{task_id}", headers=auth_header(user_a)).status_code == 200
    assert client.get(f"/tasks/{task_id}", headers=auth_header(user_b)).status_code == 404


def test_duplicate_registration_is_rejected(saas_client: tuple[TestClient, sessionmaker[Session]]) -> None:
    client, _ = saas_client
    register(client, "duplicate@example.com")
    response = client.post("/auth/register", json={"email": "duplicate@example.com", "password": "password123"})
    assert response.status_code == 409


def test_create_task_runs_pipeline_and_persists_artifacts(
    saas_client: tuple[TestClient, sessionmaker[Session]], monkeypatch: pytest.MonkeyPatch
) -> None:
    client, testing_session = saas_client
    owner = register(client, "task-owner@example.com")

    def fake_pipeline(**_: object) -> dict[str, object]:
        return {
            "status": "ok",
            "filename": "task-result.docx",
            "after_score": 94.0,
            "agent_trace": [{"step": "format", "status": "ok"}],
            "modification_report": {"summary": "格式修复完成"},
        }

    monkeypatch.setattr("main.run_agent_pipeline", fake_pipeline)
    response = client.post(
        "/tasks",
        headers=auth_header(owner),
        files={"paper": ("paper.docx", valid_docx_bytes(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        data={"mode": "local", "allow_non_paper": "true"},
    )
    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload["status"] == "pending"

    detail = None
    for _ in range(20):
        detail = client.get(f"/tasks/{payload['task_id']}", headers=auth_header(owner))
        if detail.json().get("status") == "completed":
            break
        time.sleep(0.05)
    assert detail.status_code == 200
    task = detail.json()
    assert task["status"] == "completed"
    assert task["score"] == 94.0
    assert task["trace"][0]["step"] == "resolve_template"
    assert task["trace"][0]["template_id"] == "paperforge-general-academic"
    assert task["trace"][1:] == [{"step": "format", "status": "ok"}]
    assert {artifact["file_type"] for artifact in task["artifacts"]} == {"docx", "report"}

    db = testing_session()
    saved = db.get(Task, payload["task_id"])
    assert saved is not None and saved.status == "completed"
    db.close()


def test_create_task_isolation_between_users(
    saas_client: tuple[TestClient, sessionmaker[Session]], monkeypatch: pytest.MonkeyPatch
) -> None:
    client, _ = saas_client
    user_a = register(client, "task-a@example.com")
    user_b = register(client, "task-b@example.com")
    monkeypatch.setattr("main.run_agent_pipeline", lambda **_: {"status": "ok", "after_score": 80.0, "agent_trace": []})
    response = client.post(
        "/tasks",
        headers=auth_header(user_a),
        files={"paper": ("paper.docx", valid_docx_bytes(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        data={"mode": "local", "allow_non_paper": "true"},
    )
    assert response.status_code == 201
    task_id = response.json()["task_id"]
    assert client.get(f"/tasks/{task_id}", headers=auth_header(user_a)).status_code == 200
    assert client.get(f"/tasks/{task_id}", headers=auth_header(user_b)).status_code == 404
