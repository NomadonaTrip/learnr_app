"""
Unit tests for ReadingQueueService.
Story 5.5: Background Reading Queue Population

Tests:
- Priority calculation based on competency and correctness
- Chunks to add determination based on answer type
- Semantic search query composition
- KA competency calculation
"""
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.schemas.reading_queue import ReadingPriority
from src.services.reading_queue_service import ReadingQueueService


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_session():
    """Create mock AsyncSession."""
    session = AsyncMock()
    return session


@pytest.fixture
def reading_queue_service(mock_session):
    """Create ReadingQueueService with mock session."""
    return ReadingQueueService(mock_session)


def create_mock_question(
    question_id=None,
    knowledge_area_id="BA",
    difficulty=0.0,
    question_text="What is stakeholder analysis?",
    concept_names=None,
):
    """Helper to create mock Question with concepts."""
    question = MagicMock()
    question.id = question_id or uuid4()
    question.knowledge_area_id = knowledge_area_id
    question.difficulty = difficulty
    question.question_text = question_text

    # Mock question_concepts relationship
    question.question_concepts = []
    if concept_names:
        for i, name in enumerate(concept_names):
            qc = MagicMock()
            qc.concept = MagicMock()
            qc.concept.id = uuid4()
            qc.concept.name = name
            qc.relevance = 1.0 - (i * 0.1)  # First concept has highest relevance
            question.question_concepts.append(qc)

    return question


def create_mock_enrollment(enrollment_id=None, course_id=None):
    """Helper to create mock Enrollment."""
    enrollment = MagicMock()
    enrollment.id = enrollment_id or uuid4()
    enrollment.course_id = course_id or uuid4()
    return enrollment


# ============================================================================
# Priority Calculation Tests (AC 7)
# ============================================================================


class TestCalculateReadingPriority:
    """Tests for _calculate_reading_priority method."""

    def test_high_priority_incorrect_low_competency(self, reading_queue_service):
        """Test: Competency < 0.6 AND incorrect → High priority."""
        priority = reading_queue_service._calculate_reading_priority(
            ka_competency=0.45,  # Below 0.6
            is_correct=False,
            difficulty=0.5,
        )
        assert priority == ReadingPriority.HIGH

    def test_high_priority_at_threshold(self, reading_queue_service):
        """Test: Competency at 0.59 AND incorrect → High priority."""
        priority = reading_queue_service._calculate_reading_priority(
            ka_competency=0.59,
            is_correct=False,
            difficulty=0.0,
        )
        assert priority == ReadingPriority.HIGH

    def test_medium_priority_mid_competency_incorrect(self, reading_queue_service):
        """Test: Competency 0.6-0.8 AND incorrect → Medium priority."""
        priority = reading_queue_service._calculate_reading_priority(
            ka_competency=0.65,
            is_correct=False,
            difficulty=0.0,
        )
        assert priority == ReadingPriority.MEDIUM

    def test_medium_priority_correct_hard_question(self, reading_queue_service):
        """Test: Correct on hard question (difficulty >= 0.7) → Medium priority."""
        priority = reading_queue_service._calculate_reading_priority(
            ka_competency=0.85,  # High competency
            is_correct=True,
            difficulty=0.8,  # Hard question (IRT scale)
        )
        assert priority == ReadingPriority.MEDIUM

    def test_low_priority_high_competency_correct(self, reading_queue_service):
        """Test: Competency >= 0.8 AND correct → Low priority."""
        priority = reading_queue_service._calculate_reading_priority(
            ka_competency=0.85,
            is_correct=True,
            difficulty=0.3,  # Easy/medium question
        )
        assert priority == ReadingPriority.LOW

    def test_low_priority_at_threshold(self, reading_queue_service):
        """Test: Competency at exactly 0.8 AND correct → Low priority."""
        priority = reading_queue_service._calculate_reading_priority(
            ka_competency=0.80,
            is_correct=True,
            difficulty=0.0,
        )
        assert priority == ReadingPriority.LOW


# ============================================================================
# Chunks to Add Determination Tests (AC 2, 3, 4)
# ============================================================================


class TestDetermineChunksToAdd:
    """Tests for _determine_chunks_to_add method."""

    def test_incorrect_answer_adds_chunks(self, reading_queue_service):
        """Test: Incorrect answer adds 3 chunks (default)."""
        chunks = reading_queue_service._determine_chunks_to_add(
            is_correct=False,
            difficulty=0.0,
        )
        assert chunks == 3  # Default READING_CHUNKS_INCORRECT

    def test_correct_easy_skips(self, reading_queue_service):
        """Test: Correct on easy question adds 0 chunks."""
        chunks = reading_queue_service._determine_chunks_to_add(
            is_correct=True,
            difficulty=0.3,  # Easy question
        )
        assert chunks == 0

    def test_correct_medium_skips(self, reading_queue_service):
        """Test: Correct on medium question adds 0 chunks."""
        chunks = reading_queue_service._determine_chunks_to_add(
            is_correct=True,
            difficulty=0.5,  # Medium difficulty
        )
        assert chunks == 0

    def test_correct_hard_adds_chunks(self, reading_queue_service):
        """Test: Correct on hard question adds 1 chunk (reinforcement)."""
        chunks = reading_queue_service._determine_chunks_to_add(
            is_correct=True,
            difficulty=0.8,  # Hard question (>= 0.7 threshold)
        )
        assert chunks == 1  # Default READING_CHUNKS_HARD_CORRECT

    def test_correct_at_hard_threshold(self, reading_queue_service):
        """Test: Correct at exactly difficulty=0.7 adds 1 chunk."""
        chunks = reading_queue_service._determine_chunks_to_add(
            is_correct=True,
            difficulty=0.7,  # At threshold
        )
        assert chunks == 1


