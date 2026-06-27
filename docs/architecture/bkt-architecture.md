# Bayesian Knowledge Tracing Architecture

## Status

**APPROVED** - Aligned with Multi-Course Architecture (multi-course-architecture.md)

## Executive Summary

This document defines the Bayesian Knowledge Tracing (BKT) architecture that forms the core value proposition of LearnR. Unlike traditional quiz applications that track coarse competency scores, LearnR uses probabilistic inference to systematically discover knowledge gaps across a corpus and confirm mastery with mathematical certainty.

**Core Value Proposition:** "We ask the minimum questions necessary to map exactly what you know and don't know."

**Multi-Course Design Note:** The BKT engine is **course-agnostic**. All algorithms in this document work identically across any course (CBAP, PSM1, CFA, etc.). Course scoping happens at the service/repository layer where concepts and questions are filtered by `course_id`. The BKT math operates on concept-belief pairs regardless of which course they belong to.

---

## Mathematical Primer for AI Agents

> **Purpose:** This section explains the statistical foundations of BKT for AI coding agents that may not have deep statistics background. Understanding these concepts is essential for implementing the algorithms correctly.

### Probability Distributions 101

A **probability distribution** describes all possible values a random variable can take and how likely each value is.

**Example:** If we flip a coin, the outcome is a random variable. A fair coin has P(heads) = 0.5 and P(tails) = 0.5.

### The Beta Distribution

The **Beta distribution** is a continuous probability distribution defined on the interval [0, 1]. It's perfect for modeling probabilities (like "probability of mastery").

**Parameters:**
- **α (alpha):** "Success" pseudo-count. Higher α → distribution shifts right (toward 1)
- **β (beta):** "Failure" pseudo-count. Higher β → distribution shifts left (toward 0)

**Key Formulas:**
```python
# Mean (expected value) - our best estimate of the probability
mean = alpha / (alpha + beta)

# Variance - how spread out (uncertain) the distribution is
variance = (alpha * beta) / ((alpha + beta)**2 * (alpha + beta + 1))

# Mode (peak) - most likely value (only defined when alpha, beta > 1)
mode = (alpha - 1) / (alpha + beta - 2)  # if alpha > 1 and beta > 1
```

**Intuitive Examples:**

| α | β | Mean | Interpretation |
|---|---|------|----------------|
| 1 | 1 | 0.50 | "I know nothing" (uniform distribution) |
| 2 | 2 | 0.50 | "Probably 50%, somewhat confident" |
| 8 | 2 | 0.80 | "Probably 80%, fairly confident" |
| 20 | 5 | 0.80 | "Probably 80%, very confident" |
| 1 | 9 | 0.10 | "Probably 10%, fairly confident" |

**Visual Intuition:**
```
Beta(1,1) - Flat line (uniform, know nothing)
Beta(2,2) - Bell curve centered at 0.5
Beta(8,2) - Bell curve shifted right, peaked at ~0.8
Beta(2,8) - Bell curve shifted left, peaked at ~0.2
```

### Why Beta Distribution for Knowledge?

1. **Bounded [0,1]:** Probabilities must be between 0 and 1. Beta naturally satisfies this.

2. **Conjugate Prior:** When you observe binary outcomes (correct/incorrect), the Beta distribution updates to another Beta distribution. This is called "conjugacy" and makes math simple:
   ```
   Prior: Beta(α, β)
   Observe: Success
   Posterior: Beta(α+1, β)  # Just add 1 to alpha!

   Prior: Beta(α, β)
   Observe: Failure
   Posterior: Beta(α, β+1)  # Just add 1 to beta!
   ```

3. **Two Parameters:** α and β together capture both our *estimate* (mean) and our *confidence* (higher α+β = more confident).

### Bayes' Theorem

**Bayes' Theorem** lets us update our beliefs based on new evidence:

