"""
DiagnosticSessionRepository for database operations on DiagnosticSession model.
Implements repository pattern for diagnostic session data access.
"""
from datetime import UTC, datetime, timedelta
from uuid import UUID

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from src.models.diagnostic_session import DiagnosticSession

logger = structlog.get_logger(__name__)


class DiagnosticSessionRepository:
    """Repository for DiagnosticSession database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_session(
        self,
        user_id: UUID,
        enrollment_id: UUID,
        question_ids: list[str],
    ) -> DiagnosticSession:
        """
        Create a new diagnostic session.

        Args:
            user_id: User UUID
            enrollment_id: Enrollment UUID
            question_ids: List of question UUID strings in order

        Returns:
            Created DiagnosticSession

        Raises:
            IntegrityError: If an active session already exists for this enrollment
        """
        session = DiagnosticSession(
            user_id=user_id,
            enrollment_id=enrollment_id,
            question_ids=question_ids,
            current_index=0,
            status="in_progress",
        )
        self.session.add(session)
        await self.session.flush()
        await self.session.refresh(session)

        # Verify the session was created with the correct user_id
        logger.info(
            "diagnostic_session_created",
            user_id_param=str(user_id),
            session_id=str(session.id),
            session_user_id=str(session.user_id),
            enrollment_id=str(enrollment_id),
            question_count=len(question_ids),
            user_ids_match=session.user_id == user_id,
        )

        return session

    async def get_active_session(
        self,
        user_id: UUID,
        enrollment_id: UUID,
    ) -> DiagnosticSession | None:
        """
        Get the active (in_progress) diagnostic session for a user's enrollment.

        Args:
            user_id: User UUID
            enrollment_id: Enrollment UUID

        Returns:
            DiagnosticSession if active session exists, None otherwise
        """
        result = await self.session.execute(
            select(DiagnosticSession)
            .where(DiagnosticSession.user_id == user_id)
            .where(DiagnosticSession.enrollment_id == enrollment_id)
            .where(DiagnosticSession.status == "in_progress")
        )
        session = result.scalar_one_or_none()

        # Debug logging
        if session:
            logger.info(
                "get_active_session_result",
                query_user_id=str(user_id),
                query_enrollment_id=str(enrollment_id),
                session_id=str(session.id),
                session_user_id=str(session.user_id),
                user_ids_match=session.user_id == user_id,
            )

        return session

    async def get_session_by_id(
        self,
        session_id: UUID,
    ) -> DiagnosticSession | None:
        """
        Get a diagnostic session by ID.

        Args:
            session_id: Session UUID

        Returns:
            DiagnosticSession if found, None otherwise
        """
        result = await self.session.execute(
            select(DiagnosticSession).where(DiagnosticSession.id == session_id)
        )
        session = result.scalar_one_or_none()

        # Debug logging to investigate user mismatch
        if session:
            logger.info(
                "get_session_by_id_result",
                session_id=str(session_id),
                session_user_id=str(session.user_id),
                session_enrollment_id=str(session.enrollment_id),
                session_status=session.status,
            )

        return session

    async def increment_progress(
        self,
        session_id: UUID,
    ) -> DiagnosticSession:
        """
        Increment the current_index of a session (advance to next question).

        Args:
            session_id: Session UUID

        Returns:
            Updated DiagnosticSession

        Raises:
            ValueError: If session not found
        """
        session = await self.get_session_by_id(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        session.current_index += 1
        await self.session.flush()
        await self.session.refresh(session)

        return session

    async def mark_completed(
        self,
        session_id: UUID,
    ) -> DiagnosticSession:
        """
        Mark a session as completed.

        Args:
            session_id: Session UUID

        Returns:
            Updated DiagnosticSession

        Raises:
            ValueError: If session not found
        """
        session = await self.get_session_by_id(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        session.status = "completed"
        session.completed_at = func.now()
        await self.session.flush()
        await self.session.refresh(session)

        logger.info(
            "diagnostic_session_completed",
            session_id=str(session_id),
            user_id=str(session.user_id),
        )

        return session

    async def mark_expired(
        self,
        session_id: UUID,
    ) -> DiagnosticSession:
        """
        Mark a session as expired.

        Args:
            session_id: Session UUID

        Returns:
            Updated DiagnosticSession

        Raises:
            ValueError: If session not found
        """
        session = await self.get_session_by_id(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        session.status = "expired"
        await self.session.flush()
        await self.session.refresh(session)

        logger.info(
            "diagnostic_session_expired",
            session_id=str(session_id),
            user_id=str(session.user_id),
        )

        return session

    async def mark_reset(
        self,
        session_id: UUID,
    ) -> DiagnosticSession:
        """
        Mark a session as reset.

        Args:
            session_id: Session UUID

        Returns:
            Updated DiagnosticSession

        Raises:
            ValueError: If session not found
        """
        session = await self.get_session_by_id(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        session.status = "reset"
        await self.session.flush()
        await self.session.refresh(session)

        logger.info(
            "diagnostic_session_reset",
            session_id=str(session_id),
            user_id=str(session.user_id),
        )

        return session

    async def expire_stale_sessions(
        self,
        timeout_minutes: int = 30,
    ) -> int:
        """
        Batch expire sessions that have been inactive for too long.

        Args:
            timeout_minutes: Minutes after which a session is considered stale

        Returns:
            Number of sessions expired
        """
        cutoff_time = datetime.now(UTC) - timedelta(minutes=timeout_minutes)

        result = await self.session.execute(
            update(DiagnosticSession)
            .where(DiagnosticSession.status == "in_progress")
            .where(DiagnosticSession.started_at < cutoff_time)
            .values(status="expired")
        )
        await self.session.flush()

        expired_count = result.rowcount
        if expired_count > 0:
            logger.info(
                "diagnostic_sessions_batch_expired",
                expired_count=expired_count,
                timeout_minutes=timeout_minutes,
            )

        return expired_count

    async def get_completed_session(
        self,
        user_id: UUID,
        enrollment_id: UUID,
    ) -> DiagnosticSession | None:
        """
        Get the most recent completed diagnostic session for a user's enrollment.

        Args:
            user_id: User UUID
            enrollment_id: Enrollment UUID

        Returns:
            DiagnosticSession if completed session exists, None otherwise
        """
        result = await self.session.execute(
            select(DiagnosticSession)
            .where(DiagnosticSession.user_id == user_id)
            .where(DiagnosticSession.enrollment_id == enrollment_id)
            .where(DiagnosticSession.status == "completed")
            .order_by(DiagnosticSession.completed_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
