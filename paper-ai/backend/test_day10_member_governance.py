from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, select, text

from db.models import TenantInvitation, TenantMembership
from services.rbac import ROLE_ADMIN, ROLE_MEMBER
from services.tenant_invitations import hash_token
from test_day10_membership_rbac import account, add_existing_member, headers, membership, rbac_client


def test_owner_governs_members_and_admin_member_are_denied(rbac_client) -> None:
    client, sessions = rbac_client
    owner, admin, member, newcomer = (account(client, email) for email in ("p1-owner@example.com", "p1-admin@example.com", "p1-member@example.com", "p1-new@example.com"))
    tenant_id = membership(sessions, str(owner["user"]["id"])).tenant_id
    add_existing_member(sessions, tenant_id, str(admin["user"]["id"]), ROLE_ADMIN)
    add_existing_member(sessions, tenant_id, str(member["user"]["id"]), ROLE_MEMBER)
    created = client.post(f"/tenants/{tenant_id}/members", headers=headers(owner), json={"email": newcomer["user"]["email"], "role": "member"})
    assert created.status_code == 201
    new_user_id = created.json()["user_id"]
    assert client.patch(f"/tenants/{tenant_id}/members/{new_user_id}", headers=headers(owner), json={"role": "admin"}).status_code == 200
    assert client.patch(f"/tenants/{tenant_id}/members/{new_user_id}", headers=headers(owner), json={"role": "member"}).status_code == 200
    assert client.delete(f"/tenants/{tenant_id}/members/{new_user_id}", headers=headers(owner)).status_code == 204
    assert client.post(f"/tenants/{tenant_id}/members", headers=headers(admin), json={"email": newcomer["user"]["email"], "role": "member"}).status_code == 403
    assert client.post(f"/tenants/{tenant_id}/members", headers=headers(member), json={"email": newcomer["user"]["email"], "role": "member"}).status_code == 403
    owner_id = owner["user"]["id"]
    assert client.patch(f"/tenants/{tenant_id}/members/{owner_id}", headers=headers(owner), json={"role": "admin"}).status_code == 409
    assert client.delete(f"/tenants/{tenant_id}/members/{owner_id}", headers=headers(owner)).status_code == 409
    assert client.post(f"/tenants/{tenant_id}/members", headers=headers(owner), json={"email": newcomer["user"]["email"], "role": "owner"}).status_code == 422


def test_invitation_single_use_email_and_status_security(rbac_client) -> None:
    client, sessions = rbac_client
    owner, invited, wrong = (account(client, email) for email in ("invite-owner@example.com", "invitee@example.com", "wrong@example.com"))
    tenant_id = membership(sessions, str(owner["user"]["id"])).tenant_id
    created = client.post(f"/tenants/{tenant_id}/invitations", headers=headers(owner), json={"email": invited["user"]["email"], "role": "admin"})
    assert created.status_code == 201
    token = created.json()["token"]
    assert "token_hash" not in created.json()
    assert client.post(f"/tenant-invitations/{token}/accept", headers=headers(wrong)).status_code == 403
    assert client.post(f"/tenant-invitations/{token}/accept", headers=headers(invited)).status_code == 200
    assert client.post(f"/tenant-invitations/{token}/accept", headers=headers(invited)).status_code == 409
    second = client.post(f"/tenants/{tenant_id}/invitations", headers=headers(owner), json={"email": wrong["user"]["email"], "role": "member"})
    assert second.status_code == 201
    invitation_id = second.json()["id"]
    assert client.delete(f"/tenants/{tenant_id}/invitations/{invitation_id}", headers=headers(owner)).status_code == 204
    assert client.post(f"/tenant-invitations/{second.json()['token']}/accept", headers=headers(wrong)).status_code == 409
    db = sessions()
    try:
        expired = TenantInvitation(tenant_id=tenant_id, email="expired@example.com", role="member", token_hash=hash_token("expired-token"), status="pending", expires_at=datetime.now(timezone.utc) - timedelta(seconds=1), created_by=str(owner["user"]["id"]))
        db.add(expired); db.commit()
    finally:
        db.close()
    assert client.post("/tenant-invitations/expired-token/accept", headers=headers(owner)).status_code == 409
    assert client.post(f"/tenants/{tenant_id}/invitations", headers=headers(invited), json={"email": "x@example.com", "role": "member"}).status_code == 403


def test_workspace_list_and_removal_immediately_block_access(rbac_client) -> None:
    client, sessions = rbac_client
    owner, member = account(client, "switch-owner@example.com"), account(client, "switch-member@example.com")
    tenant_id = membership(sessions, str(owner["user"]["id"])).tenant_id
    add_existing_member(sessions, tenant_id, str(member["user"]["id"]), ROLE_MEMBER)
    workspaces = client.get("/workspaces", headers=headers(member))
    assert workspaces.status_code == 200 and any(item["tenant_id"] == tenant_id for item in workspaces.json())
    assert client.get("/templates", headers=headers(member, tenant_id)).status_code == 200
    assert client.delete(f"/tenants/{tenant_id}/members/{member['user']['id']}", headers=headers(owner)).status_code == 204
    assert client.get("/templates", headers=headers(member, tenant_id)).status_code == 404


def test_0007_to_0008_roundtrip(tmp_path: Path) -> None:
    database = tmp_path / "p1-migration.db"
    url = f"sqlite:///{database.as_posix()}"
    config = Config("alembic.ini"); config.set_main_option("sqlalchemy.url", url)
    command.upgrade(config, "0007_day10_membership_rbac")
    command.upgrade(config, "0008_day10_member_governance")
    engine = create_engine(url)
    with engine.connect() as connection:
        assert "tenant_invitations" in connection.dialect.get_table_names(connection)
    command.downgrade(config, "0007_day10_membership_rbac")
    command.upgrade(config, "0008_day10_member_governance")
    engine.dispose()
