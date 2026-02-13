"""Celery 앱 설정."""

from __future__ import annotations

from celery import Celery

from app.core.config import get_app_settings

settings = get_app_settings()

celery_app = Celery(
    "richlychee",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Seoul",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

celery_app.autodiscover_tasks(["app.tasks"])
