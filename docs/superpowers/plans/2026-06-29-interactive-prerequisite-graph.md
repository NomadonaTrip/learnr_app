# Interactive Prerequisite Graph Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deep-linkable, interactive prerequisite-neighborhood graph to the curriculum experience, centered on one concept (prereqs up + dependents down, depth 2), with KA color-coding, lock status, expandable hub clusters, and click-to-practice.

**Architecture:** A new live backend endpoint `GET /concepts/{id}/neighborhood` BFS-traverses `concept_prerequisites` both directions to a clamped depth and joins per-node lock status (reusing the mastery-gate service). The frontend renders the response with React Flow + dagre on a dedicated route `/curriculum/graph/:conceptId`; dense hubs collapse overflow children into expandable cluster nodes (a pure client-side transform), so the view is independent of course size and node degree.

**Tech Stack:** FastAPI + SQLAlchemy (async) + Pydantic backend; React 18 + TypeScript + Vite + Tailwind + react-query frontend; new deps `@xyflow/react`, `dagre`. Backend tests pytest; frontend tests Vitest (+ msw for service, vi.mock for components).

**Spec:** `docs/superpowers/specs/2026-06-29-interactive-prerequisite-graph-design.md`

## Global Constraints

- 80% minimum test coverage, both frontend and backend.
- Backend: no raw SQL — SQLAlchemy ORM + repository pattern only; all DB/API ops async/await.
- Backend naming: PascalCase classes, snake_case functions/methods; API routes under existing `/concepts` prefix.
- Frontend: no axios in components — use `prerequisiteService`; never mutate Zustand/query state directly; PascalCase components, camelCase hooks/functions.
- Constants: UPPER_SNAKE_CASE both languages.
- Config/env only through config objects (e.g. `MasteryGateConfig`), never `os.environ`/`process.env` directly.
- Prerequisite TS types follow the existing co-located-in-service pattern (mirroring backend), consistent with the rest of Story 4.11.
- Commit format: `<type>(#15): <description>`.

---

## File Structure

**Backend**
- Modify `apps/api/src/schemas/mastery_gate.py` — add `NeighborhoodNode`, `NeighborhoodEdge`, `NeighborhoodResponse`; add `max_neighborhood_nodes` to `MasteryGateConfig`.
- Modify `apps/api/src/repositories/concept_repository.py` — add `get_dependents_with_strength`.
- Modify `apps/api/src/services/mastery_gate.py` — add `get_neighborhood`.
- Modify `apps/api/src/routes/prerequisites.py` — add `GET /{concept_id}/neighborhood`.

**Frontend**
- Modify `apps/web/src/services/prerequisiteService.ts` — neighborhood types + `getNeighborhood`.
- Modify `apps/web/src/hooks/useConceptLockStatus.ts` — `conceptLockKeys.neighborhood` + `useConceptNeighborhood`.
- Create `apps/web/src/hooks/useConceptPractice.ts` — extracted practice/soft-gate logic.
- Modify `apps/web/src/components/curriculum/ConceptRow.tsx` — use the hook; add "View map" link.
- Create `apps/web/src/utils/graphClustering.ts` — neighborhood → visible nodes/edges (+ clusters).
- Create `apps/web/src/utils/graphLayout.ts` — dagre layout.
- Create `apps/web/src/components/curriculum/ConceptGraphNode.tsx` — custom node (concept + cluster).
- Create `apps/web/src/components/curriculum/PrerequisiteGraph.tsx` — React Flow wrapper.
- Create `apps/web/src/pages/ConceptGraphPage.tsx` — page + state.
- Modify `apps/web/src/App.tsx` — register the route.

**Tests** — colocated per existing conventions (backend `tests/unit/...`, `tests/integration/...`; frontend `test/services`, `src/**/__tests__`, plus msw handlers/fixtures under `test/mocks` / `test/fixtures`).

---

## Task 1: Repository — `get_dependents_with_strength`

**Files:**
- Modify: `apps/api/src/repositories/concept_repository.py` (after `get_dependents`, ~line 324)
- Test: `apps/api/tests/unit/test_prerequisite_repository.py`

**Interfaces:**
- Produces: `ConceptRepository.get_dependents_with_strength(concept_id: UUID) -> list[tuple[Concept, float, str]]` — each tuple `(dependent_concept, strength, relationship_type)` for the edge `concept_id (prereq) -> dependent`.

- [ ] **Step 1: Write the failing test**

