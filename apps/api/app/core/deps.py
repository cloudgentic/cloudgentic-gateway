from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token, hash_api_key
from app.models.user import User
from app.models.api_key import ApiKey

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Extract and validate the current user from JWT token."""
    import jwt as pyjwt

    try:
        payload = decode_token(credentials.credentials)
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except pyjwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    result = await db.execute(select(User).where(User.id == UUID(user_id), User.deleted_at.is_(None)))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")

    # Check token was issued after last password change (JWT revocation)
    token_iat = payload.get("iat")
    if token_iat and user.password_changed_at:
        if token_iat < user.password_changed_at.timestamp():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalidated by password change")

    return user


async def require_2fa(user: Annotated[User, Depends(get_current_user)]) -> User:
    """Require that the user has completed 2FA setup."""
    if not user.totp_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="2FA setup required before accessing this resource",
        )
    return user


async def get_agent_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> tuple[User, ApiKey]:
    """Authenticate an agent via API key."""
    from datetime import datetime, timezone

    raw_key = credentials.credentials
    hashed = hash_api_key(raw_key)

    result = await db.execute(
        select(ApiKey).where(ApiKey.key_hash == hashed, ApiKey.revoked_at.is_(None))
    )
    api_key = result.scalar_one_or_none()

    if not api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")

    # Check expiration
    if api_key.expires_at and api_key.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key has expired")

    # Update last_used_at
    api_key.last_used_at = datetime.now(timezone.utc)

    result = await db.execute(select(User).where(User.id == api_key.user_id, User.deleted_at.is_(None)))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or disabled")

    return user, api_key
