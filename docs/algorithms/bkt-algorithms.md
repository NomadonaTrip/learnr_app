# Bayesian Knowledge Tracing Algorithms

This document specifies the core algorithms for the BKT-first architecture. All algorithms use the Beta-Bernoulli model for computational efficiency and closed-form updates.

---

## 1. Belief State Representation

### Beta Distribution

Each concept's mastery is represented as a Beta distribution:

```
P(mastery | evidence) ~ Beta(α, β)
```

**Properties:**
- **Mean (expected mastery):** `μ = α / (α + β)`
- **Variance:** `σ² = αβ / ((α + β)² × (α + β + 1))`
- **Mode:** `(α - 1) / (α + β - 2)` for α, β > 1
- **Confidence:** `(α + β) / (α + β + k)` where k is a scaling constant

**Initial Prior:**
- `α = 1, β = 1` (Uniform[0,1] - no prior knowledge)
- Alternative informative prior: `α = 2, β = 2` (slight bias toward 0.5)

```python
from dataclasses import dataclass
from typing import Optional
import math

@dataclass
class BeliefState:
    alpha: float
    beta: float
    response_count: int = 0
    last_response_at: Optional[str] = None

    @property
    def mean(self) -> float:
        """Expected probability of mastery."""
        return self.alpha / (self.alpha + self.beta)

    @property
    def variance(self) -> float:
        """Variance of the belief distribution."""
        ab = self.alpha + self.beta
        return (self.alpha * self.beta) / (ab * ab * (ab + 1))

    @property
    def confidence(self) -> float:
        """Confidence in our estimate (0 to 1)."""
        # Asymptotic approach to 1 as evidence increases
        return (self.alpha + self.beta) / (self.alpha + self.beta + 2)

    @property
    def entropy(self) -> float:
        """Uncertainty in bits (higher = more uncertain)."""
        return beta_entropy(self.alpha, self.beta)

    def classify(self, mastery_threshold: float = 0.8,
                 gap_threshold: float = 0.5,
                 confidence_threshold: float = 0.7) -> str:
        """Classify belief state as mastered, gap, or uncertain."""
        if self.confidence < confidence_threshold:
            return "uncertain"
        if self.mean >= mastery_threshold:
            return "mastered"
        if self.mean <= gap_threshold:
            return "gap"
        return "uncertain"  # Borderline


def beta_entropy(alpha: float, beta: float) -> float:
    """
    Calculate entropy of Beta(alpha, beta) distribution.

    Uses the formula:
    H(Beta(α,β)) = ln(B(α,β)) - (α-1)ψ(α) - (β-1)ψ(β) + (α+β-2)ψ(α+β)

    where B is the beta function and ψ is the digamma function.
    """
    from scipy.special import betaln, digamma

    return (betaln(alpha, beta)
            - (alpha - 1) * digamma(alpha)
            - (beta - 1) * digamma(beta)
            + (alpha + beta - 2) * digamma(alpha + beta))
```

---

## 2. Bayesian Update Algorithm

### Standard BKT Update

When a user answers a question about concept(s), update beliefs using Bayes' theorem.

**Parameters:**
- `slip (s)`: P(incorrect | mastered) ≈ 0.10 (careless errors)
- `guess (g)`: P(correct | not mastered) ≈ 0.25 (lucky guesses, 4-choice)

**Update Equations:**

For a **correct** response:
```
P(L|correct) = P(correct|L) × P(L) / P(correct)
             = (1 - s) × P(L) / [(1 - s) × P(L) + g × (1 - P(L))]
```

For an **incorrect** response:
```
P(L|incorrect) = P(incorrect|L) × P(L) / P(incorrect)
               = s × P(L) / [s × P(L) + (1 - g) × (1 - P(L))]
```

**Beta Parameter Update:**

