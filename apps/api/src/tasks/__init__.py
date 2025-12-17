"""
Background tasks for the LearnR API.

This module exports both Celery tasks and async functions for flexibility:
- Use Celery tasks for scheduled/distributed execution
- Use async functions for direct calls in tests or scripts
"""
from .session_cleanup import (
    expire_stale_diagnostic_sessions,  # Async function for direct usage
    expire_stale_diagnostic_sessions_task,  # Celery task for scheduled execution
)

__all__ = [
    "expire_stale_diagnostic_sessions",
    "expire_stale_diagnostic_sessions_task",
]
