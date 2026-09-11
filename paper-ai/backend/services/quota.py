"""Tenant-scoped quota checks and usage accounting for the Day13 P0 system."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from db.models import Quota, Usage


AGENT_RUN_METRIC = "agent_run"
DEFAULT_AGENT_RUN_QUOTA = 100


@dataclass(frozen=True)
class UsagePeriod:
    start: datetime
    end: datetime


@dataclass(frozen=True)
class QuotaSnapshot:
    tenant_id: str
    metric: str
    period: UsagePeriod
    limit: int
    used: int
    remaining: int

    def as_dict(self) -> dict[str, object]:
        return {
            "tenant_id": self.tenant_id,
            "metric": self.metric,
            "period_start": self.period.start.isoformat(),
            "period_end": self.period.end.isoformat(),
            "limit": self.limit,
            "used": self.used,
            "remaining": self.remaining,
        }


class QuotaExceededError(Exception):
    def __init__(self, snapshot: QuotaSnapshot, requested: int) -> None:
        self.snapshot = snapshot
        self.requested = requested
        super().__init__("Tenant usage quota exceeded")


def default_agent_run_quota() -> int:
    raw = os.getenv("DEFAULT_AGENT_RUN_QUOTA", str(DEFAULT_AGENT_RUN_QUOTA)).strip()
    try:
        value = int(raw)
    except ValueError:
        return DEFAULT_AGENT_RUN_QUOTA
    return max(0, value)


def current_usage_period(now: datetime | None = None) -> UsagePeriod:
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    current = current.astimezone(timezone.utc)
    if current.month == 12:
        next_month = datetime(current.year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        next_month = datetime(current.year, current.month + 1, 1, tzinfo=timezone.utc)
    return UsagePeriod(datetime(current.year, current.month, 1, tzinfo=timezone.utc), next_month)


def get_or_create_quota(db: Session, tenant_id: str, *, lock: bool = False) -> Quota:
    statement = select(Quota).where(Quota.tenant_id == tenant_id)
    if lock:
        statement = statement.with_for_update()
    quota = db.scalar(statement)
    if quota is None:
        quota = Quota(tenant_id=tenant_id, monthly_limit=default_agent_run_quota())
        db.add(quota)
        db.flush()
    return quota


def _used_quantity(db: Session, tenant_id: str, period: UsagePeriod) -> int:
    used = db.scalar(
        select(func.coalesce(func.sum(Usage.quantity), 0)).where(
            Usage.tenant_id == tenant_id,
            Usage.metric == AGENT_RUN_METRIC,
            Usage.period_start >= period.start,
            Usage.period_start < period.end,
        )
    )
    return int(used or 0)


def check_quota(
    db: Session,
    tenant_id: str,
    *,
    quantity: int = 1,
    now: datetime | None = None,
) -> QuotaSnapshot:
    """Check the current tenant period while holding the quota row lock."""
    if quantity <= 0:
        raise ValueError("quantity must be positive")
    quota = get_or_create_quota(db, tenant_id, lock=True)
    period = current_usage_period(now)
    used = _used_quantity(db, tenant_id, period)
    snapshot = QuotaSnapshot(tenant_id, AGENT_RUN_METRIC, period, quota.monthly_limit, used, max(0, quota.monthly_limit - used))
    if used + quantity > quota.monthly_limit:
        raise QuotaExceededError(snapshot, quantity)
    return snapshot


def record_usage(
    db: Session,
    *,
    tenant_id: str,
    user_id: str,
    task_id: str,
    quantity: int = 1,
    period: UsagePeriod | None = None,
) -> Usage:
    """Add one usage ledger entry; the caller owns the surrounding transaction."""
    if quantity <= 0:
        raise ValueError("quantity must be positive")
    item = Usage(
        tenant_id=tenant_id,
        user_id=user_id,
        task_id=task_id,
        metric=AGENT_RUN_METRIC,
        quantity=quantity,
        period_start=(period or current_usage_period()).start,
        metadata_json={"source": "agent_run"},
    )
    db.add(item)
    db.flush()
    return item


def get_usage_snapshot(db: Session, tenant_id: str, *, now: datetime | None = None) -> QuotaSnapshot:
    quota = get_or_create_quota(db, tenant_id)
    period = current_usage_period(now)
    used = _used_quantity(db, tenant_id, period)
    return QuotaSnapshot(tenant_id, AGENT_RUN_METRIC, period, quota.monthly_limit, used, max(0, quota.monthly_limit - used))


def usage_response(snapshot: QuotaSnapshot) -> dict[str, object]:
    """Return a stable, intentionally small read-only API representation."""
    return {
        "tenant_id": snapshot.tenant_id,
        "metric": snapshot.metric,
        "period_start": snapshot.period.start.isoformat(),
        "period_end": snapshot.period.end.isoformat(),
        "quota": {"agent_runs": snapshot.limit, "limit": snapshot.limit},
        "usage": {"agent_runs": snapshot.used, "used": snapshot.used},
        "remaining": snapshot.remaining,
    }
