import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class NotificationSettings(Base):
    __tablename__ = "notification_settings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False
    )

    # Email
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    email_address: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Telegram
    telegram_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    telegram_chat_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Discord
    discord_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    discord_webhook_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Generic webhook
    webhook_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    webhook_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Event preferences (JSONB)
    event_preferences: Mapped[dict] = mapped_column(
        JSONB, nullable=False,
        default=lambda: {
            "action_denied": True,
            "action_error": True,
            "anomaly_detected": True,
            "kill_switch_activated": True,
            "token_expiring": True,
            "rate_limit_warning": True,
        },
    )

    # Quiet hours (JSONB)
    quiet_hours: Mapped[dict] = mapped_column(
        JSONB, nullable=False,
        default=lambda: {"enabled": False, "start_hour": 22, "end_hour": 8, "timezone": "UTC"},
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
