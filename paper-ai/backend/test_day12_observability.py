from __future__ import annotations

import json
import logging

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from main import app
from db.base import Base
from db.session import get_db
from services.observability import StructuredJsonFormatter, bind_context, clear_context, log_event
from services.task_worker import TaskWorker


@pytest.fixture
def observability_client(monkeypatch: pytest.MonkeyPatch, tmp_path) -> Generator[TestClient, None, None]:
    monkeypatch.setenv("AUTH_REQUIRED", "true")
    monkeypatch.setenv("AUTO_CREATE_DB", "false")
    engine = create_engine(f"sqlite:///{(tmp_path / 'observability.db').as_posix()}")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override() -> Generator[Session, None, None]:
        db = sessions()
        try: yield db
        finally: db.close()

    app.dependency_overrides[get_db] = override
    monkeypatch.setattr("main.SessionLocal", sessions)
    worker = TaskWorker(); monkeypatch.setattr("main.task_worker", worker)
    with TestClient(app) as client:
        try: yield client
        finally: worker.shutdown()
    app.dependency_overrides.clear(); engine.dispose()


def test_request_id_is_generated_and_returned(observability_client: TestClient) -> None:
    client = observability_client
    response = client.get("/health")
    assert response.status_code == 200
    assert len(response.headers["X-Request-ID"]) == 32
    assert response.headers["X-Request-ID"] != client.get("/health").headers["X-Request-ID"]


def test_health_and_readiness_report_process_and_database(observability_client: TestClient) -> None:
    client = observability_client
    assert client.get("/health").json() == {"status": "ok"}
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready", "checks": {"database": "ok"}}


def test_error_responses_are_classified_and_correlated(observability_client: TestClient) -> None:
    client = observability_client
    response = client.get("/auth/me")
    body = response.json()
    assert response.status_code == 401
    assert body["error"]["code"] == "AUTH_ERROR"
    assert body["request_id"] == response.headers["X-Request-ID"]


def test_structured_logging_redacts_sensitive_values() -> None:
    formatter = StructuredJsonFormatter()
    logger = logging.getLogger("test.observability")
    record = logger.makeRecord("test.observability", logging.INFO, __file__, 1, "safe event", (), None, extra={"event": "upload_checked", "duration_ms": 1, "api_key": "must-not-leak", "password": "must-not-leak", "paper_text": "must-not-leak"})
    bind_context(request_id="request-1", tenant_id="tenant-1", user_id="user-1", task_id="task-1")
    try:
        payload = json.loads(formatter.format(record))
    finally:
        clear_context()
    assert payload["request_id"] == "request-1" and payload["task_id"] == "task-1"
    rendered = json.dumps(payload, ensure_ascii=False)
    assert "must-not-leak" not in rendered
    assert payload["event"] == "upload_checked" and payload["duration_ms"] == 1
