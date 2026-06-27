# Epic 4: Bayesian Adaptive Quiz Engine (BKT-First)

**Epic Goal:** Implement the core adaptive learning engine that uses Bayesian Knowledge Tracing to select questions optimally, update beliefs after each response, and progressively map the user's knowledge across the entire concept corpus until confident coverage is achieved.

**Key Difference from Original:**
- Question selection uses **maximum information gain**, not random from weak KAs
- Competency updates are **Bayesian belief updates**, not point estimate adjustments
- The goal is **confident coverage of all concepts**, not just improving a score
- Sessions are **fixed-length (10 questions by default, configurable)**, auto-completing to enable low-friction, casual engagement
- Questions selected via **BKT beliefs + IRT difficulty** to match user's competence level (challenging but not overwhelming)

**Architecture Reference:** See `docs/architecture/bkt-architecture.md`

---

## Story 4.1: Quiz Session Creation and State Management

As a **user ready to study**,
I want to start an adaptive quiz session,
so that I can practice questions selected optimally for my knowledge state.

**Acceptance Criteria:**

1. POST `/api/v1/quiz/session/start` creates new quiz session
2. Session record in `quiz_sessions` table:
   ```
   - id (UUID, PK)
   - user_id (FK)
   - session_type (ENUM: 'adaptive', 'focused_ka', 'focused_concept', 'review')
   - question_target (INT, default 10) - configurable for future optimization
   - target_ka_id (FK, nullable) - for focused_ka sessions
   - target_concept_ids (JSONB, nullable) - for focused_concept sessions
   - questions_answered (INT, default 0)
   - total_info_gain (FLOAT, default 0) - cumulative information gain
   - status (ENUM: 'active', 'paused', 'completed', 'expired')
   - started_at, paused_at, completed_at (TIMESTAMPS)
   - created_at
   ```
3. Only one active session per user (return existing if active)
4. On session start, set `question_target` to 10 (configurable default for habit-forming consistency)
5. Session start triggers first question selection (Story 4.2)
6. Response includes session_id, first question, and question_target
7. GET `/api/v1/quiz/session/{id}` returns session state including question_target
8. POST `/api/v1/quiz/session/{id}/pause` saves state for later
9. POST `/api/v1/quiz/session/{id}/end` completes session (or auto-completes when questions_answered == question_target)
10. Sessions auto-expire after 2 hours of inactivity
11. Logging: Session lifecycle events tracked

**Session Types:**
- `adaptive`: Pure BKT-driven selection (default)
- `focused_ka`: Prioritize questions from specific KA
- `focused_concept`: Target specific concepts (remediation)
- `review`: Re-test previously incorrect questions

---

## Story 4.2: Bayesian Question Selection Engine (CRITICAL)

As a **quiz engine**,
I want to select the next question that maximizes expected information gain,
so that every question efficiently reduces uncertainty about the user's knowledge.

**Acceptance Criteria:**

1. Question selection service `/app/services/question_selector.py`
2. **Primary Strategy: Maximum Information Gain**
   ```python
   def select_next_question(beliefs, available_questions):
       """
       Select question that maximizes expected entropy reduction.

       Info Gain = H(beliefs) - E[H(beliefs | response)]
       """
       best_question = None
       max_gain = -inf

       for question in available_questions:
           gain = calculate_expected_info_gain(question, beliefs)
           if gain > max_gain:
               max_gain = gain
               best_question = question

       return best_question, max_gain
   ```
3. **Information Gain Calculation:**
   - Current entropy for concepts tested by question
   - Predict P(correct) given current beliefs
   - Simulate belief updates for correct/incorrect outcomes
   - Expected posterior entropy = weighted average
   - Gain = current - expected posterior
4. **Filtering Constraints:**
   - Exclude questions answered in last 7 days (recency)
   - Exclude questions from current session (no repeats)
   - Apply session type filters (focused_ka, focused_concept)
5. **Fallback Strategies:**
   - If info gain < threshold for all questions: Select from most uncertain concepts
   - If focused session exhausts questions: Expand to related concepts
6. Response includes:
   - question_id, question_text, options, ka, difficulty
   - estimated_info_gain (for analytics)
   - NOT correct_answer, explanation (revealed after answer)
7. **Performance:** Selection completes in <200ms
8. **Logging:** Selection rationale for debugging
   - "Selected Q{id} for concepts {list}, expected info gain: {value}"
9. Unit tests: Info gain calculation, filtering, edge cases
10. Integration test: Selection favors high-uncertainty concepts

**Algorithm Details:**

```python
def calculate_expected_info_gain(question: Question, beliefs: Dict[UUID, BeliefState]) -> float:
    """Calculate expected reduction in entropy from asking this question."""

    # Get beliefs for concepts this question tests
    concept_beliefs = [beliefs[c_id] for c_id in question.concept_ids if c_id in beliefs]

    if not concept_beliefs:
        return 0.0

    # Current entropy (uncertainty)
    current_entropy = sum(beta_entropy(b.alpha, b.beta) for b in concept_beliefs)

    # Predict probability of correct response
    avg_mastery = sum(b.alpha / (b.alpha + b.beta) for b in concept_beliefs) / len(concept_beliefs)
    p_correct = (1 - question.slip_rate) * avg_mastery + question.guess_rate * (1 - avg_mastery)

    # Simulate updates for each outcome
    beliefs_if_correct = simulate_bayesian_update(concept_beliefs, is_correct=True,
                                                    slip=question.slip_rate, guess=question.guess_rate)
    beliefs_if_incorrect = simulate_bayesian_update(concept_beliefs, is_correct=False,
                                                      slip=question.slip_rate, guess=question.guess_rate)

    # Expected posterior entropy
    entropy_if_correct = sum(beta_entropy(b.alpha, b.beta) for b in beliefs_if_correct)
    entropy_if_incorrect = sum(beta_entropy(b.alpha, b.beta) for b in beliefs_if_incorrect)

    expected_posterior_entropy = p_correct * entropy_if_correct + (1 - p_correct) * entropy_if_incorrect

    return current_entropy - expected_posterior_entropy


def beta_entropy(alpha: float, beta: float) -> float:
    """Calculate entropy of Beta(alpha, beta) distribution."""
    from scipy.special import betaln, digamma
    return (betaln(alpha, beta)
            - (alpha - 1) * digamma(alpha)
            - (beta - 1) * digamma(beta)
            + (alpha + beta - 2) * digamma(alpha + beta))
```

