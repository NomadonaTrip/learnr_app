"""
Diagnostic service for optimal question selection.
Implements greedy coverage optimization algorithm for diagnostic assessment.
"""
import random
import time
from collections import defaultdict
from dataclasses import dataclass
from uuid import UUID

import structlog

from src.models.question import Question
from src.repositories.concept_repository import ConceptRepository
from src.repositories.question_repository import QuestionRepository

logger = structlog.get_logger(__name__)


@dataclass
class QuestionWithConcepts:
    """Question with its concept IDs for scoring."""
    question: Question
    concept_ids: set[UUID]


class DiagnosticService:
    """
    Service for selecting optimal diagnostic questions.

    Implements a greedy coverage optimization algorithm that:
    - Maximizes concept coverage with minimal questions
    - Balances across knowledge areas (max 4 per KA)
    - Prefers high discrimination (more informative) questions
    """

    # Configuration constants
    DEFAULT_TARGET_COUNT = 15
    MIN_QUESTIONS = 12
    MAX_QUESTIONS = 20
    MAX_QUESTIONS_PER_KA = 4

    # Scoring weights
    WEIGHT_COVERAGE = 10
    WEIGHT_DISCRIMINATION = 5
    WEIGHT_KA_BALANCE = 2

    def __init__(
        self,
        question_repo: QuestionRepository,
        concept_repo: ConceptRepository,
    ):
        """
        Initialize diagnostic service.

        Args:
            question_repo: Repository for question operations
            concept_repo: Repository for concept operations
        """
        self.question_repo = question_repo
        self.concept_repo = concept_repo

    async def select_diagnostic_questions(
        self,
        course_id: UUID,
        target_count: int = DEFAULT_TARGET_COUNT,
    ) -> tuple[list[Question], set[UUID], int]:
        """
        Select optimal diagnostic questions for a course.

        Uses greedy coverage optimization to select questions that:
        1. Maximize concept coverage across the corpus
        2. Balance across knowledge areas
        3. Prefer high discrimination questions

        Args:
            course_id: Course UUID to select questions for
            target_count: Target number of questions (12-20, default 15)

        Returns:
            Tuple of:
            - List of selected Question objects (randomized order)
            - Set of covered concept UUIDs
            - Total concept count in course

        Raises:
            ValueError: If target_count is out of valid range
        """
        start_time = time.perf_counter()

        # Validate target_count
        target_count = max(self.MIN_QUESTIONS, min(self.MAX_QUESTIONS, target_count))

        # Fetch all active questions with concepts
        questions = await self.question_repo.get_questions_with_concepts(course_id)

        # Fetch total concept count for coverage calculation
        total_concepts = await self.concept_repo.get_concept_count(course_id)

        if not questions:
            logger.warning(
                "No questions available for diagnostic",
                course_id=str(course_id),
            )
            return [], set(), total_concepts

        # Prepare questions with concept sets for efficient scoring
        questions_with_concepts = self._prepare_questions_with_concepts(questions)

        # Run selection algorithm
        selected, covered_concepts, ka_counts = self._select_questions_greedy(
            questions_with_concepts,
            target_count,
        )

        # Randomize question order for presentation
        random.shuffle(selected)

        # Calculate duration
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Log selection results
        coverage_percentage = (
            len(covered_concepts) / total_concepts if total_concepts > 0 else 0.0
        )

        logger.info(
            "Selected diagnostic questions",
            course_id=str(course_id),
            question_count=len(selected),
            concepts_covered=len(covered_concepts),
            total_concepts=total_concepts,
            coverage_percentage=round(coverage_percentage, 3),
            ka_distribution=dict(ka_counts),
            duration_ms=round(duration_ms, 2),
        )

        return selected, covered_concepts, total_concepts

    def _prepare_questions_with_concepts(
        self,
        questions: list[Question],
    ) -> list[QuestionWithConcepts]:
        """
        Prepare questions with concept ID sets for efficient scoring.

        Args:
            questions: List of Question models with question_concepts loaded

        Returns:
            List of QuestionWithConcepts dataclass instances
        """
        result = []
        for question in questions:
            concept_ids = {
                qc.concept_id for qc in question.question_concepts
            }
            result.append(QuestionWithConcepts(
                question=question,
                concept_ids=concept_ids,
            ))
        return result

    def _select_questions_greedy(
        self,
        questions: list[QuestionWithConcepts],
        target_count: int,
    ) -> tuple[list[Question], set[UUID], dict[str, int]]:
        """
        Greedy algorithm for optimal question selection.

        Scoring function:
        score = (uncovered_concepts * 10) + (discrimination * 5) + (ka_balance * 2)

        Args:
            questions: List of questions with concept IDs
            target_count: Target number of questions to select

        Returns:
            Tuple of:
            - List of selected Question objects
            - Set of covered concept UUIDs
            - Dict of KA -> count distribution
        """
        selected: list[Question] = []
        covered_concepts: set[UUID] = set()
        ka_counts: dict[str, int] = defaultdict(int)

        # Create available pool (copy to avoid modifying input)
        available = list(questions)

        while len(selected) < target_count and available:
            # Find best question
            best_question = None
            best_score = float('-inf')
            best_idx = -1

            for idx, qwc in enumerate(available):
                # Skip if KA already at max
                ka_id = qwc.question.knowledge_area_id
                if ka_counts[ka_id] >= self.MAX_QUESTIONS_PER_KA:
                    continue

                # Calculate score
                score = self._calculate_score(qwc, covered_concepts, ka_counts)

                if score > best_score:
                    best_score = score
                    best_question = qwc
                    best_idx = idx

            # No valid question found (all KAs maxed out or pool empty)
            if best_question is None:
                break

            # Add best question to selection
            selected.append(best_question.question)
            covered_concepts.update(best_question.concept_ids)
            ka_counts[best_question.question.knowledge_area_id] += 1

            # Remove from available pool
            available.pop(best_idx)

        return selected, covered_concepts, ka_counts

    def _calculate_score(
        self,
        qwc: QuestionWithConcepts,
        covered_concepts: set[UUID],
        ka_counts: dict[str, int],
    ) -> float:
        """
        Calculate selection score for a question.

        Score components:
        1. Coverage: Number of uncovered concepts * 10
        2. Discrimination: Question discrimination parameter * 5
        3. KA Balance: (4 - current KA count) * 2

        Args:
            qwc: Question with concepts
            covered_concepts: Set of already covered concept IDs
            ka_counts: Current KA distribution

        Returns:
            Score value (higher is better)
        """
        # Coverage score: prioritize questions with uncovered concepts
        uncovered = len(qwc.concept_ids - covered_concepts)
        coverage_score = uncovered * self.WEIGHT_COVERAGE

        # Discrimination score: prefer more informative questions
        discrimination_score = qwc.question.discrimination * self.WEIGHT_DISCRIMINATION

        # KA balance score: prefer KAs with fewer questions selected
        ka_id = qwc.question.knowledge_area_id
        ka_balance_score = (
            self.MAX_QUESTIONS_PER_KA - ka_counts[ka_id]
        ) * self.WEIGHT_KA_BALANCE

        return coverage_score + discrimination_score + ka_balance_score
