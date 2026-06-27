# Fundamental Concepts

### What is Bayesian Knowledge Tracing?

BKT models each learner's knowledge as a probability distribution over discrete concepts. Rather than asking "What's your score?", BKT asks "What's the probability you've mastered concept X, and how confident are we in that estimate?"

**Key Differences from Traditional Approaches:**

| Aspect             | Traditional (Quiz Apps) | BKT (LearnR)                                    |
| ------------------ | ----------------------- | ----------------------------------------------- |
| Knowledge Unit     | Category/Topic (6-20)   | Concept (500-1500)                              |
| Measurement        | Point estimate (72%)    | Distribution (Beta(8.2, 3.1))                   |
| Question Selection | Random + difficulty     | Maximum information gain                        |
| Stopping Criterion | Fixed count             | Confidence threshold                            |
| **User Output**    | "You scored 72%"        | "You're 72% ready. Focus on Strategy Analysis." |
| **System Knows**   | Category scores only    | 847/1203 concepts mastered (hidden from user)   |

> **Design Principle:** BKT complexity is system-internal. Users see familiar KA-level progress (6 bars). The intelligence is invisible; the benefits (smarter questions, faster progress) are obvious.

### The Beta-Bernoulli Model

For each concept `c` and user `u`, we maintain a Beta distribution representing our belief about mastery:

```
P(mastery) ~ Beta(α, β)

Where:
- α = pseudo-count of "mastery evidence" (successes + prior)
- β = pseudo-count of "non-mastery evidence" (failures + prior)
- Mean = α / (α + β)
- Variance = αβ / ((α + β)² × (α + β + 1))
```

**Why Beta distribution?**

- Conjugate prior for Bernoulli likelihood → closed-form updates
- Naturally bounded [0, 1] for probability
- Two parameters capture both estimate and confidence
- Computationally efficient

### The BKT Update Equations

When a user answers a question about concept `c`:

```
Parameters:
- P(L) = Prior P(mastery) = α / (α + β)
- P(G) = P(correct | not mastered) = guess rate ≈ 0.25 for 4-choice
- P(S) = P(incorrect | mastered) = slip rate ≈ 0.10

On CORRECT answer:
  P(L|correct) = P(correct|L) × P(L) / P(correct)
               = (1 - P(S)) × P(L) / [(1 - P(S)) × P(L) + P(G) × (1 - P(L))]

On INCORRECT answer:
  P(L|incorrect) = P(incorrect|L) × P(L) / P(incorrect)
                 = P(S) × P(L) / [P(S) × P(L) + (1 - P(G)) × (1 - P(L))]
```

**Beta parameter updates (moment matching):**

```python
def update_belief(alpha: float, beta: float, is_correct: bool,
                  slip: float = 0.10, guess: float = 0.25) -> Tuple[float, float]:
    """Update Beta parameters after observing a response."""
    p_mastered = alpha / (alpha + beta)

    if is_correct:
        p_correct = (1 - slip) * p_mastered + guess * (1 - p_mastered)
        posterior_mastered = (1 - slip) * p_mastered / p_correct
    else:
        p_incorrect = slip * p_mastered + (1 - guess) * (1 - p_mastered)
        posterior_mastered = slip * p_mastered / p_incorrect

    # Update using evidence weighting
    evidence_weight = 1.0  # Can be adjusted based on question quality
    new_alpha = alpha + posterior_mastered * evidence_weight
    new_beta = beta + (1 - posterior_mastered) * evidence_weight

    return new_alpha, new_beta
```

---
