"""Add per-user JWT token versioning for server-side revocation."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0012_day17_token_version"
down_revision: Union[str, Sequence[str], None] = "0011_day13_usage_quota"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("token_version", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    op.drop_column("users", "token_version")
