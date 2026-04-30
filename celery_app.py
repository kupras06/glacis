from celery import Celery

from config import settings

celery_app = Celery(
    "worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    task_always_eager=True,
    task_always_propagates=True,
)
