"""
BKT mathematical utilities for Bayesian Knowledge Tracing.
Provides entropy calculations for Beta distributions and information gain.
"""
from uuid import UUID

from scipy.special import betaln, digamma

# Default pseudo-observations for prior scaling
# Higher values = more confidence in initial belief
DEFAULT_PSEUDO_OBSERVATIONS = 10


def calculate_alpha_beta(
    prior: float,
    pseudo_observations: int = DEFAULT_PSEUDO_OBSERVATIONS
) -> tuple[float, float]:
    """
    Calculate Beta distribution alpha/beta parameters from initial belief prior.

    Uses pseudo-observations scaling to convert declared familiarity (0-1)
    to Beta distribution parameters. Higher pseudo_observations = more stable
    initial beliefs that won't swing wildly on first question.

    Example:
        prior=0.3 with pseudo_observations=10:
        alpha = 0.3 * 10 = 3 ("3 successes observed")
        beta = 0.7 * 10 = 7 ("7 failures observed")
        mean = 3 / (3 + 7) = 0.3 (same as declared prior)

    Args:
        prior: Initial belief probability [0.0, 1.0]
        pseudo_observations: Number of pseudo-observations for scaling (default 10)

    Returns:
        Tuple of (alpha, beta) values satisfying DB CHECK constraints (> 0)
    """
    # Calculate raw alpha/beta from prior
    raw_alpha = prior * pseudo_observations
    raw_beta = (1 - prior) * pseudo_observations

    # Ensure minimum values to satisfy CHECK constraint (alpha > 0, beta > 0)
    alpha = max(raw_alpha, 0.1)
    beta = max(raw_beta, 0.1)

    return alpha, beta


def beta_entropy(alpha: float, beta: float) -> float:
    """
    Calculate the differential entropy of a Beta(alpha, beta) distribution.

    Uses the formula:
        H(X) = ln(B(α,β)) - (α-1)ψ(α) - (β-1)ψ(β) + (α+β-2)ψ(α+β)

    where B is the beta function and ψ is the digamma function.

    Args:
        alpha: Alpha parameter of Beta distribution (must be > 0)
        beta: Beta parameter of Beta distribution (must be > 0)

    Returns:
        Differential entropy in nats (natural log base)
    """
    if alpha <= 0 or beta <= 0:
        raise ValueError(f"alpha and beta must be positive, got alpha={alpha}, beta={beta}")

    return (
        betaln(alpha, beta)
        - (alpha - 1) * digamma(alpha)
        - (beta - 1) * digamma(beta)
        + (alpha + beta - 2) * digamma(alpha + beta)
    )


def calculate_info_gain(
    beliefs_before: dict[UUID, tuple[float, float]],
    beliefs_after: dict[UUID, tuple[float, float]],
    concept_ids: list[UUID],
) -> float:
    """
    Calculate information gain (entropy reduction) from belief updates.

    Information gain measures how much uncertainty was reduced by
    observing the response. Higher values indicate more informative questions.

    Formula: info_gain = Σ (entropy_before - entropy_after) for each concept

    Args:
        beliefs_before: Dict mapping concept_id to (alpha, beta) before update
        beliefs_after: Dict mapping concept_id to (alpha, beta) after update
        concept_ids: List of concept IDs that were updated

    Returns:
        Total information gain in nats (always >= 0)
    """
    total_info_gain = 0.0

    for concept_id in concept_ids:
        if concept_id not in beliefs_before or concept_id not in beliefs_after:
            continue

        alpha_before, beta_before = beliefs_before[concept_id]
        alpha_after, beta_after = beliefs_after[concept_id]

        entropy_before = beta_entropy(alpha_before, beta_before)
        entropy_after = beta_entropy(alpha_after, beta_after)

        # Information gain is entropy reduction (can be negative in rare cases
        # but typically positive as we gain information)
        info_gain = entropy_before - entropy_after
        total_info_gain += max(0, info_gain)  # Ensure non-negative

    return total_info_gain


def safe_divide(numerator: float, denominator: float, epsilon: float = 1e-10) -> float:
    """
    Safely divide with protection against division by zero.

    Args:
        numerator: The numerator
        denominator: The denominator
        epsilon: Small value to prevent division by zero

    Returns:
        numerator / max(denominator, epsilon)
    """
    return numerator / max(denominator, epsilon)
