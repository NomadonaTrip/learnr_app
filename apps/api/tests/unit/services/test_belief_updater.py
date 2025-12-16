"""
Unit tests for BeliefUpdater service.
Tests the Bayesian Knowledge Tracing (BKT) belief update algorithm.
"""
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.services.belief_updater import BeliefUpdater


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_belief_repo():
    """Create mock BeliefRepository."""
    return AsyncMock()


@pytest.fixture
def belief_updater(mock_belief_repo):
    """Create BeliefUpdater with mock repository."""
    return BeliefUpdater(mock_belief_repo)


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


def create_mock_belief(concept_id, alpha=1.0, beta=1.0, response_count=0):
    """Helper to create mock BeliefState."""
    belief = MagicMock()
    belief.concept_id = concept_id
    belief.alpha = alpha
    belief.beta = beta
    belief.response_count = response_count
    return belief


# ============================================================================
# Bayesian Update Math Tests
# ============================================================================

class TestBayesianUpdateMath:
    """Test the core BKT mathematical formula."""

    def test_correct_answer_increases_alpha_more_than_beta(self, belief_updater):
        """Verify correct answer increases alpha (mastery evidence) more."""
        alpha, beta = 1.0, 1.0
        slip, guess = 0.10, 0.25

        new_alpha, new_beta = belief_updater._bayesian_update(
            alpha, beta, is_correct=True, slip=slip, guess=guess
        )

        # For correct answer with Beta(1,1) prior:
        # p_mastered = 0.5
        # p_correct = (0.9 * 0.5) + (0.25 * 0.5) = 0.575
        # posterior = 0.9 * 0.5 / 0.575 = 0.7826
        # new_alpha = 1 + 0.7826 = 1.7826
        # new_beta = 1 + 0.2174 = 1.2174
        assert new_alpha > alpha
        assert new_alpha > new_beta
        assert new_alpha - alpha > new_beta - beta
        # Verify specific values
        assert abs(new_alpha - 1.7826) < 0.01
        assert abs(new_beta - 1.2174) < 0.01

    def test_incorrect_answer_increases_beta_more_than_alpha(self, belief_updater):
        """Verify incorrect answer increases beta (non-mastery evidence) more."""
        alpha, beta = 1.0, 1.0
        slip, guess = 0.10, 0.25

        new_alpha, new_beta = belief_updater._bayesian_update(
            alpha, beta, is_correct=False, slip=slip, guess=guess
        )

        # For incorrect answer with Beta(1,1) prior:
        # p_mastered = 0.5
        # p_incorrect = (0.1 * 0.5) + (0.75 * 0.5) = 0.425
        # posterior = 0.1 * 0.5 / 0.425 = 0.1176
        # new_alpha = 1 + 0.1176 = 1.1176
        # new_beta = 1 + 0.8824 = 1.8824
        assert new_beta > beta
        assert new_beta > new_alpha
        assert new_beta - beta > new_alpha - alpha
        # Verify specific values
        assert abs(new_alpha - 1.1176) < 0.01
        assert abs(new_beta - 1.8824) < 0.01

    def test_initial_beta_1_1_state(self, belief_updater):
        """Test updates from uninformative Beta(1,1) prior (uniform distribution)."""
        alpha, beta = 1.0, 1.0  # Uninformative prior

        # Mean should be 0.5 initially
        assert alpha / (alpha + beta) == 0.5

        # After correct answer
        new_alpha, new_beta = belief_updater._bayesian_update(
            alpha, beta, is_correct=True, slip=0.10, guess=0.25
        )

        # Mean should increase
        new_mean = new_alpha / (new_alpha + new_beta)
        assert new_mean > 0.5

    def test_custom_slip_guess_rates(self, belief_updater):
        """Test with custom (non-default) slip/guess parameters."""
        alpha, beta = 2.0, 2.0

        # High slip rate (error-prone question)
        high_slip_alpha, high_slip_beta = belief_updater._bayesian_update(
            alpha, beta, is_correct=True, slip=0.30, guess=0.25
        )

        # Low slip rate (reliable question)
        low_slip_alpha, low_slip_beta = belief_updater._bayesian_update(
            alpha, beta, is_correct=True, slip=0.05, guess=0.25
        )

        # Correct answer on low-slip question should increase alpha more
        assert low_slip_alpha > high_slip_alpha

    def test_high_mastery_correct_answer(self, belief_updater):
        """Test update when user already has high mastery."""
        # High mastery: Beta(8, 2) => mean = 0.8
        alpha, beta = 8.0, 2.0

        new_alpha, new_beta = belief_updater._bayesian_update(
            alpha, beta, is_correct=True, slip=0.10, guess=0.25
        )

        # Should still increase alpha, but posterior is already high
        assert new_alpha > alpha
        new_mean = new_alpha / (new_alpha + new_beta)
        old_mean = alpha / (alpha + beta)
        assert new_mean > old_mean

    def test_low_mastery_incorrect_answer(self, belief_updater):
        """Test update when user already has low mastery."""
        # Low mastery: Beta(2, 8) => mean = 0.2
        alpha, beta = 2.0, 8.0

        new_alpha, new_beta = belief_updater._bayesian_update(
            alpha, beta, is_correct=False, slip=0.10, guess=0.25
        )

        # Should still increase beta
        assert new_beta > beta
        new_mean = new_alpha / (new_alpha + new_beta)
        old_mean = alpha / (alpha + beta)
        assert new_mean < old_mean


