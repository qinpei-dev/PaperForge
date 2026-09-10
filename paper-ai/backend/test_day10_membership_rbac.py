from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

import main
from auth import create_access_token
from db.base import Base
from db.models import Tenant, TenantMembership, User
from db.session import get_db
from services.rbac import ROLE_ADMIN, ROLE_MEMBER, ROLE_OWNER, TASK_CREATE, TEMPLATE_WRITE, add_member, change_role, permissions_for_role
from services.task_worker import TaskWorker
from services.tenant_context import resolve_tenant_context


@pytest.fixture
def rbac_client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Generator[tuple[TestClient, sessionmaker[Session]], None, None]:
    monkeypatch.setenv("AUTH_REQUIRED", "true")
    monkeypatch.setenv("AUTO_CREATE_DB", "false")
    engine = create_engine(f"sqlite:///{(tmp_path / 'rbac.db').as_posix()}")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_get_db() -> Generator[Session, None, None]:
        db = sessions()
        try:
            yield db
        finally:
            db.close()

    main.app.dependency_overrides[get_db] = override_get_db
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


def account(client: TestClient, email: str) -> dict[str, object]:
    response = client.post("/auth/register", json={"email": email, "password": "password123"})
    assert response.status_code == 201, response.text
    return response.json()


def headers(account_data: dict[str, object], tenant_id: str | None = None) -> dict[str, str]:
    result = {"Authorization": f"Bearer {account_data['access_token']}"}
    if tenant_id:
        result["X-Tenant-ID"] = tenant_id
    return result


def membership(sessions: sessionmaker[Session], user_id: str) -> TenantMembership:
    db = sessions()
    try:
        return db.scalar(select(TenantMembership).where(TenantMembership.user_id == user_id, TenantMembership.role == ROLE_OWNER))
    finally:
        db.close()


def add_existing_member(sessions: sessionmaker[Session], tenant_id: str, user_id: str, role: str) -> None:
    db = sessions()
    try:
        add_member(db, tenant_id=tenant_id, user_id=user_id, role=role)
        db.commit()
    finally:
        db.close()


def test_owner_membership_created_and_duplicate_blocked(rbac_client) -> None:
    client, sessions = rbac_client
    owner = account(client, "owner@example.com")
    owner_membership = membership(sessions, str(owner["user"]["id"]))
    assert owner_membership.role == ROLE_OWNER
    db = sessions()
    try:
        db.add(TenantMembership(tenant_id=owner_membership.tenant_id, user_id=owner_membership.user_id, role=ROLE_MEMBER, status="active"))
        with pytest.raises(IntegrityError):
            db.commit()
    finally:
        db.rollback()
        db.close()


def test_multi_tenant_multi_user_permissions_and_404_isolation(rbac_client) -> None:
    client, sessions = rbac_client
    owner = account(client, "team-owner@example.com")
    admin = account(client, "team-admin@example.com")
    member = account(client, "team-member@example.com")
    outsider = account(client, "team-outsider@example.com")
    tenant_id = membership(sessions, str(owner["user"]["id"])).tenant_id
    add_existing_member(sessions, tenant_id, str(admin["user"]["id"]), ROLE_ADMIN)
    add_existing_member(sessions, tenant_id, str(member["user"]["id"]), ROLE_MEMBER)

    owner_members = client.get(f"/tenants/{tenant_id}/members", headers=headers(owner)).json()
    assert {item["email"] for item in owner_members} >= {"team-owner@example.com", "team-admin@example.com", "team-member@example.com"}
    assert client.get(f"/tenants/{tenant_id}/members", headers=headers(admin)).status_code == 200
    assert client.get(f"/tenants/{tenant_id}/members", headers=headers(member)).status_code == 403
    assert client.get(f"/tenants/{tenant_id}/members", headers=headers(outsider)).status_code == 404
    assert client.get("/tenants/membership/me", headers=headers(admin, tenant_id)).json()["role"] == ROLE_ADMIN
    assert client.get("/templates", headers=headers(member, tenant_id)).status_code == 200
    assert client.get("/templates", headers=headers(outsider, tenant_id)).status_code == 404
    assert TASK_CREATE in permissions_for_role(ROLE_MEMBER)
    assert TEMPLATE_WRITE in permissions_for_role(ROLE_ADMIN)
    assert TEMPLATE_WRITE not in permissions_for_role(ROLE_MEMBER)

    db = sessions()
    try:
        second_tenant = Tenant(name="Second team", slug="second-team", status="active")
        db.add(second_tenant)
        db.flush()
        add_member(db, tenant_id=second_tenant.id, user_id=str(member["user"]["id"]), role=ROLE_MEMBER)
        db.commit()
        assert resolve_tenant_context(db, db.get(User, str(member["user"]["id"])), second_tenant.id).tenant_id == second_tenant.id
    finally:
        db.close()


def test_owner_safety_blocks_last_owner_and_non_owner_escalation(rbac_client) -> None:
    client, sessions = rbac_client
    owner = account(client, "safe-owner@example.com")
    member_account = account(client, "safe-member@example.com")
    owner_membership = membership(sessions, str(owner["user"]["id"]))
    add_existing_member(sessions, owner_membership.tenant_id, str(member_account["user"]["id"]), ROLE_MEMBER)
    db = sessions()
    try:
        member_record = db.scalar(select(TenantMembership).where(TenantMembership.tenant_id == owner_membership.tenant_id, TenantMembership.user_id == str(member_account["user"]["id"])))
        with pytest.raises(PermissionError):
            change_role(db, member_record, ROLE_OWNER, actor=member_record)
        with pytest.raises(ValueError):
            change_role(db, owner_membership, ROLE_MEMBER, actor=owner_membership)
    finally:
        db.close()


def test_0006_to_0007_upgrade_downgrade_reupgrade(tmp_path: Path) -> None:
    database = tmp_path / "migration.db"
    url = f"sqlite:///{database.as_posix()}"
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", url)
    command.upgrade(config, "0006_day9_tenant_template_management")
    engine = create_engine(url)
    with engine.begin() as connection:
        connection.execute(text("INSERT INTO users (id, email, password_hash) VALUES ('user-1', 'legacy@example.com', 'hash')"))
        connection.execute(text("INSERT INTO tenants (id, name, slug, status) VALUES ('tenant-1', 'Legacy', 'legacy', 'active')"))
        connection.execute(text("INSERT INTO tenant_memberships (id, tenant_id, user_id, role, status) VALUES ('membership-1', 'tenant-1', 'user-1', 'owner', 'active')"))
    command.upgrade(config, "0007_day10_membership_rbac")
    with engine.connect() as connection:
        roles = connection.execute(text("SELECT role FROM tenant_memberships")).scalars().all()
        assert roles == ["owner"]
        indexes = {row[1] for row in connection.execute(text("PRAGMA index_list('tenant_memberships')")).all()}
        assert "ix_tenant_memberships_tenant_role" in indexes
    command.downgrade(config, "0006_day9_tenant_template_management")
    command.upgrade(config, "0007_day10_membership_rbac")
    with engine.begin() as connection:
        connection.execute(text("INSERT INTO users (id, email, password_hash) VALUES ('user-2', 'admin@example.com', 'hash')"))
        connection.execute(text("INSERT INTO tenant_memberships (id, tenant_id, user_id, role, status) VALUES ('membership-2', 'tenant-1', 'user-2', 'admin', 'active')"))
    engine.dispose()
