from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_2fa
from app.core.redis import redis_client
from app.models.audit_log import AuditLog
from app.models.connected_account import ConnectedAccount
from app.models.rule import Rule
from app.models.user import User
from app.schemas.health import ProviderAccountHealth, ProviderHealthResponse, RateLimitInfo

router = APIRouter()


@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "cloudgentic-gateway"}


@router.get("/health/providers", response_model=ProviderHealthResponse)
async def provider_health(
    user: User = Depends(require_2fa),
    db: AsyncSession = Depends(get_db),
):
    """Get health status of all connected provider accounts.

    Includes token status, last action, and rate limit usage for each account.
    """
    # Fetch connected accounts
    result = await db.execute(
        select(ConnectedAccount).where(
            ConnectedAccount.user_id == user.id,
            ConnectedAccount.deleted_at.is_(None),
        )
    )
    accounts = result.scalars().all()

    account_health_list = []
    now = datetime.now(timezone.utc)

    for account in accounts:
        # Determine token status
        if not account.access_token_encrypted:
            token_status = "missing"
        elif account.token_expires_at and account.token_expires_at < now:
            token_status = "expired"
        else:
            token_status = "valid"

        # Get last action for this account from audit logs
        last_action_result = await db.execute(
            select(AuditLog)
            .where(
                AuditLog.user_id == user.id,
                AuditLog.provider == account.provider,
            )
            .order_by(AuditLog.timestamp.desc())
            .limit(1)
        )
        last_log = last_action_result.scalar_one_or_none()

        # Get rate limit rules and their current usage from Redis
        rate_limits = await _get_rate_limit_info(db, user.id, account.provider)

        account_health_list.append(
            ProviderAccountHealth(
                account_id=account.id,
                provider=account.provider,
                provider_email=account.provider_email,
                display_name=account.display_name,
                token_status=token_status,
                token_expires_at=account.token_expires_at,
                last_action=last_log.action if last_log else None,
                last_action_at=last_log.timestamp if last_log else None,
                last_action_status=last_log.status if last_log else None,
                rate_limits=rate_limits,
            )
        )

    return ProviderHealthResponse(
        accounts=account_health_list,
        total_accounts=len(account_health_list),
    )


async def _get_rate_limit_info(db: AsyncSession, user_id, provider: str) -> list[RateLimitInfo]:
    """Fetch rate limit rules for a provider and check current usage in Redis."""
    result = await db.execute(
        select(Rule).where(
            Rule.user_id == user_id,
            Rule.rule_type == "rate_limit",
            Rule.is_enabled.is_(True),
            Rule.deleted_at.is_(None),
        )
    )
    rules = result.scalars().all()

    rate_limits = []
    for rule in rules:
        conditions = rule.conditions or {}
        # Only include rules that apply to this provider (or have no provider filter)
        rule_providers = conditions.get("providers", [])
        if rule_providers and provider not in rule_providers:
            continue

        config = rule.config or {}
        max_requests = config.get("max_requests", 100)
        window_seconds = config.get("window_seconds", 3600)

        # Check Redis for current count — scan for keys matching this rule
        # Rate limit keys follow the pattern: cgw:ratelimit:{rule_id}:{api_key_id}
        pattern = f"cgw:ratelimit:{rule.id}:*"
        total_count = 0
        min_ttl = None

        try:
            async for key in redis_client.scan_iter(match=pattern, count=100):
                count_val = await redis_client.get(key)
                if count_val:
                    total_count += int(count_val)
                ttl = await redis_client.ttl(key)
                if ttl > 0 and (min_ttl is None or ttl < min_ttl):
                    min_ttl = ttl
        except Exception:
            pass  # Redis unavailable — report what we can

        rate_limits.append(
            RateLimitInfo(
                rule_id=rule.id,
                rule_name=rule.name,
                max_requests=max_requests,
                window_seconds=window_seconds,
                current_count=total_count,
                remaining=max(0, max_requests - total_count),
                resets_in_seconds=min_ttl,
            )
        )

    return rate_limits
