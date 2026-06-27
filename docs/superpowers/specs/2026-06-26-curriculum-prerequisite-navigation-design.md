# Design: Curriculum Prerequisite Navigation (Slice A + B)

**Date:** 2026-06-26
**Status:** Approved (design); pending spec review
**Related story:** 4.11 — Prerequisite-Based Curriculum Navigation
**Author:** Brainstormed with user (telltaio@gmail.com)

---

## Context & Problem

Story 4.11's backend is complete and verified (38 tests passing): a prerequisite
knowledge graph (`concept_prerequisites`), a `MasteryGateService`, four API
endpoints, and question-selector integration. However, two gaps remain:

1. **The graph is unpopulated.** Live DB check (2026-06-26) shows the CBAP course
   (`1b8a4860-156f-4d06-8393-85c4088db2d9`) has **194 concepts but 0 prerequisite
   edges**, with every concept at `prerequisite_depth = 0` (column default). The
   builder script has never been run, so there is nothing for any UI to display.
2. **No frontend consumes the endpoints.** Story 4.11 explicitly deferred UI to
   "Epic 6". ACs 4, 5, 6, 7, 8, 10 have backend support but no user-facing surface.

This design covers the first two slices of a four-slice plan to close those gaps.
Slices C and D are scoped out here and get their own design → plan → build cycles.

### Slice map (full feature)

| Slice | Delivers | Status |
|-------|----------|--------|
| **A** | Graph data population & verification | **This spec** |
| **B** | Curriculum / Concept Map page (AC 4, 5, 6, 8, 10) | **This spec** |
| C | Unlock notifications (AC 7) + standalone override surfacing | Deferred |
| D | Interactive dependency-graph visualization | Deferred |

### Decisions locked during brainstorming

- **Scope:** full UI + graph viz, delivered slice by slice. This spec = A + B.
- **Lock behavior:** *soft gate with confirm* — clicking a locked concept opens a
  confirmation dialog that calls the `attempt-locked` override endpoint (AC 8),
  then launches a focused quiz. Matches the backend `soft` default and the SM
  guidance "don't hard-block users initially".
- **Placement:** new top-level `/curriculum` route + a "Curriculum" nav link;
  the existing `/diagnostic/results` remains the Dashboard.
- **Data approach:** single bulk fetch per course, grouped into KA accordions
  client-side; per-concept blocking-prerequisite names fetched lazily on hover.

---

## Slice A — Graph data population & verification

**Goal:** populate `concept_prerequisites` + `concepts.prerequisite_depth` for the
CBAP course and provide a repeatable health check so slice B always has real data.

### Deliverables

1. **Run the existing builder** (no code change):
   ```bash
   python scripts/build_prerequisite_graph.py \
     --course-id 1b8a4860-156f-4d06-8393-85c4088db2d9 --remove-cycles
   # offline fallback (no OpenAI key): add --skip-gpt4 --skip-embeddings
   ```
   This writes edges, recomputes depths, and exports
   `scripts/output/prerequisite_graph.{graphml,json}`.

2. **New `scripts/verify_prerequisite_graph.py`** — an executable, CI-friendly
   verification helper that connects via the app DB session and asserts invariants,
   exiting non-zero on any failure:
   - edge count > 0;
   - `prerequisite_depth` populated with a non-trivial distribution (not all 0);
   - zero self-loops (`concept_id != prerequisite_concept_id`);
   - DAG holds (NetworkX topological sort succeeds — no cycles);
   - at least one root concept (no prerequisites) exists;
   - reports avg prerequisites/concept (target 2–5), max depth (target ≤ 10),
     orphan count, and edge-source breakdown (hierarchy / semantic / gpt4).
   - If `concepts` is empty, it instructs the operator to run
     `extract_babok_concepts.py` first.

### Acceptance (Slice A)

- `concept_prerequisites` edge count > 0 for the CBAP course.
- `prerequisite_depth` distribution spans more than `{0}`.
- `scripts/verify_prerequisite_graph.py` exits 0.
- Existing pytest graph suites still pass
  (`tests/unit/test_prerequisite_graph.py`,
  `apps/api/tests/unit/test_prerequisite_graph_service.py`).

---

## Slice B — Curriculum / Concept Map page

### Architecture & file layout

New route `/curriculum` (auth-protected via `ProtectedRoute`), reached from a new
**"Curriculum"** link in `components/layout/Navigation.tsx`.

