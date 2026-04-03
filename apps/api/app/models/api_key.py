import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, UUIDMixin, TimestampMixin


class ApiKey(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "api_keys"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(10), nullable=False)  # "cgw_" + first 8 chars
    key_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)

    # Scoped permissions
    scopes: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)
    # e.g., {"providers": ["google"], "actions": ["gmail.send", "calendar.read"]}

    allowed_providers: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=list)

    # Lifecycle
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="api_keys")