# ============================================================================
# Search Query Composition Tests (AC 5)
# ============================================================================


class TestBuildSearchQuery:
    """Tests for _build_search_query method."""

    def test_query_from_concept_names(self, reading_queue_service):
        """Test: Builds query from concept names."""
        question = create_mock_question(
            concept_names=["Stakeholder Analysis", "Requirements Elicitation"]
        )

        query = reading_queue_service._build_search_query(question)

        assert "Stakeholder Analysis" in query
        assert "Requirements Elicitation" in query

    def test_query_fallback_to_question_text(self, reading_queue_service):
        """Test: Falls back to question text if no concepts."""
        question = create_mock_question(
            concept_names=None,
            question_text="What is the purpose of stakeholder mapping?",
        )

        query = reading_queue_service._build_search_query(question)

        assert "stakeholder mapping" in query

    def test_query_truncation_for_long_text(self, reading_queue_service):
        """Test: Truncates long question text fallback."""
        long_text = "A" * 1000
        question = create_mock_question(
            concept_names=None,
            question_text=long_text,
        )

        query = reading_queue_service._build_search_query(question)

        assert len(query) <= 500


# ============================================================================
# Primary Concept ID Tests
# ============================================================================


class TestGetPrimaryConcept:
    """Tests for _get_primary_concept_id method."""

    def test_returns_highest_relevance_concept(self, reading_queue_service):
        """Test: Returns concept with highest relevance."""
        question = create_mock_question(
            concept_names=["Primary Concept", "Secondary Concept"]
        )
        # First concept has highest relevance by default in our helper

        concept_id = reading_queue_service._get_primary_concept_id(question)

        # Should return the first concept (highest relevance)
        assert concept_id == question.question_concepts[0].concept.id

    def test_returns_none_for_no_concepts(self, reading_queue_service):
        """Test: Returns None if no concepts."""
        question = create_mock_question(concept_names=None)

        concept_id = reading_queue_service._get_primary_concept_id(question)

        assert concept_id is None


# ============================================================================
# KA Competency Calculation Tests (AC 7)
# ============================================================================


class TestGetKACompetency:
    """Tests for _get_ka_competency method."""

    @pytest.mark.asyncio
    async def test_calculates_average_mastery(self, reading_queue_service, mock_session):
        """Test: Calculates average mastery from belief states."""
        # Mock the database result
        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row.avg_mastery = 0.75
        mock_result.fetchone.return_value = mock_row
        mock_session.execute.return_value = mock_result

        competency = await reading_queue_service._get_ka_competency(
            user_id=uuid4(),
            knowledge_area_id="BA",
        )

        assert competency == 0.75

    @pytest.mark.asyncio
    async def test_returns_default_for_no_data(self, reading_queue_service, mock_session):
        """Test: Returns 0.5 (uninformative prior) if no belief data."""
        # Mock empty database result
        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row.avg_mastery = None
        mock_result.fetchone.return_value = mock_row
        mock_session.execute.return_value = mock_result

        competency = await reading_queue_service._get_ka_competency(
            user_id=uuid4(),
            knowledge_area_id="BA",
        )

        assert competency == 0.5

    @pytest.mark.asyncio
    async def test_returns_default_for_no_row(self, reading_queue_service, mock_session):
        """Test: Returns 0.5 if no row returned."""
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        mock_session.execute.return_value = mock_result

        competency = await reading_queue_service._get_ka_competency(
            user_id=uuid4(),
            knowledge_area_id="BA",
        )

        assert competency == 0.5


# ============================================================================
# Full Integration Flow Tests (Mocked)
# ============================================================================


class TestPopulateReadingQueue:
    """Tests for populate_reading_queue method with mocked dependencies."""

    @pytest.mark.asyncio
    async def test_skips_for_correct_easy_answer(
        self, reading_queue_service, mock_session
    ):
        """Test: Skips queue population for correct easy answers (AC 4)."""
        # Mock question with concepts
        question = create_mock_question(
            concept_names=["Test Concept"],
            difficulty=0.3,  # Easy
        )

        # Mock the internal methods
        reading_queue_service._get_question_with_concepts = AsyncMock(
            return_value=question
        )
        reading_queue_service._get_enrollment = AsyncMock(
            return_value=create_mock_enrollment()
        )

        result = await reading_queue_service.populate_reading_queue(
            user_id=uuid4(),
            enrollment_id=uuid4(),
            question_id=uuid4(),
            session_id=uuid4(),
            is_correct=True,  # Correct answer
            difficulty=0.3,  # Easy question
        )

        assert result == 0

    @pytest.mark.asyncio
    async def test_returns_zero_for_missing_question(
        self, reading_queue_service, mock_session
    ):
        """Test: Returns 0 if question not found."""
        reading_queue_service._get_question_with_concepts = AsyncMock(return_value=None)

        result = await reading_queue_service.populate_reading_queue(
            user_id=uuid4(),
            enrollment_id=uuid4(),
            question_id=uuid4(),
            session_id=uuid4(),
            is_correct=False,
            difficulty=0.5,
        )

        assert result == 0

    @pytest.mark.asyncio
    async def test_returns_zero_for_missing_enrollment(
        self, reading_queue_service, mock_session
    ):
        """Test: Returns 0 if enrollment not found."""
        question = create_mock_question(concept_names=["Test"])
        reading_queue_service._get_question_with_concepts = AsyncMock(
            return_value=question
        )
        reading_queue_service._get_enrollment = AsyncMock(return_value=None)

        result = await reading_queue_service.populate_reading_queue(
            user_id=uuid4(),
            enrollment_id=uuid4(),
            question_id=uuid4(),
            session_id=uuid4(),
            is_correct=False,
            difficulty=0.5,
        )

        assert result == 0
