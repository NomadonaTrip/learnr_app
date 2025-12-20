"""
Unit tests for BeliefUpdater service.
Tests the Bayesian Knowledge Tracing (BKT) belief update algorithm.

Story 4.4: Bayesian Belief Update Engine (CRITICAL)
"""
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.schemas.belief_state import BeliefUpdateResult, BeliefUpdaterResponse
from src.services.belief_updater import BeliefUpdater
from src.utils.bkt_math import beta_entropy, calculate_info_gain, safe_divide

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
def belief_updater(mock_belief_repo):
    """Create BeliefUpdater with mock repository (no concept repo)."""
    return BeliefUpdater(mock_belief_repo)


@pytest.fixture
def belief_updater_with_concept_repo(mock_belief_repo, mock_concept_repo):
    """Create BeliefUpdater with both repositories for prerequisite testing."""
    return BeliefUpdater(
        mock_belief_repo,
        concept_repository=mock_concept_repo,
        prerequisite_propagation=0.3,
    )


def create_mock_question(
    question_id=None,
    concept_ids=None,
    slip_rate=None,
    guess_rate=None,
    correct_answer="A",
):
    """Helper to create mock Question with QuestionConcept relationships."""
    question = MagicMock()
    question.id = question_id or uuid4()
    question.correct_answer = correct_answer
    question.slip_rate = slip_rate
    question.guess_rate = guess_rate

    # Mock question_concepts relationship
    question.question_concepts = []
    if concept_ids:
        for cid in concept_ids:
            qc = MagicMock()
            qc.concept_id = cid
            question.question_concepts.append(qc)

    return question


def create_mock_belief(concept_id, alpha=1.0, beta=1.0, response_count=0, concept_name="Test Concept"):
    """Helper to create mock BeliefState."""
    belief = MagicMock()
    belief.concept_id = concept_id
    belief.alpha = alpha
    belief.beta = beta
    belief.response_count = response_count

    # Mock the concept relationship
    belief.concept = MagicMock()
    belief.concept.name = concept_name
    belief.concept.id = concept_id

    return belief


def create_mock_concept(concept_id, name="Test Concept"):
    """Helper to create mock Concept."""
    concept = MagicMock()
    concept.id = concept_id
    concept.name = name
    return concept


# ============================================================================
# BKT Math Utility Tests
# ============================================================================

class TestBktMathUtils:
    """Test the bkt_math.py utility functions."""

    def test_beta_entropy_uninformative_prior(self):
        """Test entropy of Beta(1,1) - maximum entropy uniform distribution."""
        entropy = beta_entropy(1.0, 1.0)
        # Beta(1,1) has entropy = 0 (known formula for uniform)
        assert entropy == 0.0

    def test_beta_entropy_high_confidence(self):
        """Test entropy decreases with high confidence."""
        low_entropy = beta_entropy(10.0, 2.0)  # High confidence in mastery
        high_entropy = beta_entropy(2.0, 2.0)  # Lower confidence
        assert low_entropy < high_entropy

    def test_beta_entropy_invalid_params(self):
        """Test beta_entropy raises error for invalid parameters."""
        with pytest.raises(ValueError):
            beta_entropy(0.0, 1.0)
        with pytest.raises(ValueError):
            beta_entropy(1.0, -1.0)

    def test_calculate_info_gain_positive(self):
        """Test info gain is positive when uncertainty is reduced."""
        concept_id = uuid4()
        beliefs_before = {concept_id: (1.0, 1.0)}  # Uninformative
        beliefs_after = {concept_id: (1.78, 1.22)}  # After correct answer

        info_gain = calculate_info_gain(
            beliefs_before, beliefs_after, [concept_id]
        )

        # Info gain should be positive (uncertainty reduced)
        assert info_gain > 0

    def test_calculate_info_gain_multiple_concepts(self):
        """Test info gain calculation with multiple concepts."""
        concept1 = uuid4()
        concept2 = uuid4()

        beliefs_before = {
            concept1: (1.0, 1.0),
            concept2: (2.0, 2.0),
        }
        beliefs_after = {
            concept1: (1.78, 1.22),
            concept2: (2.78, 2.22),
        }

        info_gain = calculate_info_gain(
            beliefs_before, beliefs_after, [concept1, concept2]
        )

        # Info gain should be positive and sum of both concepts
        assert info_gain > 0

    def test_safe_divide_normal(self):
        """Test safe_divide with normal values."""
        assert safe_divide(10.0, 2.0) == 5.0

    def test_safe_divide_zero_denominator(self):
        """Test safe_divide protects against division by zero."""
        result = safe_divide(10.0, 0.0)
        assert result > 0  # Should use epsilon, not crash
        assert result == 10.0 / 1e-10


