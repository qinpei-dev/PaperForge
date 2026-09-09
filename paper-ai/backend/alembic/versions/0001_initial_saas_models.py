"""create initial PaperForge SaaS metadata tables

Revision ID: 0001_initial_saas_models
Revises:
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial_saas_models"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table("users", sa.Column("id", sa.String(36), nullable=False), sa.Column("email", sa.String(320), nullable=False), sa.Column("password_hash", sa.String(255), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("email"))
    op.create_index("ix_users_email", "users", ["email"], unique=False)
    op.create_table("workspaces", sa.Column("id", sa.String(36), nullable=False), sa.Column("owner_id", sa.String(36), nullable=False), sa.Column("name", sa.String(200), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"), sa.PrimaryKeyConstraint("id"))
    op.create_index("ix_workspaces_owner_id", "workspaces", ["owner_id"], unique=False)
    op.create_table("projects", sa.Column("id", sa.String(36), nullable=False), sa.Column("workspace_id", sa.String(36), nullable=False), sa.Column("title", sa.String(300), nullable=False), sa.Column("status", sa.String(50), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"), sa.PrimaryKeyConstraint("id"))
    op.create_index("ix_projects_workspace_id", "projects", ["workspace_id"], unique=False)
    op.create_table("tasks", sa.Column("id", sa.String(36), nullable=False), sa.Column("project_id", sa.String(36), nullable=False), sa.Column("status", sa.String(50), nullable=False), sa.Column("uploaded_file", sa.Text(), nullable=True), sa.Column("agent_trace", sa.JSON(), nullable=True), sa.Column("score", sa.Float(), nullable=True), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"), sa.PrimaryKeyConstraint("id"))
    op.create_index("ix_tasks_project_id", "tasks", ["project_id"], unique=False)
    op.create_table("artifacts", sa.Column("id", sa.String(36), nullable=False), sa.Column("task_id", sa.String(36), nullable=False), sa.Column("file_path", sa.Text(), nullable=False), sa.Column("file_type", sa.String(100), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"), sa.PrimaryKeyConstraint("id"))
    op.create_index("ix_artifacts_task_id", "artifacts", ["task_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_artifacts_task_id", table_name="artifacts")
    op.drop_table("artifacts")
    op.drop_index("ix_tasks_project_id", table_name="tasks")
    op.drop_table("tasks")
    op.drop_index("ix_projects_workspace_id", table_name="projects")
    op.drop_table("projects")
    op.drop_index("ix_workspaces_owner_id", table_name="workspaces")
    op.drop_table("workspaces")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
