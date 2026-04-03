from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_2fa
from app.models.rule import Rule
from app.models.user import User
from app.rules.template_manager import list_templates, get_template, apply_template
from app.schemas.rule import RuleCreateRequest, RuleResponse, RuleUpdateRequest
from app.services.audit import log_action

router = APIRouter()

VALID_RULE_TYPES = {"rate_limit", "action_whitelist", "action_blacklist", "require_approval", "chain", "dry_run"}


class TemplateApplyRequest(BaseModel):
    name_prefix: str = ""
    is_enabled: bool = True


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


# --- Rule Templates (must be before /{rule_id} to avoid route shadowing) ---

@router.get("/templates")
async def list_rule_templates():
    """List all available rule templates."""
    return {"templates": list_templates()}


@router.post("/templates/{template_id}/apply", response_model=list[RuleResponse], status_code=status.HTTP_201_CREATED)
async def apply_rule_template(
    template_id: str,
    request_body: TemplateApplyRequest | None = None,
    user: User = Depends(require_2fa),
    db: AsyncSession = Depends(get_db),
):
    """Apply a rule template, creating all its rules for the current user."""
    import re
    if not re.match(r"^[a-z0-9-]+$", template_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid template ID")

    template = get_template(template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template '{template_id}' not found",
        )

    overrides = {}
    if request_body:
        overrides = request_body.model_dump(exclude_unset=True)

    rules = await apply_template(db, template_id, user.id, overrides)

    await log_action(
        db, user_id=user.id, action="rule.template.apply",
        resource_type="rule_template", resource_id=template_id,
        detail=f"Applied template '{template['name']}', created {len(rules)} rules",
    )

    return rules


# --- Individual Rule CRUD ---

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