# ============================================================================
# Bayesian Update Math Tests
# ============================================================================

class TestBayesianUpdateMath:
    """Test the core BKT mathematical formula."""

    def test_correct_answer_increases_mastery(self, belief_updater):
        """AC 9: Correct answer increases mastery probability."""
        alpha, beta = 1.0, 1.0
        slip, guess = 0.10, 0.25

        new_alpha, new_beta = belief_updater._bayesian_update(
            alpha, beta, is_correct=True, slip=slip, guess=guess
        )

        # Mean should increase
        old_mean = alpha / (alpha + beta)
        new_mean = new_alpha / (new_alpha + new_beta)
        assert new_mean > old_mean

        # Verify specific values (worked example from story)
        # p_mastered = 0.5
        # p_correct = (0.9 * 0.5) + (0.25 * 0.5) = 0.575
        # posterior = 0.9 * 0.5 / 0.575 = 0.7826
        assert abs(new_alpha - 1.7826) < 0.01
        assert abs(new_beta - 1.2174) < 0.01

    def test_incorrect_answer_decreases_mastery(self, belief_updater):
        """AC 9: Incorrect answer decreases mastery probability."""
        alpha, beta = 1.0, 1.0
        slip, guess = 0.10, 0.25

        new_alpha, new_beta = belief_updater._bayesian_update(
            alpha, beta, is_correct=False, slip=slip, guess=guess
        )

        # Mean should decrease
        old_mean = alpha / (alpha + beta)
        new_mean = new_alpha / (new_alpha + new_beta)
        assert new_mean < old_mean

        # Verify specific values
        # p_incorrect = (0.1 * 0.5) + (0.75 * 0.5) = 0.425
        # posterior = 0.1 * 0.5 / 0.425 = 0.1176
        assert abs(new_alpha - 1.1176) < 0.01
        assert abs(new_beta - 1.8824) < 0.01

    def test_slip_rate_affects_update_magnitude(self, belief_updater):
        """AC 9: Higher slip rate = smaller update on error."""
        alpha, beta = 2.0, 2.0

        # High slip rate (error-prone question) - incorrect answer
        high_slip_alpha, high_slip_beta = belief_updater._bayesian_update(
            alpha, beta, is_correct=False, slip=0.30, guess=0.25
        )

        # Low slip rate (reliable question) - incorrect answer
        low_slip_alpha, low_slip_beta = belief_updater._bayesian_update(
            alpha, beta, is_correct=False, slip=0.05, guess=0.25
        )

        # With high slip, an error is more likely to be a slip, not non-mastery
        # So the mean decreases less with high slip
        high_slip_mean = high_slip_alpha / (high_slip_alpha + high_slip_beta)
        low_slip_mean = low_slip_alpha / (low_slip_alpha + low_slip_beta)
        assert high_slip_mean > low_slip_mean  # Less penalty with high slip

    def test_guess_rate_affects_update_magnitude(self, belief_updater):
        """AC 9: Higher guess rate = smaller update on correct."""
        alpha, beta = 2.0, 2.0

        # High guess rate (easy to guess) - correct answer
        high_guess_alpha, _ = belief_updater._bayesian_update(
            alpha, beta, is_correct=True, slip=0.10, guess=0.40
        )

        # Low guess rate (hard to guess) - correct answer
        low_guess_alpha, _ = belief_updater._bayesian_update(
            alpha, beta, is_correct=True, slip=0.10, guess=0.10
        )

        # With low guess rate, correct answer is stronger evidence of mastery
        assert low_guess_alpha > high_guess_alpha

    def test_high_mastery_correct_answer(self, belief_updater):
        """Test update when user already has high mastery."""
        alpha, beta = 8.0, 2.0  # mean = 0.8

        new_alpha, new_beta = belief_updater._bayesian_update(
            alpha, beta, is_correct=True, slip=0.10, guess=0.25
        )

        # Should still increase alpha
        assert new_alpha > alpha
        new_mean = new_alpha / (new_alpha + new_beta)
        old_mean = alpha / (alpha + beta)
        assert new_mean > old_mean

    def test_low_mastery_incorrect_answer(self, belief_updater):
        """Test update when user already has low mastery."""
        alpha, beta = 2.0, 8.0  # mean = 0.2

        new_alpha, new_beta = belief_updater._bayesian_update(
            alpha, beta, is_correct=False, slip=0.10, guess=0.25
        )

        # Should increase beta
        assert new_beta > beta
        new_mean = new_alpha / (new_alpha + new_beta)
        old_mean = alpha / (alpha + beta)
        assert new_mean < old_mean