# ============================================================================
# Update Beliefs Integration Tests
# ============================================================================

class TestUpdateBeliefs:
    """Test the update_beliefs method with mocked repository."""

    @pytest.mark.asyncio
    async def test_updates_all_linked_concepts(self, belief_updater, mock_belief_repo):
        """Verify all concepts linked to question are updated."""
        user_id = uuid4()
        concept1, concept2, concept3 = uuid4(), uuid4(), uuid4()

        question = create_mock_question(concept_ids=[concept1, concept2, concept3])

        # Mock beliefs for all concepts
        beliefs = {
            concept1: create_mock_belief(concept1),
            concept2: create_mock_belief(concept2),
            concept3: create_mock_belief(concept3),
        }
        mock_belief_repo.get_beliefs_for_concepts.return_value = beliefs
        mock_belief_repo.flush_updates.return_value = None

        updated_ids = await belief_updater.update_beliefs(
            user_id=user_id,
            question=question,
            is_correct=True,
        )

        # All 3 concepts should be updated
        assert len(updated_ids) == 3
        assert concept1 in updated_ids
        assert concept2 in updated_ids
        assert concept3 in updated_ids

        # Verify repository methods called
        mock_belief_repo.get_beliefs_for_concepts.assert_called_once_with(
            user_id, [concept1, concept2, concept3]
        )
        mock_belief_repo.flush_updates.assert_called_once()

    @pytest.mark.asyncio
    async def test_increments_response_count(self, belief_updater, mock_belief_repo):
        """Verify response_count is incremented for each updated belief."""
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
    async def test_uses_question_slip_guess_rates(self, belief_updater, mock_belief_repo):
        """Verify question-specific slip/guess rates are used when available."""
        user_id = uuid4()
        concept_id = uuid4()

        # Question with custom rates
        question = create_mock_question(
            concept_ids=[concept_id],
            slip_rate=0.15,
            guess_rate=0.30,
        )

        belief = create_mock_belief(concept_id, alpha=1.0, beta=1.0)
        mock_belief_repo.get_beliefs_for_concepts.return_value = {concept_id: belief}
        mock_belief_repo.flush_updates.return_value = None

        await belief_updater.update_beliefs(
            user_id=user_id,
            question=question,
            is_correct=True,
        )

        # Calculate expected values with custom rates
        # p_mastered = 0.5
        # p_correct = (1 - 0.15) * 0.5 + 0.30 * (1 - 0.5) = 0.575
        # posterior = 0.85 * 0.5 / 0.575 = 0.7391
        expected_alpha = 1.0 + 0.7391
        expected_beta = 1.0 + (1 - 0.7391)

        assert abs(belief.alpha - expected_alpha) < 0.01
        assert abs(belief.beta - expected_beta) < 0.01

    @pytest.mark.asyncio
    async def test_uses_default_rates_when_question_rates_none(
        self, belief_updater, mock_belief_repo
    ):
        """Verify default slip/guess rates are used when question has None."""
        user_id = uuid4()
        concept_id = uuid4()

        # Question without custom rates
        question = create_mock_question(
            concept_ids=[concept_id],
            slip_rate=None,
            guess_rate=None,
        )

        belief = create_mock_belief(concept_id, alpha=1.0, beta=1.0)
        mock_belief_repo.get_beliefs_for_concepts.return_value = {concept_id: belief}
        mock_belief_repo.flush_updates.return_value = None

        await belief_updater.update_beliefs(
            user_id=user_id,
            question=question,
            is_correct=True,
        )

        # Should use defaults (0.10, 0.25)
        # p_mastered = 0.5
        # p_correct = (0.9 * 0.5) + (0.25 * 0.5) = 0.575
        # posterior = 0.9 * 0.5 / 0.575 = 0.7826
        expected_alpha = 1.0 + 0.7826

        assert abs(belief.alpha - expected_alpha) < 0.01

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_concepts(self, belief_updater, mock_belief_repo):
        """Verify empty list returned when question has no concepts."""
        user_id = uuid4()
        question = create_mock_question(concept_ids=[])

        updated_ids = await belief_updater.update_beliefs(
            user_id=user_id,
            question=question,
            is_correct=True,
        )

        assert updated_ids == []
        mock_belief_repo.get_beliefs_for_concepts.assert_not_called()

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_beliefs_found(self, belief_updater, mock_belief_repo):
        """Verify empty list returned when beliefs not found in database."""
        user_id = uuid4()
        concept_id = uuid4()

        question = create_mock_question(concept_ids=[concept_id])
        mock_belief_repo.get_beliefs_for_concepts.return_value = {}

        updated_ids = await belief_updater.update_beliefs(
            user_id=user_id,
            question=question,
            is_correct=True,
        )

        assert updated_ids == []

    @pytest.mark.asyncio
    async def test_handles_partial_belief_coverage(self, belief_updater, mock_belief_repo):
        """Verify partial update when some beliefs are missing."""
        user_id = uuid4()
        concept1, concept2 = uuid4(), uuid4()

        question = create_mock_question(concept_ids=[concept1, concept2])

        # Only one belief exists
        beliefs = {concept1: create_mock_belief(concept1)}
        mock_belief_repo.get_beliefs_for_concepts.return_value = beliefs
        mock_belief_repo.flush_updates.return_value = None

        updated_ids = await belief_updater.update_beliefs(
            user_id=user_id,
            question=question,
            is_correct=True,
        )

        # Only concept1 should be updated
        assert len(updated_ids) == 1
        assert concept1 in updated_ids
        assert concept2 not in updated_ids


