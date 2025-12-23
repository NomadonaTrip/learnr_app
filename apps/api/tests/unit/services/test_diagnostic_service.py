"""
Unit tests for DiagnosticService.
Tests the optimal question selection algorithm.
"""
from collections import defaultdict
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.services.diagnostic_service import DiagnosticService, QuestionWithConcepts

# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_question_repo():
    """Create mock QuestionRepository."""
    return AsyncMock()


@pytest.fixture
def mock_concept_repo():
    """Create mock ConceptRepository."""
    return AsyncMock()


@pytest.fixture
def diagnostic_service(mock_question_repo, mock_concept_repo):
    """Create DiagnosticService with mock repositories."""
    return DiagnosticService(mock_question_repo, mock_concept_repo)


def create_mock_question(
    question_id=None,
    knowledge_area_id="ba-planning",
    discrimination=1.0,
    difficulty=0.5,
    concept_ids=None,
):
    """Helper to create mock Question with QuestionConcept relationships."""
    question = MagicMock()
    question.id = question_id or uuid4()
    question.knowledge_area_id = knowledge_area_id
    question.discrimination = discrimination
    question.difficulty = difficulty
    question.question_text = f"Question {question.id}"
    question.options = {"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"}
    question.correct_answer = "A"
    question.explanation = "Explanation"

    # Mock question_concepts relationship
    question.question_concepts = []
    if concept_ids:
        for cid in concept_ids:
            qc = MagicMock()
            qc.concept_id = cid
            qc.relevance = 1.0
            question.question_concepts.append(qc)

    return question


# ============================================================================
# Coverage Optimization Tests
# ============================================================================

class TestCoverageOptimization:
    """Test that algorithm prioritizes questions covering uncovered concepts."""

    @pytest.mark.asyncio
    async def test_prioritizes_uncovered_concepts(
        self, diagnostic_service, mock_question_repo, mock_concept_repo
    ):
        """Verify questions with more uncovered concepts are selected first."""
        concept1, concept2, concept3 = uuid4(), uuid4(), uuid4()

        # Q1 covers concepts 1, 2, 3 (3 concepts)
        # Q2 covers concept 1 only (1 concept)
        # Q3 covers concept 2 only (1 concept)
        q1 = create_mock_question(concept_ids=[concept1, concept2, concept3])
        q2 = create_mock_question(concept_ids=[concept1])
        q3 = create_mock_question(concept_ids=[concept2])

        mock_question_repo.get_questions_with_concepts.return_value = [q2, q3, q1]
        mock_concept_repo.get_concept_count.return_value = 10

        selected, covered, total = await diagnostic_service.select_diagnostic_questions(
            course_id=uuid4(),
            target_count=12,
        )

        # Q1 should be selected first due to most concept coverage
        assert q1 in selected
        # All 3 concepts from Q1 should be covered
        assert concept1 in covered
        assert concept2 in covered
        assert concept3 in covered

    @pytest.mark.asyncio
    async def test_avoids_redundant_coverage(
        self, diagnostic_service, mock_question_repo, mock_concept_repo
    ):
        """Verify algorithm prefers new concepts over already-covered ones."""
        concept1, concept2, concept3 = uuid4(), uuid4(), uuid4()

        # Q1 covers concept 1
        # Q2 covers concept 1 (same as Q1 - redundant)
        # Q3 covers concept 2 (new concept)
        q1 = create_mock_question(
            knowledge_area_id="ka1",
            discrimination=1.0,
            concept_ids=[concept1],
        )
        q2 = create_mock_question(
            knowledge_area_id="ka2",
            discrimination=1.5,  # Higher discrimination but redundant
            concept_ids=[concept1],
        )
        q3 = create_mock_question(
            knowledge_area_id="ka3",
            discrimination=1.0,
            concept_ids=[concept2],
        )

        mock_question_repo.get_questions_with_concepts.return_value = [q1, q2, q3]
        mock_concept_repo.get_concept_count.return_value = 10

        selected, covered, _ = await diagnostic_service.select_diagnostic_questions(
            course_id=uuid4(),
            target_count=12,
        )

        # Both Q1 and Q3 should be selected (covering different concepts)
        # Q2 should only be selected if we need more questions
        assert concept1 in covered
        assert concept2 in covered


