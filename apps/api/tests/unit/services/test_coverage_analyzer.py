"""
Unit tests for CoverageAnalyzer service.
Tests coverage progress tracking and gap analysis (Story 4.5).
"""
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.schemas.belief_state import BeliefStatus
from src.schemas.coverage import (
    CoverageDetailReport,
    CoverageReport,
    CoverageSummary,
    GapConceptList,
    KnowledgeAreaCoverage,
)
from src.services.coverage_analyzer import CoverageAnalyzer


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_belief_repo():
    """Create mock BeliefRepository."""
    return AsyncMock()


@pytest.fixture
def mock_concept_repo():
    """Create mock ConceptRepository."""
    return AsyncMock()


@pytest.fixture
def mock_course_repo():
    """Create mock CourseRepository."""
    return AsyncMock()


@pytest.fixture
def mock_redis():
    """Create mock Redis client."""
    redis = AsyncMock()
    redis.get.return_value = None
    redis.setex.return_value = None
    redis.delete.return_value = None
    return redis


@pytest.fixture
def coverage_analyzer(mock_belief_repo, mock_concept_repo, mock_course_repo):
    """Create CoverageAnalyzer without Redis."""
    return CoverageAnalyzer(
        belief_repository=mock_belief_repo,
        concept_repository=mock_concept_repo,
        course_repository=mock_course_repo,
        redis_client=None,
    )


@pytest.fixture
def coverage_analyzer_with_redis(
    mock_belief_repo, mock_concept_repo, mock_course_repo, mock_redis
):
    """Create CoverageAnalyzer with Redis."""
    return CoverageAnalyzer(
        belief_repository=mock_belief_repo,
        concept_repository=mock_concept_repo,
        course_repository=mock_course_repo,
        redis_client=mock_redis,
    )


def create_mock_belief(concept_id, alpha=1.0, beta=1.0, response_count=0):
    """
    Helper to create mock BeliefState.

    Classification based on BeliefState.status property:
    - mastered: mean >= 0.8 AND confidence >= 0.7
    - gap: mean < 0.5 AND confidence >= 0.7
    - borderline: 0.5 <= mean < 0.8 AND confidence >= 0.7
    - uncertain: confidence < 0.7
    """
    belief = MagicMock()
    belief.concept_id = concept_id
    belief.alpha = alpha
    belief.beta = beta
    belief.response_count = response_count

    # Compute properties
    total = alpha + beta
    mean = alpha / total
    confidence = total / (total + 2)

    belief.mean = mean
    belief.confidence = confidence

    # Compute status based on BeliefState logic
    if confidence < 0.7:
        belief.status = "uncertain"
    elif mean >= 0.8:
        belief.status = "mastered"
    elif mean < 0.5:
        belief.status = "gap"
    else:
        belief.status = "borderline"

    return belief


def create_mock_concept(concept_id, name="Test Concept", ka_id="ba-planning"):
    """Helper to create mock Concept."""
    concept = MagicMock()
    concept.id = concept_id
    concept.name = name
    concept.knowledge_area_id = ka_id
    return concept


def create_mock_course(knowledge_areas=None):
    """Helper to create mock Course."""
    course = MagicMock()
    course.knowledge_areas = knowledge_areas or [
        {"id": "ba-planning", "name": "BA Planning", "display_order": 1},
        {"id": "elicitation", "name": "Elicitation", "display_order": 2},
        {"id": "strategy", "name": "Strategy", "display_order": 3},
    ]
    return course


# ============================================================================
# Status Grouping Tests (AC: 2)
# ============================================================================


