"""
BKT mathematical utilities for Bayesian Knowledge Tracing.
Provides entropy calculations for Beta distributions and information gain.
"""
from uuid import UUID

from scipy.special import betaln, digamma


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
