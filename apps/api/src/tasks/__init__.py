"""
Background tasks for the LearnR API.

This module exports both Celery tasks and async functions for flexibility:
- Use Celery tasks for scheduled/distributed execution
- Use async functions for direct calls in tests or scripts
"""
from .quiz_session_expiration import (
    expire_stale_quiz_sessions,  # Async function for direct usage
    expire_stale_quiz_sessions_task,  # Celery task for scheduled execution
)
from .reading_queue_tasks import (
    add_reading_to_queue,  # Celery task for background execution
    add_reading_to_queue_async,  # Async function for direct usage
)
from .session_cleanup import (
    expire_stale_diagnostic_sessions,  # Async function for direct usage
    expire_stale_diagnostic_sessions_task,  # Celery task for scheduled execution
)

__all__ = [
    "expire_stale_diagnostic_sessions",
    "expire_stale_diagnostic_sessions_task",
    "expire_stale_quiz_sessions",
    "expire_stale_quiz_sessions_task",
    "add_reading_to_queue",
    "add_reading_to_queue_async",
]
