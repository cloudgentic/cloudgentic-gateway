"""Audit log export endpoint — streaming CSV download with date range filter."""
import csv
import io
from datetime import datetime
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_2fa
from app.models.audit_log import AuditLog
from app.models.user import User

router = APIRouter()

BATCH_SIZE = 1000
MAX_ROWS = 50000


@router.get("/export")
async def export_audit_logs(
    user: User = Depends(require_2fa),
    db: AsyncSession = Depends(get_db),
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    action: str | None = Query(None),
    provider: str | None = Query(None),
    status: str | None = Query(None),
    limit: int = Query(10000, le=MAX_ROWS),
):
    """Export audit logs as a streaming CSV file."""
    base_query = (
        select(AuditLog)
        .where(AuditLog.user_id == user.id)
        .order_by(AuditLog.timestamp.desc())
    )

    if start_date:
        base_query = base_query.where(AuditLog.timestamp >= start_date)
    if end_date:
        base_query = base_query.where(AuditLog.timestamp <= end_date)
    if action:
        base_query = base_query.where(AuditLog.action == action)
    if provider:
        base_query = base_query.where(AuditLog.provider == provider)
    if status:
        base_query = base_query.where(AuditLog.status == status)

    base_query = base_query.limit(limit)

    async def generate_csv() -> AsyncGenerator[str, None]:
        # Header
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "id", "timestamp", "action", "provider", "status",
            "resource_type", "resource_id", "api_key_id",
            "ip_address", "detail", "is_dry_run",
        ])
        yield output.getvalue()

        # Stream rows in batches
        offset = 0
        while offset < limit:
            batch_query = base_query.offset(offset).limit(BATCH_SIZE)
            result = await db.execute(batch_query)
            rows = result.scalars().all()

            if not rows:
                break

            output = io.StringIO()
            writer = csv.writer(output)
            for log in rows:
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
            yield output.getvalue()

            offset += len(rows)
            if len(rows) < BATCH_SIZE:
                break

    filename_parts = ["audit_export"]
    if start_date:
        filename_parts.append(f"from_{start_date.strftime('%Y%m%d')}")
    if end_date:
        filename_parts.append(f"to_{end_date.strftime('%Y%m%d')}")
    filename = "_".join(filename_parts) + ".csv"

    return StreamingResponse(
        generate_csv(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
