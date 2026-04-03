"""Anomaly detection endpoints."""
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_2fa
from app.models.anomaly import AnomalyEvent, AnomalySettings
from app.models.user import User
from app.schemas.anomaly import (
    AnomalyAcknowledgeRequest,
    AnomalyEventResponse,
    AnomalySettingsResponse,
    AnomalySettingsUpdateRequest,
)

router = APIRouter()


@router.get("/", response_model=list[AnomalyEventResponse])
async def list_anomalies(
    user: User = Depends(require_2fa),
    db: AsyncSession = Depends(get_db),
    severity: str | None = Query(None),
    api_key_id: UUID | None = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
):
    """List anomaly events."""
    query = (
        select(AnomalyEvent)
        .where(AnomalyEvent.user_id == user.id)
        .order_by(AnomalyEvent.created_at.desc())
    )
    if severity:
        query = query.where(AnomalyEvent.severity == severity)
    if api_key_id:
        query = query.where(AnomalyEvent.api_key_id == api_key_id)
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


@router.post("/{anomaly_id}/acknowledge")
async def acknowledge_anomaly(
    anomaly_id: UUID,
    request: AnomalyAcknowledgeRequest,
    user: User = Depends(require_2fa),
    db: AsyncSession = Depends(get_db),
):
    """Acknowledge an anomaly event."""
    result = await db.execute(
        select(AnomalyEvent).where(
            AnomalyEvent.id == anomaly_id,
            AnomalyEvent.user_id == user.id,
        )
    )
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Anomaly not found")

    event.acknowledged_at = datetime.now(timezone.utc)
    await db.flush()
    return {"status": "acknowledged"}


@router.get("/settings", response_model=AnomalySettingsResponse)
async def get_anomaly_settings(
    user: User = Depends(require_2fa),
    db: AsyncSession = Depends(get_db),
):
    """Get anomaly detection settings."""
    result = await db.execute(
        select(AnomalySettings).where(AnomalySettings.user_id == user.id)
    )
    settings = result.scalar_one_or_none()
    if not settings:
        settings = AnomalySettings(user_id=user.id)
        db.add(settings)
        await db.flush()
    return settings


@router.put("/settings", response_model=AnomalySettingsResponse)
async def update_anomaly_settings(
    request: AnomalySettingsUpdateRequest,
    user: User = Depends(require_2fa),
    db: AsyncSession = Depends(get_db),
):
    """Update anomaly detection settings."""
    result = await db.execute(
        select(AnomalySettings).where(AnomalySettings.user_id == user.id)
    )
    settings = result.scalar_one_or_none()
    if not settings:
        settings = AnomalySettings(user_id=user.id)
        db.add(settings)

    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(settings, field, value)
    await db.flush()
    return settings
