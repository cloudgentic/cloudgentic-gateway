from datetime import datetime, timedelta, timezone

from app.core.security import encrypt_token, decrypt_token
from app.models.connected_account import ConnectedAccount


async def store_tokens(
    account: ConnectedAccount,
    token_data: dict,
    user_id: str,
) -> None:
    """Encrypt and store OAuth tokens on a connected account."""
    if "access_token" in token_data:
        account.access_token_encrypted = encrypt_token(token_data["access_token"], user_id)
    if "refresh_token" in token_data:
        account.refresh_token_encrypted = encrypt_token(token_data["refresh_token"], user_id)
    if "expires_in" in token_data:
        account.token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=token_data["expires_in"])


def get_access_token(account: ConnectedAccount, user_id: str) -> str:
    """Decrypt and return the access token."""
    if not account.access_token_encrypted:
        raise ValueError("No access token stored")
    return decrypt_token(account.access_token_encrypted, user_id)


def get_refresh_token(account: ConnectedAccount, user_id: str) -> str | None:
    """Decrypt and return the refresh token."""
    if not account.refresh_token_encrypted:
        return None
    return decrypt_token(account.refresh_token_encrypted, user_id)
