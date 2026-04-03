"""Emergency kill switch — instantly revoke all agent access."""
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_key import ApiKey
from app.models.connected_account import ConnectedAccount
from app.models.kill_switch import KillSwitchEvent
from app.models.user import User
from app.services.audit import log_action


async def activate_kill_switch(
    db: AsyncSession,
    user: User,
    *,
    revoke_api_keys: bool = True,
    disconnect_accounts: bool = False,
    reason: str | None = None,
    trigger_source: str = "dashboard",
) -> KillSwitchEvent:
    """Activate the kill switch — revoke all agent API keys and optionally disconnect accounts."""
    now = datetime.now(timezone.utc)
    keys_revoked = 0
    tokens_revoked = 0

    # Revoke all active API keys
    if revoke_api_keys:
        result = await db.execute(
            select(ApiKey).where(
                ApiKey.user_id == user.id,
                ApiKey.revoked_at.is_(None),
            )
        )
        keys = result.scalars().all()
        for key in keys:
            key.revoked_at = now
            keys_revoked += 1

    # Disconnect all accounts (clear encrypted tokens)
    if disconnect_accounts:
        result = await db.execute(
            select(ConnectedAccount).where(
                ConnectedAccount.user_id == user.id,
                ConnectedAccount.deleted_at.is_(None),
            )
        )
        accounts = result.scalars().all()
        for account in accounts:
            account.access_token_encrypted = None
            account.refresh_token_encrypted = None
            account.deleted_at = now
            tokens_revoked += 1

    # Update user kill switch timestamp
    user.kill_switch_activated_at = now
    await db.flush()

    # Log event
    event = KillSwitchEvent(
        user_id=user.id,
        trigger_source=trigger_source,
        keys_revoked=keys_revoked,
        tokens_revoked=tokens_revoked,
        reason=reason,
    )
    db.add(event)
    await db.flush()

    await log_action(
        db,
        user_id=user.id,
        action="security.kill_switch_activated",
        resource_type="kill_switch_event",
        resource_id=str(event.id),
        detail=f"Kill switch activated via {trigger_source}. Keys revoked: {keys_revoked}, Tokens revoked: {tokens_revoked}. Reason: {reason or 'N/A'}",
    )

    return event


async def restore_keys(
    db: AsyncSession,
    user: User,
    key_ids: list[UUID],
) -> int:
    """Selectively restore revoked API keys."""
    restored = 0
    for key_id in key_ids:
        result = await db.execute(
            select(ApiKey).where(
                ApiKey.id == key_id,
                ApiKey.user_id == user.id,
                ApiKey.revoked_at.is_not(None),
            )
        )
        key = result.scalar_one_or_none()
        if key:
            key.revoked_at = None
            restored += 1

    if restored > 0:
        user.kill_switch_activated_at = None
        await db.flush()

        await log_action(
            db,
            user_id=user.id,
            action="security.kill_switch_restored",
            detail=f"Restored {restored} API keys",
        )

    return restored


async def get_kill_switch_status(db: AsyncSession, user: User) -> dict:
    """Get current kill switch status."""
    if not user.kill_switch_activated_at:
        return {"is_active": False, "activated_at": None}

    result = await db.execute(
        select(KillSwitchEvent)
        .where(KillSwitchEvent.user_id == user.id)
        .order_by(KillSwitchEvent.created_at.desc())
        .limit(1)
    )
    event = result.scalar_one_or_none()

    return {
        "is_active": True,
        "activated_at": user.kill_switch_activated_at,
        "trigger_source": event.trigger_source if event else None,
        "keys_revoked": event.keys_revoked if event else 0,
        "tokens_revoked": event.tokens_revoked if event else 0,
    }
