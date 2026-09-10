"""Add Day10 member governance invitations.

Revision ID: 0008_day10_member_governance
Revises: 0007_day10_membership_rbac
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0008_day10_member_governance"
down_revision: Union[str, Sequence[str], None] = "0007_day10_membership_rbac"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tenant_invitations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("role IN ('admin', 'member')", name="ck_tenant_invitations_role"),
        sa.CheckConstraint("status IN ('pending', 'accepted', 'revoked', 'expired')", name="ck_tenant_invitations_status"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash", name="uq_tenant_invitations_token_hash"),
    )
    op.create_index("ix_tenant_invitations_tenant_status", "tenant_invitations", ["tenant_id", "status"], unique=False)
    op.create_index("ix_tenant_invitations_email", "tenant_invitations", ["email"], unique=False)
    op.create_index("ix_tenant_invitations_status", "tenant_invitations", ["status"], unique=False)
    op.create_index("ix_tenant_invitations_tenant_id", "tenant_invitations", ["tenant_id"], unique=False)
    op.create_index("ix_tenant_invitations_created_by", "tenant_invitations", ["created_by"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_tenant_invitations_created_by", table_name="tenant_invitations")
    op.drop_index("ix_tenant_invitations_tenant_id", table_name="tenant_invitations")
    op.drop_index("ix_tenant_invitations_status", table_name="tenant_invitations")
    op.drop_index("ix_tenant_invitations_email", table_name="tenant_invitations")
    op.drop_index("ix_tenant_invitations_tenant_status", table_name="tenant_invitations")
    op.drop_table("tenant_invitations")