```
P(Hypothesis | Evidence) = P(Evidence | Hypothesis) × P(Hypothesis) / P(Evidence)
```

In BKT context:
- **Hypothesis:** "Student has mastered this concept"
- **Evidence:** "Student answered correctly" or "Student answered incorrectly"

**The BKT Update (Simplified):**

```python
# Setup
P_mastered = alpha / (alpha + beta)  # Prior belief in mastery
P_guess = 0.25  # P(correct | NOT mastered) - lucky guess on 4-choice
P_slip = 0.10   # P(incorrect | mastered) - careless mistake

# If student answers CORRECTLY:
# P(mastered | correct) = P(correct | mastered) × P(mastered) / P(correct)

P_correct_if_mastered = 1 - P_slip  # = 0.90
P_correct_if_not_mastered = P_guess  # = 0.25
P_correct = P_correct_if_mastered * P_mastered + P_correct_if_not_mastered * (1 - P_mastered)

P_mastered_given_correct = (P_correct_if_mastered * P_mastered) / P_correct

# If student answers INCORRECTLY:
P_incorrect_if_mastered = P_slip  # = 0.10
P_incorrect_if_not_mastered = 1 - P_guess  # = 0.75
P_incorrect = P_incorrect_if_mastered * P_mastered + P_incorrect_if_not_mastered * (1 - P_mastered)

P_mastered_given_incorrect = (P_incorrect_if_mastered * P_mastered) / P_incorrect
```

### Entropy and Information Gain

**Entropy** measures uncertainty. High entropy = high uncertainty = we don't know the answer.

```python
from scipy.special import betaln, digamma

def beta_entropy(alpha: float, beta: float) -> float:
    """
    Calculate entropy of Beta(alpha, beta) distribution.

    Higher entropy = more uncertainty about the true probability.
    Lower entropy = more confident in our estimate.

    Range: 0 (certain) to ~0.693 (maximum uncertainty at alpha=beta=1)
    """
    return (
        betaln(alpha, beta)  # Log of Beta function
        - (alpha - 1) * digamma(alpha)  # Digamma = derivative of log-gamma
        - (beta - 1) * digamma(beta)
        + (alpha + beta - 2) * digamma(alpha + beta)
    )

# Examples:
# beta_entropy(1, 1) ≈ 0.693  (maximum uncertainty - uniform distribution)
# beta_entropy(10, 10) ≈ 0.35  (moderate confidence at 50%)
# beta_entropy(50, 50) ≈ 0.16  (high confidence at 50%)
# beta_entropy(90, 10) ≈ 0.21  (high confidence at 90%)
```

**Information Gain** = How much entropy decreases after asking a question.

```python
def expected_info_gain(current_entropy: float, p_correct: float,
                       entropy_if_correct: float, entropy_if_incorrect: float) -> float:
    """
    Expected reduction in entropy from asking a question.

    Higher info gain = more valuable question to ask.
    """
    expected_posterior_entropy = (
        p_correct * entropy_if_correct +
        (1 - p_correct) * entropy_if_incorrect
    )
    return current_entropy - expected_posterior_entropy
```

### Confidence Calculation

We use a simple heuristic for "confidence" based on total evidence:

```python
def calculate_confidence(alpha: float, beta: float) -> float:
    """
    Confidence in our estimate based on amount of evidence.

    Intuition: More data (higher alpha + beta) = more confident.

    Formula approaches 1.0 asymptotically.
    At alpha+beta=2 (prior only): confidence = 0.50
    At alpha+beta=12 (10 observations): confidence = 0.86
    At alpha+beta=22 (20 observations): confidence = 0.92
    """
    total_evidence = alpha + beta
    return total_evidence / (total_evidence + 2)
```

### Complete Worked Example

**Scenario:** New user, concept "Stakeholder Analysis", first question.

