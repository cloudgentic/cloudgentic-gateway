from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class RateLimitInfo(BaseModel):
    rule_id: UUID
    rule_name: str
    max_requests: int
    window_seconds: int
    current_count: int
    remaining: int
    resets_in_seconds: int | None = None


class ProviderAccountHealth(BaseModel):
    account_id: UUID
    provider: str
    provider_email: str | None
    display_name: str | None
    token_status: str  # valid, expired, missing
    token_expires_at: datetime | None
    last_action: str | None = None
    last_action_at: datetime | None = None
    last_action_status: str | None = None
    rate_limits: list[RateLimitInfo] = []


class ProviderHealthResponse(BaseModel):
    accounts: list[ProviderAccountHealth]
    total_accounts: int
