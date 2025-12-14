# Backend Architecture

## Status

**ALIGNED** with BKT Architecture (bkt-architecture.md)

---

## Service Architecture

**Traditional Server (FastAPI on Railway)**

Layered architecture: API Routes → Services → Repositories → Database

```
apps/api/src/
├── main.py              # FastAPI app entry
├── routes/              # API route handlers
│   ├── auth.py          # Authentication endpoints
│   ├── quiz.py          # Quiz flow with BKT question selection
│   ├── beliefs.py       # Belief state endpoints
│   └── coverage.py      # Coverage report endpoints
├── services/            # Business logic layer
│   ├── belief_updater.py    # BKT belief update logic
│   ├── question_selector.py # Optimal question selection
│   ├── coverage_analyzer.py # Coverage assessment
│   └── auth_service.py      # Authentication logic
├── repositories/        # Data access layer
│   ├── belief_repository.py    # Belief state CRUD
│   ├── concept_repository.py   # Concept/prerequisite access
│   ├── question_repository.py  # Question + concept mappings
│   └── response_repository.py  # Response logging
├── models/              # SQLAlchemy ORM models
├── schemas/             # Pydantic schemas
├── middleware/          # Auth, CORS, rate limiting
├── tasks/               # Celery background tasks
└── utils/               # Utilities (BKT math, Beta distribution)
```

---

## Core BKT Services

### BeliefUpdater Service

Updates belief states after observing a user response using Bayesian inference.

```python
# apps/api/src/services/belief_updater.py
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
        """Update beliefs for all concepts affected by this response."""
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

        # 2. Propagate to prerequisites (weaker update) on correct answers
        if is_correct:
            prerequisite_ids = await self._get_prerequisites(question.concept_ids)
            for prereq_id in prerequisite_ids:
                if prereq_id in updates or prereq_id not in beliefs:
                    continue
                belief = beliefs[prereq_id]
                updates[prereq_id] = BeliefState(
                    user_id=user_id,
                    concept_id=prereq_id,
                    alpha=belief.alpha + self.prerequisite_propagation,
                    beta=belief.beta,
                    response_count=belief.response_count
                )

        await self._persist_updates(updates)
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

        new_alpha = alpha + posterior_mastered
        new_beta = beta + (1 - posterior_mastered)

        return new_alpha, new_beta
```

### QuestionSelector Service

Selects questions to maximize expected information gain.

```python
# apps/api/src/services/question_selector.py
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
            candidates = available_questions  # Fallback

        if strategy == "max_info_gain":
            return self._select_by_info_gain(candidates, beliefs)
        elif strategy == "max_uncertainty":
            return self._select_by_uncertainty(candidates, beliefs)
        elif strategy == "prerequisite_first":
            return self._select_by_prerequisites(candidates, beliefs)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

    def _calculate_expected_info_gain(
        self,
        question: Question,
        beliefs: Dict[UUID, BeliefState]
    ) -> float:
        """
        Calculate expected reduction in total entropy.

        Info Gain = H(beliefs) - E[H(beliefs | response)]
        """
        current_entropy = sum(
            self._belief_entropy(beliefs[c_id])
            for c_id in question.concept_ids
            if c_id in beliefs
        )

        p_correct = self._predict_correct_probability(question, beliefs)

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
```

### CoverageAnalyzer Service

Analyzes corpus coverage and generates reports.

```python
# apps/api/src/services/coverage_analyzer.py
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
        mastered, gaps, uncertain = [], [], []

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
```

---

## Repository Pattern

All database access abstracted through repositories:

### Belief Repository

```python
# apps/api/src/repositories/belief_repository.py
class BeliefRepository:
    """Repository for belief state CRUD operations."""

    async def get_all_beliefs(self, user_id: UUID) -> Dict[UUID, BeliefState]:
        """Get all belief states for a user."""
        pass

    async def bulk_create(self, beliefs: List[BeliefState]) -> None:
        """Initialize beliefs for a new user (all concepts)."""
        pass

    async def bulk_update(self, updates: Dict[UUID, BeliefState]) -> None:
        """Batch update belief states after responses."""
        pass

    async def get_by_knowledge_area(
        self, user_id: UUID, knowledge_area: str
    ) -> List[BeliefState]:
        """Get beliefs filtered by knowledge area (for UI aggregation)."""
        pass
```

