from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class KillSwitchRequest(BaseModel):
    disconnect_accounts: bool = False
    reason: str | None = None
    # revoke_api_keys is always True — that's the whole point of the kill switch


class KillSwitchResponse(BaseModel):
    status: str
    keys_revoked: int
    tokens_revoked: int
    event_id: UUID
    message: str


class KillSwitchStatusResponse(BaseModel):
    is_active: bool
    activated_at: datetime | None
    trigger_source: str | None = None
    keys_revoked: int = 0
    tokens_revoked: int = 0


class KillSwitchRestoreRequest(BaseModel):
    restore_keys: list[UUID] = []


class SkillScanRequest(BaseModel):
    skill_name: str
    skill_md_content: str | None = None
    files: list[dict] | None = None


class SkillScanConcern(BaseModel):
    severity: str
    category: str
    description: str
    evidence: str | None = None
    line_number: int | None = None


class SkillScanResponse(BaseModel):
    risk_score: int
    risk_level: str
    concerns: list[SkillScanConcern]
    recommendations: list[str]
    scanned_at: datetime
