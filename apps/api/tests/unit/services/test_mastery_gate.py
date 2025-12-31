"""
Unit tests for MasteryGateService (Story 4.11).

Tests prerequisite-based mastery gates:
- Gate checking logic (_meets_mastery_gate)
- Progress calculation
- Bulk unlock status
- Question estimates
"""
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from src.schemas.mastery_gate import (
    BlockingPrerequisite,
    GateCheckResult,
    MasteryGateConfig,
)
from src.services.mastery_gate import MasteryGateService


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_session():
    """Create a mock async session."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    return session


@pytest.fixture
def mock_belief_repo():
    """Create a mock belief repository."""
    repo = AsyncMock()
    repo.get_beliefs_as_dict = AsyncMock(return_value={})
    return repo


@pytest.fixture
def mock_concept_repo():
    """Create a mock concept repository."""
    repo = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.get_prerequisites_with_strength = AsyncMock(return_value=[])
    repo.get_all_prerequisites_for_course = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def mastery_gate_service(mock_session, mock_belief_repo, mock_concept_repo):
    """Create MasteryGateService with mocked dependencies."""
    return MasteryGateService(
        session=mock_session,
        belief_repository=mock_belief_repo,
        concept_repository=mock_concept_repo,
    )


@pytest.fixture
def mock_belief_state():
    """Create a mock belief state."""
    def create_belief(
        concept_id: UUID,
        alpha: float = 2.0,
        beta: float = 2.0,
        response_count: int = 5,
    ):
        belief = MagicMock()
        belief.concept_id = concept_id
        belief.alpha = alpha
        belief.beta = beta
        belief.response_count = response_count
        belief.mean = alpha / (alpha + beta)
        belief.confidence = (alpha + beta) / (alpha + beta + 2)
        return belief
    return create_belief


@pytest.fixture
def mock_concept():
    """Create a mock concept."""
    def create_concept(
        concept_id: UUID | None = None,
        name: str = "Test Concept",
        ka_id: str = "KA1",
    ):
        concept = MagicMock()
        concept.id = concept_id or uuid4()
        concept.name = name
        concept.knowledge_area_id = ka_id
        return concept
    return create_concept


# ============================================================================
# Test: _meets_mastery_gate
# ============================================================================


class TestMeetsGate:
    """Tests for _meets_mastery_gate method."""

    def test_mastered_belief_meets_gate(self, mastery_gate_service, mock_belief_state):
        """High mastery, high confidence, sufficient responses = gate met."""
        belief = mock_belief_state(
            uuid4(),
            alpha=8.0,  # mean = 0.8
            beta=2.0,
            response_count=5,
        )
        assert mastery_gate_service._meets_mastery_gate(belief) is True

    def test_low_mastery_fails_gate(self, mastery_gate_service, mock_belief_state):
        """Low mastery fails gate even with high confidence."""
        belief = mock_belief_state(
            uuid4(),
            alpha=2.0,  # mean = 0.4
            beta=3.0,
            response_count=5,
        )
        assert mastery_gate_service._meets_mastery_gate(belief) is False

    def test_low_confidence_fails_gate(self, mastery_gate_service, mock_belief_state):
        """Low confidence fails gate even with high mastery."""
        belief = mock_belief_state(
            uuid4(),
            alpha=7.0,  # mean = 0.7
            beta=3.0,
            response_count=5,
        )
        # confidence = 10/12 = 0.83, high enough
        # But with low alpha/beta:
        low_conf_belief = mock_belief_state(
            uuid4(),
            alpha=1.4,  # mean = 0.7
            beta=0.6,
            response_count=5,
        )
        # confidence = 2/4 = 0.5, below 0.6 threshold
        assert mastery_gate_service._meets_mastery_gate(low_conf_belief) is False

    def test_insufficient_responses_fails_gate(
        self, mastery_gate_service, mock_belief_state
    ):
        """Insufficient responses fail gate even with high mastery."""
        belief = mock_belief_state(
            uuid4(),
            alpha=8.0,  # mean = 0.8
            beta=2.0,
            response_count=2,  # Below min of 3
        )
        assert mastery_gate_service._meets_mastery_gate(belief) is False

    def test_exact_threshold_meets_gate(self, mastery_gate_service, mock_belief_state):
        """Exactly at threshold should meet gate."""
        # mean = 0.7, confidence = 0.6, responses = 3
        belief = mock_belief_state(
            uuid4(),
            alpha=3.5,  # mean = 0.7
            beta=1.5,
            response_count=3,
        )
        # confidence = 5/7 ≈ 0.714, above threshold
        assert mastery_gate_service._meets_mastery_gate(belief) is True


# ============================================================================
# Test: _calculate_progress
# ============================================================================


class TestCalculateProgress:
    """Tests for _calculate_progress method."""

    def test_full_mastery_is_full_progress(self, mastery_gate_service, mock_belief_state):
        """Fully mastered belief shows 100% progress."""
        belief = mock_belief_state(uuid4(), alpha=8.0, beta=2.0)
        progress = mastery_gate_service._calculate_progress(belief)
        assert progress == pytest.approx(1.0, abs=0.05)

    def test_low_mastery_partial_progress(self, mastery_gate_service, mock_belief_state):
        """Low mastery shows partial progress (weighted by confidence)."""
        belief = mock_belief_state(uuid4(), alpha=1.0, beta=9.0)
        # mean = 0.1, confidence = 10/12 = 0.83
        # mastery_progress = 0.1/0.7 ≈ 0.14
        # confidence_progress = 0.83/0.6 = 1.0 (capped)
        # avg ≈ 0.57
        progress = mastery_gate_service._calculate_progress(belief)
        assert 0.4 < progress < 0.7

    def test_half_mastery_half_progress(self, mastery_gate_service, mock_belief_state):
        """50% mastery with low confidence shows moderate progress."""
        belief = mock_belief_state(uuid4(), alpha=1.0, beta=1.0)
        # mean = 0.5, confidence = 0.5
        progress = mastery_gate_service._calculate_progress(belief)
        # mastery_progress = 0.5/0.7 ≈ 0.71
        # confidence_progress = 0.5/0.6 ≈ 0.83
        # avg ≈ 0.77
        assert 0.5 < progress < 1.0


# ============================================================================
# Test: _estimate_questions_to_unlock
# ============================================================================


class TestEstimateQuestions:
    """Tests for _estimate_questions_to_unlock method."""

    def test_no_blocking_returns_zero(self, mastery_gate_service):
        """No blocking prerequisites = 0 questions."""
        estimate = mastery_gate_service._estimate_questions_to_unlock([])
        assert estimate == 0

    def test_blocking_prereq_estimates_questions(self, mastery_gate_service):
        """Blocking prerequisite with gap estimates questions needed."""
        prereq = BlockingPrerequisite(
            concept_id=uuid4(),
            name="Test Prereq",
            current_mastery=0.5,
            current_confidence=0.5,
            required_mastery=0.7,
            required_confidence=0.6,
            responses_count=0,
            progress_to_unlock=0.5,
        )
        estimate = mastery_gate_service._estimate_questions_to_unlock([prereq])
        # mastery_gap = 0.2, questions_for_mastery = 8
        # questions_for_confidence = max(0, 3-0) = 3
        assert estimate >= 3

    def test_multiple_blocking_sums_estimates(self, mastery_gate_service):
        """Multiple blocking prerequisites sum up estimates."""
        prereq1 = BlockingPrerequisite(
            concept_id=uuid4(),
            name="Prereq 1",
            current_mastery=0.5,
            current_confidence=0.5,
            required_mastery=0.7,
            required_confidence=0.6,
            responses_count=0,
            progress_to_unlock=0.5,
        )
        prereq2 = BlockingPrerequisite(
            concept_id=uuid4(),
            name="Prereq 2",
            current_mastery=0.4,
            current_confidence=0.5,
            required_mastery=0.7,
            required_confidence=0.6,
            responses_count=1,
            progress_to_unlock=0.4,
        )
        estimate = mastery_gate_service._estimate_questions_to_unlock([prereq1, prereq2])
        assert estimate > 6  # More than single prereq


# ============================================================================
# Test: check_prerequisites_mastered
# ============================================================================


class TestCheckPrerequisitesMastered:
    """Tests for check_prerequisites_mastered method."""

    @pytest.mark.asyncio
    async def test_no_prerequisites_is_unlocked(
        self, mastery_gate_service, mock_concept_repo, mock_concept
    ):
        """Concept with no prerequisites is always unlocked."""
        concept_id = uuid4()
        concept = mock_concept(concept_id, name="No Prereqs")
        mock_concept_repo.get_by_id.return_value = concept
        mock_concept_repo.get_prerequisites_with_strength.return_value = []

        result = await mastery_gate_service.check_prerequisites_mastered(
            user_id=uuid4(),
            concept_id=concept_id,
        )

        assert result.is_unlocked is True
        assert result.blocking_prerequisites == []
        assert result.mastery_progress == 1.0

    @pytest.mark.asyncio
    async def test_concept_not_found_raises(
        self, mastery_gate_service, mock_concept_repo
    ):
        """Non-existent concept raises ValueError."""
        mock_concept_repo.get_by_id.return_value = None

        with pytest.raises(ValueError, match="Concept .* not found"):
            await mastery_gate_service.check_prerequisites_mastered(
                user_id=uuid4(),
                concept_id=uuid4(),
            )

    @pytest.mark.asyncio
    async def test_mastered_prereqs_is_unlocked(
        self,
        mastery_gate_service,
        mock_concept_repo,
        mock_belief_repo,
        mock_concept,
        mock_belief_state,
    ):
        """All prerequisites mastered = concept unlocked."""
        concept_id = uuid4()
        prereq_id = uuid4()
        concept = mock_concept(concept_id, name="Advanced Topic")
        prereq = mock_concept(prereq_id, name="Prerequisite")

        mock_concept_repo.get_by_id.return_value = concept
        mock_concept_repo.get_prerequisites_with_strength.return_value = [
            (prereq, 1.0, "required")
        ]

        # Mastered belief for prereq
        mastered_belief = mock_belief_state(
            prereq_id, alpha=8.0, beta=2.0, response_count=5
        )
        mock_belief_repo.get_beliefs_as_dict.return_value = {
            prereq_id: mastered_belief
        }

        result = await mastery_gate_service.check_prerequisites_mastered(
            user_id=uuid4(),
            concept_id=concept_id,
        )

        assert result.is_unlocked is True
        assert result.blocking_prerequisites == []

    @pytest.mark.asyncio
    async def test_unmastered_prereqs_is_locked(
        self,
        mastery_gate_service,
        mock_concept_repo,
        mock_belief_repo,
        mock_concept,
        mock_belief_state,
    ):
        """Unmastered prerequisites = concept locked."""
        concept_id = uuid4()
        prereq_id = uuid4()
        concept = mock_concept(concept_id, name="Advanced Topic")
        prereq = mock_concept(prereq_id, name="Prerequisite")

        mock_concept_repo.get_by_id.return_value = concept
        mock_concept_repo.get_prerequisites_with_strength.return_value = [
            (prereq, 1.0, "required")
        ]

        # Low mastery belief for prereq
        low_belief = mock_belief_state(prereq_id, alpha=2.0, beta=8.0, response_count=5)
        mock_belief_repo.get_beliefs_as_dict.return_value = {prereq_id: low_belief}

        result = await mastery_gate_service.check_prerequisites_mastered(
            user_id=uuid4(),
            concept_id=concept_id,
        )

        assert result.is_unlocked is False
        assert len(result.blocking_prerequisites) == 1
        assert result.blocking_prerequisites[0].concept_id == prereq_id

    @pytest.mark.asyncio
    async def test_no_belief_state_blocks(
        self,
        mastery_gate_service,
        mock_concept_repo,
        mock_belief_repo,
        mock_concept,
    ):
        """Missing belief state for prerequisite = locked."""
        concept_id = uuid4()
        prereq_id = uuid4()
        concept = mock_concept(concept_id, name="Advanced Topic")
        prereq = mock_concept(prereq_id, name="Prerequisite")

        mock_concept_repo.get_by_id.return_value = concept
        mock_concept_repo.get_prerequisites_with_strength.return_value = [
            (prereq, 1.0, "required")
        ]
        mock_belief_repo.get_beliefs_as_dict.return_value = {}  # No beliefs

        result = await mastery_gate_service.check_prerequisites_mastered(
            user_id=uuid4(),
            concept_id=concept_id,
        )

        assert result.is_unlocked is False
        assert len(result.blocking_prerequisites) == 1

    @pytest.mark.asyncio
    async def test_non_required_prereqs_ignored(
        self,
        mastery_gate_service,
        mock_concept_repo,
        mock_belief_repo,
        mock_concept,
        mock_belief_state,
    ):
        """Non-required (suggested) prerequisites don't block."""
        concept_id = uuid4()
        prereq_id = uuid4()
        concept = mock_concept(concept_id, name="Advanced Topic")
        prereq = mock_concept(prereq_id, name="Suggested Prereq")

        mock_concept_repo.get_by_id.return_value = concept
        mock_concept_repo.get_prerequisites_with_strength.return_value = [
            (prereq, 0.5, "suggested")  # Not "required"
        ]

        # Low mastery for suggested prereq
        low_belief = mock_belief_state(prereq_id, alpha=2.0, beta=8.0, response_count=5)
        mock_belief_repo.get_beliefs_as_dict.return_value = {prereq_id: low_belief}

        result = await mastery_gate_service.check_prerequisites_mastered(
            user_id=uuid4(),
            concept_id=concept_id,
        )

        assert result.is_unlocked is True  # Suggested doesn't block


