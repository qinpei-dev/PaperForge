"""Persist template registry resources for Day9-P1."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0004_day9_template_persistence"
down_revision: Union[str, Sequence[str], None] = "0003_day4_task_workflow_stage"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "templates",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("template_id", sa.String(200), nullable=False),
        sa.Column("version", sa.String(100), nullable=False),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("school", sa.String(200), nullable=False),
        sa.Column("document_type", sa.String(100), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("source", sa.String(100), nullable=False),
        sa.Column("template_path", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("template_id", "version", name="uq_templates_template_id_version"),
    )
    op.create_index("ix_templates_template_id", "templates", ["template_id"], unique=False)
    op.create_index("ix_templates_document_type", "templates", ["document_type"], unique=False)
    op.create_index("ix_templates_status", "templates", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_templates_status", table_name="templates")
    op.drop_index("ix_templates_document_type", table_name="templates")
    op.drop_index("ix_templates_template_id", table_name="templates")
    op.drop_table("templates")
