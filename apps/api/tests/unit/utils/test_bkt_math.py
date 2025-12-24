"""
Unit tests for BKT mathematical utilities.
Story 3.4.1: Tests for calculate_alpha_beta prior calculation function.
"""
import pytest

from src.utils.bkt_math import calculate_alpha_beta, DEFAULT_PSEUDO_OBSERVATIONS


class TestCalculateAlphaBeta:
    """Tests for calculate_alpha_beta function."""

    def test_new_user_prior_0_1(self):
        """Prior 0.1 (new to topic) should return alpha=1.0, beta=9.0."""
        alpha, beta = calculate_alpha_beta(0.1)
        assert alpha == 1.0
        assert beta == 9.0

    def test_basics_user_prior_0_3(self):
        """Prior 0.3 (knows basics) should return alpha=3.0, beta=7.0."""
        alpha, beta = calculate_alpha_beta(0.3)
        assert alpha == 3.0
        assert beta == 7.0

    def test_intermediate_user_prior_0_5(self):
        """Prior 0.5 (intermediate) should return alpha=5.0, beta=5.0."""
        alpha, beta = calculate_alpha_beta(0.5)
        assert alpha == 5.0
        assert beta == 5.0

    def test_expert_user_prior_0_7(self):
        """Prior 0.7 (expert) should return alpha=7.0, beta=3.0."""
        alpha, beta = calculate_alpha_beta(0.7)
        assert alpha == 7.0
        assert abs(beta - 3.0) < 0.001  # Float precision tolerance

    def test_edge_case_prior_0_0(self):
        """Prior 0.0 should return minimum alpha (0.1) due to DB constraint."""
        alpha, beta = calculate_alpha_beta(0.0)
        # alpha = max(0.0 * 10, 0.1) = 0.1
        # beta = max(1.0 * 10, 0.1) = 10.0
        assert alpha == 0.1
        assert beta == 10.0

    def test_edge_case_prior_1_0(self):
        """Prior 1.0 should return minimum beta (0.1) due to DB constraint."""
        alpha, beta = calculate_alpha_beta(1.0)
        # alpha = max(1.0 * 10, 0.1) = 10.0
        # beta = max(0.0 * 10, 0.1) = 0.1
        assert alpha == 10.0
        assert beta == 0.1

    def test_custom_pseudo_observations(self):
        """Custom pseudo_observations should scale alpha/beta accordingly."""
        alpha, beta = calculate_alpha_beta(0.5, pseudo_observations=20)
        # alpha = 0.5 * 20 = 10.0
        # beta = 0.5 * 20 = 10.0
        assert alpha == 10.0
        assert beta == 10.0

    def test_all_outputs_satisfy_db_constraints(self):
        """All outputs must satisfy DB CHECK constraints (alpha > 0, beta > 0)."""
        test_priors = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        for prior in test_priors:
            alpha, beta = calculate_alpha_beta(prior)
            assert alpha > 0, f"alpha must be > 0 for prior={prior}, got {alpha}"
            assert beta > 0, f"beta must be > 0 for prior={prior}, got {beta}"

    def test_mean_equals_prior(self):
        """The Beta distribution mean (alpha / (alpha + beta)) should equal the prior."""
        test_priors = [0.1, 0.3, 0.5, 0.7]
        for prior in test_priors:
            alpha, beta = calculate_alpha_beta(prior)
            mean = alpha / (alpha + beta)
            assert abs(mean - prior) < 0.001, f"Mean {mean} should equal prior {prior}"

    def test_default_pseudo_observations_is_10(self):
        """Default pseudo-observations should be 10."""
        assert DEFAULT_PSEUDO_OBSERVATIONS == 10

    def test_very_small_prior(self):
        """Very small prior (0.01) should still produce valid alpha."""
        alpha, beta = calculate_alpha_beta(0.01)
        # alpha = max(0.01 * 10, 0.1) = 0.1 (hits minimum)
        # beta = max(0.99 * 10, 0.1) = 9.9
        assert alpha == 0.1
        assert beta == 9.9

    def test_very_large_prior(self):
        """Very large prior (0.99) should still produce valid beta."""
        alpha, beta = calculate_alpha_beta(0.99)
        # alpha = max(0.99 * 10, 0.1) = 9.9
        # beta = max(0.01 * 10, 0.1) = 0.1 (hits minimum)
        assert abs(alpha - 9.9) < 0.001
        assert abs(beta - 0.1) < 0.001  # Float precision tolerance
