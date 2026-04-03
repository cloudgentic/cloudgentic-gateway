from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class RuleCreateRequest(BaseModel):
    name: str
    description: str | None = None
    rule_type: str  # rate_limit, action_whitelist, action_blacklist, require_approval
    conditions: dict = {}
    config: dict = {}
    priority: int = 0
    is_enabled: bool = True


class RuleUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    conditions: dict | None = None
    config: dict | None = None
    priority: int | None = None
    is_enabled: bool | None = None


class RuleResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    rule_type: str
    conditions: dict
    config: dict
    priority: int
    is_enabled: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
