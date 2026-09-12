"""Add authenticated controlled-beta feedback intake."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0013_beta_feedback"
down_revision: Union[str, Sequence[str], None] = "0012_day17_token_version"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "feedback",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("tenant_id", sa.String(length=36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category", sa.String(length=30), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("contact", sa.String(length=320), nullable=True),
        sa.Column("route", sa.String(length=500), nullable=True),
        sa.Column("task_id", sa.String(length=36), sa.ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column("app_version", sa.String(length=50), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("category IN ('bug', 'slow', 'format', 'ai', 'suggestion', 'other')", name="ck_feedback_category"),
    )
    op.create_index("ix_feedback_user_id", "feedback", ["user_id"])
    op.create_index("ix_feedback_tenant_id", "feedback", ["tenant_id"])
    op.create_index("ix_feedback_task_id", "feedback", ["task_id"])
    op.create_index("ix_feedback_request_id", "feedback", ["request_id"])
    op.create_index("ix_feedback_tenant_created", "feedback", ["tenant_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_feedback_tenant_created", table_name="feedback")
    op.drop_index("ix_feedback_request_id", table_name="feedback")
    op.drop_index("ix_feedback_task_id", table_name="feedback")
    op.drop_index("ix_feedback_tenant_id", table_name="feedback")
    op.drop_index("ix_feedback_user_id", table_name="feedback")
    op.drop_table("feedback")
