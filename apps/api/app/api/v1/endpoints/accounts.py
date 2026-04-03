from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_2fa
from app.models.connected_account import ConnectedAccount
from app.models.user import User
from app.providers.google.oauth import GoogleOAuth
from app.schemas.connected_account import ConnectedAccountResponse, OAuthStartResponse
from app.services.audit import log_action
from app.services.vault import store_tokens

router = APIRouter()


@router.get("/", response_model=list[ConnectedAccountResponse])
async def list_accounts(
    user: User = Depends(require_2fa),
    db: AsyncSession = Depends(get_db),
):
    """List all connected accounts."""
    result = await db.execute(
        select(ConnectedAccount).where(
            ConnectedAccount.user_id == user.id,
            ConnectedAccount.deleted_at.is_(None),
        )
    )
    return result.scalars().all()


@router.get("/{provider}/connect", response_model=OAuthStartResponse)
async def start_oauth(
    provider: str,
    user: User = Depends(require_2fa),
    db: AsyncSession = Depends(get_db),
):
    """Start OAuth flow for a provider."""
    if provider == "google":
        oauth = await GoogleOAuth.create(db)
        try:
            url, state = oauth.get_authorization_url()
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        return OAuthStartResponse(authorization_url=url, state=state)
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown provider: {provider}")


@router.get("/{provider}/callback")
async def oauth_callback(
    provider: str,
    code: str,
    state: str,
    request: Request,
    user: User = Depends(require_2fa),
    db: AsyncSession = Depends(get_db),
):
    """Handle OAuth callback from provider."""
    if provider == "google":
        oauth = await GoogleOAuth.create(db)
        token_data = await oauth.exchange_code(code)
        user_info = await oauth.get_user_info(token_data["access_token"])

        # Check if account already connected
        result = await db.execute(
            select(ConnectedAccount).where(
                ConnectedAccount.user_id == user.id,
                ConnectedAccount.provider == "google",
                ConnectedAccount.provider_account_id == user_info["id"],
                ConnectedAccount.deleted_at.is_(None),
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Update tokens
            await store_tokens(existing, token_data, str(user.id))
            await db.flush()
            await log_action(
                db, user_id=user.id, action="account.reconnected",
                resource_type="connected_account", resource_id=str(existing.id),
                provider="google",
            )
            return {"message": "Account reconnected", "account_id": str(existing.id)}

        account = ConnectedAccount(
            user_id=user.id,
            provider="google",
            provider_account_id=user_info["id"],
            provider_email=user_info.get("email"),
            display_name=user_info.get("name"),
            scopes=token_data.get("scope", "").split(),
        )
        await store_tokens(account, token_data, str(user.id))
        db.add(account)
        await db.flush()

        await log_action(
            db, user_id=user.id, action="account.connected",
            resource_type="connected_account", resource_id=str(account.id),
            provider="google",
        )

        return {"message": "Account connected", "account_id": str(account.id)}

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown provider: {provider}")


@router.delete("/{account_id}")
async def disconnect_account(
    account_id: UUID,
    user: User = Depends(require_2fa),
    db: AsyncSession = Depends(get_db),
):
    """Disconnect (soft-delete) a connected account."""
    from datetime import datetime, timezone

    result = await db.execute(
        select(ConnectedAccount).where(
            ConnectedAccount.id == account_id,
            ConnectedAccount.user_id == user.id,
            ConnectedAccount.deleted_at.is_(None),
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

    account.deleted_at = datetime.now(timezone.utc)
    account.access_token_encrypted = None
    account.refresh_token_encrypted = None
    await db.flush()

    await log_action(
        db, user_id=user.id, action="account.disconnected",
        resource_type="connected_account", resource_id=str(account.id),
        provider=account.provider,
    )

    return {"message": "Account disconnected"}
