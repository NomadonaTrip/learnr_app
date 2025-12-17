"""
Celery application configuration.
Provides background task processing with Redis as broker and result backend.
"""
from celery import Celery

from src.config import settings

# Create Celery app with Redis as broker
celery_app = Celery(
    "learnr",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["src.tasks.session_cleanup"],
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Task execution settings
    task_acks_late=True,  # Acknowledge task after completion (safer for crashes)
    task_reject_on_worker_lost=True,  # Requeue tasks if worker dies
    worker_prefetch_multiplier=1,  # Fetch one task at a time (better for long tasks)

    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour

    # Beat schedule for periodic tasks
    beat_schedule={
        "expire-stale-diagnostic-sessions": {
            "task": "src.tasks.session_cleanup.expire_stale_diagnostic_sessions_task",
            "schedule": 300.0,  # Every 5 minutes (300 seconds)
            "options": {"queue": "maintenance"},
        },
    },

    # Queue routing
    task_routes={
        "src.tasks.session_cleanup.*": {"queue": "maintenance"},
    },

    # Default queue
    task_default_queue="default",
)


# Optional: Autodiscover tasks from installed apps
# celery_app.autodiscover_tasks(["src.tasks"])
