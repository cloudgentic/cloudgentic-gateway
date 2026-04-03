"""Kill switch events table + users column

Revision ID: 004
Revises: 003
Create Date: 2026-04-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("kill_switch_activated_at", sa.DateTime(timezone=True), nullable=True))

    op.create_table(
        "kill_switch_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("trigger_source", sa.String(20), nullable=False),
        sa.Column("keys_revoked", sa.Integer, nullable=False, server_default="0"),
        sa.Column("tokens_revoked", sa.Integer, nullable=False, server_default="0"),
        sa.Column("reason", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("kill_switch_events")
    op.drop_column("users", "kill_switch_activated_at")