---

## Story 4.3: Answer Submission and Immediate Feedback

As a **user answering a quiz question**,
I want to submit my answer and immediately see if I was correct,
so that I receive instant feedback on my understanding.

**Acceptance Criteria:**

1. POST `/api/v1/quiz/answer` accepts:
   ```json
   {
     "session_id": "uuid",
     "question_id": "uuid",
     "selected_answer": "A"
   }
   ```
2. Record response in `quiz_responses` table:
   ```
   - id (UUID, PK)
   - user_id (FK)
   - session_id (FK)
   - question_id (FK)
   - selected_answer (CHAR 1)
   - is_correct (BOOL)
   - time_taken_ms (INT)
   - info_gain_actual (FLOAT) - actual entropy reduction from this answer
   - belief_updates (JSONB) - snapshot of concept updates
   - created_at
   ```
3. Determine correctness by comparing to question.correct_answer
4. **Trigger Bayesian belief update** (Story 4.4)
5. Response includes:
   ```json
   {
     "is_correct": true,
     "correct_answer": "A",
     "explanation": "...",
     "concepts_updated": [
       {"concept_id": "uuid", "name": "Stakeholder Analysis", "new_mastery": 0.72}
     ],
     "session_stats": {
       "questions_answered": 8,
       "accuracy": 0.75,
       "total_info_gain": 12.4,
       "coverage_progress": 0.52
     }
   }
   ```
6. **Immediate feedback UI:**
   - Correct: Green checkmark, "Correct!"
   - Incorrect: Orange X, "Incorrect. The correct answer is {X}"
7. Track time_taken (client sends timestamp or server calculates)
8. Error handling: Invalid session, invalid question, already answered
9. Performance: Response in <200ms (including belief update)
10. Unit tests: Correctness determination, response schema

---

## Story 4.4: Bayesian Belief Update Engine (CRITICAL)

As a **system**,
I want to update belief states after each quiz answer using Bayesian inference,
so that the knowledge profile reflects the latest evidence.

**Acceptance Criteria:**

1. Belief update service `/app/services/belief_updater.py`
2. **Core Bayesian Update:**
   ```python
   def update_beliefs(user_id, question, is_correct, beliefs):
       """
       Update beliefs for all concepts tested by this question.

       Uses Beta-Bernoulli model with slip/guess parameters.
       """
       updates = {}

       for concept_id in question.concept_ids:
           belief = beliefs[concept_id]

           # BKT update equations
           p_mastered = belief.alpha / (belief.alpha + belief.beta)
           slip = question.slip_rate
           guess = question.guess_rate

           if is_correct:
               p_correct = (1 - slip) * p_mastered + guess * (1 - p_mastered)
               posterior = (1 - slip) * p_mastered / p_correct
           else:
               p_incorrect = slip * p_mastered + (1 - guess) * (1 - p_mastered)
               posterior = slip * p_mastered / p_incorrect

           # Update Beta parameters
           new_alpha = belief.alpha + posterior
           new_beta = belief.beta + (1 - posterior)

           updates[concept_id] = BeliefState(
               alpha=new_alpha,
               beta=new_beta,
               response_count=belief.response_count + 1
           )

       return updates
   ```
3. **Prerequisite Propagation** (weaker signal):
   - If correct: Slightly increase belief for prerequisite concepts
   - Propagation weight: 0.2-0.3 (configurable)
4. Persist updates atomically
5. Calculate actual information gain (for analytics):
   ```python
   actual_info_gain = entropy_before - entropy_after
   ```
6. Store belief snapshot in response record (for debugging/analysis)
7. Logging: "Updated {N} concepts for user {id}, info gain: {value}"
8. Performance: Update completes in <50ms
9. **Unit tests:**
   - Correct answer increases mastery probability
   - Incorrect answer decreases mastery probability
   - Slip/guess parameters affect update magnitude
   - Multi-concept questions update all concepts
10. Integration test: Sequential answers update beliefs progressively

---

## Story 4.5: Coverage Progress Tracking

As a **user**,
I want to see my progress toward complete knowledge coverage,
so that I understand how much more assessment is needed.

**Acceptance Criteria:**

1. Coverage analyzer service `/app/services/coverage_analyzer.py`
2. **Concept Classification:**
   - **Mastered:** P(mastery) > 0.8 AND confidence > 0.7
   - **Gap:** P(mastery) < 0.5 AND confidence > 0.7
   - **Uncertain:** confidence < 0.7 (need more data)
3. **Coverage Report:**
   ```json
   {
     "total_concepts": 1203,
     "mastered": 487,
     "gaps": 156,
     "uncertain": 560,
     "coverage_percentage": 0.534,
     "confidence_percentage": 0.534,
     "estimated_questions_remaining": 280,
     "by_knowledge_area": [
       {
         "ka": "Business Analysis Planning",
         "mastered": 89,
         "gaps": 23,
         "uncertain": 75
       }
     ]
   }
   ```
4. API endpoint: GET `/api/v1/coverage`
5. Updated after each quiz answer (incremental calculation)
6. Used by question selector to prioritize uncertain concepts
7. **Confidence calculation:**
   ```python
   confidence = (alpha + beta) / (alpha + beta + 2)  # Asymptotic to 1
   ```
8. Performance: Coverage calculation in <100ms
9. Cache coverage summary (invalidate on belief update)
10. Unit tests: Classification logic, percentage calculations

