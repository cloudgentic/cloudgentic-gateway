from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_2fa
from app.models.rule import Rule
from app.models.user import User
from app.schemas.rule import RuleCreateRequest, RuleResponse, RuleUpdateRequest
from app.services.audit import log_action

router = APIRouter()

VALID_RULE_TYPES = {"rate_limit", "action_whitelist", "action_blacklist", "require_approval"}


@router.post("/", response_model=RuleResponse, status_code=status.HTTP_201_CREATED)
async def create_rule(
    request: RuleCreateRequest,
    user: User = Depends(require_2fa),
    db: AsyncSession = Depends(get_db),
):
    """Create a new rule."""
    if request.rule_type not in VALID_RULE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid rule type. Must be one of: {', '.join(VALID_RULE_TYPES)}",
        )

    rule = Rule(
        user_id=user.id,
        name=request.name,
        description=request.description,
        rule_type=request.rule_type,
        conditions=request.conditions,
        config=request.config,
        priority=request.priority,
        is_enabled=request.is_enabled,
    )
    db.add(rule)
    await db.flush()

    await log_action(
        db, user_id=user.id, action="rule.create",
        resource_type="rule", resource_id=str(rule.id),
        detail=f"Created rule: {request.name} ({request.rule_type})",
    )

    return rule


@router.get("/", response_model=list[RuleResponse])
async def list_rules(
    user: User = Depends(require_2fa),
    db: AsyncSession = Depends(get_db),
):
    """List all rules for the current user."""
    result = await db.execute(
        select(Rule)
        .where(Rule.user_id == user.id, Rule.deleted_at.is_(None))
        .order_by(Rule.priority.desc(), Rule.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{rule_id}", response_model=RuleResponse)
async def get_rule(
    rule_id: UUID,
    user: User = Depends(require_2fa),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific rule."""
    result = await db.execute(
        select(Rule).where(Rule.id == rule_id, Rule.user_id == user.id, Rule.deleted_at.is_(None))
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
    return rule


@router.patch("/{rule_id}", response_model=RuleResponse)
async def update_rule(
    rule_id: UUID,
    request: RuleUpdateRequest,
    user: User = Depends(require_2fa),
    db: AsyncSession = Depends(get_db),
):
    """Update a rule."""
    result = await db.execute(
        select(Rule).where(Rule.id == rule_id, Rule.user_id == user.id, Rule.deleted_at.is_(None))
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")

    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(rule, field, value)
    await db.flush()

    await log_action(
        db, user_id=user.id, action="rule.update",
        resource_type="rule", resource_id=str(rule.id),
    )

    return rule


@router.delete("/{rule_id}")
async def delete_rule(
    rule_id: UUID,
    user: User = Depends(require_2fa),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete a rule."""
    from datetime import datetime, timezone

    result = await db.execute(
        select(Rule).where(Rule.id == rule_id, Rule.user_id == user.id, Rule.deleted_at.is_(None))
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")

    rule.deleted_at = datetime.now(timezone.utc)
    await db.flush()

    await log_action(
        db, user_id=user.id, action="rule.delete",
        resource_type="rule", resource_id=str(rule.id),
    )

    return {"message": "Rule deleted"}
