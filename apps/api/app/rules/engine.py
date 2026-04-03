"""Rules engine — evaluates all active rules BEFORE token decryption."""
from dataclasses import dataclass
from uuid import UUID

import redis.asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import redis_client
from app.models.rule import Rule


@dataclass
class RuleResult:
    allowed: bool
    reason: str | None = None
    rule_id: UUID | None = None


async def evaluate_rules(
    db: AsyncSession,
    user_id: UUID,
    api_key_id: UUID,
    provider: str,
    action: str,
) -> RuleResult:
    """Evaluate all active rules for a given action. Deny wins over allow."""
    result = await db.execute(
        select(Rule)
        .where(
            Rule.user_id == user_id,
            Rule.is_enabled.is_(True),
            Rule.deleted_at.is_(None),
        )
        .order_by(Rule.priority.desc())
    )
    rules = result.scalars().all()

    for rule in rules:
        if not _matches_conditions(rule, provider, action, api_key_id):
            continue

        if rule.rule_type == "rate_limit":
            allowed = await _check_rate_limit(rule, user_id, api_key_id)
            if not allowed:
                return RuleResult(
                    allowed=False,
                    reason=f"Rate limit exceeded: {rule.name}",
                    rule_id=rule.id,
                )

        elif rule.rule_type == "action_blacklist":
            blocked = rule.config.get("blocked_actions", [])
            if action in blocked:
                return RuleResult(
                    allowed=False,
                    reason=f"Action blocked by rule: {rule.name}",
                    rule_id=rule.id,
                )

        elif rule.rule_type == "action_whitelist":
            allowed_actions = rule.config.get("allowed_actions", [])
            if allowed_actions and action not in allowed_actions:
                return RuleResult(
                    allowed=False,
                    reason=f"Action not in whitelist: {rule.name}",
                    rule_id=rule.id,
                )

        elif rule.rule_type == "require_approval":
            return RuleResult(
                allowed=False,
                reason=f"Action requires approval: {rule.name}",
                rule_id=rule.id,
            )

    return RuleResult(allowed=True)


def _matches_conditions(rule: Rule, provider: str, action: str, api_key_id: UUID) -> bool:
    """Check if a rule's conditions match the current request."""
    conditions = rule.conditions
    if not conditions:
        return True  # No conditions = matches everything

    # Check provider filter
    if "providers" in conditions and provider not in conditions["providers"]:
        return False

    # Check action filter
    if "actions" in conditions and action not in conditions["actions"]:
        return False

    # Check API key filter
    if "api_keys" in conditions and str(api_key_id) not in conditions["api_keys"]:
        return False

    return True


async def _check_rate_limit(rule: Rule, user_id: UUID, api_key_id: UUID) -> bool:
    """Check a rate limit rule using atomic Redis INCR."""
    config = rule.config
    max_requests = config.get("max_requests", 100)
    window_seconds = config.get("window_seconds", 3600)

    key = f"cgw:ratelimit:{rule.id}:{api_key_id}"

    # Atomic: increment first, then check — no race condition
    count = await redis_client.incr(key)
    if count == 1:
        # First request in this window — set the expiry
        await redis_client.expire(key, window_seconds)

    return count <= max_requests
