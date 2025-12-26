"""
Celery task for populating reading queue after answer submissions.
Story 5.5: Background Reading Queue Population

This task runs asynchronously after each answer submission to add
relevant reading materials to the user's queue without blocking
the answer response.
"""
import asyncio
import time

import structlog
from celery import shared_task

logger = structlog.get_logger(__name__)

# Performance threshold for monitoring (AC 10)
TASK_DURATION_WARNING_MS = 200


@shared_task(
    bind=True,
    name="src.tasks.reading_queue_tasks.add_reading_to_queue",
    max_retries=3,
    default_retry_delay=5,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=60,
)
def add_reading_to_queue(
    self,
    user_id: str,
    enrollment_id: str,
    question_id: str,
    session_id: str,
    is_correct: bool,
    difficulty: float,
) -> dict:
    """
    Background task to populate reading queue after answer submission.

    Flow:
    1. Get question's knowledge_area_id and concepts
    2. Calculate user's KA competency from belief_states
    3. Determine priority based on competency + correctness
    4. Skip if correct on Easy/Medium question
    5. Search Qdrant for relevant reading chunks
    6. Insert/update reading_queue entries

    Args:
        user_id: User UUID string
        enrollment_id: Enrollment UUID string
        question_id: Question UUID string
        session_id: Quiz session UUID string (for logging)
        is_correct: Whether the answer was correct
        difficulty: IRT b-parameter difficulty

    Returns:
        Dict with chunks_added, duration_ms, and status
    """
    start_time = time.perf_counter()

    try:
        # Import here to avoid circular imports
        from src.services.reading_queue_service import populate_reading_queue_async

        # Run the async function in a new event loop
        result = asyncio.run(
            populate_reading_queue_async(
                user_id=user_id,
                enrollment_id=enrollment_id,
                question_id=question_id,
                session_id=session_id,
                is_correct=is_correct,
                difficulty=difficulty,
            )
        )

        duration_ms = int((time.perf_counter() - start_time) * 1000)

        logger.info(
            "reading_queue_task_completed",
            task_id=self.request.id,
            user_id=user_id,
            question_id=question_id,
            chunks_added=result.get("chunks_added", 0),
            duration_ms=duration_ms,
        )

        # Performance monitoring: warn if task exceeds threshold (AC 10)
        if duration_ms > TASK_DURATION_WARNING_MS:
            logger.warning(
                "reading_queue_task_slow",
                task_id=self.request.id,
                user_id=user_id,
                question_id=question_id,
                duration_ms=duration_ms,
                threshold_ms=TASK_DURATION_WARNING_MS,
                message="Task exceeded performance threshold - may indicate Qdrant/OpenAI latency issues",
            )

        return {
            "status": "success",
            "chunks_added": result.get("chunks_added", 0),
            "duration_ms": duration_ms,
            "task_id": self.request.id,
        }

    except Exception as e:
        duration_ms = int((time.perf_counter() - start_time) * 1000)

        logger.error(
            "reading_queue_task_failed",
            task_id=self.request.id,
            user_id=user_id,
            question_id=question_id,
            error=str(e),
            retry_count=self.request.retries,
            duration_ms=duration_ms,
        )
        raise


# Convenience alias for direct async usage (testing, scripts, etc.)
async def add_reading_to_queue_async(
    user_id: str,
    enrollment_id: str,
    question_id: str,
    session_id: str,
    is_correct: bool,
    difficulty: float,
) -> dict:
    """
    Async convenience function for direct calls (testing, scripts).

    Args:
        user_id: User UUID string
        enrollment_id: Enrollment UUID string
        question_id: Question UUID string
        session_id: Quiz session UUID string
        is_correct: Whether the answer was correct
        difficulty: IRT b-parameter difficulty

    Returns:
        Dict with chunks_added and status
    """
    from src.services.reading_queue_service import populate_reading_queue_async

    return await populate_reading_queue_async(
        user_id=user_id,
        enrollment_id=enrollment_id,
        question_id=question_id,
        session_id=session_id,
        is_correct=is_correct,
        difficulty=difficulty,
    )
