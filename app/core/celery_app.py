"""
Celery configuration and beat schedule
"""
from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

# Initialize Celery
celery_app = Celery(
    "bridgecore",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Autodiscover tasks
    include=["app.tasks.stats_aggregation"]
)

# Celery Beat Schedule for periodic tasks
celery_app.conf.beat_schedule = {
    # Aggregate hourly stats every hour at minute 5
    "aggregate-hourly-stats": {
        "task": "aggregate_hourly_stats",
        "schedule": crontab(minute=5),  # Every hour at :05
    },
    # Aggregate daily stats every day at 00:30
    "aggregate-daily-stats": {
        "task": "aggregate_daily_stats",
        "schedule": crontab(hour=0, minute=30),  # Daily at 00:30 UTC
    },
    # Clean up old logs every day at 02:00
    "cleanup-old-logs": {
        "task": "cleanup_old_logs",
        "schedule": crontab(hour=2, minute=0),  # Daily at 02:00 UTC
    },
}