# ============================================================================
# Update Beliefs Tests
# ============================================================================

class TestUpdateBeliefs:
    """Test the update_beliefs method with mocked repository."""

    @pytest.mark.asyncio
    async def test_multi_concept_question_updates_all_concepts(
        self, belief_updater, mock_belief_repo
    ):
        """AC 9: Multi-concept questions update all concepts."""
        user_id = uuid4()
        concept1, concept2, concept3 = uuid4(), uuid4(), uuid4()

        question = create_mock_question(concept_ids=[concept1, concept2, concept3])

        beliefs = {
            concept1: create_mock_belief(concept1, concept_name="Concept 1"),
            concept2: create_mock_belief(concept2, concept_name="Concept 2"),
            concept3: create_mock_belief(concept3, concept_name="Concept 3"),
        }
        mock_belief_repo.get_beliefs_for_concepts.return_value = beliefs
        mock_belief_repo.flush_updates.return_value = None

        response = await belief_updater.update_beliefs(
            user_id=user_id,
            question=question,
            is_correct=True,
        )

        # All 3 concepts should be updated
        assert response.concepts_updated_count == 3
        assert response.direct_updates_count == 3
        assert len(response.updates) == 3

        # Verify repository methods called
        mock_belief_repo.get_beliefs_for_concepts.assert_called_once()
        mock_belief_repo.flush_updates.assert_called_once()

    @pytest.mark.asyncio
    async def test_response_count_incremented(self, belief_updater, mock_belief_repo):
        """AC 9: response_count increases for direct updates."""
        user_id = uuid4()
        concept_id = uuid4()

        question = create_mock_question(concept_ids=[concept_id])

        belief = create_mock_belief(concept_id, response_count=5)
        mock_belief_repo.get_beliefs_for_concepts.return_value = {concept_id: belief}
        mock_belief_repo.flush_updates.return_value = None

        await belief_updater.update_beliefs(
            user_id=user_id,
            question=question,
            is_correct=True,
        )

        # Response count should be incremented
        assert belief.response_count == 6

    @pytest.mark.asyncio
    async def test_returns_belief_updater_response(self, belief_updater, mock_belief_repo):
        """Test that update_beliefs returns BeliefUpdaterResponse."""
        user_id = uuid4()
        concept_id = uuid4()

        question = create_mock_question(concept_ids=[concept_id])
        belief = create_mock_belief(concept_id)
        mock_belief_repo.get_beliefs_for_concepts.return_value = {concept_id: belief}
        mock_belief_repo.flush_updates.return_value = None

        response = await belief_updater.update_beliefs(
            user_id=user_id,
            question=question,
            is_correct=True,
        )

        # Verify response type and structure
        assert isinstance(response, BeliefUpdaterResponse)
        assert len(response.updates) == 1
        assert response.concepts_updated_count == 1
        assert response.direct_updates_count == 1
        assert response.propagated_updates_count == 0
        assert response.info_gain_actual >= 0
        assert response.processing_time_ms >= 0

    @pytest.mark.asyncio
    async def test_belief_update_result_fields(self, belief_updater, mock_belief_repo):
        """Test BeliefUpdateResult contains correct fields."""
        user_id = uuid4()
        concept_id = uuid4()

        question = create_mock_question(concept_ids=[concept_id])
        belief = create_mock_belief(concept_id, alpha=1.0, beta=1.0, concept_name="Test Concept")
        mock_belief_repo.get_beliefs_for_concepts.return_value = {concept_id: belief}
        mock_belief_repo.flush_updates.return_value = None

        response = await belief_updater.update_beliefs(
            user_id=user_id,
            question=question,
            is_correct=True,
        )

        update = response.updates[0]
        assert isinstance(update, BeliefUpdateResult)
        assert update.concept_id == concept_id
        assert update.concept_name == "Test Concept"
        assert update.old_alpha == 1.0
        assert update.old_beta == 1.0
        assert update.new_alpha > 1.0  # Increased for correct answer
        assert update.is_direct is True

    @pytest.mark.asyncio
    async def test_info_gain_positive_when_uncertainty_reduced(
        self, belief_updater, mock_belief_repo
    ):
        """AC 9: Info gain is positive when uncertainty is reduced."""
        user_id = uuid4()
        concept_id = uuid4()

        question = create_mock_question(concept_ids=[concept_id])
        # Start with uninformative prior (high uncertainty)
        belief = create_mock_belief(concept_id, alpha=1.0, beta=1.0)
        mock_belief_repo.get_beliefs_for_concepts.return_value = {concept_id: belief}
        mock_belief_repo.flush_updates.return_value = None

        response = await belief_updater.update_beliefs(
            user_id=user_id,
            question=question,
            is_correct=True,
        )

        # Info gain should be positive (uncertainty reduced)
        assert response.info_gain_actual > 0

    @pytest.mark.asyncio
    async def test_returns_empty_response_when_no_concepts(
        self, belief_updater, mock_belief_repo
    ):
        """Verify empty response when question has no concepts."""
        user_id = uuid4()
        question = create_mock_question(concept_ids=[])

        response = await belief_updater.update_beliefs(
            user_id=user_id,
            question=question,
            is_correct=True,
        )

        assert response.concepts_updated_count == 0
        assert len(response.updates) == 0
        mock_belief_repo.get_beliefs_for_concepts.assert_not_called()

    @pytest.mark.asyncio
    async def test_returns_empty_response_when_no_beliefs_found(
        self, belief_updater, mock_belief_repo
    ):
        """Verify empty response when beliefs not found in database."""
        user_id = uuid4()
        concept_id = uuid4()

        question = create_mock_question(concept_ids=[concept_id])
        mock_belief_repo.get_beliefs_for_concepts.return_value = {}

        response = await belief_updater.update_beliefs(
            user_id=user_id,
            question=question,
            is_correct=True,
        )

        assert response.concepts_updated_count == 0
        assert len(response.updates) == 0


