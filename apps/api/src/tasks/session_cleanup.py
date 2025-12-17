"""
Celery task for cleaning up stale diagnostic sessions.
Expires sessions that have been inactive beyond the timeout threshold.
"""
import asyncio

import structlog
from celery import shared_task

from src.db.session import AsyncSessionLocal
from src.repositories.diagnostic_session_repository import DiagnosticSessionRepository

logger = structlog.get_logger(__name__)

# Session timeout in minutes
SESSION_TIMEOUT_MINUTES = 30


async def _expire_stale_sessions() -> int:
    """
    Internal async function to batch expire stale diagnostic sessions.

    Returns:
        Number of sessions expired
    """
    async with AsyncSessionLocal() as session:
        try:
            repo = DiagnosticSessionRepository(session)
            expired_count = await repo.expire_stale_sessions(
                timeout_minutes=SESSION_TIMEOUT_MINUTES
            )
            await session.commit()

            if expired_count > 0:
                logger.info(
                    "Expired stale diagnostic sessions",
                    expired_count=expired_count,
                    timeout_minutes=SESSION_TIMEOUT_MINUTES,
                )

            return expired_count

        except Exception as e:
            await session.rollback()
            logger.error(
                "Failed to expire stale sessions",
                error=str(e),
            )
            raise


@shared_task(
    bind=True,
    name="src.tasks.session_cleanup.expire_stale_diagnostic_sessions_task",
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
)
def expire_stale_diagnostic_sessions_task(self) -> dict:
    """
    Celery task to batch expire diagnostic sessions that have exceeded the timeout.

    This task is scheduled to run every 5 minutes via Celery Beat to
    clean up sessions that users abandoned without completing.

    The task uses retry with exponential backoff for transient failures.

    Returns:
        Dictionary with expired_count and task metadata
    """
    try:
        # Run the async function in a new event loop
        # This is necessary because Celery workers are synchronous by default
        expired_count = asyncio.run(_expire_stale_sessions())

        logger.info(
            "Session cleanup task completed",
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
            "Session cleanup task failed",
            task_id=self.request.id,
            error=str(e),
            retry_count=self.request.retries,
        )
        raise


# Convenience alias for direct async usage (testing, scripts, etc.)
expire_stale_diagnostic_sessions = _expire_stale_sessions
