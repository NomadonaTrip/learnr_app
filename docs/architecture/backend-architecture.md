# Backend Architecture

### Service Architecture

**Traditional Server (FastAPI on Railway)**

Layered architecture: API Routes → Services → Repositories → Database

```
apps/api/src/
├── main.py              # FastAPI app entry
├── routes/              # API route handlers
├── services/            # Business logic layer
├── repositories/        # Data access layer
├── models/              # SQLAlchemy ORM models
├── schemas/             # Pydantic schemas
├── middleware/          # Auth, CORS, rate limiting
├── tasks/               # Celery background tasks
└── utils/               # Utilities (IRT, SM-2)
```

### Repository Pattern

All database access abstracted through repositories:
- `UserRepository`, `QuestionRepository`, `ResponseRepository`, etc.
- Async methods for non-blocking I/O
- Enables testing with mock repositories

### Authentication

**JWT-based authentication:**
- Access tokens (15 min expiry)
- Refresh tokens (7 day expiry)
- Redis blacklist for logout support
- bcrypt password hashing (cost factor 12)
- Dependency injection for current user in routes

### Concurrent Session Handling

**Challenge:** Users may access LearnR from multiple devices simultaneously (e.g., desktop at home, laptop at work, mobile during commute). The system must handle concurrent quiz sessions, competency updates, and reading queue modifications without data corruption.

**Strategy: Optimistic Locking with Conflict Detection**

#### Database-Level Concurrency Control

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

**Update Pattern (SQLAlchemy):**
```python
# apps/api/src/repositories/session_repository.py
from sqlalchemy import and_
from sqlalchemy.exc import StaleDataError

async def end_session(session_id: UUID, expected_version: int) -> QuizSession:
    """
    End a quiz session with optimistic locking.

    Raises:
        ConcurrentModificationError: If session was modified by another device
    """
    result = await db.execute(
        update(QuizSession)
        .where(and_(
            QuizSession.id == session_id,
            QuizSession.version == expected_version  # Optimistic lock check
        ))
        .values(ended_at=datetime.utcnow())
        .returning(QuizSession)
    )

    session = result.scalar_one_or_none()

    if session is None:
        raise ConcurrentModificationError(
            "Session was modified by another device. Please refresh and try again."
        )

    return session
```

#### Quiz Session Conflict Resolution

**Rule: Last-Write-Wins for Session Metadata, Merge for Responses**

| Scenario | Resolution Strategy | Example |
|----------|---------------------|---------|
| **User starts quiz on Device A, then Device B** | Allow both sessions (separate session IDs) | Two distinct quiz sessions created |
| **User ends session on Device A, Device B tries to submit answer** | Return 409 Conflict, prompt user to refresh | Frontend shows: "This session ended on another device" |
| **Same answer submitted twice (network retry)** | Idempotency: use `response_id` (client-generated UUID) | Duplicate response ignored, return existing |
| **Competency updated concurrently** | Row-level locking on `competencies` table | Serialized updates via PostgreSQL row lock |

#### Response Idempotency

**Challenge:** Network retries may cause duplicate answer submissions.

**Solution: Client-Generated Request IDs**

**Frontend:**
```typescript
// apps/web/src/services/quizService.ts
import { v4 as uuidv4 } from 'uuid';

export async function submitAnswer(questionId: string, answer: string) {
  const requestId = uuidv4(); // Client-generated idempotency key

  const response = await fetch(`/api/v1/questions/${questionId}/answer`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Request-ID': requestId,
    },
    body: JSON.stringify({ answer, request_id: requestId }),
  });

  return response.json();
}
```

**Backend:**
```python
# apps/api/src/routes/questions.py
from fastapi import Header

@router.post("/{question_id}/answer")
async def submit_answer(
    question_id: UUID,
    answer_data: AnswerSubmission,
    x_request_id: str = Header(..., alias="X-Request-ID"),
    user = Depends(get_current_user),
):
    """
    Submit answer with idempotency via request_id.

    If request_id already exists in responses table, return existing response.
    """
    # Check for existing response with same request_id
    existing = await response_repo.get_by_request_id(x_request_id)
    if existing:
        return existing  # Idempotent: return cached response

    # Create new response
    response = await response_repo.create(
        user_id=user.id,
        question_id=question_id,
        selected_answer=answer_data.answer,
        request_id=x_request_id,  # Store for idempotency
    )

    return response
```

