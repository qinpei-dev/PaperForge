"""Persist the current Agent workflow stage on SaaS tasks."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0003_day4_task_workflow_stage"
down_revision: Union[str, Sequence[str], None] = "0002_day3_task_metadata"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tasks", sa.Column("workflow_stage", sa.String(50), nullable=True))


def downgrade() -> None:
    op.drop_column("tasks", "workflow_stage")
