"""
QuizSessionService for managing adaptive quiz session lifecycle.
Handles session creation, resumption, pause/resume, and termination.
"""
from datetime import UTC, datetime, timedelta
from uuid import UUID

import structlog

from src.models.quiz_session import QuizSession
from src.repositories.quiz_session_repository import QuizSessionRepository
from src.schemas.quiz_session import QuizSessionCreate

logger = structlog.get_logger(__name__)


class QuizSessionService:
    """
    Service for managing adaptive quiz session lifecycle.

    Handles:
    - Creating new quiz sessions
    - Resuming existing active sessions
    - Pausing and resuming sessions
    - Ending sessions with optimistic locking
    - Session expiration detection
    """

    SESSION_TIMEOUT_HOURS = 2

    def __init__(
        self,
        session_repo: QuizSessionRepository,
    ):
        """
        Initialize quiz session service.

        Args:
            session_repo: Repository for session operations
        """
        self.session_repo = session_repo

    async def start_session(
        self,
        user_id: UUID,
        enrollment_id: UUID,
        session_data: QuizSessionCreate,
    ) -> tuple[QuizSession, bool]:
        """
        Start a new quiz session or return existing active session.

        If an active session exists:
        - If not expired: return existing session (is_resumed=True)
        - If expired: end it and create new session

        If no active session: create new session.

        Args:
            user_id: User UUID
            enrollment_id: Enrollment UUID
            session_data: Session configuration data

        Returns:
            Tuple of:
            - QuizSession object
            - bool: True if existing session was resumed, False if newly created
        """
        # Check for existing active session
        existing = await self.session_repo.get_active_session(user_id)

        if existing:
            if self._is_session_expired(existing):
                # End expired session, create new
                await self.session_repo.mark_ended(existing.id)
                logger.info(
                    "quiz_session_expired_on_start",
                    user_id=str(user_id),
                    session_id=str(existing.id),
                    elapsed_hours=self._get_elapsed_hours(existing),
                )
            else:
                # Return existing active session
                logger.info(
                    "quiz_session_resumed",
                    user_id=str(user_id),
                    session_id=str(existing.id),
                    is_paused=existing.is_paused,
                    total_questions=existing.total_questions,
                )
                return existing, True

        # Create new session
        session = await self.session_repo.create_session(
            user_id=user_id,
            enrollment_id=enrollment_id,
            session_type=session_data.session_type.value,
            question_strategy=session_data.question_strategy.value,
            knowledge_area_filter=session_data.knowledge_area_filter,
        )

        logger.info(
            "quiz_session_created",
            user_id=str(user_id),
            session_id=str(session.id),
            session_type=session_data.session_type.value,
            question_strategy=session_data.question_strategy.value,
        )

        return session, False

    async def get_session(
        self,
        session_id: UUID,
        user_id: UUID,
    ) -> QuizSession:
        """
        Get a session by ID with ownership validation.

        Args:
            session_id: Session UUID
            user_id: User UUID (for ownership validation)

        Returns:
            QuizSession object

        Raises:
            ValueError: If session not found or user doesn't own it
        """
        session = await self.session_repo.get_session_by_id(session_id)

        if not session:
            raise ValueError("Session not found")

        if session.user_id != user_id:
            raise ValueError("Unauthorized: session belongs to different user")

        return session

    async def pause_session(
        self,
        session_id: UUID,
        user_id: UUID,
    ) -> QuizSession:
        """
        Pause an active session.

        Args:
            session_id: Session UUID
            user_id: User UUID (for ownership validation)

        Returns:
            Updated QuizSession

        Raises:
            ValueError: If session not found, unauthorized, or not active
        """
        session = await self.get_session(session_id, user_id)

        if session.ended_at is not None:
            raise ValueError("Cannot pause ended session")

        if session.is_paused:
            raise ValueError("Session is already paused")

        # Check for expiration
        if self._is_session_expired(session):
            raise ValueError("Session has expired")

        session = await self.session_repo.mark_paused(session_id)

        logger.info(
            "quiz_session_paused",
            user_id=str(user_id),
            session_id=str(session_id),
            total_questions=session.total_questions,
        )

        return session

    async def resume_session(
        self,
        session_id: UUID,
        user_id: UUID,
    ) -> QuizSession:
        """
        Resume a paused session.

        Args:
            session_id: Session UUID
            user_id: User UUID (for ownership validation)

        Returns:
            Updated QuizSession

        Raises:
            ValueError: If session not found, unauthorized, or not paused
        """
        session = await self.get_session(session_id, user_id)

        if session.ended_at is not None:
            raise ValueError("Cannot resume ended session")

        if not session.is_paused:
            raise ValueError("Session is not paused")

        # Check for expiration
        if self._is_session_expired(session):
            raise ValueError("Session has expired")

        session = await self.session_repo.mark_resumed(session_id)

        logger.info(
            "quiz_session_resumed",
            user_id=str(user_id),
            session_id=str(session_id),
            total_questions=session.total_questions,
        )

        return session

    async def end_session(
        self,
        session_id: UUID,
        user_id: UUID,
        expected_version: int,
    ) -> QuizSession:
        """
        End a session with optimistic locking.

        Args:
            session_id: Session UUID
            user_id: User UUID (for ownership validation)
            expected_version: Expected version for optimistic locking

        Returns:
            Updated QuizSession

        Raises:
            ValueError: If session not found, unauthorized, already ended,
                       or version mismatch
        """
        session = await self.get_session(session_id, user_id)

        if session.ended_at is not None:
            raise ValueError("Session is already ended")

        # Optimistic locking check
        if session.version != expected_version:
            raise ValueError(
                f"Version conflict: expected {expected_version}, "
                f"actual {session.version}"
            )

        session = await self.session_repo.mark_ended(session_id)

        accuracy = session.accuracy

        logger.info(
            "quiz_session_ended",
            user_id=str(user_id),
            session_id=str(session_id),
            total_questions=session.total_questions,
            correct_count=session.correct_count,
            accuracy=round(accuracy, 2),
        )

        return session

    def derive_status(self, session: QuizSession) -> str:
        """
        Derive session status from database columns.

        This is a utility method that can be used externally.
        The QuizSession model also has this as a property.

        Args:
            session: QuizSession object

        Returns:
            Status string: 'active', 'paused', 'completed', or 'expired'
        """
        if session.ended_at is not None:
            return "completed"

        if self._is_session_expired(session):
            return "expired"

        if session.is_paused:
            return "paused"

        return "active"

    def _is_session_expired(self, session: QuizSession) -> bool:
        """
        Check if a session has exceeded the timeout (2 hours).

        Based on updated_at timestamp, not started_at.
        This allows sessions to stay active as long as there's activity.

        Args:
            session: QuizSession to check

        Returns:
            True if session is expired, False otherwise
        """
        timeout = timedelta(hours=self.SESSION_TIMEOUT_HOURS)
        # Ensure timezone-aware comparison
        updated_at = session.updated_at
        if updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=UTC)
        return datetime.now(UTC) > updated_at + timeout

    def _get_elapsed_hours(self, session: QuizSession) -> float:
        """
        Get elapsed hours since session was last updated.

        Args:
            session: QuizSession to check

        Returns:
            Elapsed hours as float
        """
        updated_at = session.updated_at
        if updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=UTC)
        delta = datetime.now(UTC) - updated_at
        return delta.total_seconds() / 3600