**Technical Note - New Concept Additions:**
When new concepts are added to the system (e.g., via Story 2.13), `total_concepts` increases and `coverage_percentage` may drop. This is expected behavior. New concepts start as "uncertain" with uninformative priors (Story 2.14 handles belief initialization). The question selector will naturally prioritize these high-uncertainty concepts. No special handling is required - the BKT engine adapts automatically.

---

## Story 4.6: Explanation Display and Concept Context

As a **user who answered a question**,
I want to see a detailed explanation with concept context,
so that I learn the underlying concepts, not just the answer.

**Acceptance Criteria:**

1. After answer submission, display explanation panel
2. Explanation includes:
   - **Why correct answer is right** (from question.explanation)
   - **Concepts tested** by this question (list with names - educational context)
   - **Progress indicator:** "You're improving in {concept}!" or "Keep practicing {concept}" (simple, motivational - no percentages)
   - **BABOK reference:** "See BABOK v3 Section {ref}"
   - **Link to reading:** "Study this concept" → relevant BABOK chunk
3. Explanation card styling: 14px border radius, Inter font
4. **Concept tags:** Display concept names for educational context (no mastery percentages - those are system-internal)
5. "Next Question" button advances to next BKT-selected question
6. **User feedback:** Thumbs up/down on explanation helpfulness
7. Accessibility: Screen reader friendly, keyboard navigable
8. Performance: Explanation renders immediately (data in answer response)
9. Mobile responsive
10. Analytics: Track explanation engagement, feedback rates

---

## Story 4.7: Fixed-Length Session Auto-Completion

As a **user completing a quiz**,
I want the session to automatically end when I reach the target question count,
so that I experience low-friction, bite-sized learning sessions.

**Acceptance Criteria:**

1. Session auto-completes when `questions_answered == question_target`
2. No user action required to end session (seamless completion)
3. On final answer submission:
   - Process answer and belief update as normal
   - Set `status = 'completed'` and `completed_at = NOW()`
   - Return session summary in response
4. **Session Summary displayed:**
   - Questions answered (e.g., "12/12")
   - Accuracy (e.g., "75%")
   - Concepts strengthened (count of beliefs updated)
   - Quizzes completed to date (running total)
   - "Start New Quiz" CTA
5. **Progress indicator during session:**
   - Show "Question 7 of 12" (not just "Question 7")
   - Visual progress bar showing completion percentage
6. User can still end early via explicit "End Quiz" button (optional)
7. **Tracking metrics:**
   - Increment user's `quizzes_completed` count
   - Track `total_questions_answered` (lifetime)
   - Track `total_time_spent` (session duration sum)
8. **Dashboard integration:**
   - User dashboard shows: "Quizzes completed: X"
   - Optional: "This week: Y quizzes"
9. Logging: Session completion events with duration, accuracy
10. Analytics: Track quiz completion rates, early exits

> **Note:** Admin reporting (system-wide quiz stats) deferred to Story 10.8 (Admin Dashboard API) in the Admin Content Management epic.

**Key Design Principles:**
- **Zero friction:** User doesn't think about ending sessions
- **Predictable commitment:** User knows upfront it's 10 questions
- **Progressive learning:** Each quiz builds on previous via BKT
- **Gamification-ready:** Completion count enables streaks, badges (future)

---

## Story 4.8: Focused Practice Mode

As a **user**,
I want to practice questions focused on specific concepts or knowledge areas,
so that I can target my weak areas.

**Acceptance Criteria:**

1. POST `/api/v1/quiz/session/start` accepts:
   ```json
   {
     "session_type": "focused_ka",
     "target_ka_id": "uuid"
   }
   ```
   or:
   ```json
   {
     "session_type": "focused_concept",
     "target_concept_ids": ["uuid1", "uuid2"]
   }
   ```
2. Question selector filters to target KA or concepts
3. Still uses info-gain within filtered set
4. UI shows focus context: "Practicing: Elicitation and Collaboration"
5. **Gap-based suggestions:**
   - "You have 15 gap concepts in Requirements Analysis. Focus on these?"
   - Quick-start focused session from coverage report
6. Session tracks target achievement:
   - Did beliefs improve for target concepts?
   - Did any flip from gap to mastered?
7. End-of-session summary shows target progress
8. Fallback: If target exhausted, expand to prerequisites or suggest different focus
9. Unit tests: Filter by KA, filter by concept
10. Integration test: Focused session only asks relevant questions

---

## Story 4.9: Post-Session Review Mode

As a **user who got questions wrong**,
I want to immediately review my incorrect answers,
so that I can reinforce correct understanding.

**Acceptance Criteria:**

1. When session ends (manually or suggested), check for incorrect answers
2. If incorrect answers exist, offer review:
   - "You missed 5 questions. Review now for better retention?"
   - "Skip Review" / "Start Review"
3. Review mode re-presents incorrect questions
4. **Review UI:**
   - "REVIEW" badge on question
   - "Review Question 1 of 5"
   - Same 4 options, no indication of previous answer
5. On re-answer:
   - If now correct: "Great improvement!"
   - If still incorrect: Show correct answer, explanation, reading link
6. **Belief update on review:**
   - Reinforced (incorrect → correct): Stronger positive update
   - Still incorrect: Maintain or slightly decrease belief
7. Review session tracks:
   - `total_reviewed`, `reinforced_count`, `still_incorrect_count`
8. After review, show summary:
   - "Reinforced 4/5 questions!"
   - List still-incorrect concepts with study links
9. Skip tracking: If user skips review, log for analytics
10. Analytics: Review completion rate, reinforcement rate

---

## Story 4.10: Quiz Analytics and Dashboard Data

As a **system**,
I want to provide quiz analytics for the dashboard,
so that users can track their learning progress.

**Acceptance Criteria:**

1. GET `/api/v1/quiz/stats` returns:
   ```json
   {
     "total_questions_answered": 245,
     "total_sessions": 12,
     "accuracy_overall": 0.73,
     "accuracy_trend": [0.65, 0.68, 0.71, 0.73],  // Weekly
     "total_study_time_minutes": 320,
     "coverage_progress": [
       {"date": "2025-11-20", "coverage": 0.32},
       {"date": "2025-11-27", "coverage": 0.54}
     ],
     "concepts_mastered_this_week": 45,
     "current_streak_days": 5,
     "strongest_ka": "Business Analysis Planning",
     "weakest_ka": "Solution Evaluation"
   }
   ```
