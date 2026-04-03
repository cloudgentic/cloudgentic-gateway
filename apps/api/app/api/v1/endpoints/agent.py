"""Agent-facing API endpoints. Authenticated via API key (cgw_...)."""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_agent_user
from app.models.api_key import ApiKey
from app.models.connected_account import ConnectedAccount
from app.models.user import User
from app.providers.google.service import GoogleService
from app.rules.engine import evaluate_rules
from app.services.audit import log_action

router = APIRouter()


@router.post("/execute")
async def execute_action(
    request: Request,
    db: AsyncSession = Depends(get_db),
    agent: tuple[User, ApiKey] = Depends(get_agent_user),
):
    """
    Execute an action on behalf of the user via their connected account.

    Body: {"provider": "google", "service": "gmail", "action": "send", "params": {...}}
    """
    user, api_key = agent
    body = await request.json()

    provider = body.get("provider")
    service = body.get("service")
    action = body.get("action")
    params = body.get("params", {})

    if not all([provider, service, action]):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="provider, service, and action are required")

    # Check API key scope
    if api_key.allowed_providers and provider not in api_key.allowed_providers:
        await log_action(
            db, user_id=user.id, api_key_id=api_key.id,
            action=f"{service}.{action}", provider=provider,
            status="denied", detail="Provider not in API key scope",
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Provider not allowed for this API key")

    # Evaluate rules BEFORE token decryption
    action_str = f"{service}.{action}"
    rule_result = await evaluate_rules(db, user.id, api_key.id, provider, action_str)
    if not rule_result.allowed:
        await log_action(
            db, user_id=user.id, api_key_id=api_key.id,
            action=action_str, provider=provider,
            status="denied", detail=f"Blocked by rule: {rule_result.reason}",
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=rule_result.reason)

    # Find connected account
    result = await db.execute(
        select(ConnectedAccount).where(
            ConnectedAccount.user_id == user.id,
            ConnectedAccount.provider == provider,
            ConnectedAccount.deleted_at.is_(None),
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No connected {provider} account")

    # Execute the action
    try:
        if provider == "google":
            google_svc = GoogleService(account, str(user.id))
            result_data = await google_svc.execute(service, action, params)
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown provider: {provider}")

        await log_action(
            db, user_id=user.id, api_key_id=api_key.id,
            action=action_str, provider=provider,
            resource_type="connected_account", resource_id=str(account.id),
            request_summary={"service": service, "action": action},
        )

        return {"status": "success", "data": result_data}

    except HTTPException:
        raise
    except Exception as e:
        await log_action(
            db, user_id=user.id, api_key_id=api_key.id,
            action=action_str, provider=provider,
            status="error", detail=str(e),
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Action execution failed")
