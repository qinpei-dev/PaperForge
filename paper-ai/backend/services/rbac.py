from __future__ import annotations

from collections.abc import Iterable

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from db.models import TenantMembership

ROLE_OWNER = "owner"
ROLE_ADMIN = "admin"
ROLE_MEMBER = "member"
ROLES = frozenset({ROLE_OWNER, ROLE_ADMIN, ROLE_MEMBER})

TENANT_READ = "tenant.read"
TENANT_MANAGE = "tenant.manage"
TEMPLATE_READ = "template.read"
TEMPLATE_WRITE = "template.write"
TASK_READ = "task.read"
TASK_CREATE = "task.create"
TASK_MANAGE = "task.manage"
MEMBER_READ = "member.read"
MEMBER_MANAGE = "member.manage"
OWNER_MANAGE = "owner.manage"
AUDIT_READ = "audit.read"

ALL_PERMISSIONS = frozenset({TENANT_READ, TENANT_MANAGE, TEMPLATE_READ, TEMPLATE_WRITE, TASK_READ, TASK_CREATE, TASK_MANAGE, MEMBER_READ, MEMBER_MANAGE, OWNER_MANAGE, AUDIT_READ})
ROLE_PERMISSIONS = {
    ROLE_OWNER: ALL_PERMISSIONS,
    ROLE_ADMIN: frozenset({TENANT_READ, TEMPLATE_READ, TEMPLATE_WRITE, TASK_READ, TASK_CREATE, TASK_MANAGE, MEMBER_READ, AUDIT_READ}),
    ROLE_MEMBER: frozenset({TENANT_READ, TEMPLATE_READ, TASK_READ, TASK_CREATE}),
}


def permissions_for_role(role: str) -> frozenset[str]:
    return ROLE_PERMISSIONS.get(role, frozenset())


def get_membership(db: Session, user_id: str, tenant_id: str, *, active_only: bool = True) -> TenantMembership | None:
    statement = select(TenantMembership).where(TenantMembership.user_id == user_id, TenantMembership.tenant_id == tenant_id)
    if active_only:
        statement = statement.where(TenantMembership.status == "active")
    return db.scalar(statement)


def is_tenant_member(db: Session, user_id: str, tenant_id: str) -> bool:
    return get_membership(db, user_id, tenant_id) is not None


def require_tenant_member(db: Session, user_id: str, tenant_id: str) -> TenantMembership:
    membership = get_membership(db, user_id, tenant_id)
    if membership is None:
        raise HTTPException(status_code=404, detail="没有找到 tenant。")
    return membership


def require_tenant_permission(membership: TenantMembership, permission: str) -> TenantMembership:
    if permission not in permissions_for_role(membership.role):
        # Authorization failure within a known tenant may be 403; resource lookups remain 404.
        raise HTTPException(status_code=403, detail="当前角色没有该操作权限。")
    return membership


def require_tenant_role(membership: TenantMembership, roles: Iterable[str]) -> TenantMembership:
    if membership.role not in set(roles):
        raise HTTPException(status_code=403, detail="当前角色没有该操作权限。")
    return membership


def add_member(db: Session, *, tenant_id: str, user_id: str, role: str = ROLE_MEMBER) -> TenantMembership:
    if role not in ROLES:
        raise ValueError("unknown tenant role")
    if get_membership(db, user_id, tenant_id, active_only=False) is not None:
        raise ValueError("membership already exists")
    membership = TenantMembership(tenant_id=tenant_id, user_id=user_id, role=role, status="active")
    db.add(membership)
    return membership


def _owner_count(db: Session, tenant_id: str) -> int:
    return int(db.scalar(select(func.count()).select_from(TenantMembership).where(TenantMembership.tenant_id == tenant_id, TenantMembership.role == ROLE_OWNER, TenantMembership.status == "active")) or 0)


def change_role(db: Session, membership: TenantMembership, new_role: str, *, actor: TenantMembership) -> TenantMembership:
    if actor.tenant_id != membership.tenant_id or actor.role != ROLE_OWNER:
        raise PermissionError("only an owner can change roles")
    if new_role not in {ROLE_ADMIN, ROLE_MEMBER}:
        raise ValueError("unknown tenant role")
    if membership.role == ROLE_OWNER:
        raise ValueError("owner role cannot be changed through this API")
    membership.role = new_role
    return membership


def remove_member(db: Session, membership: TenantMembership, *, actor: TenantMembership) -> None:
    if actor.tenant_id != membership.tenant_id or actor.role != ROLE_OWNER:
        raise PermissionError("only an owner can remove members")
    if membership.role == ROLE_OWNER:
        raise ValueError("owner cannot be removed through this API")
    db.delete(membership)
