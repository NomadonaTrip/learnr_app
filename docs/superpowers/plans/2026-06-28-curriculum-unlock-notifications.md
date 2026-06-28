# Curriculum Unlock Notifications (Slice C) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Record concept-unlock events when belief updates cross a mastery gate, then surface them to the user as a single post-session toast and a "recently unlocked" strip on `/curriculum`.

**Architecture:** Backend wires the existing (but never-called) `MasteryGateService.check_and_record_unlocks` into the quiz and review answer pipelines, and returns this-session unlocks inline on the existing session-summary responses (anchored on the session's start time). The frontend reads those `new_unlocks` to fire one aggregate `react-hot-toast`, and consumes the unchanged `/concepts/recent-unlocks` endpoint via a new `useRecentUnlocks` hook to render a strip.

**Tech Stack:** FastAPI / SQLAlchemy 2.0 async / Pydantic v2 / pytest (backend); React + TypeScript / Vite / @tanstack/react-query / Zustand / react-hot-toast / Vitest (frontend).

## Global Constraints

- Backend: never write raw SQL — use SQLAlchemy ORM / repository pattern (CLAUDE.md). Unlock recording must NEVER fail an answer submission — wrap every recording call in `try/except` that logs via `structlog` and swallows.
- Backend naming: snake_case functions/methods, PascalCase classes. Pydantic v2 (`Field`, `model_config = ConfigDict(...)`).
- Frontend: API calls only via the service layer (no axios in components); react-query for fetching; Zustand updated immutably; prop drilling ≤ 2 levels; PascalCase components, camelCase hooks/functions.
- Timestamps: `concept_unlock_events.unlocked_at` is `DateTime(timezone=True)`; compare against tz-aware anchors only.
- Tests: 80% minimum coverage both stacks. Run `npm run test:frontend && npm run test:backend` before committing.
- Backend test command prefix (settings do NOT auto-load `.env`): run pytest from `apps/api` with the project venv: `cd apps/api && .venv/bin/pytest <path> -v`.
- Out of scope (do NOT touch): graph viz (#15), shared-types migration, gate logic in `MasteryGateService.check_prerequisites_mastered`, and the known follow-ups (Redis test auth, `test_reading_chunks.py`, quiz_answer coverage port).

---

### Task 1: Backend — `SessionUnlockItem` schema, `new_unlocks` fields, `get_session_unlocks`

Adds the data shape and the query that backs inline session unlocks. No pipeline wiring yet.

**Files:**
- Modify: `apps/api/src/schemas/mastery_gate.py` (add `SessionUnlockItem`)
- Modify: `apps/api/src/schemas/quiz.py:74-103` (add `new_unlocks` to `SessionSummaryResponse`)
- Modify: `apps/api/src/schemas/review.py` (add `new_unlocks` to `ReviewSummaryResponse`, ~line 125)
- Modify: `apps/api/src/services/mastery_gate.py` (add `get_session_unlocks`, after `get_recent_unlocks` ~line 447)
- Test: `apps/api/tests/unit/services/test_mastery_gate.py`

**Interfaces:**
- Produces: `SessionUnlockItem(concept_id: UUID, concept_name: str)` in `src.schemas.mastery_gate`.
- Produces: `MasteryGateService.get_session_unlocks(user_id: UUID, since: datetime) -> list[SessionUnlockItem]` — events with `unlocked_at >= since`, ascending by `unlocked_at`.
- Produces: `SessionSummaryResponse.new_unlocks: list[SessionUnlockItem]` and `ReviewSummaryResponse.new_unlocks: list[SessionUnlockItem]`, both default `[]`.

- [ ] **Step 1: Add the `SessionUnlockItem` schema**

In `apps/api/src/schemas/mastery_gate.py`, add after `ConceptUnlockEventResponse` (after line 117):

```python
class SessionUnlockItem(BaseModel):
    """Lightweight concept-unlock item returned inline in session summaries.

    Carries only what a post-session toast / click-through needs.
    Story 4.11 AC 7 (Slice C).
    """
    model_config = ConfigDict(from_attributes=True)

    concept_id: UUID
    concept_name: str
```

(`BaseModel`, `ConfigDict`, `UUID` are already imported in this file.)

- [ ] **Step 2: Add `new_unlocks` to the two summary response schemas**

In `apps/api/src/schemas/quiz.py`, add this import near the top (with the other imports) — confirm the module's existing import style and match it:

```python
from src.schemas.mastery_gate import SessionUnlockItem
```

Then add to `SessionSummaryResponse` (after `session_duration_seconds`, line 103):

```python
    new_unlocks: list[SessionUnlockItem] = Field(
        default_factory=list,
        description="Concepts unlocked during this session (Story 4.11 AC 7)"
    )
```

In `apps/api/src/schemas/review.py`, add the same import and add to `ReviewSummaryResponse` (after `still_incorrect_concepts`):

```python
    new_unlocks: list[SessionUnlockItem] = Field(
        default_factory=list,
        description="Concepts unlocked during this review session (Story 4.11 AC 7)"
    )
```

- [ ] **Step 3: Write the failing test for `get_session_unlocks`**

In `apps/api/tests/unit/services/test_mastery_gate.py`, add at the end of the file (the module already imports `AsyncMock`, `MagicMock`, `UUID`, `uuid4`, `pytest`, `datetime`, `UTC`, and `MasteryGateService`; the fixtures `mock_session`, `mock_belief_repo`, `mock_concept_repo` exist):

```python
class TestGetSessionUnlocks:
    """get_session_unlocks returns events since an anchor as SessionUnlockItems."""

    @pytest.fixture
    def service(self, mock_session, mock_belief_repo, mock_concept_repo):
        return MasteryGateService(
            session=mock_session,
            belief_repository=mock_belief_repo,
            concept_repository=mock_concept_repo,
        )

    @pytest.mark.asyncio
    async def test_maps_rows_to_session_unlock_items(self, service, mock_session):
        cid_a, cid_b = uuid4(), uuid4()
        result = MagicMock()
        result.all.return_value = [(cid_a, "Approach"), (cid_b, "Elicitation")]
        mock_session.execute = AsyncMock(return_value=result)

        since = datetime(2026, 6, 28, tzinfo=UTC)
        items = await service.get_session_unlocks(uuid4(), since)

        assert [(i.concept_id, i.concept_name) for i in items] == [
            (cid_a, "Approach"),
            (cid_b, "Elicitation"),
        ]
        mock_session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_empty_when_no_rows(self, service, mock_session):
        result = MagicMock()
        result.all.return_value = []
        mock_session.execute = AsyncMock(return_value=result)

        items = await service.get_session_unlocks(uuid4(), datetime(2026, 6, 28, tzinfo=UTC))

        assert items == []
```

- [ ] **Step 4: Run the test to verify it fails**

Run: `cd apps/api && .venv/bin/pytest tests/unit/services/test_mastery_gate.py::TestGetSessionUnlocks -v`
Expected: FAIL — `AttributeError: 'MasteryGateService' object has no attribute 'get_session_unlocks'`.

- [ ] **Step 5: Implement `get_session_unlocks`**

In `apps/api/src/services/mastery_gate.py`, add the import to the existing `src.schemas.mastery_gate` import block (line 20-28): add `SessionUnlockItem` to the imported names. Then add this method after `get_recent_unlocks` (after line 447):

```python
    async def get_session_unlocks(
        self,
        user_id: UUID,
        since: datetime,
    ) -> list[SessionUnlockItem]:
        """
        Return concepts unlocked for a user at or after ``since``.

        Used to surface this-session unlocks inline on session summaries
        (Story 4.11 AC 7). Ordered oldest-first so the toast reads in
        unlock order.

        Args:
            user_id: User UUID
            since: tz-aware lower bound (typically the session's start time)

        Returns:
            List of SessionUnlockItem (concept_id + concept_name)
        """
        query = (
            select(ConceptUnlockEvent.concept_id, Concept.name)
            .join(Concept, ConceptUnlockEvent.concept_id == Concept.id)
            .where(ConceptUnlockEvent.user_id == user_id)
            .where(ConceptUnlockEvent.unlocked_at >= since)
            .order_by(ConceptUnlockEvent.unlocked_at.asc())
        )
        result = await self.session.execute(query)
        return [
            SessionUnlockItem(concept_id=concept_id, concept_name=name)
            for concept_id, name in result.all()
        ]
```

Add `from datetime import datetime` to the imports at the top of `mastery_gate.py` if not already present (the file currently imports `time` and `from uuid import UUID`; add the datetime import).

- [ ] **Step 6: Run the test to verify it passes**

Run: `cd apps/api && .venv/bin/pytest tests/unit/services/test_mastery_gate.py::TestGetSessionUnlocks -v`
Expected: PASS (2 passed).

- [ ] **Step 7: Verify schemas import cleanly (no circular import)**

Run: `cd apps/api && .venv/bin/python -c "from src.schemas.quiz import SessionSummaryResponse; from src.schemas.review import ReviewSummaryResponse; print(SessionSummaryResponse.model_fields['new_unlocks'].default_factory(), ReviewSummaryResponse.model_fields['new_unlocks'].default_factory())"`
Expected: prints `[] []` with no ImportError.

- [ ] **Step 8: Commit**

```bash
git add apps/api/src/schemas/mastery_gate.py apps/api/src/schemas/quiz.py apps/api/src/schemas/review.py apps/api/src/services/mastery_gate.py apps/api/tests/unit/services/test_mastery_gate.py
git commit -m "feat(#14): add SessionUnlockItem schema + get_session_unlocks query"
```

---

### Task 2: Backend — record unlocks + populate `new_unlocks` in the quiz pipeline

Wires `check_and_record_unlocks` into `submit_answer` and fills `new_unlocks` at session end.

**Files:**
- Modify: `apps/api/src/services/quiz_answer_service.py` (constructor ~44-66; recording after belief block ~235; summary build ~291)
- Modify: `apps/api/src/dependencies.py:332-360` (`get_quiz_answer_service`)
- Test: `apps/api/tests/unit/services/test_quiz_answer_service.py` (in `apps/api/tests/unit/services/`)

**Interfaces:**
- Consumes: `MasteryGateService.check_and_record_unlocks(user_id, updated_concept_id)` and `get_session_unlocks(user_id, since)` (Task 1).
- Produces: `QuizAnswerService.__init__(..., mastery_gate_service: MasteryGateService)` — every existing test that constructs `QuizAnswerService` must pass this new arg.

- [ ] **Step 1: Write the failing test — recording is invoked after a belief update**

In `apps/api/tests/unit/services/test_quiz_answer_service.py`, find the existing fixture that builds `QuizAnswerService` (it constructs it with `belief_updater=...`). Add a `mastery_gate_service` mock to that fixture and a new test. Use the existing construction style; the new mock:

```python
@pytest.fixture
def mock_mastery_gate_service():
    svc = AsyncMock()
    svc.check_and_record_unlocks = AsyncMock(return_value=[])
    svc.get_session_unlocks = AsyncMock(return_value=[])
    return svc
```

Add `mastery_gate_service=mock_mastery_gate_service` to the `QuizAnswerService(...)` call in the service fixture (thread the new fixture through as a parameter).

New test (place beside the other `submit_answer` tests; reuse whatever fixtures those tests use to drive a successful non-completing answer):

```python
@pytest.mark.asyncio
async def test_submit_answer_records_unlocks_for_updated_concepts(
    self, service, mock_mastery_gate_service, <existing fixtures used by a happy-path submit_answer test>
):
    # Arrange: a belief update touches one concept (mirror the happy-path setup
    # used by the existing successful-submit test, which yields belief_updates).
    ...  # same arrange as the existing passing submit_answer test

    await service.submit_answer(...)  # same call/args as that test

    # Assert: recording was attempted for the concept that was updated.
    assert mock_mastery_gate_service.check_and_record_unlocks.await_count >= 1
```

> Implementation note for the engineer: copy the arrange/act of the nearest existing passing `submit_answer` happy-path test verbatim, then add only the assertion above. This avoids re-deriving the (large) mock setup.

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd apps/api && .venv/bin/pytest tests/unit/services/test_quiz_answer_service.py -k records_unlocks -v`
Expected: FAIL — `TypeError: __init__() got an unexpected keyword argument 'mastery_gate_service'` (or, once the fixture is wired, the assertion fails because recording is never called).

- [ ] **Step 3: Add `mastery_gate_service` to the constructor**

In `apps/api/src/services/quiz_answer_service.py`, add the import near the other service imports (line 27):

```python
from src.services.mastery_gate import MasteryGateService
```

Add the parameter to `__init__` (after `belief_updater`, line 50) and store it:

```python
        belief_updater: BeliefUpdater,
        mastery_gate_service: MasteryGateService,
    ):
        ...
        self.belief_updater = belief_updater
        self.mastery_gate_service = mastery_gate_service
```

- [ ] **Step 4: Record unlocks after the belief update**

In `submit_answer`, immediately after the belief `try/except` block (after line 235, before `# 8. Create response record`), insert:

```python
        # 7b. Story 4.11 AC 7: record any concepts unlocked by this update.
        # Never fail the answer submission if unlock recording fails.
        for concept_id_str in {u["concept_id"] for u in belief_updates}:
            try:
                await self.mastery_gate_service.check_and_record_unlocks(
                    user_id=user_id,
                    updated_concept_id=UUID(concept_id_str),
                )
            except Exception as e:
                logger.error(
                    "quiz_unlock_recording_failed",
                    user_id=str(user_id),
                    concept_id=concept_id_str,
                    error=str(e),
                )
```

(`UUID` is already imported at line 8.)

- [ ] **Step 5: Populate `new_unlocks` at session completion**

In the auto-completion branch, after `session_summary` is built (after line 299), populate `new_unlocks` on it. Replace the `session_summary = SessionSummaryResponse(...)` construction (line 291-299) so it includes `new_unlocks`:

```python
            # Story 4.11 AC 7: surface concepts unlocked during this session.
            new_unlocks = []
            try:
                new_unlocks = await self.mastery_gate_service.get_session_unlocks(
                    user_id=user_id,
                    since=started_at,
                )
            except Exception as e:
                logger.error(
                    "quiz_session_unlocks_fetch_failed",
                    user_id=str(user_id),
                    session_id=str(session_id),
                    error=str(e),
                )

            session_summary = SessionSummaryResponse(
                questions_answered=session.total_questions,
                question_target=session.question_target,
                correct_count=session.correct_count,
                accuracy=round(accuracy_pct, 1),
                concepts_strengthened=concepts_strengthened,
                quizzes_completed_total=user.quizzes_completed,
                session_duration_seconds=duration_seconds,
                new_unlocks=new_unlocks,
            )
```

(`started_at` here is the tz-normalized variable already computed at line 265-268.)

- [ ] **Step 6: Wire the dependency provider**

In `apps/api/src/dependencies.py`, update `get_quiz_answer_service` (line 332-360). Add a `db` param and build the `MasteryGateService` from the same repos. Add the imports at the top of the file if missing: `from sqlalchemy.ext.asyncio import AsyncSession`, `from src.db.session import get_db` (match the existing import names used elsewhere in this file for the session dependency), and `from src.services.mastery_gate import MasteryGateService`.

```python
def get_quiz_answer_service(
    db: AsyncSession = Depends(get_db),
    response_repo: ResponseRepository = Depends(get_response_repository),
    question_repo: QuestionRepository = Depends(get_question_repository),
    session_repo: QuizSessionRepository = Depends(get_quiz_session_repository),
    user_repo: UserRepository = Depends(get_user_repository),
    belief_repo: BeliefRepository = Depends(get_belief_repository),
    concept_repo: ConceptRepository = Depends(get_concept_repository),
) -> QuizAnswerService:
    belief_updater = BeliefUpdater(
        belief_repository=belief_repo,
        concept_repository=concept_repo,
        default_slip=0.10,
        default_guess=0.25,
        prerequisite_propagation=0.3,
    )
    mastery_gate_service = MasteryGateService(
        session=db,
        belief_repository=belief_repo,
        concept_repository=concept_repo,
    )
    return QuizAnswerService(
        response_repo=response_repo,
        question_repo=question_repo,
        session_repo=session_repo,
        user_repo=user_repo,
        belief_updater=belief_updater,
        mastery_gate_service=mastery_gate_service,
    )
```

> The repos are all built from the request-scoped `get_db` session (FastAPI caches `Depends(get_db)` per request), so `db` here is the same session the repos use — one transaction.

- [ ] **Step 7: Fix any other constructors of `QuizAnswerService`**

Run: `cd apps/api && grep -rn "QuizAnswerService(" tests/ src/`
For each call site that does not yet pass `mastery_gate_service=`, add it (tests: pass an `AsyncMock()` with `check_and_record_unlocks`/`get_session_unlocks` as `AsyncMock(return_value=[])`).

- [ ] **Step 8: Run the quiz-service tests**

Run: `cd apps/api && .venv/bin/pytest tests/unit/services/test_quiz_answer_service.py -v`
Expected: PASS (all, including the new `records_unlocks` test).

- [ ] **Step 9: Commit**

```bash
git add apps/api/src/services/quiz_answer_service.py apps/api/src/dependencies.py apps/api/tests/unit/services/test_quiz_answer_service.py
git commit -m "feat(#14): record + surface concept unlocks in quiz answer pipeline"
```

---

### Task 3: Backend — record unlocks + populate `new_unlocks` in the review pipeline

**Files:**
- Modify: `apps/api/src/services/review_session_service.py` (constructor 44-66; recording in `_update_beliefs_with_reinforcement` before its return; `get_review_summary` build ~455)
- Modify: `apps/api/src/routes/review.py:36-53` (`get_review_session_service`)
- Test: `apps/api/tests/unit/services/test_review_session_service.py` (locate the existing review-service test module; if it lives elsewhere, use that path)

**Interfaces:**
- Consumes: `MasteryGateService.check_and_record_unlocks`, `get_session_unlocks` (Task 1).
- Produces: `ReviewSessionService.__init__(..., mastery_gate_service: MasteryGateService)`.

- [ ] **Step 1: Write the failing test — review records unlocks**

In the review-session test module, add a `mastery_gate_service` mock (same shape as Task 2 Step 1) to the fixture that builds `ReviewSessionService`, threading it into the constructor call. Add:

```python
@pytest.mark.asyncio
async def test_submit_review_answer_records_unlocks(
    self, service, mock_mastery_gate_service, <existing fixtures used by a happy-path review-answer test>
):
    ...  # same arrange/act as the existing passing submit_review_answer test
    assert mock_mastery_gate_service.check_and_record_unlocks.await_count >= 1
```

> Copy the arrange/act of the nearest passing review-answer test; add only the assertion.

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd apps/api && .venv/bin/pytest tests/unit/services/test_review_session_service.py -k records_unlocks -v`
Expected: FAIL — unexpected kwarg `mastery_gate_service`, or assertion fails (recording never called).

- [ ] **Step 3: Add `mastery_gate_service` to the constructor**

In `apps/api/src/services/review_session_service.py`, add the import:

```python
from src.services.mastery_gate import MasteryGateService
```

Add the parameter to `__init__` (after `belief_updater`) and store `self.mastery_gate_service = mastery_gate_service`.

- [ ] **Step 4: Record unlocks after reinforcement belief updates**

In `_update_beliefs_with_reinforcement`, immediately before `return belief_updates` (the method ends ~line 511; locate its `return`), insert:

```python
        # Story 4.11 AC 7: record concepts unlocked by reinforcement. Never
        # let unlock recording break a review submission.
        for concept_id_str in {u["concept_id"] for u in belief_updates}:
            try:
                await self.mastery_gate_service.check_and_record_unlocks(
                    user_id=user_id,
                    updated_concept_id=UUID(concept_id_str),
                )
            except Exception as e:
                logger.error(
                    "review_unlock_recording_failed",
                    user_id=str(user_id),
                    concept_id=concept_id_str,
                    error=str(e),
                )
```

Confirm `UUID` is imported at the top of `review_session_service.py`; if not, add `from uuid import UUID`.

- [ ] **Step 5: Populate `new_unlocks` in `get_review_summary`**

In `get_review_summary`, before the `return ReviewSummaryResponse(...)` (line 455), fetch unlocks since the review session was created:

```python
        new_unlocks = []
        try:
            new_unlocks = await self.mastery_gate_service.get_session_unlocks(
                user_id=user_id,
                since=review_session.created_at,
            )
        except Exception as e:
            logger.error(
                "review_session_unlocks_fetch_failed",
                user_id=str(user_id),
                review_session_id=str(review_session_id),
                error=str(e),
            )
```

Then add `new_unlocks=new_unlocks,` to the `ReviewSummaryResponse(...)` construction (after `still_incorrect_concepts=...`).

- [ ] **Step 6: Wire the dependency provider**

In `apps/api/src/routes/review.py`, update `get_review_session_service` (line 36-53) to build and pass a `MasteryGateService` (add `from src.services.mastery_gate import MasteryGateService` at the top):

```python
def get_review_session_service(
    db: AsyncSession = Depends(get_db),
) -> ReviewSessionService:
    """Dependency injection for ReviewSessionService."""
    review_repo = ReviewSessionRepository(db)
    belief_repo = BeliefRepository(db)
    concept_repo = ConceptRepository(db)
    belief_updater = BeliefUpdater(
        belief_repository=belief_repo,
        concept_repository=concept_repo,
    )
    mastery_gate_service = MasteryGateService(
        session=db,
        belief_repository=belief_repo,
        concept_repository=concept_repo,
    )
    return ReviewSessionService(
        review_repo=review_repo,
        belief_repo=belief_repo,
        concept_repo=concept_repo,
        belief_updater=belief_updater,
        mastery_gate_service=mastery_gate_service,
    )
```

- [ ] **Step 7: Fix any other constructors of `ReviewSessionService`**

Run: `cd apps/api && grep -rn "ReviewSessionService(" tests/ src/`
For each call missing `mastery_gate_service=`, add it (tests: an `AsyncMock()` with the two methods returning `[]`).

- [ ] **Step 8: Run review-service tests**

Run: `cd apps/api && .venv/bin/pytest tests/unit/services/test_review_session_service.py -v`
Expected: PASS.

- [ ] **Step 9: Commit**

```bash
git add apps/api/src/services/review_session_service.py apps/api/src/routes/review.py apps/api/tests/unit/services/test_review_session_service.py
git commit -m "feat(#14): record + surface concept unlocks in review pipeline"
```

---

### Task 4: Frontend — types for `new_unlocks`

**Files:**
- Modify: `apps/web/src/services/prerequisiteService.ts` (export `SessionUnlockItem`)
- Modify: `apps/web/src/services/quizService.ts:198-207` (add `new_unlocks` to `SessionSummary`)
- Modify: `apps/web/src/services/reviewService.ts:98-105` (add `new_unlocks` to `ReviewSummaryResponse`)

**Interfaces:**
- Produces: `SessionUnlockItem { concept_id: string; concept_name: string }` exported from `prerequisiteService`.
- Produces: `SessionSummary.new_unlocks: SessionUnlockItem[]`, `ReviewSummaryResponse.new_unlocks: SessionUnlockItem[]`.

- [ ] **Step 1: Add the `SessionUnlockItem` type**

In `apps/web/src/services/prerequisiteService.ts`, add after `ConceptUnlockEvent` (line 77):

```typescript
/**
 * Lightweight concept-unlock item returned inline on session summaries.
 * Mirrors backend schema `SessionUnlockItem`. Story 4.11 AC 7 (Slice C).
 */
export interface SessionUnlockItem {
  concept_id: string
  concept_name: string
}
```

- [ ] **Step 2: Extend the quiz + review summary types**

In `apps/web/src/services/quizService.ts`, add the import near the top:

```typescript
import type { SessionUnlockItem } from './prerequisiteService'
```

Add to `interface SessionSummary` (after `session_duration_seconds`, line 205):

```typescript
  new_unlocks: SessionUnlockItem[]
```

In `apps/web/src/services/reviewService.ts`, add the same import and add to `interface ReviewSummaryResponse` (after `still_incorrect_concepts`):

```typescript
  new_unlocks: SessionUnlockItem[]
```

- [ ] **Step 3: Type-check**

Run: `npm run type-check`
Expected: passes (existing mocks may need `new_unlocks: []` — fix any reported test type errors by adding `new_unlocks: []` to summary literals; this overlaps Task 7/8 test fixtures).

- [ ] **Step 4: Commit**

```bash
git add apps/web/src/services/prerequisiteService.ts apps/web/src/services/quizService.ts apps/web/src/services/reviewService.ts
git commit -m "feat(#14): frontend types for session new_unlocks"
```

---

### Task 5: Frontend — `useRecentUnlocks` hook

**Files:**
- Modify: `apps/web/src/hooks/useConceptLockStatus.ts` (add key + hook)
- Test: `apps/web/src/hooks/__tests__/useRecentUnlocks.test.tsx` (create)

**Interfaces:**
- Consumes: `prerequisiteService.getRecentUnlocks(limit)` and `RecentUnlocksResponse` (exist).
- Produces: `useRecentUnlocks(limit?: number)` returning `useQuery<RecentUnlocksResponse>`; `conceptLockKeys.recentUnlocks(limit)`.

- [ ] **Step 1: Write the failing test**

Create `apps/web/src/hooks/__tests__/useRecentUnlocks.test.tsx`:

```tsx
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import { useRecentUnlocks } from '../useConceptLockStatus'
import { prerequisiteService } from '../../services/prerequisiteService'

vi.mock('../../services/prerequisiteService', () => ({
  prerequisiteService: { getRecentUnlocks: vi.fn() },
}))

function wrapper({ children }: { children: ReactNode }) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>
}

