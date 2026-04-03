from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ProviderConfigSaveRequest(BaseModel):
    provider: str
    client_id: str
    client_secret: str
    extra_config: dict | None = None


class ProviderConfigResponse(BaseModel):
    id: UUID
    provider: str
    display_name: str
    is_configured: bool
    has_client_id: bool
    has_client_secret: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProviderStatusResponse(BaseModel):
    provider: str
    display_name: str
    is_configured: bool
    category: str
    description: str
    setup_url: str
    docs_url: str | None = None
