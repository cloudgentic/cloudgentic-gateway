"""Real-time anomaly detection — runs after every agent action."""
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import redis_client
from app.models.anomaly import AgentBaseline, AnomalyEvent, AnomalySettings


SENSITIVITY_SIGMA = {"low": 4.0, "medium": 3.0, "high": 2.0}


async def check_for_anomalies(
    db: AsyncSession,
    user_id: UUID,
    api_key_id: UUID,
    provider: str,
    action: str,
) -> AnomalyEvent | None:
    """Check if the current action is anomalous. Returns AnomalyEvent if detected, None otherwise."""
    # Get user settings
    result = await db.execute(
        select(AnomalySettings).where(AnomalySettings.user_id == user_id)
    )
    settings = result.scalar_one_or_none()
    if not settings or not settings.is_enabled:
        return None

    sigma = SENSITIVITY_SIGMA.get(settings.sensitivity, 3.0)
    now = datetime.now(timezone.utc)
    current_hour = now.hour

    # Increment hourly counter in Redis (always set expire to prevent orphaned keys)
    hour_key = f"cgw:anomaly:{user_id}:{api_key_id}:{provider}:{action}:h:{current_hour}"
    pipe = redis_client.pipeline()
    pipe.incr(hour_key)
    pipe.expire(hour_key, 3600)
    results = await pipe.execute()
    current_count = results[0]

    # Check burst (>10 actions in 60 seconds)
    burst_key = f"cgw:anomaly:burst:{api_key_id}:{provider}:{action}"
    pipe = redis_client.pipeline()
    pipe.incr(burst_key)
    pipe.expire(burst_key, 60)
    burst_results = await pipe.execute()
    burst_count = burst_results[0]

    if burst_count > 10:
        return await _create_anomaly(
            db, user_id, api_key_id, "burst", "high",
            {"action": f"{provider}.{action}", "count_in_60s": burst_count},
            settings,
        )

    # Get baseline
    result = await db.execute(
        select(AgentBaseline).where(
            AgentBaseline.api_key_id == api_key_id,
            AgentBaseline.provider == provider,
            AgentBaseline.action == action,
        )
    )
    baseline = result.scalar_one_or_none()

    if not baseline:
        # No baseline yet — check for new action anomaly
        # Only flag if the agent has baselines for OTHER actions (meaning it's established)
        result = await db.execute(
            select(AgentBaseline).where(AgentBaseline.api_key_id == api_key_id).limit(1)
        )
        if result.scalar_one_or_none():
            return await _create_anomaly(
                db, user_id, api_key_id, "new_action", "medium",
                {"action": f"{provider}.{action}", "message": "Agent called an action it has never used before"},
                settings,
            )
        return None

    # Rate spike check
    if baseline.stddev_hourly_count > 0 and baseline.avg_hourly_count > 0:
        threshold = baseline.avg_hourly_count + (sigma * baseline.stddev_hourly_count)
        if current_count > threshold:
            severity = "critical" if current_count > threshold * 2 else "high" if current_count > threshold * 1.5 else "medium"
            return await _create_anomaly(
                db, user_id, api_key_id, "rate_spike", severity,
                {
                    "action": f"{provider}.{action}",
                    "current_hourly_count": current_count,
                    "baseline_avg": round(baseline.avg_hourly_count, 2),
                    "baseline_stddev": round(baseline.stddev_hourly_count, 2),
                    "threshold": round(threshold, 2),
                },
                settings,
            )

    # Unusual hour check
    if baseline.typical_hours and current_hour not in baseline.typical_hours:
        return await _create_anomaly(
            db, user_id, api_key_id, "unusual_hour", "low",
            {
                "action": f"{provider}.{action}",
                "current_hour": current_hour,
                "typical_hours": baseline.typical_hours,
            },
            settings,
        )

    return None


async def _create_anomaly(
    db: AsyncSession,
    user_id: UUID,
    api_key_id: UUID,
    anomaly_type: str,
    severity: str,
    details: dict,
    settings: AnomalySettings,
) -> AnomalyEvent:
    """Create an anomaly event and optionally take auto-action."""
    auto_action = "notified"

    # Auto-pause on critical
    if severity == "critical" and settings.auto_pause_on_critical:
        from app.models.api_key import ApiKey
        result = await db.execute(select(ApiKey).where(ApiKey.id == api_key_id))
        key = result.scalar_one_or_none()
        if key:
            key.revoked_at = datetime.now(timezone.utc)
            auto_action = "paused_key"

    event = AnomalyEvent(
        user_id=user_id,
        api_key_id=api_key_id,
        anomaly_type=anomaly_type,
        severity=severity,
        details=details,
        auto_action_taken=auto_action,
    )
    db.add(event)
    await db.flush()

    return event
