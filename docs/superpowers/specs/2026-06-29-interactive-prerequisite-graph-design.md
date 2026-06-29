# Interactive Prerequisite Graph Visualization — Design

**Issue:** #15 (Slice D of Story 4.11 — Prerequisite-Based Curriculum Navigation)
**Date:** 2026-06-29
**Builds on:** Slice B (curriculum page, lock status) — see `2026-06-26-curriculum-prerequisite-navigation-design.md`

## 1. Summary

Add an interactive, deep-linkable concept-dependency graph to the curriculum
experience. Rather than rendering the full 1,197-node DAG as a single hairball,
the view is **focused on one concept at a time**: it shows that concept's local
prerequisite neighborhood (what to master first) and dependent neighborhood
(what mastering it unlocks), 2 hops in each direction, color-coded by knowledge
area and overlaid with the current user's lock status. Clicking a neighbor
re-centers the graph on it; a per-node Practice action launches focused practice.

The view's size is bounded by **progressive disclosure**, not by truncation:
dense "hub" concepts collapse their overflow children into expandable cluster
nodes. As a result the view is independent of both total course size and node
degree.

## 2. Goals / Non-goals

**Goals**
- Render a readable, interactive neighborhood graph for any concept.
- Reuse existing focused-practice launch + soft-gate-for-locked behavior.
- Stay in sync with live DB data (topology) and per-user lock status.
- Scale to courses of any size and concepts of any connectivity.

**Non-goals (YAGNI / deferred)**
- Rendering the entire course DAG at once (no WebGL / global clustering).
- Configurable traversal depth UI (fixed at depth 2 this slice).
- A side detail panel (clicking re-centers; Practice is per-node).
- Editing prerequisite relationships.

## 3. Key decisions (from brainstorming)

| Decision | Choice |
|---|---|
| Primary purpose | Focused "what to study next" neighborhood view |
| Data source | New live backend endpoint (DB + per-user lock status) |
| Neighborhood | Prerequisites (up) + dependents (down), depth 2 each |
| Entry / presentation | Dedicated deep-linkable route, full page |
| Graph library | React Flow (`@xyflow/react`) + `dagre` top-down layout |
| Node click | Re-center on the clicked neighbor; Practice is a per-node button |
| Hub density | Expandable cluster nodes (progressive disclosure), no product cap |

## 4. Architecture

```
ConceptRow ──"View map"──▶ /curriculum/graph/:conceptId
                                   │
                          ConceptGraphPage (react-query + expand state)
                                   │  GET /concepts/{id}/neighborhood?depth=2
                                   ▼
                          graphClustering(neighborhood, expandedSet)
                                   │  → visible nodes/edges (incl. cluster nodes)
                                   ▼
                          graphLayout (dagre, top-down)
                                   ▼
                          PrerequisiteGraph (<ReactFlow>)
                                   │
                          ConceptGraphNode ×N
                            ├─ concept node: click neighbor ─▶ navigate(/curriculum/graph/:thatId)
                            │                Practice button ─▶ focused quiz (soft-gate if locked)
                            └─ cluster node: click ─────────▶ expand (local state) → re-cluster + re-layout
```

## 5. Backend

### 5.1 Endpoint

`GET /concepts/{concept_id}/neighborhood?depth=2`

- Added to `apps/api/src/routes/prerequisites.py` (mounted under `/concepts`,
  auth-protected like its siblings).
- `depth` query param: integer, clamped to **1–3**, default **2**.
- `404` if `concept_id` is unknown to the user's course.

### 5.2 Schemas (`apps/api/src/schemas/`)

