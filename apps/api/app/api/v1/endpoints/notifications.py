"""Notification settings and test endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_2fa
from app.models.notification import NotificationSettings
from app.models.user import User
from app.schemas.notification import (
    NotificationSettingsResponse,
    NotificationSettingsUpdate,
    NotificationTestResponse,
)
from app.services.audit import log_action

router = APIRouter()


@router.get("/settings", response_model=NotificationSettingsResponse)
async def get_notification_settings(
    user: User = Depends(require_2fa),
    db: AsyncSession = Depends(get_db),
):
    """Get notification settings for the current user. Creates defaults if none exist."""
    result = await db.execute(
        select(NotificationSettings).where(NotificationSettings.user_id == user.id)
    )
    settings = result.scalar_one_or_none()

    if not settings:
        # Create default settings
        settings = NotificationSettings(user_id=user.id)
        db.add(settings)
        await db.flush()

    return settings


@router.put("/settings", response_model=NotificationSettingsResponse)
async def update_notification_settings(
    request: NotificationSettingsUpdate,
    user: User = Depends(require_2fa),
    db: AsyncSession = Depends(get_db),
):
    """Update notification settings for the current user."""
    result = await db.execute(
        select(NotificationSettings).where(NotificationSettings.user_id == user.id)
    )
    settings = result.scalar_one_or_none()

    if not settings:
        settings = NotificationSettings(user_id=user.id)
        db.add(settings)
        await db.flush()

    update_data = request.model_dump(exclude_unset=True)
    # Handle nested Pydantic models — serialize to dict for JSONB columns
    if "event_preferences" in update_data and update_data["event_preferences"] is not None:
        update_data["event_preferences"] = request.event_preferences.model_dump()
    if "quiet_hours" in update_data and update_data["quiet_hours"] is not None:
        update_data["quiet_hours"] = request.quiet_hours.model_dump()

    for field, value in update_data.items():
        setattr(settings, field, value)
    await db.flush()

    await log_action(
        db, user_id=user.id, action="notifications.settings.update",
        resource_type="notification_settings",
    )

    return settings


@router.post("/test/{channel}", response_model=NotificationTestResponse)
async def test_notification_channel(
    channel: str,
    user: User = Depends(require_2fa),
    db: AsyncSession = Depends(get_db),
):
    """Send a test notification to the specified channel."""
    valid_channels = {"email", "telegram", "discord", "webhook"}
    if channel not in valid_channels:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid channel. Must be one of: {', '.join(valid_channels)}",
        )

    result = await db.execute(
        select(NotificationSettings).where(NotificationSettings.user_id == user.id)
    )
    settings = result.scalar_one_or_none()
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification settings not configured. Update settings first.",
        )

    # Validate channel is configured
    if channel == "email" and not settings.email_enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email notifications not enabled")
    if channel == "telegram" and (not settings.telegram_enabled or not settings.telegram_chat_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Telegram notifications not configured")
    if channel == "discord" and (not settings.discord_enabled or not settings.discord_webhook_url):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Discord notifications not configured")
    if channel == "webhook" and (not settings.webhook_enabled or not settings.webhook_url):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Webhook notifications not configured")

    # Dispatch test notification via the notification manager
    from app.notifications.manager import NotificationManager
    manager = NotificationManager()
    success, detail = await manager.send_test(channel, settings)

    await log_action(
        db, user_id=user.id, action="notifications.test",
        detail=f"Test notification sent to {channel}: {'success' if success else 'failed'}",
    )

    return NotificationTestResponse(channel=channel, success=success, detail=detail)
