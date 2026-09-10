"""Add ownership lifecycle and tenant audit events."""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0009_day10_ownership_audit_settings"
down_revision: Union[str, Sequence[str], None] = "0008_day10_member_governance"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_index("uq_tenant_memberships_active_owner", "tenant_memberships", ["tenant_id"], unique=True, postgresql_where=sa.text("role = 'owner' AND status = 'active'"), sqlite_where=sa.text("role = 'owner' AND status = 'active'"))
    op.create_table("tenant_ownership_transfers", sa.Column("id", sa.String(36), primary_key=True), sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False), sa.Column("from_user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False), sa.Column("to_user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False), sa.Column("token_hash", sa.String(64), nullable=False), sa.Column("status", sa.String(50), nullable=False), sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("accepted_at", sa.DateTime(timezone=True)), sa.Column("cancelled_at", sa.DateTime(timezone=True)), sa.CheckConstraint("status IN ('pending', 'accepted', 'cancelled', 'expired')", name="ck_tenant_ownership_transfers_status"), sa.UniqueConstraint("token_hash", name="uq_tenant_ownership_transfers_token_hash"))
    op.create_index("ix_tenant_ownership_transfers_tenant_id", "tenant_ownership_transfers", ["tenant_id"]); op.create_index("ix_tenant_ownership_transfers_status", "tenant_ownership_transfers", ["status"])
    op.create_index("uq_tenant_ownership_transfers_pending", "tenant_ownership_transfers", ["tenant_id"], unique=True, postgresql_where=sa.text("status = 'pending'"), sqlite_where=sa.text("status = 'pending'"))
    op.create_table("tenant_audit_events", sa.Column("id", sa.String(36), primary_key=True), sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False), sa.Column("actor_user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL")), sa.Column("event_type", sa.String(100), nullable=False), sa.Column("target_type", sa.String(100)), sa.Column("target_id", sa.String(320)), sa.Column("metadata_json", sa.JSON(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_tenant_audit_events_tenant_id", "tenant_audit_events", ["tenant_id"]); op.create_index("ix_tenant_audit_events_event_type", "tenant_audit_events", ["event_type"]); op.create_index("ix_tenant_audit_events_tenant_created", "tenant_audit_events", ["tenant_id", "created_at"])

def downgrade() -> None:
    op.drop_index("ix_tenant_audit_events_tenant_created", table_name="tenant_audit_events"); op.drop_index("ix_tenant_audit_events_event_type", table_name="tenant_audit_events"); op.drop_index("ix_tenant_audit_events_tenant_id", table_name="tenant_audit_events"); op.drop_table("tenant_audit_events")
    op.drop_index("uq_tenant_ownership_transfers_pending", table_name="tenant_ownership_transfers"); op.drop_index("ix_tenant_ownership_transfers_status", table_name="tenant_ownership_transfers"); op.drop_index("ix_tenant_ownership_transfers_tenant_id", table_name="tenant_ownership_transfers"); op.drop_table("tenant_ownership_transfers")
    op.drop_index("uq_tenant_memberships_active_owner", table_name="tenant_memberships")