```python
# Initial state (uninformative prior)
alpha, beta = 1.0, 1.0
mean = 1.0 / 2.0  # = 0.50 (no idea if they know it)
confidence = 2.0 / 4.0  # = 0.50 (low confidence)

# Question parameters
slip = 0.10  # 10% chance of careless mistake
guess = 0.25  # 25% chance of lucky guess (4 choices)

# Student answers CORRECTLY
p_correct = (1 - slip) * 0.50 + guess * 0.50  # = 0.90*0.5 + 0.25*0.5 = 0.575
posterior = (1 - slip) * 0.50 / p_correct  # = 0.45 / 0.575 = 0.783

# Update Beta parameters
new_alpha = 1.0 + 0.783  # = 1.783
new_beta = 1.0 + (1 - 0.783)  # = 1.217

# New state
new_mean = 1.783 / (1.783 + 1.217)  # = 0.594 (increased!)
new_confidence = 3.0 / 5.0  # = 0.60 (slightly more confident)

# After 5 more correct answers, might reach:
# alpha ≈ 8, beta ≈ 2
# mean = 0.80 (likely mastered)
# confidence = 0.83 (fairly confident)
# Status: MASTERED (mean > 0.8 AND confidence > 0.7)
```

### Summary for Implementation

| Concept | Formula | When to Use |
|---------|---------|-------------|
| Mean (mastery probability) | `α / (α + β)` | Display progress, classify status |
| Confidence | `(α + β) / (α + β + 2)` | Determine if we have enough data |
| Entropy | `scipy.special` formula | Question selection (info gain) |
| Bayesian Update | See `_bayesian_update()` | After each answer |
| Info Gain | Current entropy - Expected posterior entropy | Rank questions |

---

## Fundamental Concepts

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

## Data Model

### Core Entities

```
┌─────────────────────────────────────────────────────────────────────┐
│                         KNOWLEDGE GRAPH                             │
├─────────────────────────────────────────────────────────────────────┤
│  concepts                                                           │
│  ├── concept_id (PK)                                               │
│  ├── name                                                          │
│  ├── description                                                   │
│  ├── babok_section_ref (e.g., "3.2.1")                            │
│  ├── knowledge_area (FK) - for aggregation/display                 │
│  ├── difficulty_estimate (0.0-1.0)                                 │
│  ├── prerequisite_depth (int) - distance from root concepts        │
│  └── created_at, updated_at                                        │
│                                                                     │
│  concept_prerequisites (DAG edges)                                  │
│  ├── concept_id (FK)                                               │
│  ├── prerequisite_concept_id (FK)                                  │
│  └── strength (0.0-1.0) - how strongly prerequisite is required    │
│                                                                     │
│  question_concepts (many-to-many)                                   │
│  ├── question_id (FK)                                              │
│  ├── concept_id (FK)                                               │
│  └── relevance (0.0-1.0) - how directly question tests concept     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                         BELIEF STATE                                │
├─────────────────────────────────────────────────────────────────────┤
│  belief_states                                                      │
│  ├── id (PK)                                                       │
│  ├── user_id (FK)                                                  │
│  ├── concept_id (FK)                                               │
│  ├── alpha (float) - Beta distribution parameter                   │
│  ├── beta (float) - Beta distribution parameter                    │
│  ├── last_response_at (timestamp) - for decay/recency              │
│  ├── response_count (int) - questions answered for this concept    │
│  ├── created_at, updated_at                                        │
│  └── UNIQUE(user_id, concept_id)                                   │
│                                                                     │
│  Derived properties (computed, not stored):                         │
│  ├── mean = alpha / (alpha + beta)                                 │
│  ├── confidence = (alpha + beta) / (alpha + beta + 10)             │
│  ├── entropy = beta_distribution(alpha, beta).entropy()            │
│  └── status = 'mastered' | 'gap' | 'uncertain'                     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                      QUESTION BANK                                  │
├─────────────────────────────────────────────────────────────────────┤
│  questions                                                          │
│  ├── question_id (PK)                                              │
│  ├── question_text                                                 │
│  ├── options (JSONB) - A, B, C, D                                  │
│  ├── correct_answer                                                │
│  ├── explanation                                                   │
│  ├── knowledge_area (FK) - for backward compatibility/display      │
│  ├── difficulty (float, 0.0-1.0) - IRT difficulty parameter        │
│  ├── discrimination (float) - IRT discrimination parameter         │
│  ├── guess_rate (float, default 0.25) - P(correct | not mastered)  │
│  ├── slip_rate (float, default 0.10) - P(incorrect | mastered)     │
│  ├── times_asked (int) - for calibration                           │
│  ├── times_correct (int) - for calibration                         │
│  └── created_at, updated_at                                        │
│                                                                     │
│  Note: Each question linked to 1-5 concepts via question_concepts   │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                      RESPONSE LOG                                   │
├─────────────────────────────────────────────────────────────────────┤
│  responses                                                          │
│  ├── response_id (PK)                                              │
│  ├── user_id (FK)                                                  │
│  ├── question_id (FK)                                              │
│  ├── session_id (FK)                                               │
│  ├── selected_answer                                               │
│  ├── is_correct (bool)                                             │
│  ├── time_taken_ms (int)                                           │
│  ├── belief_updates (JSONB) - snapshot of concept updates made     │
│  └── created_at                                                    │
└─────────────────────────────────────────────────────────────────────┘
```

