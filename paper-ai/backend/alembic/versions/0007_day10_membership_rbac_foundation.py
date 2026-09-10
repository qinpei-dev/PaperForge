"""Add Day10 membership RBAC foundation.

Revision ID: 0007_day10_membership_rbac
Revises: 0006_day9_tenant_template_management
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0007_day10_membership_rbac"
down_revision: Union[str, Sequence[str], None] = "0006_day9_tenant_template_management"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Day9 already created personal owner memberships. This migration preserves
    # them and only widens the fixed role set for the multi-user foundation.
    with op.batch_alter_table("tenant_memberships") as batch:
        batch.drop_constraint("ck_tenant_memberships_role", type_="check")
        batch.create_check_constraint("ck_tenant_memberships_role", "role IN ('owner', 'admin', 'member')")
        batch.add_column(sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_tenant_memberships_tenant_role", "tenant_memberships", ["tenant_id", "role"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_tenant_memberships_tenant_role", table_name="tenant_memberships")
    with op.batch_alter_table("tenant_memberships") as batch:
        batch.drop_constraint("ck_tenant_memberships_role", type_="check")
        batch.create_check_constraint("ck_tenant_memberships_role", "role IN ('owner', 'member')")
        batch.drop_column("updated_at")
