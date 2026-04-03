"""Audit log export endpoint — CSV download with date range filter."""
import csv
import io
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_2fa
from app.models.audit_log import AuditLog
from app.models.user import User

router = APIRouter()


@router.post("/export")
async def export_audit_logs(
    user: User = Depends(require_2fa),
    db: AsyncSession = Depends(get_db),
    start_date: datetime | None = Query(None, description="Start of date range (ISO 8601)"),
    end_date: datetime | None = Query(None, description="End of date range (ISO 8601)"),
    action: str | None = Query(None, description="Filter by action type"),
    provider: str | None = Query(None, description="Filter by provider"),
    status: str | None = Query(None, description="Filter by status"),
    limit: int = Query(10000, le=50000, description="Maximum rows to export"),
):
    """Export audit logs as a CSV file.

    Returns a streaming CSV download. Supports date range and field filtering.
    Maximum export size is 50,000 rows.
    """
    query = (
        select(AuditLog)
        .where(AuditLog.user_id == user.id)
        .order_by(AuditLog.timestamp.desc())
    )

    if start_date:
        query = query.where(AuditLog.timestamp >= start_date)
    if end_date:
        query = query.where(AuditLog.timestamp <= end_date)
    if action:
        query = query.where(AuditLog.action == action)
    if provider:
        query = query.where(AuditLog.provider == provider)
    if status:
        query = query.where(AuditLog.status == status)

    query = query.limit(limit)
    result = await db.execute(query)
    logs = result.scalars().all()

    # Generate CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # Header row
    writer.writerow([
        "id", "timestamp", "action", "provider", "status",
        "resource_type", "resource_id", "api_key_id",
        "ip_address", "detail", "is_dry_run",
    ])

    for log in logs:
        writer.writerow([
            str(log.id),
            log.timestamp.isoformat() if log.timestamp else "",
            log.action,
            log.provider or "",
            log.status,
            log.resource_type or "",
            log.resource_id or "",
            str(log.api_key_id) if log.api_key_id else "",
            log.ip_address or "",
            log.detail or "",
            log.is_dry_run,
        ])

    output.seek(0)

    # Generate filename with date range info
    filename_parts = ["audit_export"]
    if start_date:
        filename_parts.append(f"from_{start_date.strftime('%Y%m%d')}")
    if end_date:
        filename_parts.append(f"to_{end_date.strftime('%Y%m%d')}")
    filename = "_".join(filename_parts) + ".csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
