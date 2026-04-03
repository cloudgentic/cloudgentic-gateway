from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.request_context import get_client_ip
from app.models.audit_log import AuditLog


async def log_action(
    db: AsyncSession,
    *,
    user_id: UUID | None = None,
    api_key_id: UUID | None = None,
    ip_address: str | None = None,
    action: str,
    resource_type: str | None = None,
    resource_id: str | None = None,
    provider: str | None = None,
    status: str = "success",
    detail: str | None = None,
    request_summary: dict | None = None,
) -> AuditLog:
    """Append an entry to the audit log. INSERT only — never update or delete.

    IP address is auto-captured from request context if not explicitly provided.
    """
    entry = AuditLog(
        user_id=user_id,
        api_key_id=api_key_id,
        ip_address=ip_address or get_client_ip(),
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        provider=provider,
        status=status,
        detail=detail,
        request_summary=request_summary,
    )
    db.add(entry)
    await db.flush()
    return entry
