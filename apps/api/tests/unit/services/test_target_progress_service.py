"""
Unit tests for TargetProgressService.
Tests calculation of target progress metrics for focused sessions.
"""
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.services.target_progress_service import TargetProgressService


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_db():
    """Create mock database session."""
    db = AsyncMock()
    return db


@pytest.fixture
def target_progress_service(mock_db):
    """Create TargetProgressService with mock database."""
    return TargetProgressService(db=mock_db)


def create_mock_session(
    session_type: str = "adaptive",
    knowledge_area_filter: str | None = None,
    target_concept_ids: list[str] | None = None,
    enrollment_id: str | None = None,
):
    """Helper to create a mock QuizSession."""
    session = MagicMock()
    session.id = uuid4()
    session.session_type = session_type
    session.knowledge_area_filter = knowledge_area_filter
    session.target_concept_ids = target_concept_ids
    session.enrollment_id = enrollment_id or uuid4()
    return session


# ============================================================================
# Test: calculate_target_progress
# ============================================================================


class TestCalculateTargetProgress:
    """Tests for calculate_target_progress method."""

    @pytest.mark.asyncio
    async def test_returns_none_for_adaptive_session(
        self, target_progress_service, mock_db
    ):
        """Should return None for adaptive sessions."""
        session = create_mock_session(session_type="adaptive")
        user_id = uuid4()

        result = await target_progress_service.calculate_target_progress(
            session=session, user_id=user_id
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_for_fixed_length_session(
        self, target_progress_service, mock_db
    ):
        """Should return None for fixed_length sessions."""
        session = create_mock_session(session_type="fixed_length")
        user_id = uuid4()

        result = await target_progress_service.calculate_target_progress(
            session=session, user_id=user_id
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_for_diagnostic_session(
        self, target_progress_service, mock_db
    ):
        """Should return None for diagnostic sessions."""
        session = create_mock_session(session_type="diagnostic")
        user_id = uuid4()

        result = await target_progress_service.calculate_target_progress(
            session=session, user_id=user_id
        )

        assert result is None


class TestFocusedKAProgress:
    """Tests for focused_ka session progress calculation."""

    @pytest.mark.asyncio
    async def test_returns_ka_progress(self, target_progress_service, mock_db):
        """Should return progress for focused_ka session."""
        ka_id = "elicitation"
        session = create_mock_session(
            session_type="focused_ka", knowledge_area_filter=ka_id
        )
        user_id = uuid4()
        concept_id = uuid4()

        # Mock course lookup (for KA name)
        course_result = MagicMock()
        course_result.scalar_one_or_none.return_value = MagicMock(
            knowledge_areas=[{"id": ka_id, "name": "Elicitation"}]
        )

        # Mock concept lookup
        concept_result = MagicMock()
        concept_result.all.return_value = [(concept_id,)]

        # Mock belief state lookup
        belief_result = MagicMock()
        belief_result.all.return_value = [(3.0, 1.0)]  # 75% mastery

        # Mock response lookup (no responses)
        response_result = MagicMock()
        response_result.all.return_value = []

        mock_db.execute.side_effect = [
            course_result,
            concept_result,
            belief_result,
            response_result,
        ]

        result = await target_progress_service.calculate_target_progress(
            session=session, user_id=user_id
        )

        assert result is not None
        assert result.focus_type == "ka"
        assert result.target_name == "Elicitation"
        assert result.current_mastery == 0.75
        assert result.session_improvement == 0.0
        assert result.questions_in_focus_count == 0

    @pytest.mark.asyncio
    async def test_returns_none_when_no_ka_filter(
        self, target_progress_service, mock_db
    ):
        """Should return None if focused_ka session has no knowledge_area_filter."""
        session = create_mock_session(
            session_type="focused_ka", knowledge_area_filter=None
        )
        user_id = uuid4()

        result = await target_progress_service.calculate_target_progress(
            session=session, user_id=user_id
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_default_mastery_when_no_concepts(
        self, target_progress_service, mock_db
    ):
        """Should return default mastery when KA has no concepts."""
        ka_id = "empty_ka"
        session = create_mock_session(
            session_type="focused_ka", knowledge_area_filter=ka_id
        )
        user_id = uuid4()

        # Mock course lookup
        course_result = MagicMock()
        course_result.scalar_one_or_none.return_value = MagicMock(
            knowledge_areas=[{"id": ka_id, "name": "Empty KA"}]
        )

        # Mock concept lookup (empty)
        concept_result = MagicMock()
        concept_result.all.return_value = []

        mock_db.execute.side_effect = [course_result, concept_result]

        result = await target_progress_service.calculate_target_progress(
            session=session, user_id=user_id
        )

        assert result is not None
        assert result.focus_type == "ka"
        assert result.target_name == "Empty KA"
        assert result.current_mastery == 0.5  # Default
        assert result.session_improvement == 0.0
        assert result.questions_in_focus_count == 0


class TestFocusedConceptProgress:
    """Tests for focused_concept session progress calculation."""

    @pytest.mark.asyncio
    async def test_returns_single_concept_progress(
        self, target_progress_service, mock_db
    ):
        """Should return progress for single-concept focused session."""
        concept_id = uuid4()
        session = create_mock_session(
            session_type="focused_concept",
            target_concept_ids=[str(concept_id)],
        )
        user_id = uuid4()

        # Mock concept name lookup
        concept_result = MagicMock()
        concept_result.all.return_value = [(concept_id, "Test Concept")]

        # Mock belief state lookup
        belief_result = MagicMock()
        belief_result.all.return_value = [(4.0, 1.0)]  # 80% mastery

        # Mock response lookup
        response_result = MagicMock()
        response_result.all.return_value = []

        mock_db.execute.side_effect = [
            concept_result,
            belief_result,
            response_result,
        ]

        result = await target_progress_service.calculate_target_progress(
            session=session, user_id=user_id
        )

        assert result is not None
        assert result.focus_type == "concept"
        assert result.target_name == "Test Concept"
        assert result.current_mastery == 0.8
        assert result.session_improvement == 0.0
        assert result.questions_in_focus_count == 0

    @pytest.mark.asyncio
    async def test_returns_multiple_concepts_progress(
        self, target_progress_service, mock_db
    ):
        """Should return progress for multi-concept focused session."""
        concept_id1 = uuid4()
        concept_id2 = uuid4()
        concept_id3 = uuid4()
        session = create_mock_session(
            session_type="focused_concept",
            target_concept_ids=[str(concept_id1), str(concept_id2), str(concept_id3)],
        )
        user_id = uuid4()

        # Mock concept name lookup
        concept_result = MagicMock()
        concept_result.all.return_value = [
            (concept_id1, "Concept 1"),
            (concept_id2, "Concept 2"),
            (concept_id3, "Concept 3"),
        ]

        # Mock belief state lookup (average: (0.75 + 0.5 + 0.8) / 3 = 0.683...)
        belief_result = MagicMock()
        belief_result.all.return_value = [
            (3.0, 1.0),  # 75%
            (1.0, 1.0),  # 50%
            (4.0, 1.0),  # 80%
        ]

        # Mock response lookup
        response_result = MagicMock()
        response_result.all.return_value = []

        mock_db.execute.side_effect = [
            concept_result,
            belief_result,
            response_result,
        ]

        result = await target_progress_service.calculate_target_progress(
            session=session, user_id=user_id
        )

        assert result is not None
        assert result.focus_type == "concept"
        assert result.target_name == "3 concepts"
        assert 0.68 <= result.current_mastery <= 0.69

    @pytest.mark.asyncio
    async def test_returns_none_when_no_target_concepts(
        self, target_progress_service, mock_db
    ):
        """Should return None if focused_concept session has no target_concept_ids."""
        session = create_mock_session(
            session_type="focused_concept", target_concept_ids=None
        )
        user_id = uuid4()

        result = await target_progress_service.calculate_target_progress(
            session=session, user_id=user_id
        )

        assert result is None


class TestSessionMetricsCalculation:
    """Tests for session improvement and question count calculation."""

    @pytest.mark.asyncio
    async def test_calculates_improvement_from_responses(
        self, target_progress_service, mock_db
    ):
        """Should calculate improvement from belief_updates in responses."""
        concept_id = uuid4()
        session = create_mock_session(
            session_type="focused_concept",
            target_concept_ids=[str(concept_id)],
        )
        user_id = uuid4()

        # Mock concept name lookup
        concept_result = MagicMock()
        concept_result.all.return_value = [(concept_id, "Test Concept")]

        # Mock belief state lookup (current state: 80%)
        belief_result = MagicMock()
        belief_result.all.return_value = [(4.0, 1.0)]

        # Mock response lookup with belief updates
        # Question 1: Improved from 50% to 66.67% (delta = +0.1667)
        # Question 2: Improved from 66.67% to 75% (delta = +0.0833)
        response_result = MagicMock()
        response_result.all.return_value = [
            (
                [
                    {
                        "concept_id": str(concept_id),
                        "old_alpha": 1.0,
                        "old_beta": 1.0,
                        "new_alpha": 2.0,
                        "new_beta": 1.0,
                    }
                ],
                uuid4(),
            ),
            (
                [
                    {
                        "concept_id": str(concept_id),
                        "old_alpha": 2.0,
                        "old_beta": 1.0,
                        "new_alpha": 3.0,
                        "new_beta": 1.0,
                    }
                ],
                uuid4(),
            ),
        ]

        mock_db.execute.side_effect = [
            concept_result,
            belief_result,
            response_result,
        ]

        result = await target_progress_service.calculate_target_progress(
            session=session, user_id=user_id
        )

        assert result is not None
        assert result.questions_in_focus_count == 2
        # Improvement: (2/3 - 1/2) + (3/4 - 2/3) = 0.1667 + 0.0833 = 0.25
        assert 0.24 <= result.session_improvement <= 0.26

    @pytest.mark.asyncio
    async def test_ignores_non_target_concept_updates(
        self, target_progress_service, mock_db
    ):
        """Should only count updates for target concepts."""
        target_concept = uuid4()
        other_concept = uuid4()
        session = create_mock_session(
            session_type="focused_concept",
            target_concept_ids=[str(target_concept)],
        )
        user_id = uuid4()

        # Mock concept name lookup
        concept_result = MagicMock()
        concept_result.all.return_value = [(target_concept, "Target Concept")]

        # Mock belief state lookup
        belief_result = MagicMock()
        belief_result.all.return_value = [(2.0, 1.0)]

        # Mock response: question tested both target and other concept
        response_result = MagicMock()
        response_result.all.return_value = [
            (
                [
                    {
                        "concept_id": str(target_concept),
                        "old_alpha": 1.0,
                        "old_beta": 1.0,
                        "new_alpha": 2.0,
                        "new_beta": 1.0,
                    },
                    {
                        "concept_id": str(other_concept),
                        "old_alpha": 1.0,
                        "old_beta": 1.0,
                        "new_alpha": 3.0,
                        "new_beta": 1.0,
                    },
                ],
                uuid4(),
            ),
        ]

        mock_db.execute.side_effect = [
            concept_result,
            belief_result,
            response_result,
        ]

        result = await target_progress_service.calculate_target_progress(
            session=session, user_id=user_id
        )

        assert result is not None
        assert result.questions_in_focus_count == 1
        # Only target concept improvement counted: 2/3 - 1/2 = 0.1667
        assert 0.16 <= result.session_improvement <= 0.17

    @pytest.mark.asyncio
    async def test_default_mastery_when_no_beliefs(
        self, target_progress_service, mock_db
    ):
        """Should return default mastery when no belief states exist."""
        concept_id = uuid4()
        session = create_mock_session(
            session_type="focused_concept",
            target_concept_ids=[str(concept_id)],
        )
        user_id = uuid4()

        # Mock concept name lookup
        concept_result = MagicMock()
        concept_result.all.return_value = [(concept_id, "New Concept")]

        # Mock belief state lookup (empty - no beliefs yet)
        belief_result = MagicMock()
        belief_result.all.return_value = []

        # Mock response lookup
        response_result = MagicMock()
        response_result.all.return_value = []

        mock_db.execute.side_effect = [
            concept_result,
            belief_result,
            response_result,
        ]

        result = await target_progress_service.calculate_target_progress(
            session=session, user_id=user_id
        )

        assert result is not None
        assert result.current_mastery == 0.5  # Default when no beliefs
