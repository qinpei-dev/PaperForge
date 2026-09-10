from __future__ import annotations
from datetime import datetime, timedelta, timezone
from pathlib import Path
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, select
from db.models import TenantOwnershipTransfer, TenantMembership
from services.rbac import ROLE_ADMIN, ROLE_MEMBER, ROLE_OWNER
from services.tenant_invitations import hash_token
from test_day10_membership_rbac import account, add_existing_member, headers, membership, rbac_client

def test_ownership_transfer_lifecycle_and_audit(rbac_client) -> None:
    client, sessions = rbac_client
    owner, target, outsider = (account(client, email) for email in ("p2-owner@example.com", "p2-target@example.com", "p2-outsider@example.com"))
    tenant_id = membership(sessions, str(owner["user"]["id"])).tenant_id
    add_existing_member(sessions, tenant_id, str(target["user"]["id"]), ROLE_MEMBER)
    assert client.post(f"/tenants/{tenant_id}/ownership-transfer", headers=headers(outsider), json={"to_user_id": target["user"]["id"]}).status_code == 404
    assert client.post(f"/tenants/{tenant_id}/ownership-transfer", headers=headers(owner), json={"to_user_id": owner["user"]["id"]}).status_code == 409
    created = client.post(f"/tenants/{tenant_id}/ownership-transfer", headers=headers(owner), json={"to_user_id": target["user"]["id"]}); assert created.status_code == 201
    token = created.json()["token"]; assert "hash" not in str(created.json())
    assert client.post(f"/tenant-ownership-transfers/{token}/accept", headers=headers(outsider)).status_code == 403
    assert client.post(f"/tenants/{tenant_id}/ownership-transfer", headers=headers(owner), json={"to_user_id": target["user"]["id"]}).status_code == 409
    assert client.post(f"/tenant-ownership-transfers/{token}/accept", headers=headers(target)).status_code == 200
    assert client.post(f"/tenant-ownership-transfers/{token}/accept", headers=headers(target)).status_code == 409
    db = sessions()
    try:
        roles = {item.user_id: item.role for item in db.scalars(select(TenantMembership).where(TenantMembership.tenant_id == tenant_id)).all()}
        assert roles[str(owner["user"]["id"])] == ROLE_ADMIN and roles[str(target["user"]["id"])] == ROLE_OWNER
    finally: db.close()
    assert client.patch(f"/tenants/{tenant_id}", headers=headers(owner), json={"display_name": "Denied"}).status_code == 403
    assert client.patch(f"/tenants/{tenant_id}", headers=headers(target), json={"display_name": "P2 Team"}).status_code == 200
    audit = client.get(f"/tenants/{tenant_id}/audit-events", headers=headers(target)); assert audit.status_code == 200
    assert {event["event_type"] for event in audit.json()["events"]} >= {"ownership_transfer.created", "ownership_transfer.accepted", "tenant.settings_updated"}
    assert client.get(f"/tenants/{tenant_id}/audit-events", headers=headers(owner)).status_code == 200

def test_removed_target_cancelled_expired_and_audit_isolation(rbac_client) -> None:
    client, sessions = rbac_client
    owner, target, outsider = (account(client, email) for email in ("p2b-owner@example.com", "p2b-target@example.com", "p2b-outsider@example.com"))
    tenant_id = membership(sessions, str(owner["user"]["id"])).tenant_id; add_existing_member(sessions, tenant_id, str(target["user"]["id"]), ROLE_MEMBER)
    created = client.post(f"/tenants/{tenant_id}/ownership-transfer", headers=headers(owner), json={"to_user_id": target["user"]["id"]}).json()
    assert client.delete(f"/tenants/{tenant_id}/members/{target['user']['id']}", headers=headers(owner)).status_code == 204
    assert client.post(f"/tenant-ownership-transfers/{created['token']}/accept", headers=headers(target)).status_code == 409
    assert client.get(f"/tenants/{tenant_id}/audit-events", headers=headers(outsider)).status_code == 404
    assert client.get(f"/tenants/{tenant_id}/audit-events", headers=headers(target, tenant_id)).status_code == 404

def test_0008_to_0009_roundtrip(tmp_path: Path) -> None:
    url = f"sqlite:///{(tmp_path / 'p2.db').as_posix()}"; config = Config("alembic.ini"); config.set_main_option("sqlalchemy.url", url)
    command.upgrade(config, "0008_day10_member_governance"); command.upgrade(config, "0009_day10_ownership_audit_settings"); command.downgrade(config, "0008_day10_member_governance"); command.upgrade(config, "0009_day10_ownership_audit_settings")