# ============================================================================
# Custom Configuration Tests
# ============================================================================

class TestCustomConfiguration:
    """Test BeliefUpdater with custom default rates."""

    @pytest.mark.asyncio
    async def test_custom_default_slip_rate(self, mock_belief_repo):
        """Verify custom default slip rate is used."""
        updater = BeliefUpdater(
            mock_belief_repo,
            default_slip=0.20,
            default_guess=0.25,
        )

        user_id = uuid4()
        concept_id = uuid4()

        question = create_mock_question(concept_ids=[concept_id])
        belief = create_mock_belief(concept_id)
        mock_belief_repo.get_beliefs_for_concepts.return_value = {concept_id: belief}
        mock_belief_repo.flush_updates.return_value = None

        await updater.update_beliefs(
            user_id=user_id,
            question=question,
            is_correct=True,
        )

        # With slip=0.20, the update should be different
        # p_correct = (0.8 * 0.5) + (0.25 * 0.5) = 0.525
        # posterior = 0.8 * 0.5 / 0.525 = 0.7619
        expected_alpha = 1.0 + 0.7619

        assert abs(belief.alpha - expected_alpha) < 0.01

    @pytest.mark.asyncio
    async def test_custom_default_guess_rate(self, mock_belief_repo):
        """Verify custom default guess rate is used."""
        updater = BeliefUpdater(
            mock_belief_repo,
            default_slip=0.10,
            default_guess=0.40,
        )

        user_id = uuid4()
        concept_id = uuid4()

        question = create_mock_question(concept_ids=[concept_id])
        belief = create_mock_belief(concept_id)
        mock_belief_repo.get_beliefs_for_concepts.return_value = {concept_id: belief}
        mock_belief_repo.flush_updates.return_value = None

        await updater.update_beliefs(
            user_id=user_id,
            question=question,
            is_correct=True,
        )

        # With guess=0.40, the update should be different
        # p_correct = (0.9 * 0.5) + (0.40 * 0.5) = 0.65
        # posterior = 0.9 * 0.5 / 0.65 = 0.6923
        expected_alpha = 1.0 + 0.6923

        assert abs(belief.alpha - expected_alpha) < 0.01


