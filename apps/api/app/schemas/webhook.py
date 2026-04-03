from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, HttpUrl, field_validator

from app.core.url_validator import validate_external_url


class WebhookSubscriptionCreate(BaseModel):
    connected_account_id: UUID | None = None
    event_type: str
    callback_url: str

    @field_validator("callback_url")
    @classmethod
    def validate_callback(cls, v: str) -> str:
        return validate_external_url(v)
    callback_agent_key_id: UUID | None = None
    filter_config: dict = {}
    is_active: bool = True
    expires_at: datetime | None = None


class WebhookSubscriptionResponse(BaseModel):
    id: UUID
    user_id: UUID
    connected_account_id: UUID | None
    event_type: str
    callback_url: str
    callback_agent_key_id: UUID | None
    filter_config: dict
    is_active: bool
    expires_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class WebhookEventResponse(BaseModel):
    id: UUID
    subscription_id: UUID
    user_id: UUID
    event_type: str
    payload: dict
    delivery_status: str  # pending, delivered, failed
    delivered_at: datetime | None
    delivery_attempts: int
    created_at: datetime

    model_config = {"from_attributes": True}
