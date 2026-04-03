from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, field_validator


class AnomalyEventResponse(BaseModel):
    id: UUID
    user_id: UUID
    api_key_id: UUID
    anomaly_type: str
    severity: str
    details: dict
    auto_action_taken: str | None
    acknowledged_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AnomalySettingsResponse(BaseModel):
    is_enabled: bool
    sensitivity: str
    auto_pause_on_critical: bool
    auto_kill_switch_threshold: int | None
    notification_channels: list

    model_config = {"from_attributes": True}


class AnomalySettingsUpdateRequest(BaseModel):
    is_enabled: bool | None = None
    sensitivity: str | None = None  # Must be: "low", "medium", or "high"

    @field_validator("sensitivity")
    @classmethod
    def validate_sensitivity(cls, v: str | None) -> str | None:
        if v and v not in ("low", "medium", "high"):
            raise ValueError("Sensitivity must be 'low', 'medium', or 'high'")
        return v
    auto_pause_on_critical: bool | None = None
    auto_kill_switch_threshold: int | None = None
    notification_channels: list | None = None


class AnomalyAcknowledgeRequest(BaseModel):
    note: str | None = None
