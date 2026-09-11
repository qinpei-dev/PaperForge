"""Tenant and user active-task admission control.

The quota row is used as a small, existing per-tenant coordination row.  The
row lock makes the admission check and task insert serialize on PostgreSQL;
the task table remains the source of truth for active work.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from db.models import Task
from services.quota import get_or_create_quota


ACTIVE_TASK_STATUSES = ("pending", "running")
DEFAULT_MAX_ACTIVE_TASKS_PER_USER = 2
DEFAULT_MAX_ACTIVE_TASKS_PER_TENANT = 4


def _positive_int_env(name: str, default: int) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError:
        return default
    return max(1, value)


def max_active_tasks_per_user() -> int:
    return _positive_int_env("MAX_ACTIVE_TASKS_PER_USER", DEFAULT_MAX_ACTIVE_TASKS_PER_USER)


def max_active_tasks_per_tenant() -> int:
    return _positive_int_env("MAX_ACTIVE_TASKS_PER_TENANT", DEFAULT_MAX_ACTIVE_TASKS_PER_TENANT)


@dataclass(frozen=True)
class TaskConcurrencySnapshot:
    tenant_id: str
    user_id: str
    tenant_active: int
    user_active: int
    tenant_limit: int
    user_limit: int

    def as_dict(self) -> dict[str, int | str]:
        return {
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "tenant_active": self.tenant_active,
            "user_active": self.user_active,
            "tenant_limit": self.tenant_limit,
            "user_limit": self.user_limit,
        }


class TaskConcurrencyExceededError(Exception):
    def __init__(self, snapshot: TaskConcurrencySnapshot, scope: str) -> None:
        self.snapshot = snapshot
        self.scope = scope
        super().__init__(f"{scope} active task limit exceeded")


def check_task_concurrency(db: Session, tenant_id: str, user_id: str) -> TaskConcurrencySnapshot:
    """Admit one task while holding the existing tenant coordination row lock."""
    get_or_create_quota(db, tenant_id, lock=True)
    tenant_active = int(
        db.scalar(
            select(func.count()).select_from(Task).where(
                Task.tenant_id == tenant_id,
                Task.status.in_(ACTIVE_TASK_STATUSES),
            )
        )
        or 0
    )
    user_active = int(
        db.scalar(
            select(func.count()).select_from(Task).where(
                Task.tenant_id == tenant_id,
                Task.user_id == user_id,
                Task.status.in_(ACTIVE_TASK_STATUSES),
            )
        )
        or 0
    )
    snapshot = TaskConcurrencySnapshot(
        tenant_id=tenant_id,
        user_id=user_id,
        tenant_active=tenant_active,
        user_active=user_active,
        tenant_limit=max_active_tasks_per_tenant(),
        user_limit=max_active_tasks_per_user(),
    )
    if tenant_active >= snapshot.tenant_limit:
        raise TaskConcurrencyExceededError(snapshot, "tenant")
    if user_active >= snapshot.user_limit:
        raise TaskConcurrencyExceededError(snapshot, "user")
    return snapshot