# ============================================================================
# Prerequisite Propagation Tests
# ============================================================================

class TestPrerequisitePropagation:
    """Test prerequisite propagation on correct answers."""

    @pytest.mark.asyncio
    async def test_prerequisite_propagation_on_correct(
        self, belief_updater_with_concept_repo, mock_belief_repo, mock_concept_repo
    ):
        """AC 3/9: Prerequisites get weaker update on correct answer."""
        user_id = uuid4()
        direct_concept_id = uuid4()
        prereq_concept_id = uuid4()

        question = create_mock_question(concept_ids=[direct_concept_id])

        # Direct concept belief
        direct_belief = create_mock_belief(
            direct_concept_id, alpha=1.0, beta=1.0, concept_name="Direct Concept"
        )
        # Prerequisite concept belief
        prereq_belief = create_mock_belief(
            prereq_concept_id, alpha=2.0, beta=2.0, concept_name="Prerequisite Concept"
        )

        # First call: get beliefs for direct concepts
        # Second call: get beliefs for prerequisites
        mock_belief_repo.get_beliefs_for_concepts.side_effect = [
            {direct_concept_id: direct_belief},
            {prereq_concept_id: prereq_belief},
        ]
        mock_belief_repo.flush_updates.return_value = None

        # Mock prerequisites lookup
        prereq_mock = create_mock_concept(prereq_concept_id, "Prerequisite Concept")
        mock_concept_repo.get_prerequisites.return_value = [prereq_mock]

        response = await belief_updater_with_concept_repo.update_beliefs(
            user_id=user_id,
            question=question,
            is_correct=True,
        )

        # Should have 2 updates: 1 direct + 1 propagated
        assert response.concepts_updated_count == 2
        assert response.direct_updates_count == 1
        assert response.propagated_updates_count == 1

        # Find the propagated update
        propagated_update = next(
            (u for u in response.updates if not u.is_direct), None
        )
        assert propagated_update is not None
        assert propagated_update.concept_id == prereq_concept_id
        # Alpha should increase by propagation weight (0.3)
        assert propagated_update.new_alpha == 2.0 + 0.3
        # Beta should NOT change for propagated updates
        assert propagated_update.new_beta == 2.0

    @pytest.mark.asyncio
    async def test_no_propagation_on_incorrect(
        self, belief_updater_with_concept_repo, mock_belief_repo, mock_concept_repo
    ):
        """AC 9: Incorrect does not propagate to prerequisites."""
        user_id = uuid4()
        direct_concept_id = uuid4()
        prereq_concept_id = uuid4()

        question = create_mock_question(concept_ids=[direct_concept_id])

        direct_belief = create_mock_belief(
            direct_concept_id, alpha=1.0, beta=1.0, concept_name="Direct Concept"
        )

        mock_belief_repo.get_beliefs_for_concepts.return_value = {
            direct_concept_id: direct_belief
        }
        mock_belief_repo.flush_updates.return_value = None

        # Set up prerequisites (but they shouldn't be called for incorrect)
        prereq_mock = create_mock_concept(prereq_concept_id, "Prerequisite Concept")
        mock_concept_repo.get_prerequisites.return_value = [prereq_mock]

        response = await belief_updater_with_concept_repo.update_beliefs(
            user_id=user_id,
            question=question,
            is_correct=False,  # INCORRECT answer
        )

        # Should only have 1 update (direct only, no propagation)
        assert response.concepts_updated_count == 1
        assert response.direct_updates_count == 1
        assert response.propagated_updates_count == 0

        # Prerequisite lookup should not be called for incorrect answers
        # (Actually it won't be called because is_correct=False skips propagation)

    @pytest.mark.asyncio
    async def test_propagation_skips_already_updated_concepts(
        self, belief_updater_with_concept_repo, mock_belief_repo, mock_concept_repo
    ):
        """Test that prerequisites already in direct concepts are skipped."""
        user_id = uuid4()
        concept1 = uuid4()
        concept2 = uuid4()  # This is both direct and prereq of concept1

        question = create_mock_question(concept_ids=[concept1, concept2])

        belief1 = create_mock_belief(concept1, concept_name="Concept 1")
        belief2 = create_mock_belief(concept2, concept_name="Concept 2")

        mock_belief_repo.get_beliefs_for_concepts.return_value = {
            concept1: belief1,
            concept2: belief2,
        }
        mock_belief_repo.flush_updates.return_value = None

        # concept2 is a prerequisite of concept1, but it's already direct
        prereq_mock = create_mock_concept(concept2, "Concept 2")
        mock_concept_repo.get_prerequisites.return_value = [prereq_mock]

        response = await belief_updater_with_concept_repo.update_beliefs(
            user_id=user_id,
            question=question,
            is_correct=True,
        )

        # Should only have 2 direct updates (concept2 not duplicated)
        assert response.direct_updates_count == 2
        assert response.propagated_updates_count == 0

    @pytest.mark.asyncio
    async def test_response_count_not_incremented_for_propagated(
        self, belief_updater_with_concept_repo, mock_belief_repo, mock_concept_repo
    ):
        """Test that response_count is NOT incremented for propagated updates."""
        user_id = uuid4()
        direct_concept_id = uuid4()
        prereq_concept_id = uuid4()

        question = create_mock_question(concept_ids=[direct_concept_id])

        direct_belief = create_mock_belief(
            direct_concept_id, response_count=5, concept_name="Direct"
        )
        prereq_belief = create_mock_belief(
            prereq_concept_id, response_count=3, concept_name="Prereq"
        )

        mock_belief_repo.get_beliefs_for_concepts.side_effect = [
            {direct_concept_id: direct_belief},
            {prereq_concept_id: prereq_belief},
        ]
        mock_belief_repo.flush_updates.return_value = None

        prereq_mock = create_mock_concept(prereq_concept_id, "Prereq")
        mock_concept_repo.get_prerequisites.return_value = [prereq_mock]

        await belief_updater_with_concept_repo.update_beliefs(
            user_id=user_id,
            question=question,
            is_correct=True,
        )

        # Direct belief response_count should increment
        assert direct_belief.response_count == 6
        # Prerequisite belief response_count should NOT increment
        assert prereq_belief.response_count == 3


