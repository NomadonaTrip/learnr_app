"""
Unit tests for DiagnosticResultsService.
Tests the diagnostic results computation logic.
"""
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.services.diagnostic_results_service import DiagnosticResultsService

# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_db():
    """Create mock async database session."""
    return AsyncMock()


@pytest.fixture
def results_service(mock_db):
    """Create DiagnosticResultsService with mock database."""
    return DiagnosticResultsService(mock_db)


def create_mock_belief(
    user_id=None,
    concept_id=None,
    alpha=1.0,
    beta=1.0,
    response_count=0,
    knowledge_area_id="ka-1",
    concept_name="Test Concept",
):
    """Helper to create mock BeliefState with concept."""
    belief = MagicMock()
    belief.user_id = user_id or uuid4()
    belief.concept_id = concept_id or uuid4()
    belief.alpha = alpha
    belief.beta = beta
    belief.response_count = response_count
    belief.last_response_at = None

    # Properties
    belief.mean = alpha / (alpha + beta)
    belief.confidence = (alpha + beta) / (alpha + beta + 2)

    # Related concept
    belief.concept = MagicMock()
    belief.concept.id = belief.concept_id
    belief.concept.name = concept_name
    belief.concept.knowledge_area_id = knowledge_area_id

    return belief


def create_mock_course(
    course_id=None,
    mastery_threshold=0.8,
    gap_threshold=0.5,
    confidence_threshold=0.7,
    knowledge_areas=None,
):
    """Helper to create mock Course."""
    course = MagicMock()
    course.id = course_id or uuid4()
    course.mastery_threshold = mastery_threshold
    course.gap_threshold = gap_threshold
    course.confidence_threshold = confidence_threshold
    course.knowledge_areas = knowledge_areas or [
        {"id": "ka-1", "name": "Knowledge Area 1", "display_order": 1},
        {"id": "ka-2", "name": "Knowledge Area 2", "display_order": 2},
    ]
    return course


# ============================================================================
# Classification Tests
# ============================================================================

class TestBeliefClassification:
    """Test that beliefs are correctly classified into mastered, gaps, uncertain."""

    def test_classifies_mastered_correctly(self, results_service):
        """Verify high mean + high confidence = mastered."""
        beliefs = [
            create_mock_belief(alpha=10.0, beta=2.0, response_count=5),  # mean=0.833, conf=0.857
        ]

        classification = results_service._classify_beliefs(
            beliefs,
            mastery_threshold=0.8,
            gap_threshold=0.5,
            confidence_threshold=0.7,
        )

        assert classification["mastered"] == 1
        assert classification["gaps"] == 0
        assert classification["uncertain"] == 0

    def test_classifies_gaps_correctly(self, results_service):
        """Verify low mean + high confidence = gap."""
        beliefs = [
            create_mock_belief(alpha=2.0, beta=10.0, response_count=5),  # mean=0.167, conf=0.857
        ]

        classification = results_service._classify_beliefs(
            beliefs,
            mastery_threshold=0.8,
            gap_threshold=0.5,
            confidence_threshold=0.7,
        )

        assert classification["mastered"] == 0
        assert classification["gaps"] == 1
        assert classification["uncertain"] == 0
        assert len(classification["gap_candidates"]) == 1

    def test_classifies_uncertain_correctly(self, results_service):
        """Verify low confidence = uncertain."""
        beliefs = [
            create_mock_belief(alpha=1.0, beta=1.0, response_count=1),  # mean=0.5, conf=0.5
        ]

        classification = results_service._classify_beliefs(
            beliefs,
            mastery_threshold=0.8,
            gap_threshold=0.5,
            confidence_threshold=0.7,
        )

        assert classification["mastered"] == 0
        assert classification["gaps"] == 0
        assert classification["uncertain"] == 1

    def test_classifies_borderline_as_uncertain(self, results_service):
        """Verify borderline (0.5-0.8 mean with high confidence) = uncertain for display."""
        beliefs = [
            create_mock_belief(alpha=6.0, beta=4.0, response_count=5),  # mean=0.6, conf=0.833
        ]

        classification = results_service._classify_beliefs(
            beliefs,
            mastery_threshold=0.8,
            gap_threshold=0.5,
            confidence_threshold=0.7,
        )

        # Borderline is counted as uncertain for display
        assert classification["mastered"] == 0
        assert classification["gaps"] == 0
        assert classification["uncertain"] == 1

    def test_mixed_classifications(self, results_service):
        """Verify multiple beliefs are classified correctly."""
        beliefs = [
            create_mock_belief(alpha=10.0, beta=2.0, response_count=5),  # mastered
            create_mock_belief(alpha=2.0, beta=10.0, response_count=5),  # gap
            create_mock_belief(alpha=1.0, beta=1.0, response_count=1),  # uncertain
            create_mock_belief(alpha=8.0, beta=4.0, response_count=5),  # mastered (mean=0.67)
        ]

        classification = results_service._classify_beliefs(
            beliefs,
            mastery_threshold=0.8,
            gap_threshold=0.5,
            confidence_threshold=0.7,
        )

        assert classification["mastered"] == 1  # First one only
        assert classification["gaps"] == 1
        assert classification["uncertain"] == 2  # Third and fourth (borderline)


