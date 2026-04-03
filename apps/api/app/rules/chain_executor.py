"""Action chain executor — triggers follow-up actions based on chain rules.

After a successful action, checks for rule_type="chain" rules that match the
completed action, renders template variables, and executes the chain action
through the normal pipeline with a depth limit to prevent infinite loops.
"""
import logging
import re
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rule import Rule
from app.services.audit import log_action

logger = logging.getLogger(__name__)

MAX_CHAIN_DEPTH = 5


async def execute_chains(
    db: AsyncSession,
    user_id: UUID,
    api_key_id: UUID,
    provider: str,
    action: str,
    request_params: dict,
    response_data: dict,
    chain_depth: int = 0,
) -> list[dict]:
    """Check for chain rules matching the completed action and execute them.

    Args:
        db: Database session
        user_id: The user who owns the rules
        api_key_id: The API key used for the original action
        provider: Provider of the completed action (e.g., "google")
        action: The completed action (e.g., "gmail.send")
        request_params: Original request parameters
        response_data: Response data from the completed action
        chain_depth: Current depth in the chain (prevents infinite loops)

    Returns:
        List of chain execution results
    """
    if chain_depth >= MAX_CHAIN_DEPTH:
        logger.warning(
            "Chain depth limit (%d) reached for user %s, action %s",
            MAX_CHAIN_DEPTH, user_id, action,
        )
        return []

    # Find matching chain rules
    result = await db.execute(
        select(Rule).where(
            Rule.user_id == user_id,
            Rule.rule_type == "chain",
            Rule.is_enabled.is_(True),
            Rule.deleted_at.is_(None),
        ).order_by(Rule.priority.desc())
    )
    chain_rules = result.scalars().all()

    chain_results = []

    for rule in chain_rules:
        if not _chain_matches_trigger(rule, provider, action):
            continue

        config = rule.config
        chain_provider = config.get("chain_provider", provider)
        chain_service = config.get("chain_service", "")
        chain_action = config.get("chain_action", "")
        chain_params_template = config.get("chain_params", {})

        if not chain_service or not chain_action:
            logger.warning("Chain rule %s missing chain_service or chain_action", rule.id)
            continue

        # Render template variables
        template_context = {
            "request": request_params,
            "response": response_data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "provider": provider,
            "action": action,
        }
        chain_params = _render_template(chain_params_template, template_context)

        logger.info(
            "Executing chain rule %s: %s.%s (depth=%d)",
            rule.id, chain_service, chain_action, chain_depth + 1,
        )

        # Log the chain trigger
        await log_action(
            db,
            user_id=user_id,
            api_key_id=api_key_id,
            action=f"{chain_service}.{chain_action}",
            provider=chain_provider,
            detail=f"Triggered by chain rule: {rule.name} (depth={chain_depth + 1})",
            request_summary={
                "chain_rule_id": str(rule.id),
                "trigger_action": action,
                "chain_params": chain_params,
                "chain_depth": chain_depth + 1,
            },
        )

        chain_results.append({
            "chain_rule_id": str(rule.id),
            "chain_rule_name": rule.name,
            "chain_action": f"{chain_service}.{chain_action}",
            "chain_provider": chain_provider,
            "chain_params": chain_params,
            "chain_depth": chain_depth + 1,
        })

    return chain_results


def _chain_matches_trigger(rule: Rule, provider: str, action: str) -> bool:
    """Check if a chain rule is triggered by the given action."""
    conditions = rule.conditions
    if not conditions:
        return False  # Chain rules MUST have trigger conditions

    trigger_providers = conditions.get("trigger_providers", [])
    trigger_actions = conditions.get("trigger_actions", [])

    if trigger_providers and provider not in trigger_providers:
        return False
    if trigger_actions and action not in trigger_actions:
        return False

    # At least one trigger condition must be specified
    return bool(trigger_providers or trigger_actions)


def _render_template(template: dict | list | str, context: dict) -> dict | list | str:
    """Recursively render template variables like {{request.subject}}, {{response.id}}.

    Supports nested dot notation: {{request.params.to}} resolves to context["request"]["params"]["to"].
    """
    if isinstance(template, str):
        return _render_string(template, context)
    elif isinstance(template, dict):
        return {k: _render_template(v, context) for k, v in template.items()}
    elif isinstance(template, list):
        return [_render_template(item, context) for item in template]
    return template


def _render_string(template_str: str, context: dict) -> str:
    """Replace {{path.to.value}} placeholders with actual values from context."""
    pattern = re.compile(r"\{\{(\w+(?:\.\w+)*)\}\}")

    def replacer(match: re.Match) -> str:
        path = match.group(1)
        value = _resolve_path(context, path)
        if value is None:
            return match.group(0)  # Leave unresolved placeholders as-is
        return str(value)

    return pattern.sub(replacer, template_str)


def _resolve_path(data: dict, path: str):
    """Resolve a dot-separated path like 'request.params.to' in nested dicts."""
    parts = path.split(".")
    current = data
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
        if current is None:
            return None
    return current
