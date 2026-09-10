"""Database-authoritative lifecycle helpers for the lightweight TaskWorker."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import update
from sqlalchemy.orm import Session

from db.models import Task, TaskEvent


TERMINAL_STATUSES = {"completed", "failed", "cancelled", "interrupted"}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def safe_event_metadata(payload: dict[str, Any]) -> dict[str, Any]:
    """Keep replay/audit records useful without accidentally storing secrets."""
    forbidden = ("token", "password", "secret", "api_key", "authorization", "paper_text", "raw_text")
    return {key: value for key, value in payload.items() if not any(term in key.lower() for term in forbidden)}


def record_task_event(db: Session, task: Task, event_type: str, **payload: Any) -> TaskEvent:
    event = TaskEvent(
        task_id=task.id,
        tenant_id=task.tenant_id,
        event_type=event_type,
        stage=payload.get("workflow_stage") or payload.get("stage"),
        progress=payload.get("progress"),
        message=payload.get("message") or event_type,
        metadata_json=safe_event_metadata(payload),
    )
    db.add(event)
    db.flush()
    return event


def claim_pending_task(db: Session, task_id: str) -> str | None:
    """Atomically claim PENDING work; no Python lock is used as authority."""
    run_id = uuid4().hex
    now = utc_now()
    result = db.execute(
        update(Task)
        .where(Task.id == task_id, Task.status == "pending")
        .values(
            status="running", current_stage="analyzing", workflow_stage="analyzing",
            progress=0, started_at=now, updated_at=now, worker_run_id=run_id,
            attempt_count=Task.attempt_count + 1, state_version=Task.state_version + 1,
            error_code=None, error_message=None,
        )
    )
    if result.rowcount != 1:
        db.rollback()
        return None
    db.commit()
    return run_id


def advance_running_task(db: Session, task: Task, run_id: str, *, stage: str, progress: int) -> bool:
    result = db.execute(
        update(Task)
        .where(Task.id == task.id, Task.status == "running", Task.worker_run_id == run_id)
        .values(workflow_stage=stage, current_stage=stage, progress=max(0, min(100, progress)), updated_at=utc_now(), state_version=Task.state_version + 1)
    )
    if result.rowcount != 1:
        db.rollback()
        return False
    db.commit()
    db.refresh(task)
    return True


def finish_running_task(
    db: Session, task: Task, run_id: str, *, status: str, stage: str, progress: int,
    error_code: str | None = None, error_message: str | None = None, result_metadata: dict[str, Any] | None = None,
) -> bool:
    if status not in TERMINAL_STATUSES:
        raise ValueError(f"terminal status required, got {status}")
    result = db.execute(
        update(Task)
        .where(Task.id == task.id, Task.status == "running", Task.worker_run_id == run_id)
        .values(status=status, workflow_stage=stage, current_stage=stage, progress=max(0, min(100, progress)), finished_at=utc_now(), updated_at=utc_now(), error_code=error_code, error_message=error_message, result_metadata=result_metadata or {}, state_version=Task.state_version + 1)
    )
    if result.rowcount != 1:
        db.rollback()
        return False
    db.commit()
    db.refresh(task)
    return True


def reconcile_orphaned_tasks(db: Session, worker_identity: str) -> int:
    """A process restart cannot resume DOCX work safely, so mark it explicit."""
    now = utc_now()
    running = db.query(Task).filter(Task.status == "running").all()
    changed = 0
    for task in running:
        previous = task.worker_run_id
        task.status = "interrupted"
        task.workflow_stage = "interrupted"
        task.current_stage = "interrupted"
        task.finished_at = now
        task.updated_at = now
        task.error_code = "backend_restart"
        task.error_message = "Backend restarted before this in-process task could finish; automatic resume is not supported."
        task.recovery_metadata = {"reason": "orphaned_running_task", "detected_at": now.isoformat(), "previous_worker_run_id": previous, "reconciled_by": worker_identity}
        task.state_version += 1
        record_task_event(db, task, "task_interrupted", status="interrupted", workflow_stage="interrupted", progress=task.progress, message="后端重启检测到未完成任务，已标记为中断。", interruption_reason="backend_restart", previous_worker_run_id=previous)
        changed += 1
    if changed:
        db.commit()
    return changed