```python
class NeighborhoodNode(BaseModel):
    concept_id: str
    name: str
    knowledge_area_id: str
    difficulty: float | None
    is_unlocked: bool
    mastery_progress: float          # 0..1, reused from gate logic
    depth: int                       # signed: -2..-1 prereq, 0 center, 1..2 unlock
    direction: Literal["prereq", "center", "unlock"]

class NeighborhoodEdge(BaseModel):
    source: str                      # prerequisite_concept_id
    target: str                      # concept_id (the thing unlocked)
    relationship_type: str
    strength: float

class NeighborhoodResponse(BaseModel):
    center_id: str
    depth: int
    nodes: list[NeighborhoodNode]
    edges: list[NeighborhoodEdge]
    truncated: bool                  # true only if absolute safety ceiling hit
```

Edge direction is canonical: `source` = prerequisite, `target` = dependent
(prerequisite → the concept it unlocks), regardless of which side the BFS
reached first. Frontend renders arrows pointing from prerequisite upward to the
concept it enables.

### 5.3 Service / repository

- Extend the mastery-gate service (and `ConceptPrerequisite` repository) with a
  `get_neighborhood(user_id, concept_id, depth)` method.
- BFS **upstream** over `concept_prerequisites` (prerequisite → concept) and
  **downstream** (concept → dependents) from the center, up to `depth` hops each
  direction. Deduplicate nodes reached by multiple paths (a node keeps its
  smallest absolute depth; `direction` is determined by the side it was reached
  from, center always wins).
- Join each node with the user's `is_unlocked` + `mastery_progress` via existing
  gate logic.
- **Absolute safety ceiling** `MAX_NEIGHBORHOOD_NODES` (config constant,
  default 500): a defensive payload/DoS backstop for pathological dense graphs,
  **not** a product/UX limit. If exceeded, drop farthest-depth nodes first, set
  `truncated: true`, and log the truncation (never silent). In normal operation
  this is never hit — display density is handled on the frontend via clustering.
- All async; SQLAlchemy ORM + repository pattern only; no raw SQL.

## 6. Frontend

### 6.1 Dependencies

Add to `apps/web`: `@xyflow/react`, `dagre`, `@types/dagre` (dev).

### 6.2 Route

In `apps/web/src/App.tsx` (`createBrowserRouter`), add:

```tsx
{
  path: '/curriculum/graph/:conceptId',
  element: <ProtectedRoute><ConceptGraphPage /></ProtectedRoute>,
}
```

### 6.3 Service + types (`services/prerequisiteService.ts`)

Add `getNeighborhood(conceptId, depth = 2): Promise<NeighborhoodResponse>` plus
mirrored TS interfaces (`NeighborhoodNode`, `NeighborhoodEdge`,
`NeighborhoodResponse`). Follows the existing co-located-types pattern used
throughout the prerequisite feature for consistency.

### 6.4 Components

- **`pages/ConceptGraphPage.tsx`** — reads `:conceptId`; react-query
  `['neighborhood', conceptId, depth]`; owns the `expandedClusters: Set<string>`
  state (reset whenever `conceptId` changes). Renders `Navigation`, a
  back-to-curriculum link, a header with the center concept's name, and the
  graph. Handles loading skeleton / error+retry / empty states.
- **`components/curriculum/PrerequisiteGraph.tsx`** — wraps `<ReactFlow>`;
  consumes already-clustered+laid-out nodes/edges; renders `Background`,
  `Controls`, and a `MiniMap` color-coded by KA. Routes neighbor clicks up to
  the page (`navigate`) and cluster clicks to the expand handler.
- **`components/curriculum/ConceptGraphNode.tsx`** — custom React Flow node with
  two variants:
  - *concept node*: KA-color accent (from `course.knowledge_areas[].color_hex`),
    lock state via reused `ConceptLockBadge`, name, mastery bar, and a
    **Practice** button. The center node is visually emphasized.
  - *cluster node*: e.g. `"+14 more prerequisites ▸"`; clicking adds its ID to
    `expandedClusters`.

### 6.5 Utilities

