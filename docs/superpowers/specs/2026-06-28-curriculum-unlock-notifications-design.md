# Design: Curriculum Unlock Notifications (Slice C)

**Date:** 2026-06-28
**Status:** Approved (design); pending spec review
**Related story:** 4.11 — Prerequisite-Based Curriculum Navigation, AC 7
**Issue:** #14
**Author:** Brainstormed with user (telltaio@gmail.com)

---

## Context & Problem

Slice C of the four-slice curriculum/prerequisite plan (see
`2026-06-26-curriculum-prerequisite-navigation-design.md` for the slice map).
Slices A (graph population) and B (curriculum page) are merged. This slice
delivers **AC 7 — surface unlock events to the user**.

The backend already has all the unlock-event machinery:

- `concept_unlock_events` table + `ConceptUnlockEvent` model (unique on
  `(user_id, concept_id)`).
- `MasteryGateService.record_unlock_event()` and
  `MasteryGateService.check_and_record_unlocks(user_id, updated_concept_id)`.
- `GET /concepts/recent-unlocks?limit=` → `RecentUnlocksResponse`.
- `prerequisiteService.getRecentUnlocks(limit)` on the frontend.

**The gap:** `check_and_record_unlocks` / `record_unlock_event` are **never
called** anywhere in the answer/belief pipeline (verified by grep — the only
references are the definitions themselves and tests). Belief states are updated
in `quiz_answer_service.submit_answer` (~line 205) and
`review_session_service._update_beliefs_with_reinforcement`, but nothing detects
unlocks afterward. So `concept_unlock_events` is always empty and
`/concepts/recent-unlocks` always returns `{ unlocks: [], total_unlocked: 0 }`.

A strictly-frontend slice would therefore render nothing and could not be
verified end-to-end. This design **includes the small backend wiring** to record
unlocks, then builds the frontend consumers on top.

### Decisions locked during brainstorming

- **Scope:** include the backend recording wire (not frontend-only), so the
  feature is functional and verifiable end-to-end.
- **Detection (how the toast learns "new this session"):** **inline in the
  session-end response** (Option 1). The backend returns the unlocks recorded
  during this quiz/review session in the existing session-summary payload.
  Chosen over client-side diffing (localStorage seen-set) or
  filter-by-start-time because it is precise, idempotent (cached re-fetch returns
  the same summary → no double-toast), and carries no localStorage fragility.
- **Toast UX:** a single **aggregate** toast (`🎉 You unlocked N new concepts!`),
  clicking it navigates to `/curriculum`. Avoids toast stacking when several
  concepts unlock at once.
- **Curriculum strip:** **included now** — a "recently unlocked" strip on
  `/curriculum` powered by `/concepts/recent-unlocks`, giving that endpoint a
  persistent UI home and a way to revisit unlocks after the toast is gone.

---

## Architecture & file layout

```
apps/api/src/
  services/
    quiz_answer_service.py          # EDIT — call check_and_record_unlocks after belief update
    review_session_service.py       # EDIT — call check_and_record_unlocks after reinforcement
    mastery_gate.py                 # EDIT — add get_session_unlocks(user_id, since)
  schemas/
    quiz.py                         # EDIT — add new_unlocks to SessionSummaryResponse
    review.py                       # EDIT — add new_unlocks to ReviewSummaryResponse

apps/web/src/
  App.tsx (or root layout)          # EDIT — mount a single global <Toaster/>
  hooks/
    useConceptLockStatus.ts         # EDIT — add useRecentUnlocks + conceptLockKeys.recentUnlocks
  components/curriculum/
    RecentlyUnlockedStrip.tsx       # NEW — horizontal chips of recent unlocks
  pages/
    CurriculumPage.tsx              # EDIT — render RecentlyUnlockedStrip above KA sections
    QuizPage.tsx                    # EDIT — EndedState fires unlock toast (quiz summary + review summary)
  utils/ (or lib/)
    unlockToast.ts                  # NEW — showUnlockToast(unlocks, navigate) helper
```

Each unit is single-purpose and conforms to project rules (CLAUDE.md): API only
via the service layer, react-query for fetching, immutable state, prop drilling
≤ 2 levels.

---

## Backend

### 1. Record unlocks after belief updates (the missing wire)

- **Quiz:** in `quiz_answer_service.submit_answer`, after
  `belief_updater.update_beliefs` succeeds, for each updated concept id call
  `mastery_gate_service.check_and_record_unlocks(user_id, concept_id)`. Wrap in
  the same defensive `try/except` as the belief update: a recording failure is
  logged and swallowed — it must **never** fail answer submission.
- **Review:** same after `_update_beliefs_with_reinforcement` in
  `review_session_service` (reinforcement can also cross a mastery threshold).
- `check_and_record_unlocks` already dedupes via the `(user_id, concept_id)`
  existence check, so repeated calls are idempotent.
- A `MasteryGateService` instance must be available in these services. The plan
  determines the exact wiring (constructor injection vs. constructed from the
  existing session/repositories), following the surrounding DI conventions.

### 2. Surface this-session unlocks inline (Option 1)

- New schema item `SessionUnlockItem` = `{ concept_id: UUID, concept_name: str }`
  — lightweight, enough for the toast text and click-through to `/curriculum`.
- Add `new_unlocks: list[SessionUnlockItem] = []` to:
  - `SessionSummaryResponse` (`schemas/quiz.py`) — already returned inside
    `AnswerResponse.session_summary` when `session_completed` is true.
  - `ReviewSummaryResponse` (`schemas/review.py`) — already returned by
    `review_session_service.get_review_summary`.