describe('useRecentUnlocks', () => {
  beforeEach(() => vi.clearAllMocks())

  it('fetches recent unlocks with the given limit', async () => {
    vi.mocked(prerequisiteService.getRecentUnlocks).mockResolvedValue({
      unlocks: [
        { id: '1', user_id: 'u', concept_id: 'c', concept_name: 'Approach',
          prerequisite_concept_id: null, prerequisite_concept_name: null,
          unlocked_at: '2026-06-28T00:00:00Z' },
      ],
      total_unlocked: 1,
    })

    const { result } = renderHook(() => useRecentUnlocks(3), { wrapper })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data?.total_unlocked).toBe(1)
    expect(prerequisiteService.getRecentUnlocks).toHaveBeenCalledWith(3)
  })
})
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `npm run test:frontend -- useRecentUnlocks`
Expected: FAIL — `useRecentUnlocks` is not exported.

- [ ] **Step 3: Implement the hook**

In `apps/web/src/hooks/useConceptLockStatus.ts`, add `RecentUnlocksResponse` to the import from `prerequisiteService` (line 2-7). Add the key to `conceptLockKeys` (after `bulk`, line 18):

```typescript
  recentUnlocks: (limit: number) =>
    [...conceptLockKeys.all, 'recent-unlocks', limit] as const,
```

