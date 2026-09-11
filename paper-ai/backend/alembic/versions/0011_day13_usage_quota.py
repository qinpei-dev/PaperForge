"""Add tenant usage ledger and monthly Agent-run quotas."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0011_day13_usage_quota"
down_revision: Union[str, Sequence[str], None] = "0010_day11_durable_task_runtime"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "quotas",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("monthly_limit", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("monthly_limit >= 0", name="ck_quotas_monthly_limit_nonnegative"),
        sa.UniqueConstraint("tenant_id", name="uq_quotas_tenant"),
    )
    op.create_index("ix_quotas_tenant_id", "quotas", ["tenant_id"], unique=False)

    op.create_table(
        "usage_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("task_id", sa.String(36), sa.ForeignKey("tasks.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("metric", sa.String(100), nullable=False, server_default="agent_run"),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("quantity > 0", name="ck_usage_records_quantity_positive"),
        sa.UniqueConstraint("task_id", "metric", name="uq_usage_records_task_metric"),
    )
    op.create_index("ix_usage_records_tenant_id", "usage_records", ["tenant_id"], unique=False)
    op.create_index("ix_usage_records_user_id", "usage_records", ["user_id"], unique=False)
    op.create_index("ix_usage_records_task_id", "usage_records", ["task_id"], unique=False)
    op.create_index("ix_usage_records_period_start", "usage_records", ["period_start"], unique=False)
    op.create_index("ix_usage_records_tenant_period", "usage_records", ["tenant_id", "period_start"], unique=False)

    # Existing tenants receive the same default quota as new tenants.  The
    # service also lazily creates a row for tenants created outside the API.
    op.execute(
        sa.text(
            "INSERT INTO quotas (id, tenant_id, monthly_limit) "
            "SELECT lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-' || "
            "lower(hex(randomblob(2))) || '-' || lower(hex(randomblob(2))) || '-' || lower(hex(randomblob(6))), "
            "t.id, 100 FROM tenants t WHERE NOT EXISTS "
            "(SELECT 1 FROM quotas q WHERE q.tenant_id = t.id)"
        )
    ) if op.get_bind().dialect.name == "sqlite" else op.execute(
        sa.text(
            "INSERT INTO quotas (id, tenant_id, monthly_limit) "
            "SELECT md5(random()::text || clock_timestamp()::text || t.id), t.id, 100 "
            "FROM tenants t WHERE NOT EXISTS "
            "(SELECT 1 FROM quotas q WHERE q.tenant_id = t.id)"
        )
    )


def downgrade() -> None:
    op.drop_index("ix_usage_records_tenant_period", table_name="usage_records")
    op.drop_index("ix_usage_records_period_start", table_name="usage_records")
    op.drop_index("ix_usage_records_task_id", table_name="usage_records")
    op.drop_index("ix_usage_records_user_id", table_name="usage_records")
    op.drop_index("ix_usage_records_tenant_id", table_name="usage_records")
    op.drop_table("usage_records")
    op.drop_index("ix_quotas_tenant_id", table_name="quotas")
    op.drop_table("quotas")