```python
def bayesian_update(
    belief: BeliefState,
    is_correct: bool,
    slip: float = 0.10,
    guess: float = 0.25,
    evidence_weight: float = 1.0
) -> BeliefState:
    """
    Update belief state after observing a response.

    Args:
        belief: Current belief state
        is_correct: Whether the response was correct
        slip: P(incorrect | mastered)
        guess: P(correct | not mastered)
        evidence_weight: How much to weight this evidence (default 1.0)

    Returns:
        Updated belief state
    """
    # Current probability of mastery
    p_mastered = belief.mean

    if is_correct:
        # P(correct) = (1-s) × P(L) + g × (1-P(L))
        p_correct = (1 - slip) * p_mastered + guess * (1 - p_mastered)

        # P(L | correct) = (1-s) × P(L) / P(correct)
        posterior_mastered = (1 - slip) * p_mastered / p_correct
    else:
        # P(incorrect) = s × P(L) + (1-g) × (1-P(L))
        p_incorrect = slip * p_mastered + (1 - guess) * (1 - p_mastered)

        # P(L | incorrect) = s × P(L) / P(incorrect)
        posterior_mastered = slip * p_mastered / p_incorrect

    # Update Beta parameters
    # Evidence weight allows for weighting by question quality/relevance
    new_alpha = belief.alpha + posterior_mastered * evidence_weight
    new_beta = belief.beta + (1 - posterior_mastered) * evidence_weight

    return BeliefState(
        alpha=new_alpha,
        beta=new_beta,
        response_count=belief.response_count + 1
    )
```

### Multi-Concept Update

When a question tests multiple concepts, update all of them:

```python
def update_beliefs_for_question(
    beliefs: dict[str, BeliefState],
    question: Question,
    is_correct: bool
) -> dict[str, BeliefState]:
    """
    Update beliefs for all concepts tested by a question.

    Args:
        beliefs: Dict mapping concept_id to BeliefState
        question: Question with concept_ids and IRT parameters
        is_correct: Whether the response was correct

    Returns:
        Dict of updated beliefs (only for affected concepts)
    """
    updates = {}

    for concept_id in question.concept_ids:
        if concept_id not in beliefs:
            continue

        belief = beliefs[concept_id]

        # Get relevance weight (how directly this question tests the concept)
        relevance = question.concept_relevance.get(concept_id, 1.0)

        updated = bayesian_update(
            belief=belief,
            is_correct=is_correct,
            slip=question.slip_rate,
            guess=question.guess_rate,
            evidence_weight=relevance
        )

        updates[concept_id] = updated

    return updates
```

### Prerequisite Propagation

Correct answers provide weak evidence for prerequisite concepts:

```python
def propagate_to_prerequisites(
    beliefs: dict[str, BeliefState],
    concept_id: str,
    is_correct: bool,
    prereq_graph: dict[str, list[str]],
    propagation_weight: float = 0.3
) -> dict[str, BeliefState]:
    """
    Propagate belief updates to prerequisite concepts.

    Intuition: If you got a question right about an advanced concept,
    you probably know its prerequisites too (weak evidence).

    Args:
        beliefs: Current belief states
        concept_id: Concept that was directly tested
        is_correct: Whether response was correct
        prereq_graph: Dict mapping concept_id to list of prerequisite concept_ids
        propagation_weight: How much to weight prerequisite updates (0.0-1.0)

    Returns:
        Dict of updated prerequisite beliefs
    """
    if not is_correct:
        # Don't propagate incorrect answers (could be lucky guess on advanced)
        return {}

    updates = {}
    prerequisites = prereq_graph.get(concept_id, [])

    for prereq_id in prerequisites:
        if prereq_id not in beliefs:
            continue

        belief = beliefs[prereq_id]

        # Weak positive update for prerequisites
        new_alpha = belief.alpha + propagation_weight
        new_beta = belief.beta  # No change to beta

        updates[prereq_id] = BeliefState(
            alpha=new_alpha,
            beta=new_beta,
            response_count=belief.response_count  # Don't increment
        )

    return updates
```

---

## 3. Question Selection Algorithm

### Maximum Information Gain

Select questions that maximize expected reduction in entropy:

```python
from typing import List, Tuple
import math

def select_question_by_info_gain(
    beliefs: dict[str, BeliefState],
    questions: List[Question],
    exclude_ids: set[str] = None,
    top_k: int = 1
) -> List[Tuple[Question, float]]:
    """
    Select question(s) that maximize expected information gain.

    Information Gain = H(beliefs_before) - E[H(beliefs_after)]

    Args:
        beliefs: Current belief states for all concepts
        questions: Available questions to choose from
        exclude_ids: Question IDs to exclude (recently asked)
        top_k: Number of top questions to return

    Returns:
        List of (question, expected_info_gain) tuples, sorted by gain descending
    """
    exclude_ids = exclude_ids or set()

    scored_questions = []

    for question in questions:
        if question.id in exclude_ids:
            continue

        # Get beliefs for concepts this question tests
        concept_beliefs = [
            beliefs[c_id] for c_id in question.concept_ids
            if c_id in beliefs
        ]

        if not concept_beliefs:
            continue

        info_gain = calculate_expected_info_gain(
            concept_beliefs=concept_beliefs,
            slip=question.slip_rate,
            guess=question.guess_rate
        )

        scored_questions.append((question, info_gain))

    # Sort by info gain descending
    scored_questions.sort(key=lambda x: x[1], reverse=True)

    return scored_questions[:top_k]


def calculate_expected_info_gain(
    concept_beliefs: List[BeliefState],
    slip: float,
    guess: float
) -> float:
    """
    Calculate expected information gain from asking a question.

    Args:
        concept_beliefs: Beliefs for concepts tested by this question
        slip: Question's slip rate
        guess: Question's guess rate

    Returns:
        Expected reduction in total entropy (in nats)
    """
    # Current entropy
    current_entropy = sum(b.entropy for b in concept_beliefs)

    # Average mastery probability
    avg_mastery = sum(b.mean for b in concept_beliefs) / len(concept_beliefs)

    # Probability of correct response
    p_correct = (1 - slip) * avg_mastery + guess * (1 - avg_mastery)

    # Simulate beliefs after correct response
    beliefs_if_correct = [
        bayesian_update(b, is_correct=True, slip=slip, guess=guess)
        for b in concept_beliefs
    ]
    entropy_if_correct = sum(b.entropy for b in beliefs_if_correct)

    # Simulate beliefs after incorrect response
    beliefs_if_incorrect = [
        bayesian_update(b, is_correct=False, slip=slip, guess=guess)
        for b in concept_beliefs
    ]
    entropy_if_incorrect = sum(b.entropy for b in beliefs_if_incorrect)

    # Expected posterior entropy
    expected_posterior_entropy = (
        p_correct * entropy_if_correct +
        (1 - p_correct) * entropy_if_incorrect
    )

    # Information gain = current entropy - expected posterior entropy
    info_gain = current_entropy - expected_posterior_entropy

    return max(0, info_gain)  # Ensure non-negative
```

### Diagnostic Question Selection

For initial diagnostic, maximize concept coverage:

```python
def select_diagnostic_questions(
    concepts: List[Concept],
    questions: List[Question],
    target_count: int = 15,
    max_per_ka: int = 4
) -> List[Question]:
    """
    Select questions for initial diagnostic that maximize concept coverage.

    Strategy: Greedy selection prioritizing:
    1. Concepts not yet covered
    2. Question discrimination (informativeness)
    3. Knowledge area balance

    Args:
        concepts: All concepts in corpus
        questions: Available questions
        target_count: Number of questions to select
        max_per_ka: Maximum questions per knowledge area

    Returns:
        Selected questions in randomized order
    """
    from collections import defaultdict
    import random

    selected = []
    covered_concepts = set()
    ka_counts = defaultdict(int)

    # Create index of questions by concept
    questions_by_concept = defaultdict(list)
    for q in questions:
        for c_id in q.concept_ids:
            questions_by_concept[c_id].append(q)

    available = set(q.id for q in questions)

    while len(selected) < target_count and available:
        best_question = None
        best_score = -float('inf')

        for q in questions:
            if q.id not in available:
                continue

            # Skip if KA quota reached
            if ka_counts[q.ka_id] >= max_per_ka:
                continue

            # Score: new concepts covered
            new_concepts = len(set(q.concept_ids) - covered_concepts)

            # Bonus for question discrimination
            discrimination_bonus = q.discrimination * 2

            # Bonus for KA balance (prefer underrepresented KAs)
            ka_balance_bonus = (max_per_ka - ka_counts[q.ka_id])

            score = new_concepts * 10 + discrimination_bonus + ka_balance_bonus

            if score > best_score:
                best_score = score
                best_question = q

        if best_question is None:
            break

        selected.append(best_question)
        covered_concepts.update(best_question.concept_ids)
        ka_counts[best_question.ka_id] += 1
        available.remove(best_question.id)

    # Randomize order to avoid clustering by concept
    random.shuffle(selected)

    return selected
```

