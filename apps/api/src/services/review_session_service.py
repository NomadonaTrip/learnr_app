"""
ReviewSessionService for managing post-quiz review sessions.
Handles review session creation, answer submission with reinforcement logic,
and summary generation.

Story 4.9: Post-Session Review Mode
"""
from typing import Any
from uuid import UUID

import structlog

from src.models.question import Question
from src.models.review_session import ReviewSession
from src.repositories.belief_repository import BeliefRepository
from src.repositories.concept_repository import ConceptRepository
from src.repositories.review_session_repository import ReviewSessionRepository
from src.schemas.review import (
    ReviewAnswerResponse,
    ReviewAvailableResponse,
    ReviewQuestionResponse,
    ReviewSessionResponse,
    ReviewSkipResponse,
    ReviewSummaryResponse,
    StillIncorrectConcept,
)
from src.services.belief_updater import BeliefUpdater

logger = structlog.get_logger(__name__)

# Reinforcement multipliers for belief updates
REINFORCEMENT_MULTIPLIER = 1.5  # Stronger positive update for incorrect→correct
STILL_INCORRECT_MULTIPLIER = 0.5  # Weaker negative update for still-incorrect


class ReviewSessionService:
    """
    Service for managing post-quiz review sessions.

    Handles:
    - Checking if review is available for a completed session
    - Creating and managing review sessions
    - Processing review answers with reinforcement belief updates
    - Generating review summaries with study links
    """

    def __init__(
        self,
        review_repo: ReviewSessionRepository,
        belief_repo: BeliefRepository,
        concept_repo: ConceptRepository,
        belief_updater: BeliefUpdater,
    ):
        """
        Initialize review session service.

        Args:
            review_repo: Repository for review session operations
            belief_repo: Repository for belief state operations
            concept_repo: Repository for concept operations
            belief_updater: Service for updating Bayesian belief states
        """
        self.review_repo = review_repo
        self.belief_repo = belief_repo
        self.concept_repo = concept_repo
        self.belief_updater = belief_updater

    async def check_review_available(
        self,
        session_id: UUID,
    ) -> ReviewAvailableResponse:
        """
        Check if review is available for a completed quiz session.

        Returns the count of incorrect answers and question IDs.

        Args:
            session_id: Quiz session UUID

        Returns:
            ReviewAvailableResponse with availability status
        """
        incorrect_responses = await self.review_repo.get_incorrect_responses_for_session(
            session_id
        )

        question_ids = [str(r.question_id) for r in incorrect_responses]
        available = len(question_ids) > 0

        logger.info(
            "review_availability_checked",
            session_id=str(session_id),
            available=available,
            incorrect_count=len(question_ids),
        )

        return ReviewAvailableResponse(
            available=available,
            incorrect_count=len(question_ids),
            question_ids=question_ids,
        )

    async def start_review(
        self,
        user_id: UUID,
        original_session_id: UUID,
    ) -> ReviewSessionResponse:
        """
        Start a review session for incorrect answers from a quiz session.

        Creates a new ReviewSession and marks it as in_progress.

        Args:
            user_id: User UUID
            original_session_id: Original quiz session UUID

        Returns:
            ReviewSessionResponse with session details

        Raises:
            ValueError: If no incorrect answers to review
        """
        # Check for existing pending review
        existing_review = await self.review_repo.get_pending_for_session(
            original_session_id
        )
        if existing_review:
            # Resume existing review
            logger.info(
                "review_session_resumed",
                review_session_id=str(existing_review.id),
                user_id=str(user_id),
            )
            return self._build_session_response(existing_review)

        # Get incorrect responses
        incorrect_responses = await self.review_repo.get_incorrect_responses_for_session(
            original_session_id
        )

        if not incorrect_responses:
            raise ValueError("No incorrect answers to review")

        question_ids = [r.question_id for r in incorrect_responses]

        # Create review session
        review_session = await self.review_repo.create(
            user_id=user_id,
            original_session_id=original_session_id,
            question_ids=question_ids,
        )

        # Mark as started
        review_session = await self.review_repo.mark_started(review_session.id)

        logger.info(
            "review_session_started",
            user_id=str(user_id),
            original_session_id=str(original_session_id),
            questions_to_review=len(question_ids),
        )

        return self._build_session_response(review_session)

    async def get_next_review_question(
        self,
        review_session_id: UUID,
        user_id: UUID,
    ) -> ReviewQuestionResponse | None:
        """
        Get the next question to review.

        Args:
            review_session_id: ReviewSession UUID
            user_id: User UUID for ownership validation

        Returns:
            ReviewQuestionResponse or None if all reviewed
        """
        review_session = await self.review_repo.get_by_id(
            review_session_id, user_id
        )

        if not review_session:
            raise ValueError(f"Review session {review_session_id} not found")

        if review_session.status == "completed":
            return None

        if review_session.status == "skipped":
            return None

        # Get already reviewed question IDs
        reviewed_responses = await self.review_repo.get_review_responses(
            review_session_id
        )
        reviewed_question_ids = {r.question_id for r in reviewed_responses}

        # Find next unreviewed question
        question_ids = [UUID(qid) for qid in review_session.question_ids]
        next_question_id = None
        review_number = 0

        for i, qid in enumerate(question_ids):
            if qid not in reviewed_question_ids:
                next_question_id = qid
                review_number = i + 1
                break

        if next_question_id is None:
            # All questions reviewed, mark complete
            await self.review_repo.mark_completed(review_session_id)
            return None

        # Fetch question details
        question = await self.review_repo.get_question_with_options(next_question_id)

        if not question:
            logger.error(
                "review_question_not_found",
                question_id=str(next_question_id),
            )
            raise ValueError(f"Question {next_question_id} not found")

        return ReviewQuestionResponse(
            question_id=str(question.id),
            question_text=question.question_text,
            options=question.options,
            review_number=review_number,
            total_to_review=review_session.total_to_review,
        )

    async def submit_review_answer(
        self,
        review_session_id: UUID,
        user_id: UUID,
        question_id: UUID,
        selected_answer: str,
    ) -> ReviewAnswerResponse:
        """
        Submit an answer for a review question.

        Determines if the answer was reinforced (incorrect→correct) and
        applies appropriate belief update multipliers.

        Args:
            review_session_id: ReviewSession UUID
            user_id: User UUID
            question_id: Question UUID being answered
            selected_answer: Selected answer (A, B, C, or D)

        Returns:
            ReviewAnswerResponse with feedback

        Raises:
            ValueError: If invalid answer or session not found
        """
        # Validate selected_answer
        selected_answer = selected_answer.upper()
        if selected_answer not in ("A", "B", "C", "D"):
            raise ValueError(f"Invalid answer: {selected_answer}. Must be A, B, C, or D")

        # Get review session
        review_session = await self.review_repo.get_by_id(
            review_session_id, user_id
        )

        if not review_session:
            raise ValueError(f"Review session {review_session_id} not found")

        if review_session.status not in ("pending", "in_progress"):
            raise ValueError(f"Review session is {review_session.status}, cannot submit answer")

        # Check if already reviewed
        already_reviewed = await self.review_repo.check_question_already_reviewed(
            review_session_id, question_id
        )
        if already_reviewed:
            raise ValueError(f"Question {question_id} already reviewed in this session")

        # Fetch question
        question = await self.review_repo.get_question_with_options(question_id)
        if not question:
            raise ValueError(f"Question {question_id} not found")

        # Get original response to determine reinforcement
        original_response = await self.review_repo.get_original_response_for_question(
            review_session.original_session_id, question_id
        )
        if not original_response:
            raise ValueError(f"Original response for question {question_id} not found")

        # Determine correctness and reinforcement
        is_correct = selected_answer == question.correct_answer
        was_reinforced = is_correct  # Was wrong before, now correct = reinforced

        # Update beliefs with reinforcement modifier
        belief_updates = await self._update_beliefs_with_reinforcement(
            user_id=user_id,
            question=question,
            is_correct=is_correct,
            was_reinforced=was_reinforced,
        )

        # Create review response
        await self.review_repo.create_review_response(
            review_session_id=review_session_id,
            user_id=user_id,
            question_id=question_id,
            original_response_id=original_response.id,
            selected_answer=selected_answer,
            is_correct=is_correct,
            was_reinforced=was_reinforced,
            belief_updates=belief_updates,
        )

        # Update session progress
        reviewed_count = review_session.reviewed_count + 1
        reinforced_count = review_session.reinforced_count + (1 if was_reinforced else 0)
        still_incorrect = review_session.still_incorrect_count + (0 if is_correct else 1)

        await self.review_repo.update_progress(
            review_session_id,
            reviewed=reviewed_count,
            reinforced=reinforced_count,
            still_incorrect=still_incorrect,
        )

        # Check if review complete
        if reviewed_count >= review_session.total_to_review:
            await self.review_repo.mark_completed(review_session_id)

        # Build feedback message
        if was_reinforced:
            feedback_message = "Great improvement!"
        elif is_correct:
            feedback_message = "Correct!"
        else:
            feedback_message = "Still needs practice. Review the explanation below."

        # Build concepts updated response
        concepts_updated = []
        for update in belief_updates:
            concepts_updated.append({
                "concept_id": update["concept_id"],
                "name": update["concept_name"],
                "new_mastery": round(
                    update["new_alpha"] / (update["new_alpha"] + update["new_beta"]),
                    2,
                ),
            })

        # Get reading link for study
        reading_link = None
        if question.question_concepts:
            first_concept_id = question.question_concepts[0].concept_id
            reading_link = f"/reading-library?concept={first_concept_id}"

        logger.info(
            "review_answer_submitted",
            user_id=str(user_id),
            review_session_id=str(review_session_id),
            question_id=str(question_id),
            is_correct=is_correct,
            was_reinforced=was_reinforced,
        )

        return ReviewAnswerResponse(
            is_correct=is_correct,
            was_reinforced=was_reinforced,
            correct_answer=question.correct_answer,
            explanation=question.explanation or "",
            concepts_updated=concepts_updated,
            feedback_message=feedback_message,
            reading_link=reading_link,
        )

    async def skip_review(
        self,
        review_session_id: UUID,
        user_id: UUID,
    ) -> ReviewSkipResponse:
        """
        Skip the review session.

        Marks the session as skipped and logs analytics event.

        Args:
            review_session_id: ReviewSession UUID
            user_id: User UUID

        Returns:
            ReviewSkipResponse with confirmation
        """
        review_session = await self.review_repo.get_by_id(
            review_session_id, user_id
        )

        if not review_session:
            raise ValueError(f"Review session {review_session_id} not found")

        await self.review_repo.mark_skipped(review_session_id)

        logger.info(
            "review_session_skipped",
            user_id=str(user_id),
            original_session_id=str(review_session.original_session_id),
            questions_skipped=review_session.total_to_review,
        )

        return ReviewSkipResponse(
            message="Review skipped",
            session_id=str(review_session_id),
            questions_skipped=review_session.total_to_review,
        )

    async def get_review_summary(
        self,
        review_session_id: UUID,
        user_id: UUID,
    ) -> ReviewSummaryResponse:
        """
        Get the summary of a completed review session.

        Args:
            review_session_id: ReviewSession UUID
            user_id: User UUID

        Returns:
            ReviewSummaryResponse with stats and study links
        """
        review_session = await self.review_repo.get_by_id(
            review_session_id, user_id
        )

        if not review_session:
            raise ValueError(f"Review session {review_session_id} not found")

        # Get still-incorrect concepts for study links
        still_incorrect_concepts = await self._get_still_incorrect_concepts(
            review_session_id
        )

        reinforcement_rate = review_session.reinforcement_rate

        logger.info(
            "review_session_completed",
            user_id=str(user_id),
            review_session_id=str(review_session_id),
            total_reviewed=review_session.reviewed_count,
            reinforced_count=review_session.reinforced_count,
            reinforcement_rate=round(reinforcement_rate, 2),
        )

        return ReviewSummaryResponse(
            total_reviewed=review_session.reviewed_count,
            reinforced_count=review_session.reinforced_count,
            still_incorrect_count=review_session.still_incorrect_count,
            reinforcement_rate=round(reinforcement_rate, 2),
            still_incorrect_concepts=still_incorrect_concepts,
        )

    async def _update_beliefs_with_reinforcement(
        self,
        user_id: UUID,
        question: Question,
        is_correct: bool,
        was_reinforced: bool,
    ) -> list[dict[str, Any]]:
        """
        Update beliefs with reinforcement modifier.

        Applies stronger positive update for reinforced answers (incorrect→correct)
        and weaker negative update for still-incorrect answers.

        Args:
            user_id: User UUID
            question: Question model
            is_correct: Whether the answer was correct
            was_reinforced: Whether this was a reinforcement

        Returns:
            List of belief update dictionaries
        """
        # Get concept IDs from question
        concept_ids = [qc.concept_id for qc in question.question_concepts]

        if not concept_ids:
            return []

        # Fetch current beliefs
        beliefs = await self.belief_repo.get_beliefs_for_concepts(user_id, concept_ids)

        if not beliefs:
            return []

        # Get slip/guess rates
        slip = question.slip_rate if question.slip_rate else 0.10
        guess = question.guess_rate if question.guess_rate else 0.25

        belief_updates: list[dict[str, Any]] = []
        updated_beliefs = []

        for concept_id in concept_ids:
            belief = beliefs.get(concept_id)
            if not belief:
                continue

            old_alpha = belief.alpha
            old_beta = belief.beta

            # Calculate standard Bayesian update
            p_mastered = old_alpha / (old_alpha + old_beta)

            if is_correct:
                p_correct = (1 - slip) * p_mastered + guess * (1 - p_mastered)
                posterior = ((1 - slip) * p_mastered / p_correct) if p_correct > 0 else p_mastered
            else:
                p_incorrect = slip * p_mastered + (1 - guess) * (1 - p_mastered)
                posterior = (slip * p_mastered / p_incorrect) if p_incorrect > 0 else p_mastered

            # Standard update
            delta_alpha = posterior
            delta_beta = 1 - posterior

            # Apply reinforcement modifier
            if was_reinforced:
                # Stronger positive update for reinforcement
                delta_alpha *= REINFORCEMENT_MULTIPLIER
                logger.debug(
                    "reinforcement_multiplier_applied",
                    concept_id=str(concept_id),
                    multiplier=REINFORCEMENT_MULTIPLIER,
                )
            elif not is_correct:
                # Weaker negative update for still-incorrect
                delta_beta *= STILL_INCORRECT_MULTIPLIER
                logger.debug(
                    "still_incorrect_multiplier_applied",
                    concept_id=str(concept_id),
                    multiplier=STILL_INCORRECT_MULTIPLIER,
                )

            new_alpha = old_alpha + delta_alpha
            new_beta = old_beta + delta_beta

            # Update belief
            belief.alpha = new_alpha
            belief.beta = new_beta
            belief.response_count += 1
            updated_beliefs.append(belief)

            # Get concept name
            concept_name = "Unknown"
            try:
                if belief.concept and belief.concept.name:
                    concept_name = belief.concept.name
            except Exception:
                pass

            belief_updates.append({
                "concept_id": str(concept_id),
                "concept_name": concept_name,
                "old_alpha": old_alpha,
                "old_beta": old_beta,
                "new_alpha": new_alpha,
                "new_beta": new_beta,
            })

        # Persist updates
        if updated_beliefs:
            await self.belief_repo.flush_updates(updated_beliefs)

        return belief_updates

    async def _get_still_incorrect_concepts(
        self,
        review_session_id: UUID,
    ) -> list[StillIncorrectConcept]:
        """
        Get concepts that were still incorrect after review.

        Uses batch loading to avoid N+1 query pattern.

        Args:
            review_session_id: ReviewSession UUID

        Returns:
            List of StillIncorrectConcept with study links
        """
        responses = await self.review_repo.get_review_responses(review_session_id)

        # Collect question IDs from incorrect responses
        incorrect_question_ids = [
            response.question_id
            for response in responses
            if not response.is_correct
        ]

        if not incorrect_question_ids:
            return []

        # Batch load all questions with their concepts (single query)
        questions = await self.review_repo.get_questions_with_concepts_batch(
            incorrect_question_ids
        )

        # Build map for quick lookup
        question_map = {q.id: q for q in questions}

        # Extract unique concepts from incorrect questions
        still_incorrect_concepts: list[StillIncorrectConcept] = []
        seen_concept_ids: set[str] = set()

        for question_id in incorrect_question_ids:
            question = question_map.get(question_id)
            if question and question.question_concepts:
                for qc in question.question_concepts:
                    concept_id_str = str(qc.concept_id)
                    if concept_id_str not in seen_concept_ids:
                        seen_concept_ids.add(concept_id_str)
                        # Concept is eagerly loaded via selectinload
                        concept_name = qc.concept.name if qc.concept else "Unknown"

                        still_incorrect_concepts.append(
                            StillIncorrectConcept(
                                concept_id=concept_id_str,
                                name=concept_name,
                                reading_link=f"/reading-library?concept={concept_id_str}",
                            )
                        )

        return still_incorrect_concepts

    def _build_session_response(
        self,
        review_session: ReviewSession,
    ) -> ReviewSessionResponse:
        """
        Build ReviewSessionResponse from model.

        Args:
            review_session: ReviewSession model

        Returns:
            ReviewSessionResponse
        """
        return ReviewSessionResponse(
            id=str(review_session.id),
            original_session_id=str(review_session.original_session_id),
            status=review_session.status,
            total_to_review=review_session.total_to_review,
            reviewed_count=review_session.reviewed_count,
            reinforced_count=review_session.reinforced_count,
            still_incorrect_count=review_session.still_incorrect_count,
            started_at=review_session.started_at,
            created_at=review_session.created_at,
        )