### Entity Relationship Diagram

```
                    ┌──────────────┐
                    │    users     │
                    └──────┬───────┘
                           │
                           │ 1:N
                           ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   concepts   │◄───│ belief_states│    │   sessions   │
└──────┬───────┘    └──────────────┘    └──────┬───────┘
       │                                        │
       │ N:M                                    │ 1:N
       ▼                                        ▼
┌──────────────┐                        ┌──────────────┐
│  questions   │◄───────────────────────│  responses   │
└──────────────┘                        └──────────────┘
       │
       │ N:M (question_concepts)
       ▼
┌──────────────┐
│   concepts   │
└──────────────┘
```

---

## Core Algorithms

### 1. Initial Belief Seeding

When a user first enters the system, initialize beliefs for ALL concepts:

```python
async def initialize_beliefs(user_id: UUID, concepts: List[Concept]) -> None:
    """
    Initialize belief states for a new user.

    Uses uninformative prior: Beta(1, 1) = Uniform[0, 1]
    This represents "we know nothing about this user's knowledge."
    """
    belief_states = []

    for concept in concepts:
        belief_states.append(BeliefState(
            user_id=user_id,
            concept_id=concept.id,
            alpha=1.0,  # Uninformative prior
            beta=1.0,   # Uninformative prior
            response_count=0
        ))

    await belief_repository.bulk_create(belief_states)
```

### 2. Optimal Question Selection

Select questions that maximize expected information gain:

