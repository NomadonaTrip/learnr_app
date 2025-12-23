"""
QuestionSelector service for Bayesian question selection with IRT difficulty distribution.

Implements combined BKT-IRT question selection (Algorithm 9):
- BKT Layer: Selects target concept based on information gain
- IRT Layer: Selects question difficulty based on user ability level
"""
import math
import random
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Literal
from uuid import UUID

import structlog
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.belief_state import BeliefState
from src.models.question import Question
from src.models.quiz_response import QuizResponse

logger = structlog.get_logger(__name__)

# =============================================================================
# IRT Difficulty Distribution Configuration (Algorithm 8)
# =============================================================================

AbilityLevel = Literal['novice', 'intermediate', 'expert']

# Difficulty distribution by ability level
# Keys: ability level, Values: probability weights for each tier
DIFFICULTY_DISTRIBUTION = {
    'novice': {
        'easy': 0.70,      # 70% easy questions
        'medium': 0.25,    # 25% medium questions
        'hard': 0.05       # 5% hard questions (exposure, not mastery)
    },
    'intermediate': {
        'easy': 0.40,      # 40% easy (reinforcement)
        'medium': 0.40,    # 40% medium (core learning zone)
        'hard': 0.20       # 20% hard (stretch challenges)
    },
    'expert': {
        'easy': 0.10,      # 10% easy (quick wins, confidence)
        'medium': 0.40,    # 40% medium (maintain fluency)
        'hard': 0.50       # 50% hard (primary challenge)
    }
}

# Difficulty tier boundaries using IRT b-parameter scale (-3.0 to +3.0)
DIFFICULTY_TIERS = {
    'easy': (-3.0, -1.0),    # Questions with difficulty < -1.0
    'medium': (-1.0, 1.0),   # Questions with difficulty -1.0 to 1.0
    'hard': (1.0, 3.0)       # Questions with difficulty >= 1.0
}

# Ability classification thresholds (Algorithm 7)
ABILITY_THRESHOLDS = {
    # BKT mastery probability thresholds
    "mastery_novice_max": 0.4,       # Below this → likely novice
    "mastery_expert_min": 0.7,       # Above this → possibly expert

    # Minimum correct answers at difficulty level to demonstrate competence
    "medium_competence_min": 3,      # Need 3+ correct at medium to be intermediate
    "hard_competence_min": 3,        # Need 3+ correct at hard to be expert

    # Accuracy thresholds
    "medium_accuracy_min": 0.6,      # 60%+ accuracy at medium for intermediate
    "hard_accuracy_min": 0.5,        # 50%+ accuracy at hard for expert
}


@dataclass
class DifficultyPerformance:
    """User's performance breakdown by difficulty tier for a concept."""
    easy_correct: int = 0
    easy_total: int = 0
    medium_correct: int = 0
    medium_total: int = 0
    hard_correct: int = 0
    hard_total: int = 0

    @property
    def easy_accuracy(self) -> float:
        return self.easy_correct / self.easy_total if self.easy_total > 0 else 0.0

    @property
    def medium_accuracy(self) -> float:
        return self.medium_correct / self.medium_total if self.medium_total > 0 else 0.0

    @property
    def hard_accuracy(self) -> float:
        return self.hard_correct / self.hard_total if self.hard_total > 0 else 0.0

    @property
    def total_responses(self) -> int:
        return self.easy_total + self.medium_total + self.hard_total


@dataclass
class SelectionResult:
    """Result of question selection including metrics."""
    question: Question
    estimated_info_gain: float
    concepts_tested: list[UUID]
    selection_duration_ms: float


