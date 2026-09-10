from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import TenantInvitation, TenantMembership, User
from services.rbac import ROLE_ADMIN, ROLE_MEMBER, add_member

INVITATION_PENDING = "pending"
INVITATION_ACCEPTED = "accepted"
INVITATION_REVOKED = "revoked"
INVITATION_EXPIRED = "expired"
INVITATION_ROLES = frozenset({ROLE_ADMIN, ROLE_MEMBER})


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def is_expired(expires_at: datetime) -> bool:
    # SQLite returns naive datetimes even for timezone-aware columns; stored
    # invitation timestamps are always UTC.
    return expires_at.replace(tzinfo=timezone.utc) <= now_utc() if expires_at.tzinfo is None else expires_at <= now_utc()


def expire_pending_invitations(db: Session, tenant_id: str | None = None) -> None:
    statement = select(TenantInvitation).where(TenantInvitation.status == INVITATION_PENDING, TenantInvitation.expires_at <= now_utc())
    if tenant_id:
        statement = statement.where(TenantInvitation.tenant_id == tenant_id)
    for invitation in db.scalars(statement).all():
        invitation.status = INVITATION_EXPIRED


def create_invitation(db: Session, *, tenant_id: str, email: str, role: str, created_by: str, expires_in_days: int = 7) -> tuple[TenantInvitation, str]:
    if role not in INVITATION_ROLES:
        raise ValueError("invalid invitation role")
    expire_pending_invitations(db, tenant_id)
    invited_user = db.scalar(select(User).where(User.email == email))
    if invited_user is not None and db.scalar(select(TenantMembership.id).where(TenantMembership.tenant_id == tenant_id, TenantMembership.user_id == invited_user.id)) is not None:
        raise ValueError("user is already a tenant member")
    duplicate = db.scalar(select(TenantInvitation).where(TenantInvitation.tenant_id == tenant_id, TenantInvitation.email == email, TenantInvitation.status == INVITATION_PENDING))
    if duplicate is not None:
        raise ValueError("a pending invitation already exists for this email")
    token = secrets.token_urlsafe(32)
    invitation = TenantInvitation(tenant_id=tenant_id, email=email, role=role, token_hash=hash_token(token), status=INVITATION_PENDING, expires_at=now_utc() + timedelta(days=expires_in_days), created_by=created_by)
    db.add(invitation)
    return invitation, token


def accept_invitation(db: Session, *, token: str, user: User) -> TenantInvitation:
    invitation = db.scalar(select(TenantInvitation).where(TenantInvitation.token_hash == hash_token(token)).with_for_update())
    if invitation is None:
        raise ValueError("invitation not found")
    if invitation.status != INVITATION_PENDING:
        raise ValueError("invitation is no longer active")
    if is_expired(invitation.expires_at):
        invitation.status = INVITATION_EXPIRED
        raise ValueError("invitation has expired")
    if user.email.lower() != invitation.email.lower():
        raise PermissionError("invitation email does not match authenticated user")
    if db.scalar(select(TenantMembership.id).where(TenantMembership.tenant_id == invitation.tenant_id, TenantMembership.user_id == user.id)) is not None:
        raise ValueError("user is already a tenant member")
    add_member(db, tenant_id=invitation.tenant_id, user_id=user.id, role=invitation.role)
    invitation.status = INVITATION_ACCEPTED
    invitation.accepted_at = now_utc()
    return invitation