Add the hook at the end of the file:

```typescript
/**
 * Fetch the current user's recently unlocked concepts (Story 4.11 AC 7).
 *
 * Powers the "recently unlocked" strip on the curriculum page.
 *
 * @param limit - Max results (default 5)
 */
export function useRecentUnlocks(limit = 5) {
  return useQuery<RecentUnlocksResponse>({
    queryKey: conceptLockKeys.recentUnlocks(limit),
    queryFn: () => prerequisiteService.getRecentUnlocks(limit),
    staleTime: 30_000,
  })
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `npm run test:frontend -- useRecentUnlocks`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/hooks/useConceptLockStatus.ts apps/web/src/hooks/__tests__/useRecentUnlocks.test.tsx
git commit -m "feat(#14): useRecentUnlocks hook"
```

---

### Task 6: Frontend — `showUnlockToast` util + global `<Toaster/>`

**Files:**
- Create: `apps/web/src/utils/unlockToast.tsx`
- Modify: `apps/web/src/App.tsx:137-141` (mount `<Toaster/>`)
- Test: `apps/web/src/utils/__tests__/unlockToast.test.tsx` (create)

**Interfaces:**
- Consumes: `SessionUnlockItem` (Task 4); `react-hot-toast` (dependency).
- Produces: `showUnlockToast(unlocks: SessionUnlockItem[], navigate: (to: string) => void): void`.

