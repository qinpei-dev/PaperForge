"""Add durable task runtime metadata and replayable task events."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0010_day11_durable_task_runtime"
down_revision: Union[str, Sequence[str], None] = "0009_day10_ownership_audit_settings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tasks", sa.Column("progress", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("tasks", sa.Column("current_stage", sa.String(100), nullable=True))
    op.add_column("tasks", sa.Column("started_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("tasks", sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True))
    # SQLite rejects ADD COLUMN with CURRENT_TIMESTAMP as a non-constant
    # default.  Add/backfill there; PostgreSQL keeps the production contract.
    if op.get_bind().dialect.name == "sqlite":
        op.add_column("tasks", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))
        op.execute("UPDATE tasks SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL")
    else:
        op.add_column("tasks", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    op.add_column("tasks", sa.Column("error_code", sa.String(100), nullable=True))
    op.add_column("tasks", sa.Column("error_message", sa.Text(), nullable=True))
    op.add_column("tasks", sa.Column("input_metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'")))
    op.add_column("tasks", sa.Column("result_metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'")))
    op.add_column("tasks", sa.Column("worker_run_id", sa.String(64), nullable=True))
    op.add_column("tasks", sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("tasks", sa.Column("recovery_metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'")))
    op.add_column("tasks", sa.Column("state_version", sa.Integer(), nullable=False, server_default="1"))
    op.create_index("ix_tasks_worker_run_id", "tasks", ["worker_run_id"])
    op.create_table(
        "task_events",
        sa.Column("sequence", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("id", sa.String(36), nullable=False, unique=True),
        sa.Column("task_id", sa.String(36), sa.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("stage", sa.String(100), nullable=True),
        sa.Column("progress", sa.Integer(), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_task_events_task_id", "task_events", ["task_id"])
    op.create_index("ix_task_events_tenant_id", "task_events", ["tenant_id"])
    op.create_index("ix_task_events_task_sequence", "task_events", ["task_id", "sequence"], unique=True)
    op.create_index("ix_task_events_tenant_sequence", "task_events", ["tenant_id", "sequence"])


def downgrade() -> None:
    op.drop_index("ix_task_events_tenant_sequence", table_name="task_events")
    op.drop_index("ix_task_events_task_sequence", table_name="task_events")
    op.drop_index("ix_task_events_tenant_id", table_name="task_events")
    op.drop_index("ix_task_events_task_id", table_name="task_events")
    op.drop_table("task_events")
    op.drop_index("ix_tasks_worker_run_id", table_name="tasks")
    for name in ("state_version", "recovery_metadata", "attempt_count", "worker_run_id", "result_metadata", "input_metadata", "error_message", "error_code", "updated_at", "finished_at", "started_at", "current_stage", "progress"):
        op.drop_column("tasks", name)
