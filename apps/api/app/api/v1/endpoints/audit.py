from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_2fa
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.audit import AuditLogResponse

router = APIRouter()


@router.get("/", response_model=list[AuditLogResponse])
async def list_audit_logs(
    user: User = Depends(require_2fa),
    db: AsyncSession = Depends(get_db),
    action: str | None = Query(None),
    provider: str | None = Query(None),
    status: str | None = Query(None),
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
):
    """Query audit logs for the current user."""
    query = (
        select(AuditLog)
        .where(AuditLog.user_id == user.id)
        .order_by(AuditLog.timestamp.desc())
    )

    if action:
        query = query.where(AuditLog.action == action)
    if provider:
        query = query.where(AuditLog.provider == provider)
    if status:
        query = query.where(AuditLog.status == status)
    if start_date:
        query = query.where(AuditLog.timestamp >= start_date)
    if end_date:
        query = query.where(AuditLog.timestamp <= end_date)

    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()
