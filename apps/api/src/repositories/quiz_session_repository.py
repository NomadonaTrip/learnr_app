"""
QuizSessionRepository for database operations on QuizSession model.
Implements repository pattern for quiz session data access.
"""
from datetime import UTC, datetime, timedelta
from uuid import UUID

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from src.models.quiz_session import QuizSession

logger = structlog.get_logger(__name__)


class QuizSessionRepository:
    """Repository for QuizSession database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_session(
        self,
        user_id: UUID,
        enrollment_id: UUID,
        session_type: str = "adaptive",
        question_strategy: str = "max_info_gain",
        knowledge_area_filter: str | None = None,
        target_concept_ids: list[str] | None = None,
        question_target: int = 10,
    ) -> QuizSession:
        """
        Create a new quiz session.

        Args:
            user_id: User UUID
            enrollment_id: Enrollment UUID
            session_type: Type of session (diagnostic, adaptive, focused, focused_ka, focused_concept, review)
            question_strategy: Question selection strategy
            knowledge_area_filter: Optional knowledge area filter for focused/focused_ka sessions
            target_concept_ids: Optional list of concept UUID strings for focused_concept sessions
            question_target: Target number of questions (default 10 for habit-forming consistency)

        Returns:
            Created QuizSession
        """
        quiz_session = QuizSession(
            user_id=user_id,
            enrollment_id=enrollment_id,
            session_type=session_type,
            question_strategy=question_strategy,
            knowledge_area_filter=knowledge_area_filter,
            target_concept_ids=target_concept_ids or [],
            question_target=question_target,
        )
        self.session.add(quiz_session)
        await self.session.flush()
        await self.session.refresh(quiz_session)

        logger.info(
            "quiz_session_created",
            session_id=str(quiz_session.id),
            user_id=str(user_id),
            enrollment_id=str(enrollment_id),
            session_type=session_type,
            question_strategy=question_strategy,
        )

        return quiz_session

    async def get_active_session(
        self,
        user_id: UUID,
    ) -> QuizSession | None:
        """
        Get the active (not ended) quiz session for a user.

        Per story spec: Only one active session per user globally
        (where ended_at IS NULL).

        Args:
            user_id: User UUID

        Returns:
            QuizSession if active session exists, None otherwise
        """
        result = await self.session.execute(
            select(QuizSession)
            .where(QuizSession.user_id == user_id)
            .where(QuizSession.ended_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_session_by_id(
        self,
        session_id: UUID,
    ) -> QuizSession | None:
        """
        Get a quiz session by ID.

        Args:
            session_id: Session UUID

        Returns:
            QuizSession if found, None otherwise
        """
        result = await self.session.execute(
            select(QuizSession).where(QuizSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def get_session_by_id_for_update(
        self,
        session_id: UUID,
    ) -> QuizSession | None:
        """
        Get a quiz session by ID with row lock for concurrent access safety.

        Args:
            session_id: Session UUID

        Returns:
            QuizSession if found, None otherwise
        """
        result = await self.session.execute(
            select(QuizSession)
            .where(QuizSession.id == session_id)
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def increment_question_count(
        self,
        session_id: UUID,
        is_correct: bool,
    ) -> QuizSession:
        """
        Increment the question count and optionally correct count.

        Args:
            session_id: Session UUID
            is_correct: Whether the answer was correct

        Returns:
            Updated QuizSession

        Raises:
            ValueError: If session not found
        """
        session = await self.get_session_by_id_for_update(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        session.total_questions += 1
        if is_correct:
            session.correct_count += 1

        await self.session.flush()
        await self.session.refresh(session)

        logger.debug(
            "quiz_session_question_recorded",
            session_id=str(session_id),
            total_questions=session.total_questions,
            correct_count=session.correct_count,
            is_correct=is_correct,
        )

        return session

    async def mark_paused(
        self,
        session_id: UUID,
    ) -> QuizSession:
        """
        Mark a session as paused.

        Args:
            session_id: Session UUID

        Returns:
            Updated QuizSession

        Raises:
            ValueError: If session not found
        """
        session = await self.get_session_by_id_for_update(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        session.is_paused = True
        await self.session.flush()
        await self.session.refresh(session)

        logger.info(
            "quiz_session_paused",
            session_id=str(session_id),
            user_id=str(session.user_id),
        )

        return session

    async def mark_resumed(
        self,
        session_id: UUID,
    ) -> QuizSession:
        """
        Mark a session as resumed (unpaused).

        Args:
            session_id: Session UUID

        Returns:
            Updated QuizSession

        Raises:
            ValueError: If session not found
        """
        session = await self.get_session_by_id_for_update(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        session.is_paused = False
        await self.session.flush()
        await self.session.refresh(session)

        logger.info(
            "quiz_session_resumed",
            session_id=str(session_id),
            user_id=str(session.user_id),
        )

        return session

    async def mark_ended(
        self,
        session_id: UUID,
    ) -> QuizSession:
        """
        Mark a session as ended.

        Args:
            session_id: Session UUID

        Returns:
            Updated QuizSession

        Raises:
            ValueError: If session not found
        """
        session = await self.get_session_by_id_for_update(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        session.ended_at = func.now()
        await self.session.flush()
        await self.session.refresh(session)

        logger.info(
            "quiz_session_ended",
            session_id=str(session_id),
            user_id=str(session.user_id),
            total_questions=session.total_questions,
            correct_count=session.correct_count,
        )

        return session

    async def get_stale_sessions(
        self,
        timeout_hours: int = 2,
    ) -> list[QuizSession]:
        """
        Get sessions that have been inactive for longer than timeout.

        Used for session expiration cleanup.

        Args:
            timeout_hours: Hours after which a session is considered stale

        Returns:
            List of stale QuizSession objects
        """
        cutoff_time = datetime.now(UTC) - timedelta(hours=timeout_hours)

        result = await self.session.execute(
            select(QuizSession)
            .where(QuizSession.ended_at.is_(None))
            .where(QuizSession.updated_at < cutoff_time)
        )
        return list(result.scalars().all())

    async def expire_stale_sessions(
        self,
        timeout_hours: int = 2,
    ) -> int:
        """
        Batch expire sessions that have been inactive for too long.

        Args:
            timeout_hours: Hours after which a session is considered stale

        Returns:
            Number of sessions expired
        """
        cutoff_time = datetime.now(UTC) - timedelta(hours=timeout_hours)

        result = await self.session.execute(
            update(QuizSession)
            .where(QuizSession.ended_at.is_(None))
            .where(QuizSession.updated_at < cutoff_time)
            .values(ended_at=func.now())
        )
        await self.session.flush()

        expired_count = result.rowcount
        if expired_count > 0:
            logger.info(
                "quiz_sessions_batch_expired",
                expired_count=expired_count,
                timeout_hours=timeout_hours,
            )

        return expired_count
