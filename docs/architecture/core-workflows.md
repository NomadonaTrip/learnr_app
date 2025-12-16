# Core Workflows

## Status

**ALIGNED** with BKT Architecture (bkt-architecture.md)

---

### Workflow 1: User Registration & Belief Initialization

User completes 7-question onboarding flow (anonymous), then creates account with onboarding data persisted to profile. Upon account creation, belief states are initialized for all concepts.

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant PostgreSQL

    User->>Frontend: Complete onboarding questions
    Frontend->>Frontend: Store answers locally
    User->>Frontend: Submit registration form
    Frontend->>API: POST /auth/register (email, password, onboarding)
    API->>PostgreSQL: Create user record
    API->>PostgreSQL: initialize_beliefs(user_id)
    Note right of PostgreSQL: Creates ~1500 belief states<br/>with Beta(1,1) uninformative prior
    API-->>Frontend: { user, access_token, refresh_token }
    Frontend-->>User: Redirect to dashboard
```

**Key Points:**
- All concepts initialized with Beta(1, 1) = uniform prior ("we know nothing")
- Belief initialization is synchronous (user waits ~1-2 seconds)
- User immediately ready for diagnostic assessment

---

### Workflow 2: Initial Diagnostic Assessment

User takes 12-20 question diagnostic using **balanced coverage** strategy to seed beliefs across all Knowledge Areas. No per-question feedback during assessment.

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant QuestionSelector
    participant BeliefUpdater
    participant PostgreSQL

    User->>Frontend: Start Diagnostic
    Frontend->>API: POST /sessions { type: "diagnostic", strategy: "balanced" }
    API-->>Frontend: { session_id }

    loop 12-20 Questions (Balanced Coverage)
        Frontend->>API: POST /quiz/next-question { strategy: "balanced" }
        API->>PostgreSQL: Get user beliefs
        API->>QuestionSelector: Select question (balanced across KAs)
        QuestionSelector-->>API: Question covering untested KA
        API-->>Frontend: Question (no current belief shown)
        Frontend-->>User: Display question

        User->>Frontend: Select answer
        Frontend->>API: POST /quiz/answer (no immediate feedback)
        API->>BeliefUpdater: Update beliefs for tested concepts
        BeliefUpdater->>PostgreSQL: Persist belief updates
        API-->>Frontend: { is_correct } (stored, not shown)
    end

    User->>Frontend: Complete diagnostic
    Frontend->>API: POST /sessions/{id}/end
    API->>API: Calculate coverage summary
    API-->>Frontend: Diagnostic results + coverage report
    Frontend-->>User: Show initial coverage map
```

**Strategy: Balanced Coverage**
- Ensures questions cover all 6 Knowledge Areas evenly
- Seeds beliefs across the corpus for better subsequent selection
- No feedback during diagnostic to prevent learning bias

**Results Display:**
- Overall readiness score (aggregated from beliefs)
- Per-KA readiness breakdown
- Identified gaps (concepts with P(mastery) < 0.5 and high confidence)
- Estimated questions to full coverage

---

### Workflow 3: Adaptive Quiz with BKT Question Selection

User answers questions selected for **maximum information gain**. Each answer triggers Bayesian belief updates and returns immediate feedback.

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant QuestionSelector
    participant BeliefUpdater
    participant PostgreSQL
    participant Qdrant

    User->>Frontend: Start Quiz
    Frontend->>API: POST /sessions { type: "adaptive", strategy: "max_info_gain" }
    API-->>Frontend: { session_id }

    loop Adaptive Quiz
        Frontend->>API: POST /quiz/next-question { strategy: "max_info_gain" }
        API->>PostgreSQL: Get user belief states
        API->>Qdrant: Get candidate questions
        API->>QuestionSelector: Calculate expected info gain for each question
        Note right of QuestionSelector: Info Gain = H(beliefs) - E[H(beliefs|response)]<br/>Select question with max gain
        QuestionSelector-->>API: Optimal question + concepts tested
        API-->>Frontend: Question with expected_info_gain
        Frontend-->>User: Display question

        User->>Frontend: Submit answer
        Frontend->>API: POST /quiz/answer { question_id, answer, X-Request-ID }
        API->>API: Check idempotency (request_id)
        API->>BeliefUpdater: Bayesian update for tested concepts

        Note right of BeliefUpdater: For each concept:<br/>P(L|correct) = (1-slip)·P(L) / P(correct)<br/>Update α, β via moment matching

        BeliefUpdater->>PostgreSQL: Persist updated beliefs
        BeliefUpdater->>PostgreSQL: Propagate to prerequisites (weaker update)
        API->>PostgreSQL: Store response + belief_updates snapshot
        API-->>Frontend: { is_correct, explanation, belief_updates }
        Frontend-->>User: Show feedback + "Strengthened N concepts"

        opt Incorrect Answer
            API->>API: Queue reading recommendation
            API-->>Frontend: reading_recommendation in response
        end
    end
