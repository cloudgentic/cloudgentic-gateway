"""Anomaly detection: baselines, events, settings tables

Revision ID: 006
Revises: 005
Create Date: 2026-04-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "agent_baselines",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("api_key_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("api_keys.id"), nullable=False, index=True),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("avg_daily_count", sa.Float, nullable=False, server_default="0"),
        sa.Column("stddev_daily_count", sa.Float, nullable=False, server_default="0"),
        sa.Column("avg_hourly_count", sa.Float, nullable=False, server_default="0"),
        sa.Column("stddev_hourly_count", sa.Float, nullable=False, server_default="0"),
        sa.Column("max_daily_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("typical_hours", postgresql.JSONB, server_default="[]"),
        sa.Column("typical_recipients", postgresql.JSONB, server_default="[]"),
        sa.Column("last_computed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("api_key_id", "provider", "action", name="uq_baseline_key_provider_action"),
    )

    op.create_table(
        "anomaly_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("api_key_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("api_keys.id"), nullable=False),
        sa.Column("anomaly_type", sa.String(50), nullable=False),
        sa.Column("severity", sa.String(10), nullable=False),
        sa.Column("details", postgresql.JSONB, nullable=False),
        sa.Column("auto_action_taken", sa.String(30), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
    )

    op.create_table(
        "anomaly_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), unique=True, nullable=False),
        sa.Column("is_enabled", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("sensitivity", sa.String(10), nullable=False, server_default="medium"),
        sa.Column("auto_pause_on_critical", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("auto_kill_switch_threshold", sa.Integer, nullable=True),
        sa.Column("notification_channels", postgresql.JSONB, nullable=False, server_default=sa.text("'[\"dashboard\"]'")),
        sa.Column("notification_webhook_url", sa.Text, nullable=True),
        sa.Column("notification_telegram_chat_id", sa.Text, nullable=True),
        sa.Column("notification_discord_webhook_url", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("anomaly_settings")
    op.drop_table("anomaly_events")
    op.drop_table("agent_baselines")