# ============================================================================
# Confidence Level Tests
# ============================================================================

class TestConfidenceLevel:
    """Test confidence level computation based on coverage."""

    def test_initial_confidence_low_coverage(self, results_service):
        """Verify <30% coverage = initial."""
        assert results_service._compute_confidence_level(0.0) == "initial"
        assert results_service._compute_confidence_level(0.1) == "initial"
        assert results_service._compute_confidence_level(0.29) == "initial"

    def test_developing_confidence_medium_coverage(self, results_service):
        """Verify 30-70% coverage = developing."""
        assert results_service._compute_confidence_level(0.3) == "developing"
        assert results_service._compute_confidence_level(0.5) == "developing"
        assert results_service._compute_confidence_level(0.69) == "developing"

    def test_established_confidence_high_coverage(self, results_service):
        """Verify >70% coverage = established."""
        assert results_service._compute_confidence_level(0.7) == "established"
        assert results_service._compute_confidence_level(0.85) == "established"
        assert results_service._compute_confidence_level(1.0) == "established"


# ============================================================================
# Top Gaps Tests
# ============================================================================

class TestTopGaps:
    """Test top gaps computation."""

    def test_returns_sorted_by_lowest_mastery(self, results_service):
        """Verify gaps are sorted by lowest mastery probability first."""
        beliefs = [
            create_mock_belief(alpha=4.0, beta=6.0, response_count=5, concept_name="Concept A"),  # mean=0.4
            create_mock_belief(alpha=2.0, beta=8.0, response_count=5, concept_name="Concept B"),  # mean=0.2
            create_mock_belief(alpha=3.0, beta=7.0, response_count=5, concept_name="Concept C"),  # mean=0.3
        ]

        gap_candidates = [(b, b.mean) for b in beliefs]
        top_gaps = results_service._compute_top_gaps(gap_candidates, limit=10)

        assert len(top_gaps) == 3
        assert top_gaps[0].name == "Concept B"  # Lowest (0.2)
        assert top_gaps[1].name == "Concept C"  # Middle (0.3)
        assert top_gaps[2].name == "Concept A"  # Highest (0.4)

    def test_respects_limit(self, results_service):
        """Verify only returns up to limit gaps."""
        beliefs = [
            create_mock_belief(alpha=2.0, beta=8.0, response_count=5, concept_name=f"Concept {i}")
            for i in range(20)
        ]

        gap_candidates = [(b, b.mean) for b in beliefs]
        top_gaps = results_service._compute_top_gaps(gap_candidates, limit=10)

        assert len(top_gaps) == 10

    def test_empty_gaps_returns_empty_list(self, results_service):
        """Verify empty input returns empty list."""
        top_gaps = results_service._compute_top_gaps([], limit=10)
        assert top_gaps == []


# ============================================================================
# KA Breakdown Tests
# ============================================================================

