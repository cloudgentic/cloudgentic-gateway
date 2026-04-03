"""Notification settings table

Revision ID: 009
Revises: 008
Create Date: 2026-04-02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


DEFAULT_EVENT_PREFS = (
    '{"action_denied": true, "action_error": true, "anomaly_detected": true, '
    '"kill_switch_activated": true, "token_expiring": true, "rate_limit_warning": true}'
)
DEFAULT_QUIET_HOURS = '{"enabled": false, "start_hour": 22, "end_hour": 8, "timezone": "UTC"}'


def upgrade() -> None:
    op.create_table(
        "notification_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), unique=True, nullable=False),
        # Email
        sa.Column("email_enabled", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("email_address", sa.String(255), nullable=True),
        # Telegram
        sa.Column("telegram_enabled", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("telegram_chat_id", sa.String(255), nullable=True),
        # Discord
        sa.Column("discord_enabled", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("discord_webhook_url", sa.Text, nullable=True),
        # Webhook
        sa.Column("webhook_enabled", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("webhook_url", sa.Text, nullable=True),
        # Event preferences
        sa.Column("event_preferences", postgresql.JSONB, nullable=False, server_default=sa.text(f"'{DEFAULT_EVENT_PREFS}'")),
        # Quiet hours
        sa.Column("quiet_hours", postgresql.JSONB, nullable=False, server_default=sa.text(f"'{DEFAULT_QUIET_HOURS}'")),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("notification_settings")
