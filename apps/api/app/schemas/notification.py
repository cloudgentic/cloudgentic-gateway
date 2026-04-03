from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, field_validator

from app.core.url_validator import validate_external_url


class QuietHours(BaseModel):
    enabled: bool = False
    start_hour: int = 22  # 0-23
    end_hour: int = 8  # 0-23
    timezone: str = "UTC"


class EventPreferences(BaseModel):
    action_denied: bool = True
    action_error: bool = True
    anomaly_detected: bool = True
    kill_switch_activated: bool = True
    token_expiring: bool = True
    rate_limit_warning: bool = True


class NotificationSettingsResponse(BaseModel):
    user_id: UUID
    email_enabled: bool
    email_address: str | None
    telegram_enabled: bool
    telegram_chat_id: str | None
    discord_enabled: bool
    discord_webhook_url: str | None
    webhook_enabled: bool
    webhook_url: str | None
    event_preferences: EventPreferences
    quiet_hours: QuietHours
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NotificationSettingsUpdate(BaseModel):
    email_enabled: bool | None = None
    email_address: str | None = None
    telegram_enabled: bool | None = None
    telegram_chat_id: str | None = None
    discord_enabled: bool | None = None
    discord_webhook_url: str | None = None
    webhook_enabled: bool | None = None
    webhook_url: str | None = None
    event_preferences: EventPreferences | None = None
    quiet_hours: QuietHours | None = None

    @field_validator("discord_webhook_url", "webhook_url")
    @classmethod
    def validate_urls(cls, v: str | None) -> str | None:
        if v:
            return validate_external_url(v)
        return v


class NotificationTestRequest(BaseModel):
    message: str = "This is a test notification from CloudGentic Gateway."


class NotificationTestResponse(BaseModel):
    channel: str
    success: bool
    detail: str | None = None