```python
class QuestionSelector:
    """
    Selects questions to maximize learning efficiency.

    Primary strategy: Maximum Expected Information Gain
    - Calculate entropy reduction for each candidate question
    - Select question with highest expected reduction

    Constraints:
    - Don't repeat recently asked questions (7-day window)
    - Prefer questions with calibrated parameters
    - Consider prerequisite relationships
    """

    def __init__(
        self,
        recency_window_days: int = 7,
        prerequisite_weight: float = 0.2
    ):
        self.recency_window_days = recency_window_days
        self.prerequisite_weight = prerequisite_weight

    async def select_next_question(
        self,
        user_id: UUID,
        beliefs: Dict[UUID, BeliefState],
        available_questions: List[Question],
        strategy: str = "max_info_gain"
    ) -> Question:
        """Select optimal next question."""

        # Filter out recently asked questions
        recent_question_ids = await self._get_recent_questions(user_id)
        candidates = [q for q in available_questions if q.id not in recent_question_ids]

        if not candidates:
            # Fallback: allow repeats if no fresh questions
            candidates = available_questions

        if strategy == "max_info_gain":
            return self._select_by_info_gain(candidates, beliefs)
        elif strategy == "max_uncertainty":
            return self._select_by_uncertainty(candidates, beliefs)
        elif strategy == "prerequisite_first":
            return self._select_by_prerequisites(candidates, beliefs)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

    def _select_by_info_gain(
        self,
        questions: List[Question],
        beliefs: Dict[UUID, BeliefState]
    ) -> Question:
        """Select question with maximum expected information gain."""
        best_question = None
        max_gain = -float('inf')

        for question in questions:
            gain = self._calculate_expected_info_gain(question, beliefs)

            # Bonus for prerequisite concepts (foundational knowledge)
            prereq_bonus = self._prerequisite_bonus(question, beliefs)
            adjusted_gain = gain + self.prerequisite_weight * prereq_bonus

            if adjusted_gain > max_gain:
                max_gain = adjusted_gain
                best_question = question

        return best_question

    def _calculate_expected_info_gain(
        self,
        question: Question,
        beliefs: Dict[UUID, BeliefState]
    ) -> float:
        """
        Calculate expected reduction in total entropy.

        Info Gain = H(beliefs) - E[H(beliefs | response)]
                  = H(beliefs) - [P(correct) × H(beliefs|correct) +
                                  P(incorrect) × H(beliefs|incorrect)]
        """
        # Current entropy for concepts this question tests
        current_entropy = sum(
            self._belief_entropy(beliefs[c_id])
            for c_id in question.concept_ids
            if c_id in beliefs
        )

        # Predict response probability
        p_correct = self._predict_correct_probability(question, beliefs)

        # Simulate belief updates for each outcome
        beliefs_if_correct = self._simulate_update(question, beliefs, is_correct=True)
        beliefs_if_incorrect = self._simulate_update(question, beliefs, is_correct=False)

        entropy_if_correct = sum(
            self._belief_entropy(beliefs_if_correct[c_id])
            for c_id in question.concept_ids
            if c_id in beliefs_if_correct
        )

        entropy_if_incorrect = sum(
            self._belief_entropy(beliefs_if_incorrect[c_id])
            for c_id in question.concept_ids
            if c_id in beliefs_if_incorrect
        )

        expected_posterior_entropy = (
            p_correct * entropy_if_correct +
            (1 - p_correct) * entropy_if_incorrect
        )

        return current_entropy - expected_posterior_entropy

    def _belief_entropy(self, belief: BeliefState) -> float:
        """Calculate entropy of a Beta distribution."""
        from scipy.special import betaln, digamma
        a, b = belief.alpha, belief.beta
        return (
            betaln(a, b) -
            (a - 1) * digamma(a) -
            (b - 1) * digamma(b) +
            (a + b - 2) * digamma(a + b)
        )

    def _predict_correct_probability(
        self,
        question: Question,
        beliefs: Dict[UUID, BeliefState]
    ) -> float:
        """Predict probability of correct response given current beliefs."""
        # Average mastery across concepts tested by this question
        concept_beliefs = [beliefs[c_id] for c_id in question.concept_ids if c_id in beliefs]

        if not concept_beliefs:
            return 0.5  # No information

        avg_mastery = sum(b.alpha / (b.alpha + b.beta) for b in concept_beliefs) / len(concept_beliefs)

        # Apply IRT model
        p_correct = (1 - question.slip_rate) * avg_mastery + question.guess_rate * (1 - avg_mastery)

        return p_correct
```

### 3. Belief Update After Response