class TestKABreakdown:
    """Test per-knowledge area breakdown computation."""

    @pytest.mark.asyncio
    async def test_groups_by_knowledge_area(self, results_service):
        """Verify beliefs are grouped by KA correctly."""
        beliefs = [
            create_mock_belief(knowledge_area_id="ka-1", response_count=1),
            create_mock_belief(knowledge_area_id="ka-1", response_count=1),
            create_mock_belief(knowledge_area_id="ka-2", response_count=0),
        ]

        course = create_mock_course()

        breakdown = await results_service._compute_ka_breakdown(
            beliefs, course, 0.8, 0.7
        )

        assert len(breakdown) == 2
        ka1 = next(ka for ka in breakdown if ka.ka_id == "ka-1")
        ka2 = next(ka for ka in breakdown if ka.ka_id == "ka-2")

        assert ka1.concepts == 2
        assert ka1.touched == 2
        assert ka2.concepts == 1
        assert ka2.touched == 0

    @pytest.mark.asyncio
    async def test_calculates_estimated_mastery(self, results_service):
        """Verify estimated mastery is average of touched concepts."""
        beliefs = [
            create_mock_belief(
                knowledge_area_id="ka-1",
                alpha=8.0, beta=2.0,  # mean=0.8
                response_count=3,
            ),
            create_mock_belief(
                knowledge_area_id="ka-1",
                alpha=6.0, beta=4.0,  # mean=0.6
                response_count=3,
            ),
            create_mock_belief(
                knowledge_area_id="ka-1",
                alpha=1.0, beta=1.0,  # mean=0.5, but not touched
                response_count=0,
            ),
        ]

        course = create_mock_course()

        breakdown = await results_service._compute_ka_breakdown(
            beliefs, course, 0.8, 0.7
        )

        ka1 = next(ka for ka in breakdown if ka.ka_id == "ka-1")

        # Average of touched: (0.8 + 0.6) / 2 = 0.7
        assert ka1.estimated_mastery == 0.7
        assert ka1.touched == 2
        assert ka1.concepts == 3

    @pytest.mark.asyncio
    async def test_sorts_by_display_order(self, results_service):
        """Verify KAs are sorted by display_order from course config."""
        beliefs = [
            create_mock_belief(knowledge_area_id="ka-2", response_count=1),
            create_mock_belief(knowledge_area_id="ka-1", response_count=1),
        ]

        course = create_mock_course(knowledge_areas=[
            {"id": "ka-1", "name": "First", "display_order": 1},
            {"id": "ka-2", "name": "Second", "display_order": 2},
        ])

        breakdown = await results_service._compute_ka_breakdown(
            beliefs, course, 0.8, 0.7
        )

        assert breakdown[0].ka_id == "ka-1"
        assert breakdown[1].ka_id == "ka-2"


# ============================================================================
# Recommendations Tests
# ============================================================================

class TestRecommendations:
    """Test recommendations generation."""

    def test_identifies_weakest_ka_as_focus(self, results_service):
        """Verify primary focus is set to KA with lowest mastery."""
        from src.schemas.diagnostic_results import KnowledgeAreaResult

        ka_breakdown = [
            KnowledgeAreaResult(
                ka="Knowledge Area 1", ka_id="ka-1",
                concepts=10, touched=5, estimated_mastery=0.8
            ),
            KnowledgeAreaResult(
                ka="Knowledge Area 2", ka_id="ka-2",
                concepts=10, touched=5, estimated_mastery=0.4  # Weakest
            ),
            KnowledgeAreaResult(
                ka="Knowledge Area 3", ka_id="ka-3",
                concepts=10, touched=5, estimated_mastery=0.6
            ),
        ]

        recommendations = results_service._generate_recommendations(
            coverage=0.5,
            ka_breakdown=ka_breakdown,
            uncertain_count=15,
        )

        assert recommendations.primary_focus == "Knowledge Area 2"

    def test_estimates_questions_from_uncertain_count(self, results_service):
        """Verify question estimate based on uncertain count."""
        from src.schemas.diagnostic_results import KnowledgeAreaResult

        ka_breakdown = [
            KnowledgeAreaResult(
                ka="Knowledge Area 1", ka_id="ka-1",
                concepts=10, touched=5, estimated_mastery=0.5
            ),
        ]

        recommendations = results_service._generate_recommendations(
            coverage=0.5,
            ka_breakdown=ka_breakdown,
            uncertain_count=30,
        )

        # ~30 uncertain / 3 concepts per question = 10 questions
        assert recommendations.estimated_questions_to_coverage == 10

    def test_low_coverage_message(self, results_service):
        """Verify message for low coverage."""
        from src.schemas.diagnostic_results import KnowledgeAreaResult

        ka_breakdown = [
            KnowledgeAreaResult(
                ka="KA", ka_id="ka-1",
                concepts=10, touched=2, estimated_mastery=0.5
            ),
        ]

        recommendations = results_service._generate_recommendations(
            coverage=0.2,
            ka_breakdown=ka_breakdown,
            uncertain_count=8,
        )

        assert "20%" in recommendations.message
        assert "Good start" in recommendations.message

    def test_medium_coverage_message(self, results_service):
        """Verify message for medium coverage."""
        from src.schemas.diagnostic_results import KnowledgeAreaResult

        ka_breakdown = [
            KnowledgeAreaResult(
                ka="Focus KA", ka_id="ka-1",
                concepts=10, touched=5, estimated_mastery=0.5
            ),
        ]

        recommendations = results_service._generate_recommendations(
            coverage=0.5,
            ka_breakdown=ka_breakdown,
            uncertain_count=5,
        )

        assert "50%" in recommendations.message
        assert "Focus KA" in recommendations.message

    def test_high_coverage_message(self, results_service):
        """Verify message for high coverage."""
        from src.schemas.diagnostic_results import KnowledgeAreaResult

        ka_breakdown = [
            KnowledgeAreaResult(
                ka="KA", ka_id="ka-1",
                concepts=10, touched=8, estimated_mastery=0.7
            ),
        ]

        recommendations = results_service._generate_recommendations(
            coverage=0.8,
            ka_breakdown=ka_breakdown,
            uncertain_count=2,
        )

        assert "80%" in recommendations.message
        assert "Excellent" in recommendations.message


