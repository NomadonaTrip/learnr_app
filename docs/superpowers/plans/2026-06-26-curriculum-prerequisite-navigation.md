# Curriculum Prerequisite Navigation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Populate the CBAP prerequisite graph and ship a `/curriculum` page where learners see lock/unlock status per knowledge area, view blocking prerequisites, and launch focused practice (with a soft-gate confirm for locked concepts).

**Architecture:** Slice A runs the existing graph builder against the CBAP course and adds a verification script. Slice B adds a React page that fetches bulk unlock status once per course, groups concepts into KA accordions client-side, lazily fetches blocking-prerequisite detail per concept on hover, and launches focused quizzes via the existing `/quiz?focus=concept&targets=…` URL mechanism. The override endpoint is called when a user confirms launching a locked concept.

**Tech Stack:** Python 3.11 / SQLAlchemy async / NetworkX (slice A); React + TypeScript + Vite + Tailwind + Zustand + `@tanstack/react-query` + react-router-dom + Vitest/RTL (slice B).

## Global Constraints

- Frontend API access only via the service layer (`prerequisiteService`, `courseService`) — never axios in components.
- Data fetching via `@tanstack/react-query`; Zustand updated immutably.
- Components PascalCase; hooks camelCase (`useX`); functions camelCase; constants UPPER_SNAKE_CASE.
- Backend: SQLAlchemy ORM only (no raw SQL in app code); snake_case functions/tables.
- 80% minimum test coverage, both frontend and backend.
- Reuse existing patterns: `CollapsibleSection` for accordions, `getErrorMessage` style from `hooks/useReview.ts` for error text, focused-practice launch via `/quiz?focus=concept&targets=<id>&name=<name>`.
- CBAP course id: `1b8a4860-156f-4d06-8393-85c4088db2d9` (194 concepts).
- No backend changes to `MasteryGateService` or the four existing `/concepts/*` endpoints.

---

## File Structure

**Slice A**
- Create: `scripts/verify_prerequisite_graph.py` — standalone async DB health check for the prerequisite graph.

**Slice B**
- Modify: `apps/web/src/hooks/useConceptLockStatus.ts` — add `useAttemptLockedConcept` mutation hook.
- Create: `apps/web/src/utils/curriculum.ts` — pure `groupConceptsByKa` helper + `buildFocusQuizUrl`.
- Create: `apps/web/src/components/curriculum/ConceptLockBadge.tsx` — locked/unlocked pill.
- Create: `apps/web/src/components/curriculum/ConceptLockTooltip.tsx` — presentational blocking-prereq popover.
- Create: `apps/web/src/components/curriculum/LockedConceptConfirmDialog.tsx` — soft-gate confirm dialog.
- Create: `apps/web/src/components/curriculum/ConceptRow.tsx` — one concept row (container: handles hover detail, click, override, navigation).
- Create: `apps/web/src/components/curriculum/KnowledgeAreaSection.tsx` — KA accordion with count header.
- Create: `apps/web/src/pages/CurriculumPage.tsx` — page shell + data fetch + grouping + states.
- Modify: `apps/web/src/App.tsx` — add `/curriculum` protected route.
- Modify: `apps/web/src/components/layout/Navigation.tsx` — add "Curriculum" nav link.
- Tests co-located under `__tests__/` next to each unit, matching the existing convention.

---

## Task A1: Populate the CBAP graph + verification script

**Files:**
- Create: `scripts/verify_prerequisite_graph.py`
- Run: `scripts/build_prerequisite_graph.py` (existing, no change)
- Verify: existing `tests/unit/test_prerequisite_graph.py`, `apps/api/tests/unit/test_prerequisite_graph_service.py`

**Interfaces:**
- Consumes: `concept_prerequisites`, `concepts` tables; `DATABASE_URL` env var.
- Produces: a CLI script exiting 0 on a healthy graph, non-zero otherwise. No code consumed by later tasks.

- [ ] **Step 1: Confirm the graph is currently empty (baseline)**

Run:
```bash
docker exec learnr-postgres-dev psql -U learnr -d learnr_dev -tAc \
  "SELECT count(*) FROM concept_prerequisites;"
```
Expected: `0` (confirms the builder has not run yet).

- [ ] **Step 2: Write the verification script**

Create `scripts/verify_prerequisite_graph.py`:
```python
"""
Verify the prerequisite knowledge graph is populated and healthy.

Exits 0 if all invariants hold, 1 otherwise. Safe to run in CI after
build_prerequisite_graph.py or after any concept re-extraction.

Usage:
    python scripts/verify_prerequisite_graph.py --course-id <UUID>
"""
import argparse
import asyncio
import os
import sys
from pathlib import Path
from uuid import UUID

import networkx as nx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Match build_prerequisite_graph.py bootstrap: make `src` importable.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "apps" / "api"))


async def verify(course_id: UUID) -> list[str]:
    """Return a list of failure messages (empty list == healthy)."""
    database_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://learnr:learnr123@localhost:5432/learnr_dev",
    )
    engine = create_async_engine(database_url, echo=False)
    failures: list[str] = []

    async with engine.connect() as conn:
        concept_count = (
            await conn.execute(
                text("SELECT count(*) FROM concepts WHERE course_id = :cid"),
                {"cid": str(course_id)},
            )
        ).scalar_one()
        if concept_count == 0:
            return [
                "No concepts for this course. Run scripts/extract_babok_concepts.py first."
            ]

        edge_rows = (
            await conn.execute(
                text(
                    """
                    SELECT cp.concept_id, cp.prerequisite_concept_id
                    FROM concept_prerequisites cp
                    JOIN concepts c ON c.id = cp.concept_id
                    WHERE c.course_id = :cid
                    """
                ),
                {"cid": str(course_id)},
            )
        ).all()

        if len(edge_rows) == 0:
            failures.append("0 prerequisite edges — run build_prerequisite_graph.py.")

        self_loops = sum(1 for a, b in edge_rows if a == b)
        if self_loops:
            failures.append(f"{self_loops} self-loop edges found.")

        depth_distinct = (
            await conn.execute(
                text(
                    "SELECT count(DISTINCT prerequisite_depth) FROM concepts "
                    "WHERE course_id = :cid"
                ),
                {"cid": str(course_id)},
            )
        ).scalar_one()
        if edge_rows and depth_distinct <= 1:
            failures.append(
                "prerequisite_depth has a single value — depths not computed."
            )

        graph = nx.DiGraph()
        graph.add_edges_from((str(a), str(b)) for a, b in edge_rows)
        if not nx.is_directed_acyclic_graph(graph):
            failures.append("Graph contains cycles (not a DAG).")

        roots = [n for n in graph.nodes if graph.out_degree(n) == 0]
        if edge_rows and not roots:
            failures.append("No root concepts (every node has a prerequisite).")

        avg_prereqs = (len(edge_rows) / concept_count) if concept_count else 0
        max_depth = (
            await conn.execute(
                text(
                    "SELECT COALESCE(max(prerequisite_depth), 0) FROM concepts "
                    "WHERE course_id = :cid"
                ),
                {"cid": str(course_id)},
            )
        ).scalar_one()

        print(f"concepts={concept_count} edges={len(edge_rows)} "
              f"avg_prereqs={avg_prereqs:.2f} max_depth={max_depth} roots={len(roots)}")

    await engine.dispose()
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify prerequisite graph health")
    parser.add_argument(
        "--course-id",
        default="1b8a4860-156f-4d06-8393-85c4088db2d9",
        help="Course UUID (defaults to CBAP)",
    )
    args = parser.parse_args()
    failures = asyncio.run(verify(UUID(args.course_id)))
    if failures:
        print("FAIL:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("OK: prerequisite graph is healthy.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 3: Run verify against the empty graph to confirm it FAILS**

Run:
```bash
cd /mnt/e/TOOLMAKER/PYTHON/LearnR_2 && python scripts/verify_prerequisite_graph.py
```
Expected: exit code 1, output includes `0 prerequisite edges`.

- [ ] **Step 4: Build the graph for CBAP**

Run (online — uses OpenAI for semantic + GPT-4 inference):
```bash
cd /mnt/e/TOOLMAKER/PYTHON/LearnR_2 && python scripts/build_prerequisite_graph.py \
  --course-id 1b8a4860-156f-4d06-8393-85c4088db2d9 --remove-cycles