```python
class BeliefUpdater:
    """
    Updates belief states after observing a response.

    Handles:
    - Direct concept updates (concepts tested by the question)
    - Prerequisite propagation (if you know X, likely know prerequisites)
    - Multi-concept questions (partial credit model)
    """

    def __init__(
        self,
        default_slip: float = 0.10,
        default_guess: float = 0.25,
        prerequisite_propagation: float = 0.3
    ):
        self.default_slip = default_slip
        self.default_guess = default_guess
        self.prerequisite_propagation = prerequisite_propagation

    async def update_beliefs(
        self,
        user_id: UUID,
        question: Question,
        is_correct: bool,
        beliefs: Dict[UUID, BeliefState]
    ) -> Dict[UUID, BeliefState]:
        """
        Update beliefs for all concepts affected by this response.

        Returns updated beliefs dict.
        """
        updates = {}

        # 1. Update directly tested concepts
        for concept_id in question.concept_ids:
            if concept_id not in beliefs:
                continue

            belief = beliefs[concept_id]
            slip = question.slip_rate or self.default_slip
            guess = question.guess_rate or self.default_guess

            new_alpha, new_beta = self._bayesian_update(
                belief.alpha, belief.beta,
                is_correct, slip, guess
            )

            updates[concept_id] = BeliefState(
                user_id=user_id,
                concept_id=concept_id,
                alpha=new_alpha,
                beta=new_beta,
                response_count=belief.response_count + 1
            )

        # 2. Propagate to prerequisites (weaker update)
        if is_correct:
            # Correct answer provides weak evidence for prerequisites
            prerequisite_ids = await self._get_prerequisites(question.concept_ids)

            for prereq_id in prerequisite_ids:
                if prereq_id in updates or prereq_id not in beliefs:
                    continue

                belief = beliefs[prereq_id]
                # Weaker update for prerequisites
                propagated_alpha = belief.alpha + self.prerequisite_propagation
                propagated_beta = belief.beta

                updates[prereq_id] = BeliefState(
                    user_id=user_id,
                    concept_id=prereq_id,
                    alpha=propagated_alpha,
                    beta=propagated_beta,
                    response_count=belief.response_count  # Don't increment
                )

        # 3. Persist updates
        await self._persist_updates(updates)

        # 4. Return merged beliefs
        return {**beliefs, **updates}

    def _bayesian_update(
        self,
        alpha: float,
        beta: float,
        is_correct: bool,
        slip: float,
        guess: float
    ) -> Tuple[float, float]:
        """Core Bayesian update for Beta parameters."""
        p_mastered = alpha / (alpha + beta)

        if is_correct:
            p_correct = (1 - slip) * p_mastered + guess * (1 - p_mastered)
            posterior_mastered = (1 - slip) * p_mastered / p_correct
        else:
            p_incorrect = slip * p_mastered + (1 - guess) * (1 - p_mastered)
            posterior_mastered = slip * p_mastered / p_incorrect

        # Evidence-weighted update
        new_alpha = alpha + posterior_mastered
        new_beta = beta + (1 - posterior_mastered)

        return new_alpha, new_beta
```

### 4. Coverage Assessment