2. Historical data aggregated efficiently (pre-compute daily)
3. Streak calculation based on quiz activity
4. KA strength/weakness from aggregated concept beliefs
5. Performance: Stats query in <200ms
6. Cache with 5-minute TTL (updated on session end)
7. Used by dashboard (Epic 6) for visualizations
8. Export endpoint for detailed analytics (CSV)
9. Admin endpoint for platform-wide metrics
10. Unit tests: Aggregation logic, trend calculation

---

## Story 4.11: Prerequisite-Based Curriculum Navigation (NEW)

As a **user progressing through the curriculum**,
I want the system to enforce prerequisite mastery before testing advanced concepts,
so that I build knowledge systematically and don't face questions I'm unprepared for.

**Background:**
The concept prerequisite graph (Story 2.3) defines which concepts must be understood before others. This story enforces those relationships during question selection, ensuring learners follow a logical progression through the curriculum.

**Acceptance Criteria:**

1. **Mastery Gate Threshold Configuration:**
   ```python
   MASTERY_GATE_CONFIG = {
       'prerequisite_mastery_threshold': 0.7,  # P(mastery) > 0.7 required
       'prerequisite_confidence_threshold': 0.6,  # Confidence > 0.6 required
       'enforcement_mode': 'soft',  # 'soft' or 'hard'
       'min_responses_for_gate': 3,  # Minimum responses before gate applies
   }
   ```

2. **Gate Check Service** `/app/services/mastery_gate.py`:
   ```python
   def check_prerequisites_mastered(user_id: UUID, concept_id: UUID) -> GateCheckResult:
       """
       Check if all prerequisites for a concept are mastered.

       Returns:
           GateCheckResult:
               - is_unlocked: bool
               - blocking_prerequisites: List[ConceptSummary]  # Unmastered prereqs
               - closest_to_unlock: ConceptSummary  # Prereq with highest mastery
               - mastery_progress: float  # 0.0-1.0 progress toward unlock
       """
       prereqs = get_concept_prerequisites(concept_id)
       beliefs = get_user_beliefs(user_id, [p.id for p in prereqs])

       blocking = []
       for prereq in prereqs:
           belief = beliefs.get(prereq.id)
           if belief is None or not meets_mastery_gate(belief):
               blocking.append(prereq)

       return GateCheckResult(
           is_unlocked=len(blocking) == 0,
           blocking_prerequisites=blocking,
           closest_to_unlock=get_highest_mastery(blocking),
           mastery_progress=calculate_unlock_progress(prereqs, beliefs)
       )
   ```

3. **Question Selector Integration:**
   - Before selecting a question, check if target concept's prerequisites are mastered
   - **Soft enforcement (default):** Deprioritize locked concepts (weight = 0.1)
   - **Hard enforcement:** Exclude locked concepts entirely
   - Log when concept is deprioritized/excluded due to prerequisites

4. **Filter Extension for Question Selection:**
   ```python
   def apply_prerequisite_filter(candidates: List[Question],
                                  user_id: UUID,
                                  enforcement: str) -> List[Question]:
       """
       Filter or weight questions based on prerequisite mastery.
       """
       filtered = []
       for question in candidates:
           gate_results = [check_prerequisites_mastered(user_id, c_id)
                          for c_id in question.concept_ids]

           if all(g.is_unlocked for g in gate_results):
               filtered.append((question, 1.0))  # Full weight
           elif enforcement == 'soft':
               filtered.append((question, 0.1))  # Deprioritized
           # Hard enforcement: excluded entirely

       return filtered
   ```

5. **API Endpoint for Concept Lock Status:**
   - GET `/api/v1/concepts/{id}/prerequisites/status`
   - Response:
     ```json
     {
       "concept_id": "uuid",
       "concept_name": "Requirements Prioritization",
       "is_unlocked": false,
       "blocking_prerequisites": [
         {
           "concept_id": "uuid",
           "name": "Stakeholder Analysis",
           "current_mastery": 0.58,
           "required_mastery": 0.70,
           "responses_count": 5
         }
       ],
       "mastery_progress": 0.72,
       "estimated_questions_to_unlock": 4
     }
     ```

6. **Bulk Status Endpoint:**
   - GET `/api/v1/concepts/unlock-status?ka_id={ka_id}`
   - Returns unlock status for all concepts in a KA
   - Used by dashboard for visual curriculum map

7. **Unlock Notification:**
   - When prerequisite mastery is achieved, trigger unlock event
   - Store in `concept_unlock_events` table:
     ```
     - id (UUID, PK)
     - user_id (FK)
     - concept_id (FK)
     - unlocked_at (TIMESTAMP)
     - prerequisite_concept_id (FK) - which prereq triggered unlock
     ```
   - Push notification (if enabled): "You've unlocked {concept}!"

8. **Dashboard Integration:**
   - Coverage report includes locked/unlocked counts:
     ```json
     {
       "total_concepts": 1203,
       "unlocked": 892,
       "locked": 311,
       "locked_by_ka": [
         {"ka": "Solution Evaluation", "locked_count": 45}
       ]
     }
     ```
   - Visual indicator: Lock icon on concept cards/nodes

9. **Override Capability:**
   - POST `/api/v1/concepts/{id}/attempt-locked`
   - Allows user to attempt locked concept (for advanced users)
   - Logs override event for analytics
   - Question selector applies 0.5 weight (middle ground)
   - Warning shown: "This concept has unmastered prerequisites. Answers may be harder."

10. **Performance Requirements:**
    - Gate check: <20ms per concept
    - Batch check (all concepts): <200ms
    - Cache prerequisite graph in memory
    - Cache user unlock status with 5-minute TTL

**Configuration Options:**

