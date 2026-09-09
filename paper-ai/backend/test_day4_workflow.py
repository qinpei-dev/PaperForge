from __future__ import annotations

import time
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from db.base import Base
from db.models import Project, Task, User, Workspace
from db.session import get_db
from main import app
from services.agent_pipeline import run_agent_pipeline


@pytest.fixture
def client() -> Generator[tuple[TestClient, sessionmaker[Session]], None, None]:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_get_db() -> Generator[Session, None, None]:
        db = sessions()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client, sessions
    app.dependency_overrides.clear()
    engine.dispose()


def register(client: TestClient, email: str) -> dict[str, object]:
    response = client.post("/auth/register", json={"email": email, "password": "password123"})
    assert response.status_code == 201
    return response.json()


def headers(payload: dict[str, object]) -> dict[str, str]:
    return {"Authorization": f"Bearer {payload['access_token']}"}


def test_pipeline_progress_callback_order(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    events: list[str] = []

    def fake_agent(**kwargs: object) -> dict[str, object]:
        callback = kwargs["progress_callback"]
        assert callable(callback)
        for stage in ("analyzing", "planning", "executing", "verifying", "completed"):
            callback(stage)
        return {"status": "ok", "agent_trace": []}

    monkeypatch.setattr("services.agent_pipeline.run_paper_agent", fake_agent)
    result = run_agent_pipeline(tmp_path / "paper.docx", tmp_path, mode="local", progress_callback=events.append)
    assert events == ["analyzing", "planning", "executing", "verifying", "completed"]
    assert result["status"] == "ok"


def test_pipeline_failed_callback(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    events: list[str] = []

    def fake_agent(**_: object) -> dict[str, object]:
        raise RuntimeError("boom")

    monkeypatch.setattr("services.agent_pipeline.run_paper_agent", fake_agent)
    result = run_agent_pipeline(tmp_path / "paper.docx", tmp_path, progress_callback=events.append)
    assert events == ["failed"]
    assert result["status"] == "error"


def test_task_workflow_stage_api_and_isolation(client, monkeypatch: pytest.MonkeyPatch) -> None:
    test_client, sessions = client
    owner = register(test_client, "day4-owner@example.com")
    other = register(test_client, "day4-other@example.com")

    def fake_pipeline(**kwargs: object) -> dict[str, object]:
        callback = kwargs["progress_callback"]
        for stage in ("analyzing", "planning", "executing", "verifying", "completed"):
            callback(stage)
        return {"status": "ok", "after_score": 95.0, "agent_trace": []}

    monkeypatch.setattr("main.run_agent_pipeline", fake_pipeline)
    response = test_client.post("/tasks", headers=headers(owner), files={"paper": ("paper.docx", b"fake", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}, data={"mode": "local", "allow_non_paper": "true"})
    assert response.status_code == 201
    task_id = response.json()["task_id"]
    detail = None
    for _ in range(20):
        detail = test_client.get(f"/tasks/{task_id}", headers=headers(owner))
        if detail.json().get("status") == "completed":
            break
        time.sleep(0.05)
    assert detail.status_code == 200
    assert detail.json()["status"] == "completed"
    assert detail.json()["workflow_stage"] == "completed"
    assert detail.json()["progress"] == 100
    assert test_client.get(f"/tasks/{task_id}", headers=headers(other)).status_code == 404
    db = sessions()
    saved = db.get(Task, task_id)
    assert saved is not None and saved.workflow_stage == "completed"
    db.close()


def test_legacy_task_without_workflow_stage_is_readable(client) -> None:
    test_client, sessions = client
    owner = register(test_client, "day4-legacy@example.com")
    db = sessions()
    workspace = db.scalar(select(Workspace).where(Workspace.id == owner["workspace_id"]))
    assert workspace is not None
    project = Project(workspace_id=workspace.id, title="Legacy", status="active")
    db.add(project); db.flush()
    task = Task(project_id=project.id, status="completed", score=88.0)
    db.add(task); db.commit(); task_id = task.id; db.close()
    payload = test_client.get(f"/tasks/{task_id}", headers=headers(owner)).json()
    assert payload["status"] == "completed"
    assert payload["workflow_stage"] is None


def test_failed_task_persists_failed_workflow_stage(client, monkeypatch: pytest.MonkeyPatch) -> None:
    test_client, sessions = client
    owner = register(test_client, "day4-failed@example.com")

    def fake_pipeline(**kwargs: object) -> dict[str, object]:
        callback = kwargs["progress_callback"]
        callback("analyzing")
        callback("failed")
        return {"status": "error", "error": "controlled failure", "agent_trace": []}

    monkeypatch.setattr("main.run_agent_pipeline", fake_pipeline)
    response = test_client.post("/tasks", headers=headers(owner), files={"paper": ("paper.docx", b"fake", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}, data={"mode": "local", "allow_non_paper": "true"})
    assert response.status_code == 201
    task_id = response.json()["task_id"]
    detail = None
    for _ in range(20):
        detail = test_client.get(f"/tasks/{task_id}", headers=headers(owner)).json()
        if detail.get("status") == "failed":
            break
        time.sleep(0.05)
    assert detail["status"] == "failed"
    assert detail["workflow_stage"] == "failed"
    db = sessions(); saved = db.get(Task, task_id)
    assert saved is not None and saved.status == "failed" and saved.workflow_stage == "failed"
    db.close()
