"""Rule template manager — loads and applies predefined rule templates."""
import json
import logging
from pathlib import Path
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rule import Rule

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).parent / "templates"


def list_templates() -> list[dict]:
    """List all available rule templates."""
    templates = []
    if not TEMPLATES_DIR.exists():
        return templates

    for template_file in sorted(TEMPLATES_DIR.glob("*.json")):
        try:
            data = json.loads(template_file.read_text(encoding="utf-8"))
            templates.append({
                "id": template_file.stem,
                "name": data.get("name", template_file.stem),
                "description": data.get("description", ""),
                "category": data.get("category", "general"),
                "rules": [
                    {
                        "name": r.get("name", ""),
                        "rule_type": r.get("rule_type", ""),
                        "description": r.get("description", ""),
                    }
                    for r in data.get("rules", [])
                ],
            })
        except (json.JSONDecodeError, Exception) as e:
            logger.error("Failed to load template %s: %s", template_file.name, e)

    return templates


def get_template(template_id: str) -> dict | None:
    """Load a specific template by ID (filename without extension)."""
    template_path = TEMPLATES_DIR / f"{template_id}.json"
    if not template_path.exists():
        return None

    try:
        return json.loads(template_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, Exception) as e:
        logger.error("Failed to load template %s: %s", template_id, e)
        return None


async def apply_template(
    db: AsyncSession,
    template_id: str,
    user_id: UUID,
    overrides: dict | None = None,
) -> list[Rule]:
    """Apply a template, creating all its rules for the given user.

    Args:
        db: Database session
        template_id: Template ID (filename stem)
        user_id: User to create rules for
        overrides: Optional overrides for rule fields (applied to all rules)

    Returns:
        List of created Rule objects
    """
    template = get_template(template_id)
    if not template:
        return []

    overrides = overrides or {}
    created_rules = []

    for rule_def in template.get("rules", []):
        rule = Rule(
            user_id=user_id,
            name=overrides.get("name_prefix", "") + rule_def.get("name", "Unnamed Rule"),
            description=rule_def.get("description"),
            rule_type=rule_def["rule_type"],
            conditions=rule_def.get("conditions", {}),
            config=rule_def.get("config", {}),
            priority=rule_def.get("priority", 0),
            is_enabled=overrides.get("is_enabled", True),
        )
        db.add(rule)
        created_rules.append(rule)

    await db.flush()
    return created_rules