| Parameter | Default | Description |
|-----------|---------|-------------|
| `prerequisite_mastery_threshold` | 0.7 | P(mastery) required for prerequisite |
| `prerequisite_confidence_threshold` | 0.6 | Confidence required for prerequisite |
| `enforcement_mode` | `soft` | `soft` = deprioritize, `hard` = exclude |
| `min_responses_for_gate` | 3 | Minimum responses before gate applies |
| `unlock_notification_enabled` | true | Send notification on concept unlock |

**UI Considerations:**

1. **Locked Concept Display:**
   - Gray/muted appearance with lock icon
   - Tooltip: "Master {prereq1}, {prereq2} to unlock"
   - Progress bar showing mastery progress toward unlock

2. **Unlock Celebration:**
   - Brief animation when concept unlocks
   - Toast: "New concept available: {name}"

3. **Learning Path Visualization (Future):**
   - Visual graph showing concept dependencies
   - Nodes colored by mastery state (locked/uncertain/mastered)
   - Clickable to start focused practice

**Algorithm Reference:**
- Prerequisite graph structure: `docs/stories/2.3.concept-prerequisite-graph.md`
- Belief state model: `docs/prd/algorithm-specifications.md` (Algorithm 3)

**Testing Requirements:**

1. Unit tests:
   - `test_check_prerequisites_mastered_all_met`: Returns unlocked when all prereqs mastered
   - `test_check_prerequisites_mastered_partial`: Returns blocking list correctly
   - `test_question_filter_soft_enforcement`: Deprioritizes locked concepts
   - `test_question_filter_hard_enforcement`: Excludes locked concepts
   - `test_unlock_event_triggered`: Event fires when prereq mastered

2. Integration tests:
   - `test_question_selection_respects_gates`: Selector avoids locked concepts
   - `test_override_attempt_logged`: Override events tracked
   - `test_cascade_unlock`: Unlocking prereq unlocks dependent concepts

---

## Story 4.12: Exam Readiness Assessment & Coverage Gates (NEW)

As a **user preparing for certification**,
I want to see a clear exam readiness assessment based on my coverage and confidence levels,
so that I know when I'm adequately prepared and can focus on specific weak areas.

**Background:**
Story 4.5 provides coverage tracking (mastered/gap/uncertain counts). This story extends that foundation with explicit exam readiness thresholds, KA balance requirements, and actionable recommendations. It answers the question: "Am I ready to take the exam?"

**Functional Requirements Reference:** FR5C (Coverage Completion & Exam Readiness)

**Acceptance Criteria:**

1. **Exam Readiness Calculator Service** `/app/services/readiness_calculator.py`:
   ```python
   class ReadinessCalculator:
       """
       Calculates exam readiness based on coverage, confidence, and KA balance.

       Readiness Status:
       - NOT_READY: readiness_score < 0.60
       - ALMOST_READY: 0.60 <= readiness_score < 0.80
       - READY: 0.80 <= readiness_score < 0.90
       - WELL_PREPARED: readiness_score >= 0.90
       """

       def __init__(self, coverage_analyzer: CoverageAnalyzer):
           self.coverage_analyzer = coverage_analyzer
           self.config = ReadinessConfig.from_course(course_id)

       async def calculate_readiness(self, user_id: UUID) -> ReadinessAssessment:
           """
           Calculate comprehensive exam readiness assessment.

           Returns:
               ReadinessAssessment:
                   - readiness_score: float (0.0-1.0)
                   - status: ReadinessStatus enum
                   - coverage_score: float
                   - confidence_score: float
                   - ka_balance_score: float
                   - blocking_issues: List[ReadinessIssue]
                   - recommendations: List[str]
                   - estimated_questions_to_ready: int
           """
   ```

2. **Readiness Score Calculation:**
   ```python
   def calculate_readiness_score(coverage: CoverageReport) -> float:
       """
       Weighted readiness score combining three factors.

       Formula: (coverage × 0.4) + (confidence × 0.3) + (ka_balance × 0.3)

       Where:
       - coverage = mastered_count / total_concepts
       - confidence = avg confidence across all beliefs
       - ka_balance = 1.0 - (max_ka_coverage - min_ka_coverage)
       """
       coverage_score = coverage.mastered / coverage.total_concepts
       confidence_score = coverage.confidence_percentage

       ka_coverages = [ka.mastered / ka.total for ka in coverage.by_knowledge_area]
       ka_variance = max(ka_coverages) - min(ka_coverages)
       ka_balance_score = max(0, 1.0 - ka_variance)

       return (coverage_score * 0.4) + (confidence_score * 0.3) + (ka_balance_score * 0.3)
   ```

3. **Readiness Status Thresholds:**
   | Status | Score Range | Dashboard Display |
   |--------|-------------|-------------------|
   | NOT_READY | < 60% | Red indicator, "Not Ready" |
   | ALMOST_READY | 60-79% | Yellow indicator, "Almost Ready" |
   | READY | 80-89% | Green indicator, "Ready" |
   | WELL_PREPARED | >= 90% | Green + star, "Well Prepared" |

4. **Knowledge Area Balance Validation:**
   ```python
   def check_ka_balance(coverage: CoverageReport, min_threshold: float = 0.60) -> List[KAIssue]:
       """
       Identify KAs below minimum coverage threshold.

       Returns list of blocking KA issues:
       - ka_id, ka_name, current_coverage, required_coverage, gap_count
       """
       issues = []
       for ka in coverage.by_knowledge_area:
           ka_coverage = ka.mastered / ka.total if ka.total > 0 else 0
           if ka_coverage < min_threshold:
               issues.append(KAIssue(
                   ka_id=ka.ka_id,
                   ka_name=ka.ka_name,
                   current_coverage=ka_coverage,
                   required_coverage=min_threshold,
                   gap_concepts=ka.gaps
               ))
       return issues
   ```

