from celery import Celery

from config import settings

celery_app = Celery(
    "worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    task_always_eager=settings.is_development,
    task_always_propagates=settings.is_development,
)
