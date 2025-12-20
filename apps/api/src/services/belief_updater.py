"""
BeliefUpdater service for Bayesian Knowledge Tracing (BKT) belief updates.
Updates belief states after observing user responses using Bayesian inference.

Story 4.4: Bayesian Belief Update Engine (CRITICAL)
"""
import time
from typing import TYPE_CHECKING
from uuid import UUID

import structlog

from src.schemas.belief_state import BeliefUpdateResult, BeliefUpdaterResponse
from src.utils.bkt_math import calculate_info_gain, safe_divide

if TYPE_CHECKING:
    from src.models.belief_state import BeliefState
    from src.models.question import Question
    from src.repositories.belief_repository import BeliefRepository
    from src.repositories.concept_repository import ConceptRepository

logger = structlog.get_logger(__name__)


class BeliefUpdater:
    """
    Updates belief states after observing a user response using Bayesian inference.

    This is the core BKT engine for LearnR's adaptive learning system.
    Uses Beta distribution parameters (alpha, beta) to model mastery probability.

    The update formula follows Bayesian Knowledge Tracing:
    - For correct answers: posterior reflects increased mastery evidence
    - For incorrect answers: posterior reflects increased non-mastery evidence

    Features:
    - Direct concept updates for concepts tested by the question
    - Prerequisite propagation: correct answers slightly boost prerequisite beliefs
    - Information gain calculation for analytics
    - Atomic persistence of all updates
    """

    # Default BKT parameters
    DEFAULT_SLIP = 0.10  # P(incorrect | mastered) - careless error
    DEFAULT_GUESS = 0.25  # P(correct | not mastered) - lucky guess
    DEFAULT_PREREQUISITE_PROPAGATION = 0.3  # Weight for prerequisite updates

    def __init__(
        self,
        belief_repository: "BeliefRepository",
        concept_repository: "ConceptRepository | None" = None,
        default_slip: float = DEFAULT_SLIP,
        default_guess: float = DEFAULT_GUESS,
        prerequisite_propagation: float = DEFAULT_PREREQUISITE_PROPAGATION,
    ):
        """
        Initialize BeliefUpdater.

        Args:
            belief_repository: Repository for belief state database operations
            concept_repository: Repository for concept operations (needed for prerequisite lookup)
            default_slip: Default P(incorrect | mastered), default 0.10
            default_guess: Default P(correct | not mastered), default 0.25
            prerequisite_propagation: Weight for propagating updates to prerequisites, default 0.3
        """
        self.belief_repository = belief_repository
        self.concept_repository = concept_repository
        self.default_slip = default_slip
        self.default_guess = default_guess
        self.prerequisite_propagation = prerequisite_propagation

    async def update_beliefs(
        self,
        user_id: UUID,
        question: "Question",
        is_correct: bool,
    ) -> BeliefUpdaterResponse:
        """
        Update beliefs for all concepts affected by this response.

        Performs:
        1. Direct updates for concepts tested by the question
        2. Prerequisite propagation (if correct and concept_repository available)
        3. Information gain calculation
        4. Atomic persistence

        Args:
            user_id: User UUID
            question: Question model with question_concepts relationship loaded
            is_correct: Whether the user's answer was correct

        Returns:
            BeliefUpdaterResponse with updates list and info_gain_actual
        """
        start_time = time.perf_counter()

        # Get concept IDs from question
        concept_ids = [qc.concept_id for qc in question.question_concepts]

        if not concept_ids:
            logger.warning(
                "Question has no linked concepts",
                question_id=str(question.id),
            )
            return BeliefUpdaterResponse(
                processing_time_ms=(time.perf_counter() - start_time) * 1000
            )

        # Fetch current beliefs with row-level locking
        beliefs = await self.belief_repository.get_beliefs_for_concepts(
            user_id, concept_ids
        )

        # Lazy initialization: create missing beliefs for new concepts (Story 2.14)
        missing_concept_ids = set(concept_ids) - set(beliefs.keys())
        if missing_concept_ids:
            logger.info(
                "Creating missing belief states (lazy init)",
                user_id=str(user_id),
                missing_count=len(missing_concept_ids),
                concept_ids=[str(cid) for cid in missing_concept_ids],
            )
            new_beliefs = await self._create_missing_beliefs(
                user_id, missing_concept_ids
            )
            beliefs.update(new_beliefs)

        if not beliefs:
            logger.warning(
                "No belief states found for concepts (even after lazy init)",
                user_id=str(user_id),
                concept_count=len(concept_ids),
            )
            return BeliefUpdaterResponse(
                processing_time_ms=(time.perf_counter() - start_time) * 1000
            )

        # Get slip/guess rates (per-question or defaults)
        slip = question.slip_rate if question.slip_rate is not None else self.default_slip
        guess = question.guess_rate if question.guess_rate is not None else self.default_guess

        # Store beliefs before update for info gain calculation
        beliefs_before: dict[UUID, tuple[float, float]] = {
            cid: (belief.alpha, belief.beta) for cid, belief in beliefs.items()
        }

        # Track update results
        update_results: list[BeliefUpdateResult] = []
        updated_beliefs: list[BeliefState] = []
        direct_concept_ids: set[UUID] = set()

        # === Direct concept updates ===
        for concept_id in concept_ids:
            belief = beliefs.get(concept_id)
            if not belief:
                logger.warning(
                    "Belief state not found for concept",
                    user_id=str(user_id),
                    concept_id=str(concept_id),
                )
                continue

            old_alpha, old_beta = belief.alpha, belief.beta

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
            updated_beliefs.append(belief)
            direct_concept_ids.add(concept_id)

            # Get concept name for the result
            concept_name = self._get_concept_name(belief)

            update_results.append(
                BeliefUpdateResult(
                    concept_id=concept_id,
                    concept_name=concept_name,
                    old_alpha=old_alpha,
                    old_beta=old_beta,
                    new_alpha=new_alpha,
                    new_beta=new_beta,
                    is_direct=True,
                )
            )

            logger.debug(
                "Updated belief for concept",
                concept_id=str(concept_id),
                old_mean=round(old_alpha / (old_alpha + old_beta), 4),
                new_mean=round(new_alpha / (new_alpha + new_beta), 4),
                is_correct=is_correct,
            )

        # === Prerequisite propagation (only on correct answers) ===
        propagated_count = 0
        if is_correct and self.concept_repository is not None:
            propagated_count = await self._propagate_to_prerequisites(
                user_id=user_id,
                direct_concept_ids=direct_concept_ids,
                beliefs_before=beliefs_before,
                update_results=update_results,
                updated_beliefs=updated_beliefs,
            )

        # === Persist all updates atomically ===
        if updated_beliefs:
            await self.belief_repository.flush_updates(updated_beliefs)

        # === Calculate information gain ===
        beliefs_after: dict[UUID, tuple[float, float]] = {
            result.concept_id: (result.new_alpha, result.new_beta)
            for result in update_results
            if result.is_direct  # Only direct updates contribute to info gain
        }
        info_gain = calculate_info_gain(
            beliefs_before, beliefs_after, list(direct_concept_ids)
        )

        # Calculate duration
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Build response
        response = BeliefUpdaterResponse(
            updates=update_results,
            info_gain_actual=round(info_gain, 4),
            concepts_updated_count=len(update_results),
            direct_updates_count=len(direct_concept_ids),
            propagated_updates_count=propagated_count,
            processing_time_ms=round(duration_ms, 2),
        )

        # Log results per AC 7
        logger.info(
            f"Updated {len(direct_concept_ids)} concepts for user {user_id}, info gain: {round(info_gain, 4)}",
            user_id=str(user_id),
            question_id=str(question.id),
            concepts_updated=len(direct_concept_ids),
            propagated_updates=propagated_count,
            is_correct=is_correct,
            info_gain=round(info_gain, 4),
            duration_ms=round(duration_ms, 2),
        )

        # Warn if slow (AC 8: <50ms target)
        if duration_ms > 50:
            logger.warning(
                "Slow belief update (target <50ms)",
                duration_ms=round(duration_ms, 2),
                user_id=str(user_id),
                question_id=str(question.id),
            )

        return response

    async def _propagate_to_prerequisites(
        self,
        user_id: UUID,
        direct_concept_ids: set[UUID],
        beliefs_before: dict[UUID, tuple[float, float]],
        update_results: list[BeliefUpdateResult],
        updated_beliefs: list["BeliefState"],
    ) -> int:
        """
        Propagate belief updates to prerequisite concepts (weaker signal).

        If user gets a concept correct, they likely know the prerequisites too.
        Apply a weaker update (prerequisite_propagation weight) to prereqs.

        Args:
            user_id: User UUID
            direct_concept_ids: Concepts directly tested by question
            beliefs_before: Pre-update beliefs for info gain calc
            update_results: List to append propagated updates to
            updated_beliefs: List to append updated belief models to

        Returns:
            Number of prerequisite concepts updated
        """
        if self.concept_repository is None:
            return 0

        # Collect all prerequisite concept IDs
        all_prereq_ids: set[UUID] = set()
        for concept_id in direct_concept_ids:
            try:
                prereqs = await self.concept_repository.get_prerequisites(concept_id)
                for prereq in prereqs:
                    # Skip if already updated directly
                    if prereq.id not in direct_concept_ids:
                        all_prereq_ids.add(prereq.id)
            except Exception as e:
                logger.warning(
                    "Failed to get prerequisites for concept",
                    concept_id=str(concept_id),
                    error=str(e),
                )

        if not all_prereq_ids:
            return 0

        # Fetch beliefs for prerequisites
        prereq_beliefs = await self.belief_repository.get_beliefs_for_concepts(
            user_id, list(all_prereq_ids)
        )

        propagated_count = 0
        for prereq_id, belief in prereq_beliefs.items():
            old_alpha, old_beta = belief.alpha, belief.beta

            # Store for info gain if not already tracked
            if prereq_id not in beliefs_before:
                beliefs_before[prereq_id] = (old_alpha, old_beta)

            # Apply weaker update: only add propagation weight to alpha
            # This represents weak evidence of prerequisite mastery
            new_alpha = old_alpha + self.prerequisite_propagation
            new_beta = old_beta  # Don't update beta

            # Update belief (DO NOT increment response_count for propagated)
            belief.alpha = new_alpha
            updated_beliefs.append(belief)

            # Get concept name
            concept_name = self._get_concept_name(belief)

            update_results.append(
                BeliefUpdateResult(
                    concept_id=prereq_id,
                    concept_name=concept_name,
                    old_alpha=old_alpha,
                    old_beta=old_beta,
                    new_alpha=new_alpha,
                    new_beta=new_beta,
                    is_direct=False,
                )
            )

            propagated_count += 1

            logger.debug(
                "Propagated update to prerequisite",
                prereq_id=str(prereq_id),
                old_mean=round(old_alpha / (old_alpha + old_beta), 4),
                new_mean=round(new_alpha / (new_alpha + new_beta), 4),
                propagation_weight=self.prerequisite_propagation,
            )

        if propagated_count > 0:
            logger.info(
                "Prerequisite propagation applied",
                user_id=str(user_id),
                direct_concepts=len(direct_concept_ids),
                prerequisites_updated=propagated_count,
            )

        return propagated_count

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
            # Use safe_divide to prevent division by zero in edge cases
            posterior = safe_divide((1 - slip) * p_mastered, p_correct)
        else:
            # P(incorrect) under the model
            p_incorrect = slip * p_mastered + (1 - guess) * (1 - p_mastered)
            # Posterior probability of mastery given incorrect answer
            posterior = safe_divide(slip * p_mastered, p_incorrect)

        # Update Beta distribution parameters
        new_alpha = alpha + posterior
        new_beta = beta + (1 - posterior)

        return new_alpha, new_beta

    def _get_concept_name(self, belief: "BeliefState") -> str:
        """
        Get concept name from belief state's relationship.

        Args:
            belief: BeliefState model with concept relationship

        Returns:
            Concept name or "Unknown" if not loaded
        """
        try:
            if belief.concept and belief.concept.name:
                return belief.concept.name
        except Exception:
            pass
        return "Unknown"

    async def _create_missing_beliefs(
        self,
        user_id: UUID,
        concept_ids: set[UUID],
    ) -> dict[UUID, "BeliefState"]:
        """
        Create missing belief states for concepts using uninformative prior Beta(1,1).

        This implements lazy initialization for Story 2.14: when a user encounters
        a concept that was added after their registration, we create the belief
        state on-the-fly with an uninformative prior.

        Args:
            user_id: User UUID
            concept_ids: Set of concept UUIDs that need belief states

        Returns:
            Dictionary mapping concept_id to newly created BeliefState
        """
        if not concept_ids:
            return {}

        # Use bulk_create_from_concepts for efficiency and idempotency
        # This uses ON CONFLICT DO NOTHING so it's safe to call even if
        # beliefs were created concurrently
        concept_id_list = list(concept_ids)
        created_count = await self.belief_repository.bulk_create_from_concepts(
            user_id=user_id,
            concept_ids=concept_id_list,
            alpha=1.0,  # Uninformative prior Beta(1,1)
            beta=1.0,
        )

        logger.debug(
            "Created missing beliefs via lazy init",
            user_id=str(user_id),
            requested_count=len(concept_ids),
            created_count=created_count,
        )

        # Fetch the newly created beliefs (need to get them with FOR UPDATE lock)
        new_beliefs = await self.belief_repository.get_beliefs_for_concepts(
            user_id, concept_id_list
        )

        return new_beliefs