```
Offline fallback (hierarchy-only, no API key):
```bash
python scripts/build_prerequisite_graph.py \
  --course-id 1b8a4860-156f-4d06-8393-85c4088db2d9 --remove-cycles --skip-gpt4 --skip-embeddings
```
Expected: log lines reporting edges created and depths updated; `scripts/output/prerequisite_graph.{graphml,json}` written.

- [ ] **Step 5: Run verify again to confirm it PASSES**

Run:
```bash
python scripts/verify_prerequisite_graph.py
```
Expected: exit code 0, output `OK: prerequisite graph is healthy.` with edges > 0.

- [ ] **Step 6: Run existing graph test suites**

Run:
```bash
cd /mnt/e/TOOLMAKER/PYTHON/LearnR_2 && python -m pytest \
  tests/unit/test_prerequisite_graph.py \
  apps/api/tests/unit/test_prerequisite_graph_service.py -q
```
Expected: all pass.

- [ ] **Step 7: Commit**

```bash
cd /mnt/e/TOOLMAKER/PYTHON/LearnR_2
git add scripts/verify_prerequisite_graph.py
git commit -m "feat: add prerequisite graph verification script and populate CBAP graph"
```

---

## Task B1: Add `useAttemptLockedConcept` mutation hook

**Files:**
- Modify: `apps/web/src/hooks/useConceptLockStatus.ts`
- Test: `apps/web/src/hooks/__tests__/useAttemptLockedConcept.test.tsx`

**Interfaces:**
- Consumes: `prerequisiteService.attemptLockedConcept(conceptId) → Promise<OverrideAttemptResponse>` (exists).
- Produces: `useAttemptLockedConcept()` returning a react-query mutation whose `mutateAsync(conceptId: string)` resolves to `OverrideAttemptResponse`.

- [ ] **Step 1: Write the failing test**

Create `apps/web/src/hooks/__tests__/useAttemptLockedConcept.test.tsx`:
```tsx
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useAttemptLockedConcept } from '../useConceptLockStatus'
import { prerequisiteService } from '../../services/prerequisiteService'

vi.mock('../../services/prerequisiteService', () => ({
  prerequisiteService: { attemptLockedConcept: vi.fn() },
}))

function wrapper({ children }: { children: React.ReactNode }) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>
}

describe('useAttemptLockedConcept', () => {
  beforeEach(() => vi.clearAllMocks())

  it('calls the override endpoint and returns the response', async () => {
    vi.mocked(prerequisiteService.attemptLockedConcept).mockResolvedValue({
      concept_id: 'c1',
      concept_name: 'Stakeholder Analysis',
      was_locked: true,
      override_allowed: true,
      blocking_prerequisites: [],
      mastery_progress: 0.5,
      message: 'Proceeding with locked concept.',
    })

    const { result } = renderHook(() => useAttemptLockedConcept(), { wrapper })
    const response = await result.current.mutateAsync('c1')

    expect(prerequisiteService.attemptLockedConcept).toHaveBeenCalledWith('c1')
    expect(response.was_locked).toBe(true)
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
  })
})
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd apps/web && npx vitest run src/hooks/__tests__/useAttemptLockedConcept.test.tsx`
Expected: FAIL — `useAttemptLockedConcept` is not exported.

- [ ] **Step 3: Add the hook**

Append to `apps/web/src/hooks/useConceptLockStatus.ts` (after the existing exports), adding `useMutation` to the existing react-query import:
```tsx
// at top: change the import to include useMutation
// import { useQuery, useMutation } from '@tanstack/react-query'
import { OverrideAttemptResponse } from '../services/prerequisiteService'

/**
 * Override-launch a locked concept. Logs the attempt server-side (AC 8) and
 * returns the concept's lock status. The caller navigates to the focused quiz
 * on success.
 */
export function useAttemptLockedConcept() {
  return useMutation<OverrideAttemptResponse, unknown, string>({
    mutationFn: (conceptId: string) =>
      prerequisiteService.attemptLockedConcept(conceptId),
  })
}
```
Also add `prerequisiteService` to the existing service import line in this file if not already imported (`import { prerequisiteService, GateCheckResult, BulkUnlockStatusResponse, OverrideAttemptResponse } from '../services/prerequisiteService'`).

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd apps/web && npx vitest run src/hooks/__tests__/useAttemptLockedConcept.test.tsx`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/hooks/useConceptLockStatus.ts apps/web/src/hooks/__tests__/useAttemptLockedConcept.test.tsx
git commit -m "feat: add useAttemptLockedConcept mutation hook"
```

---

## Task B2: Curriculum utils — `groupConceptsByKa` + `buildFocusQuizUrl`

**Files:**
- Create: `apps/web/src/utils/curriculum.ts`
- Test: `apps/web/src/utils/__tests__/curriculum.test.ts`

**Interfaces:**
- Consumes: `ConceptUnlockStatus` from `prerequisiteService`; KA shape `{ id, name, abbreviation, color_hex }` from `courseService.CourseDetail.knowledge_areas`.
- Produces:
  - `groupConceptsByKa(concepts: ConceptUnlockStatus[], knowledgeAreas: KnowledgeAreaMeta[]) → KaGroup[]` where `KaGroup = { knowledgeArea: KnowledgeAreaMeta; concepts: ConceptUnlockStatus[]; unlockedCount: number; totalCount: number }`. Groups by `concept.knowledge_area_id === knowledgeArea.id`, preserving the `knowledgeAreas` order, dropping KAs with no concepts.
  - `buildFocusQuizUrl(conceptId: string, conceptName: string) → string` returning `/quiz?focus=concept&targets=<enc>&name=<enc>`.

- [ ] **Step 1: Write the failing test**

Create `apps/web/src/utils/__tests__/curriculum.test.ts`:
```ts
import { describe, it, expect } from 'vitest'
import { groupConceptsByKa, buildFocusQuizUrl } from '../curriculum'
import type { ConceptUnlockStatus } from '../../services/prerequisiteService'

