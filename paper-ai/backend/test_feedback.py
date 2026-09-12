from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from db.models import Feedback, Project, Task, TenantMembership, Workspace
from test_saas import auth_header, register, saas_client


def test_feedback_requires_authentication(saas_client) -> None:
    client, _ = saas_client
    response = client.post("/feedback", json={"category": "bug", "description": "登录问题"})
    assert response.status_code == 401


def test_feedback_validates_category_description_and_length(saas_client) -> None:
    client, _ = saas_client
    owner = register(client, "feedback-validation@example.com")
    headers = auth_header(owner)
    assert client.post("/feedback", headers=headers, json={"category": "not-real", "description": "x"}).status_code == 422
    assert client.post("/feedback", headers=headers, json={"category": "bug", "description": " "}).status_code == 422
    assert client.post("/feedback", headers=headers, json={"category": "bug", "description": "x" * 5001}).status_code == 422


def test_feedback_binds_identity_and_records_speed_context(saas_client) -> None:
    client, _ = saas_client
    owner = register(client, "feedback-owner@example.com")
    headers = auth_header(owner)
    response = client.post(
        "/feedback",
        headers=headers,
        json={"category": "slow", "description": "处理很慢", "contact": "beta@example.com", "route": "/tasks/detail"},
    )
    assert response.status_code == 201, response.text
    with saas_client[1]() as db:
        item = db.scalar(select(Feedback).where(Feedback.id == response.json()["id"]))
        membership = db.scalar(select(TenantMembership).where(TenantMembership.user_id == owner["user"]["id"]))
        assert item is not None
        assert item.user_id == owner["user"]["id"]
        assert item.tenant_id == membership.tenant_id
        assert item.app_version == "v3.7.3"
        assert item.request_id
        assert item.contact == "beta@example.com"


def test_feedback_task_must_belong_to_current_tenant_and_records_elapsed(saas_client) -> None:
    client, _ = saas_client
    owner = register(client, "feedback-task-owner@example.com")
    db_factory = saas_client[1]
    with db_factory() as db:
        membership = db.scalar(select(TenantMembership).where(TenantMembership.user_id == owner["user"]["id"]))
        workspace = db.scalar(select(Workspace).where(Workspace.id == owner["workspace_id"]))
        project = Project(workspace_id=workspace.id, title="Feedback Task", status="active")
        db.add(project)
        db.flush()
        started = datetime.now(timezone.utc) - timedelta(seconds=12)
        task = Task(project_id=project.id, tenant_id=membership.tenant_id, user_id=membership.user_id, status="running", started_at=started)
        db.add(task)
        db.commit()
        task_id = task.id

    response = client.post("/feedback", headers=auth_header(owner), json={"category": "slow", "description": "这个任务很慢", "task_id": task_id})
    assert response.status_code == 201, response.text
    with db_factory() as db:
        item = db.get(Feedback, response.json()["id"])
        assert item is not None and item.metadata_json["task_status"] == "running"
        assert item.metadata_json["elapsed_seconds"] >= 12

    other = register(client, "feedback-other@example.com")
    assert client.post("/feedback", headers=auth_header(other), json={"category": "bug", "description": "跨租户", "task_id": task_id}).status_code == 404