# ============================================================================
# KA Balance Tests
# ============================================================================

class TestKABalance:
    """Test that max 4 questions per KA constraint is enforced."""

    @pytest.mark.asyncio
    async def test_max_four_per_ka(
        self, diagnostic_service, mock_question_repo, mock_concept_repo
    ):
        """Verify no more than 4 questions selected from same KA."""
        # Create 6 questions all from same KA
        questions = [
            create_mock_question(
                knowledge_area_id="same-ka",
                concept_ids=[uuid4()],  # Each covers unique concept
            )
            for _ in range(6)
        ]

        # Add 8 more from different KAs to allow selection to continue
        for i in range(8):
            questions.append(
                create_mock_question(
                    knowledge_area_id=f"other-ka-{i}",
                    concept_ids=[uuid4()],
                )
            )

        mock_question_repo.get_questions_with_concepts.return_value = questions
        mock_concept_repo.get_concept_count.return_value = 100

        selected, _, _ = await diagnostic_service.select_diagnostic_questions(
            course_id=uuid4(),
            target_count=15,
        )

        # Count questions per KA
        ka_counts = defaultdict(int)
        for q in selected:
            ka_counts[q.knowledge_area_id] += 1

        # No KA should have more than 4 questions
        assert ka_counts["same-ka"] <= 4

    @pytest.mark.asyncio
    async def test_balances_across_kas(
        self, diagnostic_service, mock_question_repo, mock_concept_repo
    ):
        """Verify algorithm balances questions across KAs."""
        # Create 5 questions each from 4 different KAs
        kas = ["ka1", "ka2", "ka3", "ka4"]
        questions = []
        for ka in kas:
            for i in range(5):
                questions.append(
                    create_mock_question(
                        knowledge_area_id=ka,
                        concept_ids=[uuid4()],
                    )
                )

        mock_question_repo.get_questions_with_concepts.return_value = questions
        mock_concept_repo.get_concept_count.return_value = 100

        selected, _, _ = await diagnostic_service.select_diagnostic_questions(
            course_id=uuid4(),
            target_count=16,  # 4 per KA * 4 KAs
        )

        # Count questions per KA
        ka_counts = defaultdict(int)
        for q in selected:
            ka_counts[q.knowledge_area_id] += 1

        # Should be balanced (each KA gets 4)
        for ka in kas:
            assert ka_counts[ka] == 4


# ============================================================================
# Discrimination Preference Tests
# ============================================================================

class TestDiscriminationPreference:
    """Test that higher discrimination questions are preferred."""

    @pytest.mark.asyncio
    async def test_prefers_high_discrimination(
        self, diagnostic_service, mock_question_repo, mock_concept_repo
    ):
        """Verify higher discrimination questions score better."""
        concept1 = uuid4()

        # Both cover same concept, but Q1 has higher discrimination
        q1_high = create_mock_question(
            knowledge_area_id="ka1",
            discrimination=2.0,  # High discrimination
            concept_ids=[concept1],
        )
        q2_low = create_mock_question(
            knowledge_area_id="ka2",
            discrimination=0.5,  # Low discrimination
            concept_ids=[concept1],
        )

        mock_question_repo.get_questions_with_concepts.return_value = [q2_low, q1_high]
        mock_concept_repo.get_concept_count.return_value = 10

        selected, _, _ = await diagnostic_service.select_diagnostic_questions(
            course_id=uuid4(),
            target_count=12,
        )

        # High discrimination question should be selected first
        # (it should be earlier in selection order before shuffle)
        assert q1_high in selected

    def test_score_calculation_includes_discrimination(self, diagnostic_service):
        """Verify discrimination contributes to score calculation."""
        concept1 = uuid4()
        covered = set()
        ka_counts = defaultdict(int)

        q_high = create_mock_question(discrimination=2.0, concept_ids=[concept1])
        q_low = create_mock_question(discrimination=0.5, concept_ids=[concept1])

        qwc_high = QuestionWithConcepts(question=q_high, concept_ids={concept1})
        qwc_low = QuestionWithConcepts(question=q_low, concept_ids={concept1})

        score_high = diagnostic_service._calculate_score(qwc_high, covered, ka_counts)
        score_low = diagnostic_service._calculate_score(qwc_low, covered, ka_counts)

        # Higher discrimination should have higher score
        assert score_high > score_low