const ka = [
  { id: 'ka-plan', name: 'Planning', abbreviation: 'BAPM', color_hex: '#3b82f6' },
  { id: 'ka-elic', name: 'Elicitation', abbreviation: 'EC', color_hex: '#22c55e' },
]

function concept(id: string, kaId: string, unlocked: boolean): ConceptUnlockStatus {
  return {
    concept_id: id, concept_name: id, knowledge_area_id: kaId,
    is_unlocked: unlocked, has_prerequisites: !unlocked,
    prerequisite_count: unlocked ? 0 : 2, mastered_prerequisite_count: unlocked ? 0 : 1,
    mastery_progress: unlocked ? 1 : 0.5,
  }
}

describe('groupConceptsByKa', () => {
  it('groups concepts under their KA and counts unlocked/total', () => {
    const groups = groupConceptsByKa(
      [concept('a', 'ka-plan', true), concept('b', 'ka-plan', false), concept('c', 'ka-elic', true)],
      ka,
    )
    expect(groups).toHaveLength(2)
    expect(groups[0].knowledgeArea.id).toBe('ka-plan')
    expect(groups[0].totalCount).toBe(2)
    expect(groups[0].unlockedCount).toBe(1)
    expect(groups[1].knowledgeArea.id).toBe('ka-elic')
  })

  it('drops KAs that have no concepts', () => {
    const groups = groupConceptsByKa([concept('a', 'ka-plan', true)], ka)
    expect(groups).toHaveLength(1)
    expect(groups[0].knowledgeArea.id).toBe('ka-plan')
  })
})

describe('buildFocusQuizUrl', () => {
  it('encodes the concept id and name', () => {
    expect(buildFocusQuizUrl('c-1', 'Risk & Value')).toBe(
      '/quiz?focus=concept&targets=c-1&name=Risk%20%26%20Value',
    )
  })
})
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd apps/web && npx vitest run src/utils/__tests__/curriculum.test.ts`
Expected: FAIL — module not found.

- [ ] **Step 3: Write the implementation**

Create `apps/web/src/utils/curriculum.ts`:
```ts
import type { ConceptUnlockStatus } from '../services/prerequisiteService'

export interface KnowledgeAreaMeta {
  id: string
  name: string
  abbreviation: string
  color_hex: string
}

export interface KaGroup {
  knowledgeArea: KnowledgeAreaMeta
  concepts: ConceptUnlockStatus[]
  unlockedCount: number
  totalCount: number
}

/**
 * Group concepts under their knowledge area, preserving KA order and
 * dropping KAs with no concepts.
 */
export function groupConceptsByKa(
  concepts: ConceptUnlockStatus[],
  knowledgeAreas: KnowledgeAreaMeta[],
): KaGroup[] {
  return knowledgeAreas
    .map((knowledgeArea) => {
      const kaConcepts = concepts.filter(
        (c) => c.knowledge_area_id === knowledgeArea.id,
      )
      return {
        knowledgeArea,
        concepts: kaConcepts,
        unlockedCount: kaConcepts.filter((c) => c.is_unlocked).length,
        totalCount: kaConcepts.length,
      }
    })
    .filter((group) => group.totalCount > 0)
}

/**
 * Build the focused-practice quiz URL for a single concept, matching the
 * existing `/quiz?focus=concept&targets=…` convention (QuizPage parses these).
 */
export function buildFocusQuizUrl(conceptId: string, conceptName: string): string {
  return `/quiz?focus=concept&targets=${encodeURIComponent(
    conceptId,
  )}&name=${encodeURIComponent(conceptName)}`
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd apps/web && npx vitest run src/utils/__tests__/curriculum.test.ts`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/utils/curriculum.ts apps/web/src/utils/__tests__/curriculum.test.ts
git commit -m "feat: add curriculum grouping and focus-quiz-url utils"
```

---

## Task B3: `ConceptLockBadge` component

**Files:**
- Create: `apps/web/src/components/curriculum/ConceptLockBadge.tsx`
- Test: `apps/web/src/components/curriculum/__tests__/ConceptLockBadge.test.tsx`

**Interfaces:**
- Produces: `ConceptLockBadge({ isUnlocked }: { isUnlocked: boolean })` — green "Unlocked" pill or gray "Locked" pill, with an `aria-label` reflecting state.

- [ ] **Step 1: Write the failing test**

Create `apps/web/src/components/curriculum/__tests__/ConceptLockBadge.test.tsx`:
```tsx
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ConceptLockBadge } from '../ConceptLockBadge'

describe('ConceptLockBadge', () => {
  it('renders an unlocked badge', () => {
    render(<ConceptLockBadge isUnlocked />)
    expect(screen.getByLabelText('Concept unlocked')).toBeInTheDocument()
    expect(screen.getByText('Unlocked')).toBeInTheDocument()
  })

  it('renders a locked badge', () => {
    render(<ConceptLockBadge isUnlocked={false} />)
    expect(screen.getByLabelText('Concept locked')).toBeInTheDocument()
    expect(screen.getByText('Locked')).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd apps/web && npx vitest run src/components/curriculum/__tests__/ConceptLockBadge.test.tsx`
Expected: FAIL — module not found.

- [ ] **Step 3: Write the implementation**

Create `apps/web/src/components/curriculum/ConceptLockBadge.tsx`:
```tsx
interface ConceptLockBadgeProps {
  isUnlocked: boolean
}

/**
 * Small pill showing whether a concept is unlocked or locked (AC 4).
 */
export function ConceptLockBadge({ isUnlocked }: ConceptLockBadgeProps) {
  return (
    <span
      aria-label={isUnlocked ? 'Concept unlocked' : 'Concept locked'}
      className={
        isUnlocked
          ? 'inline-flex items-center gap-1 rounded-full bg-green-50 px-2.5 py-0.5 text-xs font-medium text-green-700'
          : 'inline-flex items-center gap-1 rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-500'
      }
    >
      {isUnlocked ? 'Unlocked' : 'Locked'}
    </span>
  )
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd apps/web && npx vitest run src/components/curriculum/__tests__/ConceptLockBadge.test.tsx`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/components/curriculum/ConceptLockBadge.tsx apps/web/src/components/curriculum/__tests__/ConceptLockBadge.test.tsx
git commit -m "feat: add ConceptLockBadge component"
```

---

## Task B4: `ConceptLockTooltip` (presentational)

**Files:**
- Create: `apps/web/src/components/curriculum/ConceptLockTooltip.tsx`
- Test: `apps/web/src/components/curriculum/__tests__/ConceptLockTooltip.test.tsx`

**Interfaces:**
- Produces: `ConceptLockTooltip(props)` where
  `props = { isLoading: boolean; error: boolean; blockingPrerequisites: { concept_id: string; name: string }[]; closestName: string | null }`.
  Pure/presentational — no data fetching. Shows a loading line, an error line, "All prerequisites met" when empty+not-loading+no-error, or a list of blocking prerequisite names with the closest-to-unlock annotated (AC 5/6).

- [ ] **Step 1: Write the failing test**

Create `apps/web/src/components/curriculum/__tests__/ConceptLockTooltip.test.tsx`:
```tsx
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ConceptLockTooltip } from '../ConceptLockTooltip'