- [ ] **Step 1: Write the failing test**

Create `apps/web/src/utils/__tests__/unlockToast.test.tsx`:

```tsx
import { describe, it, expect, vi, beforeEach } from 'vitest'
import toast from 'react-hot-toast'
import { showUnlockToast, buildUnlockMessage } from '../unlockToast'
import type { SessionUnlockItem } from '../../services/prerequisiteService'

vi.mock('react-hot-toast', () => ({
  default: Object.assign(vi.fn(), { dismiss: vi.fn() }),
}))

const item = (name: string): SessionUnlockItem => ({ concept_id: name, concept_name: name })

describe('buildUnlockMessage', () => {
  it('singular', () => {
    expect(buildUnlockMessage([item('Approach')])).toBe('🎉 You unlocked Approach!')
  })
  it('two named', () => {
    expect(buildUnlockMessage([item('A'), item('B')])).toBe('🎉 You unlocked A and B!')
  })
  it('more than two summarises', () => {
    expect(buildUnlockMessage([item('A'), item('B'), item('C')])).toBe(
      '🎉 You unlocked 3 new concepts: A, B +1 more',
    )
  })
})

describe('showUnlockToast', () => {
  beforeEach(() => vi.clearAllMocks())

  it('does nothing when there are no unlocks', () => {
    showUnlockToast([], vi.fn())
    expect(toast).not.toHaveBeenCalled()
  })

  it('fires a toast when there are unlocks', () => {
    showUnlockToast([item('Approach')], vi.fn())
    expect(toast).toHaveBeenCalledTimes(1)
  })
})
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `npm run test:frontend -- unlockToast`
Expected: FAIL — module `../unlockToast` not found.

- [ ] **Step 3: Implement the util**

Create `apps/web/src/utils/unlockToast.tsx`:

```tsx
import toast from 'react-hot-toast'
import type { SessionUnlockItem } from '../services/prerequisiteService'

