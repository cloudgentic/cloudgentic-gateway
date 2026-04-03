from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_2fa
from app.core.security import generate_api_key, API_KEY_PREFIX
from app.models.api_key import ApiKey
from app.models.user import User
from app.schemas.api_key import ApiKeyCreateRequest, ApiKeyCreateResponse, ApiKeyResponse
from app.services.audit import log_action

router = APIRouter()


@router.post("/", response_model=ApiKeyCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    request: ApiKeyCreateRequest,
    user: User = Depends(require_2fa),
    db: AsyncSession = Depends(get_db),
):
    """Create a new agent API key. The raw key is only shown once."""
    raw_key, hashed_key = generate_api_key()

    api_key = ApiKey(
        user_id=user.id,
        name=request.name,
        key_prefix=raw_key[:12],  # "cgw_" + first 8 chars
        key_hash=hashed_key,
        scopes=request.scopes,
        allowed_providers=request.allowed_providers,
        expires_at=request.expires_at,
    )
    db.add(api_key)
    await db.flush()

    await log_action(
        db, user_id=user.id, action="api_key.create",
        resource_type="api_key", resource_id=str(api_key.id),
        detail=f"Created API key: {request.name}",
    )

    return ApiKeyCreateResponse(
        id=api_key.id,
        name=api_key.name,
        key=raw_key,
        key_prefix=api_key.key_prefix,
        scopes=api_key.scopes,
        allowed_providers=api_key.allowed_providers,
        created_at=api_key.created_at,
    )


@router.get("/", response_model=list[ApiKeyResponse])
async def list_api_keys(
    user: User = Depends(require_2fa),
    db: AsyncSession = Depends(get_db),
):
    """List all API keys for the current user."""
    result = await db.execute(
        select(ApiKey).where(ApiKey.user_id == user.id).order_by(ApiKey.created_at.desc())
    )
    return result.scalars().all()


@router.delete("/{key_id}")
async def revoke_api_key(
    key_id: UUID,
    user: User = Depends(require_2fa),
    db: AsyncSession = Depends(get_db),
):
    """Revoke an API key."""
    result = await db.execute(
        select(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == user.id)
    )
    api_key = result.scalar_one_or_none()
    if not api_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")

    if api_key.revoked_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="API key already revoked")

    api_key.revoked_at = datetime.now(timezone.utc)
    await db.flush()

    await log_action(
        db, user_id=user.id, action="api_key.revoke",
        resource_type="api_key", resource_id=str(api_key.id),
        detail=f"Revoked API key: {api_key.name}",
    )

    return {"message": "API key revoked"}
