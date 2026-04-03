"""Webhook subscription and event management endpoints."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_2fa
from app.models.user import User
from app.models.webhook import WebhookSubscription, WebhookEvent
from app.schemas.webhook import (
    WebhookSubscriptionCreate,
    WebhookSubscriptionResponse,
    WebhookEventResponse,
)
from app.services.audit import log_action

router = APIRouter()


@router.post("/subscribe", response_model=WebhookSubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook_subscription(
    request: WebhookSubscriptionCreate,
    user: User = Depends(require_2fa),
    db: AsyncSession = Depends(get_db),
):
    """Create a new webhook subscription."""
    subscription = WebhookSubscription(
        user_id=user.id,
        connected_account_id=request.connected_account_id,
        event_type=request.event_type,
        callback_url=request.callback_url,
        callback_agent_key_id=request.callback_agent_key_id,
        filter_config=request.filter_config,
        is_active=request.is_active,
        expires_at=request.expires_at,
    )
    db.add(subscription)
    await db.flush()

    await log_action(
        db, user_id=user.id, action="webhook.subscribe",
        resource_type="webhook_subscription", resource_id=str(subscription.id),
        detail=f"Subscribed to event: {request.event_type}",
    )

    return subscription


@router.get("/", response_model=list[WebhookSubscriptionResponse])
async def list_webhook_subscriptions(
    user: User = Depends(require_2fa),
    db: AsyncSession = Depends(get_db),
    is_active: bool | None = Query(None),
):
    """List all webhook subscriptions for the current user."""
    query = select(WebhookSubscription).where(
        WebhookSubscription.user_id == user.id
    ).order_by(WebhookSubscription.created_at.desc())

    if is_active is not None:
        query = query.where(WebhookSubscription.is_active == is_active)

    result = await db.execute(query)
    return result.scalars().all()


@router.delete("/{subscription_id}")
async def delete_webhook_subscription(
    subscription_id: UUID,
    user: User = Depends(require_2fa),
    db: AsyncSession = Depends(get_db),
):
    """Delete a webhook subscription."""
    result = await db.execute(
        select(WebhookSubscription).where(
            WebhookSubscription.id == subscription_id,
            WebhookSubscription.user_id == user.id,
        )
    )
    subscription = result.scalar_one_or_none()
    if not subscription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook subscription not found")

    await db.delete(subscription)
    await db.flush()

    await log_action(
        db, user_id=user.id, action="webhook.unsubscribe",
        resource_type="webhook_subscription", resource_id=str(subscription_id),
    )

    return {"message": "Webhook subscription deleted"}


@router.get("/{subscription_id}/events", response_model=list[WebhookEventResponse])
async def list_webhook_events(
    subscription_id: UUID,
    user: User = Depends(require_2fa),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
):
    """List events for a specific webhook subscription."""
    # Verify ownership
    sub_result = await db.execute(
        select(WebhookSubscription).where(
            WebhookSubscription.id == subscription_id,
            WebhookSubscription.user_id == user.id,
        )
    )
    if not sub_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook subscription not found")

    result = await db.execute(
        select(WebhookEvent)
        .where(WebhookEvent.subscription_id == subscription_id)
        .order_by(WebhookEvent.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return result.scalars().all()