class TestStatusGrouping:
    """Test that aggregation correctly groups by BeliefState.status."""

    @pytest.mark.asyncio
    async def test_grouping_mastered(
        self, coverage_analyzer, mock_belief_repo, mock_concept_repo, mock_course_repo
    ):
        """Test beliefs with status='mastered' counted correctly."""
        user_id = uuid4()
        course_id = uuid4()

        # Create mastered beliefs (alpha=9, beta=1 → mean=0.9, confidence=0.83)
        beliefs = [
            create_mock_belief(uuid4(), alpha=9.0, beta=1.0) for _ in range(5)
        ]

        mock_belief_repo.get_all_beliefs.return_value = beliefs
        mock_concept_repo.get_all_concepts.return_value = []
        mock_course_repo.get_by_id.return_value = create_mock_course()

        report = await coverage_analyzer.analyze_coverage(user_id, course_id)

        assert report.mastered == 5
        assert report.gaps == 0
        assert report.borderline == 0
        assert report.uncertain == 0

    @pytest.mark.asyncio
    async def test_grouping_gap(
        self, coverage_analyzer, mock_belief_repo, mock_concept_repo, mock_course_repo
    ):
        """Test beliefs with status='gap' counted correctly."""
        user_id = uuid4()
        course_id = uuid4()

        # Create gap beliefs (alpha=1, beta=9 → mean=0.1, confidence=0.83)
        beliefs = [
            create_mock_belief(uuid4(), alpha=1.0, beta=9.0) for _ in range(3)
        ]

        mock_belief_repo.get_all_beliefs.return_value = beliefs
        mock_concept_repo.get_all_concepts.return_value = []
        mock_course_repo.get_by_id.return_value = create_mock_course()

        report = await coverage_analyzer.analyze_coverage(user_id, course_id)

        assert report.mastered == 0
        assert report.gaps == 3
        assert report.borderline == 0
        assert report.uncertain == 0

    @pytest.mark.asyncio
    async def test_grouping_borderline(
        self, coverage_analyzer, mock_belief_repo, mock_concept_repo, mock_course_repo
    ):
        """Test beliefs with status='borderline' counted correctly."""
        user_id = uuid4()
        course_id = uuid4()

        # Create borderline beliefs (alpha=6, beta=4 → mean=0.6, confidence=0.83)
        beliefs = [
            create_mock_belief(uuid4(), alpha=6.0, beta=4.0) for _ in range(4)
        ]

        mock_belief_repo.get_all_beliefs.return_value = beliefs
        mock_concept_repo.get_all_concepts.return_value = []
        mock_course_repo.get_by_id.return_value = create_mock_course()

        report = await coverage_analyzer.analyze_coverage(user_id, course_id)

        assert report.mastered == 0
        assert report.gaps == 0
        assert report.borderline == 4
        assert report.uncertain == 0

    @pytest.mark.asyncio
    async def test_grouping_uncertain(
        self, coverage_analyzer, mock_belief_repo, mock_concept_repo, mock_course_repo
    ):
        """Test beliefs with status='uncertain' counted correctly."""
        user_id = uuid4()
        course_id = uuid4()

        # Create uncertain beliefs (alpha=1, beta=1 → mean=0.5, confidence=0.5)
        beliefs = [
            create_mock_belief(uuid4(), alpha=1.0, beta=1.0) for _ in range(6)
        ]

        mock_belief_repo.get_all_beliefs.return_value = beliefs
        mock_concept_repo.get_all_concepts.return_value = []
        mock_course_repo.get_by_id.return_value = create_mock_course()

        report = await coverage_analyzer.analyze_coverage(user_id, course_id)

        assert report.mastered == 0
        assert report.gaps == 0
        assert report.borderline == 0
        assert report.uncertain == 6


# ============================================================================
# Percentage Calculation Tests (AC: 3)
# ============================================================================


class TestPercentageCalculations:
    """Test percentage calculations."""

    @pytest.mark.asyncio
    async def test_coverage_percentage_calculation(
        self, coverage_analyzer, mock_belief_repo, mock_concept_repo, mock_course_repo
    ):
        """Test coverage_percentage = mastered / total_concepts."""
        user_id = uuid4()
        course_id = uuid4()

        # 50 mastered, 50 uncertain = 50% coverage
        beliefs = [
            create_mock_belief(uuid4(), alpha=9.0, beta=1.0) for _ in range(50)  # mastered
        ] + [
            create_mock_belief(uuid4(), alpha=1.0, beta=1.0) for _ in range(50)  # uncertain
        ]

        mock_belief_repo.get_all_beliefs.return_value = beliefs
        mock_concept_repo.get_all_concepts.return_value = []
        mock_course_repo.get_by_id.return_value = create_mock_course()

        report = await coverage_analyzer.analyze_coverage(user_id, course_id)

        assert report.total_concepts == 100
        assert report.coverage_percentage == 0.5  # 50/100

    @pytest.mark.asyncio
    async def test_confidence_percentage_calculation(
        self, coverage_analyzer, mock_belief_repo, mock_concept_repo, mock_course_repo
    ):
        """Test confidence_percentage = (mastered + gaps + borderline) / total."""
        user_id = uuid4()
        course_id = uuid4()

        # 30 mastered, 20 gaps, 20 borderline, 30 uncertain = 70% confidence
        beliefs = (
            [create_mock_belief(uuid4(), alpha=9.0, beta=1.0) for _ in range(30)]  # mastered
            + [create_mock_belief(uuid4(), alpha=1.0, beta=9.0) for _ in range(20)]  # gap
            + [create_mock_belief(uuid4(), alpha=6.0, beta=4.0) for _ in range(20)]  # borderline
            + [create_mock_belief(uuid4(), alpha=1.0, beta=1.0) for _ in range(30)]  # uncertain
        )

        mock_belief_repo.get_all_beliefs.return_value = beliefs
        mock_concept_repo.get_all_concepts.return_value = []
        mock_course_repo.get_by_id.return_value = create_mock_course()

        report = await coverage_analyzer.analyze_coverage(user_id, course_id)

        assert report.total_concepts == 100
        assert report.confidence_percentage == 0.7  # (30+20+20)/100

    @pytest.mark.asyncio
    async def test_estimated_questions_remaining(
        self, coverage_analyzer, mock_belief_repo, mock_concept_repo, mock_course_repo
    ):
        """Test estimated_questions_remaining heuristic: uncertain * 4 / 2."""
        user_id = uuid4()
        course_id = uuid4()

        # 100 uncertain concepts → 200 questions
        beliefs = [
            create_mock_belief(uuid4(), alpha=1.0, beta=1.0) for _ in range(100)
        ]

        mock_belief_repo.get_all_beliefs.return_value = beliefs
        mock_concept_repo.get_all_concepts.return_value = []
        mock_course_repo.get_by_id.return_value = create_mock_course()

        report = await coverage_analyzer.analyze_coverage(user_id, course_id)

        assert report.estimated_questions_remaining == 200  # 100 * 4 / 2