```python
class CoverageAnalyzer:
    """
    Analyzes corpus coverage and generates reports.

    Classifies each concept as:
    - MASTERED: High confidence of mastery (P(mastery) > 0.8, confidence > 0.7)
    - GAP: High confidence of non-mastery (P(mastery) < 0.5, confidence > 0.7)
    - UNCERTAIN: Need more data to classify
    """

    MASTERY_THRESHOLD = 0.8
    GAP_THRESHOLD = 0.5
    CONFIDENCE_THRESHOLD = 0.7

    def analyze_coverage(
        self,
        beliefs: Dict[UUID, BeliefState]
    ) -> CoverageReport:
        """Generate comprehensive coverage report."""
        mastered = []
        gaps = []
        uncertain = []

        for concept_id, belief in beliefs.items():
            mean = belief.alpha / (belief.alpha + belief.beta)
            confidence = self._calculate_confidence(belief)

            if confidence >= self.CONFIDENCE_THRESHOLD:
                if mean >= self.MASTERY_THRESHOLD:
                    mastered.append(ConceptStatus(
                        concept_id=concept_id,
                        status='mastered',
                        probability=mean,
                        confidence=confidence
                    ))
                elif mean <= self.GAP_THRESHOLD:
                    gaps.append(ConceptStatus(
                        concept_id=concept_id,
                        status='gap',
                        probability=mean,
                        confidence=confidence
                    ))
                else:
                    # Borderline - technically uncertain
                    uncertain.append(ConceptStatus(
                        concept_id=concept_id,
                        status='borderline',
                        probability=mean,
                        confidence=confidence
                    ))
            else:
                uncertain.append(ConceptStatus(
                    concept_id=concept_id,
                    status='uncertain',
                    probability=mean,
                    confidence=confidence
                ))

        total = len(beliefs)

        return CoverageReport(
            total_concepts=total,
            mastered_count=len(mastered),
            gap_count=len(gaps),
            uncertain_count=len(uncertain),
            coverage_percentage=len(mastered) / total if total > 0 else 0,
            confidence_percentage=(len(mastered) + len(gaps)) / total if total > 0 else 0,
            mastered=mastered,
            gaps=gaps,
            uncertain=uncertain,
            estimated_questions_to_coverage=self._estimate_remaining_questions(uncertain)
        )

    def _calculate_confidence(self, belief: BeliefState) -> float:
        """
        Calculate confidence in our estimate.

        Based on total evidence (alpha + beta).
        More responses = higher confidence.
        """
        total_evidence = belief.alpha + belief.beta
        # Asymptotic approach to 1.0
        # At 10 responses, confidence ≈ 0.83
        # At 20 responses, confidence ≈ 0.91
        return total_evidence / (total_evidence + 2)

    def _estimate_remaining_questions(
        self,
        uncertain: List[ConceptStatus]
    ) -> int:
        """
        Estimate questions needed to achieve full coverage.

        Heuristic: ~3-5 questions per uncertain concept,
        accounting for multi-concept questions.
        """
        if not uncertain:
            return 0

        # Average concepts per question ≈ 2
        # Average questions to resolve uncertainty ≈ 4
        return int(len(uncertain) * 4 / 2)
```

---

## Question Selection Strategies

### Strategy Comparison

| Strategy             | Best For              | Complexity   | Coverage Speed |
| -------------------- | --------------------- | ------------ | -------------- |
| Max Information Gain | General use           | O(Q × C)     | Fastest        |
| Max Uncertainty      | Simple implementation | O(C)         | Fast           |
| Prerequisite-First   | Structured domains    | O(Q × C × P) | Moderate       |
| Balanced Coverage    | Initial diagnostics   | O(Q × C)     | Even           |

### Recommended Approach

1. **Initial Diagnostic (first 12-20 questions):** Balanced Coverage
   - Goal: Seed beliefs across all knowledge areas
   - Select questions that cover diverse concepts

2. **Adaptive Quiz (ongoing):** Max Information Gain
   - Goal: Efficiently reduce uncertainty
   - Prioritize questions about uncertain concepts

3. **Gap Remediation (targeted practice):** Prerequisite-First
   - Goal: Build from foundations
   - Ensure prerequisites are solid before advanced concepts

---

## API Endpoints

### Belief State Endpoints

```
GET  /api/v1/beliefs
     Returns current belief states for authenticated user
     Query params: ?knowledge_area=X (optional filter)

GET  /api/v1/beliefs/{concept_id}
     Returns belief state for specific concept

GET  /api/v1/coverage
     Returns coverage report with mastered/gaps/uncertain counts

GET  /api/v1/coverage/details
     Returns full concept-level coverage with all belief states
```

### Question Selection Endpoints