describe('ConceptLockTooltip', () => {
  it('shows loading', () => {
    render(<ConceptLockTooltip isLoading error={false} blockingPrerequisites={[]} closestName={null} />)
    expect(screen.getByText('Loading prerequisites…')).toBeInTheDocument()
  })

  it('shows error inline', () => {
    render(<ConceptLockTooltip isLoading={false} error blockingPrerequisites={[]} closestName={null} />)
    expect(screen.getByText("Couldn't load prerequisites")).toBeInTheDocument()
  })

  it('lists blocking prerequisites and marks the closest', () => {
    render(
      <ConceptLockTooltip
        isLoading={false}
        error={false}
        blockingPrerequisites={[{ concept_id: 'a', name: 'Stakeholders' }, { concept_id: 'b', name: 'Scope' }]}
        closestName="Scope"
      />,
    )
    expect(screen.getByText('Stakeholders')).toBeInTheDocument()
    expect(screen.getByText(/Scope/)).toBeInTheDocument()
    expect(screen.getByText(/closest/i)).toBeInTheDocument()
  })

  it('shows all-met when there are no blockers', () => {
    render(<ConceptLockTooltip isLoading={false} error={false} blockingPrerequisites={[]} closestName={null} />)
    expect(screen.getByText('All prerequisites met')).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd apps/web && npx vitest run src/components/curriculum/__tests__/ConceptLockTooltip.test.tsx`
Expected: FAIL — module not found.

- [ ] **Step 3: Write the implementation**

Create `apps/web/src/components/curriculum/ConceptLockTooltip.tsx`:
```tsx
interface ConceptLockTooltipProps {
  isLoading: boolean
  error: boolean
  blockingPrerequisites: { concept_id: string; name: string }[]
  closestName: string | null
}

/**
 * Presentational popover listing the unmastered prerequisites blocking a
 * concept (AC 5), annotating the one closest to unlock (AC 6).
 */
export function ConceptLockTooltip({
  isLoading,
  error,
  blockingPrerequisites,
  closestName,
}: ConceptLockTooltipProps) {
  return (
    <div
      role="tooltip"
      className="mt-2 rounded-lg border border-gray-200 bg-white p-3 text-sm shadow-md"
    >
      {isLoading && <p className="text-gray-500">Loading prerequisites…</p>}
      {!isLoading && error && (
        <p className="text-amber-600">Couldn't load prerequisites</p>
      )}
      {!isLoading && !error && blockingPrerequisites.length === 0 && (
        <p className="text-green-700">All prerequisites met</p>
      )}
      {!isLoading && !error && blockingPrerequisites.length > 0 && (
        <>
          <p className="mb-1 font-medium text-gray-700">Master these first:</p>
          <ul className="space-y-1">
            {blockingPrerequisites.map((p) => (
              <li key={p.concept_id} className="text-gray-600">
                {p.name}
                {closestName === p.name && (
                  <span className="ml-1 text-xs text-primary-600">(closest to unlock)</span>
                )}
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  )
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd apps/web && npx vitest run src/components/curriculum/__tests__/ConceptLockTooltip.test.tsx`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/components/curriculum/ConceptLockTooltip.tsx apps/web/src/components/curriculum/__tests__/ConceptLockTooltip.test.tsx
git commit -m "feat: add ConceptLockTooltip presentational component"
```

---

## Task B5: `LockedConceptConfirmDialog`

**Files:**
- Create: `apps/web/src/components/curriculum/LockedConceptConfirmDialog.tsx`
- Test: `apps/web/src/components/curriculum/__tests__/LockedConceptConfirmDialog.test.tsx`

**Interfaces:**
- Produces: `LockedConceptConfirmDialog(props)` where
  `props = { conceptName: string; blockingPrerequisites: { concept_id: string; name: string }[]; isSubmitting: boolean; onConfirm: () => void; onCancel: () => void }`.
  Renders a `role="dialog"`; "Practice anyway" button calls `onConfirm`, "Cancel" calls `onCancel`; confirm button is disabled while `isSubmitting`.

- [ ] **Step 1: Write the failing test**

Create `apps/web/src/components/curriculum/__tests__/LockedConceptConfirmDialog.test.tsx`:
```tsx
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { LockedConceptConfirmDialog } from '../LockedConceptConfirmDialog'

describe('LockedConceptConfirmDialog', () => {
  const props = {
    conceptName: 'Strategy Analysis',
    blockingPrerequisites: [{ concept_id: 'a', name: 'Current State' }],
    isSubmitting: false,
    onConfirm: vi.fn(),
    onCancel: vi.fn(),
  }
  beforeEach(() => vi.clearAllMocks())

  it('renders the concept name and blockers', () => {
    render(<LockedConceptConfirmDialog {...props} />)
    expect(screen.getByRole('dialog')).toBeInTheDocument()
    expect(screen.getByText(/Strategy Analysis/)).toBeInTheDocument()
    expect(screen.getByText('Current State')).toBeInTheDocument()
  })

  it('calls onConfirm when practice-anyway is clicked', () => {
    render(<LockedConceptConfirmDialog {...props} />)
    fireEvent.click(screen.getByRole('button', { name: /practice anyway/i }))
    expect(props.onConfirm).toHaveBeenCalledTimes(1)
  })

  it('calls onCancel when cancel is clicked', () => {
    render(<LockedConceptConfirmDialog {...props} />)
    fireEvent.click(screen.getByRole('button', { name: /cancel/i }))
    expect(props.onCancel).toHaveBeenCalledTimes(1)
  })

  it('disables confirm while submitting', () => {
    render(<LockedConceptConfirmDialog {...props} isSubmitting />)
    expect(screen.getByRole('button', { name: /starting/i })).toBeDisabled()
  })
})
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd apps/web && npx vitest run src/components/curriculum/__tests__/LockedConceptConfirmDialog.test.tsx`
Expected: FAIL — module not found.

- [ ] **Step 3: Write the implementation**

Create `apps/web/src/components/curriculum/LockedConceptConfirmDialog.tsx`:
```tsx
interface LockedConceptConfirmDialogProps {
  conceptName: string
  blockingPrerequisites: { concept_id: string; name: string }[]
  isSubmitting: boolean
  onConfirm: () => void
  onCancel: () => void
}

/**
 * Soft-gate confirmation before practicing a locked concept (AC 8).
 * Confirming triggers the override-attempt call, then the focused quiz launch.
 */
export function LockedConceptConfirmDialog({
  conceptName,
  blockingPrerequisites,
  isSubmitting,
  onConfirm,
  onCancel,
}: LockedConceptConfirmDialogProps) {
  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={`Practice ${conceptName} before prerequisites are mastered?`}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      onKeyDown={(e) => e.key === 'Escape' && onCancel()}
    >
      <div className="w-full max-w-md rounded-[14px] bg-white p-6 shadow-xl">
        <h2 className="text-lg font-semibold text-charcoal">
          Practice “{conceptName}” anyway?
        </h2>
        <p className="mt-2 text-sm text-gray-600">
          These prerequisites aren’t mastered yet. You can still practice, but
          mastering them first usually leads to better results.
        </p>
        {blockingPrerequisites.length > 0 && (
          <ul className="mt-3 space-y-1 text-sm text-gray-700">
            {blockingPrerequisites.map((p) => (
              <li key={p.concept_id}>• {p.name}</li>
            ))}
          </ul>
        )}
        <div className="mt-6 flex justify-end gap-3">
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 text-sm font-medium text-gray-700 rounded-[14px] border border-gray-300 hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={isSubmitting}
            className="px-4 py-2 text-sm font-medium text-white rounded-[14px] bg-primary-600 hover:bg-primary-700 disabled:opacity-50"
          >
            {isSubmitting ? 'Starting…' : 'Practice anyway'}
          </button>
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd apps/web && npx vitest run src/components/curriculum/__tests__/LockedConceptConfirmDialog.test.tsx`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/components/curriculum/LockedConceptConfirmDialog.tsx apps/web/src/components/curriculum/__tests__/LockedConceptConfirmDialog.test.tsx
git commit -m "feat: add LockedConceptConfirmDialog component"
```

---

## Task B6: `ConceptRow` (container)

**Files:**
- Create: `apps/web/src/components/curriculum/ConceptRow.tsx`
- Test: `apps/web/src/components/curriculum/__tests__/ConceptRow.test.tsx`

**Interfaces:**
- Consumes: `ConceptUnlockStatus`; `useConceptLockStatus(conceptId | null)` (exists; disabled when arg is falsy); `useAttemptLockedConcept()` (Task B1); `buildFocusQuizUrl` (Task B2); `ConceptLockBadge` (B3); `ConceptLockTooltip` (B4); `LockedConceptConfirmDialog` (B5); `useNavigate` from react-router-dom.
- Produces: `ConceptRow({ concept }: { concept: ConceptUnlockStatus })`.
  - Unlocked click → `navigate(buildFocusQuizUrl(...))`.
  - Locked click → open dialog; on confirm → `await attemptLocked.mutateAsync(conceptId)` then `navigate(buildFocusQuizUrl(...))`.
  - On hover/focus → enable `useConceptLockStatus` and render the tooltip.

- [ ] **Step 1: Write the failing test**

Create `apps/web/src/components/curriculum/__tests__/ConceptRow.test.tsx`:
```tsx
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { ConceptRow } from '../ConceptRow'
import type { ConceptUnlockStatus } from '../../../services/prerequisiteService'

const navigateMock = vi.fn()
vi.mock('react-router-dom', () => ({ useNavigate: () => navigateMock }))

const mutateAsyncMock = vi.fn()
vi.mock('../../../hooks/useConceptLockStatus', () => ({
  useConceptLockStatus: () => ({ data: undefined, isLoading: false, isError: false }),
  useAttemptLockedConcept: () => ({ mutateAsync: mutateAsyncMock, isPending: false }),
}))

function makeConcept(unlocked: boolean): ConceptUnlockStatus {
  return {
    concept_id: 'c-1', concept_name: 'Stakeholder Analysis', knowledge_area_id: 'ka-1',
    is_unlocked: unlocked, has_prerequisites: !unlocked,
    prerequisite_count: unlocked ? 0 : 2, mastered_prerequisite_count: 0,
    mastery_progress: unlocked ? 1 : 0.5,
  }
}

describe('ConceptRow', () => {
  beforeEach(() => vi.clearAllMocks())

  it('renders the concept name and an unlocked badge', () => {
    render(<ConceptRow concept={makeConcept(true)} />)
    expect(screen.getByText('Stakeholder Analysis')).toBeInTheDocument()
    expect(screen.getByLabelText('Concept unlocked')).toBeInTheDocument()
  })

  it('navigates straight to focused quiz when unlocked', () => {
    render(<ConceptRow concept={makeConcept(true)} />)
    fireEvent.click(screen.getByRole('button', { name: /practice/i }))
    expect(navigateMock).toHaveBeenCalledWith(
      '/quiz?focus=concept&targets=c-1&name=Stakeholder%20Analysis',
    )
  })

  it('opens the confirm dialog when locked, then overrides and navigates', async () => {
    mutateAsyncMock.mockResolvedValue({})
    render(<ConceptRow concept={makeConcept(false)} />)
    fireEvent.click(screen.getByRole('button', { name: /practice/i }))
    expect(screen.getByRole('dialog')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /practice anyway/i }))
    await waitFor(() => expect(mutateAsyncMock).toHaveBeenCalledWith('c-1'))
    expect(navigateMock).toHaveBeenCalledWith(
      '/quiz?focus=concept&targets=c-1&name=Stakeholder%20Analysis',
    )
  })
})
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd apps/web && npx vitest run src/components/curriculum/__tests__/ConceptRow.test.tsx`
Expected: FAIL — module not found.

- [ ] **Step 3: Write the implementation**

Create `apps/web/src/components/curriculum/ConceptRow.tsx`:
```tsx
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import type { ConceptUnlockStatus } from '../../services/prerequisiteService'
import { useConceptLockStatus, useAttemptLockedConcept } from '../../hooks/useConceptLockStatus'
import { buildFocusQuizUrl } from '../../utils/curriculum'
import { ConceptLockBadge } from './ConceptLockBadge'
import { ConceptLockTooltip } from './ConceptLockTooltip'
import { LockedConceptConfirmDialog } from './LockedConceptConfirmDialog'

interface ConceptRowProps {
  concept: ConceptUnlockStatus
}

/**
 * One concept row: badge, mastery progress, lazy prerequisite tooltip, and a
 * Practice action with a soft-gate confirm for locked concepts.
 */
export function ConceptRow({ concept }: ConceptRowProps) {
  const navigate = useNavigate()
  const [showDetail, setShowDetail] = useState(false)
  const [showDialog, setShowDialog] = useState(false)
  const attemptLocked = useAttemptLockedConcept()

  // Lazy: only fetch blocking-prerequisite detail once the row is hovered/focused.
  const status = useConceptLockStatus(showDetail ? concept.concept_id : null)
  const blockers = (status.data?.blocking_prerequisites ?? []).map((b) => ({
    concept_id: b.concept_id,
    name: b.name,
  }))
  const closestName = status.data?.closest_to_unlock?.name ?? null

  const launch = () =>
    navigate(buildFocusQuizUrl(concept.concept_id, concept.concept_name))

  const handlePractice = () => {
    if (concept.is_unlocked) {
      launch()
    } else {
      setShowDialog(true)
    }
  }

  const handleConfirm = async () => {
    try {
      await attemptLocked.mutateAsync(concept.concept_id)
      setShowDialog(false)
      launch()
    } catch {
      // Keep the dialog open on failure; mutation error state is surfaced below.
    }
  }

  return (
    <div
      className="border-b border-gray-100 py-3"
      onMouseEnter={() => setShowDetail(true)}
      onFocus={() => setShowDetail(true)}
    >
      <div className="flex items-center justify-between gap-3">
        <div className="min-w-0">
          <p className="truncate text-sm font-medium text-gray-900">
            {concept.concept_name}
          </p>
          <div className="mt-1 flex items-center gap-2">
            <ConceptLockBadge isUnlocked={concept.is_unlocked} />
            {concept.has_prerequisites && (
              <span className="text-xs text-gray-500">
                {concept.mastered_prerequisite_count}/{concept.prerequisite_count} prerequisites
              </span>
            )}
          </div>
          <div className="mt-2 h-1.5 w-40 overflow-hidden rounded-full bg-gray-100">
            <div
              className="h-full rounded-full bg-primary-500"
              style={{ width: `${Math.round(concept.mastery_progress * 100)}%` }}
            />
          </div>
        </div>
        <button
          type="button"
          onClick={handlePractice}
          className="shrink-0 px-3 py-1.5 text-sm font-medium text-primary-700 rounded-[14px] border border-primary-200 hover:bg-primary-50"
        >
          Practice
        </button>
      </div>

      {showDetail && !concept.is_unlocked && (
        <ConceptLockTooltip
          isLoading={status.isLoading}
          error={status.isError}
          blockingPrerequisites={blockers}
          closestName={closestName}
        />
      )}

      {showDialog && (
        <LockedConceptConfirmDialog
          conceptName={concept.concept_name}
          blockingPrerequisites={blockers}
          isSubmitting={attemptLocked.isPending}
          onConfirm={handleConfirm}
          onCancel={() => setShowDialog(false)}
        />
      )}
    </div>
  )
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd apps/web && npx vitest run src/components/curriculum/__tests__/ConceptRow.test.tsx`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/components/curriculum/ConceptRow.tsx apps/web/src/components/curriculum/__tests__/ConceptRow.test.tsx
git commit -m "feat: add ConceptRow with soft-gate launch flow"
```

---

## Task B7: `KnowledgeAreaSection`

**Files:**
- Create: `apps/web/src/components/curriculum/KnowledgeAreaSection.tsx`
- Test: `apps/web/src/components/curriculum/__tests__/KnowledgeAreaSection.test.tsx`

**Interfaces:**
- Consumes: `KaGroup` from `utils/curriculum` (B2); `CollapsibleSection` (exists, props `{ id, title, children, defaultExpanded? }`); `ConceptRow` (B6).
- Produces: `KnowledgeAreaSection({ group }: { group: KaGroup })` — a collapsible titled `"<KA name> — <unlocked>/<total> unlocked"` (AC 10) containing one `ConceptRow` per concept.

- [ ] **Step 1: Write the failing test**

Create `apps/web/src/components/curriculum/__tests__/KnowledgeAreaSection.test.tsx`:
```tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { KnowledgeAreaSection } from '../KnowledgeAreaSection'
import type { KaGroup } from '../../../utils/curriculum'

// ConceptRow pulls in router/hooks; stub it to keep this a pure section test.
vi.mock('../ConceptRow', () => ({
  ConceptRow: ({ concept }: { concept: { concept_name: string } }) => (
    <div data-testid="concept-row">{concept.concept_name}</div>
  ),
}))

const group: KaGroup = {
  knowledgeArea: { id: 'ka-1', name: 'Planning', abbreviation: 'BAPM', color_hex: '#3b82f6' },
  concepts: [
    { concept_id: 'a', concept_name: 'Approach', knowledge_area_id: 'ka-1', is_unlocked: true, has_prerequisites: false, prerequisite_count: 0, mastered_prerequisite_count: 0, mastery_progress: 1 },
    { concept_id: 'b', concept_name: 'Governance', knowledge_area_id: 'ka-1', is_unlocked: false, has_prerequisites: true, prerequisite_count: 2, mastered_prerequisite_count: 1, mastery_progress: 0.5 },
  ],
  unlockedCount: 1,
  totalCount: 2,
}

describe('KnowledgeAreaSection', () => {
  it('renders the KA title with unlocked/total count', () => {
    render(<KnowledgeAreaSection group={group} />)
    expect(screen.getByText(/Planning — 1\/2 unlocked/)).toBeInTheDocument()
  })

  it('renders a row per concept when expanded by default', () => {
    render(<KnowledgeAreaSection group={group} />)
    expect(screen.getAllByTestId('concept-row')).toHaveLength(2)
  })
})
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd apps/web && npx vitest run src/components/curriculum/__tests__/KnowledgeAreaSection.test.tsx`
Expected: FAIL — module not found.

- [ ] **Step 3: Write the implementation**

Create `apps/web/src/components/curriculum/KnowledgeAreaSection.tsx`:
```tsx
import { CollapsibleSection } from '../ui/CollapsibleSection'
import { ConceptRow } from './ConceptRow'
import type { KaGroup } from '../../utils/curriculum'

interface KnowledgeAreaSectionProps {
  group: KaGroup
}

/**
 * Collapsible group of concepts for one knowledge area, with an unlocked/total
 * count in the header (AC 10).
 */
export function KnowledgeAreaSection({ group }: KnowledgeAreaSectionProps) {
  const { knowledgeArea, concepts, unlockedCount, totalCount } = group
  return (
    <CollapsibleSection
      id={`ka-${knowledgeArea.id}`}
      title={`${knowledgeArea.name} — ${unlockedCount}/${totalCount} unlocked`}
      defaultExpanded
    >
      <div className="divide-y divide-gray-100">
        {concepts.map((concept) => (
          <ConceptRow key={concept.concept_id} concept={concept} />
        ))}
      </div>
    </CollapsibleSection>
  )
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd apps/web && npx vitest run src/components/curriculum/__tests__/KnowledgeAreaSection.test.tsx`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/components/curriculum/KnowledgeAreaSection.tsx apps/web/src/components/curriculum/__tests__/KnowledgeAreaSection.test.tsx
git commit -m "feat: add KnowledgeAreaSection accordion"
```

---

## Task B8: `CurriculumPage`

**Files:**
- Create: `apps/web/src/pages/CurriculumPage.tsx`
- Test: `apps/web/src/pages/__tests__/CurriculumPage.test.tsx`

**Interfaces:**
- Consumes: `courseService.fetchCourseBySlug` (exists); `useBulkUnlockStatus(courseId | null)` (exists); `groupConceptsByKa` (B2); `KnowledgeAreaSection` (B7); `Navigation` (exists).
- Produces: `CurriculumPage()` route component. Resolves the course slug from sessionStorage (same pattern as `useDiagnosticResults`, default `'cbap'`), fetches the course for its `id` + `knowledge_areas`, fetches bulk unlock status, groups, and renders: loading / no-graph empty / error / grouped success.

- [ ] **Step 1: Write the failing test**

Create `apps/web/src/pages/__tests__/CurriculumPage.test.tsx`:
```tsx
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { CurriculumPage } from '../CurriculumPage'
import { courseService } from '../../services/courseService'
import { prerequisiteService } from '../../services/prerequisiteService'

vi.mock('../../components/layout/Navigation', () => ({ Navigation: () => null }))
// KnowledgeAreaSection pulls ConceptRow (router/hooks); stub for a page-level test.
vi.mock('../../components/curriculum/KnowledgeAreaSection', () => ({
  KnowledgeAreaSection: ({ group }: { group: { knowledgeArea: { name: string } } }) => (
    <div data-testid="ka-section">{group.knowledgeArea.name}</div>
  ),
}))
vi.mock('../../services/courseService', () => ({
  courseService: { fetchCourseBySlug: vi.fn() },
}))
vi.mock('../../services/prerequisiteService', () => ({
  prerequisiteService: { getBulkUnlockStatus: vi.fn() },
}))

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <CurriculumPage />
    </QueryClientProvider>,
  )
}

const course = {
  id: 'course-1', slug: 'cbap', name: 'CBAP', knowledge_areas: [
    { id: 'ka-1', name: 'Planning', abbreviation: 'BAPM', color_hex: '#3b82f6' },
  ],
}

describe('CurriculumPage', () => {
  beforeEach(() => vi.clearAllMocks())

  it('renders KA sections on success', async () => {
    vi.mocked(courseService.fetchCourseBySlug).mockResolvedValue(course as never)
    vi.mocked(prerequisiteService.getBulkUnlockStatus).mockResolvedValue({
      knowledge_area_id: null, total_concepts: 1, unlocked_count: 1, locked_count: 0,
      no_prerequisites_count: 1, concepts: [
        { concept_id: 'a', concept_name: 'Approach', knowledge_area_id: 'ka-1', is_unlocked: true, has_prerequisites: false, prerequisite_count: 0, mastered_prerequisite_count: 0, mastery_progress: 1 },
      ],
    })
    renderPage()
    await waitFor(() => expect(screen.getByTestId('ka-section')).toHaveTextContent('Planning'))
  })

  it('shows the not-ready empty state when there are no concepts', async () => {
    vi.mocked(courseService.fetchCourseBySlug).mockResolvedValue(course as never)
    vi.mocked(prerequisiteService.getBulkUnlockStatus).mockResolvedValue({
      knowledge_area_id: null, total_concepts: 0, unlocked_count: 0, locked_count: 0,
      no_prerequisites_count: 0, concepts: [],
    })
    renderPage()
    await waitFor(() =>
      expect(screen.getByText(/curriculum map isn’t ready/i)).toBeInTheDocument(),
    )
  })

  it('shows an error card when the status request fails', async () => {
    vi.mocked(courseService.fetchCourseBySlug).mockResolvedValue(course as never)
    vi.mocked(prerequisiteService.getBulkUnlockStatus).mockRejectedValue(new Error('boom'))
    renderPage()
    await waitFor(() =>
      expect(screen.getByText(/couldn’t load your curriculum/i)).toBeInTheDocument(),
    )
  })
})
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd apps/web && npx vitest run src/pages/__tests__/CurriculumPage.test.tsx`
Expected: FAIL — module not found.

- [ ] **Step 3: Write the implementation**

Create `apps/web/src/pages/CurriculumPage.tsx`:
```tsx
import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Navigation } from '../components/layout/Navigation'
import { courseService } from '../services/courseService'
import { useBulkUnlockStatus } from '../hooks/useConceptLockStatus'
import { groupConceptsByKa } from '../utils/curriculum'
import { KnowledgeAreaSection } from '../components/curriculum/KnowledgeAreaSection'

const ONBOARDING_STORAGE_KEY = 'learnr_onboarding'
const DEFAULT_COURSE_SLUG = 'cbap'

/** Resolve the onboarding-selected course slug (mirrors useDiagnosticResults). */
function getSelectedCourseSlug(): string {
  try {
    const stored = sessionStorage.getItem(ONBOARDING_STORAGE_KEY)
    if (stored) {
      const data = JSON.parse(stored)
      return data.course || DEFAULT_COURSE_SLUG
    }
  } catch {
    // Ignore parse errors
  }
  return DEFAULT_COURSE_SLUG
}

/**
 * Curriculum / Concept Map page: lock-status per knowledge area with focused
 * practice launch (Story 4.11 UI, slice B).
 */
export function CurriculumPage() {
  const courseSlug = useMemo(() => getSelectedCourseSlug(), [])
  const courseQuery = useQuery({
    queryKey: ['course', courseSlug],
    queryFn: () => courseService.fetchCourseBySlug(courseSlug),
    staleTime: Infinity,
    retry: 2,
  })

  const courseId = courseQuery.data?.id ?? null
  const statusQuery = useBulkUnlockStatus(courseId)

  const groups = useMemo(() => {
    if (!courseQuery.data || !statusQuery.data) return []
    return groupConceptsByKa(
      statusQuery.data.concepts,
      courseQuery.data.knowledge_areas,
    )
  }, [courseQuery.data, statusQuery.data])

  const isLoading = courseQuery.isLoading || statusQuery.isLoading
  const isError = courseQuery.isError || statusQuery.isError
  const isEmptyGraph = statusQuery.data?.total_concepts === 0

  return (
    <div className="min-h-screen bg-cream">
      <Navigation />
      <main className="mx-auto max-w-3xl px-4 py-8 sm:px-6 lg:px-8">
        <h1 className="text-2xl font-bold text-charcoal">Curriculum</h1>
        <p className="mt-1 text-sm text-gray-600">
          Concepts grouped by knowledge area. Locked concepts list the
          prerequisites to master first.
        </p>

        <div className="mt-6 space-y-3">
          {isLoading && <p className="text-gray-500">Loading your curriculum…</p>}

          {!isLoading && isError && (
            <div className="rounded-[14px] border border-red-200 bg-red-50 p-4">
              <p className="font-medium text-red-800">Couldn’t load your curriculum</p>
              <button
                type="button"
                onClick={() => statusQuery.refetch()}
                className="mt-2 text-sm font-medium text-red-700 underline"
              >
                Try again
              </button>
            </div>
          )}

          {!isLoading && !isError && isEmptyGraph && (
            <div className="rounded-[14px] border border-gray-200 bg-white p-6 text-center">
              <p className="font-medium text-charcoal">
                Your curriculum map isn’t ready yet
              </p>
              <p className="mt-1 text-sm text-gray-600">
                Prerequisite data is still being prepared. Check back soon.
              </p>
            </div>
          )}

          {!isLoading && !isError && !isEmptyGraph &&
            groups.map((group) => (
              <KnowledgeAreaSection key={group.knowledgeArea.id} group={group} />
            ))}
        </div>
      </main>
    </div>
  )
}

export default CurriculumPage
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd apps/web && npx vitest run src/pages/__tests__/CurriculumPage.test.tsx`
Expected: PASS (all three states).

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/pages/CurriculumPage.tsx apps/web/src/pages/__tests__/CurriculumPage.test.tsx
git commit -m "feat: add CurriculumPage with KA grouping and states"
```

---

## Task B9: Wire route + nav link

**Files:**
- Modify: `apps/web/src/App.tsx`
- Modify: `apps/web/src/components/layout/Navigation.tsx`

**Interfaces:**
- Consumes: `CurriculumPage` (B8), existing `ProtectedRoute`, existing `Navigation` link pattern.
- Produces: `/curriculum` protected route + a "Curriculum" nav link.

- [ ] **Step 1: Add the import and route in `App.tsx`**

Add the import near the other page imports (after the `QuizPage` import line):
```tsx
import { CurriculumPage } from './pages/CurriculumPage'
```
Add this route object to the `createBrowserRouter([...])` array, immediately after the `/quiz` route object:
```tsx
  {
    path: '/curriculum',
    element: (
      <ProtectedRoute>
        <CurriculumPage />
      </ProtectedRoute>
    ),
  },
```

- [ ] **Step 2: Add the nav link in `Navigation.tsx`**

Insert this `Link` immediately after the Dashboard `Link` (the one with `to="/diagnostic/results"`), before the Reading Library link:
```tsx
            {/* Curriculum Link */}
            <Link
              to="/curriculum"
              className="flex items-center gap-1 text-sm font-medium text-gray-600 hover:text-gray-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2 rounded-lg px-3 py-2"
              aria-label="Curriculum"
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                />
              </svg>
              <span>Curriculum</span>
            </Link>
```

- [ ] **Step 3: Type-check and run the full frontend test suite**

Run:
```bash
cd /mnt/e/TOOLMAKER/PYTHON/LearnR_2/apps/web
npx tsc --noEmit -p tsconfig.json
npx vitest run src/components/curriculum src/pages/__tests__/CurriculumPage.test.tsx src/utils/__tests__/curriculum.test.ts src/hooks/__tests__/useAttemptLockedConcept.test.tsx
```
Expected: no new tsc errors in any `curriculum`/`CurriculumPage`/`useAttemptLockedConcept` file; all listed tests pass.

- [ ] **Step 4: Manual smoke check**

Run `npm run dev:frontend` and `npm run dev:backend`, log in, click **Curriculum** in the nav. Expect KA accordions with badges; hover a locked concept to see its blocking prerequisites; click **Practice** on a locked concept to get the confirm dialog; confirm to land in a focused quiz.

- [ ] **Step 5: Commit**

```bash
cd /mnt/e/TOOLMAKER/PYTHON/LearnR_2
git add apps/web/src/App.tsx apps/web/src/components/layout/Navigation.tsx
git commit -m "feat: wire /curriculum route and nav link"
```

---

## Final verification

- [ ] Run frontend tests + coverage: `cd apps/web && npx vitest run --coverage` — curriculum units ≥ 80%.
- [ ] Run `python scripts/verify_prerequisite_graph.py` — exits 0.
- [ ] Confirm the earlier-scaffolded `prerequisiteService.ts` + `useConceptLockStatus.ts` (service + bulk/status hooks) are committed alongside this work.

---

## Self-Review Notes

**Spec coverage:** A (build + verify) → Task A1. AC 4 (lock/unlock visibility) → B3/B6/B7. AC 5 (blocking prereqs on hover) → B4/B6. AC 6 (closest to unlock) → B4/B6. AC 8 (override) → B1/B5/B6. AC 10 (per-KA counts) → B2/B7. Page placement + route + nav → B8/B9. Slices C (AC 7 notifications) and D (graph viz) are intentionally out of scope.

**Type consistency:** `ConceptUnlockStatus`, `GateCheckResult`, `OverrideAttemptResponse`, `BulkUnlockStatusResponse` are the names exported by the existing `prerequisiteService.ts`. `useConceptLockStatus(conceptId|null)` and `useBulkUnlockStatus(courseId|null)` exist; `useAttemptLockedConcept` is added in B1 and consumed in B6. `groupConceptsByKa`/`KaGroup`/`buildFocusQuizUrl` defined in B2, consumed in B6/B7/B8. Focus URL shape matches QuizPage's parser (`focus`, `targets`, `name`).

**Assumption to validate at execution:** the onboarding course slug resolves to CBAP; if a user has no onboarding data, the default `'cbap'` slug is used (same fallback as `useDiagnosticResults`).