# ============================================================================
# Custom Configuration Tests
# ============================================================================

class TestCustomConfiguration:
    """Test BeliefUpdater with custom default rates."""

    @pytest.mark.asyncio
    async def test_custom_prerequisite_propagation_weight(self, mock_belief_repo, mock_concept_repo):
        """Test custom prerequisite propagation weight."""
        updater = BeliefUpdater(
            mock_belief_repo,
            concept_repository=mock_concept_repo,
            prerequisite_propagation=0.5,  # Custom weight
        )

        user_id = uuid4()
        direct_concept_id = uuid4()
        prereq_concept_id = uuid4()

        question = create_mock_question(concept_ids=[direct_concept_id])

        direct_belief = create_mock_belief(direct_concept_id, concept_name="Direct")
        prereq_belief = create_mock_belief(
            prereq_concept_id, alpha=2.0, beta=2.0, concept_name="Prereq"
        )

        mock_belief_repo.get_beliefs_for_concepts.side_effect = [
            {direct_concept_id: direct_belief},
            {prereq_concept_id: prereq_belief},
        ]
        mock_belief_repo.flush_updates.return_value = None

        prereq_mock = create_mock_concept(prereq_concept_id, "Prereq")
        mock_concept_repo.get_prerequisites.return_value = [prereq_mock]

        response = await updater.update_beliefs(
            user_id=user_id,
            question=question,
            is_correct=True,
        )

        # Find propagated update
        propagated = next((u for u in response.updates if not u.is_direct), None)
        assert propagated is not None
        # Should use custom weight of 0.5
        assert propagated.new_alpha == 2.0 + 0.5


