import uuid

from sqlalchemy import Boolean, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, UUIDMixin, TimestampMixin


class ProviderConfig(Base, UUIDMixin, TimestampMixin):
    """Stores OAuth app credentials for each provider, encrypted at rest."""
    __tablename__ = "provider_configs"

    provider: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    client_id_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    client_secret_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_configured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    extra_config_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON string, encrypted
