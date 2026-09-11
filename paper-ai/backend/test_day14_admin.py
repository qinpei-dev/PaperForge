from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

import main
from db.base import Base
from db.models import Project, Quota, Task, TenantMembership, Usage, User, Workspace
from db.session import get_db
from services.quota import current_usage_period


@pytest.fixture
def admin_client(monkeypatch: pytest.MonkeyPatch, tmp_path) -> Generator[tuple[TestClient, sessionmaker[Session]], None, None]:
    monkeypatch.setenv("AUTH_REQUIRED", "true")
    monkeypatch.setenv("AUTO_CREATE_DB", "false")
    monkeypatch.setenv("ADMIN_EMAILS", " ADMIN@EXAMPLE.COM ")
    engine = create_engine(f"sqlite:///{(tmp_path / 'admin.db').as_posix()}")
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
    with TestClient(app) as client:
        try:
            yield client, sessions
        finally:
            pass
    app.dependency_overrides.clear()
    engine.dispose()


def register(client: TestClient, email: str) -> dict[str, object]:
    response = client.post("/auth/register", json={"email": email, "password": "password123"})
    assert response.status_code == 201, response.text
    return response.json()


def headers(payload: dict[str, object]) -> dict[str, str]:
    return {"Authorization": f"Bearer {payload['access_token']}"}


def seed_tasks(sessions: sessionmaker[Session], admin: dict[str, object], member: dict[str, object]) -> None:
    db = sessions()
    try:
        users = [
            db.scalar(select(User).where(User.email == "admin@example.com")),
            db.scalar(select(User).where(User.email == "member@example.com")),
        ]
        assert all(users)
        for user, statuses in zip(users, [["pending", "completed"], ["running", "failed"]], strict=True):
            membership = db.scalar(select(TenantMembership).where(TenantMembership.user_id == user.id))
            workspace = db.scalar(select(Workspace).where(Workspace.owner_id == user.id))
            assert membership is not None and workspace is not None
            project = Project(workspace_id=workspace.id, title="Admin test project")
            db.add(project)
            db.flush()
            quota = db.scalar(select(Quota).where(Quota.tenant_id == membership.tenant_id))
            assert quota is not None
            for index, status in enumerate(statuses):
                task = Task(
                    project_id=project.id,
                    tenant_id=membership.tenant_id,
                    user_id=user.id,
                    status=status,
                    paper_name=f"paper-{index}.docx",
                )
                db.add(task)
                db.flush()
                db.add(
                    Usage(
                        tenant_id=membership.tenant_id,
                        user_id=user.id,
                        task_id=task.id,
                        metric="agent_run",
                        quantity=1,
                        period_start=current_usage_period().start,
                        metadata_json={"source": "test"},
                    )
                )
        db.commit()
    finally:
        db.close()


def test_admin_stats_requires_platform_admin_and_returns_aggregates(
    admin_client: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, sessions = admin_client
    admin = register(client, "admin@example.com")
    member = register(client, "member@example.com")
    assert admin["user"]["is_admin"] is True
    assert member["user"]["is_admin"] is False
    seed_tasks(sessions, admin, member)

    response = client.get("/admin/stats", headers=headers(admin))

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["tenants"] == {"total": 2, "active": 2}
    assert body["users"] == {"total": 2}
    assert body["tasks"]["total"] == 4
    assert body["tasks"]["status_summary"] == {"completed": 1, "failed": 1, "pending": 1, "running": 1}
    assert body["usage"]["metric"] == "agent_run"
    assert body["usage"]["used"] == 4
    assert body["usage"]["all_time_used"] == 4
    assert body["usage"]["monthly_quota_total"] == 200

    with_tenant_header = client.get("/admin/stats", headers={**headers(admin), "X-Tenant-ID": "untrusted-tenant-id"})
    assert with_tenant_header.status_code == 200
    isolated_body = with_tenant_header.json()
    assert isolated_body["tenants"] == body["tenants"]
    assert isolated_body["users"] == body["users"]
    assert isolated_body["tasks"] == body["tasks"]
    assert isolated_body["usage"] == body["usage"]


def test_non_admin_and_anonymous_cannot_access_admin_stats(
    admin_client: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, _ = admin_client
    register(client, "admin@example.com")
    member = register(client, "member@example.com")

    assert client.get("/admin/stats").status_code == 401
    denied = client.get("/admin/stats", headers=headers(member))
    assert denied.status_code == 403
    assert "平台管理员" in str(denied.json())
