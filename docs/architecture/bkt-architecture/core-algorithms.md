# Core Algorithms

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