```
apps/web/src/
  pages/
    CurriculumPage.tsx              # NEW — shell: fetch course + bulk status, group by KA, states
  components/curriculum/            # NEW directory
    KnowledgeAreaSection.tsx        # collapsible KA group: header count + progress
    ConceptRow.tsx                  # one concept: badge, progress, click handler
    ConceptLockBadge.tsx            # locked/unlocked pill (aria-labelled)
    ConceptLockTooltip.tsx          # lazy popover listing unmastered prereqs (AC 5/6)
    LockedConceptConfirmDialog.tsx  # soft-gate confirm → override → launch quiz (AC 8)
  hooks/
    useConceptLockStatus.ts         # EXISTS (status + bulk); ADD useAttemptLockedConcept mutation
  services/
    prerequisiteService.ts          # EXISTS — getPrerequisiteStatus/getBulkUnlockStatus/attemptLockedConcept
```

Each component is single-purpose and prop-driven. Conforms to project rules
(CLAUDE.md): API only via the service layer (no axios in components), react-query
for fetching, Zustand updated immutably, prop drilling ≤ 2 levels (the
concept-launch handler is passed page → section → row).

### Data flow

1. **Course resolution:** `getSelectedCourseSlug()` → `courseService.fetchCourseBySlug(slug)`
   (react-query) → `course.id` (UUID the endpoints require) + `knowledge_areas[]`
   (name, `color_hex`, abbreviation).
2. **Bulk status:** `useBulkUnlockStatus(course.id)` → all concepts, each with
   `knowledge_area_id`, `is_unlocked`, `prerequisite_count`,
   `mastered_prerequisite_count`, `mastery_progress`.
3. **Group** concepts by `knowledge_area_id`, joining KA metadata from
   `course.knowledge_areas` for color/label. One `KnowledgeAreaSection` per KA with
   a header count (`unlocked/total`) → **AC 10**.
4. **Per-row badge + progress bar** from bulk data → **AC 4**.
5. **Tooltip (lazy):** on row hover/focus, `useConceptLockStatus(conceptId)` fetches
   `blocking_prerequisites` (names) + `closest_to_unlock` → tooltip lists unmastered
   prerequisites → **AC 5 / AC 6**. react-query caches it (fires once per concept).
6. **Click concept:**
   - *Unlocked* → set `quizStore.focusContext = { type: 'concept', focusTargetId }`
     → `navigate('/quiz')` (reuses existing focused-practice entry path).
   - *Locked* → open `LockedConceptConfirmDialog` → on confirm,
     `useAttemptLockedConcept(conceptId)` mutation (logs override, **AC 8**) → then
     set `focusContext` → `navigate('/quiz')`.

### Error & edge-case handling

- **No course slug / course not found** → friendly empty state + CTA to
  onboarding/dashboard (no crash).
- **Graph not populated** (`total_concepts === 0`; the dependency on slice A) →
  distinct empty state ("Your curriculum map isn't ready yet"), clearly not an error.
- **Bulk status request error** → page-level error card with retry, using the
  `getErrorMessage` pattern from `hooks/useReview.ts`.
- **Tooltip fetch error** → inline, non-fatal ("Couldn't load prerequisites");
  never blocks the page.
- **Override mutation error** → dialog shows the error and keeps the user in place
  (no half-navigation).
- **401** → already handled globally by the `api` axios interceptor.

### Accessibility / UX

- Lock badge carries an `aria-label` reflecting state.
- Tooltip is keyboard-reachable (opens on focus, not hover-only).
- Confirm dialog traps focus and is dismissible via Escape.
- Section expand/collapse uses framer-motion, consistent with existing pages.

---

## Testing

- **Slice A (data):** `scripts/verify_prerequisite_graph.py` is the executable
  check; existing pytest graph suites still pass.
- **Slice B (frontend, Vitest):**
  - `ConceptRow` — locked vs unlocked rendering, progress bar, click dispatch.
  - `ConceptLockBadge` — correct label/aria per state.
  - `KnowledgeAreaSection` — count math, collapse behavior.
  - `LockedConceptConfirmDialog` — confirm calls override mutation then navigates;
    cancel does neither.
  - `CurriculumPage` — loading / empty-no-course / empty-no-graph / error /
    grouped-success states, with mocked `prerequisiteService` + `courseService`,
    wrapped in a react-query test client.
  - Target the repo's 80% coverage minimum.

---

## Out of scope (this spec)

- Unlock notifications / toasts (AC 7) — slice C.
- Interactive force-directed graph visualization (new viz dependency) — slice D.
- Any backend change to `MasteryGateService` or the four existing endpoints.
- Changes to diagnostic, reading, or review flows.

---

## Assumptions

- The onboarding-selected course slug resolves to the CBAP course for current
  users; `courseService.fetchCourseBySlug` returns `id` + `knowledge_areas`.
- The existing focused-practice path (`quizStore.focusContext` + `/quiz`) accepts
  `type: 'concept'` with a concept UUID, as used by current focused practice.
- The builder can reach OpenAI (or is run with `--skip-gpt4 --skip-embeddings` for
  a hierarchy-only graph) during slice A execution.
