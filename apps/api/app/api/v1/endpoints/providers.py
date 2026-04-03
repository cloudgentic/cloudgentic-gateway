"""Provider configuration endpoints — admin only."""
import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_2fa, require_admin
from app.core.security import encrypt_token, decrypt_token
from app.models.provider_config import ProviderConfig
from app.models.user import User
from app.schemas.provider_config import (
    ProviderConfigSaveRequest,
    ProviderConfigResponse,
    ProviderStatusResponse,
)
from app.services.audit import log_action
from app.providers.registry import PROVIDER_REGISTRY

router = APIRouter()

# Use a fixed "system" user ID for encrypting provider configs
SYSTEM_KEY_CONTEXT = "system-provider-config"


@router.get("/", response_model=list[ProviderStatusResponse])
async def list_providers(
    user: User = Depends(require_2fa),
    db: AsyncSession = Depends(get_db),
):
    """List all supported providers and their configuration status."""
    result = await db.execute(select(ProviderConfig))
    configs = {c.provider: c for c in result.scalars().all()}

    providers = []
    for key, info in PROVIDER_REGISTRY.items():
        config = configs.get(key)
        providers.append(
            ProviderStatusResponse(
                provider=key,
                display_name=info["display_name"],
                is_configured=config.is_configured if config else False,
                category=info["category"],
                description=info["description"],
                setup_url=info["setup_url"],
                docs_url=info.get("docs_url"),
            )
        )
    return providers


@router.post("/{provider}/configure", response_model=ProviderConfigResponse)
async def configure_provider(
    provider: str,
    request: ProviderConfigSaveRequest,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Save OAuth credentials for a provider. Admin only."""
    if provider not in PROVIDER_REGISTRY:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown provider: {provider}")

    info = PROVIDER_REGISTRY[provider]

    result = await db.execute(
        select(ProviderConfig).where(ProviderConfig.provider == provider)
    )
    config = result.scalar_one_or_none()

    encrypted_id = encrypt_token(request.client_id, SYSTEM_KEY_CONTEXT)
    encrypted_secret = encrypt_token(request.client_secret, SYSTEM_KEY_CONTEXT)
    encrypted_extra = None
    if request.extra_config:
        encrypted_extra = encrypt_token(json.dumps(request.extra_config), SYSTEM_KEY_CONTEXT)

    if config:
        config.client_id_encrypted = encrypted_id
        config.client_secret_encrypted = encrypted_secret
        config.extra_config_encrypted = encrypted_extra
        config.is_configured = True
    else:
        config = ProviderConfig(
            provider=provider,
            display_name=info["display_name"],
            client_id_encrypted=encrypted_id,
            client_secret_encrypted=encrypted_secret,
            extra_config_encrypted=encrypted_extra,
            is_configured=True,
        )
        db.add(config)

    await db.flush()

    await log_action(
        db, user_id=user.id, action="provider.configured",
        resource_type="provider_config", resource_id=provider,
        detail=f"Configured OAuth for {info['display_name']}",
    )

    return ProviderConfigResponse(
        id=config.id,
        provider=config.provider,
        display_name=config.display_name,
        is_configured=True,
        has_client_id=True,
        has_client_secret=True,
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


@router.delete("/{provider}/configure")
async def remove_provider_config(
    provider: str,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Remove OAuth credentials for a provider. Admin only."""
    result = await db.execute(
        select(ProviderConfig).where(ProviderConfig.provider == provider)
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider not configured")

    config.client_id_encrypted = None
    config.client_secret_encrypted = None
    config.extra_config_encrypted = None
    config.is_configured = False
    await db.flush()

    await log_action(
        db, user_id=user.id, action="provider.removed",
        resource_type="provider_config", resource_id=provider,
    )

    return {"message": f"{provider} configuration removed"}


def get_provider_credentials(provider: str, db_config: ProviderConfig | None) -> tuple[str, str]:
    """Get decrypted provider credentials. Falls back to env vars."""
    from app.core.config import get_settings
    settings = get_settings()

    if db_config and db_config.is_configured:
        client_id = decrypt_token(db_config.client_id_encrypted, SYSTEM_KEY_CONTEXT)
        client_secret = decrypt_token(db_config.client_secret_encrypted, SYSTEM_KEY_CONTEXT)
        return client_id, client_secret

    # Fallback to env vars
    if provider == "google":
        return settings.google_client_id, settings.google_client_secret

    return "", ""
