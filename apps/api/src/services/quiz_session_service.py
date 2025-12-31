"""
QuizSessionService for managing adaptive quiz session lifecycle.
Handles session creation, resumption, pause/resume, and termination.
"""
from datetime import UTC, datetime, timedelta
from uuid import UUID

import structlog

from src.models.quiz_session import QuizSession
from src.repositories.concept_repository import ConceptRepository
from src.repositories.course_repository import CourseRepository
from src.repositories.quiz_session_repository import QuizSessionRepository
from src.schemas.quiz_session import QuizSessionCreate, QuizSessionType

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
    - Focused session validation
    """

    SESSION_TIMEOUT_HOURS = 2

    def __init__(
        self,
        session_repo: QuizSessionRepository,
        course_repo: CourseRepository | None = None,
        concept_repo: ConceptRepository | None = None,
    ):
        """
        Initialize quiz session service.

        Args:
            session_repo: Repository for session operations
            course_repo: Repository for course operations (optional, for focused session validation)
            concept_repo: Repository for concept operations (optional, for focused session validation)
        """
        self.session_repo = session_repo
        self.course_repo = course_repo
        self.concept_repo = concept_repo

    async def start_session(
        self,
        user_id: UUID,
        enrollment_id: UUID,
        session_data: QuizSessionCreate,
        course_id: UUID | None = None,
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
            course_id: Course UUID (required for focused session validation)

        Returns:
            Tuple of:
            - QuizSession object
            - bool: True if existing session was resumed, False if newly created

        Raises:
            ValueError: If focused session targets are invalid
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
            elif self._can_resume_session(existing, session_data):
                # Return existing active session only if it matches requested type/target
                logger.info(
                    "quiz_session_resumed",
                    user_id=str(user_id),
                    session_id=str(existing.id),
                    is_paused=existing.is_paused,
                    total_questions=existing.total_questions,
                )
                return existing, True
            else:
                # End existing session because user wants a different session type/target
                await self.session_repo.mark_ended(existing.id)
                logger.info(
                    "quiz_session_replaced",
                    user_id=str(user_id),
                    old_session_id=str(existing.id),
                    old_session_type=existing.session_type,
                    new_session_type=session_data.session_type.value,
                    reason="session_type_mismatch",
                )

        # Validate focused session targets if applicable
        await self._validate_focused_session_targets(session_data, course_id)

        # Prepare target_concept_ids for storage
        target_concept_ids: list[str] | None = None
        if session_data.target_concept_ids:
            target_concept_ids = [str(cid) for cid in session_data.target_concept_ids]

        # Create new session with conflict handling
        # This handles race conditions and orphaned active sessions
        try:
            session = await self.session_repo.create_session(
                user_id=user_id,
                enrollment_id=enrollment_id,
                session_type=session_data.session_type.value,
                question_strategy=session_data.question_strategy.value,
                knowledge_area_filter=session_data.knowledge_area_filter,
                target_concept_ids=target_concept_ids,
            )
        except Exception as e:
            # Check if this is a unique constraint violation on active sessions
            if "idx_quiz_sessions_user_active_unique" in str(e):
                logger.warning(
                    "quiz_session_conflict_detected",
                    user_id=str(user_id),
                    error=str(e),
                )
                # Force-end any orphaned active sessions and retry
                await self.session_repo.force_end_active_sessions(user_id)
                session = await self.session_repo.create_session(
                    user_id=user_id,
                    enrollment_id=enrollment_id,
                    session_type=session_data.session_type.value,
                    question_strategy=session_data.question_strategy.value,
                    knowledge_area_filter=session_data.knowledge_area_filter,
                    target_concept_ids=target_concept_ids,
                )
                logger.info(
                    "quiz_session_created_after_conflict_resolution",
                    user_id=str(user_id),
                    session_id=str(session.id),
                )
            else:
                raise

        # Log session creation with focus details if applicable
        focus_type = None
        if session_data.session_type == QuizSessionType.FOCUSED_KA:
            focus_type = "ka"
        elif session_data.session_type == QuizSessionType.FOCUSED_CONCEPT:
            focus_type = "concept"

        if focus_type:
            logger.info(
                "focused_session_started",
                user_id=str(user_id),
                session_id=str(session.id),
                focus_type=focus_type,
                target_id=session_data.knowledge_area_filter if focus_type == "ka" else None,
                target_concept_count=len(target_concept_ids) if target_concept_ids else 0,
            )
        else:
            logger.info(
                "quiz_session_created",
                user_id=str(user_id),
                session_id=str(session.id),
                session_type=session_data.session_type.value,
                question_strategy=session_data.question_strategy.value,
            )

        return session, False

    async def _validate_focused_session_targets(
        self,
        session_data: QuizSessionCreate,
        course_id: UUID | None,
    ) -> None:
        """
        Validate focused session targets exist and belong to the course.

        Args:
            session_data: Session configuration data
            course_id: Course UUID for validation

        Raises:
            ValueError: If validation fails
        """
        # No validation needed for non-focused sessions
        if session_data.session_type not in (
            QuizSessionType.FOCUSED_KA,
            QuizSessionType.FOCUSED_CONCEPT,
        ):
            return

        # Validate FOCUSED_KA: knowledge_area_filter must exist in course
        if session_data.session_type == QuizSessionType.FOCUSED_KA:
            if not session_data.knowledge_area_filter:
                raise ValueError("knowledge_area_filter required for focused_ka sessions")

            if course_id and self.course_repo:
                course = await self.course_repo.get_by_id(course_id)
                if course:
                    ka_ids = [ka.get("id") for ka in (course.knowledge_areas or [])]
                    if session_data.knowledge_area_filter not in ka_ids:
                        raise ValueError(
                            f"Invalid knowledge area: {session_data.knowledge_area_filter}"
                        )

        # Validate FOCUSED_CONCEPT: target_concept_ids must exist and belong to course
        if session_data.session_type == QuizSessionType.FOCUSED_CONCEPT:
            if not session_data.target_concept_ids:
                raise ValueError("target_concept_ids required for focused_concept sessions")

            if course_id and self.concept_repo:
                concepts = await self.concept_repo.get_by_ids(
                    list(session_data.target_concept_ids)
                )

                # Check if all concepts were found
                found_ids = {c.id for c in concepts}
                missing_ids = set(session_data.target_concept_ids) - found_ids
                if missing_ids:
                    raise ValueError(f"Invalid concept IDs: {list(missing_ids)}")

                # Check if all concepts belong to the course
                invalid_course_concepts = [
                    c.id for c in concepts if c.course_id != course_id
                ]
                if invalid_course_concepts:
                    raise ValueError(
                        f"Concepts do not belong to course: {invalid_course_concepts}"
                    )

    def _can_resume_session(
        self,
        existing: QuizSession,
        requested: QuizSessionCreate,
    ) -> bool:
        """
        Check if an existing session can be resumed for the requested session type.

        A session can be resumed only if:
        - Session types match
        - For focused_ka: knowledge_area_filter matches
        - For focused_concept: target_concept_ids match

        Args:
            existing: Existing active session
            requested: Requested session configuration

        Returns:
            True if session can be resumed, False if a new session should be created
        """
        # Session types must match
        if existing.session_type != requested.session_type.value:
            return False

        # For focused_ka, KA filter must match
        if requested.session_type == QuizSessionType.FOCUSED_KA:
            if existing.knowledge_area_filter != requested.knowledge_area_filter:
                return False

        # For focused_concept, target concepts must match
        if requested.session_type == QuizSessionType.FOCUSED_CONCEPT:
            existing_targets = set(existing.target_concept_ids or [])
            requested_targets = set(str(cid) for cid in (requested.target_concept_ids or []))
            if existing_targets != requested_targets:
                return False

        return True

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