Add to `apps/api/tests/unit/test_prerequisite_repository.py` (follow the file's existing fixture style — it already creates a course + concepts + `ConceptPrerequisite` rows via `db_session`):

```python
@pytest.mark.asyncio
async def test_get_dependents_with_strength_returns_strength_and_type(
    db_session, concept_repo_with_chain
):
    # concept_repo_with_chain fixture exposes: repo, prereq_id, dependent_id
    # with an edge dependent depends-on prereq (strength=0.8, type="required")
    repo = concept_repo_with_chain["repo"]
    prereq_id = concept_repo_with_chain["prereq_id"]
    dependent_id = concept_repo_with_chain["dependent_id"]

    result = await repo.get_dependents_with_strength(prereq_id)

    assert len(result) == 1
    concept, strength, rel_type = result[0]
    assert concept.id == dependent_id
    assert strength == 0.8
    assert rel_type == "required"


@pytest.mark.asyncio
async def test_get_dependents_with_strength_empty_when_no_dependents(
    db_session, concept_repo_with_chain
):
    repo = concept_repo_with_chain["repo"]
    dependent_id = concept_repo_with_chain["dependent_id"]
    # dependent_id is a leaf — nothing depends on it
    assert await repo.get_dependents_with_strength(dependent_id) == []
```

Add this fixture near the top of the test file if not already present:

```python
@pytest.fixture
async def concept_repo_with_chain(db_session):
    from uuid import uuid4
    from src.models.concept import Concept
    from src.models.concept_prerequisite import ConceptPrerequisite
    from src.models.course import Course
    from src.repositories.concept_repository import ConceptRepository

    course = Course(slug=f"chain-{uuid4().hex[:8]}", name="C", description="d",
                    corpus_name="cbap", knowledge_areas=[{"id": "ka-1", "name": "KA"}],
                    is_active=True)
    db_session.add(course)
    await db_session.flush()

    prereq = Concept(course_id=course.id, name="Prereq", knowledge_area_id="ka-1",
                     difficulty_estimate=0.5)
    dependent = Concept(course_id=course.id, name="Dependent", knowledge_area_id="ka-1",
                        difficulty_estimate=0.6)
    db_session.add_all([prereq, dependent])
    await db_session.flush()

    db_session.add(ConceptPrerequisite(
        concept_id=dependent.id, prerequisite_concept_id=prereq.id,
        strength=0.8, relationship_type="required"))
    await db_session.commit()

    return {"repo": ConceptRepository(db_session),
            "prereq_id": prereq.id, "dependent_id": dependent.id}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/api && pytest tests/unit/test_prerequisite_repository.py -k dependents_with_strength -v`
Expected: FAIL — `AttributeError: 'ConceptRepository' object has no attribute 'get_dependents_with_strength'`

- [ ] **Step 3: Write minimal implementation**

In `apps/api/src/repositories/concept_repository.py`, after `get_dependents` (mirror `get_prerequisites_with_strength` but reverse the join):

```python
    async def get_dependents_with_strength(
        self, concept_id: UUID
    ) -> list[tuple[Concept, float, str]]:
        """
        Get direct dependents (reverse edge) with strength and relationship type.

        Args:
            concept_id: Prerequisite concept UUID

        Returns:
            List of tuples (dependent Concept, strength, relationship_type)
            for the edge ``concept_id (prereq) -> dependent``.
        """
        result = await self.session.execute(
            select(
                Concept,
                ConceptPrerequisite.strength,
                ConceptPrerequisite.relationship_type,
            )
            .join(
                ConceptPrerequisite,
                ConceptPrerequisite.concept_id == Concept.id,
            )
            .where(ConceptPrerequisite.prerequisite_concept_id == concept_id)
            .order_by(ConceptPrerequisite.strength.desc())
        )
        return list(result.all())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd apps/api && pytest tests/unit/test_prerequisite_repository.py -k dependents_with_strength -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add apps/api/src/repositories/concept_repository.py apps/api/tests/unit/test_prerequisite_repository.py
git commit -m "feat(#15): add get_dependents_with_strength repo method"
```

---

## Task 2: Schemas + Service — `get_neighborhood`

**Files:**
- Modify: `apps/api/src/schemas/mastery_gate.py` (add 3 schemas; add config field)
- Modify: `apps/api/src/services/mastery_gate.py` (add `get_neighborhood`)
- Test: `apps/api/tests/unit/services/test_mastery_gate.py`

**Interfaces:**
- Consumes: `ConceptRepository.get_by_id`, `.get_prerequisites_with_strength`, `.get_dependents_with_strength` (Task 1); `MasteryGateService.check_prerequisites_mastered(user_id, concept_id) -> GateCheckResult` (existing; provides `.is_unlocked`, `.mastery_progress`).
- Produces:
  - `NeighborhoodNode(concept_id: UUID, name: str, knowledge_area_id: str, difficulty: float, is_unlocked: bool, mastery_progress: float, depth: int, direction: Literal["prereq","center","unlock"])`
  - `NeighborhoodEdge(source: UUID, target: UUID, relationship_type: str, strength: float)`
  - `NeighborhoodResponse(center_id: UUID, depth: int, nodes: list[NeighborhoodNode], edges: list[NeighborhoodEdge], truncated: bool)`
  - `MasteryGateService.get_neighborhood(user_id: UUID, concept_id: UUID, depth: int = 2) -> NeighborhoodResponse` (raises `ValueError` if concept missing).
  - `MasteryGateConfig.max_neighborhood_nodes: int` (default 500).

- [ ] **Step 1: Write the failing test**

Add to `apps/api/tests/unit/services/test_mastery_gate.py`. The file already provides `mastery_gate_service`, `mock_concept_repo`, `mock_belief_repo` fixtures (mocked repos).

```python
class TestGetNeighborhood:
    @pytest.mark.asyncio
    async def test_builds_bidirectional_neighborhood_with_lock_status(
        self, mastery_gate_service, mock_concept_repo
    ):
        from unittest.mock import AsyncMock
        center_id, prereq_id, dep_id = uuid4(), uuid4(), uuid4()

        def concept(cid, name):
            c = MagicMock()
            c.id, c.name, c.knowledge_area_id, c.difficulty_estimate = cid, name, "ka-1", 0.5
            return c

        mock_concept_repo.get_by_id = AsyncMock(return_value=concept(center_id, "Center"))
        mock_concept_repo.get_prerequisites_with_strength = AsyncMock(
            side_effect=lambda cid: [(concept(prereq_id, "Prereq"), 0.8, "required")]
            if cid == center_id else []
        )
        mock_concept_repo.get_dependents_with_strength = AsyncMock(
            side_effect=lambda cid: [(concept(dep_id, "Dependent"), 0.7, "required")]
            if cid == center_id else []
        )

        # Reuse the real gate check but stub its result per concept.
        async def fake_gate(user_id, concept_id):
            return GateCheckResult(
                concept_id=concept_id, concept_name="x",
                is_unlocked=(concept_id != prereq_id),
                blocking_prerequisites=[], closest_to_unlock=None,
                mastery_progress=0.4 if concept_id == prereq_id else 1.0,
                estimated_questions_to_unlock=0)
        mastery_gate_service.check_prerequisites_mastered = fake_gate

        result = await mastery_gate_service.get_neighborhood(uuid4(), center_id, depth=2)

        ids = {n.concept_id: n for n in result.nodes}
        assert set(ids) == {center_id, prereq_id, dep_id}
        assert ids[center_id].direction == "center" and ids[center_id].depth == 0
        assert ids[prereq_id].direction == "prereq" and ids[prereq_id].depth == -1
        assert ids[dep_id].direction == "unlock" and ids[dep_id].depth == 1
        assert ids[prereq_id].is_unlocked is False
        # Edges are canonical: prereq -> center, center -> dependent
        edge_pairs = {(e.source, e.target) for e in result.edges}
        assert (prereq_id, center_id) in edge_pairs
        assert (center_id, dep_id) in edge_pairs
        assert result.truncated is False

    @pytest.mark.asyncio
    async def test_truncates_when_over_ceiling(
        self, mastery_gate_service, mock_concept_repo
    ):
        from unittest.mock import AsyncMock
        mastery_gate_service.config.max_neighborhood_nodes = 1  # only center fits
        center_id, prereq_id = uuid4(), uuid4()

        def concept(cid):
            c = MagicMock()
            c.id, c.name, c.knowledge_area_id, c.difficulty_estimate = cid, "n", "ka-1", 0.5
            return c

        mock_concept_repo.get_by_id = AsyncMock(return_value=concept(center_id))
        mock_concept_repo.get_prerequisites_with_strength = AsyncMock(
            side_effect=lambda cid: [(concept(prereq_id), 0.8, "required")]
            if cid == center_id else [])
        mock_concept_repo.get_dependents_with_strength = AsyncMock(return_value=[])

        async def fake_gate(user_id, concept_id):
            return GateCheckResult(
                concept_id=concept_id, concept_name="x", is_unlocked=True,
                blocking_prerequisites=[], closest_to_unlock=None,
                mastery_progress=1.0, estimated_questions_to_unlock=0)
        mastery_gate_service.check_prerequisites_mastered = fake_gate

        result = await mastery_gate_service.get_neighborhood(uuid4(), center_id, depth=2)
        assert result.truncated is True
        assert [n.concept_id for n in result.nodes] == [center_id]

    @pytest.mark.asyncio
    async def test_raises_when_concept_missing(
        self, mastery_gate_service, mock_concept_repo
    ):
        from unittest.mock import AsyncMock
        mock_concept_repo.get_by_id = AsyncMock(return_value=None)
        with pytest.raises(ValueError):
            await mastery_gate_service.get_neighborhood(uuid4(), uuid4(), depth=2)
```

Ensure `MagicMock` is imported in the test file (it already imports from `unittest.mock`).

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/api && pytest tests/unit/services/test_mastery_gate.py::TestGetNeighborhood -v`
Expected: FAIL — `AttributeError: ... no attribute 'get_neighborhood'`

- [ ] **Step 3: Write minimal implementation**

In `apps/api/src/schemas/mastery_gate.py`:

Add the config field inside `MasteryGateConfig` (after `min_responses_for_gate`):

```python
    max_neighborhood_nodes: int = Field(
        default=500,
        ge=1,
        description="Absolute safety ceiling on nodes returned by the "
        "neighborhood endpoint (defensive backstop, not a UX limit)",
    )
```

Add at the end of the file (ensure `from typing import Literal` and `from uuid import UUID` are imported at top):

```python
class NeighborhoodNode(BaseModel):
    """One concept in a focused prerequisite neighborhood (Story 4.11, Slice D)."""
    concept_id: UUID
    name: str
    knowledge_area_id: str
    difficulty: float
    is_unlocked: bool
    mastery_progress: float = Field(ge=0.0, le=1.0)
    depth: int  # signed: negative=prereq (up), 0=center, positive=unlock (down)
    direction: Literal["prereq", "center", "unlock"]


class NeighborhoodEdge(BaseModel):
    """A prerequisite edge: ``source`` (prereq) -> ``target`` (dependent)."""
    source: UUID
    target: UUID
    relationship_type: str
    strength: float


class NeighborhoodResponse(BaseModel):
    """Focused neighborhood around a concept (prereqs up + dependents down)."""
    center_id: UUID
    depth: int
    nodes: list[NeighborhoodNode]
    edges: list[NeighborhoodEdge]
    truncated: bool
```

In `apps/api/src/services/mastery_gate.py`, add the imports to the existing schema import block:

```python
from src.schemas.mastery_gate import (
    NeighborhoodEdge,
    NeighborhoodNode,
    NeighborhoodResponse,
)
```

Add the method to `MasteryGateService`:

```python
    async def get_neighborhood(
        self,
        user_id: UUID,
        concept_id: UUID,
        depth: int = 2,
    ) -> NeighborhoodResponse:
        """
        Build a focused prerequisite neighborhood around a concept.

        BFS upstream (prerequisites) and downstream (dependents) up to ``depth``
        hops each, dedups nodes (smallest absolute depth wins; center wins),
        and joins per-node lock status. Applies an absolute safety ceiling.
        """
        center = await self.concept_repository.get_by_id(concept_id)
        if center is None:
            raise ValueError(f"Concept {concept_id} not found")

        # node_id -> (concept, signed_depth, direction)
        discovered: dict[UUID, tuple[object, int, str]] = {
            concept_id: (center, 0, "center")
        }
        edges: dict[tuple[UUID, UUID], NeighborhoodEdge] = {}

        # Upstream: prerequisites (edge prereq -> current)
        frontier = [concept_id]
        for d in range(1, depth + 1):
            nxt: list[UUID] = []
            for cid in frontier:
                for prereq, strength, rel in (
                    await self.concept_repository.get_prerequisites_with_strength(cid)
                ):
                    edges[(prereq.id, cid)] = NeighborhoodEdge(
                        source=prereq.id, target=cid,
                        relationship_type=rel, strength=strength)
                    if prereq.id not in discovered:
                        discovered[prereq.id] = (prereq, -d, "prereq")
                        nxt.append(prereq.id)
            frontier = nxt

        # Downstream: dependents (edge current -> dependent)
        frontier = [concept_id]
        for d in range(1, depth + 1):
            nxt = []
            for cid in frontier:
                for dep, strength, rel in (
                    await self.concept_repository.get_dependents_with_strength(cid)
                ):
                    edges[(cid, dep.id)] = NeighborhoodEdge(
                        source=cid, target=dep.id,
                        relationship_type=rel, strength=strength)
                    if dep.id not in discovered:
                        discovered[dep.id] = (dep, d, "unlock")
                        nxt.append(dep.id)
            frontier = nxt

        # Safety ceiling: keep center + nearest by absolute depth.
        truncated = False
        kept_ids = set(discovered)
        if len(discovered) > self.config.max_neighborhood_nodes:
            truncated = True
            ordered = sorted(discovered.items(), key=lambda kv: abs(kv[1][1]))
            kept_ids = {cid for cid, _ in ordered[: self.config.max_neighborhood_nodes]}
            logger.warning(
                "neighborhood_truncated",
                concept_id=str(concept_id),
                discovered=len(discovered),
                ceiling=self.config.max_neighborhood_nodes,
            )

        # Join lock status per kept node.
        nodes: list[NeighborhoodNode] = []
        for cid in kept_ids:
            concept, signed_depth, direction = discovered[cid]
            gate = await self.check_prerequisites_mastered(user_id, cid)
            nodes.append(NeighborhoodNode(
                concept_id=cid,
                name=concept.name,
                knowledge_area_id=concept.knowledge_area_id,
                difficulty=concept.difficulty_estimate,
                is_unlocked=gate.is_unlocked,
                mastery_progress=gate.mastery_progress,
                depth=signed_depth,
                direction=direction,
            ))

        kept_edges = [
            e for (s, t), e in edges.items() if s in kept_ids and t in kept_ids
        ]
        return NeighborhoodResponse(
            center_id=concept_id, depth=depth,
            nodes=nodes, edges=kept_edges, truncated=truncated)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd apps/api && pytest tests/unit/services/test_mastery_gate.py::TestGetNeighborhood -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add apps/api/src/schemas/mastery_gate.py apps/api/src/services/mastery_gate.py apps/api/tests/unit/services/test_mastery_gate.py
git commit -m "feat(#15): neighborhood schemas + MasteryGateService.get_neighborhood"
```

---

## Task 3: Route — `GET /{concept_id}/neighborhood`

**Files:**
- Modify: `apps/api/src/routes/prerequisites.py`
- Test: `apps/api/tests/integration/test_prerequisite_navigation_api.py`

**Interfaces:**
- Consumes: `MasteryGateService.get_neighborhood` (Task 2); existing `get_mastery_gate_service`, `get_current_user` deps.
- Produces: `GET /concepts/{concept_id}/neighborhood?depth=2` → `NeighborhoodResponse` (200); `404` if concept missing; `depth` clamped 1–3.

- [ ] **Step 1: Write the failing test**

Add to `apps/api/tests/integration/test_prerequisite_navigation_api.py` (the file already has `authenticated_client`/`test_user`/`test_concepts` style fixtures — match the names used by existing tests in that file):

```python
class TestNeighborhoodEndpoint:
    @pytest.mark.asyncio
    async def test_returns_neighborhood_for_known_concept(
        self, authenticated_client, test_concepts
    ):
        # test_concepts creates concepts with prerequisite links; pick one with edges.
        center = test_concepts[1]
        resp = await authenticated_client.get(
            f"/concepts/{center.id}/neighborhood?depth=2")
        assert resp.status_code == 200
        body = resp.json()
        assert body["center_id"] == str(center.id)
        assert any(n["concept_id"] == str(center.id) and n["direction"] == "center"
                   for n in body["nodes"])
        assert body["truncated"] is False

    @pytest.mark.asyncio
    async def test_404_for_unknown_concept(self, authenticated_client):
        from uuid import uuid4
        resp = await authenticated_client.get(f"/concepts/{uuid4()}/neighborhood")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_depth_out_of_range_is_rejected(
        self, authenticated_client, test_concepts
    ):
        resp = await authenticated_client.get(
            f"/concepts/{test_concepts[0].id}/neighborhood?depth=9")
        assert resp.status_code == 422  # FastAPI Query(le=3) validation

    @pytest.mark.asyncio
    async def test_requires_auth(self, client, test_concepts):
        resp = await client.get(f"/concepts/{test_concepts[0].id}/neighborhood")
        assert resp.status_code == 401
```

> If the file's unauthenticated client fixture has a different name than `client`, use that file's existing convention (grep the file for how other endpoints test the 401 case).

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/api && pytest tests/integration/test_prerequisite_navigation_api.py::TestNeighborhoodEndpoint -v`
Expected: FAIL — 404/route-not-found for `/neighborhood` (endpoint doesn't exist yet)

- [ ] **Step 3: Write minimal implementation**

In `apps/api/src/routes/prerequisites.py`, add `HTTPException` to the fastapi import and `NeighborhoodResponse` to the schema import, then add the route (place after `get_prerequisite_status`):

```python
from fastapi import APIRouter, Depends, HTTPException, Query
```

```python
from src.schemas.mastery_gate import (
    BulkUnlockStatusResponse,
    GateCheckResult,
    NeighborhoodResponse,
    OverrideAttemptResponse,
    RecentUnlocksResponse,
)
```

```python
@router.get(
    "/{concept_id}/neighborhood",
    response_model=NeighborhoodResponse,
    summary="Get a concept's prerequisite neighborhood",
    description="""
    Return a focused neighborhood around a concept: prerequisites (upstream)
    and dependents (downstream), up to `depth` hops each direction, joined with
    the current user's per-concept lock status. Powers the interactive
    prerequisite graph (Story 4.11, Slice D).
    """,
)
async def get_concept_neighborhood(
    concept_id: UUID,
    depth: int = Query(2, ge=1, le=3, description="Hops in each direction"),
    current_user: User = Depends(get_current_user),
    service: MasteryGateService = Depends(get_mastery_gate_service),
) -> NeighborhoodResponse:
    """Return the prerequisite/dependent neighborhood for a concept."""
    logger.info(
        "neighborhood_requested",
        user_id=str(current_user.id),
        concept_id=str(concept_id),
        depth=depth,
    )
    try:
        return await service.get_neighborhood(
            user_id=current_user.id, concept_id=concept_id, depth=depth
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="Concept not found")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd apps/api && pytest tests/integration/test_prerequisite_navigation_api.py::TestNeighborhoodEndpoint -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add apps/api/src/routes/prerequisites.py apps/api/tests/integration/test_prerequisite_navigation_api.py
git commit -m "feat(#15): GET /concepts/{id}/neighborhood endpoint"
```

---

## Task 4: Frontend service — `getNeighborhood`

**Files:**
- Modify: `apps/web/src/services/prerequisiteService.ts`
- Create: `apps/web/src/test/mocks/handlers/neighborhoodHandlers.ts`
- Modify: `apps/web/src/test/mocks/server.ts` (register handlers if it composes a default set — otherwise tests pass handlers via `server.use`)
- Test: `apps/web/src/test/services/prerequisiteService.test.ts` (create)

**Interfaces:**
- Produces:
  - TS `NeighborhoodNode { concept_id: string; name: string; knowledge_area_id: string; difficulty: number; is_unlocked: boolean; mastery_progress: number; depth: number; direction: 'prereq' | 'center' | 'unlock' }`
  - `NeighborhoodEdge { source: string; target: string; relationship_type: string; strength: number }`
  - `NeighborhoodResponse { center_id: string; depth: number; nodes: NeighborhoodNode[]; edges: NeighborhoodEdge[]; truncated: boolean }`
  - `prerequisiteService.getNeighborhood(conceptId: string, depth?: number): Promise<NeighborhoodResponse>` → `GET /concepts/{id}/neighborhood?depth=`

- [ ] **Step 1: Write the failing test**

Create `apps/web/src/test/mocks/handlers/neighborhoodHandlers.ts`:

```typescript
import { http, HttpResponse } from 'msw'

export const neighborhoodFixture = {
  center_id: 'center-1',
  depth: 2,
  truncated: false,
  nodes: [
    { concept_id: 'center-1', name: 'Center', knowledge_area_id: 'ka-1', difficulty: 0.5, is_unlocked: true, mastery_progress: 1, depth: 0, direction: 'center' as const },
    { concept_id: 'p-1', name: 'Prereq', knowledge_area_id: 'ka-1', difficulty: 0.4, is_unlocked: false, mastery_progress: 0.3, depth: -1, direction: 'prereq' as const },
  ],
  edges: [{ source: 'p-1', target: 'center-1', relationship_type: 'required', strength: 0.8 }],
}

export const neighborhoodHandlers = [
  http.get('*/concepts/:id/neighborhood', () => HttpResponse.json(neighborhoodFixture)),
]
```

Create `apps/web/src/test/services/prerequisiteService.test.ts`:

```typescript
import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest'
import { prerequisiteService } from '../../services/prerequisiteService'
import { server } from '../mocks/server'
import { neighborhoodHandlers, neighborhoodFixture } from '../mocks/handlers/neighborhoodHandlers'

describe('prerequisiteService.getNeighborhood', () => {
  beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
  afterEach(() => server.resetHandlers())
  afterAll(() => server.close())

  it('GETs the neighborhood and returns the parsed body', async () => {
    server.use(...neighborhoodHandlers)
    const result = await prerequisiteService.getNeighborhood('center-1', 2)
    expect(result.center_id).toBe(neighborhoodFixture.center_id)
    expect(result.nodes).toHaveLength(2)
    expect(result.edges[0].source).toBe('p-1')
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/web && npx vitest run src/test/services/prerequisiteService.test.ts`
Expected: FAIL — `prerequisiteService.getNeighborhood is not a function`

- [ ] **Step 3: Write minimal implementation**

In `apps/web/src/services/prerequisiteService.ts`, add the types before the `prerequisiteService` object:

```typescript
/** One concept in a focused prerequisite neighborhood. Story 4.11 Slice D. */
export interface NeighborhoodNode {
  concept_id: string
  name: string
  knowledge_area_id: string
  difficulty: number
  is_unlocked: boolean
  mastery_progress: number
  depth: number // negative=prereq, 0=center, positive=unlock
  direction: 'prereq' | 'center' | 'unlock'
}

/** A prerequisite edge: source (prereq) -> target (dependent). */
export interface NeighborhoodEdge {
  source: string
  target: string
  relationship_type: string
  strength: number
}

/** Focused neighborhood around a concept. Mirrors backend `NeighborhoodResponse`. */
export interface NeighborhoodResponse {
  center_id: string
  depth: number
  nodes: NeighborhoodNode[]
  edges: NeighborhoodEdge[]
  truncated: boolean
}
```

Add the method inside the `prerequisiteService` object (after `getBulkUnlockStatus`):

```typescript
  /**
   * Get a concept's prerequisite neighborhood (prereqs up + dependents down).
   * @param conceptId - Concept UUID
   * @param depth - Hops in each direction (1-3, default 2)
   */
  async getNeighborhood(
    conceptId: string,
    depth = 2
  ): Promise<NeighborhoodResponse> {
    const response = await api.get<NeighborhoodResponse>(
      `/concepts/${conceptId}/neighborhood`,
      { params: { depth } }
    )
    return response.data
  },
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd apps/web && npx vitest run src/test/services/prerequisiteService.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/services/prerequisiteService.ts apps/web/src/test/services/prerequisiteService.test.ts apps/web/src/test/mocks/handlers/neighborhoodHandlers.ts
git commit -m "feat(#15): prerequisiteService.getNeighborhood + types"
```

---

## Task 5: Extract `useConceptPractice` and refactor `ConceptRow`

**Files:**
- Create: `apps/web/src/hooks/useConceptPractice.ts`
- Modify: `apps/web/src/components/curriculum/ConceptRow.tsx`
- Test: `apps/web/src/hooks/__tests__/useConceptPractice.test.tsx` (create)

**Interfaces:**
- Consumes: `useAttemptLockedConcept` (existing), `buildFocusQuizUrl` (existing), `react-router-dom` `useNavigate`.
- Produces: `useConceptPractice({ conceptId: string; conceptName: string; isUnlocked: boolean }) => { showDialog: boolean; isSubmitting: boolean; isError: boolean; handlePractice: () => void; confirm: () => Promise<void>; cancel: () => void }`

- [ ] **Step 1: Write the failing test**

Create `apps/web/src/hooks/__tests__/useConceptPractice.test.tsx`:

```tsx
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { useConceptPractice } from '../useConceptPractice'

const navigate = vi.fn()
vi.mock('react-router-dom', async (orig) => ({
  ...(await orig<typeof import('react-router-dom')>()),
  useNavigate: () => navigate,
}))
const mutateAsync = vi.fn().mockResolvedValue({})
vi.mock('../useConceptLockStatus', () => ({
  useAttemptLockedConcept: () => ({ mutateAsync, isPending: false, isError: false }),
}))

function wrap() {
  const client = new QueryClient()
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={client}><MemoryRouter>{children}</MemoryRouter></QueryClientProvider>
  )
}

describe('useConceptPractice', () => {
  beforeEach(() => vi.clearAllMocks())

  it('navigates immediately when unlocked', () => {
    const { result } = renderHook(
      () => useConceptPractice({ conceptId: 'c1', conceptName: 'C', isUnlocked: true }),
      { wrapper: wrap() })
    act(() => result.current.handlePractice())
    expect(navigate).toHaveBeenCalledWith(expect.stringContaining('c1'))
    expect(result.current.showDialog).toBe(false)
  })

  it('opens the dialog when locked, then confirms + launches', async () => {
    const { result } = renderHook(
      () => useConceptPractice({ conceptId: 'c2', conceptName: 'C', isUnlocked: false }),
      { wrapper: wrap() })
    act(() => result.current.handlePractice())
    expect(result.current.showDialog).toBe(true)
    expect(navigate).not.toHaveBeenCalled()
    await act(async () => { await result.current.confirm() })
    expect(mutateAsync).toHaveBeenCalledWith('c2')
    await waitFor(() => expect(navigate).toHaveBeenCalledWith(expect.stringContaining('c2')))
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/web && npx vitest run src/hooks/__tests__/useConceptPractice.test.tsx`
Expected: FAIL — cannot find module `../useConceptPractice`

- [ ] **Step 3: Write minimal implementation**

Create `apps/web/src/hooks/useConceptPractice.ts`:

```typescript
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAttemptLockedConcept } from './useConceptLockStatus'
import { buildFocusQuizUrl } from '../utils/curriculum'

interface UseConceptPracticeArgs {
  conceptId: string
  conceptName: string
  isUnlocked: boolean
}

/**
 * Encapsulates the "Practice this concept" flow shared by the curriculum list
 * and the prerequisite graph: launch directly when unlocked, otherwise open a
 * soft-gate confirm that logs the override before launching. Story 4.11.
 */
export function useConceptPractice({
  conceptId,
  conceptName,
  isUnlocked,
}: UseConceptPracticeArgs) {
  const navigate = useNavigate()
  const [showDialog, setShowDialog] = useState(false)
  const attemptLocked = useAttemptLockedConcept()

  const launch = () => navigate(buildFocusQuizUrl(conceptId, conceptName))

  const handlePractice = () => {
    if (isUnlocked) launch()
    else setShowDialog(true)
  }

  const confirm = async () => {
    try {
      await attemptLocked.mutateAsync(conceptId)
      setShowDialog(false)
      launch()
    } catch {
      // Keep the dialog open on failure; mutation error surfaced via isError.
    }
  }

  const cancel = () => setShowDialog(false)

  return {
    showDialog,
    isSubmitting: attemptLocked.isPending,
    isError: attemptLocked.isError,
    handlePractice,
    confirm,
    cancel,
  }
}
```

Refactor `apps/web/src/components/curriculum/ConceptRow.tsx` to use it — replace the local `navigate`/`showDialog`/`attemptLocked`/`launch`/`handlePractice`/`handleConfirm` (lines 19–52) with:

```tsx
  const [showDetail, setShowDetail] = useState(false)
  const practice = useConceptPractice({
    conceptId: concept.concept_id,
    conceptName: concept.concept_name,
    isUnlocked: concept.is_unlocked,
  })

  const status = useConceptLockStatus(showDetail && !concept.is_unlocked ? concept.concept_id : null)
  const blockers = (status.data?.blocking_prerequisites ?? []).map((b) => ({
    concept_id: b.concept_id,
    name: b.name,
  }))
  const closestName = status.data?.closest_to_unlock?.name ?? null
```

Update imports (remove `useNavigate`, `useAttemptLockedConcept`, `buildFocusQuizUrl`; add the hook):

```tsx
import { useState } from 'react'
import type { ConceptUnlockStatus } from '../../services/prerequisiteService'
import { useConceptLockStatus } from '../../hooks/useConceptLockStatus'
import { useConceptPractice } from '../../hooks/useConceptPractice'
import { ConceptLockBadge } from './ConceptLockBadge'
import { ConceptLockTooltip } from './ConceptLockTooltip'
import { LockedConceptConfirmDialog } from './LockedConceptConfirmDialog'
```

Update the button + dialog JSX to use `practice.*`:

```tsx
        <button
          type="button"
          onClick={practice.handlePractice}
          aria-describedby={showTooltip ? tooltipId : undefined}
          className="shrink-0 px-3 py-1.5 text-sm font-medium text-primary-700 rounded-[14px] border border-primary-200 hover:bg-primary-50"
        >
          Practice
        </button>
```

```tsx
      {practice.showDialog && (
        <LockedConceptConfirmDialog
          conceptName={concept.concept_name}
          blockingPrerequisites={blockers}
          isSubmitting={practice.isSubmitting}
          isError={practice.isError}
          onConfirm={practice.confirm}
          onCancel={practice.cancel}
        />
      )}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd apps/web && npx vitest run src/hooks/__tests__/useConceptPractice.test.tsx src/components/curriculum/__tests__`
Expected: PASS (hook tests + existing ConceptRow tests still green)

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/hooks/useConceptPractice.ts apps/web/src/hooks/__tests__/useConceptPractice.test.tsx apps/web/src/components/curriculum/ConceptRow.tsx
git commit -m "refactor(#15): extract useConceptPractice hook, reuse in ConceptRow"
```

---

## Task 6: Clustering util — `graphClustering.ts`

**Files:**
- Create: `apps/web/src/utils/graphClustering.ts`
- Test: `apps/web/src/utils/__tests__/graphClustering.test.ts` (create)

**Interfaces:**
- Consumes: `NeighborhoodResponse`, `NeighborhoodNode` (Task 4).
- Produces:
  - `CLUSTER_THRESHOLD = 6`
  - `ConceptNodeData { kind: 'concept'; node: NeighborhoodNode }`
  - `ClusterNodeData { kind: 'cluster'; parentId: string; direction: 'prereq' | 'unlock'; hiddenCount: number; hiddenIds: string[] }`
  - `VisibleNode { id: string; data: ConceptNodeData | ClusterNodeData }`
  - `VisibleEdge { id: string; source: string; target: string }`
  - `clusterNeighborhood(neighborhood: NeighborhoodResponse, expanded: Set<string>) => { nodes: VisibleNode[]; edges: VisibleEdge[] }`

Clustering rule: each non-center node has exactly one tree edge (BFS edges from the backend). For each (parent, direction) group, sort children by edge `strength` desc then `mastery_progress` desc; if the group exceeds `CLUSTER_THRESHOLD` and the cluster is **not** expanded, render the top `CLUSTER_THRESHOLD` children plus one cluster node for the overflow; otherwise render all children. Cluster id is `cluster:{parentId}:{direction}`.

- [ ] **Step 1: Write the failing test**

Create `apps/web/src/utils/__tests__/graphClustering.test.ts`:

```typescript
import { describe, it, expect } from 'vitest'
import { clusterNeighborhood, CLUSTER_THRESHOLD } from '../graphClustering'
import type { NeighborhoodResponse } from '../../services/prerequisiteService'

function makeHub(prereqCount: number): NeighborhoodResponse {
  const nodes = [
    { concept_id: 'c', name: 'C', knowledge_area_id: 'ka', difficulty: 0.5, is_unlocked: true, mastery_progress: 1, depth: 0, direction: 'center' as const },
  ]
  const edges = []
  for (let i = 0; i < prereqCount; i++) {
    nodes.push({ concept_id: `p${i}`, name: `P${i}`, knowledge_area_id: 'ka', difficulty: 0.4, is_unlocked: false, mastery_progress: i / prereqCount, depth: -1, direction: 'prereq' as const })
    edges.push({ source: `p${i}`, target: 'c', relationship_type: 'required', strength: i / prereqCount })
  }
  return { center_id: 'c', depth: 2, truncated: false, nodes, edges }
}

describe('clusterNeighborhood', () => {
  it('shows all children when at or under the threshold', () => {
    const { nodes } = clusterNeighborhood(makeHub(CLUSTER_THRESHOLD), new Set())
    expect(nodes.filter((n) => n.data.kind === 'cluster')).toHaveLength(0)
    expect(nodes).toHaveLength(CLUSTER_THRESHOLD + 1) // + center
  })

  it('collapses overflow into one cluster node', () => {
    const { nodes, edges } = clusterNeighborhood(makeHub(CLUSTER_THRESHOLD + 5), new Set())
    const clusters = nodes.filter((n) => n.data.kind === 'cluster')
    expect(clusters).toHaveLength(1)
    expect((clusters[0].data as { hiddenCount: number }).hiddenCount).toBe(5)
    // top-K concept children + 1 cluster + center
    expect(nodes.filter((n) => n.data.kind === 'concept')).toHaveLength(CLUSTER_THRESHOLD + 1)
    // cluster has an edge to its parent
    expect(edges.some((e) => e.target === 'c' && e.source.startsWith('cluster:'))).toBe(true)
  })

  it('expands a cluster when its id is in the expanded set', () => {
    const hub = makeHub(CLUSTER_THRESHOLD + 5)
    const clusterId = `cluster:c:prereq`
    const { nodes } = clusterNeighborhood(hub, new Set([clusterId]))
    expect(nodes.filter((n) => n.data.kind === 'cluster')).toHaveLength(0)
    expect(nodes.filter((n) => n.data.kind === 'concept')).toHaveLength(CLUSTER_THRESHOLD + 5 + 1)
  })

  it('keeps top children ranked by strength desc', () => {
    const { nodes } = clusterNeighborhood(makeHub(CLUSTER_THRESHOLD + 3), new Set())
    const shown = nodes.filter((n) => n.data.kind === 'concept' && n.id !== 'c')
      .map((n) => (n.data as { node: { concept_id: string } }).node.concept_id)
    // highest-index prereqs have highest strength; the lowest-strength ones get hidden
    expect(shown).not.toContain('p0')
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/web && npx vitest run src/utils/__tests__/graphClustering.test.ts`
Expected: FAIL — cannot find module `../graphClustering`

- [ ] **Step 3: Write minimal implementation**

Create `apps/web/src/utils/graphClustering.ts`:

```typescript
import type {
  NeighborhoodNode,
  NeighborhoodResponse,
} from '../services/prerequisiteService'

/** Max children shown per (parent, direction) before overflow is collapsed. */
export const CLUSTER_THRESHOLD = 6

export interface ConceptNodeData {
  kind: 'concept'
  node: NeighborhoodNode
}

export interface ClusterNodeData {
  kind: 'cluster'
  parentId: string
  direction: 'prereq' | 'unlock'
  hiddenCount: number
  hiddenIds: string[]
}

export interface VisibleNode {
  id: string
  data: ConceptNodeData | ClusterNodeData
}

export interface VisibleEdge {
  id: string
  source: string
  target: string
}

interface Child {
  node: NeighborhoodNode
  strength: number
  edge: { source: string; target: string }
}

/**
 * Transform a neighborhood into render-ready nodes/edges, collapsing dense
 * (parent, direction) groups into expandable cluster nodes. Pure. Story 4.11 D.
 */
export function clusterNeighborhood(
  neighborhood: NeighborhoodResponse,
  expanded: Set<string>
): { nodes: VisibleNode[]; edges: VisibleEdge[] } {
  const byId = new Map(neighborhood.nodes.map((n) => [n.concept_id, n]))

  // Group children by (parentId, direction). The child is the endpoint with the
  // larger absolute depth; the parent is the more-central endpoint.
  const groups = new Map<string, Child[]>()
  for (const edge of neighborhood.edges) {
    const a = byId.get(edge.source)
    const b = byId.get(edge.target)
    if (!a || !b) continue
    const childNode = Math.abs(a.depth) >= Math.abs(b.depth) ? a : b
    const parentNode = childNode === a ? b : a
    const direction = childNode.direction === 'unlock' ? 'unlock' : 'prereq'
    const key = `${parentNode.concept_id}:${direction}`
    const list = groups.get(key) ?? []
    list.push({ node: childNode, strength: edge.strength, edge })
    groups.set(key, list)
  }

  const nodes: VisibleNode[] = []
  const edges: VisibleEdge[] = []

  // Always include the center node.
  const center = neighborhood.nodes.find((n) => n.direction === 'center')
  if (center) {
    nodes.push({ id: center.concept_id, data: { kind: 'concept', node: center } })
  }

  for (const [key, childrenRaw] of groups) {
    const [parentId, direction] = key.split(':') as [string, 'prereq' | 'unlock']
    const children = [...childrenRaw].sort(
      (x, y) =>
        y.strength - x.strength ||
        y.node.mastery_progress - x.node.mastery_progress
    )
    const clusterId = `cluster:${parentId}:${direction}`
    const isExpanded = expanded.has(clusterId)
    const overflow = children.length > CLUSTER_THRESHOLD && !isExpanded
    const shown = overflow ? children.slice(0, CLUSTER_THRESHOLD) : children
    const hidden = overflow ? children.slice(CLUSTER_THRESHOLD) : []

    for (const child of shown) {
      nodes.push({
        id: child.node.concept_id,
        data: { kind: 'concept', node: child.node },
      })
      edges.push({
        id: `${child.edge.source}->${child.edge.target}`,
        source: child.edge.source,
        target: child.edge.target,
      })
    }

    if (hidden.length > 0) {
      nodes.push({
        id: clusterId,
        data: {
          kind: 'cluster',
          parentId,
          direction,
          hiddenCount: hidden.length,
          hiddenIds: hidden.map((h) => h.node.concept_id),
        },
      })
      // Edge orientation matches the direction: prereqs point up to the parent,
      // unlocks point down from the parent.
      edges.push(
        direction === 'prereq'
          ? { id: `${clusterId}->${parentId}`, source: clusterId, target: parentId }
          : { id: `${parentId}->${clusterId}`, source: parentId, target: clusterId }
      )
    }
  }

  return { nodes, edges }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd apps/web && npx vitest run src/utils/__tests__/graphClustering.test.ts`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/utils/graphClustering.ts apps/web/src/utils/__tests__/graphClustering.test.ts
git commit -m "feat(#15): graphClustering util with expandable hub clusters"
```

---

## Task 7: Layout util — `graphLayout.ts` (+ install dagre)

**Files:**
- Modify: `apps/web/package.json` (add `dagre`, dev `@types/dagre`)
- Create: `apps/web/src/utils/graphLayout.ts`
- Test: `apps/web/src/utils/__tests__/graphLayout.test.ts` (create)

**Interfaces:**
- Consumes: `VisibleNode`, `VisibleEdge` (Task 6).
- Produces: `PositionedNode = VisibleNode & { position: { x: number; y: number } }`; `layoutGraph(nodes: VisibleNode[], edges: VisibleEdge[]): PositionedNode[]`.

- [ ] **Step 1: Install dependencies**

Run: `cd apps/web && npm install dagre && npm install -D @types/dagre`

- [ ] **Step 2: Write the failing test**

Create `apps/web/src/utils/__tests__/graphLayout.test.ts`:

```typescript
import { describe, it, expect } from 'vitest'
import { layoutGraph } from '../graphLayout'
import type { VisibleNode, VisibleEdge } from '../graphClustering'

const center: VisibleNode = { id: 'c', data: { kind: 'concept', node: { concept_id: 'c', name: 'C', knowledge_area_id: 'ka', difficulty: 0.5, is_unlocked: true, mastery_progress: 1, depth: 0, direction: 'center' } } }
const prereq: VisibleNode = { id: 'p', data: { kind: 'concept', node: { concept_id: 'p', name: 'P', knowledge_area_id: 'ka', difficulty: 0.4, is_unlocked: false, mastery_progress: 0.3, depth: -1, direction: 'prereq' } } }
const edges: VisibleEdge[] = [{ id: 'p->c', source: 'p', target: 'c' }]

describe('layoutGraph', () => {
  it('assigns a numeric position to every node', () => {
    const positioned = layoutGraph([center, prereq], edges)
    expect(positioned).toHaveLength(2)
    for (const n of positioned) {
      expect(typeof n.position.x).toBe('number')
      expect(typeof n.position.y).toBe('number')
    }
  })

  it('places the prerequisite below the concept it unlocks (bottom-up rank)', () => {
    const positioned = layoutGraph([center, prereq], edges)
    const c = positioned.find((n) => n.id === 'c')!
    const p = positioned.find((n) => n.id === 'p')!
    expect(p.position.y).toBeGreaterThan(c.position.y) // larger y = lower on screen
  })
})
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd apps/web && npx vitest run src/utils/__tests__/graphLayout.test.ts`
Expected: FAIL — cannot find module `../graphLayout`

- [ ] **Step 4: Write minimal implementation**

Create `apps/web/src/utils/graphLayout.ts`:

```typescript
import dagre from 'dagre'
import type { VisibleEdge, VisibleNode } from './graphClustering'

export type PositionedNode = VisibleNode & {
  position: { x: number; y: number }
}

const NODE_WIDTH = 200
const NODE_HEIGHT = 84

/**
 * Lay out the neighborhood top-to-bottom with prerequisites below the concepts
 * they unlock (rankdir 'BT' so arrows read upward). Pure. Story 4.11 Slice D.
 */
export function layoutGraph(
  nodes: VisibleNode[],
  edges: VisibleEdge[]
): PositionedNode[] {
  const g = new dagre.graphlib.Graph()
  g.setGraph({ rankdir: 'BT', nodesep: 48, ranksep: 96 })
  g.setDefaultEdgeLabel(() => ({}))

  for (const node of nodes) {
    g.setNode(node.id, { width: NODE_WIDTH, height: NODE_HEIGHT })
  }
  for (const edge of edges) {
    g.setEdge(edge.source, edge.target)
  }

  dagre.layout(g)

  return nodes.map((node) => {
    const { x, y } = g.node(node.id)
    return {
      ...node,
      position: { x: x - NODE_WIDTH / 2, y: y - NODE_HEIGHT / 2 },
    }
  })
}
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd apps/web && npx vitest run src/utils/__tests__/graphLayout.test.ts`
Expected: PASS (2 passed)

- [ ] **Step 6: Commit**

```bash
git add apps/web/package.json apps/web/package-lock.json apps/web/src/utils/graphLayout.ts apps/web/src/utils/__tests__/graphLayout.test.ts
git commit -m "feat(#15): dagre graphLayout util (+ dagre dep)"
```

---

## Task 8: Custom node — `ConceptGraphNode.tsx` (+ install @xyflow/react)

**Files:**
- Modify: `apps/web/package.json` (add `@xyflow/react`)
- Create: `apps/web/src/components/curriculum/ConceptGraphNode.tsx`
- Test: `apps/web/src/components/curriculum/__tests__/ConceptGraphNode.test.tsx` (create)

**Interfaces:**
- Consumes: `ConceptLockBadge` (existing), `useConceptPractice` (Task 5), `LockedConceptConfirmDialog` (existing), `@xyflow/react` `Handle`/`Position`/`NodeProps`, `ConceptNodeData`/`ClusterNodeData` (Task 6).
- Produces: `GraphNodeData` union (the `data` payload React Flow passes) and default-exported `ConceptGraphNode` component registered under node type `graphNode`:

```typescript
export type GraphNodeData =
  | { kind: 'concept'; node: NeighborhoodNode; kaColor: string; isCenter: boolean; onRecenter: (conceptId: string) => void }
  | { kind: 'cluster'; direction: 'prereq' | 'unlock'; hiddenCount: number; onExpand: () => void }
```

- [ ] **Step 1: Install dependency**

Run: `cd apps/web && npm install @xyflow/react`

- [ ] **Step 2: Write the failing test**

Create `apps/web/src/components/curriculum/__tests__/ConceptGraphNode.test.tsx`:

```tsx
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import ConceptGraphNode, { type GraphNodeData } from '../ConceptGraphNode'

// React Flow Handle needs a provider/DOM; stub the bits we use.
vi.mock('@xyflow/react', () => ({
  Handle: () => null,
  Position: { Top: 'top', Bottom: 'bottom' },
}))

function renderNode(data: GraphNodeData) {
  const client = new QueryClient()
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        {/* React Flow calls the node with { data }; emulate that. */}
        <ConceptGraphNode data={data} />
      </MemoryRouter>
    </QueryClientProvider>
  )
}

const conceptNode = {
  concept_id: 'p1', name: 'Stakeholder Analysis', knowledge_area_id: 'ka-1',
  difficulty: 0.5, is_unlocked: false, mastery_progress: 0.3, depth: -1, direction: 'prereq' as const,
}

describe('ConceptGraphNode', () => {
  beforeEach(() => vi.clearAllMocks())

  it('renders a concept node with name and re-centers on click', () => {
    const onRecenter = vi.fn()
    renderNode({ kind: 'concept', node: conceptNode, kaColor: '#3b82f6', isCenter: false, onRecenter })
    expect(screen.getByText('Stakeholder Analysis')).toBeInTheDocument()
    fireEvent.click(screen.getByText('Stakeholder Analysis'))
    expect(onRecenter).toHaveBeenCalledWith('p1')
  })

  it('does not re-center when the node is the center', () => {
    const onRecenter = vi.fn()
    renderNode({ kind: 'concept', node: { ...conceptNode, direction: 'center', depth: 0 }, kaColor: '#3b82f6', isCenter: true, onRecenter })
    fireEvent.click(screen.getByText('Stakeholder Analysis'))
    expect(onRecenter).not.toHaveBeenCalled()
  })

  it('renders a cluster node and calls onExpand', () => {
    const onExpand = vi.fn()
    renderNode({ kind: 'cluster', direction: 'prereq', hiddenCount: 7, onExpand })
    const btn = screen.getByRole('button', { name: /7 more prerequisites/i })
    fireEvent.click(btn)
    expect(onExpand).toHaveBeenCalled()
  })
})
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd apps/web && npx vitest run src/components/curriculum/__tests__/ConceptGraphNode.test.tsx`
Expected: FAIL — cannot find module `../ConceptGraphNode`

- [ ] **Step 4: Write minimal implementation**

Create `apps/web/src/components/curriculum/ConceptGraphNode.tsx`:

```tsx
import { Handle, Position } from '@xyflow/react'
import type { NeighborhoodNode } from '../../services/prerequisiteService'
import { useConceptPractice } from '../../hooks/useConceptPractice'
import { ConceptLockBadge } from './ConceptLockBadge'
import { LockedConceptConfirmDialog } from './LockedConceptConfirmDialog'

export type GraphNodeData =
  | {
      kind: 'concept'
      node: NeighborhoodNode
      kaColor: string
      isCenter: boolean
      onRecenter: (conceptId: string) => void
    }
  | {
      kind: 'cluster'
      direction: 'prereq' | 'unlock'
      hiddenCount: number
      onExpand: () => void
    }

const DIRECTION_LABEL = { prereq: 'prerequisites', unlock: 'unlocks' } as const

/** A React Flow custom node: either a concept card or an expandable cluster. */
export default function ConceptGraphNode({ data }: { data: GraphNodeData }) {
  if (data.kind === 'cluster') {
    return (
      <>
        <Handle type="target" position={Position.Top} />
        <button
          type="button"
          onClick={data.onExpand}
          aria-expanded={false}
          className="rounded-[14px] border border-dashed border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-600 hover:bg-gray-50"
        >
          +{data.hiddenCount} more {DIRECTION_LABEL[data.direction]} ▸
        </button>
        <Handle type="source" position={Position.Bottom} />
      </>
    )
  }

  const { node, kaColor, isCenter, onRecenter } = data
  return <ConceptCard node={node} kaColor={kaColor} isCenter={isCenter} onRecenter={onRecenter} />
}

function ConceptCard({
  node,
  kaColor,
  isCenter,
  onRecenter,
}: {
  node: NeighborhoodNode
  kaColor: string
  isCenter: boolean
  onRecenter: (conceptId: string) => void
}) {
  const practice = useConceptPractice({
    conceptId: node.concept_id,
    conceptName: node.name,
    isUnlocked: node.is_unlocked,
  })

  return (
    <div
      onClick={() => { if (!isCenter) onRecenter(node.concept_id) }}
      className={`w-[200px] rounded-[14px] border-l-4 bg-white p-3 shadow-sm ${
        isCenter ? 'ring-2 ring-primary-500' : 'cursor-pointer hover:shadow-md'
      }`}
      style={{ borderLeftColor: kaColor }}
    >
      <Handle type="target" position={Position.Top} />
      <p className="truncate text-sm font-medium text-gray-900">{node.name}</p>
      <div className="mt-1 flex items-center gap-2">
        <ConceptLockBadge isUnlocked={node.is_unlocked} />
        <span className="text-xs text-gray-500">
          {Math.round(node.mastery_progress * 100)}%
        </span>
      </div>
      <button
        type="button"
        onClick={(e) => { e.stopPropagation(); practice.handlePractice() }}
        className="mt-2 w-full rounded-[14px] border border-primary-200 px-2 py-1 text-xs font-medium text-primary-700 hover:bg-primary-50"
      >
        Practice
      </button>
      {practice.showDialog && (
        <LockedConceptConfirmDialog
          conceptName={node.name}
          blockingPrerequisites={[]}
          isSubmitting={practice.isSubmitting}
          isError={practice.isError}
          onConfirm={practice.confirm}
          onCancel={practice.cancel}
        />
      )}
      <Handle type="source" position={Position.Bottom} />
    </div>
  )
}
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd apps/web && npx vitest run src/components/curriculum/__tests__/ConceptGraphNode.test.tsx`
Expected: PASS (3 passed)

- [ ] **Step 6: Commit**

```bash
git add apps/web/package.json apps/web/package-lock.json apps/web/src/components/curriculum/ConceptGraphNode.tsx apps/web/src/components/curriculum/__tests__/ConceptGraphNode.test.tsx
git commit -m "feat(#15): ConceptGraphNode custom node (concept + cluster) + @xyflow/react"
```

---

## Task 9: Graph wrapper — `PrerequisiteGraph.tsx`

**Files:**
- Create: `apps/web/src/components/curriculum/PrerequisiteGraph.tsx`
- Test: `apps/web/src/components/curriculum/__tests__/PrerequisiteGraph.test.tsx` (create)

**Interfaces:**
- Consumes: `clusterNeighborhood` (Task 6), `layoutGraph` (Task 7), `ConceptGraphNode` + `GraphNodeData` (Task 8), `NeighborhoodResponse` (Task 4), `@xyflow/react` `ReactFlow`/`Background`/`Controls`/`MiniMap`.
- Produces:
  - Props `PrerequisiteGraphProps { neighborhood: NeighborhoodResponse; expanded: Set<string>; kaColorMap: Record<string, string>; onRecenter: (conceptId: string) => void; onToggleCluster: (clusterId: string) => void }`
  - default-exported `PrerequisiteGraph`.

- [ ] **Step 1: Write the failing test**

Create `apps/web/src/components/curriculum/__tests__/PrerequisiteGraph.test.tsx`:

```tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import PrerequisiteGraph from '../PrerequisiteGraph'
import type { NeighborhoodResponse } from '../../../services/prerequisiteService'

// Render a lightweight stand-in for the canvas: expose node count + ids.
vi.mock('@xyflow/react', () => ({
  ReactFlow: ({ nodes }: { nodes: Array<{ id: string }> }) => (
    <div data-testid="rf">
      {nodes.map((n) => <span key={n.id} data-testid="rf-node">{n.id}</span>)}
    </div>
  ),
  Background: () => null,
  Controls: () => null,
  MiniMap: () => null,
}))

const neighborhood: NeighborhoodResponse = {
  center_id: 'c', depth: 2, truncated: false,
  nodes: [
    { concept_id: 'c', name: 'C', knowledge_area_id: 'ka-1', difficulty: 0.5, is_unlocked: true, mastery_progress: 1, depth: 0, direction: 'center' },
    { concept_id: 'p', name: 'P', knowledge_area_id: 'ka-1', difficulty: 0.4, is_unlocked: false, mastery_progress: 0.3, depth: -1, direction: 'prereq' },
  ],
  edges: [{ source: 'p', target: 'c', relationship_type: 'required', strength: 0.8 }],
}

describe('PrerequisiteGraph', () => {
  it('renders one React Flow node per visible node', () => {
    render(
      <PrerequisiteGraph
        neighborhood={neighborhood}
        expanded={new Set()}
        kaColorMap={{ 'ka-1': '#3b82f6' }}
        onRecenter={vi.fn()}
        onToggleCluster={vi.fn()}
      />
    )
    expect(screen.getByTestId('rf')).toBeInTheDocument()
    expect(screen.getAllByTestId('rf-node')).toHaveLength(2)
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/web && npx vitest run src/components/curriculum/__tests__/PrerequisiteGraph.test.tsx`
Expected: FAIL — cannot find module `../PrerequisiteGraph`

- [ ] **Step 3: Write minimal implementation**

Create `apps/web/src/components/curriculum/PrerequisiteGraph.tsx`:

```tsx
import { useMemo } from 'react'
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  MarkerType,
  type Node,
  type Edge,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import type { NeighborhoodResponse } from '../../services/prerequisiteService'
import { clusterNeighborhood } from '../../utils/graphClustering'
import { layoutGraph } from '../../utils/graphLayout'
import ConceptGraphNode, { type GraphNodeData } from './ConceptGraphNode'

interface PrerequisiteGraphProps {
  neighborhood: NeighborhoodResponse
  expanded: Set<string>
  kaColorMap: Record<string, string>
  onRecenter: (conceptId: string) => void
  onToggleCluster: (clusterId: string) => void
}

const NODE_TYPES = { graphNode: ConceptGraphNode }
const DEFAULT_KA_COLOR = '#94a3b8'

/** React Flow wrapper: clusters + lays out a neighborhood and renders it. */
export default function PrerequisiteGraph({
  neighborhood,
  expanded,
  kaColorMap,
  onRecenter,
  onToggleCluster,
}: PrerequisiteGraphProps) {
  const { nodes, edges } = useMemo(() => {
    const visible = clusterNeighborhood(neighborhood, expanded)
    const positioned = layoutGraph(visible.nodes, visible.edges)

    const rfNodes: Node<GraphNodeData>[] = positioned.map((n) => {
      if (n.data.kind === 'cluster') {
        return {
          id: n.id,
          type: 'graphNode',
          position: n.position,
          data: {
            kind: 'cluster',
            direction: n.data.direction,
            hiddenCount: n.data.hiddenCount,
            onExpand: () => onToggleCluster(n.id),
          },
        }
      }
      return {
        id: n.id,
        type: 'graphNode',
        position: n.position,
        data: {
          kind: 'concept',
          node: n.data.node,
          kaColor: kaColorMap[n.data.node.knowledge_area_id] ?? DEFAULT_KA_COLOR,
          isCenter: n.data.node.direction === 'center',
          onRecenter,
        },
      }
    })

    const rfEdges: Edge[] = visible.edges.map((e) => ({
      id: e.id,
      source: e.source,
      target: e.target,
      markerEnd: { type: MarkerType.ArrowClosed },
    }))

    return { nodes: rfNodes, edges: rfEdges }
  }, [neighborhood, expanded, kaColorMap, onRecenter, onToggleCluster])

  return (
    <div className="h-[70vh] w-full rounded-[14px] border border-gray-200 bg-white">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={NODE_TYPES}
        fitView
        proOptions={{ hideAttribution: true }}
      >
        <Background />
        <Controls />
        <MiniMap pannable zoomable />
      </ReactFlow>
    </div>
  )
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd apps/web && npx vitest run src/components/curriculum/__tests__/PrerequisiteGraph.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/components/curriculum/PrerequisiteGraph.tsx apps/web/src/components/curriculum/__tests__/PrerequisiteGraph.test.tsx
git commit -m "feat(#15): PrerequisiteGraph React Flow wrapper"
```

---

## Task 10: Page + route — `ConceptGraphPage.tsx`

**Files:**
- Modify: `apps/web/src/hooks/useConceptLockStatus.ts` (add `conceptLockKeys.neighborhood` + `useConceptNeighborhood`)
- Create: `apps/web/src/pages/ConceptGraphPage.tsx`
- Modify: `apps/web/src/App.tsx` (route + import)
- Test: `apps/web/src/pages/__tests__/ConceptGraphPage.test.tsx` (create)

**Interfaces:**
- Consumes: `prerequisiteService.getNeighborhood` (Task 4), `courseService.fetchCourseBySlug` (existing), `PrerequisiteGraph` (Task 9), `useParams`/`useNavigate`/`Link`.
- Produces: `useConceptNeighborhood(conceptId, depth?)` react-query hook; default-exported `ConceptGraphPage`; route `/curriculum/graph/:conceptId`.

- [ ] **Step 1: Write the failing test**

Create `apps/web/src/pages/__tests__/ConceptGraphPage.test.tsx`:

```tsx
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import ConceptGraphPage from '../ConceptGraphPage'
import { courseService } from '../../services/courseService'
import { prerequisiteService } from '../../services/prerequisiteService'

const navigate = vi.fn()
vi.mock('react-router-dom', async (orig) => ({
  ...(await orig<typeof import('react-router-dom')>()),
  useNavigate: () => navigate,
}))
vi.mock('../../components/layout/Navigation', () => ({ Navigation: () => null }))
vi.mock('../../services/courseService', () => ({ courseService: { fetchCourseBySlug: vi.fn() } }))
vi.mock('../../services/prerequisiteService', () => ({ prerequisiteService: { getNeighborhood: vi.fn() } }))
// Stub the graph: expose buttons to trigger re-center + cluster toggle.
vi.mock('../../components/curriculum/PrerequisiteGraph', () => ({
  default: ({ onRecenter, onToggleCluster }: { onRecenter: (id: string) => void; onToggleCluster: (id: string) => void }) => (
    <div>
      <button onClick={() => onRecenter('p1')}>recenter</button>
      <button onClick={() => onToggleCluster('cluster:c:prereq')}>toggle</button>
    </div>
  ),
}))

const course = { id: 'course-1', slug: 'cbap', name: 'CBAP', knowledge_areas: [{ id: 'ka-1', name: 'Planning', abbreviation: 'P', color_hex: '#3b82f6' }] }
const neighborhood = {
  center_id: 'c', depth: 2, truncated: false,
  nodes: [{ concept_id: 'c', name: 'Center Concept', knowledge_area_id: 'ka-1', difficulty: 0.5, is_unlocked: true, mastery_progress: 1, depth: 0, direction: 'center' }],
  edges: [],
}

function renderAt(conceptId: string) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[`/curriculum/graph/${conceptId}`]}>
        <Routes><Route path="/curriculum/graph/:conceptId" element={<ConceptGraphPage />} /></Routes>
      </MemoryRouter>
    </QueryClientProvider>
  )
}

describe('ConceptGraphPage', () => {
  beforeEach(() => vi.clearAllMocks())

  it('renders the center concept name on success', async () => {
    vi.mocked(courseService.fetchCourseBySlug).mockResolvedValue(course as never)
    vi.mocked(prerequisiteService.getNeighborhood).mockResolvedValue(neighborhood as never)
    renderAt('c')
    await waitFor(() => expect(screen.getByText('Center Concept')).toBeInTheDocument())
  })

  it('re-centers by navigating to the clicked concept', async () => {
    vi.mocked(courseService.fetchCourseBySlug).mockResolvedValue(course as never)
    vi.mocked(prerequisiteService.getNeighborhood).mockResolvedValue(neighborhood as never)
    renderAt('c')
    await waitFor(() => screen.getByText('recenter'))
    fireEvent.click(screen.getByText('recenter'))
    expect(navigate).toHaveBeenCalledWith('/curriculum/graph/p1')
  })

  it('shows an error state with retry', async () => {
    vi.mocked(courseService.fetchCourseBySlug).mockResolvedValue(course as never)
    vi.mocked(prerequisiteService.getNeighborhood).mockRejectedValue(new Error('boom'))
    renderAt('c')
    await waitFor(() => expect(screen.getByText(/couldn't load/i)).toBeInTheDocument())
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/web && npx vitest run src/pages/__tests__/ConceptGraphPage.test.tsx`
Expected: FAIL — cannot find module `../ConceptGraphPage`

- [ ] **Step 3: Write minimal implementation**

In `apps/web/src/hooks/useConceptLockStatus.ts`, add to the `conceptLockKeys` factory:

```typescript
  neighborhood: (conceptId: string, depth: number) =>
    [...conceptLockKeys.all, 'neighborhood', conceptId, depth] as const,
```

Add the `NeighborhoodResponse` import and the hook:

```typescript
import {
  prerequisiteService,
  GateCheckResult,
  BulkUnlockStatusResponse,
  OverrideAttemptResponse,
  RecentUnlocksResponse,
  NeighborhoodResponse,
} from '../services/prerequisiteService'
```

```typescript
/**
 * Fetch a concept's prerequisite neighborhood for the interactive graph
 * (Story 4.11, Slice D).
 *
 * @param conceptId - Concept UUID, or null/undefined to disable
 * @param depth - Hops each direction (default 2)
 */
export function useConceptNeighborhood(
  conceptId: string | null | undefined,
  depth = 2
) {
  return useQuery<NeighborhoodResponse>({
    queryKey: conceptLockKeys.neighborhood(conceptId ?? '', depth),
    queryFn: () => prerequisiteService.getNeighborhood(conceptId as string, depth),
    enabled: Boolean(conceptId),
    staleTime: 30_000,
  })
}
```

Create `apps/web/src/pages/ConceptGraphPage.tsx`:

```tsx
import { useEffect, useMemo, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Navigation } from '../components/layout/Navigation'
import { courseService } from '../services/courseService'
import { useConceptNeighborhood } from '../hooks/useConceptLockStatus'
import PrerequisiteGraph from '../components/curriculum/PrerequisiteGraph'

const ONBOARDING_STORAGE_KEY = 'learnr_onboarding'
const DEFAULT_COURSE_SLUG = 'cbap'

function getSelectedCourseSlug(): string {
  try {
    const stored = sessionStorage.getItem(ONBOARDING_STORAGE_KEY)
    if (stored) return JSON.parse(stored).course || DEFAULT_COURSE_SLUG
  } catch {
    // ignore
  }
  return DEFAULT_COURSE_SLUG
}

/** Full-page interactive prerequisite graph centered on one concept (Slice D). */
export default function ConceptGraphPage() {
  const { conceptId } = useParams<{ conceptId: string }>()
  const navigate = useNavigate()
  const [expanded, setExpanded] = useState<Set<string>>(new Set())

  // Reset cluster expansion whenever the focused concept changes.
  useEffect(() => setExpanded(new Set()), [conceptId])

  const courseSlug = useMemo(() => getSelectedCourseSlug(), [])
  const courseQuery = useQuery({
    queryKey: ['course', courseSlug],
    queryFn: () => courseService.fetchCourseBySlug(courseSlug),
    staleTime: Infinity,
    retry: 2,
  })

  const neighborhoodQuery = useConceptNeighborhood(conceptId)

  const kaColorMap = useMemo(() => {
    const map: Record<string, string> = {}
    for (const ka of courseQuery.data?.knowledge_areas ?? []) {
      map[ka.id] = ka.color_hex
    }
    return map
  }, [courseQuery.data])

  const center = neighborhoodQuery.data?.nodes.find((n) => n.direction === 'center')
  const isEmpty =
    neighborhoodQuery.data && neighborhoodQuery.data.nodes.length <= 1

  const onRecenter = (id: string) => navigate(`/curriculum/graph/${id}`)
  const onToggleCluster = (clusterId: string) =>
    setExpanded((prev) => new Set(prev).add(clusterId))

  return (
    <div className="min-h-screen bg-cream">
      <Navigation />
      <main className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
        <Link to="/curriculum" className="text-sm font-medium text-primary-700 underline">
          ← Back to curriculum
        </Link>
        <h1 className="mt-2 text-2xl font-bold text-charcoal">
          {center ? center.name : 'Prerequisite map'}
        </h1>
        <p className="mt-1 text-sm text-gray-600">
          Prerequisites to master first (below) and what this unlocks (above).
          Click a concept to explore it; use Practice to start a focused session.
        </p>

        <div className="mt-6">
          {neighborhoodQuery.isLoading && (
            <p className="text-gray-500">Loading the prerequisite map…</p>
          )}

          {neighborhoodQuery.isError && (
            <div className="rounded-[14px] border border-red-200 bg-red-50 p-4">
              <p className="font-medium text-red-800">Couldn't load the prerequisite map</p>
              <button
                type="button"
                onClick={() => void neighborhoodQuery.refetch()}
                className="mt-2 text-sm font-medium text-red-700 underline"
              >
                Try again
              </button>
            </div>
          )}

          {neighborhoodQuery.data && isEmpty && (
            <div className="rounded-[14px] border border-gray-200 bg-white p-6 text-center">
              <p className="font-medium text-charcoal">No prerequisites</p>
              <p className="mt-1 text-sm text-gray-600">
                This concept has no prerequisites or dependents — you can start it now.
              </p>
            </div>
          )}

          {neighborhoodQuery.data && !isEmpty && (
            <>
              <PrerequisiteGraph
                neighborhood={neighborhoodQuery.data}
                expanded={expanded}
                kaColorMap={kaColorMap}
                onRecenter={onRecenter}
                onToggleCluster={onToggleCluster}
              />
              {/* Accessible text equivalent of the canvas. */}
              <ul className="sr-only">
                {neighborhoodQuery.data.nodes.map((n) => (
                  <li key={n.concept_id}>
                    <Link to={`/curriculum/graph/${n.concept_id}`}>
                      {n.name} — {n.direction}, {n.is_unlocked ? 'unlocked' : 'locked'}
                    </Link>
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
      </main>
    </div>
  )
}
```

In `apps/web/src/App.tsx`, import the page and register the route after the `/curriculum` route:

```tsx
import ConceptGraphPage from './pages/ConceptGraphPage'
```

```tsx
  {
    path: '/curriculum/graph/:conceptId',
    element: (
      <ProtectedRoute>
        <ConceptGraphPage />
      </ProtectedRoute>
    ),
  },
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd apps/web && npx vitest run src/pages/__tests__/ConceptGraphPage.test.tsx`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/hooks/useConceptLockStatus.ts apps/web/src/pages/ConceptGraphPage.tsx apps/web/src/App.tsx apps/web/src/pages/__tests__/ConceptGraphPage.test.tsx
git commit -m "feat(#15): ConceptGraphPage + /curriculum/graph/:conceptId route"
```

---

## Task 11: Entry point — "View map" link on `ConceptRow`

**Files:**
- Modify: `apps/web/src/components/curriculum/ConceptRow.tsx`
- Test: `apps/web/src/components/curriculum/__tests__/ConceptRow.test.tsx` (add a case; create the file if absent)

**Interfaces:**
- Consumes: `Link` from `react-router-dom`; existing `concept.concept_id`.
- Produces: a `<Link>` to `/curriculum/graph/{concept_id}` rendered in each row.

- [ ] **Step 1: Write the failing test**

Add to `apps/web/src/components/curriculum/__tests__/ConceptRow.test.tsx`:

```tsx
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { ConceptRow } from '../ConceptRow'

const concept = {
  concept_id: 'abc', concept_name: 'Test Concept', knowledge_area_id: 'ka-1',
  is_unlocked: true, has_prerequisites: false, prerequisite_count: 0,
  mastered_prerequisite_count: 0, mastery_progress: 1,
}

function renderRow() {
  const client = new QueryClient()
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <ConceptRow concept={concept} />
      </MemoryRouter>
    </QueryClientProvider>
  )
}

describe('ConceptRow view-map link', () => {
  it('links to the concept graph route', () => {
    renderRow()
    const link = screen.getByRole('link', { name: /view map/i })
    expect(link).toHaveAttribute('href', '/curriculum/graph/abc')
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/web && npx vitest run src/components/curriculum/__tests__/ConceptRow.test.tsx -t "view-map"`
Expected: FAIL — no link named "view map"

- [ ] **Step 3: Write minimal implementation**

In `apps/web/src/components/curriculum/ConceptRow.tsx`, add the import:

```tsx
import { Link } from 'react-router-dom'
```

Wrap the action buttons so the Practice button and a new "View map" link sit together (replace the single Practice `<button>` block):

```tsx
        <div className="flex shrink-0 items-center gap-2">
          <Link
            to={`/curriculum/graph/${concept.concept_id}`}
            className="px-3 py-1.5 text-sm font-medium text-gray-600 rounded-[14px] border border-gray-200 hover:bg-gray-50"
          >
            View map
          </Link>
          <button
            type="button"
            onClick={practice.handlePractice}
            aria-describedby={showTooltip ? tooltipId : undefined}
            className="px-3 py-1.5 text-sm font-medium text-primary-700 rounded-[14px] border border-primary-200 hover:bg-primary-50"
          >
            Practice
          </button>
        </div>
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd apps/web && npx vitest run src/components/curriculum/__tests__/ConceptRow.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/components/curriculum/ConceptRow.tsx apps/web/src/components/curriculum/__tests__/ConceptRow.test.tsx
git commit -m "feat(#15): link curriculum rows to the prerequisite graph"
```

---

## Task 12: Full-suite verification, coverage, CHANGELOG

**Files:**
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Run backend tests + coverage**

Run: `cd apps/api && pytest tests/unit/services/test_mastery_gate.py tests/unit/test_prerequisite_repository.py tests/integration/test_prerequisite_navigation_api.py -v`
Expected: all PASS. Then full: `cd apps/api && pytest` — no regressions.

- [ ] **Step 2: Run frontend tests + coverage**

Run: `cd apps/web && npx vitest run --coverage`
Expected: all PASS; coverage ≥ 80% for the new files. If a new file is under 80%, add the missing-branch test before proceeding.

- [ ] **Step 3: Type-check + lint**

Run: `npm run type-check && npm run lint`
Expected: clean. Fix any issues (e.g. unused imports left from the `ConceptRow` refactor).

- [ ] **Step 4: Update CHANGELOG**

Add under an `Added` section (reference issue #15):

```markdown
### Added
- Interactive prerequisite graph (#15, Story 4.11 Slice D): new
  `GET /concepts/{id}/neighborhood` endpoint and a deep-linkable
  `/curriculum/graph/:conceptId` page rendering a concept's prerequisite and
  dependent neighborhood (React Flow + dagre), with KA color-coding, lock
  status, click-to-re-center, per-node practice launch, and expandable hub
  clusters for dense concepts.
```

- [ ] **Step 5: Commit**

```bash
git add CHANGELOG.md
git commit -m "docs(#15): changelog for interactive prerequisite graph"
```

---

## Self-Review

**Spec coverage check:**
- Endpoint (live, depth 2, lock status join) → Tasks 1–3. ✓
- Schemas (signed depth, direction, truncated) → Task 2. ✓
- Absolute safety ceiling, logged, non-silent → Task 2 (`max_neighborhood_nodes`, `neighborhood_truncated` log). ✓
- React Flow + dagre, deep-linkable route → Tasks 7, 9, 10. ✓
- Neighbor click re-centers; per-node Practice with soft-gate → Tasks 8, 10 (`onRecenter`, `useConceptPractice`). ✓
- Expandable cluster nodes, ranked by actionability, nothing hidden silently → Task 6 (`clusterNeighborhood`, `+N more`). ✓
- KA colors resolved client-side from cached course → Task 10 (`kaColorMap`). ✓
- `useConceptPractice` extraction, reused in ConceptRow + node → Tasks 5, 8. ✓
- Entry point from ConceptRow → Task 11. ✓
- Accessible text-list equivalent → Task 10 (`sr-only` list). ✓
- Loading / error / empty states → Task 10. ✓
- Testing both ends ≥80% → per-task tests + Task 12. ✓

**Type consistency check:** `NeighborhoodResponse`/`NeighborhoodNode`/`NeighborhoodEdge` names + fields match across backend (Task 2) and frontend (Task 4). `VisibleNode`/`VisibleEdge`/`ConceptNodeData`/`ClusterNodeData` (Task 6) consumed unchanged in Tasks 7–9. `GraphNodeData` defined in Task 8, consumed in Task 9. `clusterNeighborhood`/`layoutGraph`/`useConceptNeighborhood`/`useConceptPractice` signatures consistent across producer and consumer tasks. Cluster id format `cluster:{parentId}:{direction}` is consistent between Task 6 (produced) and Task 10 test (referenced). ✓

**Placeholder scan:** No TBD/TODO; every code step shows full code; commands have expected output. ✓