# ============================================================================
# Edge Cases
# ============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_extreme_high_mastery_correct(self, belief_updater):
        """Test update with very high prior mastery and correct answer."""
        alpha, beta = 99.0, 1.0  # mean ≈ 0.99

        new_alpha, new_beta = belief_updater._bayesian_update(
            alpha, beta, is_correct=True, slip=0.10, guess=0.25
        )

        # Should still increase alpha slightly
        assert new_alpha > alpha
        new_mean = new_alpha / (new_alpha + new_beta)
        assert new_mean > 0.98

    def test_extreme_low_mastery_incorrect(self, belief_updater):
        """Test update with very low prior mastery and incorrect answer."""
        alpha, beta = 1.0, 99.0  # mean ≈ 0.01

        new_alpha, new_beta = belief_updater._bayesian_update(
            alpha, beta, is_correct=False, slip=0.10, guess=0.25
        )

        # Should increase beta slightly
        assert new_beta > beta
        new_mean = new_alpha / (new_alpha + new_beta)
        assert new_mean < 0.02

    def test_zero_slip_rate(self, belief_updater):
        """Test with zero slip rate (perfect question reliability)."""
        alpha, beta = 1.0, 1.0

        # Zero slip means an error indicates lower probability of mastery
        # With slip=0: posterior = 0, so new_alpha stays at 1, new_beta = 2
        # new_mean = 1/3 ≈ 0.333
        new_alpha, new_beta = belief_updater._bayesian_update(
            alpha, beta, is_correct=False, slip=0.0, guess=0.25
        )

        # Posterior is 0, so mean decreases from 0.5 to 1/3
        new_mean = new_alpha / (new_alpha + new_beta)
        assert new_mean < 0.5  # Decreased from prior mean of 0.5
        assert abs(new_mean - 1/3) < 0.01  # Should be exactly 1/3

    def test_zero_guess_rate(self, belief_updater):
        """Test with zero guess rate (impossible to guess correctly)."""
        alpha, beta = 1.0, 1.0

        # Zero guess means correct answer provides strong evidence of mastery
        # With guess=0, slip=0.10: posterior = 1.0, so new_alpha = 2, new_beta = 1
        # new_mean = 2/3 ≈ 0.666
        new_alpha, new_beta = belief_updater._bayesian_update(
            alpha, beta, is_correct=True, slip=0.10, guess=0.0
        )

        # Posterior is 1.0, so mean increases from 0.5 to 2/3
        new_mean = new_alpha / (new_alpha + new_beta)
        assert new_mean > 0.5  # Increased from prior mean of 0.5
        assert abs(new_mean - 2/3) < 0.01  # Should be exactly 2/3


# ============================================================================
# Schema Tests
# ============================================================================

