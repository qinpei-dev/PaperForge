from __future__ import annotations

from dataclasses import dataclass
from uuid import NAMESPACE_URL, uuid5

from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from auth import get_current_user
from db.models import Tenant, TenantMembership, User
from db.session import get_db


@dataclass(frozen=True)
class TenantContext:
    current_user: User
    tenant: Tenant
    membership: TenantMembership

    @property
    def tenant_id(self) -> str:
        return self.tenant.id


def personal_tenant_id(user_id: str) -> str:
    return str(uuid5(NAMESPACE_URL, f"paperforge:personal-tenant:{user_id}"))


def personal_membership_id(user_id: str) -> str:
    return str(uuid5(NAMESPACE_URL, f"paperforge:personal-membership:{user_id}"))


def personal_tenant_slug(user_id: str) -> str:
    return f"personal-{user_id.lower()}"


def ensure_personal_tenant(db: Session, user: User) -> TenantMembership:
    """Idempotently provide the stable compatibility tenant for one user."""
    if not user.id:
        db.flush()
    tenant_id = personal_tenant_id(user.id)
    tenant = db.get(Tenant, tenant_id)
    if tenant is None:
        tenant = Tenant(
            id=tenant_id,
            name=f"{user.email} Personal Tenant",
            slug=personal_tenant_slug(user.id),
            status="active",
        )
        db.add(tenant)
        db.flush()
    membership = db.scalar(
        select(TenantMembership).where(
            TenantMembership.tenant_id == tenant.id,
            TenantMembership.user_id == user.id,
        )
    )
    if membership is None:
        membership = TenantMembership(
            id=personal_membership_id(user.id),
            tenant_id=tenant.id,
            user_id=user.id,
            role="owner",
            status="active",
        )
        db.add(membership)
        db.flush()
    return membership


def bootstrap_personal_tenants(db: Session) -> int:
    inserted = 0
    users = list(db.scalars(select(User).order_by(User.id)).all())
    for user in users:
        tenant_id = personal_tenant_id(user.id)
        membership_existed = db.scalar(
            select(TenantMembership.id).where(
                TenantMembership.tenant_id == tenant_id,
                TenantMembership.user_id == user.id,
            )
        ) is not None
        ensure_personal_tenant(db, user)
        if not membership_existed:
            inserted += 1
    db.commit()
    return inserted


def resolve_tenant_context(db: Session, user: User, tenant_id: str | None = None) -> TenantContext:
    """Resolve a server-verified active tenant context; client tenant ids are never trusted."""
    membership = ensure_personal_tenant(db, user) if tenant_id is None else db.scalar(
        select(TenantMembership).where(
            TenantMembership.tenant_id == tenant_id,
            TenantMembership.user_id == user.id,
        )
    )
    db.commit()
    if membership is None:
        # Keep tenant/resource anti-enumeration behavior for cross-tenant IDs.
        raise HTTPException(status_code=404, detail="没有找到 tenant。")
    tenant = db.get(Tenant, membership.tenant_id)
    if membership.status != "active":
        raise HTTPException(status_code=403, detail="当前 tenant membership 已停用。")
    if tenant is None or tenant.status != "active":
        raise HTTPException(status_code=403, detail="当前 tenant 已停用或不存在。")
    return TenantContext(current_user=user, tenant=tenant, membership=membership)


def get_current_tenant(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    requested_tenant_id: str | None = Header(None, alias="X-Tenant-ID"),
) -> TenantContext:
    return resolve_tenant_context(db, current_user, requested_tenant_id)
