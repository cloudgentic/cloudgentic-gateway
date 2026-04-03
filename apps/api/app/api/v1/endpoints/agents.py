"""Agent-facing API endpoints for preflight checks and multi-agent overview.

- Preflight: authenticated via API key, returns environment health for agents
- Overview: authenticated via user session, returns all agents with 24h stats
"""
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_agent_user, require_2fa
from app.models.api_key import ApiKey
from app.models.audit_log import AuditLog
from app.models.connected_account import ConnectedAccount
from app.models.kill_switch import KillSwitchEvent
from app.models.rule import Rule
from app.models.user import User

router = APIRouter()


@router.get("/preflight")
async def agent_preflight(
    db: AsyncSession = Depends(get_db),
    agent: tuple[User, ApiKey] = Depends(get_agent_user),
):
    """Preflight check for agents. Returns connected account health, active rules,
    pending approvals, and kill switch status.

    Authenticated via API key (Bearer cgw_...).
    """
    user, api_key = agent
    now = datetime.now(timezone.utc)

    # Connected accounts health
    acct_result = await db.execute(
        select(ConnectedAccount).where(
            ConnectedAccount.user_id == user.id,
            ConnectedAccount.deleted_at.is_(None),
        )
    )
    accounts = acct_result.scalars().all()

    accounts_health = []
    for acct in accounts:
        if not acct.access_token_encrypted:
            token_status = "missing"
        elif acct.token_expires_at and acct.token_expires_at < now:
            token_status = "expired"
        else:
            token_status = "valid"

        accounts_health.append({
            "account_id": str(acct.id),
            "provider": acct.provider,
            "provider_email": acct.provider_email,
            "token_status": token_status,
            "token_expires_at": acct.token_expires_at.isoformat() if acct.token_expires_at else None,
        })

    # Active rules
    rules_result = await db.execute(
        select(Rule).where(
            Rule.user_id == user.id,
            Rule.is_enabled.is_(True),
            Rule.deleted_at.is_(None),
        ).order_by(Rule.priority.desc())
    )
    active_rules = [
        {
            "id": str(r.id),
            "name": r.name,
            "rule_type": r.rule_type,
            "priority": r.priority,
        }
        for r in rules_result.scalars().all()
    ]

    # Pending approvals — audit logs with status "denied" and require_approval reason in last 24h
    approval_cutoff = now - timedelta(hours=24)
    approvals_result = await db.execute(
        select(sa_func.count()).select_from(AuditLog).where(
            AuditLog.user_id == user.id,
            AuditLog.status == "denied",
            AuditLog.detail.ilike("%requires approval%"),
            AuditLog.timestamp >= approval_cutoff,
        )
    )
    pending_approvals = approvals_result.scalar() or 0

    # Kill switch status
    kill_switch_active = user.kill_switch_activated_at is not None

    last_kill = None
    if kill_switch_active:
        ks_result = await db.execute(
            select(KillSwitchEvent).where(
                KillSwitchEvent.user_id == user.id,
            ).order_by(KillSwitchEvent.created_at.desc()).limit(1)
        )
        ks_event = ks_result.scalar_one_or_none()
        if ks_event:
            last_kill = {
                "activated_at": ks_event.created_at.isoformat(),
                "trigger_source": ks_event.trigger_source,
                "reason": ks_event.reason,
            }

    return {
        "status": "ready" if not kill_switch_active else "kill_switch_active",
        "api_key": {
            "id": str(api_key.id),
            "name": api_key.name,
            "allowed_providers": api_key.allowed_providers,
        },
        "connected_accounts": accounts_health,
        "active_rules": active_rules,
        "pending_approvals": pending_approvals,
        "kill_switch": {
            "active": kill_switch_active,
            "details": last_kill,
        },
        "checked_at": now.isoformat(),
    }


@router.get("/overview")
async def agents_overview(
    user: User = Depends(require_2fa),
    db: AsyncSession = Depends(get_db),
):
    """Multi-agent dashboard overview. Returns all API keys (agents) with 24h activity stats.

    Authenticated via user session (Bearer JWT).
    """
    now = datetime.now(timezone.utc)
    cutoff_24h = now - timedelta(hours=24)

    # Fetch all API keys for the user (not revoked)
    keys_result = await db.execute(
        select(ApiKey).where(
            ApiKey.user_id == user.id,
            ApiKey.revoked_at.is_(None),
        ).order_by(ApiKey.created_at.desc())
    )
    api_keys = keys_result.scalars().all()

    agents = []
    for key in api_keys:
        # 24h stats for this API key
        stats_result = await db.execute(
            select(
                sa_func.count().label("total_actions"),
                sa_func.count().filter(AuditLog.status == "success").label("success_count"),
                sa_func.count().filter(AuditLog.status == "denied").label("denied_count"),
                sa_func.count().filter(AuditLog.status == "error").label("error_count"),
                sa_func.count().filter(AuditLog.status == "dry_run").label("dry_run_count"),
            ).select_from(AuditLog).where(
                AuditLog.api_key_id == key.id,
                AuditLog.timestamp >= cutoff_24h,
            )
        )
        stats = stats_result.one()

        # Last action
        last_action_result = await db.execute(
            select(AuditLog).where(
                AuditLog.api_key_id == key.id,
            ).order_by(AuditLog.timestamp.desc()).limit(1)
        )
        last_log = last_action_result.scalar_one_or_none()

        # Top actions in 24h
        top_actions_result = await db.execute(
            select(AuditLog.action, sa_func.count().label("count"))
            .where(
                AuditLog.api_key_id == key.id,
                AuditLog.timestamp >= cutoff_24h,
            )
            .group_by(AuditLog.action)
            .order_by(sa_func.count().desc())
            .limit(5)
        )
        top_actions = [
            {"action": row.action, "count": row.count}
            for row in top_actions_result.all()
        ]

        agents.append({
            "api_key_id": str(key.id),
            "name": key.name,
            "key_prefix": key.key_prefix,
            "allowed_providers": key.allowed_providers,
            "created_at": key.created_at.isoformat(),
            "last_used_at": key.last_used_at.isoformat() if key.last_used_at else None,
            "expires_at": key.expires_at.isoformat() if key.expires_at else None,
            "stats_24h": {
                "total_actions": stats.total_actions,
                "success": stats.success_count,
                "denied": stats.denied_count,
                "errors": stats.error_count,
                "dry_runs": stats.dry_run_count,
            },
            "last_action": {
                "action": last_log.action,
                "status": last_log.status,
                "timestamp": last_log.timestamp.isoformat(),
                "provider": last_log.provider,
            } if last_log else None,
            "top_actions_24h": top_actions,
        })

    return {
        "total_agents": len(agents),
        "agents": agents,
        "generated_at": now.isoformat(),
    }