- **`utils/graphClustering.ts`** (pure): `(neighborhood, expandedSet) →
  { nodes, edges }` including synthetic cluster nodes. For each
  (parent, direction), show the top-`CLUSTER_THRESHOLD` (config constant, ~6)
  children ranked by **actionability** — edge `strength` desc, tiebreak by
  closeness-to-unlock (higher `mastery_progress`) for prerequisites — and
  collapse the overflow into a single cluster node. If a cluster's ID is in
  `expandedSet`, emit its real children + edges instead.
- **`utils/graphLayout.ts`** (pure): dagre top-down layout → node positions.
  Memoized on `[visibleNodes, visibleEdges]`.

### 6.6 Shared practice hook (refactor, in-scope)

Extract `hooks/useConceptPractice.ts` from `ConceptRow`'s inline logic:
unlocked → `navigate(buildFocusQuizUrl(...))`; locked → open
`LockedConceptConfirmDialog`, then `attemptLocked` + launch on confirm. Reuse it
in both `ConceptRow` and `ConceptGraphNode` (no behavior change to `ConceptRow`).

### 6.7 Entry point

Add a "View map" / prerequisites action on `ConceptRow` linking to
`/curriculum/graph/:conceptId`.

## 7. Data flow & state

- react-query owns server state, keyed by `conceptId`.
- Clicking a neighbor changes the route param → query refetches → clustering and
  dagre re-run → graph re-renders centered on the new concept.
- Clicking a cluster mutates `expandedClusters` (local state) → clustering and
  layout re-run; no network call.
- KA → color is resolved client-side from the already-cached course query
  (`course.knowledge_areas[].color_hex`), keeping the endpoint lean.

## 8. Performance

Bounded by **display**, not data:
- Only top-`CLUSTER_THRESHOLD` children per parent render until expanded, so even
  a 200-prerequisite hub shows a handful of nodes plus a cluster chip.
- Independent of total course size (only one local neighborhood is ever loaded)
  and of node degree (overflow is collapsed, not truncated).
- Layout/clustering memoized; recompute only on data or expansion change.

## 9. Error / empty / accessibility

- **Loading:** skeleton consistent with `CurriculumPage`.
- **Error:** panel with retry (mirrors current curriculum error UI).
- **Empty:** concept with no prerequisites and no dependents → render the lone
  center node with "No prerequisites — you can start this now."
- **Accessibility:** the React Flow canvas is not screen-reader friendly, so the
  page also renders a visually-hidden, ordered **text list** of prerequisites and
  dependents (real links to re-center + real Practice buttons) as the accessible
  equivalent. Node Practice actions are real `<button>`s; cluster expanders are
  real buttons with `aria-expanded`.

## 10. Testing (≥80% both ends)

**Backend (pytest)**
- `get_neighborhood`: BFS depth both directions; dedup across paths; smallest-
  depth wins; direction assignment; canonical edge orientation; lock-status join.
- Absolute ceiling: `truncated` flag set + farthest-depth dropped when exceeded.
- Route: auth required; `404` unknown concept; `depth` clamping; response shape.

**Frontend (Vitest + msw)**
- `getNeighborhood` service call.
- `graphClustering`: top-K selection, actionability ranking, overflow cluster
  creation, expand reveals correct children + edges.
- `graphLayout`: deterministic positions for a small fixture.
- `ConceptGraphNode`: concept variant (KA color, lock badge, Practice → soft-gate
  via `useConceptPractice`); cluster variant (renders count, click expands).
- `ConceptGraphPage`: loading / error / empty / rendered; neighbor click
  re-navigates; cluster expand updates the graph without a refetch.
- `useConceptPractice` hook unit test.
- axe check on the page.

## 11. Out of scope / follow-ups

- Whole-course overview / per-KA subgraph views (separate slices if wanted).
- Configurable-depth UI control.
- Selection side panel with richer concept detail.
- Serving topology from the static `prerequisite_graph.json` export (we chose the
  live endpoint instead).
