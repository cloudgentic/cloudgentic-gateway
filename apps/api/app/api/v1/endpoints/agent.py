"""Agent-facing API endpoints. Authenticated via API key (cgw_...)."""
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_agent_user
from app.models.api_key import ApiKey
from app.models.connected_account import ConnectedAccount
from app.models.user import User
from app.providers.google.service import GoogleService
from app.rules.engine import evaluate_rules
from app.schemas.agent import AgentExecuteRequest
from app.services.audit import log_action

router = APIRouter()


@router.post("/execute")
async def execute_action(
    body: AgentExecuteRequest,
    db: AsyncSession = Depends(get_db),
    agent: tuple[User, ApiKey] = Depends(get_agent_user),
    x_gateway_dry_run: str | None = Header(None),
):
    """Execute an action on behalf of the user via their connected account."""
    user, api_key = agent
    is_dry_run = body.dry_run or (x_gateway_dry_run and x_gateway_dry_run.lower() == "true")

    # Check API key scope
    if api_key.allowed_providers and body.provider not in api_key.allowed_providers:
        await log_action(
            db, user_id=user.id, api_key_id=api_key.id,
            action=f"{body.service}.{body.action}", provider=body.provider,
            status="denied", detail="Provider not in API key scope",
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Provider not allowed for this API key")

    # Evaluate rules BEFORE token decryption
    action_str = f"{body.service}.{body.action}"
    rule_result = await evaluate_rules(db, user.id, api_key.id, body.provider, action_str)

    # Check if any dry_run rule matched
    if rule_result.rule_id:
        from app.models.rule import Rule
        rule_check = await db.execute(select(Rule).where(Rule.id == rule_result.rule_id))
        matched_rule = rule_check.scalar_one_or_none()
        if matched_rule and matched_rule.rule_type == "dry_run":
            is_dry_run = True

    if not rule_result.allowed and not is_dry_run:
        await log_action(
            db, user_id=user.id, api_key_id=api_key.id,
            action=action_str, provider=body.provider,
            status="denied", detail=f"Blocked by rule: {rule_result.reason}",
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=rule_result.reason)

    # Find connected account
    result = await db.execute(
        select(ConnectedAccount).where(
            ConnectedAccount.user_id == user.id,
            ConnectedAccount.provider == body.provider,
            ConnectedAccount.deleted_at.is_(None),
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No connected {body.provider} account")

    # Dry-run mode: return what would be executed without calling the external API
    if is_dry_run:
        token_status = "valid"
        if not account.access_token_encrypted:
            token_status = "missing"
        elif account.token_expires_at:
            from datetime import datetime, timezone
            if account.token_expires_at < datetime.now(timezone.utc):
                token_status = "expired"

        await log_action(
            db, user_id=user.id, api_key_id=api_key.id,
            action=action_str, provider=body.provider,
            status="dry_run",
            request_summary={"service": body.service, "action": body.action, "params": body.params},
        )

        return {
            "status": "dry_run",
            "would_execute": {
                "provider": body.provider,
                "service": body.service,
                "action": body.action,
                "params": body.params,
            },
            "rules_evaluated": rule_result.allowed,
            "token_status": token_status,
        }

    # Execute the action
    try:
        if body.provider == "google":
            google_svc = GoogleService(account, str(user.id), db=db)
            result_data = await google_svc.execute(body.service, body.action, body.params)
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown provider: {body.provider}")

        await log_action(
            db, user_id=user.id, api_key_id=api_key.id,
            action=action_str, provider=body.provider,
            resource_type="connected_account", resource_id=str(account.id),
            request_summary={"service": body.service, "action": body.action},
        )

        # Anomaly detection — check after successful action
        try:
            from app.security.anomaly_detector import check_for_anomalies
            await check_for_anomalies(db, user.id, api_key.id, body.provider, action_str)
        except Exception:
            pass  # Anomaly detection should never fail the action

        return {"status": "success", "data": result_data}

    except HTTPException:
        raise
    except Exception as e:
        await log_action(
            db, user_id=user.id, api_key_id=api_key.id,
            action=action_str, provider=body.provider,
            status="error", detail=str(e),
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Action execution failed")
