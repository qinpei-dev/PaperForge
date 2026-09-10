"""Add tenant context and resource isolation for Day9-P2.

Revision ID: 0005_day9_tenant_isolation
Revises: 0004_day9_template_persistence
"""

from typing import Sequence, Union
from uuid import NAMESPACE_URL, uuid5

from alembic import op
import sqlalchemy as sa


revision: str = "0005_day9_tenant_isolation"
down_revision: Union[str, Sequence[str], None] = "0004_day9_template_persistence"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _personal_tenant_id(user_id: str) -> str:
    return str(uuid5(NAMESPACE_URL, f"paperforge:personal-tenant:{user_id}"))


def _personal_membership_id(user_id: str) -> str:
    return str(uuid5(NAMESPACE_URL, f"paperforge:personal-membership:{user_id}"))


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("slug", sa.String(200), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("status IN ('active', 'disabled')", name="ck_tenants_status"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_tenants_slug", "tenants", ["slug"], unique=False)
    op.create_index("ix_tenants_status", "tenants", ["status"], unique=False)
    op.create_table(
        "tenant_memberships",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("role IN ('owner', 'member')", name="ck_tenant_memberships_role"),
        sa.CheckConstraint("status IN ('active', 'disabled')", name="ck_tenant_memberships_status"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "user_id", name="uq_tenant_memberships_tenant_user"),
    )
    op.create_index("ix_tenant_memberships_tenant_id", "tenant_memberships", ["tenant_id"], unique=False)
    op.create_index("ix_tenant_memberships_user_id", "tenant_memberships", ["user_id"], unique=False)
    op.create_index("ix_tenant_memberships_status", "tenant_memberships", ["status"], unique=False)

    connection = op.get_bind()
    users = connection.execute(sa.text("SELECT id, email FROM users ORDER BY id")).mappings().all()
    for user in users:
        user_id = str(user["id"])
        tenant_id = _personal_tenant_id(user_id)
        connection.execute(
            sa.text("INSERT INTO tenants (id, name, slug, status) VALUES (:id, :name, :slug, 'active')"),
            {"id": tenant_id, "name": f"{user['email']} Personal Tenant", "slug": f"personal-{user_id.lower()}"},
        )
        connection.execute(
            sa.text("INSERT INTO tenant_memberships (id, tenant_id, user_id, role, status) VALUES (:id, :tenant_id, :user_id, 'owner', 'active')"),
            {"id": _personal_membership_id(user_id), "tenant_id": tenant_id, "user_id": user_id},
        )

    with op.batch_alter_table("templates") as batch:
        batch.add_column(sa.Column("scope", sa.String(50), server_default="platform", nullable=False))
        batch.add_column(sa.Column("tenant_id", sa.String(36), nullable=True))
        batch.drop_constraint("uq_templates_template_id_version", type_="unique")
        batch.create_foreign_key("fk_templates_tenant_id", "tenants", ["tenant_id"], ["id"], ondelete="CASCADE")
        batch.create_check_constraint("ck_templates_scope", "scope IN ('platform', 'tenant')")
        batch.create_check_constraint("ck_templates_scope_tenant", "(scope = 'platform' AND tenant_id IS NULL) OR (scope = 'tenant' AND tenant_id IS NOT NULL)")
        batch.create_unique_constraint("uq_templates_tenant_identity", ["tenant_id", "template_id", "version"])
    connection.execute(sa.text("UPDATE templates SET scope = 'platform', tenant_id = NULL"))
    op.create_index("ix_templates_scope", "templates", ["scope"], unique=False)
    op.create_index("ix_templates_tenant_id", "templates", ["tenant_id"], unique=False)
    op.create_index("ix_templates_scope_tenant", "templates", ["scope", "tenant_id"], unique=False)
    op.create_index(
        "uq_templates_platform_identity",
        "templates",
        ["template_id", "version"],
        unique=True,
        sqlite_where=sa.text("scope = 'platform'"),
        postgresql_where=sa.text("scope = 'platform'"),
    )

    with op.batch_alter_table("tasks") as batch:
        batch.add_column(sa.Column("tenant_id", sa.String(36), nullable=True))
        batch.add_column(sa.Column("user_id", sa.String(36), nullable=True))
        batch.create_foreign_key("fk_tasks_tenant_id", "tenants", ["tenant_id"], ["id"], ondelete="RESTRICT")
        batch.create_foreign_key("fk_tasks_user_id", "users", ["user_id"], ["id"], ondelete="RESTRICT")
    task_owners = connection.execute(
        sa.text("SELECT tasks.id AS task_id, workspaces.owner_id AS user_id FROM tasks JOIN projects ON projects.id = tasks.project_id JOIN workspaces ON workspaces.id = projects.workspace_id")
    ).mappings().all()
    mapped_task_ids = set()
    for row in task_owners:
        task_id = str(row["task_id"])
        user_id = str(row["user_id"])
        connection.execute(
            sa.text("UPDATE tasks SET tenant_id = :tenant_id, user_id = :user_id WHERE id = :task_id"),
            {"tenant_id": _personal_tenant_id(user_id), "user_id": user_id, "task_id": task_id},
        )
        mapped_task_ids.add(task_id)
    all_task_ids = {str(row[0]) for row in connection.execute(sa.text("SELECT id FROM tasks")).all()}
    if all_task_ids != mapped_task_ids:
        raise RuntimeError("Cannot backfill tenant provenance for orphaned legacy tasks")
    with op.batch_alter_table("tasks") as batch:
        batch.alter_column("tenant_id", existing_type=sa.String(36), nullable=False)
        batch.alter_column("user_id", existing_type=sa.String(36), nullable=False)
    op.create_index("ix_tasks_tenant_id", "tasks", ["tenant_id"], unique=False)
    op.create_index("ix_tasks_user_id", "tasks", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_tasks_user_id", table_name="tasks")
    op.drop_index("ix_tasks_tenant_id", table_name="tasks")
    with op.batch_alter_table("tasks") as batch:
        batch.drop_constraint("fk_tasks_user_id", type_="foreignkey")
        batch.drop_constraint("fk_tasks_tenant_id", type_="foreignkey")
        batch.drop_column("user_id")
        batch.drop_column("tenant_id")
    op.drop_index("uq_templates_platform_identity", table_name="templates")
    op.drop_index("ix_templates_scope_tenant", table_name="templates")
    op.drop_index("ix_templates_tenant_id", table_name="templates")
    op.drop_index("ix_templates_scope", table_name="templates")
    with op.batch_alter_table("templates") as batch:
        batch.drop_constraint("uq_templates_tenant_identity", type_="unique")
        batch.drop_constraint("ck_templates_scope_tenant", type_="check")
        batch.drop_constraint("ck_templates_scope", type_="check")
        batch.drop_constraint("fk_templates_tenant_id", type_="foreignkey")
        batch.drop_column("tenant_id")
        batch.drop_column("scope")
        batch.create_unique_constraint("uq_templates_template_id_version", ["template_id", "version"])
    op.drop_index("ix_tenant_memberships_status", table_name="tenant_memberships")
    op.drop_index("ix_tenant_memberships_user_id", table_name="tenant_memberships")
    op.drop_index("ix_tenant_memberships_tenant_id", table_name="tenant_memberships")
    op.drop_table("tenant_memberships")
    op.drop_index("ix_tenants_status", table_name="tenants")
    op.drop_index("ix_tenants_slug", table_name="tenants")
    op.drop_table("tenants")
