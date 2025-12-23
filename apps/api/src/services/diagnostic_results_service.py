"""
Diagnostic results service for computing results after diagnostic completion.
Aggregates belief states to produce comprehensive knowledge profile.
"""
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.models.belief_state import BeliefState
from src.models.concept import Concept
from src.models.course import Course
from src.models.question import Question
from src.schemas.diagnostic_results import (
    ConceptGap,
    ConfidenceLevel,
    DiagnosticResultsResponse,
    DiagnosticScore,
    KnowledgeAreaResult,
    Recommendations,
)

logger = structlog.get_logger(__name__)


class DiagnosticResultsService:
    """
    Service for computing diagnostic results from belief states.

    Analyzes user's belief states after diagnostic completion to produce:
    - Coverage statistics (total, touched, percentage)
    - Classification counts (mastered, gaps, uncertain)
    - Per-knowledge area breakdown
    - Top identified gaps
    - Personalized recommendations
    """

    # Default thresholds (can be overridden by course config)
    DEFAULT_MASTERY_THRESHOLD = 0.8
    DEFAULT_GAP_THRESHOLD = 0.5
    DEFAULT_CONFIDENCE_THRESHOLD = 0.7

    def __init__(self, db: AsyncSession):
        """
        Initialize service with database session.

        Args:
            db: Async database session
        """
        self.db = db

    async def compute_diagnostic_results(
        self,
        user_id: UUID,
        course_id: UUID,
        answers: dict[str, str] | None = None,
    ) -> DiagnosticResultsResponse:
        """
        Compute comprehensive diagnostic results for a user.

        Args:
            user_id: User UUID
            course_id: Course UUID
            answers: Dict of question_id -> selected_answer from Redis session

        Returns:
            DiagnosticResultsResponse with all computed statistics
        """
        logger.info(
            "Computing diagnostic results",
            user_id=str(user_id),
            course_id=str(course_id),
            answers_count=len(answers) if answers else 0,
        )

        # Compute score from answers
        score = await self._compute_score(answers or {})

        # Get course thresholds
        course = await self._get_course(course_id)
        mastery_threshold = course.mastery_threshold if course else self.DEFAULT_MASTERY_THRESHOLD
        gap_threshold = course.gap_threshold if course else self.DEFAULT_GAP_THRESHOLD
        confidence_threshold = (
            course.confidence_threshold if course else self.DEFAULT_CONFIDENCE_THRESHOLD
        )

        # Get all belief states with concept info for this user/course
        beliefs = await self._get_beliefs_with_concepts(user_id, course_id)

        # Compute basic statistics
        total_concepts = len(beliefs)
        concepts_touched = sum(1 for b in beliefs if b.response_count > 0)
        coverage_percentage = concepts_touched / total_concepts if total_concepts > 0 else 0.0

        # Classify beliefs
        classification = self._classify_beliefs(
            beliefs,
            mastery_threshold,
            gap_threshold,
            confidence_threshold,
        )

        # Compute confidence level based on coverage
        confidence_level = self._compute_confidence_level(coverage_percentage)

        # Compute per-KA breakdown
        by_knowledge_area = await self._compute_ka_breakdown(
            beliefs,
            course,
            mastery_threshold,
            confidence_threshold,
        )

        # Get top gaps
        top_gaps = self._compute_top_gaps(
            classification["gap_candidates"],
            limit=10,
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            coverage_percentage,
            by_knowledge_area,
            classification["uncertain"],
        )

        logger.info(
            "Diagnostic results computed",
            user_id=str(user_id),
            total_concepts=total_concepts,
            concepts_touched=concepts_touched,
            coverage_percentage=round(coverage_percentage, 3),
            estimated_mastered=classification["mastered"],
            estimated_gaps=classification["gaps"],
            uncertain=classification["uncertain"],
        )

        return DiagnosticResultsResponse(
            score=score,
            total_concepts=total_concepts,
            concepts_touched=concepts_touched,
            coverage_percentage=round(coverage_percentage, 3),
            estimated_mastered=classification["mastered"],
            estimated_gaps=classification["gaps"],
            uncertain=classification["uncertain"],
            confidence_level=confidence_level,
            by_knowledge_area=by_knowledge_area,
            top_gaps=top_gaps,
            recommendations=recommendations,
        )

    async def _get_course(self, course_id: UUID) -> Course | None:
        """Get course by ID."""
        result = await self.db.execute(
            select(Course).where(Course.id == course_id)
        )
        return result.scalar_one_or_none()

    async def _compute_score(self, answers: dict[str, str]) -> DiagnosticScore:
        """
        Compute diagnostic score by comparing answers to correct answers.

        Args:
            answers: Dict of question_id -> selected_answer from Redis session

        Returns:
            DiagnosticScore with correct/incorrect counts and percentage
        """
        if not answers:
            return DiagnosticScore(
                questions_answered=0,
                questions_correct=0,
                questions_incorrect=0,
                score_percentage=0.0,
            )

        # Get question IDs from answers
        question_ids = [UUID(qid) for qid in answers.keys()]

        # Fetch correct answers from database
        result = await self.db.execute(
            select(Question.id, Question.correct_answer)
            .where(Question.id.in_(question_ids))
        )
        correct_answers = {str(row.id): row.correct_answer for row in result.all()}

        # Compare answers
        questions_correct = 0
        for question_id, selected_answer in answers.items():
            correct_answer = correct_answers.get(question_id)
            if correct_answer and selected_answer == correct_answer:
                questions_correct += 1

        questions_answered = len(answers)
        questions_incorrect = questions_answered - questions_correct
        score_percentage = (
            round((questions_correct / questions_answered) * 100, 1)
            if questions_answered > 0
            else 0.0
        )

        logger.info(
            "Computed diagnostic score",
            questions_answered=questions_answered,
            questions_correct=questions_correct,
            score_percentage=score_percentage,
        )

        return DiagnosticScore(
            questions_answered=questions_answered,
            questions_correct=questions_correct,
            questions_incorrect=questions_incorrect,
            score_percentage=score_percentage,
        )

    async def _get_beliefs_with_concepts(
        self,
        user_id: UUID,
        course_id: UUID,
    ) -> list[BeliefState]:
        """
        Get all belief states for a user's course with concept info eagerly loaded.

        Args:
            user_id: User UUID
            course_id: Course UUID

        Returns:
            List of BeliefState with concept relationship loaded
        """
        result = await self.db.execute(
            select(BeliefState)
            .options(joinedload(BeliefState.concept))
            .join(Concept, BeliefState.concept_id == Concept.id)
            .where(BeliefState.user_id == user_id)
            .where(Concept.course_id == course_id)
        )
        return list(result.scalars().unique().all())

    def _classify_beliefs(
        self,
        beliefs: list[BeliefState],
        mastery_threshold: float,
        gap_threshold: float,
        confidence_threshold: float,
    ) -> dict:
        """
        Classify beliefs into mastered, gaps, and uncertain categories.

        Args:
            beliefs: List of BeliefState models
            mastery_threshold: Threshold for mastery (default 0.8)
            gap_threshold: Threshold for gap (default 0.5)
            confidence_threshold: Threshold for confidence (default 0.7)

        Returns:
            Dictionary with counts and gap candidates for further processing
        """
        mastered = 0
        gaps = 0
        uncertain = 0
        gap_candidates: list[tuple[BeliefState, float]] = []

        for belief in beliefs:
            mean = belief.mean
            confidence = belief.confidence

            if confidence < confidence_threshold:
                uncertain += 1
            elif mean >= mastery_threshold:
                mastered += 1
            elif mean < gap_threshold:
                gaps += 1
                gap_candidates.append((belief, mean))
            else:
                # Borderline - count as uncertain for display purposes
                uncertain += 1

        return {
            "mastered": mastered,
            "gaps": gaps,
            "uncertain": uncertain,
            "gap_candidates": gap_candidates,
        }

    def _compute_confidence_level(self, coverage: float) -> ConfidenceLevel:
        """
        Determine confidence level based on coverage percentage.

        Args:
            coverage: Coverage percentage (0.0-1.0)

        Returns:
            ConfidenceLevel string
        """
        if coverage < 0.3:
            return "initial"
        elif coverage < 0.7:
            return "developing"
        else:
            return "established"

    async def _compute_ka_breakdown(
        self,
        beliefs: list[BeliefState],
        course: Course | None,
        mastery_threshold: float,
        confidence_threshold: float,
    ) -> list[KnowledgeAreaResult]:
        """
        Compute per-knowledge area statistics.

        Args:
            beliefs: List of BeliefState models with concept loaded
            course: Course model for KA metadata
            mastery_threshold: Mastery threshold for classification
            confidence_threshold: Confidence threshold for classification

        Returns:
            List of KnowledgeAreaResult ordered by display_order
        """
        # Group beliefs by knowledge area
        ka_beliefs: dict[str, list[BeliefState]] = {}
        for belief in beliefs:
            if belief.concept:
                ka_id = belief.concept.knowledge_area_id
                if ka_id not in ka_beliefs:
                    ka_beliefs[ka_id] = []
                ka_beliefs[ka_id].append(belief)

        # Get KA metadata from course
        ka_metadata: dict[str, dict] = {}
        ka_order: dict[str, int] = {}
        if course and course.knowledge_areas:
            for ka in course.knowledge_areas:
                ka_metadata[ka["id"]] = ka
                ka_order[ka["id"]] = ka.get("display_order", 999)

        # Compute statistics per KA
        results: list[KnowledgeAreaResult] = []
        for ka_id, ka_belief_list in ka_beliefs.items():
            concepts_count = len(ka_belief_list)
            touched_count = sum(1 for b in ka_belief_list if b.response_count > 0)

            # Calculate estimated mastery for touched concepts
            touched_beliefs = [b for b in ka_belief_list if b.response_count > 0]
            if touched_beliefs:
                # Average of mean values for touched concepts
                avg_mastery = sum(b.mean for b in touched_beliefs) / len(touched_beliefs)
            else:
                avg_mastery = 0.0

            # Get KA name from metadata or fallback
            ka_info = ka_metadata.get(ka_id, {})
            ka_name = ka_info.get("name", ka_id)

            results.append(KnowledgeAreaResult(
                ka=ka_name,
                ka_id=ka_id,
                concepts=concepts_count,
                touched=touched_count,
                estimated_mastery=round(avg_mastery, 2),
            ))

        # Sort by display order
        results.sort(key=lambda r: ka_order.get(r.ka_id, 999))

        return results

    def _compute_top_gaps(
        self,
        gap_candidates: list[tuple[BeliefState, float]],
        limit: int = 10,
    ) -> list[ConceptGap]:
        """
        Get top gaps sorted by lowest mastery probability.

        Args:
            gap_candidates: List of (BeliefState, mean) tuples
            limit: Maximum gaps to return

        Returns:
            List of ConceptGap objects
        """
        # Sort by mean ascending (lowest mastery first)
        sorted_gaps = sorted(gap_candidates, key=lambda x: x[1])

        return [
            ConceptGap(
                concept_id=belief.concept_id,
                name=belief.concept.name if belief.concept else "Unknown",
                mastery_probability=round(mean, 2),
                knowledge_area=belief.concept.knowledge_area_id if belief.concept else "Unknown",
            )
            for belief, mean in sorted_gaps[:limit]
        ]

    def _generate_recommendations(
        self,
        coverage: float,
        ka_breakdown: list[KnowledgeAreaResult],
        uncertain_count: int,
    ) -> Recommendations:
        """
        Generate actionable recommendations based on results.

        Args:
            coverage: Coverage percentage (0.0-1.0)
            ka_breakdown: Per-KA statistics
            uncertain_count: Count of uncertain concepts

        Returns:
            Recommendations with focus area and message
        """
        # Find KA with lowest mastery (that has been touched)
        touched_kas = [ka for ka in ka_breakdown if ka.touched > 0]
        if touched_kas:
            weakest_ka = min(touched_kas, key=lambda ka: ka.estimated_mastery)
            primary_focus = weakest_ka.ka
        elif ka_breakdown:
            # No touched KAs - recommend first one
            primary_focus = ka_breakdown[0].ka
        else:
            primary_focus = "General Study"

        # Estimate questions needed (average ~3 concepts per question)
        estimated_questions = max(1, int(uncertain_count / 3))

        # Generate contextual message
        coverage_pct = int(coverage * 100)
        if coverage < 0.3:
            message = (
                f"Good start! Your diagnostic covered {coverage_pct}% of concepts. "
                "Continue with adaptive quizzes to build a complete knowledge profile."
            )
        elif coverage < 0.6:
            message = (
                f"Great progress! You've assessed {coverage_pct}% of concepts. "
                f"Focus on {primary_focus} to strengthen your weakest area."
            )
        else:
            message = (
                f"Excellent coverage! With {coverage_pct}% of concepts assessed, "
                "you have a solid baseline. Keep refining through adaptive study."
            )

        return Recommendations(
            primary_focus=primary_focus,
            estimated_questions_to_coverage=estimated_questions,
            message=message,
        )
