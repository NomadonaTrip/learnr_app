"""
BeliefUpdater service for Bayesian Knowledge Tracing (BKT) belief updates.
Updates belief states after observing user responses using Bayesian inference.
"""
import time
from typing import TYPE_CHECKING
from uuid import UUID

import structlog

if TYPE_CHECKING:
    from src.models.question import Question
    from src.repositories.belief_repository import BeliefRepository

logger = structlog.get_logger(__name__)


class BeliefUpdater:
    """
    Updates belief states after observing a user response using Bayesian inference.

    This is the core BKT engine for LearnR's adaptive learning system.
    Uses Beta distribution parameters (alpha, beta) to model mastery probability.

    The update formula follows Bayesian Knowledge Tracing:
    - For correct answers: posterior reflects increased mastery evidence
    - For incorrect answers: posterior reflects increased non-mastery evidence
    """

    # Default BKT parameters
    DEFAULT_SLIP = 0.10  # P(incorrect | mastered) - careless error
    DEFAULT_GUESS = 0.25  # P(correct | not mastered) - lucky guess

    def __init__(
        self,
        belief_repository: "BeliefRepository",
        default_slip: float = DEFAULT_SLIP,
        default_guess: float = DEFAULT_GUESS,
    ):
        """
        Initialize BeliefUpdater.

        Args:
            belief_repository: Repository for belief state database operations
            default_slip: Default P(incorrect | mastered), default 0.10
            default_guess: Default P(correct | not mastered), default 0.25
        """
        self.belief_repository = belief_repository
        self.default_slip = default_slip
        self.default_guess = default_guess

    async def update_beliefs(
        self,
        user_id: UUID,
        question: "Question",
        is_correct: bool,
    ) -> list[UUID]:
        """
        Update beliefs for all concepts tested by this question.

        Args:
            user_id: User UUID
            question: Question model with question_concepts relationship loaded
            is_correct: Whether the user's answer was correct

        Returns:
            List of concept IDs that were updated
        """
        start_time = time.perf_counter()

        # Get concept IDs from question
        concept_ids = [qc.concept_id for qc in question.question_concepts]

        if not concept_ids:
            logger.warning(
                "Question has no linked concepts",
                question_id=str(question.id),
            )
            return []

        # Fetch current beliefs with row-level locking
        beliefs = await self.belief_repository.get_beliefs_for_concepts(
            user_id, concept_ids
        )

        if not beliefs:
            logger.warning(
                "No belief states found for concepts",
                user_id=str(user_id),
                concept_count=len(concept_ids),
            )
            return []

        # Get slip/guess rates (per-question or defaults)
        slip = question.slip_rate if question.slip_rate is not None else self.default_slip
        guess = question.guess_rate if question.guess_rate is not None else self.default_guess

        # Compute and apply updates
        updated_concept_ids = []
        for concept_id in concept_ids:
            belief = beliefs.get(concept_id)
            if not belief:
                logger.warning(
                    "Belief state not found for concept",
                    user_id=str(user_id),
                    concept_id=str(concept_id),
                )
                continue

            # Compute new alpha/beta using Bayesian update
            new_alpha, new_beta = self._bayesian_update(
                belief.alpha,
                belief.beta,
                is_correct,
                slip,
                guess,
            )

            # Update belief state
            belief.alpha = new_alpha
            belief.beta = new_beta
            belief.response_count += 1
            updated_concept_ids.append(concept_id)

        # Persist all updates atomically
        if updated_concept_ids:
            await self.belief_repository.flush_updates(list(beliefs.values()))

        # Calculate duration
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Log results
        logger.info(
            "Updated beliefs for concepts after question",
            user_id=str(user_id),
            question_id=str(question.id),
            concepts_updated=len(updated_concept_ids),
            is_correct=is_correct,
            duration_ms=round(duration_ms, 2),
        )

        # Warn if slow
        if duration_ms > 100:
            logger.warning(
                "Slow belief update",
                duration_ms=round(duration_ms, 2),
                user_id=str(user_id),
                question_id=str(question.id),
            )

        return updated_concept_ids

    def _bayesian_update(
        self,
        alpha: float,
        beta: float,
        is_correct: bool,
        slip: float,
        guess: float,
    ) -> tuple[float, float]:
        """
        Core Bayesian update for Beta distribution parameters.

        Uses Bayesian Knowledge Tracing (BKT) formula to compute posterior
        probability of mastery given observed response.

        For correct answer:
            p_correct = (1 - slip) * p_mastered + guess * (1 - p_mastered)
            posterior = (1 - slip) * p_mastered / p_correct

        For incorrect answer:
            p_incorrect = slip * p_mastered + (1 - guess) * (1 - p_mastered)
            posterior = slip * p_mastered / p_incorrect

        Args:
            alpha: Current alpha parameter (mastery evidence)
            beta: Current beta parameter (non-mastery evidence)
            is_correct: Whether the answer was correct
            slip: P(incorrect | mastered)
            guess: P(correct | not mastered)

        Returns:
            Tuple of (new_alpha, new_beta)
        """
        # Calculate prior probability of mastery
        p_mastered = alpha / (alpha + beta)

        if is_correct:
            # P(correct) under the model
            p_correct = (1 - slip) * p_mastered + guess * (1 - p_mastered)
            # Posterior probability of mastery given correct answer
            posterior = (1 - slip) * p_mastered / p_correct
        else:
            # P(incorrect) under the model
            p_incorrect = slip * p_mastered + (1 - guess) * (1 - p_mastered)
            # Posterior probability of mastery given incorrect answer
            posterior = slip * p_mastered / p_incorrect

        # Update Beta distribution parameters
        new_alpha = alpha + posterior
        new_beta = beta + (1 - posterior)

        return new_alpha, new_beta
