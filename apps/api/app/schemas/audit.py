from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    id: UUID
    timestamp: datetime
    user_id: UUID | None
    api_key_id: UUID | None
    ip_address: str | None
    action: str
    resource_type: str | None
    resource_id: str | None
    provider: str | None
    status: str
    detail: str | None
    request_summary: dict | None

    model_config = {"from_attributes": True}


class AuditLogQuery(BaseModel):
    action: str | None = None
    provider: str | None = None
    status: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    limit: int = 50
    offset: int = 0