```
POST /api/v1/quiz/next-question
     Body: { "strategy": "max_info_gain" | "max_uncertainty" | "prerequisite_first" }
     Returns: Optimally selected question

POST /api/v1/quiz/answer
     Body: { "question_id": UUID, "selected_answer": "A"|"B"|"C"|"D" }
     Returns: { "is_correct": bool, "explanation": str, "belief_updates": [...] }
```

### Coverage Report Endpoints

```
GET  /api/v1/coverage/summary
     Returns: {
       "total_concepts": 1203,
       "mastered": 847,
       "gaps": 156,
       "uncertain": 200,
       "coverage_percentage": 0.704,
       "estimated_questions_remaining": 400
     }

GET  /api/v1/coverage/by-knowledge-area
     Returns: Coverage breakdown by KA for dashboard display

GET  /api/v1/coverage/gaps
     Returns: List of gap concepts sorted by priority
```

---

## Migration Path

### Phase 1: Data Model (Week 1-2)

1. Create `concepts` table with BABOK concept extraction
2. Create `concept_prerequisites` table
3. Create `belief_states` table
4. Create `question_concepts` junction table
5. Migrate existing questions to new schema

### Phase 2: Core Algorithm (Week 3-4)

1. Implement BeliefUpdater service
2. Implement QuestionSelector service
3. Implement CoverageAnalyzer service
4. Unit tests for all BKT math

### Phase 3: API Integration (Week 5-6)

1. New endpoints for belief states and coverage
2. Modify quiz flow to use BKT question selection
3. Modify answer submission to update beliefs

### Phase 4: UI Updates (Week 7-8)

1. Coverage visualization (concept-level heatmap)
2. Gap analysis with concept details
3. Progress tracking with confidence intervals

---

## Performance Considerations

### Belief State Storage

- ~1,500 concepts × N users = potentially millions of rows
- Index on (user_id, concept_id) for fast lookups
- Consider materialized views for coverage aggregations

### Question Selection

- Max info gain requires evaluating all questions: O(Q × C)
- For large question banks, use pre-computed question scores
- Cache question-concept mappings

### Real-time Updates

- Belief updates are O(C) per question (C = concepts tested)
- Use async updates for prerequisite propagation
- Batch belief state writes

---

## Success Metrics

### Algorithm Quality

- **Coverage efficiency:** Questions to reach 90% confidence coverage
- **Prediction accuracy:** How well P(correct) predicts actual responses
- **Calibration:** Are confident predictions actually correct?

### User Experience

- **Time to first gap identification:** < 5 minutes
- **Perceived accuracy:** User survey "Did this reflect your knowledge?"
- **Engagement:** Return rate after initial diagnostic

### Business Metrics

- **Differentiation:** "Progressive corpus coverage" as unique value prop
- **Retention:** Users who see coverage progress stay longer
- **Conversion:** Coverage reports drive premium conversion

---

## References

1. Corbett, A. T., & Anderson, J. R. (1994). Knowledge tracing: Modeling the acquisition of procedural knowledge. _User Modeling and User-Adapted Interaction, 4_(4), 253-278.

2. Yudelson, M. V., Koedinger, K. R., & Gordon, G. J. (2013). Individualized Bayesian knowledge tracing models. In _International Conference on Artificial Intelligence in Education_ (pp. 171-180).

3. Piech, C., et al. (2015). Deep knowledge tracing. In _Advances in Neural Information Processing Systems_ (pp. 505-513).

---

## Change Log

| Date       | Version | Description                    | Author                |
| ---------- | ------- | ------------------------------ | --------------------- |
| 2025-12-08 | 1.1     | Added Mathematical Primer for AI Agents section - Beta distribution basics, Bayes' theorem, entropy/info gain, confidence calculation, worked examples | Winston (Architect) |
| 2025-12-08 | 1.0     | Added multi-course design note - BKT engine is course-agnostic | Winston (Architect) |
| 2025-11-27 | 0.1     | Initial BKT architecture draft | Sarah (Product Owner) |