# ============================================================================
# Edge Cases
# ============================================================================


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_empty_beliefs_returns_zeros(
        self, coverage_analyzer, mock_belief_repo, mock_concept_repo, mock_course_repo
    ):
        """Test no beliefs returns zero counts."""
        user_id = uuid4()
        course_id = uuid4()

        mock_belief_repo.get_all_beliefs.return_value = []
        mock_concept_repo.get_all_concepts.return_value = []
        mock_course_repo.get_by_id.return_value = create_mock_course()

        report = await coverage_analyzer.analyze_coverage(user_id, course_id)

        assert report.total_concepts == 0
        assert report.mastered == 0
        assert report.gaps == 0
        assert report.borderline == 0
        assert report.uncertain == 0
        assert report.coverage_percentage == 0.0
        assert report.confidence_percentage == 0.0
        assert report.estimated_questions_remaining == 0

    @pytest.mark.asyncio
    async def test_all_mastered(
        self, coverage_analyzer, mock_belief_repo, mock_concept_repo, mock_course_repo
    ):
        """Test 100% coverage when all mastered."""
        user_id = uuid4()
        course_id = uuid4()

        beliefs = [
            create_mock_belief(uuid4(), alpha=9.0, beta=1.0) for _ in range(50)
        ]

        mock_belief_repo.get_all_beliefs.return_value = beliefs
        mock_concept_repo.get_all_concepts.return_value = []
        mock_course_repo.get_by_id.return_value = create_mock_course()

        report = await coverage_analyzer.analyze_coverage(user_id, course_id)

        assert report.coverage_percentage == 1.0
        assert report.confidence_percentage == 1.0
        assert report.estimated_questions_remaining == 0

    @pytest.mark.asyncio
    async def test_all_uncertain(
        self, coverage_analyzer, mock_belief_repo, mock_concept_repo, mock_course_repo
    ):
        """Test 0% coverage and 0% confidence when all uncertain."""
        user_id = uuid4()
        course_id = uuid4()

        beliefs = [
            create_mock_belief(uuid4(), alpha=1.0, beta=1.0) for _ in range(50)
        ]

        mock_belief_repo.get_all_beliefs.return_value = beliefs
        mock_concept_repo.get_all_concepts.return_value = []
        mock_course_repo.get_by_id.return_value = create_mock_course()

        report = await coverage_analyzer.analyze_coverage(user_id, course_id)

        assert report.coverage_percentage == 0.0
        assert report.confidence_percentage == 0.0
        assert report.uncertain == 50


# ============================================================================
# Knowledge Area Breakdown Tests (AC: 3)
# ============================================================================


