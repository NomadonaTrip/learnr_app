"""
DiagnosticSessionService for managing diagnostic session lifecycle.
Handles session creation, resumption, progress tracking, and reset functionality.
"""
from datetime import UTC, datetime, timedelta
from uuid import UUID

import structlog

from src.models.diagnostic_session import DiagnosticSession
from src.models.question import Question
from src.repositories.belief_repository import BeliefRepository
from src.repositories.diagnostic_session_repository import DiagnosticSessionRepository
from src.repositories.question_repository import QuestionRepository
from src.services.diagnostic_service import DiagnosticService

logger = structlog.get_logger(__name__)


class DiagnosticSessionService:
    """
    Service for managing diagnostic session lifecycle.

    Handles:
    - Creating new diagnostic sessions with optimal question selection
    - Resuming existing active sessions
    - Recording answers and advancing progress
    - Session expiration and reset
    """

    SESSION_TIMEOUT_MINUTES = 30

    def __init__(
        self,
        session_repo: DiagnosticSessionRepository,
        belief_repo: BeliefRepository,
        question_repo: QuestionRepository,
        diagnostic_service: DiagnosticService,
    ):
        """
        Initialize diagnostic session service.

        Args:
            session_repo: Repository for session operations
            belief_repo: Repository for belief state operations
            question_repo: Repository for question operations
            diagnostic_service: Service for question selection
        """
        self.session_repo = session_repo
        self.belief_repo = belief_repo
        self.question_repo = question_repo
        self.diagnostic_service = diagnostic_service

    async def start_or_resume_session(
        self,
        user_id: UUID,
        enrollment_id: UUID,
        course_id: UUID,
    ) -> tuple[DiagnosticSession, list[Question], bool]:
        """
        Start a new diagnostic session or resume an existing one.

        If an active session exists:
        - If not expired: resume and return remaining questions
        - If expired: mark as expired and create new session

        If no active session: create new session with optimal questions.

        Args:
            user_id: User UUID
            enrollment_id: Enrollment UUID
            course_id: Course UUID (needed for question selection)

        Returns:
            Tuple of:
            - DiagnosticSession object
            - List of Question objects (remaining questions if resuming)
            - bool: True if session was resumed, False if newly created
        """
        # Check for existing active session
        existing = await self.session_repo.get_active_session(user_id, enrollment_id)

        if existing:
            if self._is_session_expired(existing):
                # Expire old session, create new
                await self.session_repo.mark_expired(existing.id)
                logger.info(
                    "diagnostic_session_expired_on_resume",
                    user_id=str(user_id),
                    session_id=str(existing.id),
                    elapsed_minutes=(
                        datetime.now(UTC) - existing.started_at.replace(tzinfo=UTC)
                    ).total_seconds() / 60,
                )
                session, questions = await self._create_new_session(
                    user_id, enrollment_id, course_id
                )
                return session, questions, False
            else:
                # Resume existing session - return remaining questions
                questions = await self._get_remaining_questions(existing)
                logger.info(
                    "diagnostic_session_resumed",
                    user_id=str(user_id),
                    session_id=str(existing.id),
                    current_index=existing.current_index,
                    questions_remaining=len(questions),
                )
                return existing, questions, True

        # No active session - create new
        session, questions = await self._create_new_session(
            user_id, enrollment_id, course_id
        )
        return session, questions, False

    async def _create_new_session(
        self,
        user_id: UUID,
        enrollment_id: UUID,
        course_id: UUID,
    ) -> tuple[DiagnosticSession, list[Question]]:
        """
        Create a new diagnostic session with selected questions.

        Args:
            user_id: User UUID
            enrollment_id: Enrollment UUID
            course_id: Course UUID

        Returns:
            Tuple of (DiagnosticSession, list[Question])
        """
        # Select optimal questions for diagnostic
        questions, covered_concepts, total_concepts = (
            await self.diagnostic_service.select_diagnostic_questions(
                course_id=course_id,
                target_count=15,
            )
        )

        question_ids = [str(q.id) for q in questions]

        session = await self.session_repo.create_session(
            user_id=user_id,
            enrollment_id=enrollment_id,
            question_ids=question_ids,
        )

        logger.info(
            "diagnostic_session_created",
            user_id=str(user_id),
            session_id=str(session.id),
            question_count=len(questions),
            concepts_covered=len(covered_concepts),
        )

        return session, questions

    async def validate_session_for_answer(
        self,
        session_id: UUID,
        question_id: UUID,
        user_id: UUID,
    ) -> DiagnosticSession:
        """
        Validate session state before allowing an answer submission.

        This validates basic session state without checking question position.
        The question position validation is done later in record_answer to allow
        for proper 404 handling when the question doesn't exist.

        Args:
            session_id: Session UUID
            question_id: Question UUID being answered (used only for already-answered check)
            user_id: User UUID (for authorization check)

        Returns:
            DiagnosticSession if valid

        Raises:
            ValueError: If session not found, unauthorized, or invalid state
            AlreadyAnsweredError: If question was already answered
        """
        session = await self.session_repo.get_session_by_id(session_id)

        if not session:
            raise ValueError("Session not found")

        if session.user_id != user_id:
            raise ValueError("Unauthorized: session belongs to different user")

        if session.status != "in_progress":
            raise ValueError(f"Session is {session.status}, cannot record answer")

        if session.current_index >= len(session.question_ids):
            raise ValueError("Session has no more questions")

        # Check if question was already answered
        question_id_str = str(question_id)
        already_answered_ids = session.question_ids[:session.current_index]
        if question_id_str in already_answered_ids:
            from src.exceptions import AlreadyAnsweredError
            raise AlreadyAnsweredError(
                "Question already answered in this session",
                {"session_id": str(session_id), "question_id": str(question_id)},
            )

        # Note: Question position validation is NOT done here.
        # It happens in record_answer after question existence is verified,
        # so we can return 404 for nonexistent questions.

        return session

    async def record_answer(
        self,
        session_id: UUID,
        question_id: UUID,
        user_id: UUID,
    ) -> DiagnosticSession:
        """
        Record answer submission and advance session progress.

        Note: Belief updates are handled separately by BeliefUpdater service.
        This method only tracks session progress.

        Args:
            session_id: Session UUID
            question_id: Question UUID being answered
            user_id: User UUID (for validation)

        Returns:
            Updated DiagnosticSession

        Raises:
            ValueError: If session not found, unauthorized, or invalid state
        """
        session = await self.session_repo.get_session_by_id(session_id)

        if not session:
            raise ValueError("Session not found")

        # Debug logging for user mismatch investigation
        logger.info(
            "record_answer_user_check",
            session_id=str(session_id),
            session_user_id=str(session.user_id),
            request_user_id=str(user_id),
            user_ids_match=session.user_id == user_id,
            session_user_id_type=type(session.user_id).__name__,
            request_user_id_type=type(user_id).__name__,
        )

        if session.user_id != user_id:
            logger.warning(
                "user_id_mismatch_details",
                session_user_id_str=str(session.user_id),
                request_user_id_str=str(user_id),
                session_user_id_repr=repr(session.user_id),
                request_user_id_repr=repr(user_id),
            )
            raise ValueError("Unauthorized: session belongs to different user")

        if session.status != "in_progress":
            raise ValueError(f"Session is {session.status}, cannot record answer")

        # Validate question is at expected position
        if session.current_index >= len(session.question_ids):
            raise ValueError("Session has no more questions")

        # Check if question was already answered (appears before current index)
        question_id_str = str(question_id)
        already_answered_ids = session.question_ids[:session.current_index]
        if question_id_str in already_answered_ids:
            from src.exceptions import AlreadyAnsweredError
            raise AlreadyAnsweredError(
                "Question already answered in this session",
                {"session_id": str(session_id), "question_id": str(question_id)},
            )

        expected_question_id = session.question_ids[session.current_index]
        if question_id_str != expected_question_id:
            raise ValueError(
                f"Question {question_id} does not match expected position "
                f"(expected {expected_question_id})"
            )

        # Advance progress
        session = await self.session_repo.increment_progress(session_id)

        # Check if completed
        if session.current_index >= len(session.question_ids):
            session = await self.session_repo.mark_completed(session_id)
            logger.info(
                "diagnostic_session_completed",
                user_id=str(user_id),
                session_id=str(session_id),
                duration_seconds=(
                    (session.completed_at.replace(tzinfo=None) - session.started_at.replace(tzinfo=None)).total_seconds()
                    if session.completed_at
                    else 0
                ),
            )

        return session

    async def reset_diagnostic(
        self,
        user_id: UUID,
        enrollment_id: UUID,
    ) -> dict:
        """
        Reset diagnostic: clear session and reset all belief states.

        This allows the user to retake the diagnostic assessment from scratch.

        Args:
            user_id: User UUID
            enrollment_id: Enrollment UUID

        Returns:
            Dict with reset results:
            - session_cleared: bool
            - beliefs_reset_count: int
        """
        # Mark any active session as reset
        session_cleared = False
        active_session = await self.session_repo.get_active_session(
            user_id, enrollment_id
        )
        if active_session:
            await self.session_repo.mark_reset(active_session.id)
            session_cleared = True

        # Reset all belief states to Beta(1,1)
        beliefs_reset = await self.belief_repo.reset_beliefs_for_enrollment(
            user_id=user_id,
            enrollment_id=enrollment_id,
            alpha=1.0,
            beta=1.0,
        )

        logger.info(
            "diagnostic_reset_completed",
            user_id=str(user_id),
            enrollment_id=str(enrollment_id),
            session_cleared=session_cleared,
            beliefs_reset=beliefs_reset,
        )

        return {
            "session_cleared": session_cleared,
            "beliefs_reset_count": beliefs_reset,
        }

    def _is_session_expired(self, session: DiagnosticSession) -> bool:
        """
        Check if a session has exceeded the timeout.

        Args:
            session: DiagnosticSession to check

        Returns:
            True if session is expired, False otherwise
        """
        timeout = timedelta(minutes=self.SESSION_TIMEOUT_MINUTES)
        # Ensure timezone-aware comparison
        started_at = session.started_at
        if started_at.tzinfo is None:
            started_at = started_at.replace(tzinfo=UTC)
        return datetime.now(UTC) > started_at + timeout

    async def _get_remaining_questions(
        self,
        session: DiagnosticSession,
    ) -> list[Question]:
        """
        Get questions starting from current_index.

        Args:
            session: DiagnosticSession to get questions for

        Returns:
            List of remaining Question objects in order
        """
        remaining_ids = session.question_ids[session.current_index:]
        return await self.question_repo.get_questions_by_ids(
            remaining_ids,
            preserve_order=True,
            load_concepts=True,
        )
