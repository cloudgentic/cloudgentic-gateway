import uuid
from datetime import datetime

from sqlalchemy import Boolean, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, UUIDMixin, TimestampMixin, SoftDeleteMixin


class User(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # TOTP 2FA
    totp_secret: Mapped[str | None] = mapped_column(Text, nullable=True)
    totp_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # WebAuthn
    webauthn_credentials: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=list)

    # Security tracking
    password_changed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Setup tracking
    setup_complete: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships — lazy="noload" to avoid N+1 on every auth check
    connected_accounts = relationship("ConnectedAccount", back_populates="user", lazy="noload")
    api_keys = relationship("ApiKey", back_populates="user", lazy="noload")
    rules = relationship("Rule", back_populates="user", lazy="noload")
