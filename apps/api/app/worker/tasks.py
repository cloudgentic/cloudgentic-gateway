"""Celery background tasks."""
from app.worker import celery_app


@celery_app.task(name="gateway.refresh_token")
def refresh_token_task(account_id: str, user_id: str):
    """Background task to refresh an OAuth token."""
    import asyncio
    from app.providers.google.oauth import GoogleOAuth
    # This would be expanded with actual DB session handling
    pass


@celery_app.task(name="gateway.cleanup_expired_keys")
def cleanup_expired_keys():
    """Periodic task to mark expired API keys."""
    pass