# ============================================================================
# Test: Custom Configuration
# ============================================================================


class TestCustomConfig:
    """Tests for custom MasteryGateConfig."""

    def test_custom_thresholds(self, mock_session, mock_belief_repo, mock_concept_repo):
        """Custom config overrides default thresholds."""
        custom_config = MasteryGateConfig(
            prerequisite_mastery_threshold=0.9,
            prerequisite_confidence_threshold=0.8,
            min_responses_for_gate=5,
        )
        service = MasteryGateService(
            session=mock_session,
            belief_repository=mock_belief_repo,
            concept_repository=mock_concept_repo,
            config=custom_config,
        )

        # Create belief that would pass default thresholds but not custom
        belief = MagicMock()
        belief.alpha = 8.0  # mean = 0.8 < 0.9 threshold
        belief.beta = 2.0
        belief.mean = 0.8
        belief.confidence = 0.83  # > 0.8 threshold
        belief.response_count = 5

        assert service._meets_mastery_gate(belief) is False

    def test_higher_threshold_more_restrictive(
        self, mock_session, mock_belief_repo, mock_concept_repo
    ):
        """Higher thresholds require higher mastery to pass."""
        # Default config (0.7 mastery threshold)
        default_service = MasteryGateService(
            session=mock_session,
            belief_repository=mock_belief_repo,
            concept_repository=mock_concept_repo,
        )

        # Strict config (0.9 mastery threshold)
        strict_config = MasteryGateConfig(prerequisite_mastery_threshold=0.9)
        strict_service = MasteryGateService(
            session=mock_session,
            belief_repository=mock_belief_repo,
            concept_repository=mock_concept_repo,
            config=strict_config,
        )

        belief = MagicMock()
        belief.alpha = 7.5
        belief.beta = 2.5  # mean = 0.75
        belief.mean = 0.75
        belief.confidence = 0.83
        belief.response_count = 5

        assert default_service._meets_mastery_gate(belief) is True
        assert strict_service._meets_mastery_gate(belief) is False