```

**Question Selection: Max Information Gain**
```
For each candidate question Q:
  1. Get concepts C tested by Q
  2. Calculate current entropy H(beliefs) for C
  3. Simulate belief update if correct → H(beliefs|correct)
  4. Simulate belief update if incorrect → H(beliefs|incorrect)
  5. P(correct) = (1-slip)·mean + guess·(1-mean)
  6. Expected posterior entropy = P(correct)·H(correct) + P(incorrect)·H(incorrect)
  7. Info gain = H(current) - Expected posterior entropy

Select Q with maximum info gain
```

**Belief Update (Bayesian):**
```python
# On correct answer:
p_correct = (1 - slip) * p_mastered + guess * (1 - p_mastered)
posterior_mastered = (1 - slip) * p_mastered / p_correct
new_alpha = alpha + posterior_mastered
new_beta = beta + (1 - posterior_mastered)
```

---

### Workflow 4: Coverage Analysis & Gap Identification

User views their coverage report showing mastered concepts, gaps, and uncertain areas.

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant CoverageAnalyzer
    participant PostgreSQL

    User->>Frontend: Navigate to Coverage page
    Frontend->>API: GET /coverage/summary
    API->>PostgreSQL: Get all belief states for user
    API->>CoverageAnalyzer: Analyze coverage

    Note right of CoverageAnalyzer: For each belief:<br/>mean = α/(α+β)<br/>confidence = (α+β)/(α+β+10)<br/><br/>if confidence ≥ 0.7:<br/>  if mean ≥ 0.8 → mastered<br/>  if mean ≤ 0.5 → gap<br/>  else → borderline<br/>else → uncertain

    CoverageAnalyzer-->>API: CoverageReport
    API-->>Frontend: { total, mastered, gaps, uncertain, coverage_% }
    Frontend-->>User: Display coverage summary

    opt User clicks "View Gaps"
        Frontend->>API: GET /coverage/gaps
        API->>CoverageAnalyzer: Get sorted gaps
        CoverageAnalyzer-->>API: Gaps sorted by priority
        Note right of CoverageAnalyzer: Priority = (1 - probability) × confidence
        API-->>Frontend: Gap concepts with priorities
        Frontend-->>User: Display gap analysis panel
    end

    opt User clicks Knowledge Area bar
        Frontend->>API: GET /coverage/by-knowledge-area
        API-->>Frontend: Per-KA breakdown
        Frontend-->>User: Show KA detail with concept-level beliefs
    end
```

**Coverage Classification Thresholds:**
| Status | Criteria |
|--------|----------|
| Mastered | mean ≥ 0.8 AND confidence ≥ 0.7 |
| Gap | mean ≤ 0.5 AND confidence ≥ 0.7 |
| Borderline | 0.5 < mean < 0.8 AND confidence ≥ 0.7 |
| Uncertain | confidence < 0.7 |

---

### Workflow 5: Focused Study (Gap Remediation)

User focuses on a specific Knowledge Area or gap concept using **prerequisite-first** strategy.

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant QuestionSelector
    participant PostgreSQL

    User->>Frontend: Click "Study This Knowledge Area" or gap concept
    Frontend->>API: POST /sessions { type: "focused", strategy: "prerequisite_first", ka_filter: "Strategy Analysis" }
    API-->>Frontend: { session_id }

    loop Focused Quiz
        Frontend->>API: POST /quiz/next-question { strategy: "prerequisite_first", ka_filter }
        API->>PostgreSQL: Get beliefs for KA concepts
        API->>PostgreSQL: Get prerequisite graph for gaps
        API->>QuestionSelector: Select question (prerequisites first)

        Note right of QuestionSelector: 1. Identify gap concepts in KA<br/>2. Find prerequisites of gaps<br/>3. Prioritize prerequisites with low confidence<br/>4. Build from foundations upward

        QuestionSelector-->>API: Question on prerequisite concept
        API-->>Frontend: Question
        Frontend-->>User: Display question

        User->>Frontend: Submit answer
        Frontend->>API: POST /quiz/answer
        API-->>Frontend: Feedback + belief updates
        Frontend-->>User: Show progress on gap remediation
    end
