from __future__ import annotations

import io
import zipfile
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from starlette.responses import Response
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

import main
from db.base import Base
from db.models import Quota, Task, TenantMembership, Usage
from db.session import get_db
from services.task_worker import TaskWorker


def valid_docx_bytes() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("word/document.xml", "<w:document/>")
    return buffer.getvalue()


@pytest.fixture
def quota_client(monkeypatch: pytest.MonkeyPatch, tmp_path) -> Generator[tuple[TestClient, sessionmaker[Session]], None, None]:
    monkeypatch.setenv("AUTH_REQUIRED", "true")
    monkeypatch.setenv("AUTO_CREATE_DB", "false")
    engine = create_engine(f"sqlite:///{(tmp_path / 'quota.db').as_posix()}")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override() -> Generator[Session, None, None]:
        db = sessions()
        try:
            yield db
        finally:
            db.close()

    app = main.app
    app.dependency_overrides[get_db] = override
    monkeypatch.setattr(main, "SessionLocal", sessions)
    worker = TaskWorker()
    monkeypatch.setattr(main, "task_worker", worker)
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


def headers(payload: dict[str, object]) -> dict[str, str]:
    return {"Authorization": f"Bearer {payload['access_token']}"}


def run_agent(client: TestClient, auth: dict[str, object]) -> Response:
    return client.post(
        "/agent/run",
        headers=headers(auth),
        files={"paper": ("paper.docx", valid_docx_bytes(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        data={"mode": "local", "allow_non_paper": "true"},
    )


def test_usage_is_tenant_scoped_and_starts_at_zero(quota_client: tuple[TestClient, sessionmaker[Session]]) -> None:
    client, sessions = quota_client
    owner = register(client, "quota-owner@example.com")

    response = client.get("/usage", headers=headers(owner))

    assert response.status_code == 200, response.text
    body = response.json()
    db = sessions()
    try:
        membership = db.scalar(select(TenantMembership).where(TenantMembership.user_id == owner["user"]["id"]))
        assert membership is not None
        assert body["tenant_id"] == membership.tenant_id
    finally:
        db.close()
    assert body["metric"] == "agent_run"
    assert body["usage"]["used"] == 0
    assert body["quota"]["limit"] == 100
    assert body["remaining"] == 100
    db = sessions()
    try:
        assert db.scalar(select(Quota).where(Quota.tenant_id == body["tenant_id"])) is not None
    finally:
        db.close()


def test_agent_run_records_usage_after_task_creation(
    quota_client: tuple[TestClient, sessionmaker[Session]], monkeypatch: pytest.MonkeyPatch
) -> None:
    client, sessions = quota_client
    owner = register(client, "quota-record@example.com")
    monkeypatch.setattr(main, "run_agent_pipeline", lambda **_: {"status": "ok", "after_score": 92.0, "agent_trace": []})

    response = run_agent(client, owner)

    assert response.status_code == 200, response.text
    task_id = response.json()["task_id"]
    db = sessions()
    try:
        usage = db.scalar(select(Usage).where(Usage.task_id == task_id))
        assert usage is not None
        membership = db.scalar(select(TenantMembership).where(TenantMembership.user_id == owner["user"]["id"]))
        assert membership is not None and usage.tenant_id == membership.tenant_id
        assert db.scalar(select(Task).where(Task.id == task_id)) is not None
    finally:
        db.close()
    current = client.get("/usage", headers=headers(owner))
    assert current.status_code == 200
    assert current.json()["usage"]["used"] == 1
    assert current.json()["remaining"] == 99


def test_quota_is_checked_before_creating_the_next_task(
    quota_client: tuple[TestClient, sessionmaker[Session]], monkeypatch: pytest.MonkeyPatch
) -> None:
    client, sessions = quota_client
    owner = register(client, "quota-limit@example.com")
    db = sessions()
    try:
        membership = db.scalar(select(TenantMembership).where(TenantMembership.user_id == owner["user"]["id"]))
        assert membership is not None
        quota = db.scalar(select(Quota).where(Quota.tenant_id == membership.tenant_id))
        if quota is None:
            quota = Quota(tenant_id=membership.tenant_id, monthly_limit=1)
            db.add(quota)
        else:
            quota.monthly_limit = 1
        db.commit()
    finally:
        db.close()
    monkeypatch.setattr(main, "run_agent_pipeline", lambda **_: {"status": "ok", "after_score": 92.0, "agent_trace": []})

    assert run_agent(client, owner).status_code == 200
    rejected = run_agent(client, owner)

    assert rejected.status_code == 429
    assert rejected.json()["error"]["message"]["code"] == "QUOTA_EXCEEDED"
    db = sessions()
    try:
        membership = db.scalar(select(TenantMembership).where(TenantMembership.user_id == owner["user"]["id"]))
        assert membership is not None
        assert len(db.scalars(select(Task).where(Task.tenant_id == membership.tenant_id)).all()) == 1
        assert len(db.scalars(select(Usage).where(Usage.tenant_id == membership.tenant_id)).all()) == 1
    finally:
        db.close()


def test_usage_does_not_cross_tenant_boundary(quota_client: tuple[TestClient, sessionmaker[Session]]) -> None:
    client, sessions = quota_client
    owner_a = register(client, "quota-a@example.com")
    owner_b = register(client, "quota-b@example.com")
    db = sessions()
    try:
        tenant_a = db.scalar(select(TenantMembership).where(TenantMembership.user_id == owner_a["user"]["id"]))
        assert tenant_a is not None
        tenant_id = tenant_a.tenant_id
    finally:
        db.close()

    assert client.get("/usage", headers={**headers(owner_b), "X-Tenant-ID": tenant_id}).status_code == 404