5. **Configurable Thresholds per Course:**
   ```python
   READINESS_CONFIG = {
       'default': {
           'exam_ready_coverage_threshold': 0.80,
           'exam_ready_confidence_threshold': 0.70,
           'ka_minimum_coverage_threshold': 0.60,
           'ka_imbalance_variance_threshold': 0.20,
       },
       'cbap': {
           # Use defaults
       },
       'cfa_level_1': {
           'exam_ready_coverage_threshold': 0.85,  # Higher bar
           'ka_minimum_coverage_threshold': 0.70,
       }
   }
   ```

6. **API Endpoint:**
   - GET `/api/v1/readiness` returns:
     ```json
     {
       "readiness_score": 0.72,
       "status": "ALMOST_READY",
       "status_display": "Almost Ready",
       "coverage_score": 0.68,
       "confidence_score": 0.75,
       "ka_balance_score": 0.73,
       "is_exam_ready": false,
       "blocking_issues": [
         {
           "type": "ka_below_threshold",
           "ka_id": "solution_evaluation",
           "ka_name": "Solution Evaluation",
           "current": 0.45,
           "required": 0.60,
           "message": "Solution Evaluation is at 45% coverage (60% required)"
         }
       ],
       "recommendations": [
         "Focus on Solution Evaluation - currently at 45% coverage",
         "Answer 25 more questions to increase overall confidence",
         "You have 156 gap concepts to review"
       ],
       "progress_to_ready": 0.80,
       "estimated_questions_to_ready": 85,
       "by_knowledge_area": [
         {
           "ka_id": "business_analysis_planning",
           "ka_name": "Business Analysis Planning",
           "coverage": 0.82,
           "status": "ready",
           "color": "green"
         },
         {
           "ka_id": "solution_evaluation",
           "ka_name": "Solution Evaluation",
           "coverage": 0.45,
           "status": "below_threshold",
           "color": "red"
         }
       ]
     }
     ```

7. **Readiness Schemas** `/app/schemas/readiness.py`:
   ```python
   class ReadinessStatus(str, Enum):
       NOT_READY = "not_ready"
       ALMOST_READY = "almost_ready"
       READY = "ready"
       WELL_PREPARED = "well_prepared"

   class ReadinessIssue(BaseModel):
       type: str  # "ka_below_threshold", "low_confidence", "high_gap_count"
       message: str
       ka_id: str | None = None
       current: float | None = None
       required: float | None = None

   class KAReadinessStatus(BaseModel):
       ka_id: str
       ka_name: str
       coverage: float
       status: str  # "ready", "almost_ready", "below_threshold"
       color: str  # "green", "yellow", "red"

   class ReadinessAssessment(BaseModel):
       readiness_score: float
       status: ReadinessStatus
       status_display: str
       coverage_score: float
       confidence_score: float
       ka_balance_score: float
       is_exam_ready: bool
       blocking_issues: list[ReadinessIssue]
       recommendations: list[str]
       progress_to_ready: float  # 0.0-1.0 toward 80%
       estimated_questions_to_ready: int
       by_knowledge_area: list[KAReadinessStatus]
   ```

8. **Recommendation Generator:**
   ```python
   def generate_recommendations(assessment: ReadinessAssessment) -> List[str]:
       """
       Generate actionable recommendations based on current state.

       Priority order:
       1. KA below threshold (most blocking)
       2. Low overall coverage
       3. Low confidence (need more questions)
       4. High gap count (need review)
       """
       recommendations = []

       # KA-specific recommendations
       for issue in assessment.blocking_issues:
           if issue.type == "ka_below_threshold":
               recommendations.append(
                   f"Focus on {issue.ka_name} - currently at {issue.current:.0%} coverage"
               )

       # Coverage recommendations
       if assessment.coverage_score < 0.80:
           remaining = int((0.80 - assessment.coverage_score) * total_concepts)
           recommendations.append(f"Master {remaining} more concepts to reach 80% coverage")

       # Confidence recommendations
       if assessment.confidence_score < 0.70:
           recommendations.append("Answer more questions to increase confidence in your assessments")

       return recommendations[:5]  # Limit to top 5
   ```

9. **Dashboard Integration:**
   - Include `readiness_summary` in dashboard API response
   - Display readiness progress bar with percentage
   - Show color-coded KA indicators
   - "X% to Exam Ready" motivational display

10. **Exam Date Warning:**
    - When user sets exam date < 7 days away AND readiness < 60%:
      - Show soft warning: "Your exam is in X days but you're at Y% readiness"
      - Suggest: "Consider rescheduling or increasing study intensity"
    - Not a hard block - user can proceed

**Performance Requirements:**
- Readiness calculation: <150ms
- Uses cached coverage data from Story 4.5
- Cache readiness result with 5-minute TTL

**Dependencies:**
- **Requires:** Story 4.5 (Coverage Progress Tracking) - provides CoverageAnalyzer
- **Extends:** Story 4.5 coverage report with readiness assessment
- **Integrates with:** Epic 6 (Dashboard) for readiness display

**Testing Requirements:**

1. Unit tests:
   - `test_readiness_score_calculation`: Verify weighted formula
   - `test_status_thresholds`: NOT_READY/ALMOST_READY/READY/WELL_PREPARED boundaries
   - `test_ka_balance_detection`: Identify KAs below threshold
   - `test_recommendations_priority`: Most critical issues first
   - `test_course_specific_thresholds`: CFA vs CBAP thresholds

2. Integration tests:
   - `test_readiness_api_response`: Correct schema returned
   - `test_readiness_updates_with_coverage`: Changes reflect belief updates
   - `test_exam_date_warning_triggered`: Warning shown when appropriate

---

## Story 4.13: Advanced Performance Analytics (NEW)

As a **user wanting deeper insights into my learning patterns**,
I want to see detailed analytics about my study habits, question performance, and improvement velocity,
so that I can optimize my study approach and understand what's working.

**Background:**
Story 4.10 provides basic quiz analytics (accuracy trends, study time, coverage progress). This story extends those capabilities with time-based analytics, question-level insights, improvement velocity tracking, comparison analytics, and exportable reports.

**Functional Requirements Reference:** Extends FR5 (Competency Tracking & Estimation)

