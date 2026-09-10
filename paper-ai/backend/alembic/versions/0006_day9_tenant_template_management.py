"""Add managed tenant template storage metadata.

Revision ID: 0006_day9_tenant_template_management
Revises: 0005_day9_tenant_isolation
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0006_day9_tenant_template_management"
down_revision: Union[str, Sequence[str], None] = "0005_day9_tenant_isolation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("templates") as batch:
        batch.add_column(sa.Column("storage_locator", sa.Text(), nullable=True))
        batch.add_column(sa.Column("original_filename", sa.String(320), nullable=True))
        batch.add_column(sa.Column("file_size", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("content_type", sa.String(200), nullable=True))
        batch.add_column(sa.Column("checksum", sa.String(64), nullable=True))
        batch.add_column(sa.Column("uploaded_by", sa.String(36), nullable=True))
        batch.create_foreign_key("fk_templates_uploaded_by", "users", ["uploaded_by"], ["id"], ondelete="SET NULL")
    op.create_index("ix_templates_checksum", "templates", ["checksum"], unique=False)
    op.create_index("ix_templates_uploaded_by", "templates", ["uploaded_by"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_templates_uploaded_by", table_name="templates")
    op.drop_index("ix_templates_checksum", table_name="templates")
    with op.batch_alter_table("templates") as batch:
        batch.drop_constraint("fk_templates_uploaded_by", type_="foreignkey")
        batch.drop_column("uploaded_by")
        batch.drop_column("checksum")
        batch.drop_column("content_type")
        batch.drop_column("file_size")
        batch.drop_column("original_filename")
        batch.drop_column("storage_locator")