- New `MasteryGateService.get_session_unlocks(user_id, since: datetime)` →
  `list[SessionUnlockItem]`: queries `concept_unlock_events` for `user_id` with
  `unlocked_at >= since`, joined to `Concept.name`, mirroring the existing query
  in `get_recent_unlocks`.
- Populate `new_unlocks` at session end using the session's `started_at` as
  `since`:
  - Quiz: when `submit_answer` builds `SessionSummaryResponse` (the
    `mark_ended` branch), call `get_session_unlocks(user_id, session.started_at)`.
  - Review: when `get_review_summary` builds `ReviewSummaryResponse`, call it
    with the review session's start timestamp.
- `GET /concepts/recent-unlocks` is **unchanged** — it continues to power the
  curriculum strip.

---

## Frontend

### 3. Toast (aggregate, click → /curriculum)

- Mount a single global `<Toaster/>` (react-hot-toast — already a dependency,
  used in `AccountCreationPage`) at the app root so post-session toasts render
  regardless of the current route. The local `<Toaster/>` in
  `AccountCreationPage` can remain or be removed in favor of the global one
  (plan decides; no duplicate Toasters on the same screen).
- New `showUnlockToast(unlocks: SessionUnlockItem[], navigate)` helper:
  - Message: `🎉 You unlocked N new concept(s)!` — names the first one or two,
    appends `+M more` when more remain. Correct singular/plural.
  - The toast is clickable; clicking calls `navigate('/curriculum')` and
    dismisses.
- Fire it from `EndedState` (QuizPage), which renders both the quiz session
  summary and (via the `ReviewSummary` component) the review summary:
  - when `session_summary.new_unlocks` is non-empty (post-quiz);
  - when the review summary's `new_unlocks` is non-empty (post-review).
- **Fire-once guard:** track the last-toasted session id (module-level ref or
  store) so a remount of `EndedState`/review summary does not re-toast the same
  session.

### 4. Recently-unlocked strip on /curriculum

- New `useRecentUnlocks(limit = 5)` react-query hook over the existing
  `prerequisiteService.getRecentUnlocks`. Add
  `conceptLockKeys.recentUnlocks(limit)` →
  `['concept-lock', 'recent-unlocks', limit]` to the existing key factory;
  `staleTime: 30_000` to match the other lock hooks.
- New `RecentlyUnlockedStrip.tsx` in `components/curriculum/`:
  - A horizontal row of chips, one per recent unlock (concept name + relative
    time from `unlocked_at`).
  - Renders **nothing** when the list is empty or the fetch errored — invisible
    until there is data; never blocks the curriculum page.
  - Each chip is keyboard-focusable; the strip carries an accessible label.
- Render it on `CurriculumPage` above the first `KnowledgeAreaSection`.

---

## Data flow

```
answer / review answer submitted
  → belief_updater updates beliefs
  → check_and_record_unlocks(user_id, concept_id) records newly-crossed concepts
       (idempotent; failures logged + swallowed)
  → at session end, summary carries new_unlocks
       = get_session_unlocks(user_id, session.started_at)
  → EndedState / review summary fires ONE aggregate toast (once per session)
  → user clicks toast → navigate('/curriculum')
  → RecentlyUnlockedStrip (via /concepts/recent-unlocks) shows the persistent list
```

---

## Error & edge-case handling

- **Recording failure:** caught and logged inside the answer/review submission;
  submission still succeeds.
- **No new unlocks:** `new_unlocks` is `[]`; no toast fires; schema is quiet.
- **Toast remount:** fire-once-per-session guard prevents double-toast.
- **Strip fetch error / empty:** strip renders nothing; curriculum page
  unaffected.
- **401:** already handled globally by the `api` axios interceptor.

---

## Testing

### Backend (pytest)

- `check_and_record_unlocks` is invoked after a belief update in both
  `submit_answer` (quiz) and the review reinforcement path.
- Recording is idempotent — answering again does not duplicate events.
- Recording failure does not fail answer/review submission (defensive path).
- `get_session_unlocks` returns only events with `unlocked_at >= since`,
  joined to concept names.
- `SessionSummaryResponse` / `ReviewSummaryResponse` serialize `new_unlocks`
  (and default to `[]`).

### Frontend (Vitest)

- `useRecentUnlocks` — calls the service, correct query key, returns data.
- `RecentlyUnlockedStrip` — renders nothing when empty/errored; renders chips
  when populated; chips are focusable.
- `showUnlockToast` — message content, singular/plural, `+M more`, click →
  `navigate('/curriculum')`.
- `EndedState` — fires the toast once when `session_summary.new_unlocks` is
  present, not when empty; no double-fire on remount.
- Target the repo's 80% coverage minimum.

---

## Out of scope (this spec)

- Interactive dependency-graph visualization (Slice D / #15).
- Any change to `MasteryGateService` gate logic or the behavior of the four
  existing prerequisite endpoints.
- Real-time / push notifications — this slice is post-session only.
- Migrating unlock types to `packages/shared-types` (kept in
  `prerequisiteService.ts`, consistent with Slice B).
- The known follow-ups logged in project memory (Redis test-env auth,
  `test_reading_chunks.py` index-name assertions, `quiz_answer_service` coverage
  port) — untouched.

---

## Assumptions

- `quiz_answer_service` and `review_session_service` can obtain a
  `MasteryGateService` (or its dependencies — session + `ConceptRepository`)
  without a larger refactor; exact DI is decided in the plan.
- `QuizSession.started_at` (confirmed present) is the correct "this session"
  anchor for quiz; the review session exposes an equivalent start timestamp.
- `check_and_record_unlocks` correctly evaluates unlock state from the freshly
  written belief states (belief update is committed/visible before the call).
- react-hot-toast remains the toast mechanism; a single global `<Toaster/>` is
  acceptable app-wide.