class TestBeliefUpdateSchemas:
    """Test BeliefUpdateResult and BeliefUpdaterResponse schemas."""

    def test_belief_update_result_computed_fields(self):
        """Test computed fields in BeliefUpdateResult."""
        update = BeliefUpdateResult(
            concept_id=uuid4(),
            concept_name="Test Concept",
            old_alpha=1.0,
            old_beta=1.0,
            new_alpha=1.78,
            new_beta=1.22,
            is_direct=True,
        )

        assert update.old_mean == 0.5
        assert abs(update.new_mean - 0.5933) < 0.001
        assert update.old_confidence == 0.5
        assert update.new_confidence > update.old_confidence

    def test_belief_updater_response_to_jsonb(self):
        """Test to_belief_updates_jsonb conversion."""
        concept_id = uuid4()
        update = BeliefUpdateResult(
            concept_id=concept_id,
            concept_name="Test",
            old_alpha=1.0,
            old_beta=1.0,
            new_alpha=1.78,
            new_beta=1.22,
            is_direct=True,
        )

        response = BeliefUpdaterResponse(
            updates=[update],
            info_gain_actual=0.15,
            concepts_updated_count=1,
            direct_updates_count=1,
            propagated_updates_count=0,
            processing_time_ms=5.2,
        )

        jsonb = response.to_belief_updates_jsonb()
        assert len(jsonb) == 1
        assert jsonb[0]["concept_id"] == str(concept_id)
        assert jsonb[0]["concept_name"] == "Test"
        assert jsonb[0]["old_alpha"] == 1.0
        assert jsonb[0]["new_alpha"] == 1.78


# ============================================================================
# Story 2.14: Lazy Initialization Tests
# ============================================================================