### Concept Repository

```python
# apps/api/src/repositories/concept_repository.py
class ConceptRepository:
    """Repository for concept and prerequisite access."""

    async def get_all_concepts(self) -> List[Concept]:
        """Get all concepts for belief initialization."""
        pass

    async def get_prerequisites(self, concept_ids: List[UUID]) -> List[UUID]:
        """Get prerequisite concept IDs for propagation."""
        pass

    async def get_concepts_by_question(self, question_id: UUID) -> List[Concept]:
        """Get concepts tested by a question."""
        pass
```

### Question Repository

```python
# apps/api/src/repositories/question_repository.py
class QuestionRepository:
    """Repository for questions with concept mappings."""

    async def get_questions_with_concepts(self) -> List[Question]:
        """Get all questions with their concept mappings for selection."""
        pass

    async def get_recent_questions(
        self, user_id: UUID, days: int = 7
    ) -> List[UUID]:
        """Get question IDs asked recently (for recency filtering)."""
        pass
```

---

## Data Model

### Core Entities (from BKT Architecture)

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
│  ├── request_id (UUID, UNIQUE) - idempotency key                   │
│  └── created_at                                                    │
└─────────────────────────────────────────────────────────────────────┘
```

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

## Authentication

**JWT-based authentication:**
- Access tokens (15 min expiry)
- Refresh tokens (7 day expiry)
- Redis blacklist for logout support
- bcrypt password hashing (cost factor 12)
- Dependency injection for current user in routes

---

## Concurrent Session Handling

**Challenge:** Users may access LearnR from multiple devices simultaneously. The system must handle concurrent quiz sessions and belief state updates without data corruption.

**Strategy: Optimistic Locking with Conflict Detection**

### Database-Level Concurrency Control

**Optimistic Locking Pattern:**
All tables with concurrent write risk include `updated_at` timestamp column with automatic trigger updates.

```sql
-- Example: quiz_sessions table
CREATE TABLE quiz_sessions (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMP,
    version INTEGER NOT NULL DEFAULT 1,  -- Optimistic lock version
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Trigger: auto-update version on modification
CREATE OR REPLACE FUNCTION update_version_and_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.version = OLD.version + 1;
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER quiz_sessions_version_trigger
BEFORE UPDATE ON quiz_sessions
FOR EACH ROW
EXECUTE FUNCTION update_version_and_timestamp();
```

### Quiz Session Conflict Resolution

**Rule: Last-Write-Wins for Session Metadata, Merge for Responses**

| Scenario | Resolution Strategy | Example |
|----------|---------------------|---------|
| **User starts quiz on Device A, then Device B** | Allow both sessions (separate session IDs) | Two distinct quiz sessions created |
| **User ends session on Device A, Device B tries to submit answer** | Return 409 Conflict, prompt user to refresh | Frontend shows: "This session ended on another device" |
| **Same answer submitted twice (network retry)** | Idempotency: use `request_id` (client-generated UUID) | Duplicate response ignored, return existing |
| **Belief state updated concurrently** | Row-level locking on `belief_states` table | Serialized updates via PostgreSQL row lock |

### Response Idempotency

**Challenge:** Network retries may cause duplicate answer submissions.

**Solution: Client-Generated Request IDs**

```python
# apps/api/src/routes/quiz.py
@router.post("/answer")
async def submit_answer(
    answer_data: AnswerSubmission,
    x_request_id: str = Header(..., alias="X-Request-ID"),
    user = Depends(get_current_user),
):
    """
    Submit answer with idempotency via request_id.
    If request_id already exists in responses table, return existing response.
    """
    existing = await response_repo.get_by_request_id(x_request_id)
    if existing:
        return existing  # Idempotent: return cached response

    # Create new response and update beliefs
    response = await response_repo.create(
        user_id=user.id,
        question_id=answer_data.question_id,
        selected_answer=answer_data.answer,
        request_id=x_request_id,
    )

    # Update beliefs for all concepts tested by this question
    belief_updates = await belief_updater.update_beliefs(
        user_id=user.id,
        question=question,
        is_correct=response.is_correct,
        beliefs=current_beliefs
    )

    return AnswerResponse(
        is_correct=response.is_correct,
        explanation=question.explanation,
        belief_updates=belief_updates
    )
```

### Belief State Update Locking

**Challenge:** Belief states updated concurrently from multiple sessions may produce incorrect results.

**Solution: Row-Level Locking**

```python
# apps/api/src/repositories/belief_repository.py
async def update_belief_with_lock(
    user_id: UUID,
    concept_id: UUID,
    new_alpha: float,
    new_beta: float
) -> BeliefState:
    """
    Update belief state with row-level locking to prevent concurrent modification.
    """
    async with db.begin():
        result = await db.execute(
            select(BeliefState)
            .where(and_(
                BeliefState.user_id == user_id,
                BeliefState.concept_id == concept_id
            ))
            .with_for_update()  # Row-level lock
        )

        belief = result.scalar_one()
        belief.alpha = new_alpha
        belief.beta = new_beta
        belief.last_response_at = datetime.utcnow()
        belief.response_count += 1

        await db.flush()

    return belief
```

---

## Resilience Patterns

### Circuit Breakers for External Services

LearnR depends on external services that may experience outages. Circuit breakers prevent cascading failures and provide graceful degradation.

**Implementation:** Using `circuitbreaker` Python library with Redis-backed state for distributed environments.

```python
# apps/api/src/utils/circuit_breaker.py
from circuitbreaker import circuit
from functools import wraps
import structlog

logger = structlog.get_logger()

class CircuitBreakerConfig:
    """Configuration for external service circuit breakers."""

    OPENAI = {
        "failure_threshold": 5,      # Open after 5 consecutive failures
        "recovery_timeout": 30,      # Try again after 30 seconds
        "expected_exception": (OpenAIError, TimeoutError, ConnectionError),
    }

    QDRANT = {
        "failure_threshold": 3,      # Open after 3 consecutive failures
        "recovery_timeout": 15,      # Try again after 15 seconds
        "expected_exception": (QdrantException, TimeoutError, ConnectionError),
    }

    SENDGRID = {
        "failure_threshold": 5,
        "recovery_timeout": 60,
        "expected_exception": (SendGridException, TimeoutError),
    }


# OpenAI Circuit Breaker
@circuit(
    failure_threshold=CircuitBreakerConfig.OPENAI["failure_threshold"],
    recovery_timeout=CircuitBreakerConfig.OPENAI["recovery_timeout"],
    expected_exception=CircuitBreakerConfig.OPENAI["expected_exception"],
)
async def call_openai_with_circuit_breaker(func, *args, **kwargs):
    """Wrap OpenAI API calls with circuit breaker."""
    return await func(*args, **kwargs)


# Qdrant Circuit Breaker
@circuit(
    failure_threshold=CircuitBreakerConfig.QDRANT["failure_threshold"],
    recovery_timeout=CircuitBreakerConfig.QDRANT["recovery_timeout"],
    expected_exception=CircuitBreakerConfig.QDRANT["expected_exception"],
)
async def call_qdrant_with_circuit_breaker(func, *args, **kwargs):
    """Wrap Qdrant API calls with circuit breaker."""
    return await func(*args, **kwargs)
```

### Circuit Breaker States

| State | Behavior | Transition |
|-------|----------|------------|
| **CLOSED** | Normal operation, requests pass through | → OPEN after N failures |
| **OPEN** | All requests fail immediately (no external call) | → HALF-OPEN after timeout |
| **HALF-OPEN** | Single test request allowed | → CLOSED on success, → OPEN on failure |

### Service-Specific Circuit Breakers

#### OpenAI (Embeddings & LLM)

```python
# apps/api/src/services/embedding_service.py
class EmbeddingService:
    """Generate embeddings with circuit breaker and fallback."""

    async def generate_embedding(self, text: str) -> List[float]:
        try:
            return await call_openai_with_circuit_breaker(
                self._openai_embed, text
            )
        except CircuitBreakerError:
            logger.warning("OpenAI circuit breaker OPEN, using cached embedding")
            return await self._get_cached_or_fallback(text)

    async def _get_cached_or_fallback(self, text: str) -> List[float]:
        """Fallback when OpenAI is unavailable."""
        # 1. Check Redis cache for previously computed embedding
        cached = await self.redis.get(f"embedding:{hash(text)}")
        if cached:
            return json.loads(cached)

        # 2. Return zero vector (degrades search quality but doesn't break)
        logger.error("No cached embedding, returning zero vector")
        return [0.0] * 3072  # text-embedding-3-large dimension
```

#### Qdrant (Vector Search)

```python
# apps/api/src/services/vector_search_service.py
class VectorSearchService:
    """Vector search with circuit breaker and fallback."""

    async def search_similar_questions(
        self,
        query_vector: List[float],
        limit: int = 10
    ) -> List[Question]:
        try:
            return await call_qdrant_with_circuit_breaker(
                self._qdrant_search, query_vector, limit
            )
        except CircuitBreakerError:
            logger.warning("Qdrant circuit breaker OPEN, using PostgreSQL fallback")
            return await self._postgres_fallback_search(limit)

    async def _postgres_fallback_search(self, limit: int) -> List[Question]:
        """Fallback: Random questions from PostgreSQL when Qdrant down."""
        # Select random questions weighted by uncertainty
        return await self.question_repo.get_random_by_uncertainty(
            user_id=self.user_id,
            limit=limit
        )
```

#### SendGrid (Email)

```python
# apps/api/src/services/email_service.py
class EmailService:
    """Email service with circuit breaker and queue fallback."""

    async def send_email(self, to: str, subject: str, body: str) -> bool:
        try:
            return await call_sendgrid_with_circuit_breaker(
                self._sendgrid_send, to, subject, body
            )
        except CircuitBreakerError:
            logger.warning("SendGrid circuit breaker OPEN, queueing email")
            await self._queue_for_retry(to, subject, body)
            return False  # Email queued, not sent

    async def _queue_for_retry(self, to: str, subject: str, body: str):
        """Queue email in Redis for Celery retry task."""
        await self.redis.rpush("email_queue", json.dumps({
            "to": to,
            "subject": subject,
            "body": body,
            "queued_at": datetime.utcnow().isoformat()
        }))
```

---

## Failure Scenario Matrix

This matrix documents system behavior when each external dependency fails.

### External Service Failures

| Service | Failure Mode | Detection | User Impact | Fallback Behavior | Recovery |
|---------|--------------|-----------|-------------|-------------------|----------|
| **OpenAI API** | Timeout/5xx | Circuit breaker (5 failures) | Cannot generate new embeddings | Use cached embeddings; new content import disabled | Auto-recover when circuit closes |
| **OpenAI API** | Rate limit (429) | Exponential backoff | Slower embedding generation | Queue and retry with backoff | Backoff resolves automatically |
| **Qdrant** | Timeout/Connection | Circuit breaker (3 failures) | Degraded question selection | PostgreSQL random selection weighted by uncertainty | Auto-recover when circuit closes |
| **Qdrant** | Data corruption | Health check failure | Reading retrieval broken | Disable reading recommendations; quiz continues | Manual intervention required |
| **PostgreSQL** | Connection pool exhausted | Connection timeout | All requests fail | N/A (critical dependency) | Auto-scale connections; alert on-call |
| **PostgreSQL** | Replication lag | Read-after-write inconsistency | Stale data displayed | Force primary reads for critical paths | Lag resolves automatically |
| **Redis** | Connection failure | Sentinel detection | Rate limiting disabled; sessions degraded | Stateless fallback (no caching) | Sentinel failover to replica |
| **SendGrid** | API error | Circuit breaker (5 failures) | Password reset emails delayed | Queue in Redis; Celery retry every 5 min | Auto-recover or manual flush |
| **Vercel (CDN)** | Edge failure | External monitoring | Frontend unavailable | N/A (user sees error page) | Vercel auto-failover |
| **Railway** | Container crash | Health check failure | API unavailable | Auto-restart; load balancer routes to healthy instances | Auto-recover via health checks |

### Internal Service Failures

| Component | Failure Mode | Detection | User Impact | Fallback Behavior | Recovery |
|-----------|--------------|-----------|-------------|-------------------|----------|
| **BKT Engine** | Calculation error | Exception logging | Wrong question selection | Fall back to random selection | Deploy fix |
| **Belief Updater** | Transaction deadlock | Database timeout | Belief state not updated | Retry with exponential backoff | Retry succeeds |
| **Coverage Analyzer** | Timeout on large dataset | Request timeout | Dashboard shows stale data | Return cached coverage summary | Background refresh |
| **Celery Worker** | Queue backlog | Queue depth monitoring | Background tasks delayed | Scale workers; prioritize critical tasks | Auto-scale or manual intervention |

### Graceful Degradation Hierarchy

When multiple services fail, the system degrades gracefully in this priority order:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    FULL FUNCTIONALITY                                    │
│  All services operational: BKT selection, reading recommendations,      │
│  real-time analytics, email notifications                               │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼ Qdrant fails
┌─────────────────────────────────────────────────────────────────────────┐
│                    DEGRADED: NO SEMANTIC SEARCH                         │
│  Quiz continues with PostgreSQL-based question selection               │
│  Reading recommendations disabled (show "temporarily unavailable")      │
│  Analytics and email continue normally                                  │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼ OpenAI fails
┌─────────────────────────────────────────────────────────────────────────┐
│                    DEGRADED: NO NEW EMBEDDINGS                          │
│  Existing content works; new question/content import disabled           │
│  Quiz continues with existing question bank                             │
│  Admin notified to pause content operations                             │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼ Redis fails
┌─────────────────────────────────────────────────────────────────────────┐
│                    DEGRADED: NO CACHING                                 │
│  Rate limiting disabled (accept increased load risk)                    │
│  Session cache unavailable (stateless JWT still works)                  │
│  Coverage cache unavailable (calculate on every request)                │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼ PostgreSQL fails
┌─────────────────────────────────────────────────────────────────────────┐
│                    CRITICAL: MAINTENANCE MODE                           │
│  All API requests return 503 Service Unavailable                        │
│  Frontend shows maintenance page                                        │
│  On-call engineer paged immediately                                     │
└─────────────────────────────────────────────────────────────────────────┘
```

### Alerting Thresholds

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| Circuit breaker OPEN events | 1 in 5 min | 3 in 5 min | Page on-call |
| API error rate (5xx) | >1% | >5% | Page on-call |
| Response latency p95 | >500ms | >2000ms | Investigate |
| PostgreSQL connections | >70% pool | >90% pool | Scale pool |
| Redis memory | >80% | >95% | Scale instance |
| Celery queue depth | >1000 tasks | >5000 tasks | Scale workers |

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

## Monitoring & Alerting

**Metrics to Track:**
- Concurrent session conflict rate (target: <1% of requests)
- Optimistic lock failures (alert if >5% over 5 minutes)
- Duplicate request_id occurrences (indicates network retry behavior)
- Question selection latency (target: <100ms)
- Belief update latency (target: <50ms)

**Logging:**
```python
logger.info(
    "Belief update completed",
    extra={
        "user_id": user_id,
        "question_id": question_id,
        "concepts_updated": len(belief_updates),
        "duration_ms": duration_ms,
    }
)
```

---

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-12-08 | 2.1 | Added Resilience Patterns section - circuit breakers for OpenAI/Qdrant/SendGrid, failure scenario matrix, graceful degradation hierarchy, alerting thresholds | Winston (Architect) |
| 2025-12-03 | 2.0 | Aligned with BKT Architecture - replaced competency model with belief states | Winston (Architect) |
| 2025-11-01 | 1.0 | Initial backend architecture | Original |
