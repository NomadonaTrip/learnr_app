"""
Coverage Analyzer Service (Story 4.5).
Analyzes corpus coverage and generates reports for progress tracking.

Classifies each concept as:
- MASTERED: High confidence of mastery (P(mastery) >= 0.8, confidence >= 0.7)
- GAP: High confidence of non-mastery (P(mastery) < 0.5, confidence >= 0.7)
- BORDERLINE: Moderate mastery, high confidence (0.5 <= P(mastery) < 0.8, confidence >= 0.7)
- UNCERTAIN: Need more data to classify (confidence < 0.7)
"""
import json
import logging
import time
from uuid import UUID

from redis.asyncio import Redis

from src.models.belief_state import BeliefState
from src.models.concept import Concept
from src.repositories.belief_repository import BeliefRepository
from src.repositories.concept_repository import ConceptRepository
from src.repositories.course_repository import CourseRepository
from src.schemas.belief_state import BeliefStatus
from src.schemas.coverage import (
    ConceptStatus,
    CoverageDetailReport,
    CoverageReport,
    CoverageSummary,
    GapConcept,
    GapConceptList,
    KnowledgeAreaCoverage,
)

logger = logging.getLogger(__name__)


class CoverageAnalyzer:
    """
    Analyzes corpus coverage and generates reports.

    Uses BeliefState.status property for classification - does NOT reimplement
    the classification logic (per Task 2 requirements).
    """

    # Cache configuration
    CACHE_KEY_PREFIX = "coverage"
    CACHE_TTL_SECONDS = 300  # 5 minutes

    def __init__(
        self,
        belief_repository: BeliefRepository,
        concept_repository: ConceptRepository,
        course_repository: CourseRepository,
        redis_client: Redis | None = None,
    ):
        """
        Initialize CoverageAnalyzer with dependencies.

        Args:
            belief_repository: Repository for belief state access
            concept_repository: Repository for concept access
            course_repository: Repository for course access
            redis_client: Optional Redis client for caching
        """
        self.belief_repository = belief_repository
        self.concept_repository = concept_repository
        self.course_repository = course_repository
        self.redis = redis_client

    def _get_cache_key(self, user_id: UUID, suffix: str = "summary") -> str:
        """Generate cache key for coverage data."""
        return f"{self.CACHE_KEY_PREFIX}:{user_id}:{suffix}"

    async def _get_cached_coverage(self, user_id: UUID) -> CoverageSummary | None:
        """
        Get cached coverage summary.

        Args:
            user_id: User UUID

        Returns:
            CoverageSummary if cached, None otherwise
        """
        if not self.redis:
            return None

        try:
            cache_key = self._get_cache_key(user_id, "summary")
            cached = await self.redis.get(cache_key)
            if cached:
                data = json.loads(cached)
                return CoverageSummary(**data)
        except Exception as e:
            logger.warning(f"Failed to get cached coverage: {e}")

        return None

    async def _set_cached_coverage(
        self,
        user_id: UUID,
        coverage: CoverageSummary,
        ttl: int | None = None
    ) -> None:
        """
        Cache coverage summary.

        Args:
            user_id: User UUID
            coverage: Coverage summary to cache
            ttl: Optional TTL override (defaults to CACHE_TTL_SECONDS)
        """
        if not self.redis:
            return

        try:
            cache_key = self._get_cache_key(user_id, "summary")
            ttl = ttl or self.CACHE_TTL_SECONDS
            # Serialize using model_dump for Pydantic v2
            await self.redis.setex(
                cache_key,
                ttl,
                json.dumps(coverage.model_dump())
            )
        except Exception as e:
            logger.warning(f"Failed to cache coverage: {e}")

    async def invalidate_coverage_cache(self, user_id: UUID) -> None:
        """
        Invalidate cached coverage for a user.

        Should be called by BeliefUpdater after belief updates.

        Args:
            user_id: User UUID
        """
        if not self.redis:
            return

        try:
            # Invalidate all coverage cache keys for this user
            keys_to_delete = [
                self._get_cache_key(user_id, "summary"),
                self._get_cache_key(user_id, "report"),
                self._get_cache_key(user_id, "gaps"),
            ]
            await self.redis.delete(*keys_to_delete)
            logger.debug(f"Invalidated coverage cache for user {user_id}")
        except Exception as e:
            logger.warning(f"Failed to invalidate coverage cache: {e}")

    def _estimate_remaining_questions(self, uncertain_count: int) -> int:
        """
        Estimate questions needed to achieve full coverage.

        Heuristic: ~4 questions per uncertain concept,
        accounting for multi-concept questions (avg 2 concepts per question).

        Args:
            uncertain_count: Number of uncertain concepts

        Returns:
            Estimated number of questions remaining
        """
        if uncertain_count == 0:
            return 0
        # Average concepts per question ≈ 2
        # Average questions to resolve uncertainty ≈ 4
        return int(uncertain_count * 4 / 2)

    def _build_concept_status(
        self,
        belief: BeliefState,
        concept: Concept
    ) -> ConceptStatus:
        """
        Build ConceptStatus from belief and concept.

        Args:
            belief: BeliefState model
            concept: Concept model

        Returns:
            ConceptStatus schema
        """
        return ConceptStatus(
            concept_id=belief.concept_id,
            concept_name=concept.name,
            knowledge_area_id=concept.knowledge_area_id,
            status=BeliefStatus(belief.status),
            probability=round(belief.mean, 4),
            confidence=round(belief.confidence, 4),
        )

    async def analyze_coverage(
        self,
        user_id: UUID,
        course_id: UUID,
        use_cache: bool = True
    ) -> CoverageReport:
        """
        Generate comprehensive coverage report.

        Args:
            user_id: User UUID
            course_id: Course UUID
            use_cache: Whether to use cached results

        Returns:
            CoverageReport with summary and KA breakdown
        """
        start_time = time.perf_counter()

        # Check cache first
        if use_cache:
            cached = await self._get_cached_coverage(user_id)
            if cached:
                logger.debug(f"Returning cached coverage for user {user_id}")
                # For cached summary, we need to fetch KA breakdown separately
                # or cache the full report. For now, return summary-only.
                ka_breakdown = await self.analyze_coverage_by_ka(user_id, course_id)
                return CoverageReport(
                    **cached.model_dump(),
                    by_knowledge_area=ka_breakdown
                )

        # Fetch all beliefs for the user
        beliefs = await self.belief_repository.get_all_beliefs(user_id)

        # Group by status using BeliefState.status property
        status_groups: dict[str, list[BeliefState]] = {
            "mastered": [],
            "gap": [],
            "borderline": [],
            "uncertain": [],
        }

        for belief in beliefs:
            status_groups[belief.status].append(belief)

        # Calculate counts
        total_concepts = len(beliefs)
        mastered_count = len(status_groups["mastered"])
        gap_count = len(status_groups["gap"])
        borderline_count = len(status_groups["borderline"])
        uncertain_count = len(status_groups["uncertain"])

        # Calculate percentages (avoid division by zero)
        if total_concepts > 0:
            coverage_percentage = mastered_count / total_concepts
            # Confidence percentage = classified concepts (not uncertain)
            classified_count = mastered_count + gap_count + borderline_count
            confidence_percentage = classified_count / total_concepts
        else:
            coverage_percentage = 0.0
            confidence_percentage = 0.0

        # Estimate remaining questions
        estimated_remaining = self._estimate_remaining_questions(uncertain_count)

        # Build summary
        summary = CoverageSummary(
            total_concepts=total_concepts,
            mastered=mastered_count,
            gaps=gap_count,
            borderline=borderline_count,
            uncertain=uncertain_count,
            coverage_percentage=round(coverage_percentage, 4),
            confidence_percentage=round(confidence_percentage, 4),
            estimated_questions_remaining=estimated_remaining,
        )

        # Cache the summary
        if use_cache:
            await self._set_cached_coverage(user_id, summary)

        # Get KA breakdown
        ka_breakdown = await self.analyze_coverage_by_ka(user_id, course_id)

        # Log performance
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        logger.info(f"Coverage analysis for user {user_id} completed in {elapsed_ms:.2f}ms")

        return CoverageReport(
            **summary.model_dump(),
            by_knowledge_area=ka_breakdown
        )

    async def analyze_coverage_by_ka(
        self,
        user_id: UUID,
        course_id: UUID
    ) -> list[KnowledgeAreaCoverage]:
        """
        Generate coverage breakdown by knowledge area.

        Args:
            user_id: User UUID
            course_id: Course UUID

        Returns:
            List of KnowledgeAreaCoverage for each KA
        """
        # Get course for KA names
        course = await self.course_repository.get_by_id(course_id)
        if not course:
            logger.warning(f"Course {course_id} not found")
            return []

        # Build KA name lookup
        ka_names: dict[str, str] = {}
        if course.knowledge_areas:
            for ka in course.knowledge_areas:
                ka_names[ka.get("id", "")] = ka.get("name", ka.get("id", "Unknown"))

        # Get all beliefs
        beliefs = await self.belief_repository.get_all_beliefs(user_id)

        # Get all concepts for mapping belief -> KA
        concepts = await self.concept_repository.get_all_concepts(course_id)
        concept_map: dict[UUID, Concept] = {c.id: c for c in concepts}

        # Group beliefs by KA
        ka_beliefs: dict[str, list[BeliefState]] = {}
        for belief in beliefs:
            concept = concept_map.get(belief.concept_id)
            if concept:
                ka_id = concept.knowledge_area_id
                if ka_id not in ka_beliefs:
                    ka_beliefs[ka_id] = []
                ka_beliefs[ka_id].append(belief)

        # Build KA coverage list
        result: list[KnowledgeAreaCoverage] = []

        for ka_id, ka_belief_list in ka_beliefs.items():
            # Count by status
            mastered = 0
            gap = 0
            borderline = 0
            uncertain = 0

            for b in ka_belief_list:
                status = b.status
                if status == "mastered":
                    mastered += 1
                elif status == "gap":
                    gap += 1
                elif status == "borderline":
                    borderline += 1
                else:
                    uncertain += 1

            total = len(ka_belief_list)
            readiness = mastered / total if total > 0 else 0.0

            result.append(KnowledgeAreaCoverage(
                ka_id=ka_id,
                ka_name=ka_names.get(ka_id, ka_id),
                total_concepts=total,
                mastered_count=mastered,
                gap_count=gap,
                borderline_count=borderline,
                uncertain_count=uncertain,
                readiness_score=round(readiness, 4),
            ))

        # Sort by display order if available, else by ka_id
        if course.knowledge_areas:
            order_map = {
                ka.get("id"): ka.get("display_order", 999)
                for ka in course.knowledge_areas
            }
            result.sort(key=lambda x: order_map.get(x.ka_id, 999))

        return result

    async def get_gap_concepts(
        self,
        user_id: UUID,
        course_id: UUID,
        limit: int | None = None
    ) -> GapConceptList:
        """
        Get list of gap concepts sorted by priority (lowest probability first).

        Useful for focused practice mode.

        Args:
            user_id: User UUID
            course_id: Course UUID
            limit: Optional limit on number of gaps returned

        Returns:
            GapConceptList with gaps sorted by probability ascending
        """
        # Get all beliefs
        beliefs = await self.belief_repository.get_all_beliefs(user_id)

        # Get concepts for names and KA
        concepts = await self.concept_repository.get_all_concepts(course_id)
        concept_map: dict[UUID, Concept] = {c.id: c for c in concepts}

        # Filter to gap beliefs and build list
        gaps: list[GapConcept] = []
        for belief in beliefs:
            if belief.status == "gap":
                concept = concept_map.get(belief.concept_id)
                if concept:
                    gaps.append(GapConcept(
                        concept_id=belief.concept_id,
                        concept_name=concept.name,
                        knowledge_area_id=concept.knowledge_area_id,
                        probability=round(belief.mean, 4),
                        confidence=round(belief.confidence, 4),
                    ))

        # Sort by probability ascending (worst gaps first)
        gaps.sort(key=lambda x: x.probability)

        # Apply limit if specified
        if limit:
            gaps = gaps[:limit]

        return GapConceptList(
            total_gaps=len(gaps),
            gaps=gaps,
        )

    async def get_detailed_coverage(
        self,
        user_id: UUID,
        course_id: UUID
    ) -> CoverageDetailReport:
        """
        Get detailed coverage report with concept lists.

        For debugging and analytics purposes.

        Args:
            user_id: User UUID
            course_id: Course UUID

        Returns:
            CoverageDetailReport with full concept lists
        """
        # Get basic coverage
        report = await self.analyze_coverage(user_id, course_id, use_cache=False)

        # Get all beliefs and concepts
        beliefs = await self.belief_repository.get_all_beliefs(user_id)
        concepts = await self.concept_repository.get_all_concepts(course_id)
        concept_map: dict[UUID, Concept] = {c.id: c for c in concepts}

        # Build concept status lists
        mastered_concepts: list[ConceptStatus] = []
        gap_concepts: list[ConceptStatus] = []
        borderline_concepts: list[ConceptStatus] = []
        uncertain_concepts: list[ConceptStatus] = []

        for belief in beliefs:
            concept = concept_map.get(belief.concept_id)
            if not concept:
                continue

            status_obj = self._build_concept_status(belief, concept)

            if belief.status == "mastered":
                mastered_concepts.append(status_obj)
            elif belief.status == "gap":
                gap_concepts.append(status_obj)
            elif belief.status == "borderline":
                borderline_concepts.append(status_obj)
            else:
                uncertain_concepts.append(status_obj)

        # Sort each list by probability (descending for mastered, ascending for gaps)
        mastered_concepts.sort(key=lambda x: x.probability, reverse=True)
        gap_concepts.sort(key=lambda x: x.probability)
        borderline_concepts.sort(key=lambda x: x.probability)
        uncertain_concepts.sort(key=lambda x: x.confidence)

        return CoverageDetailReport(
            **report.model_dump(),
            mastered_concepts=mastered_concepts,
            gap_concepts=gap_concepts,
            borderline_concepts=borderline_concepts,
            uncertain_concepts=uncertain_concepts,
        )