# ============================================================================
# Randomization Tests
# ============================================================================

class TestRandomization:
    """Test that output order is randomized."""

    @pytest.mark.asyncio
    async def test_output_is_shuffled(
        self, diagnostic_service, mock_question_repo, mock_concept_repo
    ):
        """Verify output questions are not in deterministic order."""
        # Create many questions
        questions = [
            create_mock_question(
                knowledge_area_id=f"ka{i % 5}",
                concept_ids=[uuid4()],
            )
            for i in range(20)
        ]

        mock_question_repo.get_questions_with_concepts.return_value = questions
        mock_concept_repo.get_concept_count.return_value = 100

        # Run multiple times and check if orders differ
        orders = []
        for _ in range(5):
            selected, _, _ = await diagnostic_service.select_diagnostic_questions(
                course_id=uuid4(),
                target_count=15,
            )
            orders.append([q.id for q in selected])

        # At least some orders should be different (randomized)
        # Note: There's a tiny chance all 5 could be same, but extremely unlikely
        unique_orders = set(tuple(o) for o in orders)
        assert len(unique_orders) > 1, "Output should be randomized"


# ============================================================================
# Edge Case Tests
# ============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_fewer_questions_than_target(
        self, diagnostic_service, mock_question_repo, mock_concept_repo
    ):
        """Verify handles case with fewer questions than target count."""
        # Only 5 questions available, spread across KAs to avoid KA limit
        questions = [
            create_mock_question(
                knowledge_area_id=f"ka{i}",  # Different KAs
                concept_ids=[uuid4()],
            )
            for i in range(5)
        ]

        mock_question_repo.get_questions_with_concepts.return_value = questions
        mock_concept_repo.get_concept_count.return_value = 10

        selected, _, _ = await diagnostic_service.select_diagnostic_questions(
            course_id=uuid4(),
            target_count=15,
        )

        # Should select all available questions
        assert len(selected) == 5

    @pytest.mark.asyncio
    async def test_single_ka_questions(
        self, diagnostic_service, mock_question_repo, mock_concept_repo
    ):
        """Verify handles case where all questions from single KA."""
        # All 10 questions from same KA
        questions = [
            create_mock_question(
                knowledge_area_id="single-ka",
                concept_ids=[uuid4()],
            )
            for _ in range(10)
        ]

        mock_question_repo.get_questions_with_concepts.return_value = questions
        mock_concept_repo.get_concept_count.return_value = 100

        selected, _, _ = await diagnostic_service.select_diagnostic_questions(
            course_id=uuid4(),
            target_count=15,
        )

        # Should only select 4 (max per KA)
        assert len(selected) == 4

    @pytest.mark.asyncio
    async def test_questions_with_no_concepts(
        self, diagnostic_service, mock_question_repo, mock_concept_repo
    ):
        """Verify handles questions without concept mappings."""
        # Mix of questions with and without concepts
        q_with_concepts = create_mock_question(
            knowledge_area_id="ka1",
            concept_ids=[uuid4(), uuid4()],
        )
        q_no_concepts = create_mock_question(
            knowledge_area_id="ka2",
            concept_ids=[],  # No concepts
        )

        mock_question_repo.get_questions_with_concepts.return_value = [
            q_with_concepts,
            q_no_concepts,
        ]
        mock_concept_repo.get_concept_count.return_value = 10

        selected, covered, _ = await diagnostic_service.select_diagnostic_questions(
            course_id=uuid4(),
            target_count=12,
        )

        # Should still select both (no error)
        assert len(selected) == 2
        # Only concepts from q_with_concepts should be in covered
        assert len(covered) == 2

    @pytest.mark.asyncio
    async def test_empty_question_pool(
        self, diagnostic_service, mock_question_repo, mock_concept_repo
    ):
        """Verify handles empty question pool gracefully."""
        mock_question_repo.get_questions_with_concepts.return_value = []
        mock_concept_repo.get_concept_count.return_value = 100

        selected, covered, total = await diagnostic_service.select_diagnostic_questions(
            course_id=uuid4(),
            target_count=15,
        )

        assert selected == []
        assert covered == set()
        assert total == 100

    @pytest.mark.asyncio
    async def test_target_count_clamped_to_valid_range(
        self, diagnostic_service, mock_question_repo, mock_concept_repo
    ):
        """Verify target_count is clamped to valid range (12-20)."""
        questions = [
            create_mock_question(
                knowledge_area_id=f"ka{i % 5}",
                concept_ids=[uuid4()],
            )
            for i in range(25)
        ]

        mock_question_repo.get_questions_with_concepts.return_value = questions
        mock_concept_repo.get_concept_count.return_value = 100

        # Test with target too low
        selected, _, _ = await diagnostic_service.select_diagnostic_questions(
            course_id=uuid4(),
            target_count=5,  # Below minimum
        )
        assert len(selected) == 12  # Clamped to minimum

        # Test with target too high
        selected, _, _ = await diagnostic_service.select_diagnostic_questions(
            course_id=uuid4(),
            target_count=50,  # Above maximum
        )
        assert len(selected) == 20  # Clamped to maximum