---

## 4. Coverage Analysis

### Concept Classification

```python
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class CoverageReport:
    total_concepts: int
    mastered_count: int
    gap_count: int
    uncertain_count: int
    coverage_percentage: float  # (mastered + gap) / total
    mastered_concepts: List[str]
    gap_concepts: List[str]
    uncertain_concepts: List[str]
    by_knowledge_area: Dict[str, dict]
    estimated_questions_remaining: int


def analyze_coverage(
    beliefs: dict[str, BeliefState],
    concepts: List[Concept],
    mastery_threshold: float = 0.8,
    gap_threshold: float = 0.5,
    confidence_threshold: float = 0.7
) -> CoverageReport:
    """
    Analyze coverage across all concepts.

    Args:
        beliefs: Current belief states
        concepts: All concepts in corpus
        mastery_threshold: P(mastery) above which concept is "mastered"
        gap_threshold: P(mastery) below which concept is "gap"
        confidence_threshold: Minimum confidence to classify

    Returns:
        CoverageReport with full analysis
    """
    mastered = []
    gaps = []
    uncertain = []

    ka_stats = {}

    for concept in concepts:
        belief = beliefs.get(concept.id)

        if belief is None:
            uncertain.append(concept.id)
            continue

        status = belief.classify(mastery_threshold, gap_threshold, confidence_threshold)

        if status == "mastered":
            mastered.append(concept.id)
        elif status == "gap":
            gaps.append(concept.id)
        else:
            uncertain.append(concept.id)

        # Track by KA
        if concept.ka_id not in ka_stats:
            ka_stats[concept.ka_id] = {"mastered": 0, "gaps": 0, "uncertain": 0, "total": 0}
        ka_stats[concept.ka_id]["total"] += 1
        ka_stats[concept.ka_id][status if status in ["mastered", "gaps"] else "uncertain"] += 1

    total = len(concepts)
    classified = len(mastered) + len(gaps)

    # Estimate remaining questions
    # Heuristic: ~4 questions per uncertain concept, 2 concepts per question
    estimated_remaining = int(len(uncertain) * 4 / 2)

    return CoverageReport(
        total_concepts=total,
        mastered_count=len(mastered),
        gap_count=len(gaps),
        uncertain_count=len(uncertain),
        coverage_percentage=classified / total if total > 0 else 0,
        mastered_concepts=mastered,
        gap_concepts=gaps,
        uncertain_concepts=uncertain,
        by_knowledge_area=ka_stats,
        estimated_questions_remaining=estimated_remaining
    )
```

---

## 5. Session Termination

### Diminishing Returns Detection

```python
def should_suggest_session_end(
    session_responses: List[dict],
    min_questions: int = 10,
    max_questions: int = 50,
    diminishing_threshold: float = 0.3
) -> Tuple[bool, str]:
    """
    Determine if session should suggest ending due to diminishing returns.

    Args:
        session_responses: List of response dicts with 'info_gain_actual' field
        min_questions: Minimum questions before suggesting end
        max_questions: Hard cap on questions per session
        diminishing_threshold: Ratio of recent to average gain to trigger suggestion

    Returns:
        (should_suggest, reason)
    """
    n = len(session_responses)

    # Hard cap
    if n >= max_questions:
        return True, "maximum_questions_reached"

    # Minimum questions
    if n < min_questions:
        return False, ""

    # Calculate info gains
    gains = [r.get("info_gain_actual", 0) for r in session_responses]

    if not gains:
        return False, ""

    # Average gain for session
    avg_gain = sum(gains) / len(gains)

    if avg_gain <= 0:
        return True, "zero_average_gain"

    # Recent gain (last 5 questions)
    recent_gains = gains[-5:]
    recent_avg = sum(recent_gains) / len(recent_gains)

    # Check for diminishing returns
    if recent_avg < avg_gain * diminishing_threshold:
        return True, "diminishing_returns"

    return False, ""
```

