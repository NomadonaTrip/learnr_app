"""
QuizAnswerService for processing answer submissions and providing feedback.
Story 4.3: Answer Submission and Immediate Feedback
"""
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import structlog

from src.exceptions import AlreadyAnsweredError, InvalidQuestionError, InvalidSessionError
from src.models.question import Question
from src.models.quiz_response import QuizResponse
from src.repositories.question_repository import QuestionRepository
from src.repositories.quiz_session_repository import QuizSessionRepository
from src.repositories.response_repository import ResponseRepository
from src.schemas.quiz import AnswerResponse, ConceptUpdate, SessionStats

logger = structlog.get_logger(__name__)


class QuizAnswerService:
    """
    Service for processing quiz answer submissions.

    Handles:
    - Answer correctness determination
    - Response recording with idempotency
    - Session statistics updates
    - Feedback generation (explanation, concepts updated)
    """

    def __init__(
        self,
        response_repo: ResponseRepository,
        question_repo: QuestionRepository,
        session_repo: QuizSessionRepository,
    ):
        """
        Initialize quiz answer service.

        Args:
            response_repo: Repository for response operations
            question_repo: Repository for question lookups
            session_repo: Repository for session operations
        """
        self.response_repo = response_repo
        self.question_repo = question_repo
        self.session_repo = session_repo

    async def submit_answer(
        self,
        user_id: UUID,
        session_id: UUID,
        question_id: UUID,
        selected_answer: str,
        request_id: UUID | None = None,
        client_timestamp: datetime | None = None,
        server_question_served_at: datetime | None = None,
    ) -> tuple[AnswerResponse, bool]:
        """
        Submit an answer and get immediate feedback.

        This method handles:
        1. Idempotency check (return cached response if request_id exists)
        2. Session validation (exists, active, owned by user)
        3. Question validation (exists, active)
        4. Duplicate answer check (question not already answered in session)
        5. Correctness determination
        6. Response recording
        7. Session statistics update
        8. Feedback generation

        Args:
            user_id: User UUID submitting the answer
            session_id: Quiz session UUID
            question_id: Question UUID being answered
            selected_answer: Selected answer option (A, B, C, or D)
            request_id: Optional idempotency key
            client_timestamp: Optional client-provided timestamp for time calculation
            server_question_served_at: Optional server timestamp when question was served

        Returns:
            Tuple of:
            - AnswerResponse with feedback
            - bool: True if response was cached (idempotent), False if newly created

        Raises:
            InvalidSessionError: If session not found, expired, or not owned by user
            InvalidQuestionError: If question not found or inactive
            AlreadyAnsweredError: If question already answered in this session
        """
        start_time = datetime.now(UTC)

        # 1. Idempotency check
        if request_id:
            existing_response = await self.response_repo.get_by_request_id(request_id)
            if existing_response:
                logger.info(
                    "quiz_answer_idempotent_hit",
                    request_id=str(request_id),
                    response_id=str(existing_response.id),
                )
                # Fetch question to build response
                question = await self.question_repo.get_question_by_id(
                    existing_response.question_id,
                    load_concepts=True,
                )
                # Get session stats
                session = await self.session_repo.get_session_by_id(session_id)
                return self._build_response(
                    existing_response, question, session
                ), True

        # 2. Session validation
        session = await self.session_repo.get_session_by_id(session_id)
        if not session:
            raise InvalidSessionError("Session not found", {"session_id": str(session_id)})

        if session.user_id != user_id:
            raise InvalidSessionError(
                "Unauthorized: session belongs to different user",
                {"session_id": str(session_id)},
            )

        if session.ended_at is not None:
            raise InvalidSessionError(
                "Session has ended",
                {"session_id": str(session_id)},
            )

        # Check for session expiration (2 hours timeout)
        from datetime import timedelta
        if session.updated_at:
            updated_at = session.updated_at
            if updated_at.tzinfo is None:
                updated_at = updated_at.replace(tzinfo=UTC)
            if datetime.now(UTC) > updated_at + timedelta(hours=2):
                raise InvalidSessionError(
                    "Session has expired",
                    {"session_id": str(session_id)},
                )

        # 3. Question validation
        question = await self.question_repo.get_question_by_id(
            question_id,
            load_concepts=True,
        )
        if not question:
            raise InvalidQuestionError(
                "Question not found",
                {"question_id": str(question_id)},
            )

        if not question.is_active:
            raise InvalidQuestionError(
                "Question is not active",
                {"question_id": str(question_id)},
            )

        # 4. Duplicate answer check
        already_answered = await self.response_repo.check_already_answered(
            session_id, question_id
        )
        if already_answered:
            raise AlreadyAnsweredError(
                "Question already answered in this session",
                {
                    "session_id": str(session_id),
                    "question_id": str(question_id),
                },
            )

        # 5. Determine correctness
        selected_answer = selected_answer.upper()
        is_correct = selected_answer == question.correct_answer

        # 6. Calculate time taken
        time_taken_ms = self._calculate_time_taken(
            client_timestamp,
            server_question_served_at,
            start_time,
        )

        # 7. Stub belief updates (Story 4.4 integration point)
        # TODO: Story 4.4 - Replace with actual belief update
        # belief_updates = await belief_updater.update_beliefs(user_id, question, is_correct)
        belief_updates: list[dict[str, Any]] = []

        # 8. Create response record
        response = await self.response_repo.create(
            user_id=user_id,
            session_id=session_id,
            question_id=question_id,
            selected_answer=selected_answer,
            is_correct=is_correct,
            time_taken_ms=time_taken_ms,
            request_id=request_id,
            belief_updates=belief_updates,
        )

        # 9. Update session statistics
        session = await self.session_repo.increment_question_count(
            session_id, is_correct
        )

        # 10. Log and return
        elapsed_ms = (datetime.now(UTC) - start_time).total_seconds() * 1000
        logger.info(
            "quiz_answer_submitted",
            session_id=str(session_id),
            question_id=str(question_id),
            is_correct=is_correct,
            time_taken_ms=time_taken_ms,
            processing_ms=round(elapsed_ms, 2),
            request_id=str(request_id) if request_id else None,
        )

        return self._build_response(response, question, session), False

    def _calculate_time_taken(
        self,
        client_timestamp: datetime | None,
        server_question_served_at: datetime | None,
        submission_time: datetime,
    ) -> int | None:
        """
        Calculate time taken to answer in milliseconds.

        Priority:
        1. Client timestamp if provided
        2. Server question served timestamp if available
        3. None if neither available

        Args:
            client_timestamp: Client-provided timestamp
            server_question_served_at: Server timestamp when question was served
            submission_time: Time when answer was received

        Returns:
            Time taken in milliseconds, or None if not calculable
        """
        if client_timestamp:
            # Use client timestamp (trust client for now)
            if client_timestamp.tzinfo is None:
                client_timestamp = client_timestamp.replace(tzinfo=UTC)
            delta = submission_time - client_timestamp
            return max(0, int(delta.total_seconds() * 1000))

        if server_question_served_at:
            # Use server timestamp
            if server_question_served_at.tzinfo is None:
                server_question_served_at = server_question_served_at.replace(tzinfo=UTC)
            delta = submission_time - server_question_served_at
            return max(0, int(delta.total_seconds() * 1000))

        return None

    def _build_response(
        self,
        response: QuizResponse,
        question: Question,
        session,
    ) -> AnswerResponse:
        """
        Build the answer response with feedback.

        Args:
            response: The quiz response record
            question: The question that was answered
            session: The quiz session

        Returns:
            AnswerResponse with all feedback fields
        """
        # Build concepts_updated from belief_updates or empty for now
        concepts_updated: list[ConceptUpdate] = []

        # Stub: In Story 4.4, this will be populated from belief updates
        # For now, return empty list
        if response.belief_updates:
            for update in response.belief_updates:
                concepts_updated.append(
                    ConceptUpdate(
                        concept_id=UUID(update["concept_id"]),
                        name=update.get("concept_name", "Unknown"),
                        new_mastery=(
                            update.get("new_alpha", 1.0)
                            / (update.get("new_alpha", 1.0) + update.get("new_beta", 1.0))
                        ),
                    )
                )

        # Calculate session stats
        accuracy = session.correct_count / session.total_questions if session.total_questions > 0 else 0.0

        session_stats = SessionStats(
            questions_answered=session.total_questions,
            accuracy=accuracy,
            total_info_gain=0.0,  # Stub: Story 4.4 will populate
            coverage_progress=0.0,  # Stub: Could be calculated from concept coverage
        )

        return AnswerResponse(
            is_correct=response.is_correct,
            correct_answer=question.correct_answer,
            explanation=question.explanation or "",
            concepts_updated=concepts_updated,
            session_stats=session_stats,
        )