/** Build the aggregate unlock message (pure; exported for testing). */
export function buildUnlockMessage(unlocks: SessionUnlockItem[]): string {
  const names = unlocks.map((u) => u.concept_name)
  if (names.length === 1) return `🎉 You unlocked ${names[0]}!`
  if (names.length === 2) return `🎉 You unlocked ${names[0]} and ${names[1]}!`
  const shown = names.slice(0, 2).join(', ')
  return `🎉 You unlocked ${names.length} new concepts: ${shown} +${names.length - 2} more`
}

/**
 * Fire a single aggregate "concepts unlocked" toast. Clicking it navigates to
 * the curriculum page. No-op when there are no unlocks. Story 4.11 AC 7.
 */
export function showUnlockToast(
  unlocks: SessionUnlockItem[],
  navigate: (to: string) => void,
): void {
  if (unlocks.length === 0) return
  const message = buildUnlockMessage(unlocks)

  toast(
    (t) => (
      <button
        type="button"
        onClick={() => {
          toast.dismiss(t.id)
          navigate('/curriculum')
        }}
        className="flex items-center gap-2 text-left text-sm font-medium text-charcoal"
        aria-label={`${message} View curriculum.`}
      >
        {message}
      </button>
    ),
    { duration: 6000, ariaProps: { role: 'status', 'aria-live': 'polite' } },
  )
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `npm run test:frontend -- unlockToast`
Expected: PASS.

- [ ] **Step 5: Mount a global `<Toaster/>`**

In `apps/web/src/App.tsx`, add the import:

```typescript
import { Toaster } from 'react-hot-toast'
```

Change the `App` component (line 137-139) to render the Toaster alongside the router:

```typescript
function App() {
  return (
    <>
      <RouterProvider router={router} />
      <Toaster position="top-center" toastOptions={{ duration: 4000 }} />
    </>
  )
}
```

If `AccountCreationPage` mounts its own `<Toaster/>`, leave it — react-hot-toast tolerates it, but prefer removing the local one in that page so there is a single Toaster. (Optional cleanup; not required for this task.)

- [ ] **Step 6: Type-check + commit**

Run: `npm run type-check`
Expected: passes.

```bash
git add apps/web/src/utils/unlockToast.tsx apps/web/src/utils/__tests__/unlockToast.test.tsx apps/web/src/App.tsx
git commit -m "feat(#14): unlock toast helper + global Toaster"
```

---

### Task 7: Frontend — `RecentlyUnlockedStrip` on the curriculum page

**Files:**
- Create: `apps/web/src/components/curriculum/RecentlyUnlockedStrip.tsx`
- Modify: `apps/web/src/pages/CurriculumPage.tsx` (render the strip)
- Test: `apps/web/src/components/curriculum/__tests__/RecentlyUnlockedStrip.test.tsx` (create)

**Interfaces:**
- Consumes: `useRecentUnlocks` (Task 5).
- Produces: `RecentlyUnlockedStrip` (no props) — renders `null` when empty/loading/errored.

- [ ] **Step 1: Write the failing test**

Create `apps/web/src/components/curriculum/__tests__/RecentlyUnlockedStrip.test.tsx`:

```tsx
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { RecentlyUnlockedStrip } from '../RecentlyUnlockedStrip'
import * as hooks from '../../../hooks/useConceptLockStatus'

vi.mock('../../../hooks/useConceptLockStatus', () => ({ useRecentUnlocks: vi.fn() }))

const ev = (name: string) => ({
  id: name, user_id: 'u', concept_id: name, concept_name: name,
  prerequisite_concept_id: null, prerequisite_concept_name: null,
  unlocked_at: '2026-06-28T00:00:00Z',
})

describe('RecentlyUnlockedStrip', () => {
  beforeEach(() => vi.clearAllMocks())

  it('renders nothing when there are no unlocks', () => {
    vi.mocked(hooks.useRecentUnlocks).mockReturnValue({
      data: { unlocks: [], total_unlocked: 0 }, isLoading: false, isError: false,
    } as never)
    const { container } = render(<RecentlyUnlockedStrip />)
    expect(container).toBeEmptyDOMElement()
  })

  it('renders nothing on error', () => {
    vi.mocked(hooks.useRecentUnlocks).mockReturnValue({
      data: undefined, isLoading: false, isError: true,
    } as never)
    const { container } = render(<RecentlyUnlockedStrip />)
    expect(container).toBeEmptyDOMElement()
  })

  it('renders a chip per unlock', () => {
    vi.mocked(hooks.useRecentUnlocks).mockReturnValue({
      data: { unlocks: [ev('Approach'), ev('Elicitation')], total_unlocked: 2 },
      isLoading: false, isError: false,
    } as never)
    render(<RecentlyUnlockedStrip />)
    expect(screen.getByText('Approach')).toBeInTheDocument()
    expect(screen.getByText('Elicitation')).toBeInTheDocument()
    expect(screen.getByRole('list', { name: /recently unlocked/i })).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `npm run test:frontend -- RecentlyUnlockedStrip`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement the component**

Create `apps/web/src/components/curriculum/RecentlyUnlockedStrip.tsx`:

```tsx
import { useRecentUnlocks } from '../../hooks/useConceptLockStatus'

/**
 * Horizontal strip of the user's recently unlocked concepts (Story 4.11 AC 7).
 * Renders nothing until there is data, so it is invisible on a fresh account.
 */
export function RecentlyUnlockedStrip() {
  const { data, isLoading, isError } = useRecentUnlocks(5)

  if (isLoading || isError) return null
  const unlocks = data?.unlocks ?? []
  if (unlocks.length === 0) return null

  return (
    <section className="mt-4" aria-label="Recently unlocked concepts">
      <h2 className="text-xs font-semibold uppercase tracking-wide text-gray-500">
        Recently unlocked
      </h2>
      <ul
        aria-label="Recently unlocked concepts"
        className="mt-2 flex gap-2 overflow-x-auto pb-1"
      >
        {unlocks.map((u) => (
          <li
            key={u.id}
            tabIndex={0}
            className="flex shrink-0 items-center gap-1 rounded-full border border-green-200 bg-green-50 px-3 py-1 text-sm font-medium text-green-800 focus:outline-none focus:ring-2 focus:ring-green-500"
          >
            <span aria-hidden="true">🔓</span>
            {u.concept_name}
          </li>
        ))}
      </ul>
    </section>
  )
}

export default RecentlyUnlockedStrip
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `npm run test:frontend -- RecentlyUnlockedStrip`
Expected: PASS (3 passed).

- [ ] **Step 5: Render the strip on the curriculum page**

In `apps/web/src/pages/CurriculumPage.tsx`, add the import (after line 7):

```typescript
import { RecentlyUnlockedStrip } from '../components/curriculum/RecentlyUnlockedStrip'
```

Render it after the description `<p>` and before `<div className="mt-6 space-y-3">` (line 63):

```tsx
        <RecentlyUnlockedStrip />

        <div className="mt-6 space-y-3">
```

- [ ] **Step 6: Update the CurriculumPage test mock**

The existing `apps/web/src/pages/__tests__/CurriculumPage.test.tsx` mocks `prerequisiteService` with only `getBulkUnlockStatus`. The page now also renders `RecentlyUnlockedStrip`, which calls `useRecentUnlocks`. Add a mock so the page test stays isolated — add to the top of that file:

```tsx
vi.mock('../../components/curriculum/RecentlyUnlockedStrip', () => ({
  RecentlyUnlockedStrip: () => null,
}))
```

Run: `npm run test:frontend -- CurriculumPage`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add apps/web/src/components/curriculum/RecentlyUnlockedStrip.tsx apps/web/src/pages/CurriculumPage.tsx apps/web/src/pages/__tests__/CurriculumPage.test.tsx apps/web/src/components/curriculum/__tests__/RecentlyUnlockedStrip.test.tsx
git commit -m "feat(#14): RecentlyUnlockedStrip on curriculum page"
```

---

### Task 8: Frontend — fire the unlock toast from `EndedState` (quiz + review)

**Files:**
- Modify: `apps/web/src/pages/QuizPage.tsx` (`EndedState`, 643-789)
- Test: `apps/web/src/pages/__tests__/QuizPage.unlockToast.test.tsx` (create)

**Interfaces:**
- Consumes: `showUnlockToast` (Task 6); `useQuizStore` selector for `sessionSummary` (exists, `stores/quizStore.ts:122`); `reviewSummary` from `useReview` (exists, `summary` field).

- [ ] **Step 1: Write the failing test**

Create `apps/web/src/pages/__tests__/QuizPage.unlockToast.test.tsx`. This unit-tests a small extracted hook (`useUnlockToastOnSession`) rather than the whole page, to keep the test focused:

```tsx
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook } from '@testing-library/react'
import { useUnlockToastOnSession } from '../QuizPage'
import * as unlockToast from '../../utils/unlockToast'
import type { SessionUnlockItem } from '../../services/prerequisiteService'

