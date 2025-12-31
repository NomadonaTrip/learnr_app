"""
TargetProgressService for calculating focused session target progress.
Computes mastery metrics for KA or concept targets at session end.
"""
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.belief_state import BeliefState
from src.models.concept import Concept
from src.models.course import Course
from src.models.quiz_response import QuizResponse
from src.models.quiz_session import QuizSession
from src.schemas.quiz_session import TargetProgress

logger = structlog.get_logger(__name__)


class TargetProgressService:
    """
    Service for calculating target progress in focused sessions.

    Computes metrics for focused_ka and focused_concept sessions:
    - Current mastery average for target
    - Session improvement (delta from session start)
    - Questions count in focus
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_target_progress(
        self,
        session: QuizSession,
        user_id: UUID,
    ) -> TargetProgress | None:
        """
        Calculate target progress metrics for a focused session.

        Args:
            session: The quiz session (must be focused_ka or focused_concept)
            user_id: User UUID

        Returns:
            TargetProgress with metrics, or None if not a focused session
        """
        # Only calculate for focused sessions
        if session.session_type not in ("focused_ka", "focused_concept"):
            return None

        if session.session_type == "focused_ka":
            return await self._calculate_ka_progress(session, user_id)
        else:
            return await self._calculate_concept_progress(session, user_id)

    async def _calculate_ka_progress(
        self,
        session: QuizSession,
        user_id: UUID,
    ) -> TargetProgress | None:
        """Calculate progress for focused_ka session."""
        if not session.knowledge_area_filter:
            return None

        # Get KA name from course
        enrollment_result = await self.db.execute(
            select(Course)
            .join(Course.enrollments)
            .where(Course.enrollments.any(id=session.enrollment_id))
        )
        course = enrollment_result.scalar_one_or_none()

        ka_name = session.knowledge_area_filter
        if course and course.knowledge_areas:
            for ka in course.knowledge_areas:
                if ka.get("id") == session.knowledge_area_filter:
                    ka_name = ka.get("name", session.knowledge_area_filter)
                    break

        # Get concepts in this KA
        concept_result = await self.db.execute(
            select(Concept.id)
            .where(Concept.knowledge_area_id == session.knowledge_area_filter)
        )
        concept_ids = [row[0] for row in concept_result.all()]

        if not concept_ids:
            return TargetProgress(
                focus_type="ka",
                target_name=ka_name,
                questions_in_focus_count=0,
                session_improvement=0.0,
                current_mastery=0.5,
            )

        # Calculate current mastery
        current_mastery = await self._calculate_average_mastery(user_id, concept_ids)

        # Calculate session improvement and question count
        improvement, question_count = await self._calculate_session_metrics(
            session.id, user_id, concept_ids
        )

        logger.info(
            "target_progress_calculated",
            session_id=str(session.id),
            focus_type="ka",
            target_id=session.knowledge_area_filter,
            current_mastery=current_mastery,
            improvement=improvement,
            questions_in_focus=question_count,
        )

        return TargetProgress(
            focus_type="ka",
            target_name=ka_name,
            questions_in_focus_count=question_count,
            session_improvement=round(improvement, 4),
            current_mastery=round(current_mastery, 4),
        )

    async def _calculate_concept_progress(
        self,
        session: QuizSession,
        user_id: UUID,
    ) -> TargetProgress | None:
        """Calculate progress for focused_concept session."""
        if not session.target_concept_ids:
            return None

        # Convert stored UUIDs (strings) to UUID objects
        target_ids = [UUID(cid) for cid in session.target_concept_ids]

        # Get concept names
        concept_result = await self.db.execute(
            select(Concept.id, Concept.name)
            .where(Concept.id.in_(target_ids))
        )
        concepts = {row[0]: row[1] for row in concept_result.all()}

        if len(concepts) == 1:
            target_name = list(concepts.values())[0]
        else:
            target_name = f"{len(concepts)} concepts"

        if not target_ids:
            return TargetProgress(
                focus_type="concept",
                target_name=target_name,
                questions_in_focus_count=0,
                session_improvement=0.0,
                current_mastery=0.5,
            )

        # Calculate current mastery
        current_mastery = await self._calculate_average_mastery(user_id, target_ids)

        # Calculate session improvement and question count
        improvement, question_count = await self._calculate_session_metrics(
            session.id, user_id, target_ids
        )

        logger.info(
            "target_progress_calculated",
            session_id=str(session.id),
            focus_type="concept",
            target_count=len(target_ids),
            current_mastery=current_mastery,
            improvement=improvement,
            questions_in_focus=question_count,
        )

        return TargetProgress(
            focus_type="concept",
            target_name=target_name,
            questions_in_focus_count=question_count,
            session_improvement=round(improvement, 4),
            current_mastery=round(current_mastery, 4),
        )

    async def _calculate_average_mastery(
        self,
        user_id: UUID,
        concept_ids: list[UUID],
    ) -> float:
        """Calculate average mastery for a set of concepts."""
        if not concept_ids:
            return 0.5

        result = await self.db.execute(
            select(BeliefState.alpha, BeliefState.beta)
            .where(BeliefState.user_id == user_id)
            .where(BeliefState.concept_id.in_(concept_ids))
        )

        beliefs = result.all()
        if not beliefs:
            return 0.5

        total_mastery = sum(
            alpha / (alpha + beta) if (alpha + beta) > 0 else 0.5
            for alpha, beta in beliefs
        )
        return total_mastery / len(beliefs)

    async def _calculate_session_metrics(
        self,
        session_id: UUID,
        user_id: UUID,
        concept_ids: list[UUID],
    ) -> tuple[float, int]:
        """
        Calculate session improvement and question count for target concepts.

        Uses belief_updates stored in quiz_responses to determine:
        - How many questions tested target concepts
        - Total mastery improvement (sum of deltas from all updates)

        Returns:
            Tuple of (improvement, question_count)
        """
        # Get responses for this session that have belief_updates
        from src.models.question_concept import QuestionConcept

        response_result = await self.db.execute(
            select(QuizResponse.belief_updates, QuizResponse.question_id)
            .where(QuizResponse.session_id == session_id)
            .where(QuizResponse.belief_updates.isnot(None))
        )
        responses = response_result.all()

        concept_id_strs = {str(cid) for cid in concept_ids}
        total_improvement = 0.0
        questions_in_focus = 0

        for belief_updates, question_id in responses:
            if not belief_updates:
                continue

            question_hit_target = False

            for update in belief_updates:
                concept_id_str = update.get("concept_id")
                if concept_id_str in concept_id_strs:
                    question_hit_target = True

                    # Calculate improvement from this update
                    old_alpha = update.get("old_alpha", 1.0)
                    old_beta = update.get("old_beta", 1.0)
                    new_alpha = update.get("new_alpha", 1.0)
                    new_beta = update.get("new_beta", 1.0)

                    old_mastery = old_alpha / (old_alpha + old_beta)
                    new_mastery = new_alpha / (new_alpha + new_beta)
                    total_improvement += (new_mastery - old_mastery)

            if question_hit_target:
                questions_in_focus += 1

        return total_improvement, questions_in_focus
