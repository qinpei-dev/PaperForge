from __future__ import annotations

from collections.abc import Generator
from threading import Event

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from db.base import Base
from db.models import Task
from db.session import get_db
from main import app


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Generator[tuple[TestClient, sessionmaker[Session]], None, None]:
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
    monkeypatch.setattr("main.SessionLocal", sessions)
    with TestClient(app) as test_client:
        yield test_client, sessions
    app.dependency_overrides.clear()
    engine.dispose()


def register(client: TestClient, email: str) -> dict[str, object]:
    return client.post("/auth/register", json={"email": email, "password": "password123"}).json()


def auth(user: dict[str, object]) -> dict[str, str]:
    return {"Authorization": f"Bearer {user['access_token']}"}


def upload(client: TestClient, user: dict[str, object]):
    return client.post("/tasks", headers=auth(user), files={"paper": ("paper.docx", b"fake", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}, data={"mode": "local", "allow_non_paper": "true"})


def test_task_creation_returns_before_worker_finishes(client, monkeypatch: pytest.MonkeyPatch) -> None:
    test_client, sessions = client
    owner = register(test_client, "day5-create@example.com")
    started, release = Event(), Event()

    def fake_pipeline(**kwargs: object) -> dict[str, object]:
        started.set(); release.wait(timeout=2)
        return {"status": "ok", "after_score": 93.0, "agent_trace": []}

    monkeypatch.setattr("main.run_agent_pipeline", fake_pipeline)
    response = upload(test_client, owner)
    assert response.status_code == 201
    task_id = response.json()["task_id"]
    assert response.json()["status"] == "pending"
    assert started.wait(timeout=1)
    db = sessions(); saved = db.get(Task, task_id); assert saved is not None and saved.status in {"pending", "running"}; db.close()
    release.set()


def test_worker_persists_progress_and_completion(client, monkeypatch: pytest.MonkeyPatch) -> None:
    test_client, _ = client
    owner = register(test_client, "day5-progress@example.com")

    def fake_pipeline(**kwargs: object) -> dict[str, object]:
        callback = kwargs["progress_callback"]
        for stage in ("analyzing", "planning", "executing", "verifying", "completed"):
            callback(stage)
        return {"status": "ok", "after_score": 96.0, "agent_trace": []}

    monkeypatch.setattr("main.run_agent_pipeline", fake_pipeline)
    task_id = upload(test_client, owner).json()["task_id"]
    for _ in range(20):
        detail = test_client.get(f"/tasks/{task_id}", headers=auth(owner)).json()
        if detail["status"] == "completed": break
        import time; time.sleep(0.05)
    assert detail["workflow_stage"] == "completed" and detail["progress"] == 100


def test_worker_failure_and_user_isolation(client, monkeypatch: pytest.MonkeyPatch) -> None:
    test_client, _ = client
    owner = register(test_client, "day5-failure@example.com")
    other = register(test_client, "day5-other@example.com")

    def fake_pipeline(**kwargs: object) -> dict[str, object]:
        raise RuntimeError("worker boom")

    monkeypatch.setattr("main.run_agent_pipeline", fake_pipeline)
    task_id = upload(test_client, owner).json()["task_id"]
    for _ in range(20):
        detail = test_client.get(f"/tasks/{task_id}", headers=auth(owner)).json()
        if detail["status"] == "failed": break
        import time; time.sleep(0.05)
    assert detail["status"] == "failed" and detail["workflow_stage"] == "failed"
    assert test_client.get(f"/tasks/{task_id}", headers=auth(other)).status_code == 404