# ============================================================================
# Score Calculation Tests
# ============================================================================

class TestScoreCalculation:
    """Test the scoring function directly."""

    def test_coverage_weight(self, diagnostic_service):
        """Verify coverage component contributes correctly to score."""
        concept1, concept2 = uuid4(), uuid4()
        covered = set()
        ka_counts = defaultdict(int)

        # Question covering 2 concepts vs 1 concept
        q_two = create_mock_question(concept_ids=[concept1, concept2])
        q_one = create_mock_question(concept_ids=[concept1])

        qwc_two = QuestionWithConcepts(question=q_two, concept_ids={concept1, concept2})
        qwc_one = QuestionWithConcepts(question=q_one, concept_ids={concept1})

        score_two = diagnostic_service._calculate_score(qwc_two, covered, ka_counts)
        score_one = diagnostic_service._calculate_score(qwc_one, covered, ka_counts)

        # Two concepts should have 10 points more (WEIGHT_COVERAGE = 10)
        assert score_two - score_one == 10

    def test_ka_balance_weight(self, diagnostic_service):
        """Verify KA balance component contributes correctly to score."""
        concept1 = uuid4()
        covered = set()

        q1 = create_mock_question(knowledge_area_id="ka-full", concept_ids=[concept1])
        q2 = create_mock_question(knowledge_area_id="ka-empty", concept_ids=[concept1])

        qwc1 = QuestionWithConcepts(question=q1, concept_ids={concept1})
        qwc2 = QuestionWithConcepts(question=q2, concept_ids={concept1})

        # ka-full already has 3 questions
        ka_counts = {"ka-full": 3, "ka-empty": 0}

        score_full = diagnostic_service._calculate_score(qwc1, covered, ka_counts)
        score_empty = diagnostic_service._calculate_score(qwc2, covered, ka_counts)

        # ka-empty should score higher due to balance bonus
        assert score_empty > score_full