vi.mock('../../utils/unlockToast', () => ({ showUnlockToast: vi.fn() }))
vi.mock('react-router-dom', () => ({ useNavigate: () => vi.fn() }))

const unlocks: SessionUnlockItem[] = [{ concept_id: 'a', concept_name: 'Approach' }]

describe('useUnlockToastOnSession', () => {
  beforeEach(() => vi.clearAllMocks())

  it('fires once when unlocks are present', () => {
    const { rerender } = renderHook(
      ({ id, u }) => useUnlockToastOnSession(id, u),
      { initialProps: { id: 's1', u: unlocks } },
    )
    expect(unlockToast.showUnlockToast).toHaveBeenCalledTimes(1)
    rerender({ id: 's1', u: unlocks }) // remount/re-render of same session
    expect(unlockToast.showUnlockToast).toHaveBeenCalledTimes(1)
  })

  it('does not fire when there are no unlocks', () => {
    renderHook(() => useUnlockToastOnSession('s1', []))
    expect(unlockToast.showUnlockToast).not.toHaveBeenCalled()
  })

  it('fires again for a different session id', () => {
    const { rerender } = renderHook(
      ({ id, u }) => useUnlockToastOnSession(id, u),
      { initialProps: { id: 's1', u: unlocks } },
    )
    rerender({ id: 's2', u: unlocks })
    expect(unlockToast.showUnlockToast).toHaveBeenCalledTimes(2)
  })
})
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `npm run test:frontend -- QuizPage.unlockToast`
Expected: FAIL — `useUnlockToastOnSession` is not exported.

