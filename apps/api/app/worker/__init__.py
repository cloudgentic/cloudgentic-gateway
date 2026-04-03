from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "gateway",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    broker_connection_retry_on_startup=True,
)

# Import tasks
celery_app.autodiscover_tasks(["app.worker"])