**Acceptance Criteria:**

1. **Time-Based Analytics Service** `/app/services/time_analytics.py`:
   ```python
   class TimeAnalyticsService:
       """
       Analyzes study patterns by time of day, day of week, and session duration.
       """

       async def get_optimal_study_times(self, user_id: UUID) -> OptimalStudyTimes:
           """
           Identify when user performs best.

           Returns:
               OptimalStudyTimes:
                   - best_hour: int (0-23)
                   - best_day: str (Monday-Sunday)
                   - accuracy_by_hour: Dict[int, float]
                   - accuracy_by_day: Dict[str, float]
                   - avg_session_duration_minutes: float
                   - optimal_session_length: int (based on fatigue analysis)
           """

       async def get_session_fatigue_analysis(self, user_id: UUID) -> FatigueAnalysis:
           """
           Analyze accuracy decay within sessions.

           Returns:
               FatigueAnalysis:
                   - accuracy_first_10: float
                   - accuracy_last_10: float
                   - fatigue_onset_question: int (when accuracy drops >10%)
                   - recommended_session_length: int
           """
   ```

2. **Question-Level Analytics:**
   ```python
   async def get_question_analytics(self, user_id: UUID) -> QuestionAnalytics:
       """
       Analyze performance at the question level.

       Returns:
           QuestionAnalytics:
               - hardest_questions: List[QuestionStat]  # Lowest accuracy
               - easiest_questions: List[QuestionStat]  # Highest accuracy
               - most_time_consuming: List[QuestionStat]  # Longest avg time
               - frequently_missed_concepts: List[ConceptStat]
               - question_type_performance: Dict[str, float]  # By KA
       """
   ```

3. **Improvement Velocity Tracking:**
   ```python
   async def get_improvement_velocity(self, user_id: UUID) -> ImprovementVelocity:
       """
       Calculate rate of improvement over time.

       Returns:
           ImprovementVelocity:
               - weekly_accuracy_change: float  # +/- percentage points
               - weekly_coverage_change: float
               - concepts_mastered_this_week: int
               - concepts_mastered_last_week: int
               - velocity_trend: str  # "accelerating", "steady", "slowing"
               - projected_ready_date: date | None
               - days_ahead_or_behind: int
       """
   ```

4. **Comparison Analytics (Anonymized):**
   ```python
   async def get_comparison_analytics(self, user_id: UUID) -> ComparisonAnalytics:
       """
       Compare user performance to anonymized cohort averages.

       Privacy: All comparisons use aggregated, anonymized data.

       Returns:
           ComparisonAnalytics:
               - percentile_rank: int  # User's percentile (1-100)
               - avg_cohort_accuracy: float
               - avg_cohort_coverage: float
               - avg_cohort_study_time_weekly: float
               - cohort_size: int
               - user_vs_cohort: Dict[str, str]  # "above", "at", "below"
       """
   ```

5. **API Endpoints:**
   - GET `/api/v1/analytics/time-patterns` - Time-based analytics
     ```json
     {
       "best_study_hour": 14,
       "best_study_day": "Tuesday",
       "accuracy_by_hour": {"9": 0.72, "14": 0.85, "21": 0.68},
       "avg_session_minutes": 23.5,
       "recommended_session_length": 25,
       "fatigue_onset": 18
     }
     ```

   - GET `/api/v1/analytics/questions` - Question-level analytics
     ```json
     {
       "hardest_questions": [
         {"question_id": "uuid", "text_preview": "...", "accuracy": 0.25, "attempts": 4}
       ],
       "frequently_missed_concepts": [
         {"concept_id": "uuid", "name": "RACI Matrix", "miss_rate": 0.45}
       ],
       "performance_by_ka": {
         "Business Analysis Planning": 0.78,
         "Solution Evaluation": 0.62
       }
     }
     ```

   - GET `/api/v1/analytics/velocity` - Improvement velocity
     ```json
     {
       "weekly_accuracy_change": 3.2,
       "weekly_coverage_change": 8.5,
       "velocity_trend": "accelerating",
       "concepts_mastered_this_week": 45,
       "projected_ready_date": "2025-02-15",
       "days_ahead_of_schedule": 5
     }
     ```

   - GET `/api/v1/analytics/comparison` - Cohort comparison
     ```json
     {
       "percentile_rank": 72,
       "user_accuracy": 0.78,
       "cohort_avg_accuracy": 0.71,
       "cohort_size": 1250,
       "comparison": {
         "accuracy": "above",
         "coverage": "at",
         "study_time": "below"
       }
     }
     ```

   - GET `/api/v1/analytics/export` - Export analytics report
     - Query params: `format=csv|pdf|json`, `date_range=30d|90d|all`
     - Returns downloadable file or JSON

6. **Analytics Schemas** `/app/schemas/analytics.py`:
   ```python
   class OptimalStudyTimes(BaseModel):
       best_study_hour: int
       best_study_day: str
       accuracy_by_hour: dict[int, float]
       accuracy_by_day: dict[str, float]
       avg_session_minutes: float
       recommended_session_length: int
       fatigue_onset_question: int

   class QuestionStat(BaseModel):
       question_id: UUID
       text_preview: str  # First 100 chars
       accuracy: float
       attempts: int
       avg_time_seconds: float

   class ImprovementVelocity(BaseModel):
       weekly_accuracy_change: float
       weekly_coverage_change: float
       velocity_trend: Literal["accelerating", "steady", "slowing"]
       concepts_mastered_this_week: int
       projected_ready_date: date | None
       days_ahead_or_behind: int

   class ComparisonAnalytics(BaseModel):
       percentile_rank: int
       user_accuracy: float
       cohort_avg_accuracy: float
       cohort_size: int
       comparison: dict[str, Literal["above", "at", "below"]]
   ```