class TestKnowledgeAreaBreakdown:
    """Test coverage breakdown by knowledge area."""

    @pytest.mark.asyncio
    async def test_ka_breakdown_groups_correctly(
        self, coverage_analyzer, mock_belief_repo, mock_concept_repo, mock_course_repo
    ):
        """Test beliefs grouped by knowledge_area_id."""
        user_id = uuid4()
        course_id = uuid4()

        # Create concepts in different KAs
        concept1 = uuid4()
        concept2 = uuid4()
        concept3 = uuid4()
        concept4 = uuid4()

        concepts = [
            create_mock_concept(concept1, "Concept 1", "ba-planning"),
            create_mock_concept(concept2, "Concept 2", "ba-planning"),
            create_mock_concept(concept3, "Concept 3", "elicitation"),
            create_mock_concept(concept4, "Concept 4", "strategy"),
        ]

        # Create beliefs for these concepts
        beliefs = [
            create_mock_belief(concept1, alpha=9.0, beta=1.0),  # mastered
            create_mock_belief(concept2, alpha=1.0, beta=9.0),  # gap
            create_mock_belief(concept3, alpha=9.0, beta=1.0),  # mastered
            create_mock_belief(concept4, alpha=1.0, beta=1.0),  # uncertain
        ]

        mock_belief_repo.get_all_beliefs.return_value = beliefs
        mock_concept_repo.get_all_concepts.return_value = concepts
        mock_course_repo.get_by_id.return_value = create_mock_course()

        ka_breakdown = await coverage_analyzer.analyze_coverage_by_ka(user_id, course_id)

        # Should have 3 KAs
        assert len(ka_breakdown) == 3

        # Find each KA
        planning = next((ka for ka in ka_breakdown if ka.ka_id == "ba-planning"), None)
        elicit = next((ka for ka in ka_breakdown if ka.ka_id == "elicitation"), None)
        strategy = next((ka for ka in ka_breakdown if ka.ka_id == "strategy"), None)

        # Verify ba-planning: 1 mastered, 1 gap
        assert planning is not None
        assert planning.total_concepts == 2
        assert planning.mastered_count == 1
        assert planning.gap_count == 1
        assert planning.readiness_score == 0.5

        # Verify elicitation: 1 mastered
        assert elicit is not None
        assert elicit.total_concepts == 1
        assert elicit.mastered_count == 1
        assert elicit.readiness_score == 1.0

        # Verify strategy: 1 uncertain
        assert strategy is not None
        assert strategy.total_concepts == 1
        assert strategy.uncertain_count == 1
        assert strategy.readiness_score == 0.0


# ============================================================================
# Gap Concepts Tests (AC: 3)
# ============================================================================


class TestGapConcepts:
    """Test gap concept list generation."""

    @pytest.mark.asyncio
    async def test_get_gaps_returns_sorted_list(
        self, coverage_analyzer, mock_belief_repo, mock_concept_repo
    ):
        """Test gaps sorted by probability ascending (worst first)."""
        user_id = uuid4()
        course_id = uuid4()

        # Create gap beliefs with different probabilities
        concept1, concept2, concept3 = uuid4(), uuid4(), uuid4()

        beliefs = [
            create_mock_belief(concept1, alpha=1.0, beta=4.0),  # mean=0.2
            create_mock_belief(concept2, alpha=1.0, beta=9.0),  # mean=0.1 (worst)
            create_mock_belief(concept3, alpha=2.0, beta=8.0),  # mean=0.2
        ]

        concepts = [
            create_mock_concept(concept1, "Concept 1"),
            create_mock_concept(concept2, "Concept 2"),
            create_mock_concept(concept3, "Concept 3"),
        ]

        mock_belief_repo.get_all_beliefs.return_value = beliefs
        mock_concept_repo.get_all_concepts.return_value = concepts

        gaps = await coverage_analyzer.get_gap_concepts(user_id, course_id)

        assert gaps.total_gaps == 3
        # Should be sorted by probability ascending
        assert gaps.gaps[0].concept_id == concept2  # mean=0.1 first

    @pytest.mark.asyncio
    async def test_get_gaps_respects_limit(
        self, coverage_analyzer, mock_belief_repo, mock_concept_repo
    ):
        """Test gaps can be limited."""
        user_id = uuid4()
        course_id = uuid4()

        # Create 10 gap beliefs
        beliefs = [
            create_mock_belief(uuid4(), alpha=1.0, beta=9.0) for _ in range(10)
        ]
        concepts = [
            create_mock_concept(b.concept_id, f"Concept {i}")
            for i, b in enumerate(beliefs)
        ]

        mock_belief_repo.get_all_beliefs.return_value = beliefs
        mock_concept_repo.get_all_concepts.return_value = concepts

        gaps = await coverage_analyzer.get_gap_concepts(user_id, course_id, limit=5)

        assert gaps.total_gaps == 5
        assert len(gaps.gaps) == 5


# ============================================================================
# Redis Caching Tests (AC: 9)
# ============================================================================


