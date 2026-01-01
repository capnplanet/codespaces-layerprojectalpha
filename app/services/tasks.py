from celery import Celery

from app.core.config import get_settings

settings = get_settings()
celery_app = Celery(
    "tasks",
    broker=settings.redis_url,
    backend=settings.redis_url,
)


@celery_app.task
def background_eval(dataset: str) -> str:
    return f"eval started for {dataset}"