7. **Export Report Generator:**
   ```python
   class ReportGenerator:
       """Generate exportable analytics reports."""

       async def generate_pdf_report(self, user_id: UUID, date_range: str) -> bytes:
           """
           Generate PDF progress report.

           Includes:
           - Executive summary (readiness, velocity)
           - KA breakdown with trends
           - Time-based insights
           - Recommendations
           """

       async def generate_csv_export(self, user_id: UUID, date_range: str) -> str:
           """
           Generate CSV with raw analytics data.

           Columns: date, session_id, questions_answered, accuracy,
                    study_time, concepts_covered, ka_scores
           """
   ```

8. **Dashboard Integration:**
   - Analytics summary card on main dashboard
   - "View Detailed Analytics" link to full analytics page
   - Key insight callouts: "You perform best at 2 PM" or "Your velocity is accelerating"

9. **Privacy & Data Handling:**
   - Comparison analytics use only aggregated cohort data
   - No individual user data exposed in comparisons
   - Export includes only requesting user's own data
   - Cohort minimum size: 50 users (below this, show "Insufficient data")

10. **Performance Requirements:**
    - Time analytics: <300ms
    - Question analytics: <500ms
    - Velocity calculation: <200ms
    - Comparison analytics: <400ms (uses pre-computed cohort stats)
    - Export generation: <5s for PDF, <2s for CSV

**Configuration Options:**

| Parameter | Default | Description |
|-----------|---------|-------------|
| `cohort_minimum_size` | 50 | Minimum users for comparison analytics |
| `fatigue_threshold` | 0.10 | Accuracy drop to detect fatigue |
| `velocity_window_days` | 7 | Days for velocity calculation |
| `export_date_range_max` | 365 | Maximum days for export |

**Dependencies:**
- **Requires:** Story 4.10 (Quiz Analytics) - base analytics infrastructure
- **Requires:** Story 4.5 (Coverage Tracking) - coverage data
- **Integrates with:** Epic 6 (Dashboard) - analytics summary display

**Testing Requirements:**

1. Unit tests:
   - `test_optimal_study_time_calculation`: Correct hour/day identification
   - `test_fatigue_analysis`: Fatigue onset detection
   - `test_improvement_velocity`: Velocity trend calculation
   - `test_percentile_rank`: Correct ranking against cohort
   - `test_cohort_minimum_size`: Returns null if cohort too small

2. Integration tests:
   - `test_time_patterns_api`: Returns correct schema
   - `test_question_analytics_api`: Hardest/easiest questions accurate
   - `test_export_csv`: CSV contains expected columns
   - `test_export_pdf`: PDF generates without error

---

## Removed/Consolidated Stories

From original Epic 4:
- **4.2 (Original):** Replaced by Bayesian selection (4.2 BKT)
- **4.4 (Original):** Replaced by Bayesian updates (4.4 BKT)
- **Post-session review (4.6-4.9):** Consolidated into 4.9 BKT

---

## Dependencies

```
Epic 4 Dependencies:

4.1 (Session) → 4.2 (Selection) → 4.3 (Answer) → 4.4 (Belief Update)
4.4 → 4.5 (Coverage) → 4.7 (Termination)
4.3 → 4.6 (Explanation)
4.1 → 4.8 (Focused Mode)
4.3 → 4.9 (Review)
4.4, 4.5 → 4.10 (Analytics)
4.2, 4.4 → 4.11 (Mastery Gates) - integrates with question selector, uses belief updates
4.5 → 4.12 (Exam Readiness) - extends coverage tracking with readiness assessment
4.10, 4.5 → 4.13 (Advanced Analytics) - extends quiz analytics with time/velocity/comparison

Requires from Epic 3:
- Belief states initialized (3.4)
- User authenticated

Requires from Epic 2:
- Questions with concept mappings
- Concepts with prerequisites (2.3) - CRITICAL for Story 4.11
```

---

## Success Metrics

| Metric | Target | Story |
|--------|--------|-------|
| Question selection time | <200ms | 4.2 |
| Belief update time | <50ms | 4.4 |
| Avg info gain per question | >0.5 bits | 4.2 |
| Coverage rate per session | +5-10% | 4.5 |
| Session completion rate | >70% | 4.7 |
| Review completion rate | >60% | 4.9 |
| Questions to 80% coverage | <300 | 4.5 |
| Gate check latency | <20ms | 4.11 |
| Batch unlock check | <200ms | 4.11 |
| Prerequisite violation rate | <5% | 4.11 |
| Override usage rate | <10% | 4.11 |
| Readiness calculation time | <150ms | 4.12 |
| Users reaching "Ready" status | >60% by exam | 4.12 |
| KA balance variance | <20% at readiness | 4.12 |
| Time analytics latency | <300ms | 4.13 |
| Question analytics latency | <500ms | 4.13 |
| Velocity calculation latency | <200ms | 4.13 |
| Export generation (PDF) | <5s | 4.13 |
| Users viewing analytics | >40% weekly | 4.13 |

---

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-11-27 | 2.0 | Redesigned for BKT-first architecture; Question selection uses max info gain (4.2); Belief updates are Bayesian (4.4); Added coverage tracking (4.5); Added adaptive termination (4.7); Added focused practice (4.8) | Sarah (Product Owner) |
| 2025-12-21 | 2.1 | Added Story 4.11: Prerequisite-Based Curriculum Navigation - mastery gates, soft/hard enforcement, unlock notifications, dashboard integration | PM (John) |
| 2025-12-21 | 2.2 | Added Story 4.12: Exam Readiness Assessment & Coverage Gates - FR5C requirements, readiness calculator, KA balance validation, recommendations | PM (John) |
| 2025-12-21 | 2.3 | Added Story 4.13: Advanced Performance Analytics - time-based analytics, question-level insights, improvement velocity, comparison analytics, export reports | PM (John) |
| 2025-12-24 | 2.4 | Story 4.7: Removed AC 9 (Admin reporting) - deferred to Story 10.8 in Admin Content Management epic; renumbered ACs | Sarah (Product Owner) |
| 2025-12-24 | 2.5 | Changed quiz session length from random(10-15) to fixed default of 10 questions for habit-forming consistency; `question_target` field remains configurable | Bob (Scrum Master) |
