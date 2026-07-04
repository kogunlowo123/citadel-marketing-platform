from celery import Celery
from celery.schedules import crontab

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "citadel_marketing",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_routes={
        "app.workers.send_campaign.*": {"queue": "campaigns"},
        "app.workers.process_import.*": {"queue": "imports"},
    },
    beat_schedule={
        "check-scheduled-campaigns": {
            "task": "app.workers.collect_analytics.check_scheduled_campaigns",
            "schedule": 60.0,
        },
        "refresh-dynamic-segments": {
            "task": "app.workers.collect_analytics.refresh_dynamic_segments",
            "schedule": 300.0,
        },
        "daily-cleanup": {
            "task": "app.workers.collect_analytics.daily_cleanup",
            "schedule": crontab(hour=2, minute=0),
        },
        "update-engagement-scores": {
            "task": "app.workers.collect_analytics.update_engagement_scores",
            "schedule": crontab(hour="*/6", minute=0),
        },
    },
)

celery_app.autodiscover_tasks(["app.workers"])
