from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from time import sleep

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from db.base import Base
from db.session import get_db
from main import app
from services.task_events import TaskEventStore
from services.task_worker import TaskWorker


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch, tmp_path) -> Generator[TestClient, None, None]:
    engine = create_engine(f"sqlite:///{(tmp_path / 'test.db').as_posix()}")
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
    with TestClient(app) as test_client:
        try:
            yield test_client
        finally:
            worker.shutdown()
    app.dependency_overrides.clear()
    engine.dispose()


def register(client: TestClient, email: str) -> dict[str, object]:
    return client.post("/auth/register", json={"email": email, "password": "password123"}).json()


def auth(user: dict[str, object]) -> dict[str, str]:
    return {"Authorization": f"Bearer {user['access_token']}"}


def create_task(client: TestClient, user: dict[str, object]) -> str:
    response = client.post("/tasks", headers=auth(user), files={"paper": ("paper.docx", b"fake", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}, data={"mode": "local", "allow_non_paper": "true"})
    assert response.status_code == 201
    return str(response.json()["task_id"])


def wait_for(client: TestClient, task_id: str, user: dict[str, object], status: str) -> None:
    for _ in range(40):
        if client.get(f"/tasks/{task_id}", headers=auth(user)).json().get("status") == status:
            return
        sleep(0.025)
    pytest.fail(f"task did not reach {status}")


def read_sse(response) -> list[dict[str, object]]:
    blocks = response.text.strip().split("\n\n")
    return [__import__("json").loads(next(line[6:] for line in block.splitlines() if line.startswith("data: "))) for block in blocks if "data: " in block]


def test_artifacts_are_published_before_completed_event(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    owner = register(client, "day6-owner@example.com")

    def fake_pipeline(**kwargs: object) -> dict[str, object]:
        callback = kwargs["progress_callback"]
        for stage in ("analyzing", "planning", "executing", "verifying", "completed"):
            callback(stage)
        return {"status": "ok", "filename": "day6-result.docx", "after_score": 95.0, "agent_trace": [], "modification_report": {"summary": "ok"}}

    monkeypatch.setattr("main.run_agent_pipeline", fake_pipeline)
    task_id = create_task(client, owner)
    wait_for(client, task_id, owner, "completed")
    response = client.get(f"/tasks/{task_id}/events", headers=auth(owner))
    assert response.status_code == 200
    events = read_sse(response)
    assert events[0]["event_type"] == "task_created"
    assert events[-1]["event_type"] == "task_completed"
    assert [event["workflow_stage"] for event in events if event.get("event_type") == "workflow_stage_changed"] == ["analyzing", "planning", "executing", "verifying"]
    event_types = [str(event["event_type"]) for event in events]
    assert event_types.index("artifact_created") < event_types.index("task_completed")


def test_other_user_cannot_subscribe(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    owner = register(client, "day6-private@example.com")
    other = register(client, "day6-intruder@example.com")
    monkeypatch.setattr("main.run_agent_pipeline", lambda **_: {"status": "ok", "agent_trace": []})
    task_id = create_task(client, owner)
    wait_for(client, task_id, owner, "completed")
    assert client.get(f"/tasks/{task_id}/events", headers=auth(other)).status_code == 404


def test_failed_task_emits_failed_event(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    owner = register(client, "day6-failed@example.com")

    def failing_pipeline(**_: object) -> dict[str, object]:
        raise RuntimeError(r"day6 failure at C:\private\uploads\secret-paper.docx")

    monkeypatch.setattr("main.run_agent_pipeline", failing_pipeline)
    task_id = create_task(client, owner)
    wait_for(client, task_id, owner, "failed")
    response = client.get(f"/tasks/{task_id}/events", headers=auth(owner))
    events = read_sse(response)
    assert events[-1]["event_type"] == "task_failed"
    assert events[-1]["status"] == "failed"
    assert r"C:\private" not in response.text
    assert "secret-paper.docx" not in response.text
    assert "Traceback" not in response.text


def test_terminal_event_history_is_cleaned_after_ttl_and_bounded() -> None:
    bounded_store = TaskEventStore(terminal_ttl_seconds=60, max_completed_histories=1)
    bounded_store.publish_event("first", "task_completed", status="completed")
    bounded_store.publish_event("second", "task_completed", status="completed")
    assert not bounded_store.has_events("first")
    assert bounded_store.has_events("second")
    store = TaskEventStore(terminal_ttl_seconds=0.001)
    store.publish_event("expired", "task_completed", status="completed")
    sleep(0.01)
    assert not store.has_events("expired")


def test_frontend_uses_polling_only_as_sse_fallback() -> None:
    source = (Path(__file__).resolve().parents[1] / "frontend" / "app" / "tasks" / "[taskId]" / "page.tsx").read_text(encoding="utf-8")
    assert "await loadTask(false); if (!stopped && !terminalReceived) void connectStream();" in source
    assert "if (scheduleNext && pollingActive)" in source
    assert "if (!terminalReceived) startPolling();" in source
    assert "void loadTask(); void connectStream();" not in source