```

**Prerequisite-First Strategy:**
1. Get gap concepts in target KA
2. Traverse prerequisite DAG to find foundational concepts
3. Check if prerequisites are mastered
4. If prerequisite uncertain/gap → ask about prerequisite first
5. Once prerequisites solid → ask about target gap

---

### Workflow 6: Reading Library with Gap-Linked Recommendations

User accesses reading library with items prioritized by gap concepts.

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant PostgreSQL
    participant Qdrant

    User->>Frontend: Navigate to Reading Library
    Frontend->>API: GET /reading-queue
    API->>PostgreSQL: Get queue items with priorities
    API-->>Frontend: Items sorted by priority (High gaps first)
    Frontend-->>User: Display prioritized reading list

    opt Background: After incorrect answer
        API->>PostgreSQL: Get gap concept from question
        API->>Qdrant: Find reading chunks matching concept
        API->>PostgreSQL: Add to reading_queue with triggered_by_concept_id
        Note right of API: Priority based on:<br/>- Concept gap severity<br/>- Recency of incorrect answer<br/>- Chunk relevance score
    end

    User->>Frontend: Click reading item
    Frontend->>API: PUT /reading-queue/{id} { status: "reading" }
    Frontend-->>User: Display BABOK content
    Note right of User: Content linked to gap concept<br/>explains underlying principles

    User->>Frontend: Mark as complete
    Frontend->>API: PUT /reading-queue/{id} { status: "completed" }
    API->>PostgreSQL: Update reading_queue
    API-->>Frontend: Updated queue
```

**Reading Priority Calculation:**
```
priority_score = (1 - concept_probability) × concept_confidence × chunk_relevance

High: priority_score > 0.6
Medium: 0.3 < priority_score ≤ 0.6
Low: priority_score ≤ 0.3
```

---

### Workflow 7: Post-Session Review (Reinforcement)

After completing a quiz session, user re-answers incorrect questions for reinforcement learning.

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant BeliefUpdater
    participant PostgreSQL

    User->>Frontend: End quiz session
    Frontend->>API: POST /sessions/{id}/end
    API-->>Frontend: Session summary + incorrect count

    opt Has incorrect answers
        Frontend-->>User: "Review 5 incorrect questions?"
        User->>Frontend: Accept review
        Frontend->>API: POST /sessions/{id}/review/start
        API->>PostgreSQL: Get incorrect responses from session
        API-->>Frontend: Incorrect questions for review

        loop Review incorrect questions
            Frontend-->>User: Show question + "You answered X, correct is Y"
            User->>Frontend: Re-answer question
            Frontend->>API: POST /sessions/{id}/review/answer
            API->>BeliefUpdater: Update belief (review response)
            Note right of BeliefUpdater: Review correct = stronger positive update<br/>Review incorrect = weaker negative update
            BeliefUpdater->>PostgreSQL: Update beliefs
            API-->>Frontend: Review feedback
        end

        Frontend-->>User: Review complete summary
    end
```

**Review Belief Updates:**
- Correct on review: Stronger evidence of learning (higher weight)
- Incorrect on review: Identifies persistent gap (add to high-priority reading)

---

### Workflow 8: Multi-Device Concurrent Access

User accesses LearnR from multiple devices; system handles concurrent sessions safely.

```mermaid
sequenceDiagram
    participant Device_A
    participant Device_B
    participant API
    participant PostgreSQL

    Device_A->>API: POST /sessions (start quiz)
    API->>PostgreSQL: Create session (version=1)
    API-->>Device_A: { session_id, version: 1 }

    Device_B->>API: POST /sessions (start quiz)
    API->>PostgreSQL: Create new session (separate)
    API-->>Device_B: { session_id_2, version: 1 }

    Note right of API: Two separate sessions OK

    Device_A->>API: POST /quiz/answer (X-Request-ID: abc)
    API->>PostgreSQL: Update beliefs (row lock)
    API-->>Device_A: Success

    Device_B->>API: POST /quiz/answer (X-Request-ID: def)
    API->>PostgreSQL: Update beliefs (row lock, serialized)
    API-->>Device_B: Success

    Note right of API: Belief updates serialized via row locks

    Device_A->>API: POST /sessions/{id}/end (version: 1)
    API->>PostgreSQL: End session, version check passes
    API-->>Device_A: Session ended

    Device_B->>API: POST /quiz/answer on session_1
    API-->>Device_B: 409 SESSION_ENDED
    Device_B-->>Device_B: Show "Session ended on another device"
```

**Concurrency Guarantees:**
- Separate sessions allowed (no conflict)
- Belief updates use row-level locking (serialized)
- Session modifications use optimistic locking (version check)
- Duplicate submissions prevented via request_id

---

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-12-03 | 2.0 | Aligned with BKT Architecture - updated all workflows for belief states, question selection strategies, coverage analysis | Winston (Architect) |
| 2025-11-01 | 1.0 | Initial core workflows | Original |
