"""
Celery task for cleaning up stale quiz sessions.
Expires sessions that have been inactive beyond the timeout threshold (2 hours).
"""
import asyncio

import structlog
from celery import shared_task

from src.db.session import AsyncSessionLocal
from src.repositories.quiz_session_repository import QuizSessionRepository

logger = structlog.get_logger(__name__)

# Session timeout in hours (per architecture spec)
SESSION_TIMEOUT_HOURS = 2


async def _expire_stale_quiz_sessions() -> int:
    """
    Internal async function to batch expire stale quiz sessions.

    Returns:
        Number of sessions expired
    """
    async with AsyncSessionLocal() as session:
        try:
            repo = QuizSessionRepository(session)
            expired_count = await repo.expire_stale_sessions(
                timeout_hours=SESSION_TIMEOUT_HOURS
            )
            await session.commit()

            if expired_count > 0:
                logger.info(
                    "quiz_sessions_expired",
                    count=expired_count,
                    timeout_hours=SESSION_TIMEOUT_HOURS,
                )

            return expired_count

        except Exception as e:
            await session.rollback()
            logger.error(
                "Failed to expire stale quiz sessions",
                error=str(e),
            )
            raise


@shared_task(
    bind=True,
    name="src.tasks.quiz_session_expiration.expire_stale_quiz_sessions_task",
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
)
def expire_stale_quiz_sessions_task(self) -> dict:
    """
    Celery task to batch expire quiz sessions that have exceeded the timeout (2 hours).

    This task is scheduled to run every 15 minutes via Celery Beat to
    clean up sessions that users abandoned without completing.

    The task uses retry with exponential backoff for transient failures.

    Returns:
        Dictionary with expired_count and task metadata
    """
    try:
        # Run the async function in a new event loop
        # This is necessary because Celery workers are synchronous by default
        expired_count = asyncio.run(_expire_stale_quiz_sessions())

        logger.info(
            "Quiz session cleanup task completed",
            task_id=self.request.id,
            expired_count=expired_count,
        )

        return {
            "status": "success",
            "expired_count": expired_count,
            "task_id": self.request.id,
        }

    except Exception as e:
        logger.error(
            "Quiz session cleanup task failed",
            task_id=self.request.id,
            error=str(e),
            retry_count=self.request.retries,
        )
        raise


# Convenience alias for direct async usage (testing, scripts, etc.)
expire_stale_quiz_sessions = _expire_stale_quiz_sessions
