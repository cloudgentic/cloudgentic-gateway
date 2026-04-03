import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, UUIDMixin, TimestampMixin, SoftDeleteMixin


class Rule(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "rules"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Rule type: "rate_limit", "action_whitelist", "action_blacklist", "require_approval"
    rule_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # Conditions — when this rule applies
    # e.g., {"providers": ["google"], "actions": ["gmail.send"], "api_keys": ["uuid1"]}
    conditions: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Configuration — rule-specific config
    # rate_limit: {"max_requests": 100, "window_seconds": 3600}
    # action_whitelist: {"allowed_actions": ["gmail.read", "calendar.list"]}
    # action_blacklist: {"blocked_actions": ["gmail.send"]}
    # require_approval: {"notify_via": "email", "timeout_minutes": 60}
    config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Relationships
    user = relationship("User", back_populates="rules")
