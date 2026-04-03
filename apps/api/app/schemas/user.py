from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    display_name: str | None
    is_active: bool
    is_admin: bool
    totp_enabled: bool
    setup_complete: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdateRequest(BaseModel):
    display_name: str | None = None


class SetupStatusResponse(BaseModel):
    has_admin: bool
    setup_complete: bool
