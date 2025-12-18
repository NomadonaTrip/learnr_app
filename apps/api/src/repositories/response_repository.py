"""
Response repository for quiz answer data access operations.
Story 4.3: Answer Submission and Immediate Feedback
"""
import logging
from typing import Any
from uuid import UUID

from sqlalchemy import Integer, func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.quiz_response import QuizResponse

logger = logging.getLogger(__name__)


class ResponseRepository:
    """Repository for quiz response data access operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize response repository.

        Args:
            db: AsyncSession for database operations
        """
        self.db = db

    async def create(
        self,
        user_id: UUID,
        session_id: UUID,
        question_id: UUID,
        selected_answer: str,
        is_correct: bool,
        time_taken_ms: int | None = None,
        request_id: UUID | None = None,
        belief_updates: list[dict[str, Any]] | None = None,
    ) -> QuizResponse:
        """
        Create a new quiz response record.

        Args:
            user_id: User UUID who submitted the answer
            session_id: Quiz session UUID
            question_id: Question UUID being answered
            selected_answer: Selected answer option (A, B, C, or D)
            is_correct: Whether the answer was correct
            time_taken_ms: Time taken to answer in milliseconds
            request_id: Optional idempotency key
            belief_updates: Optional belief update snapshot (JSON)

        Returns:
            Created QuizResponse instance

        Raises:
            IntegrityError: If request_id already exists (duplicate request)
            SQLAlchemyError: If database operation fails
        """
        try:
            response = QuizResponse(
                user_id=user_id,
                session_id=session_id,
                question_id=question_id,
                selected_answer=selected_answer.upper(),
                is_correct=is_correct,
                time_taken_ms=time_taken_ms,
                request_id=request_id,
                belief_updates=belief_updates,
            )
            self.db.add(response)
            await self.db.flush()
            await self.db.refresh(response)
            logger.info(
                f"Created quiz response: {response.id} "
                f"(session={session_id}, question={question_id}, correct={is_correct})"
            )
            return response
        except IntegrityError:
            logger.warning(f"Duplicate request_id detected: {request_id}")
            raise
        except SQLAlchemyError as e:
            logger.error(f"Failed to create quiz response: {str(e)}")
            raise

    async def get_by_id(self, response_id: UUID) -> QuizResponse | None:
        """
        Retrieve a response by its ID.

        Args:
            response_id: Response UUID

        Returns:
            QuizResponse instance or None if not found
        """
        result = await self.db.execute(
            select(QuizResponse).where(QuizResponse.id == response_id)
        )
        return result.scalar_one_or_none()

    async def get_by_request_id(self, request_id: UUID) -> QuizResponse | None:
        """
        Retrieve a response by its idempotency key.

        Used for idempotent answer submission - if a response exists
        with this request_id, return it instead of creating a new one.

        Args:
            request_id: Idempotency key UUID

        Returns:
            QuizResponse instance or None if not found
        """
        if request_id is None:
            return None

        result = await self.db.execute(
            select(QuizResponse).where(QuizResponse.request_id == request_id)
        )
        return result.scalar_one_or_none()

    async def get_by_session_id(
        self,
        session_id: UUID,
        load_question: bool = False,
    ) -> list[QuizResponse]:
        """
        Retrieve all responses for a quiz session.

        Args:
            session_id: Quiz session UUID
            load_question: Whether to eagerly load question relationships

        Returns:
            List of QuizResponse instances ordered by created_at
        """
        query = (
            select(QuizResponse)
            .where(QuizResponse.session_id == session_id)
            .order_by(QuizResponse.created_at)
        )

        if load_question:
            query = query.options(selectinload(QuizResponse.question))

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def check_already_answered(
        self,
        session_id: UUID,
        question_id: UUID,
    ) -> bool:
        """
        Check if a question has already been answered in a session.

        Used to prevent duplicate answers within the same session.

        Args:
            session_id: Quiz session UUID
            question_id: Question UUID

        Returns:
            True if question already answered, False otherwise
        """
        result = await self.db.execute(
            select(QuizResponse.id)
            .where(QuizResponse.session_id == session_id)
            .where(QuizResponse.question_id == question_id)
            .limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def get_session_stats(self, session_id: UUID) -> dict[str, Any]:
        """
        Calculate session statistics from responses.

        Args:
            session_id: Quiz session UUID

        Returns:
            Dictionary with questions_answered, correct_count, accuracy
        """
        # Get count of responses and correct responses in one query
        result = await self.db.execute(
            select(
                func.count(QuizResponse.id).label("total"),
                func.sum(
                    func.cast(QuizResponse.is_correct, Integer)
                ).label("correct"),
            )
            .where(QuizResponse.session_id == session_id)
        )
        row = result.one()
        total = row.total or 0
        correct = row.correct or 0

        return {
            "questions_answered": total,
            "correct_count": correct,
            "accuracy": correct / total if total > 0 else 0.0,
        }

    async def get_recently_answered_question_ids(
        self,
        user_id: UUID,
        limit: int = 100,
    ) -> list[UUID]:
        """
        Get recently answered question IDs for a user.

        Used for recency filtering in question selection.

        Args:
            user_id: User UUID
            limit: Maximum number of recent questions to return

        Returns:
            List of question UUIDs ordered by most recent first
        """
        result = await self.db.execute(
            select(QuizResponse.question_id)
            .where(QuizResponse.user_id == user_id)
            .order_by(QuizResponse.created_at.desc())
            .limit(limit)
        )
        return [row[0] for row in result.all()]

    async def update_info_gain(
        self,
        response_id: UUID,
        info_gain_actual: float,
    ) -> QuizResponse | None:
        """
        Update the actual information gain for a response.

        Called by Story 4.4 (Bayesian Belief Update) after calculating
        the actual entropy reduction from this answer.

        Args:
            response_id: Response UUID
            info_gain_actual: Calculated information gain value

        Returns:
            Updated QuizResponse instance or None if not found
        """
        response = await self.get_by_id(response_id)
        if response:
            response.info_gain_actual = info_gain_actual
            await self.db.flush()
            await self.db.refresh(response)
        return response
