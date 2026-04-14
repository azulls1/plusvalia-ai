"""
Celery application for geo-app background tasks.
Broker: Redis, Result backend: Redis.
"""
import os
from celery import Celery
from celery.schedules import crontab

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

app = Celery(
    "geo_app",
    broker=REDIS_URL,
    backend=RESULT_BACKEND,
    include=[
        "tasks.training_tasks",
        "tasks.enrichment_tasks",
        "tasks.monitoring_tasks",
    ],
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Mexico_City",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    result_expires=86400,  # 24 hours
    task_soft_time_limit=600,  # 10 min soft limit
    task_time_limit=900,  # 15 min hard limit
    task_default_queue="default",
    task_queues={
        "default": {"exchange": "default", "routing_key": "default"},
        "ml": {"exchange": "ml", "routing_key": "ml"},
        "enrichment": {"exchange": "enrichment", "routing_key": "enrichment"},
    },
    task_routes={
        "tasks.training_tasks.*": {"queue": "ml"},
        "tasks.enrichment_tasks.*": {"queue": "enrichment"},
        "tasks.monitoring_tasks.*": {"queue": "default"},
    },
)

# Celery Beat schedule
app.conf.beat_schedule = {
    "check-drift-every-6-hours": {
        "task": "tasks.monitoring_tasks.check_drift",
        "schedule": crontab(minute=0, hour="*/6"),
        "options": {"queue": "default"},
    },
    "recompute-baseline-weekly": {
        "task": "tasks.monitoring_tasks.compute_baseline",
        "schedule": crontab(day_of_week=0, hour=2, minute=0),
        "options": {"queue": "default"},
    },
    "cleanup-expired-cache-daily": {
        "task": "tasks.monitoring_tasks.cleanup_cache",
        "schedule": crontab(hour=3, minute=0),
        "options": {"queue": "default"},
    },
}
