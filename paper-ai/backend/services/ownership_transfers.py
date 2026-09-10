from __future__ import annotations
import secrets
from datetime import timedelta
from sqlalchemy import select
from sqlalchemy.orm import Session
from db.models import TenantMembership, TenantOwnershipTransfer, User
from services.rbac import ROLE_ADMIN, ROLE_OWNER
from services.tenant_audit import record_audit_event
from services.tenant_invitations import hash_token, is_expired, now_utc

PENDING, ACCEPTED, CANCELLED, EXPIRED = "pending", "accepted", "cancelled", "expired"

def expire_pending_transfers(db: Session, tenant_id: str | None = None) -> None:
    statement = select(TenantOwnershipTransfer).where(TenantOwnershipTransfer.status == PENDING).with_for_update()
    if tenant_id: statement = statement.where(TenantOwnershipTransfer.tenant_id == tenant_id)
    for transfer in db.scalars(statement).all():
        if is_expired(transfer.expires_at): transfer.status = EXPIRED

def create_transfer(db: Session, *, tenant_id: str, actor: TenantMembership, to_user_id: str) -> tuple[TenantOwnershipTransfer, str]:
    if actor.role != ROLE_OWNER or actor.user_id == to_user_id: raise ValueError("invalid ownership transfer target")
    target = db.scalar(select(TenantMembership).where(TenantMembership.tenant_id == tenant_id, TenantMembership.user_id == to_user_id, TenantMembership.status == "active").with_for_update())
    if target is None: raise ValueError("target must be an active tenant member")
    expire_pending_transfers(db, tenant_id)
    if db.scalar(select(TenantOwnershipTransfer.id).where(TenantOwnershipTransfer.tenant_id == tenant_id, TenantOwnershipTransfer.status == PENDING).with_for_update()): raise ValueError("pending ownership transfer already exists")
    token = secrets.token_urlsafe(32)
    transfer = TenantOwnershipTransfer(tenant_id=tenant_id, from_user_id=actor.user_id, to_user_id=to_user_id, token_hash=hash_token(token), status=PENDING, expires_at=now_utc() + timedelta(hours=24))
    db.add(transfer); record_audit_event(db, tenant_id=tenant_id, actor_user_id=actor.user_id, event_type="ownership_transfer.created", target_type="membership", target_id=to_user_id)
    return transfer, token

def accept_transfer(db: Session, *, token: str, user: User) -> TenantOwnershipTransfer:
    transfer = db.scalar(select(TenantOwnershipTransfer).where(TenantOwnershipTransfer.token_hash == hash_token(token)).with_for_update())
    if transfer is None or transfer.status != PENDING: raise ValueError("transfer is no longer active")
    if is_expired(transfer.expires_at): transfer.status = EXPIRED; raise ValueError("transfer expired")
    if transfer.to_user_id != user.id: raise PermissionError("transfer target mismatch")
    members = list(db.scalars(select(TenantMembership).where(TenantMembership.tenant_id == transfer.tenant_id, TenantMembership.status == "active").with_for_update()).all())
    old_owner = next((item for item in members if item.user_id == transfer.from_user_id and item.role == ROLE_OWNER), None)
    new_owner = next((item for item in members if item.user_id == transfer.to_user_id), None)
    if old_owner is None or new_owner is None: raise ValueError("transfer participants are no longer valid")
    old_owner.role = ROLE_ADMIN
    new_owner.role = ROLE_OWNER
    transfer.status = ACCEPTED; transfer.accepted_at = now_utc()
    record_audit_event(db, tenant_id=transfer.tenant_id, actor_user_id=user.id, event_type="ownership_transfer.accepted", target_type="membership", target_id=user.id, metadata={"previous_owner_id": old_owner.user_id})
    return transfer