class QuestionSelector:
    """
    Bayesian question selection engine.

    Selects the next question that maximizes expected information gain,
    efficiently reducing uncertainty about the user's knowledge.
    """

    def __init__(
        self,
        db: AsyncSession,
        recency_window_days: int = 7,
        prerequisite_weight: float = 0.2,
        min_info_gain_threshold: float = 0.01,
    ):
        """
        Initialize the question selector.

        Args:
            db: Database session for queries
            recency_window_days: Days within which to exclude recently answered questions
            prerequisite_weight: Bonus weight for prerequisite concepts (0.0-1.0)
            min_info_gain_threshold: Minimum info gain before falling back to uncertainty
        """
        self.db = db
        self.recency_window_days = recency_window_days
        self.prerequisite_weight = prerequisite_weight
        self.min_info_gain_threshold = min_info_gain_threshold

    async def select_next_question(
        self,
        user_id: UUID,
        session_id: UUID,
        beliefs: dict[UUID, BeliefState],
        available_questions: list[Question],
        strategy: str = "max_info_gain",
        knowledge_area_filter: str | None = None,
    ) -> tuple[Question, float]:
        """
        Select the next question for a quiz session.

        Args:
            user_id: User UUID
            session_id: Quiz session UUID
            beliefs: Dictionary mapping concept_id to BeliefState
            available_questions: List of questions to consider
            strategy: Selection strategy (max_info_gain, max_uncertainty, prerequisite_first)
            knowledge_area_filter: Optional knowledge area ID to filter questions

        Returns:
            Tuple of (selected_question, estimated_info_gain)

        Raises:
            ValueError: If no eligible questions are available
        """
        start_time = time.perf_counter()

        # Apply filters
        candidates = await self._filter_questions(
            user_id=user_id,
            session_id=session_id,
            questions=available_questions,
            knowledge_area_filter=knowledge_area_filter,
        )

        if not candidates:
            # Try expanding if focused session exhausted questions
            if knowledge_area_filter:
                logger.warning(
                    "question_selection_exhausted",
                    session_id=str(session_id),
                    knowledge_area_filter=knowledge_area_filter,
                    reason="no_candidates_after_filtering",
                )
                raise ValueError(
                    f"No questions available for knowledge area: {knowledge_area_filter}"
                )
            raise ValueError("No eligible questions available for selection")

        # Select based on strategy
        if strategy == "max_info_gain":
            question, info_gain = self._select_by_info_gain(candidates, beliefs)

            # Fallback if info gain is too low for all questions
            if info_gain < self.min_info_gain_threshold:
                logger.warning(
                    "question_selection_fallback",
                    session_id=str(session_id),
                    reason="all_candidates_below_threshold",
                    threshold=self.min_info_gain_threshold,
                    fallback_strategy="max_uncertainty",
                )
                question, info_gain = self._select_by_uncertainty(candidates, beliefs)
        elif strategy == "max_uncertainty":
            question, info_gain = self._select_by_uncertainty(candidates, beliefs)
        elif strategy == "prerequisite_first":
            question, info_gain = self._select_by_info_gain(
                candidates, beliefs, apply_prerequisite_bonus=True
            )
        elif strategy == "balanced":
            # For balanced, just use info gain without any special weighting
            question, info_gain = self._select_by_info_gain(candidates, beliefs)
        else:
            # Default to info gain
            question, info_gain = self._select_by_info_gain(candidates, beliefs)

        duration_ms = (time.perf_counter() - start_time) * 1000

        # Get concept IDs for the selected question
        concept_ids = [qc.concept_id for qc in question.question_concepts]

        logger.info(
            "question_selected",
            session_id=str(session_id),
            question_id=str(question.id),
            strategy=strategy,
            info_gain=round(info_gain, 4),
            concepts_tested=[str(c) for c in concept_ids],
            candidates_count=len(candidates),
            selection_duration_ms=round(duration_ms, 2),
        )

        return question, info_gain

    async def _filter_questions(
        self,
        user_id: UUID,
        session_id: UUID,
        questions: list[Question],
        knowledge_area_filter: str | None = None,
    ) -> list[Question]:
        """
        Apply all filtering constraints to questions.

        Filters:
        - Knowledge area filter (if provided)
        - Recency filter (exclude questions answered in last N days)
        - Session filter (exclude questions already in current session)

        Args:
            user_id: User UUID
            session_id: Session UUID
            questions: Questions to filter
            knowledge_area_filter: Optional knowledge area ID

        Returns:
            Filtered list of questions
        """
        # Apply knowledge area filter first (most restrictive, cheapest)
        if knowledge_area_filter:
            questions = self._filter_by_knowledge_area(questions, knowledge_area_filter)

        if not questions:
            return []

        # Get recent question IDs (from database)
        recent_ids = await self._get_recent_question_ids(user_id, self.recency_window_days)

        # Get session question IDs (from database)
        session_ids = await self._get_session_question_ids(session_id)

        # Combine exclusions
        excluded_ids = recent_ids | session_ids

        # Filter out excluded questions
        return [q for q in questions if q.id not in excluded_ids]

    def _filter_by_knowledge_area(
        self,
        questions: list[Question],
        knowledge_area_filter: str,
    ) -> list[Question]:
        """
        Filter questions by knowledge area.

        Args:
            questions: Questions to filter
            knowledge_area_filter: Knowledge area ID to match

        Returns:
            Questions matching the knowledge area
        """
        return [q for q in questions if q.knowledge_area_id == knowledge_area_filter]

    async def _get_recent_question_ids(
        self,
        user_id: UUID,
        days: int,
    ) -> set[UUID]:
        """
        Get question IDs answered by user within the recency window.

        Args:
            user_id: User UUID
            days: Number of days to look back

        Returns:
            Set of question UUIDs answered recently
        """
        cutoff = datetime.now(UTC) - timedelta(days=days)

        result = await self.db.execute(
            select(QuizResponse.question_id)
            .where(QuizResponse.user_id == user_id)
            .where(QuizResponse.created_at > cutoff)
            .distinct()
        )

        return {row[0] for row in result.all()}

    async def _get_session_question_ids(
        self,
        session_id: UUID,
    ) -> set[UUID]:
        """
        Get question IDs already answered in this session.

        Args:
            session_id: Quiz session UUID

        Returns:
            Set of question UUIDs in the session
        """
        result = await self.db.execute(
            select(QuizResponse.question_id)
            .where(QuizResponse.session_id == session_id)
            .distinct()
        )

        return {row[0] for row in result.all()}

    def _select_by_info_gain(
        self,
        candidates: list[Question],
        beliefs: dict[UUID, BeliefState],
        apply_prerequisite_bonus: bool = False,
    ) -> tuple[Question, float]:
        """
        Select the question with maximum expected information gain.

        Args:
            candidates: Eligible questions
            beliefs: User's belief states by concept
            apply_prerequisite_bonus: Whether to add bonus for foundational concepts

        Returns:
            Tuple of (best_question, info_gain)
        """
        best_question = None
        best_gain = -1.0

        for question in candidates:
            gain = self._calculate_expected_info_gain(question, beliefs)

            # Apply prerequisite bonus if configured
            if apply_prerequisite_bonus:
                gain = self._apply_prerequisite_bonus(question, beliefs, gain)

            if gain > best_gain:
                best_gain = gain
                best_question = question

        if best_question is None:
            # This shouldn't happen if candidates is non-empty
            raise ValueError("No question could be selected")

        return best_question, best_gain

    def _select_by_uncertainty(
        self,
        candidates: list[Question],
        beliefs: dict[UUID, BeliefState],
    ) -> tuple[Question, float]:
        """
        Select the question testing the most uncertain concepts (fallback strategy).

        Higher (less negative) entropy = more uncertainty = better for learning.
        We select the question with the highest average entropy across its concepts.

        Args:
            candidates: Eligible questions
            beliefs: User's belief states by concept

        Returns:
            Tuple of (best_question, avg_entropy)
        """
        best_question = None
        best_entropy = float('-inf')  # Start with negative infinity

        for question in candidates:
            # Calculate total entropy for concepts tested by this question
            total_entropy = 0.0
            concept_count = 0

            for qc in question.question_concepts:
                if qc.concept_id in beliefs:
                    belief = beliefs[qc.concept_id]
                    total_entropy += self._belief_entropy(belief.alpha, belief.beta)
                    concept_count += 1

            # Normalize by concept count to avoid bias toward multi-concept questions
            if concept_count > 0:
                avg_entropy = total_entropy / concept_count
            else:
                # No beliefs found for this question's concepts - use neutral value
                avg_entropy = 0.0

            if avg_entropy > best_entropy:
                best_entropy = avg_entropy
                best_question = question

        if best_question is None:
            raise ValueError("No question could be selected")

        # Return the selected question and its average entropy
        return best_question, best_entropy

    def _calculate_expected_info_gain(
        self,
        question: Question,
        beliefs: dict[UUID, BeliefState],
    ) -> float:
        """
        Calculate expected information gain from asking this question.

        Information gain = current entropy - expected posterior entropy

        Args:
            question: Question to evaluate
            beliefs: User's belief states

        Returns:
            Expected reduction in entropy (information gain)
        """
        # Get beliefs for concepts this question tests
        concept_beliefs = []
        for qc in question.question_concepts:
            if qc.concept_id in beliefs:
                concept_beliefs.append(beliefs[qc.concept_id])

        if not concept_beliefs:
            return 0.0

        # Current entropy (uncertainty)
        current_entropy = sum(
            self._belief_entropy(b.alpha, b.beta) for b in concept_beliefs
        )

        # Predict probability of correct response
        p_correct = self._predict_correct_probability(question, concept_beliefs)

        # Simulate updates for each outcome
        beliefs_if_correct = self._simulate_update(
            concept_beliefs,
            is_correct=True,
            slip=question.slip_rate,
            guess=question.guess_rate,
        )
        beliefs_if_incorrect = self._simulate_update(
            concept_beliefs,
            is_correct=False,
            slip=question.slip_rate,
            guess=question.guess_rate,
        )

        # Expected posterior entropy
        entropy_if_correct = sum(
            self._belief_entropy(a, b) for a, b in beliefs_if_correct
        )
        entropy_if_incorrect = sum(
            self._belief_entropy(a, b) for a, b in beliefs_if_incorrect
        )

        expected_posterior_entropy = (
            p_correct * entropy_if_correct
            + (1 - p_correct) * entropy_if_incorrect
        )

        return current_entropy - expected_posterior_entropy

    def _belief_entropy(self, alpha: float, beta: float) -> float:
        """
        Calculate entropy of Beta(alpha, beta) distribution.

        Higher entropy = more uncertainty about the true probability.
        Lower entropy = more confident in our estimate.

        Range: 0 (certain) to ~0.693 (maximum uncertainty at alpha=beta=1)

        Args:
            alpha: Beta distribution alpha parameter
            beta: Beta distribution beta parameter

        Returns:
            Differential entropy of the Beta distribution
        """
        # Log beta function: ln B(α, β) = ln Γ(α) + ln Γ(β) - ln Γ(α+β)
        log_beta = math.lgamma(alpha) + math.lgamma(beta) - math.lgamma(alpha + beta)

        # Digamma approximation for ψ(x) using the recurrence relation
        # ψ(x) ≈ ln(x) - 1/(2x) for x > 6, otherwise use recurrence
        psi_alpha = self._digamma(alpha)
        psi_beta = self._digamma(beta)
        psi_sum = self._digamma(alpha + beta)

        return (
            log_beta
            - (alpha - 1) * psi_alpha
            - (beta - 1) * psi_beta
            + (alpha + beta - 2) * psi_sum
        )

    def _digamma(self, x: float) -> float:
        """
        Compute the digamma function ψ(x) = d/dx ln Γ(x).

        Uses recurrence relation for small x, asymptotic expansion for large x.

        Args:
            x: Input value (must be positive)

        Returns:
            Value of digamma function at x
        """
        # For small x, use recurrence: ψ(x+1) = ψ(x) + 1/x
        result = 0.0
        while x < 6:
            result -= 1 / x
            x += 1

        # Asymptotic expansion for x >= 6:
        # ψ(x) ≈ ln(x) - 1/(2x) - 1/(12x²) + 1/(120x⁴) - 1/(252x⁶)
        x2 = x * x
        result += (
            math.log(x)
            - 1 / (2 * x)
            - 1 / (12 * x2)
            + 1 / (120 * x2 * x2)
            - 1 / (252 * x2 * x2 * x2)
        )
        return result

    def _predict_correct_probability(
        self,
        question: Question,
        concept_beliefs: list[BeliefState],
    ) -> float:
        """
        Predict probability of correct response given current beliefs.

        Uses slip/guess model: p_correct = (1 - slip) * mastery + guess * (1 - mastery)

        Args:
            question: Question with slip/guess parameters
            concept_beliefs: Beliefs for concepts tested

        Returns:
            Probability of correct answer (0.0-1.0)
        """
        if not concept_beliefs:
            return 0.5  # No information, assume 50%

        # Average mastery across concepts
        avg_mastery = sum(b.mean for b in concept_beliefs) / len(concept_beliefs)

        # Apply slip/guess model
        p_correct = (
            (1 - question.slip_rate) * avg_mastery
            + question.guess_rate * (1 - avg_mastery)
        )

        return p_correct

    def _simulate_update(
        self,
        concept_beliefs: list[BeliefState],
        is_correct: bool,
        slip: float,
        guess: float,
    ) -> list[tuple[float, float]]:
        """
        Simulate Bayesian update for each outcome without persisting.

        Args:
            concept_beliefs: Current beliefs to update
            is_correct: Whether the simulated response is correct
            slip: Question slip rate
            guess: Question guess rate

        Returns:
            List of (new_alpha, new_beta) tuples for each concept
        """
        updated = []

        for belief in concept_beliefs:
            new_alpha, new_beta = self._bayesian_update(
                alpha=belief.alpha,
                beta=belief.beta,
                is_correct=is_correct,
                slip=slip,
                guess=guess,
            )
            updated.append((new_alpha, new_beta))

        return updated

    def _bayesian_update(
        self,
        alpha: float,
        beta: float,
        is_correct: bool,
        slip: float,
        guess: float,
    ) -> tuple[float, float]:
        """
        Core Bayesian update for Beta parameters.

        Args:
            alpha: Current alpha parameter
            beta: Current beta parameter
            is_correct: Whether response was correct
            slip: Probability of incorrect given mastered
            guess: Probability of correct given not mastered

        Returns:
            Tuple of (new_alpha, new_beta)
        """
        p_mastered = alpha / (alpha + beta)

        if is_correct:
            p_correct = (1 - slip) * p_mastered + guess * (1 - p_mastered)
            # Avoid division by zero
            if p_correct > 0:
                posterior_mastered = (1 - slip) * p_mastered / p_correct
            else:
                posterior_mastered = p_mastered
        else:
            p_incorrect = slip * p_mastered + (1 - guess) * (1 - p_mastered)
            # Avoid division by zero
            if p_incorrect > 0:
                posterior_mastered = slip * p_mastered / p_incorrect
            else:
                posterior_mastered = p_mastered

        new_alpha = alpha + posterior_mastered
        new_beta = beta + (1 - posterior_mastered)

        return new_alpha, new_beta

    def _apply_prerequisite_bonus(
        self,
        question: Question,
        beliefs: dict[UUID, BeliefState],
        base_gain: float,
    ) -> float:
        """
        Apply bonus for questions testing foundational/prerequisite concepts.

        Questions testing concepts that are prerequisites for uncertain concepts
        get a boost, encouraging the system to solidify foundations first.

        Args:
            question: Question to evaluate
            beliefs: User's belief states
            base_gain: Base information gain

        Returns:
            Adjusted information gain with prerequisite bonus
        """
        # For now, apply a simple bonus based on uncertainty level
        # Future: Could use concept prerequisite graph
        uncertain_count = 0
        for qc in question.question_concepts:
            if qc.concept_id in beliefs:
                belief = beliefs[qc.concept_id]
                if belief.status == "uncertain":
                    uncertain_count += 1

        if uncertain_count > 0:
            bonus = self.prerequisite_weight * (uncertain_count / len(question.question_concepts))
            return base_gain * (1 + bonus)

        return base_gain

    # =========================================================================
    # IRT Difficulty Distribution Methods (Algorithm 7 & 8)
    # =========================================================================

    async def get_difficulty_performance(
        self,
        user_id: UUID,
        concept_id: UUID,
    ) -> DifficultyPerformance:
        """
        Get user's performance breakdown by difficulty tier for a concept.

        Queries quiz_responses joined with questions to aggregate performance
        by IRT difficulty tier.

        Args:
            user_id: User UUID
            concept_id: Concept UUID

        Returns:
            DifficultyPerformance with counts by tier
        """
        from src.models.question_concept import QuestionConcept

        # Query responses for questions mapped to this concept
        result = await self.db.execute(
            select(
                Question.difficulty,
                QuizResponse.is_correct
            )
            .join(QuestionConcept, Question.id == QuestionConcept.question_id)
            .join(QuizResponse, Question.id == QuizResponse.question_id)
            .where(
                and_(
                    QuizResponse.user_id == user_id,
                    QuestionConcept.concept_id == concept_id
                )
            )
        )

        performance = DifficultyPerformance()

        for row in result.all():
            difficulty, is_correct = row

            # Classify by IRT tier boundaries
            if difficulty < DIFFICULTY_TIERS['easy'][1]:  # < -1.0
                performance.easy_total += 1
                if is_correct:
                    performance.easy_correct += 1
            elif difficulty < DIFFICULTY_TIERS['medium'][1]:  # < 1.0
                performance.medium_total += 1
                if is_correct:
                    performance.medium_correct += 1
            else:  # >= 1.0
                performance.hard_total += 1
                if is_correct:
                    performance.hard_correct += 1

        return performance

    def classify_user_ability(
        self,
        mastery_probability: float,
        performance: DifficultyPerformance
    ) -> AbilityLevel:
        """
        Classify user's ability level for a concept (Algorithm 7).

        Classification Rules (in order of precedence):

        EXPERT if:
          - Mastery probability >= 0.7 AND
          - At least 3 correct answers at Hard difficulty AND
          - Hard accuracy >= 50%

        INTERMEDIATE if:
          - Mastery probability >= 0.4 AND
          - At least 3 correct answers at Medium difficulty AND
          - Medium accuracy >= 60%

        NOVICE otherwise (default for new users or struggling learners)

        Args:
            mastery_probability: BKT mastery probability (0.0-1.0)
            performance: User's performance breakdown by tier

        Returns:
            AbilityLevel: 'novice', 'intermediate', or 'expert'
        """
        thresholds = ABILITY_THRESHOLDS

        # Check for Expert level
        if (mastery_probability >= thresholds["mastery_expert_min"] and
            performance.hard_correct >= thresholds["hard_competence_min"] and
            performance.hard_accuracy >= thresholds["hard_accuracy_min"]):
            return 'expert'

        # Check for Intermediate level
        if (mastery_probability >= thresholds["mastery_novice_max"] and
            performance.medium_correct >= thresholds["medium_competence_min"] and
            performance.medium_accuracy >= thresholds["medium_accuracy_min"]):
            return 'intermediate'

        # Default to Novice
        return 'novice'

    def select_difficulty_tier(self, ability_level: AbilityLevel) -> str:
        """
        Probabilistically select a difficulty tier based on ability level.

        Uses weighted random selection based on DIFFICULTY_DISTRIBUTION.

        Args:
            ability_level: User's classified ability level

        Returns:
            Difficulty tier: 'easy', 'medium', or 'hard'
        """
        distribution = DIFFICULTY_DISTRIBUTION[ability_level]

        # Weighted random choice
        rand = random.random()
        cumulative = 0.0

        for tier, probability in distribution.items():
            cumulative += probability
            if rand < cumulative:
                return tier

        return 'medium'  # Fallback (should never reach)

    def get_questions_in_tier(
        self,
        questions: list[Question],
        tier: str
    ) -> list[Question]:
        """
        Filter questions to those within a difficulty tier.

        Args:
            questions: Questions to filter
            tier: Difficulty tier ('easy', 'medium', 'hard')

        Returns:
            Questions within the specified tier
        """
        min_diff, max_diff = DIFFICULTY_TIERS[tier]

        return [
            q for q in questions
            if min_diff <= q.difficulty < max_diff
        ]

    def _fallback_tier_selection(
        self,
        questions: list[Question],
        original_tier: str,
        ability_level: AbilityLevel
    ) -> list[Question]:
        """
        Fallback tier selection when original tier has no questions.

        Strategy based on ability level:
        - Novice: Prefer medium over hard
        - Intermediate: Prefer adjacent tier with more questions
        - Expert: Prefer medium over easy

        Args:
            questions: All available questions
            original_tier: Originally selected tier
            ability_level: User's ability level

        Returns:
            Questions from fallback tier, or empty list
        """
        tier_order = {
            'novice': ['medium', 'hard'],       # If no easy, try medium, then hard
            'intermediate': ['easy', 'hard'],   # If no medium, try easy, then hard
            'expert': ['medium', 'easy']        # If no hard, try medium, then easy
        }

        for fallback_tier in tier_order[ability_level]:
            fallback_questions = self.get_questions_in_tier(questions, fallback_tier)
            if fallback_questions:
                logger.debug(
                    "irt_tier_fallback",
                    original_tier=original_tier,
                    fallback_tier=fallback_tier,
                    questions_found=len(fallback_questions)
                )
                return fallback_questions

        return []

    async def select_question_by_irt(
        self,
        user_id: UUID,
        concept_id: UUID,
        available_questions: list[Question],
        belief: BeliefState | None = None,
    ) -> tuple[Question, AbilityLevel, str]:
        """
        Select a question using IRT-based difficulty distribution (Algorithm 8).

        Steps:
        1. Get user's response history for concept
        2. Classify ability level (novice/intermediate/expert)
        3. Sample difficulty tier from distribution
        4. Filter questions to tier
        5. Random selection from filtered pool
        6. Fallback to adjacent tier if empty

        Args:
            user_id: User UUID
            concept_id: Target concept UUID
            available_questions: Pre-filtered questions for the concept
            belief: Optional pre-loaded belief state

        Returns:
            Tuple of (selected_question, ability_level, selected_tier)

        Raises:
            ValueError: If no questions available
        """
        if not available_questions:
            raise ValueError(f"No questions available for concept {concept_id}")

        # Step 1: Get performance history
        performance = await self.get_difficulty_performance(user_id, concept_id)

        # Step 2: Classify ability level
        if performance.total_responses == 0:
            # No history - default to novice
            ability_level: AbilityLevel = 'novice'
        else:
            mastery_prob = belief.mean if belief else 0.5
            ability_level = self.classify_user_ability(mastery_prob, performance)

        # Step 3: Sample difficulty tier
        target_tier = self.select_difficulty_tier(ability_level)

        # Step 4: Filter questions to tier
        tier_questions = self.get_questions_in_tier(available_questions, target_tier)

        # Step 5: Fallback if tier is empty
        was_fallback = False
        if not tier_questions:
            tier_questions = self._fallback_tier_selection(
                available_questions, target_tier, ability_level
            )
            was_fallback = True

        # Step 6: Random selection from tier
        if tier_questions:
            selected = random.choice(tier_questions)
        else:
            # Ultimate fallback: any question
            selected = random.choice(available_questions)
            was_fallback = True

        logger.info(
            "irt_question_selected",
            user_id=str(user_id),
            concept_id=str(concept_id),
            ability_level=ability_level,
            target_tier=target_tier,
            question_id=str(selected.id),
            question_difficulty=selected.difficulty,
            was_fallback=was_fallback,
            distribution=DIFFICULTY_DISTRIBUTION[ability_level],
            performance={
                "easy": f"{performance.easy_correct}/{performance.easy_total}",
                "medium": f"{performance.medium_correct}/{performance.medium_total}",
                "hard": f"{performance.hard_correct}/{performance.hard_total}",
            }
        )

        return selected, ability_level, target_tier

    # =========================================================================
    # Combined BKT-IRT Selection (Algorithm 9)
    # =========================================================================

    async def select_next_question_adaptive(
        self,
        user_id: UUID,
        session_id: UUID,
        beliefs: dict[UUID, BeliefState],
        available_questions: list[Question],
        knowledge_area_filter: str | None = None,
        use_irt: bool = True,
    ) -> tuple[Question, float, AbilityLevel | None, str | None]:
        """
        Combined BKT-IRT adaptive question selection (Algorithm 9).

        This method orchestrates the complete adaptive selection process:

        BKT Layer (What to teach):
        1. Calculate information gain for each concept
        2. Apply prerequisite weighting
        3. Select concept with highest info gain

        IRT Layer (How hard to teach):
        4. Classify user ability for selected concept
        5. Sample difficulty tier from distribution
        6. Select question at appropriate difficulty

        Args:
            user_id: User UUID
            session_id: Quiz session UUID
            beliefs: Dictionary mapping concept_id to BeliefState
            available_questions: List of all available questions
            knowledge_area_filter: Optional knowledge area filter
            use_irt: Whether to apply IRT difficulty distribution

        Returns:
            Tuple of (question, info_gain, ability_level, difficulty_tier)

        Raises:
            ValueError: If no eligible questions available
        """
        start_time = time.perf_counter()

        # Apply filters (existing logic)
        candidates = await self._filter_questions(
            user_id=user_id,
            session_id=session_id,
            questions=available_questions,
            knowledge_area_filter=knowledge_area_filter,
        )

        if not candidates:
            if knowledge_area_filter:
                raise ValueError(
                    f"No questions available for knowledge area: {knowledge_area_filter}"
                )
            raise ValueError("No eligible questions available for selection")

        # BKT Layer: Select by information gain to find best concept
        question, info_gain = self._select_by_info_gain(candidates, beliefs)

        # Get the primary concept for this question
        primary_concept_id = None
        if question.question_concepts:
            primary_concept_id = question.question_concepts[0].concept_id

        ability_level = None
        difficulty_tier = None

        if use_irt and primary_concept_id:
            # Get questions for this concept
            concept_questions = [
                q for q in candidates
                if any(qc.concept_id == primary_concept_id for qc in q.question_concepts)
            ]

            if concept_questions:
                # IRT Layer: Select question at appropriate difficulty
                belief = beliefs.get(primary_concept_id)
                question, ability_level, difficulty_tier = await self.select_question_by_irt(
                    user_id=user_id,
                    concept_id=primary_concept_id,
                    available_questions=concept_questions,
                    belief=belief,
                )

        duration_ms = (time.perf_counter() - start_time) * 1000
        concept_ids = [qc.concept_id for qc in question.question_concepts]

        logger.info(
            "adaptive_question_selected",
            session_id=str(session_id),
            question_id=str(question.id),
            info_gain=round(info_gain, 4),
            ability_level=ability_level,
            difficulty_tier=difficulty_tier,
            question_difficulty=question.difficulty,
            concepts_tested=[str(c) for c in concept_ids],
            candidates_count=len(candidates),
            use_irt=use_irt,
            selection_duration_ms=round(duration_ms, 2),
        )

        return question, info_gain, ability_level, difficulty_tier
