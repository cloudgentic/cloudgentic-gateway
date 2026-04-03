"""Security endpoints — kill switch, skill scanner."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_2fa
from app.models.user import User
from app.schemas.security import (
    KillSwitchRequest,
    KillSwitchResponse,
    KillSwitchRestoreRequest,
    KillSwitchStatusResponse,
    SkillScanRequest,
    SkillScanResponse,
)
from app.security.kill_switch import activate_kill_switch, restore_keys, get_kill_switch_status

router = APIRouter()


@router.post("/kill-switch", response_model=KillSwitchResponse)
async def kill_switch(
    request: KillSwitchRequest,
    user: User = Depends(require_2fa),
    db: AsyncSession = Depends(get_db),
):
    """Emergency kill switch — instantly revoke all agent access."""
    event = await activate_kill_switch(
        db,
        user,
        revoke_api_keys=request.revoke_api_keys,
        disconnect_accounts=request.disconnect_accounts,
        reason=request.reason,
        trigger_source="api",
    )
    return KillSwitchResponse(
        status="executed",
        keys_revoked=event.keys_revoked,
        tokens_revoked=event.tokens_revoked,
        event_id=event.id,
        message="All agent access has been revoked. Create new API keys to re-enable agents.",
    )


@router.post("/kill-switch/restore")
async def kill_switch_restore(
    request: KillSwitchRestoreRequest,
    user: User = Depends(require_2fa),
    db: AsyncSession = Depends(get_db),
):
    """Selectively restore revoked API keys after kill switch."""
    restored = await restore_keys(db, user, request.restore_keys)
    return {"status": "restored", "keys_restored": restored}


@router.get("/kill-switch/status", response_model=KillSwitchStatusResponse)
async def kill_switch_status(
    user: User = Depends(require_2fa),
    db: AsyncSession = Depends(get_db),
):
    """Get current kill switch status."""
    status_data = await get_kill_switch_status(db, user)
    return KillSwitchStatusResponse(**status_data)


@router.post("/scan-skill", response_model=SkillScanResponse)
async def scan_skill(
    request: SkillScanRequest,
    user: User = Depends(require_2fa),
    db: AsyncSession = Depends(get_db),
):
    """Scan an OpenClaw skill for security concerns."""
    from app.security.skill_scanner import scan_skill as do_scan
    from app.services.audit import log_action

    result = do_scan(
        skill_name=request.skill_name,
        skill_md_content=request.skill_md_content,
        files=request.files,
    )

    await log_action(
        db,
        user_id=user.id,
        action="security.skill_scanned",
        detail=f"Scanned skill '{request.skill_name}': risk_level={result.risk_level}, score={result.risk_score}",
    )

    return result
