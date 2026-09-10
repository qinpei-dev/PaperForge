from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

import main
from auth import create_access_token
from db.base import Base
from db.models import Project, Task, TaskEvent, Tenant, TenantMembership, User, Workspace
from db.session import get_db
from services.durable_tasks import advance_running_task, claim_pending_task, finish_running_task, reconcile_orphaned_tasks, record_task_event


@pytest.fixture
def runtime_db(tmp_path) -> Generator[sessionmaker[Session], None, None]:
    engine = create_engine(f"sqlite:///{(tmp_path / 'runtime.db').as_posix()}")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    try:
        yield sessions
    finally:
        engine.dispose()


def make_task(sessions: sessionmaker[Session], suffix: str = "a") -> tuple[Task, User]:
    db = sessions()
    user = User(email=f"runtime-{suffix}@example.com", password_hash="hash")
    tenant = Tenant(name=f"Runtime {suffix}", slug=f"runtime-{suffix}", status="active")
    TenantMembership(tenant=tenant, user=user, role="owner", status="active")
    workspace = Workspace(name="Runtime", owner=user)
    project = Project(title="Runtime", workspace=workspace)
    task = Task(project=project, tenant=tenant, user=user, status="pending", paper_name="paper.docx", uploaded_file="input.docx")
    db.add(task); db.commit(); db.refresh(task); db.expunge(task); db.expunge(user); db.close()
    return task, user


def test_durable_lifecycle_terminal_protection_and_single_claim(runtime_db) -> None:
    task, _ = make_task(runtime_db)
    first = runtime_db(); second = runtime_db()
    try:
        run_one = claim_pending_task(first, task.id)
        run_two = claim_pending_task(second, task.id)
        assert run_one is not None and run_two is None
        current = first.get(Task, task.id)
        assert current is not None and current.status == "running" and current.attempt_count == 1
        assert advance_running_task(first, current, run_one, stage="executing", progress=60)
        assert finish_running_task(first, current, run_one, status="completed", stage="completed", progress=100)
        assert not advance_running_task(second, second.get(Task, task.id), run_one, stage="executing", progress=60)
        saved = first.get(Task, task.id)
        assert saved.status == "completed" and saved.progress == 100
    finally:
        first.close(); second.close()


def test_restart_reconciliation_marks_orphan_interrupted(runtime_db) -> None:
    task, _ = make_task(runtime_db)
    db = runtime_db()
    try:
        run_id = claim_pending_task(db, task.id)
        current = db.get(Task, task.id)
        assert run_id and current
        assert reconcile_orphaned_tasks(db, "test-startup") == 1
        db.expire_all(); interrupted = db.get(Task, task.id)
        assert interrupted.status == "interrupted"
        assert interrupted.error_code == "backend_restart"
        assert interrupted.recovery_metadata["previous_worker_run_id"] == run_id
        assert db.scalar(select(TaskEvent).where(TaskEvent.task_id == task.id, TaskEvent.event_type == "task_interrupted")) is not None
    finally:
        db.close()


def test_event_replay_is_tenant_scoped(runtime_db, monkeypatch) -> None:
    sessions = runtime_db
    task_a, user_a = make_task(sessions, "a")
    task_b, user_b = make_task(sessions, "b")
    db = sessions()
    try:
        current = db.get(Task, task_a.id)
        record_task_event(db, current, "task_created", status="pending", progress=0, message="created")
        record_task_event(db, current, "task_completed", status="completed", workflow_stage="completed", progress=100, message="done")
        current.status = "completed"; current.workflow_stage = "completed"; current.progress = 100
        db.commit()
    finally:
        db.close()

    def override() -> Generator[Session, None, None]:
        scoped = sessions()
        try: yield scoped
        finally: scoped.close()
    main.app.dependency_overrides[get_db] = override
    monkeypatch.setattr(main, "SessionLocal", sessions)
    monkeypatch.setenv("AUTH_REQUIRED", "true")
    headers_a = {"Authorization": f"Bearer {create_access_token(user_a.id)}", "X-Tenant-ID": task_a.tenant_id}
    headers_b = {"Authorization": f"Bearer {create_access_token(user_b.id)}", "X-Tenant-ID": task_b.tenant_id}
    with TestClient(main.app) as client:
        response = client.get(f"/tasks/{task_a.id}/events", headers=headers_a)
        assert response.status_code == 200
        assert "id: 1" in response.text and "created" in response.text and "done" in response.text
        replay = client.get(f"/tasks/{task_a.id}/events?after=1", headers={**headers_a, "Last-Event-ID": "1"})
        assert "created" not in replay.text and "done" in replay.text
        assert client.get(f"/tasks/{task_a.id}/events", headers=headers_b).status_code == 404
        assert client.get(f"/tasks/{task_b.id}/events", headers=headers_a).status_code == 404
    main.app.dependency_overrides.clear()
