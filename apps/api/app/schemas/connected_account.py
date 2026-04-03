from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ConnectedAccountResponse(BaseModel):
    id: UUID
    provider: str
    provider_account_id: str
    provider_email: str | None
    display_name: str | None
    scopes: list | None
    token_expires_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class OAuthStartResponse(BaseModel):
    authorization_url: str
    state: str
