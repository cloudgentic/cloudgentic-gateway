from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ApiKeyCreateRequest(BaseModel):
    name: str
    scopes: dict | None = None
    allowed_providers: list[str] | None = None
    expires_at: datetime | None = None


class ApiKeyCreateResponse(BaseModel):
    id: UUID
    name: str
    key: str  # Only shown once at creation
    key_prefix: str
    scopes: dict | None
    allowed_providers: list[str] | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ApiKeyResponse(BaseModel):
    id: UUID
    name: str
    key_prefix: str
    scopes: dict | None
    allowed_providers: list[str] | None
    last_used_at: datetime | None
    expires_at: datetime | None
    revoked_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