**Database Schema Addition:**
```sql
ALTER TABLE responses ADD COLUMN request_id UUID UNIQUE;
CREATE INDEX idx_responses_request_id ON responses(request_id);
```

#### Competency Update Locking

**Challenge:** Competency scores updated concurrently from multiple sessions may produce incorrect results.

**Solution: Row-Level Locking**

```python
# apps/api/src/services/adaptive_engine.py
from sqlalchemy import select

async def update_competency(user_id: UUID, knowledge_area: str, delta: float):
    """
    Update competency with row-level locking to prevent concurrent modification.
    """
    async with db.begin():  # Transaction
        # Acquire row lock (SELECT ... FOR UPDATE)
        result = await db.execute(
            select(Competency)
            .where(and_(
                Competency.user_id == user_id,
                Competency.knowledge_area == knowledge_area
            ))
            .with_for_update()  # Row-level lock
        )

        competency = result.scalar_one()

        # Update competency score
        competency.score = min(100, max(0, competency.score + delta))
        competency.last_updated = datetime.utcnow()

        await db.flush()

    return competency
```

**Performance:** Row locks are released at transaction commit, minimal contention for single-user updates.

#### Reading Queue Deduplication

**Challenge:** Multiple quiz sessions may trigger duplicate reading queue items.

**Solution: Unique Constraint + INSERT ... ON CONFLICT**

```sql
ALTER TABLE reading_queue
ADD CONSTRAINT unique_user_chunk UNIQUE (user_id, chunk_id);
```

```python
# apps/api/src/repositories/reading_repository.py
async def add_to_queue(user_id: UUID, chunk_id: UUID, priority: str):
    """
    Add reading item to queue with deduplication.

    If (user_id, chunk_id) already exists, update priority if higher.
    """
    query = insert(ReadingQueue).values(
        user_id=user_id,
        chunk_id=chunk_id,
        priority=priority,
        added_at=datetime.utcnow(),
    ).on_conflict_do_update(
        constraint='unique_user_chunk',
        set_={
            'priority': func.greatest(ReadingQueue.priority, priority),
            'added_at': datetime.utcnow(),  # Refresh timestamp
        }
    )

    await db.execute(query)
```

#### Frontend Conflict UI

**User Experience for Conflicts:**

**Scenario 1: Session Ended on Another Device**
```tsx
// Frontend error handler
if (error.status === 409 && error.code === 'SESSION_ENDED') {
  showToast({
    type: 'warning',
    message: 'This session ended on another device. Redirecting to dashboard...',
    duration: 3000,
  });

  setTimeout(() => navigate('/dashboard'), 3000);
}
```

**Scenario 2: Optimistic Lock Failure**
```tsx
if (error.status === 409 && error.code === 'CONCURRENT_MODIFICATION') {
  showToast({
    type: 'error',
    message: 'Data changed on another device. Refreshing...',
    duration: 2000,
  });

  // Refetch latest data
  queryClient.invalidateQueries(['session', sessionId]);
}
```

#### Monitoring & Alerting

**Metrics to Track:**
- Concurrent session conflict rate (target: <1% of requests)
- Optimistic lock failures (alert if >5% over 5 minutes)
- Duplicate request_id occurrences (indicates network retry behavior)

**Logging:**
```python
logger.info(
    "Concurrent modification detected",
    extra={
        "user_id": user_id,
        "resource": "quiz_session",
        "expected_version": expected_version,
        "actual_version": actual_version,
    }
)
```

#### Edge Cases

| Edge Case | Handling |
|-----------|----------|
| **User starts session on Device A, loses network, continues on Device B** | Device A session times out after 30 min inactivity; Device B creates new session |
| **User submits same answer twice (double-click)** | Request ID deduplication prevents duplicate response |
| **User updates profile on Device A while quiz running on Device B** | Independent updates; no conflict (separate tables) |
| **Reading queue badge count stale on Device A** | Periodic polling (30s) + refresh on app focus ensures eventual consistency |

**Key Principle:** Prioritize user experience over perfect consistency. Eventual consistency is acceptable for analytics (e.g., badge counts), but critical data (responses, competency) uses strong consistency (locking).

---