- [ ] **Step 3: Implement the fire-once hook**

In `apps/web/src/pages/QuizPage.tsx`, add imports near the top:

```typescript
import { showUnlockToast } from '../utils/unlockToast'
import type { SessionUnlockItem } from '../services/prerequisiteService'
import { useQuizStore } from '../stores/quizStore'
```

(`useEffect`, `useRef`, `useNavigate` are already imported.)

Add this exported hook at module scope (above `EndedState`):

```typescript
/**
 * Fire the aggregate unlock toast once per session id (Story 4.11 AC 7).
 * Exported for unit testing. Guards against re-fire on EndedState remount.
 */
export function useUnlockToastOnSession(
  sessionKey: string | null,
  unlocks: SessionUnlockItem[],
) {
  const navigate = useNavigate()
  const toastedKey = useRef<string | null>(null)
  useEffect(() => {
    if (!sessionKey || unlocks.length === 0) return
    if (toastedKey.current === sessionKey) return
    toastedKey.current = sessionKey
    showUnlockToast(unlocks, navigate)
  }, [sessionKey, unlocks, navigate])
}
```

- [ ] **Step 4: Run the hook test to verify it passes**

Run: `npm run test:frontend -- QuizPage.unlockToast`
Expected: PASS (3 passed).

- [ ] **Step 5: Wire the hook into `EndedState`**

