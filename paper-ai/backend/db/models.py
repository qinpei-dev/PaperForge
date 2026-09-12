from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


def new_id() -> str:
    return str(uuid4())


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    token_version: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    workspaces: Mapped[list[Workspace]] = relationship(back_populates="owner", cascade="all, delete-orphan")
    tenant_memberships: Mapped[list[TenantMembership]] = relationship(back_populates="user", cascade="all, delete-orphan")
    tasks: Mapped[list[Task]] = relationship(back_populates="user")
    usage_records: Mapped[list[Usage]] = relationship(back_populates="user")
    feedback_items: Mapped[list[Feedback]] = relationship(back_populates="user")


class Tenant(Base):
    __tablename__ = "tenants"
    __table_args__ = (CheckConstraint("status IN ('active', 'disabled')", name="ck_tenants_status"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), unique=True, index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    memberships: Mapped[list[TenantMembership]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
    invitations: Mapped[list[TenantInvitation]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
    ownership_transfers: Mapped[list[TenantOwnershipTransfer]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
    audit_events: Mapped[list[TenantAuditEvent]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
    quota: Mapped[Quota | None] = relationship(back_populates="tenant", uselist=False, cascade="all, delete-orphan")
    usage_records: Mapped[list[Usage]] = relationship(back_populates="tenant")
    templates: Mapped[list[Template]] = relationship(back_populates="tenant")
    tasks: Mapped[list[Task]] = relationship(back_populates="tenant")
    task_events: Mapped[list[TaskEvent]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
    feedback_items: Mapped[list[Feedback]] = relationship(back_populates="tenant", cascade="all, delete-orphan")


class TenantMembership(Base):
    __tablename__ = "tenant_memberships"
    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", name="uq_tenant_memberships_tenant_user"),
        CheckConstraint("role IN ('owner', 'admin', 'member')", name="ck_tenant_memberships_role"),
        CheckConstraint("status IN ('active', 'disabled')", name="ck_tenant_memberships_status"),
        Index("ix_tenant_memberships_tenant_role", "tenant_id", "role"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="member")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    tenant: Mapped[Tenant] = relationship(back_populates="memberships")
    user: Mapped[User] = relationship(back_populates="tenant_memberships")


class TenantInvitation(Base):
    __tablename__ = "tenant_invitations"
    __table_args__ = (
        CheckConstraint("role IN ('admin', 'member')", name="ck_tenant_invitations_role"),
        CheckConstraint("status IN ('pending', 'accepted', 'revoked', 'expired')", name="ck_tenant_invitations_status"),
        Index("ix_tenant_invitations_tenant_status", "tenant_id", "status"),
        UniqueConstraint("token_hash", name="uq_tenant_invitations_token_hash"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(320), index=True, nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="member")
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending", index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    tenant: Mapped[Tenant] = relationship(back_populates="invitations")


class TenantOwnershipTransfer(Base):
    __tablename__ = "tenant_ownership_transfers"
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'accepted', 'cancelled', 'expired')", name="ck_tenant_ownership_transfers_status"),
        UniqueConstraint("token_hash", name="uq_tenant_ownership_transfers_token_hash"),
        Index("uq_tenant_ownership_transfers_pending", "tenant_id", unique=True, sqlite_where=text("status = 'pending'"), postgresql_where=text("status = 'pending'")),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False)
    from_user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    to_user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending", index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    tenant: Mapped[Tenant] = relationship(back_populates="ownership_transfers")


class TenantAuditEvent(Base):
    __tablename__ = "tenant_audit_events"
    __table_args__ = (Index("ix_tenant_audit_events_tenant_created", "tenant_id", "created_at"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False)
    actor_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    target_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    target_id: Mapped[str | None] = mapped_column(String(320), nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    tenant: Mapped[Tenant] = relationship(back_populates="audit_events")


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    owner: Mapped[User] = relationship(back_populates="workspaces")
    projects: Mapped[list[Project]] = relationship(back_populates="workspace", cascade="all, delete-orphan")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    workspace: Mapped[Workspace] = relationship(back_populates="projects")
    tasks: Mapped[list[Task]] = relationship(back_populates="project", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="RESTRICT"), index=True, nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True, nullable=False)
    # Keep lifecycle status for API compatibility; workflow_stage tracks the
    # current Agent phase and is nullable for legacy rows.
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    workflow_stage: Mapped[str | None] = mapped_column(String(50), nullable=True)
    paper_name: Mapped[str | None] = mapped_column(String(320), nullable=True)
    uploaded_file: Mapped[str | None] = mapped_column(Text, nullable=True)
    agent_trace: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(JSON, nullable=True)
    before_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Day11 durable runtime fields.  ``status`` and ``workflow_stage`` keep
    # their existing lowercase API values for compatibility.
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_stage: Mapped[str | None] = mapped_column(String(100), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    input_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    result_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    worker_run_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    recovery_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    state_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    project: Mapped[Project] = relationship(back_populates="tasks")
    tenant: Mapped[Tenant] = relationship(back_populates="tasks")
    user: Mapped[User] = relationship(back_populates="tasks")
    artifacts: Mapped[list[Artifact]] = relationship(back_populates="task", cascade="all, delete-orphan")
    events: Mapped[list[TaskEvent]] = relationship(back_populates="task", cascade="all, delete-orphan")
    usage_records: Mapped[list[Usage]] = relationship(back_populates="task")
    feedback_items: Mapped[list[Feedback]] = relationship(back_populates="task")


class TaskEvent(Base):
    """Append-only, tenant-scoped task events used by SSE replay."""

    __tablename__ = "task_events"
    __table_args__ = (
        Index("ix_task_events_task_sequence", "task_id", "sequence", unique=True),
        Index("ix_task_events_tenant_sequence", "tenant_id", "sequence"),
    )

    sequence: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, default=new_id)
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), index=True, nullable=False)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    stage: Mapped[str | None] = mapped_column(String(100), nullable=True)
    progress: Mapped[int | None] = mapped_column(Integer, nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    task: Mapped[Task] = relationship(back_populates="events")
    tenant: Mapped[Tenant] = relationship(back_populates="task_events")


class Artifact(Base):
    __tablename__ = "artifacts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), index=True, nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    file_type: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    task: Mapped[Task] = relationship(back_populates="artifacts")


class Quota(Base):
    """Tenant-level monthly limits for the P0 usage system."""

    __tablename__ = "quotas"
    __table_args__ = (
        CheckConstraint("monthly_limit >= 0", name="ck_quotas_monthly_limit_nonnegative"),
        UniqueConstraint("tenant_id", name="uq_quotas_tenant"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    monthly_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=100, server_default="100")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    tenant: Mapped[Tenant] = relationship(back_populates="quota")

    @property
    def agent_run_limit(self) -> int:
        """Compatibility name for the single P0 quota metric."""
        return self.monthly_limit

    @agent_run_limit.setter
    def agent_run_limit(self, value: int) -> None:
        self.monthly_limit = value

    @property
    def limit(self) -> int:
        return self.monthly_limit

    @limit.setter
    def limit(self, value: int) -> None:
        self.monthly_limit = value


class Usage(Base):
    """Append-only tenant usage ledger; one agent-run entry per task."""

    __tablename__ = "usage_records"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_usage_records_quantity_positive"),
        UniqueConstraint("task_id", "metric", name="uq_usage_records_task_metric"),
        Index("ix_usage_records_tenant_period", "tenant_id", "period_start"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id", ondelete="RESTRICT"), nullable=False, index=True)
    metric: Mapped[str] = mapped_column(String(100), nullable=False, default="agent_run", server_default="agent_run")
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict, server_default=text("'{}'"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    tenant: Mapped[Tenant] = relationship(back_populates="usage_records")
    user: Mapped[User] = relationship(back_populates="usage_records")
    task: Mapped[Task] = relationship(back_populates="usage_records")


# Keep the longer domain name available to callers without introducing a
# second table or a second usage vocabulary in the P0 API.
UsageRecord = Usage


class Feedback(Base):
    """Minimal authenticated feedback intake for the controlled beta."""

    __tablename__ = "feedback"
    __table_args__ = (
        CheckConstraint("category IN ('bug', 'slow', 'format', 'ai', 'suggestion', 'other')", name="ck_feedback_category"),
        Index("ix_feedback_tenant_created", "tenant_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True, nullable=False)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    contact: Mapped[str | None] = mapped_column(String(320), nullable=True)
    route: Mapped[str | None] = mapped_column(String(500), nullable=True)
    task_id: Mapped[str | None] = mapped_column(ForeignKey("tasks.id", ondelete="SET NULL"), index=True, nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    app_version: Mapped[str] = mapped_column(String(50), nullable=False)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped[User] = relationship(back_populates="feedback_items")
    tenant: Mapped[Tenant] = relationship(back_populates="feedback_items")
    task: Mapped[Task | None] = relationship(back_populates="feedback_items")


class Template(Base):
    __tablename__ = "templates"
    __table_args__ = (
        CheckConstraint("scope IN ('platform', 'tenant')", name="ck_templates_scope"),
        CheckConstraint(
            "(scope = 'platform' AND tenant_id IS NULL) OR (scope = 'tenant' AND tenant_id IS NOT NULL)",
            name="ck_templates_scope_tenant",
        ),
        UniqueConstraint("tenant_id", "template_id", "version", name="uq_templates_tenant_identity"),
        Index(
            "uq_templates_platform_identity",
            "template_id",
            "version",
            unique=True,
            sqlite_where=text("scope = 'platform'"),
            postgresql_where=text("scope = 'platform'"),
        ),
        Index("ix_templates_scope_tenant", "scope", "tenant_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    scope: Mapped[str] = mapped_column(String(50), nullable=False, default="platform", index=True)
    tenant_id: Mapped[str | None] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True)
    template_id: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    school: Mapped[str] = mapped_column(String(200), nullable=False)
    document_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active", index=True)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    storage_locator: Mapped[str | None] = mapped_column(Text, nullable=True)
    template_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    original_filename: Mapped[str | None] = mapped_column(String(320), nullable=True)
    file_size: Mapped[int | None] = mapped_column(nullable=True)
    content_type: Mapped[str | None] = mapped_column(String(200), nullable=True)
    checksum: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    uploaded_by: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    template_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    tenant: Mapped[Tenant | None] = relationship(back_populates="templates")
