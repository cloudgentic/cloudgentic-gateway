import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, Text, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class KillSwitchEvent(Base):
    __tablename__ = "kill_switch_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    trigger_source: Mapped[str] = mapped_column(String(20), nullable=False)  # dashboard, api, mcp, anomaly_auto
    keys_revoked: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tokens_revoked: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
