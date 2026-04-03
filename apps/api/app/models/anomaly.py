import uuid
from datetime import datetime

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AgentBaseline(Base):
    __tablename__ = "agent_baselines"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    api_key_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("api_keys.id"), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    avg_daily_count: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    stddev_daily_count: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    avg_hourly_count: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    stddev_hourly_count: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    max_daily_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    typical_hours: Mapped[list | None] = mapped_column(JSONB, default=list)
    typical_recipients: Mapped[list | None] = mapped_column(JSONB, default=list)
    last_computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class AnomalyEvent(Base):
    __tablename__ = "anomaly_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    api_key_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("api_keys.id"), nullable=False)
    anomaly_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(10), nullable=False)
    details: Mapped[dict] = mapped_column(JSONB, nullable=False)
    auto_action_taken: Mapped[str | None] = mapped_column(String(30), nullable=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)


class AnomalySettings(Base):
    __tablename__ = "anomaly_settings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sensitivity: Mapped[str] = mapped_column(String(10), nullable=False, default="medium")
    auto_pause_on_critical: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    auto_kill_switch_threshold: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notification_channels: Mapped[list] = mapped_column(JSONB, nullable=False, default=lambda: ["dashboard"])
    notification_webhook_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    notification_telegram_chat_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    notification_discord_webhook_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
