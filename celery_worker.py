"""Celery application factory, broker/backend configuration, and periodic beat schedule."""

from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "aibot",
    broker=str(settings.redis_url),
    backend=str(settings.redis_url),
    include=["app.tasks"],
)

celery_app.conf.update(
    task_serializer=settings.celery_task_serializer,
    accept_content=[settings.celery_task_serializer],
    result_serializer=settings.celery_task_serializer,
    timezone="UTC",
    enable_utc=True,
    result_expires=86400,
)

celery_app.conf.beat_schedule = {
    "news-pipeline": {
        "task": "app.tasks.fetch_news_task",
        "schedule": crontab(minute="*/30"),
    },
}
