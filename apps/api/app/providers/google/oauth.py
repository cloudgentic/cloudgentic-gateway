import secrets

import httpx
from authlib.integrations.httpx_client import AsyncOAuth2Client
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import decrypt_token

settings = get_settings()

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

GOOGLE_SCOPES = [
    "openid",
    "email",
    "profile",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/drive.file",
]

SYSTEM_KEY_CONTEXT = "system-provider-config"


async def _get_google_credentials(db: AsyncSession | None = None) -> tuple[str, str]:
    """Get Google OAuth credentials from DB first, then fall back to env."""
    if db:
        from app.models.provider_config import ProviderConfig
        result = await db.execute(
            select(ProviderConfig).where(
                ProviderConfig.provider == "google",
                ProviderConfig.is_configured.is_(True),
            )
        )
        config = result.scalar_one_or_none()
        if config and config.client_id_encrypted and config.client_secret_encrypted:
            client_id = decrypt_token(config.client_id_encrypted, SYSTEM_KEY_CONTEXT)
            client_secret = decrypt_token(config.client_secret_encrypted, SYSTEM_KEY_CONTEXT)
            return client_id, client_secret

    # Fallback to env
    return settings.google_client_id, settings.google_client_secret


class GoogleOAuth:
    def __init__(self, client_id: str = "", client_secret: str = ""):
        self.client_id = client_id or settings.google_client_id
        self.client_secret = client_secret or settings.google_client_secret
        self.redirect_uri = f"{settings.api_url}/api/v1/accounts/google/callback"

    @classmethod
    async def create(cls, db: AsyncSession | None = None) -> "GoogleOAuth":
        """Factory that loads credentials from DB or env."""
        client_id, client_secret = await _get_google_credentials(db)
        return cls(client_id=client_id, client_secret=client_secret)

    def get_authorization_url(self) -> tuple[str, str]:
        """Generate Google OAuth authorization URL."""
        if not self.client_id:
            raise ValueError("Google OAuth not configured. Go to Settings → Providers to set up Google.")
        state = secrets.token_urlsafe(32)
        client = AsyncOAuth2Client(
            client_id=self.client_id,
            redirect_uri=self.redirect_uri,
            scope=" ".join(GOOGLE_SCOPES),
        )
        url, _ = client.create_authorization_url(
            GOOGLE_AUTH_URL,
            state=state,
            access_type="offline",
            prompt="consent",
        )
        return url, state

    async def exchange_code(self, code: str) -> dict:
        """Exchange authorization code for tokens."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": self.redirect_uri,
                },
            )
            response.raise_for_status()
            return response.json()

    async def refresh_access_token(self, refresh_token: str) -> dict:
        """Refresh an expired access token."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                },
            )
            response.raise_for_status()
            return response.json()

    async def get_user_info(self, access_token: str) -> dict:
        """Get Google user info."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            return response.json()
