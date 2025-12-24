"""
MasteryGate service for prerequisite-based curriculum navigation.
Story 4.11: Prerequisite-Based Curriculum Navigation

This service checks if prerequisites are mastered before allowing
access to advanced concepts.
"""
import time
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.belief_state import BeliefState
from src.models.concept import Concept
from src.models.concept_unlock_event import ConceptUnlockEvent
from src.repositories.belief_repository import BeliefRepository
from src.repositories.concept_repository import ConceptRepository
from src.schemas.mastery_gate import (
    BlockingPrerequisite,
    BulkUnlockStatusResponse,
    ConceptUnlockEventResponse,
    ConceptUnlockStatus,
    GateCheckResult,
    MasteryGateConfig,
    RecentUnlocksResponse,
)

logger = structlog.get_logger(__name__)

# Default configuration
DEFAULT_CONFIG = MasteryGateConfig()


class MasteryGateService:
    """
    Service for checking and enforcing prerequisite mastery gates.

    Mastery gates ensure users build knowledge systematically by requiring
    mastery of prerequisite concepts before advanced concepts are unlocked.
    """

    def __init__(
        self,
        session: AsyncSession,
        belief_repository: BeliefRepository,
        concept_repository: ConceptRepository,
        config: MasteryGateConfig | None = None,
    ):
        self.session = session
        self.belief_repository = belief_repository
        self.concept_repository = concept_repository
        self.config = config or DEFAULT_CONFIG

    async def check_prerequisites_mastered(
        self,
        user_id: UUID,
        concept_id: UUID,
    ) -> GateCheckResult:
        """
        Check if all prerequisites for a concept are mastered.

        Args:
            user_id: User UUID
            concept_id: Target concept UUID

        Returns:
            GateCheckResult with unlock status and blocking prerequisites
        """
        start_time = time.perf_counter()

        # Get concept details
        concept = await self.concept_repository.get_by_id(concept_id)
        if not concept:
            raise ValueError(f"Concept {concept_id} not found")

        # Get prerequisites with strength
        prereqs_with_strength = await self.concept_repository.get_prerequisites_with_strength(
            concept_id
        )

        # If no prerequisites, concept is unlocked
        if not prereqs_with_strength:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.debug(
                "gate_check_no_prerequisites",
                concept_id=str(concept_id),
                duration_ms=round(duration_ms, 2),
            )
            return GateCheckResult(
                concept_id=concept_id,
                concept_name=concept.name,
                is_unlocked=True,
                blocking_prerequisites=[],
                closest_to_unlock=None,
                mastery_progress=1.0,
                estimated_questions_to_unlock=0,
            )

        # Get user beliefs for all prerequisites
        beliefs = await self.belief_repository.get_beliefs_as_dict(user_id)

        # Check each prerequisite
        blocking = []
        total_progress = 0.0

        for prereq_concept, strength, rel_type in prereqs_with_strength:
            # Only check 'required' prerequisites for gates
            if rel_type != "required":
                total_progress += 1.0
                continue

            belief = beliefs.get(prereq_concept.id)

            if belief is None:
                # No belief state - treat as not mastered
                blocking_prereq = BlockingPrerequisite(
                    concept_id=prereq_concept.id,
                    name=prereq_concept.name,
                    current_mastery=0.5,  # Prior
                    current_confidence=0.5,  # Prior
                    required_mastery=self.config.prerequisite_mastery_threshold,
                    required_confidence=self.config.prerequisite_confidence_threshold,
                    responses_count=0,
                    progress_to_unlock=0.0,
                )
                blocking.append(blocking_prereq)
                continue

            # Check mastery gate
            is_mastered = self._meets_mastery_gate(belief)

            if not is_mastered:
                progress = self._calculate_progress(belief)
                blocking_prereq = BlockingPrerequisite(
                    concept_id=prereq_concept.id,
                    name=prereq_concept.name,
                    current_mastery=belief.mean,
                    current_confidence=belief.confidence,
                    required_mastery=self.config.prerequisite_mastery_threshold,
                    required_confidence=self.config.prerequisite_confidence_threshold,
                    responses_count=belief.response_count,
                    progress_to_unlock=progress,
                )
                blocking.append(blocking_prereq)
                total_progress += progress
            else:
                total_progress += 1.0

        # Calculate overall progress
        required_count = sum(1 for _, _, t in prereqs_with_strength if t == "required")
        mastery_progress = total_progress / required_count if required_count > 0 else 1.0

        # Find closest to unlock
        closest = None
        if blocking:
            closest = max(blocking, key=lambda b: b.progress_to_unlock)

        # Estimate questions to unlock
        estimated_questions = self._estimate_questions_to_unlock(blocking)

        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            "gate_check_complete",
            user_id=str(user_id),
            concept_id=str(concept_id),
            is_unlocked=len(blocking) == 0,
            blocking_count=len(blocking),
            mastery_progress=round(mastery_progress, 4),
            duration_ms=round(duration_ms, 2),
        )

        return GateCheckResult(
            concept_id=concept_id,
            concept_name=concept.name,
            is_unlocked=len(blocking) == 0,
            blocking_prerequisites=blocking,
            closest_to_unlock=closest,
            mastery_progress=mastery_progress,
            estimated_questions_to_unlock=estimated_questions,
        )

    def _meets_mastery_gate(self, belief: BeliefState) -> bool:
        """Check if a belief state meets the mastery gate threshold."""
        # Check minimum responses
        if belief.response_count < self.config.min_responses_for_gate:
            return False

        # Check mastery and confidence thresholds
        return (
            belief.mean >= self.config.prerequisite_mastery_threshold
            and belief.confidence >= self.config.prerequisite_confidence_threshold
        )

    def _calculate_progress(self, belief: BeliefState) -> float:
        """Calculate progress toward meeting mastery gate (0.0-1.0)."""
        # Weight mastery and confidence equally
        mastery_progress = min(
            belief.mean / self.config.prerequisite_mastery_threshold, 1.0
        )
        confidence_progress = min(
            belief.confidence / self.config.prerequisite_confidence_threshold, 1.0
        )
        return (mastery_progress + confidence_progress) / 2

    def _estimate_questions_to_unlock(
        self, blocking: list[BlockingPrerequisite]
    ) -> int:
        """Estimate questions needed to unlock based on blocking prerequisites."""
        if not blocking:
            return 0

        total_questions = 0
        for prereq in blocking:
            # Estimate based on gap to threshold
            mastery_gap = max(0, prereq.required_mastery - prereq.current_mastery)

            # Rough heuristic: ~4 correct answers to increase mastery by 0.1
            # and ~3 responses minimum to build confidence
            questions_for_mastery = int(mastery_gap * 40)
            questions_for_confidence = max(0, 3 - prereq.responses_count)

            total_questions += max(questions_for_mastery, questions_for_confidence)

        return total_questions

    async def get_bulk_unlock_status(
        self,
        user_id: UUID,
        course_id: UUID,
        knowledge_area_id: str | None = None,
    ) -> BulkUnlockStatusResponse:
        """
        Get unlock status for all concepts in a course or knowledge area.

        Args:
            user_id: User UUID
            course_id: Course UUID
            knowledge_area_id: Optional KA filter

        Returns:
            BulkUnlockStatusResponse with status for all concepts
        """
        start_time = time.perf_counter()

        # Build query for concepts
        query = select(Concept).where(Concept.course_id == course_id)
        if knowledge_area_id:
            query = query.where(Concept.knowledge_area_id == knowledge_area_id)
        query = query.order_by(Concept.name)

        result = await self.session.execute(query)
        concepts = list(result.scalars().all())

        # Get all prerequisites for the course
        all_prereqs = await self.concept_repository.get_all_prerequisites_for_course(
            course_id
        )

        # Build prerequisite map: concept_id -> list of prereq_concept_ids
        prereq_map: dict[UUID, list[UUID]] = {}
        for prereq in all_prereqs:
            if prereq.concept_id not in prereq_map:
                prereq_map[prereq.concept_id] = []
            prereq_map[prereq.concept_id].append(prereq.prerequisite_concept_id)

        # Get user beliefs
        beliefs = await self.belief_repository.get_beliefs_as_dict(user_id)

        # Check each concept
        statuses = []
        unlocked_count = 0
        locked_count = 0
        no_prereqs_count = 0

        for concept in concepts:
            prereq_ids = prereq_map.get(concept.id, [])
            has_prerequisites = len(prereq_ids) > 0

            if not has_prerequisites:
                # No prerequisites = always unlocked
                no_prereqs_count += 1
                unlocked_count += 1
                statuses.append(
                    ConceptUnlockStatus(
                        concept_id=concept.id,
                        concept_name=concept.name,
                        knowledge_area_id=concept.knowledge_area_id,
                        is_unlocked=True,
                        has_prerequisites=False,
                        prerequisite_count=0,
                        mastered_prerequisite_count=0,
                        mastery_progress=1.0,
                    )
                )
                continue

            # Check prerequisites
            mastered_count = 0
            total_progress = 0.0

            for prereq_id in prereq_ids:
                belief = beliefs.get(prereq_id)
                if belief and self._meets_mastery_gate(belief):
                    mastered_count += 1
                    total_progress += 1.0
                elif belief:
                    total_progress += self._calculate_progress(belief)

            is_unlocked = mastered_count == len(prereq_ids)
            progress = total_progress / len(prereq_ids) if prereq_ids else 1.0

            if is_unlocked:
                unlocked_count += 1
            else:
                locked_count += 1

            statuses.append(
                ConceptUnlockStatus(
                    concept_id=concept.id,
                    concept_name=concept.name,
                    knowledge_area_id=concept.knowledge_area_id,
                    is_unlocked=is_unlocked,
                    has_prerequisites=True,
                    prerequisite_count=len(prereq_ids),
                    mastered_prerequisite_count=mastered_count,
                    mastery_progress=progress,
                )
            )

        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            "bulk_unlock_status_complete",
            user_id=str(user_id),
            course_id=str(course_id),
            knowledge_area_id=knowledge_area_id,
            total_concepts=len(concepts),
            unlocked=unlocked_count,
            locked=locked_count,
            duration_ms=round(duration_ms, 2),
        )

        return BulkUnlockStatusResponse(
            knowledge_area_id=knowledge_area_id,
            total_concepts=len(concepts),
            unlocked_count=unlocked_count,
            locked_count=locked_count,
            no_prerequisites_count=no_prereqs_count,
            concepts=statuses,
        )

    async def record_unlock_event(
        self,
        user_id: UUID,
        concept_id: UUID,
        triggering_prereq_id: UUID | None = None,
    ) -> ConceptUnlockEvent:
        """
        Record a concept unlock event.

        Args:
            user_id: User UUID
            concept_id: Unlocked concept UUID
            triggering_prereq_id: Prerequisite that triggered unlock (optional)

        Returns:
            Created ConceptUnlockEvent
        """
        event = ConceptUnlockEvent(
            user_id=user_id,
            concept_id=concept_id,
            prerequisite_concept_id=triggering_prereq_id,
        )
        self.session.add(event)
        await self.session.flush()

        logger.info(
            "concept_unlocked",
            user_id=str(user_id),
            concept_id=str(concept_id),
            triggering_prereq_id=str(triggering_prereq_id) if triggering_prereq_id else None,
        )

        return event

    async def get_recent_unlocks(
        self,
        user_id: UUID,
        limit: int = 5,
    ) -> RecentUnlocksResponse:
        """
        Get recently unlocked concepts for a user.

        Args:
            user_id: User UUID
            limit: Maximum number of recent unlocks to return

        Returns:
            RecentUnlocksResponse with recent unlock events
        """
        # Query unlock events with concept names
        query = (
            select(ConceptUnlockEvent, Concept.name)
            .join(Concept, ConceptUnlockEvent.concept_id == Concept.id)
            .where(ConceptUnlockEvent.user_id == user_id)
            .order_by(ConceptUnlockEvent.unlocked_at.desc())
            .limit(limit)
        )

        result = await self.session.execute(query)
        rows = result.all()

        # Count total unlocked
        count_query = (
            select(ConceptUnlockEvent)
            .where(ConceptUnlockEvent.user_id == user_id)
        )
        count_result = await self.session.execute(count_query)
        total = len(list(count_result.scalars().all()))

        unlocks = []
        for event, concept_name in rows:
            # Get prerequisite name if available
            prereq_name = None
            if event.prerequisite_concept_id:
                prereq = await self.concept_repository.get_by_id(
                    event.prerequisite_concept_id
                )
                prereq_name = prereq.name if prereq else None

            unlocks.append(
                ConceptUnlockEventResponse(
                    id=event.id,
                    user_id=event.user_id,
                    concept_id=event.concept_id,
                    concept_name=concept_name,
                    prerequisite_concept_id=event.prerequisite_concept_id,
                    prerequisite_concept_name=prereq_name,
                    unlocked_at=event.unlocked_at,
                )
            )

        return RecentUnlocksResponse(
            unlocks=unlocks,
            total_unlocked=total,
        )

    async def check_and_record_unlocks(
        self,
        user_id: UUID,
        updated_concept_id: UUID,
    ) -> list[ConceptUnlockEvent]:
        """
        Check if mastering a concept unlocks any dependent concepts.

        Called after belief updates to trigger unlock events.

        Args:
            user_id: User UUID
            updated_concept_id: Concept that was just updated

        Returns:
            List of new unlock events created
        """
        # Get concepts that depend on this concept
        dependents = await self.concept_repository.get_dependents(updated_concept_id)

        new_unlocks = []
        for dependent in dependents:
            # Check if this concept is now unlocked
            gate_result = await self.check_prerequisites_mastered(
                user_id, dependent.id
            )

            if gate_result.is_unlocked:
                # Check if already recorded
                existing = await self.session.execute(
                    select(ConceptUnlockEvent)
                    .where(ConceptUnlockEvent.user_id == user_id)
                    .where(ConceptUnlockEvent.concept_id == dependent.id)
                )
                if existing.scalar_one_or_none() is None:
                    # Record new unlock
                    event = await self.record_unlock_event(
                        user_id=user_id,
                        concept_id=dependent.id,
                        triggering_prereq_id=updated_concept_id,
                    )
                    new_unlocks.append(event)

        return new_unlocks
