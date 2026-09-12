from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from db.models import Feedback, TenantMembership, User
from test_day14_admin import admin_client as admin_client_fixture
from test_day14_admin import headers, register


@pytest.fixture
def admin_client(admin_client_fixture):
    return admin_client_fixture


def test_admin_feedback_is_authenticated_filtered_paginated_and_cross_tenant(admin_client) -> None:
    client, sessions = admin_client
    assert client.get("/admin/feedback").status_code == 401
    admin = register(client, "admin@example.com")
    member = register(client, "member@example.com")
    with sessions() as db:
        admin_user = db.scalar(select(User).where(User.email == "admin@example.com"))
        member_user = db.scalar(select(User).where(User.email == "member@example.com"))
        assert admin_user and member_user
        admin_membership = db.scalar(select(TenantMembership).where(TenantMembership.user_id == admin_user.id))
        member_membership = db.scalar(select(TenantMembership).where(TenantMembership.user_id == member_user.id))
        assert admin_membership and member_membership
        db.add_all([
            Feedback(user_id=admin_user.id, tenant_id=admin_membership.tenant_id, category="bug", description="admin bug", contact="a@example.com", route="/tasks", request_id="r1", app_version="v3.7.3", created_at=datetime.now(timezone.utc), metadata_json={"task_status": "failed", "elapsed_seconds": 3}),
            Feedback(user_id=member_user.id, tenant_id=member_membership.tenant_id, category="slow", description="member slow", task_id="task-slow", app_version="v3.7.3", created_at=datetime.now(timezone.utc), metadata_json={"task_status": "running", "elapsed_seconds": 12, "secret": "must-not-leak"}),
        ])
        db.commit()
    denied = client.get("/admin/feedback", headers=headers(member))
    assert denied.status_code == 403
    response = client.get("/admin/feedback?page=1&page_size=1&category=slow&user=member@example.com", headers=headers(admin))
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["total"] == 1 and len(body["items"]) == 1
    item = body["items"][0]
    assert item["tenant_id"] != item["user_id"]
    assert item["speed_metadata"] == {"task_status": "running", "elapsed_seconds": 12}
    assert "password_hash" not in item and "secret" not in item and "Authorization" not in item
    assert client.get("/admin/feedback?category=invalid", headers=headers(admin)).status_code == 422