class TestRedisCaching:
    """Test Redis caching functionality."""

    @pytest.mark.asyncio
    async def test_cache_key_format(
        self, coverage_analyzer_with_redis
    ):
        """Test cache key format is coverage:{user_id}:summary."""
        user_id = uuid4()
        key = coverage_analyzer_with_redis._get_cache_key(user_id, "summary")
        assert key == f"coverage:{user_id}:summary"

    @pytest.mark.asyncio
    async def test_invalidate_coverage_cache(
        self, coverage_analyzer_with_redis, mock_redis
    ):
        """Test cache invalidation deletes all coverage keys."""
        user_id = uuid4()

        await coverage_analyzer_with_redis.invalidate_coverage_cache(user_id)

        # Should delete summary, report, and gaps keys
        mock_redis.delete.assert_called_once()
        deleted_keys = mock_redis.delete.call_args[0]
        assert f"coverage:{user_id}:summary" in deleted_keys
        assert f"coverage:{user_id}:report" in deleted_keys
        assert f"coverage:{user_id}:gaps" in deleted_keys

    @pytest.mark.asyncio
    async def test_no_cache_when_redis_none(
        self, coverage_analyzer, mock_belief_repo, mock_concept_repo, mock_course_repo
    ):
        """Test caching gracefully handles None Redis."""
        user_id = uuid4()
        course_id = uuid4()

        mock_belief_repo.get_all_beliefs.return_value = []
        mock_concept_repo.get_all_concepts.return_value = []
        mock_course_repo.get_by_id.return_value = create_mock_course()

        # Should not raise when Redis is None
        report = await coverage_analyzer.analyze_coverage(user_id, course_id)
        assert report is not None


# ============================================================================
# Response Structure Tests
# ============================================================================


class TestResponseStructure:
    """Test response schema structure."""

    @pytest.mark.asyncio
    async def test_analyze_coverage_returns_correct_structure(
        self, coverage_analyzer, mock_belief_repo, mock_concept_repo, mock_course_repo
    ):
        """Test CoverageReport has all required fields."""
        user_id = uuid4()
        course_id = uuid4()

        mock_belief_repo.get_all_beliefs.return_value = [
            create_mock_belief(uuid4(), alpha=9.0, beta=1.0)
        ]
        mock_concept_repo.get_all_concepts.return_value = []
        mock_course_repo.get_by_id.return_value = create_mock_course()

        report = await coverage_analyzer.analyze_coverage(user_id, course_id)

        assert isinstance(report, CoverageReport)
        assert hasattr(report, "total_concepts")
        assert hasattr(report, "mastered")
        assert hasattr(report, "gaps")
        assert hasattr(report, "borderline")
        assert hasattr(report, "uncertain")
        assert hasattr(report, "coverage_percentage")
        assert hasattr(report, "confidence_percentage")
        assert hasattr(report, "estimated_questions_remaining")
        assert hasattr(report, "by_knowledge_area")

    @pytest.mark.asyncio
    async def test_get_detailed_coverage_returns_concept_lists(
        self, coverage_analyzer, mock_belief_repo, mock_concept_repo, mock_course_repo
    ):
        """Test CoverageDetailReport includes concept lists."""
        user_id = uuid4()
        course_id = uuid4()
        concept_id = uuid4()

        beliefs = [create_mock_belief(concept_id, alpha=9.0, beta=1.0)]
        concepts = [create_mock_concept(concept_id, "Test Concept")]

        mock_belief_repo.get_all_beliefs.return_value = beliefs
        mock_concept_repo.get_all_concepts.return_value = concepts
        mock_course_repo.get_by_id.return_value = create_mock_course()

        report = await coverage_analyzer.get_detailed_coverage(user_id, course_id)

        assert isinstance(report, CoverageDetailReport)
        assert hasattr(report, "mastered_concepts")
        assert hasattr(report, "gap_concepts")
        assert hasattr(report, "borderline_concepts")
        assert hasattr(report, "uncertain_concepts")
        assert len(report.mastered_concepts) == 1


# ============================================================================
# Remaining Questions Heuristic Tests
# ============================================================================


class TestRemainingQuestionsHeuristic:
    """Test the _estimate_remaining_questions heuristic."""

    def test_zero_uncertain_returns_zero(self, coverage_analyzer):
        """Test 0 uncertain → 0 questions."""
        assert coverage_analyzer._estimate_remaining_questions(0) == 0

    def test_formula_applies_correctly(self, coverage_analyzer):
        """Test formula: uncertain * 4 / 2."""
        assert coverage_analyzer._estimate_remaining_questions(50) == 100
        assert coverage_analyzer._estimate_remaining_questions(100) == 200
        assert coverage_analyzer._estimate_remaining_questions(1) == 2