# ============================================================================
# Edge Cases
# ============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_extreme_high_mastery_correct(self, belief_updater):
        """Test update with very high prior mastery and correct answer."""
        # Near-certain mastery: Beta(99, 1) => mean ≈ 0.99
        alpha, beta = 99.0, 1.0

        new_alpha, new_beta = belief_updater._bayesian_update(
            alpha, beta, is_correct=True, slip=0.10, guess=0.25
        )

        # Should still increase alpha slightly
        assert new_alpha > alpha
        # Mean should remain high
        new_mean = new_alpha / (new_alpha + new_beta)
        assert new_mean > 0.98

    def test_extreme_low_mastery_incorrect(self, belief_updater):
        """Test update with very low prior mastery and incorrect answer."""
        # Near-certain non-mastery: Beta(1, 99) => mean ≈ 0.01
        alpha, beta = 1.0, 99.0

        new_alpha, new_beta = belief_updater._bayesian_update(
            alpha, beta, is_correct=False, slip=0.10, guess=0.25
        )

        # Should increase beta slightly
        assert new_beta > beta
        # Mean should remain low
        new_mean = new_alpha / (new_alpha + new_beta)
        assert new_mean < 0.02

    def test_surprise_correct_from_low_mastery(self, belief_updater):
        """Test correct answer from low mastery (meaningful update expected)."""
        # Low mastery: Beta(1, 4) => mean = 0.2
        alpha, beta = 1.0, 4.0

        new_alpha, new_beta = belief_updater._bayesian_update(
            alpha, beta, is_correct=True, slip=0.10, guess=0.25
        )

        # Correct answer should increase mastery estimate
        old_mean = alpha / (alpha + beta)
        new_mean = new_alpha / (new_alpha + new_beta)
        assert new_mean > old_mean
        # The update should be positive (even if small due to guess rate)
        # With guess=0.25, a correct answer from low mastery has less impact
        # because it might have been a lucky guess
        assert new_mean - old_mean > 0.01

    def test_surprise_incorrect_from_high_mastery(self, belief_updater):
        """Test incorrect answer from high mastery (could be slip)."""
        # High mastery: Beta(4, 1) => mean = 0.8
        alpha, beta = 4.0, 1.0

        new_alpha, new_beta = belief_updater._bayesian_update(
            alpha, beta, is_correct=False, slip=0.10, guess=0.25
        )

        # Incorrect answer should decrease mastery, but not drastically
        # (could be slip, not necessarily non-mastery)
        old_mean = alpha / (alpha + beta)
        new_mean = new_alpha / (new_alpha + new_beta)
        assert new_mean < old_mean
        # Still relatively high due to slip possibility
        assert new_mean > 0.4
