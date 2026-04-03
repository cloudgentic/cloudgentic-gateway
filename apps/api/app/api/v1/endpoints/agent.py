"""Agent-facing API endpoints. Authenticated via API key (cgw_...)."""
from fastapi import APIRouter, Depends, HTTPException, status
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
):
    """Execute an action on behalf of the user via their connected account."""
    user, api_key = agent

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
    if not rule_result.allowed:
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