class TestLazyInitialization:
    """Test lazy initialization of belief states for new concepts."""

    @pytest.mark.asyncio
    async def test_create_missing_beliefs_creates_with_uninformative_prior(
        self, belief_updater, mock_belief_repo
    ):
        """Test _create_missing_beliefs creates beliefs with Beta(1,1)."""
        user_id = uuid4()
        concept_id = uuid4()
        concept_ids = {concept_id}

        # Mock bulk_create_from_concepts to return count
        mock_belief_repo.bulk_create_from_concepts.return_value = 1

        # Mock get_beliefs_for_concepts to return the new belief
        new_belief = create_mock_belief(concept_id, alpha=1.0, beta=1.0)
        mock_belief_repo.get_beliefs_for_concepts.return_value = {concept_id: new_belief}

        result = await belief_updater._create_missing_beliefs(user_id, concept_ids)

        # Verify bulk_create_from_concepts was called with uninformative prior
        mock_belief_repo.bulk_create_from_concepts.assert_called_once_with(
            user_id=user_id,
            concept_ids=[concept_id],
            alpha=1.0,  # Uninformative prior Beta(1,1)
            beta=1.0,
        )

        # Verify result
        assert concept_id in result
        assert result[concept_id].alpha == 1.0
        assert result[concept_id].beta == 1.0

    @pytest.mark.asyncio
    async def test_create_missing_beliefs_returns_empty_for_no_concepts(
        self, belief_updater, mock_belief_repo
    ):
        """Test _create_missing_beliefs returns empty dict for empty input."""
        user_id = uuid4()

        result = await belief_updater._create_missing_beliefs(user_id, set())

        assert result == {}
        mock_belief_repo.bulk_create_from_concepts.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_beliefs_calls_lazy_init_for_missing_beliefs(
        self, belief_updater, mock_belief_repo
    ):
        """Test update_beliefs creates missing beliefs via lazy init."""
        user_id = uuid4()
        existing_concept_id = uuid4()
        missing_concept_id = uuid4()

        question = create_mock_question(
            concept_ids=[existing_concept_id, missing_concept_id]
        )

        # First call returns only existing belief (missing one is missing)
        existing_belief = create_mock_belief(
            existing_concept_id, alpha=2.0, beta=2.0, concept_name="Existing"
        )
        missing_belief = create_mock_belief(
            missing_concept_id, alpha=1.0, beta=1.0, concept_name="Missing"
        )

        # First call: return only existing belief
        # Second call (after lazy init): return newly created belief
        mock_belief_repo.get_beliefs_for_concepts.side_effect = [
            {existing_concept_id: existing_belief},  # Initial fetch
            {missing_concept_id: missing_belief},     # After bulk_create
        ]
        mock_belief_repo.bulk_create_from_concepts.return_value = 1
        mock_belief_repo.flush_updates.return_value = None

        response = await belief_updater.update_beliefs(
            user_id=user_id,
            question=question,
            is_correct=True,
        )

        # Verify lazy init was called for missing concept
        mock_belief_repo.bulk_create_from_concepts.assert_called_once()
        call_args = mock_belief_repo.bulk_create_from_concepts.call_args
        assert call_args.kwargs["user_id"] == user_id
        assert missing_concept_id in call_args.kwargs["concept_ids"]
        assert call_args.kwargs["alpha"] == 1.0
        assert call_args.kwargs["beta"] == 1.0

        # Both concepts should be updated
        assert response.concepts_updated_count == 2

    @pytest.mark.asyncio
    async def test_update_beliefs_does_not_call_lazy_init_when_all_exist(
        self, belief_updater, mock_belief_repo
    ):
        """Test update_beliefs does NOT call lazy init when all beliefs exist."""
        user_id = uuid4()
        concept1 = uuid4()
        concept2 = uuid4()

        question = create_mock_question(concept_ids=[concept1, concept2])

        # Both beliefs exist
        beliefs = {
            concept1: create_mock_belief(concept1, alpha=2.0, beta=2.0, concept_name="C1"),
            concept2: create_mock_belief(concept2, alpha=3.0, beta=1.0, concept_name="C2"),
        }
        mock_belief_repo.get_beliefs_for_concepts.return_value = beliefs
        mock_belief_repo.flush_updates.return_value = None

        await belief_updater.update_beliefs(
            user_id=user_id,
            question=question,
            is_correct=True,
        )

        # bulk_create_from_concepts should NOT be called
        mock_belief_repo.bulk_create_from_concepts.assert_not_called()

    @pytest.mark.asyncio
    async def test_lazy_init_does_not_modify_existing_beliefs(
        self, belief_updater, mock_belief_repo
    ):
        """Test existing beliefs are not modified by lazy init."""
        user_id = uuid4()
        existing_concept_id = uuid4()
        missing_concept_id = uuid4()

        question = create_mock_question(
            concept_ids=[existing_concept_id, missing_concept_id]
        )

        # Existing belief with non-default values
        existing_belief = create_mock_belief(
            existing_concept_id,
            alpha=5.0,  # Non-default
            beta=3.0,   # Non-default
            response_count=10,
            concept_name="Existing"
        )
        new_belief = create_mock_belief(
            missing_concept_id, alpha=1.0, beta=1.0, concept_name="New"
        )

        mock_belief_repo.get_beliefs_for_concepts.side_effect = [
            {existing_concept_id: existing_belief},  # Initial fetch
            {missing_concept_id: new_belief},         # After bulk_create
        ]
        mock_belief_repo.bulk_create_from_concepts.return_value = 1
        mock_belief_repo.flush_updates.return_value = None

        response = await belief_updater.update_beliefs(
            user_id=user_id,
            question=question,
            is_correct=True,
        )

        # Find the update for existing concept
        existing_update = next(
            (u for u in response.updates if u.concept_id == existing_concept_id),
            None
        )

        # Verify existing belief was updated FROM its original values
        # (not reset to Beta(1,1))
        assert existing_update is not None
        assert existing_update.old_alpha == 5.0  # Original value preserved
        assert existing_update.old_beta == 3.0   # Original value preserved
        assert existing_update.new_alpha > 5.0   # Updated (correct answer)

    @pytest.mark.asyncio
    async def test_lazy_init_handles_multiple_missing_concepts(
        self, belief_updater, mock_belief_repo
    ):
        """Test lazy init creates beliefs for multiple missing concepts."""
        user_id = uuid4()
        missing1, missing2, missing3 = uuid4(), uuid4(), uuid4()

        question = create_mock_question(concept_ids=[missing1, missing2, missing3])

        # Create beliefs for all missing concepts
        beliefs = {
            missing1: create_mock_belief(missing1, concept_name="M1"),
            missing2: create_mock_belief(missing2, concept_name="M2"),
            missing3: create_mock_belief(missing3, concept_name="M3"),
        }

        mock_belief_repo.get_beliefs_for_concepts.side_effect = [
            {},       # Initial fetch: no beliefs
            beliefs,  # After bulk_create
        ]
        mock_belief_repo.bulk_create_from_concepts.return_value = 3
        mock_belief_repo.flush_updates.return_value = None

        response = await belief_updater.update_beliefs(
            user_id=user_id,
            question=question,
            is_correct=True,
        )

        # Verify bulk_create was called with all 3 missing concepts
        mock_belief_repo.bulk_create_from_concepts.assert_called_once()
        call_args = mock_belief_repo.bulk_create_from_concepts.call_args
        created_concepts = set(call_args.kwargs["concept_ids"])
        assert created_concepts == {missing1, missing2, missing3}

        # All 3 should be updated
        assert response.concepts_updated_count == 3