---

## 6. IRT Parameter Calibration

### Online Calibration

Update question parameters based on observed responses:

```python
def calibrate_question_parameters(
    question: Question,
    responses: List[dict],
    learning_rate: float = 0.1
) -> Question:
    """
    Calibrate IRT parameters based on observed responses.

    Uses a simple online update:
    - Difficulty adjusted based on observed vs expected accuracy
    - Discrimination estimated from response variance

    Args:
        question: Question to calibrate
        responses: List of response dicts with 'is_correct' and 'user_mastery' fields
        learning_rate: How quickly to adjust parameters

    Returns:
        Question with updated parameters
    """
    if len(responses) < 10:
        # Not enough data to calibrate
        return question

    # Observed accuracy
    correct_count = sum(1 for r in responses if r["is_correct"])
    observed_accuracy = correct_count / len(responses)

    # Average user mastery when answering this question
    avg_mastery = sum(r.get("user_mastery", 0.5) for r in responses) / len(responses)

    # Expected accuracy given current parameters
    expected_accuracy = (1 - question.slip_rate) * avg_mastery + question.guess_rate * (1 - avg_mastery)

    # Adjust difficulty
    # If observed < expected, question is harder than estimated
    difficulty_adjustment = (expected_accuracy - observed_accuracy) * learning_rate
    new_difficulty = max(0, min(1, question.difficulty + difficulty_adjustment))

    # Update question
    question.difficulty = new_difficulty
    question.times_asked = len(responses)
    question.times_correct = correct_count

    return question
```

---

## 7. Performance Considerations

### Batch Operations

```python
async def batch_update_beliefs(
    user_id: str,
    updates: dict[str, BeliefState],
    db_session
) -> None:
    """
    Batch update multiple belief states in single transaction.

    Uses bulk update for efficiency.
    """
    from sqlalchemy import update
    from models import BeliefStateModel

    update_values = [
        {
            "user_id": user_id,
            "concept_id": concept_id,
            "alpha": belief.alpha,
            "beta": belief.beta,
            "response_count": belief.response_count,
            "updated_at": datetime.utcnow()
        }
        for concept_id, belief in updates.items()
    ]

    # Use upsert pattern
    stmt = insert(BeliefStateModel).values(update_values)
    stmt = stmt.on_conflict_do_update(
        index_elements=["user_id", "concept_id"],
        set_={
            "alpha": stmt.excluded.alpha,
            "beta": stmt.excluded.beta,
            "response_count": stmt.excluded.response_count,
            "updated_at": stmt.excluded.updated_at
        }
    )

    await db_session.execute(stmt)
    await db_session.commit()
```

### Caching

```python
from functools import lru_cache
from typing import FrozenSet

@lru_cache(maxsize=1000)
def cached_beta_entropy(alpha: float, beta: float) -> float:
    """Cached entropy calculation for common (alpha, beta) pairs."""
    # Round to 2 decimal places for cache efficiency
    return beta_entropy(round(alpha, 2), round(beta, 2))


@lru_cache(maxsize=100)
def cached_prerequisite_chain(concept_id: str) -> FrozenSet[str]:
    """Cache prerequisite chains (rarely change)."""
    # Implementation would query DB and cache result
    pass
```

---

## References

1. **Corbett & Anderson (1994)** - Original BKT paper
2. **Yudelson et al. (2013)** - Individualized BKT
3. **Baker et al. (2008)** - BKT with contextual guess and slip
4. **Piech et al. (2015)** - Deep Knowledge Tracing (for future reference)

---

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-11-27 | 1.0 | Initial BKT algorithm specification | Sarah (Product Owner) |