# ============================================================================
# Full Computation Tests
# ============================================================================

class TestFullComputation:
    """Test the complete compute_diagnostic_results method."""

    @pytest.mark.asyncio
    async def test_compute_diagnostic_results(self, results_service, mock_db):
        """Verify full computation returns expected structure."""
        user_id = uuid4()
        course_id = uuid4()
        course = create_mock_course(course_id=course_id)

        beliefs = [
            create_mock_belief(
                user_id=user_id,
                alpha=10.0, beta=2.0,  # mastered
                response_count=5,
                knowledge_area_id="ka-1",
            ),
            create_mock_belief(
                user_id=user_id,
                alpha=2.0, beta=10.0,  # gap
                response_count=5,
                knowledge_area_id="ka-2",
            ),
            create_mock_belief(
                user_id=user_id,
                alpha=1.0, beta=1.0,  # uncertain
                response_count=0,
                knowledge_area_id="ka-1",
            ),
        ]

        # Mock database calls
        with patch.object(
            results_service, '_get_course', return_value=course
        ) as mock_get_course, patch.object(
            results_service, '_get_beliefs_with_concepts', return_value=beliefs
        ) as mock_get_beliefs, patch.object(
            results_service, '_has_completed_adaptive_quiz', return_value=True
        ) as mock_has_quiz:

            results = await results_service.compute_diagnostic_results(
                user_id=user_id,
                course_id=course_id,
            )

            mock_get_course.assert_called_once_with(course_id)
            mock_get_beliefs.assert_called_once_with(user_id, course_id)
            mock_has_quiz.assert_called_once_with(user_id)

            # Verify basic counts
            assert results.total_concepts == 3
            assert results.concepts_touched == 2
            assert round(results.coverage_percentage, 3) == 0.667

            # Verify classification
            assert results.estimated_mastered == 1
            assert results.estimated_gaps == 1
            assert results.uncertain == 1

            # Verify confidence level
            assert results.confidence_level == "developing"

            # Verify KA breakdown exists
            assert len(results.by_knowledge_area) == 2

            # Verify top gaps
            assert len(results.top_gaps) == 1
            assert results.top_gaps[0].mastery_probability == 0.17  # Rounded

            # Verify recommendations
            assert results.recommendations.primary_focus is not None
            assert results.recommendations.message is not None

            # Verify new overall competence fields
            assert results.overall_competence is not None
            assert results.has_completed_adaptive_quiz is True
            # Only 2 beliefs have response_count > 0, so concepts_assessed = 2
            assert results.concepts_assessed == 2
            # Average mean of ASSESSED concepts only: (10/12 + 2/12) / 2 = (0.833 + 0.167) / 2 = 0.5
            assert round(results.overall_competence, 0) == 50  # ~50%
