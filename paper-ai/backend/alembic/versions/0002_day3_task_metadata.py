"""Add paper name and score history fields for the Day 3 task experience."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002_day3_task_metadata"
down_revision: Union[str, Sequence[str], None] = "0001_initial_saas_models"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tasks", sa.Column("paper_name", sa.String(320), nullable=True))
    op.add_column("tasks", sa.Column("before_score", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("tasks", "before_score")
    op.drop_column("tasks", "paper_name")