Inside `EndedState` (after `const navigate = useNavigate()`, line 658), read the quiz session summary from the store and call the hook for both quiz and review unlocks:

```typescript
  const sessionSummary = useQuizStore((s) => s.sessionSummary)

  // Story 4.11 AC 7: toast concepts unlocked this quiz session.
  useUnlockToastOnSession(
    sessionSummary ? sessionId : null,
    sessionSummary?.new_unlocks ?? [],
  )

  // ...and concepts unlocked during the post-session review.
  useUnlockToastOnSession(
    reviewSummary ? `${sessionId}:review` : null,
    reviewSummary?.new_unlocks ?? [],
  )
```

Place the second call AFTER `reviewSummary` is destructured from `useReview` (the `summary: reviewSummary` binding at line 670). The two distinct keys (`sessionId` vs `${sessionId}:review`) ensure a quiz-unlock toast and a later review-unlock toast both fire, each once.

- [ ] **Step 6: Run the full quiz-page test suite**

Run: `npm run test:frontend -- QuizPage`
Expected: PASS (existing QuizPage tests + the new hook test). If an existing test constructs a `SessionSummary` literal, add `new_unlocks: []` to it.

- [ ] **Step 7: Commit**

```bash
git add apps/web/src/pages/QuizPage.tsx apps/web/src/pages/__tests__/QuizPage.unlockToast.test.tsx
git commit -m "feat(#14): fire unlock toast post-quiz and post-review"
```

---

### Task 9: Full-suite verification + changelog

**Files:**
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Backend tests (targeted areas)**

Run: `cd apps/api && .venv/bin/pytest tests/unit/services/test_mastery_gate.py tests/unit/services/test_quiz_answer_service.py tests/unit/services/test_review_session_service.py -v`
Expected: all PASS. (The wider suite has 28 known-dormant failures — Redis auth + 2 `test_reading_chunks` assertions — documented in project memory; those are out of scope and must remain the only failures.)

- [ ] **Step 2: Frontend tests + type-check + lint**

Run: `npm run test:frontend && npm run type-check && npm run lint`
Expected: PASS.

- [ ] **Step 3: Update the changelog**

In `CHANGELOG.md`, add under a new/!current "Added" section:

```markdown
### Added
- **Concept unlock notifications (Story 4.11 AC 7, #14):** unlock events are now
  recorded after quiz and review belief updates cross a mastery gate; this-session
  unlocks are returned inline on session summaries and surfaced as a single
  aggregate toast (click → /curriculum), plus a "recently unlocked" strip on the
  curriculum page backed by `/concepts/recent-unlocks`.
```

- [ ] **Step 4: Commit**

```bash
git add CHANGELOG.md
git commit -m "docs(#14): changelog for concept unlock notifications"
```

---

## Self-Review notes (coverage map)

- Backend recording wire (spec §Backend.1): Tasks 2 (quiz) + 3 (review).
- Inline `new_unlocks` (spec §Backend.2, Option 1): Task 1 (schema + query) + Tasks 2/3 (populate).
- Toast, aggregate, click→/curriculum, fire-once (spec §Frontend.3): Tasks 6 + 8.
- `useRecentUnlocks` + strip, invisible-when-empty (spec §Frontend.4): Tasks 5 + 7.
- Defensive recording never fails submission (spec §Error handling): Task 2 Step 4, Task 3 Step 4 (try/except).
- Anchors: quiz uses tz-normalized `started_at` (Task 2 Step 5); review uses `review_session.created_at` (Task 3 Step 5).
- Out-of-scope fences respected (no gate-logic, viz, or shared-types changes).
```
