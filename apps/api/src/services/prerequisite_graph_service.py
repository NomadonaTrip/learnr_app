"""
Prerequisite Graph Service

Provides in-memory caching of the prerequisite graph for fast BKT lookups.
Loaded on application startup and provides O(1) prerequisite lookups.
"""
import asyncio
import logging
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple
from uuid import UUID

import networkx as nx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


@dataclass
class CachedConcept:
    """Lightweight concept data for cache."""
    id: UUID
    name: str
    knowledge_area_id: str
    difficulty_estimate: float
    prerequisite_depth: int


@dataclass
class CachedPrerequisite:
    """Cached prerequisite relationship."""
    prerequisite_id: UUID
    strength: float
    relationship_type: str


class PrerequisiteGraphService:
    """
    In-memory prerequisite graph cache for fast BKT lookups.

    Provides:
    - O(1) direct prerequisite lookup
    - Cached BFS for prerequisite chains
    - O(1) prerequisite depth lookup
    - Graph statistics
    """

    _instance: Optional["PrerequisiteGraphService"] = None
    _lock = asyncio.Lock()

    def __init__(self):
        # Graph storage
        self.graph: Optional[nx.DiGraph] = None
        self.concepts: Dict[UUID, CachedConcept] = {}
        self.prerequisites: Dict[UUID, List[CachedPrerequisite]] = defaultdict(list)
        self.dependents: Dict[UUID, List[UUID]] = defaultdict(list)
        self.depths: Dict[UUID, int] = {}
        self.root_concepts: Set[UUID] = set()

        # Cache metadata
        self.loaded_at: Optional[float] = None
        self.course_ids: Set[UUID] = set()
        self.load_time_ms: float = 0.0
        self.concept_count: int = 0
        self.edge_count: int = 0

    @classmethod
    async def get_instance(cls) -> "PrerequisiteGraphService":
        """Get singleton instance."""
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    async def reset_instance(cls) -> None:
        """Reset singleton (for testing)."""
        async with cls._lock:
            cls._instance = None

    async def load_graph(self, session: AsyncSession, course_id: Optional[UUID] = None) -> None:
        """
        Load prerequisite graph into memory.

        Args:
            session: Database session
            course_id: Optional course ID to filter by (loads all if None)
        """
        from src.models.concept import Concept
        from src.models.concept_prerequisite import ConceptPrerequisite

        start_time = time.time()
        logger.info("Loading prerequisite graph into memory...")

        # Clear existing data
        self.graph = nx.DiGraph()
        self.concepts.clear()
        self.prerequisites.clear()
        self.dependents.clear()
        self.depths.clear()
        self.root_concepts.clear()
        self.course_ids.clear()

        # Load concepts
        concept_query = select(Concept)
        if course_id:
            concept_query = concept_query.where(Concept.course_id == course_id)

        result = await session.execute(concept_query)
        db_concepts = result.scalars().all()

        for c in db_concepts:
            cached = CachedConcept(
                id=c.id,
                name=c.name,
                knowledge_area_id=c.knowledge_area_id,
                difficulty_estimate=c.difficulty_estimate,
                prerequisite_depth=c.prerequisite_depth,
            )
            self.concepts[c.id] = cached
            self.depths[c.id] = c.prerequisite_depth
            self.course_ids.add(c.course_id)

            # Add node to graph
            self.graph.add_node(
                c.id,
                name=c.name,
                ka=c.knowledge_area_id,
                difficulty=c.difficulty_estimate,
                depth=c.prerequisite_depth,
            )

        self.concept_count = len(self.concepts)
        logger.info(f"Loaded {self.concept_count} concepts")

        # Load prerequisites
        concept_ids = list(self.concepts.keys())
        if not concept_ids:
            self.load_time_ms = (time.time() - start_time) * 1000
            self.loaded_at = time.time()
            return

        prereq_query = select(ConceptPrerequisite).where(
            ConceptPrerequisite.concept_id.in_(concept_ids)
        )
        result = await session.execute(prereq_query)
        db_prereqs = result.scalars().all()

        for p in db_prereqs:
            cached = CachedPrerequisite(
                prerequisite_id=p.prerequisite_concept_id,
                strength=p.strength,
                relationship_type=p.relationship_type,
            )
            self.prerequisites[p.concept_id].append(cached)
            self.dependents[p.prerequisite_concept_id].append(p.concept_id)

            # Add edge to graph (prereq -> concept)
            self.graph.add_edge(
                p.prerequisite_concept_id,
                p.concept_id,
                strength=p.strength,
                relationship_type=p.relationship_type,
            )

        self.edge_count = len(db_prereqs)
        logger.info(f"Loaded {self.edge_count} prerequisite relationships")

        # Identify root concepts (no prerequisites)
        for concept_id in self.concepts:
            if concept_id not in self.prerequisites or not self.prerequisites[concept_id]:
                self.root_concepts.add(concept_id)

        logger.info(f"Identified {len(self.root_concepts)} root concepts")

        self.load_time_ms = (time.time() - start_time) * 1000
        self.loaded_at = time.time()

        logger.info(f"Prerequisite graph loaded in {self.load_time_ms:.2f}ms")

        if self.load_time_ms > 5000:
            logger.warning(f"Graph load time ({self.load_time_ms:.0f}ms) exceeds 5s threshold")

    def is_loaded(self) -> bool:
        """Check if graph is loaded."""
        return self.graph is not None and self.loaded_at is not None

    def get_prerequisites(self, concept_id: UUID) -> List[CachedPrerequisite]:
        """
        Get direct prerequisites for a concept. O(1) lookup.

        Args:
            concept_id: Concept UUID

        Returns:
            List of cached prerequisites
        """
        return self.prerequisites.get(concept_id, [])

    def get_prerequisite_ids(self, concept_id: UUID) -> List[UUID]:
        """
        Get prerequisite concept IDs. O(1) lookup.

        Args:
            concept_id: Concept UUID

        Returns:
            List of prerequisite concept UUIDs
        """
        return [p.prerequisite_id for p in self.prerequisites.get(concept_id, [])]

    def get_prerequisite_chain(
        self, concept_id: UUID, max_depth: int = 10
    ) -> List[Tuple[UUID, int]]:
        """
        Get full prerequisite chain using cached BFS.

        Args:
            concept_id: Target concept UUID
            max_depth: Maximum depth to traverse

        Returns:
            List of (concept_id, depth) tuples
        """
        if not self.graph or concept_id not in self.graph:
            return []

        # BFS backwards through graph
        visited: Dict[UUID, int] = {}
        queue: List[Tuple[UUID, int]] = []

        # Start with direct prerequisites
        for prereq in self.prerequisites.get(concept_id, []):
            queue.append((prereq.prerequisite_id, 1))

        while queue:
            current_id, depth = queue.pop(0)

            if depth > max_depth:
                continue

            if current_id in visited:
                continue

            visited[current_id] = depth

            # Add prerequisites of current
            for prereq in self.prerequisites.get(current_id, []):
                if prereq.prerequisite_id not in visited:
                    queue.append((prereq.prerequisite_id, depth + 1))

        # Sort by depth
        result = [(cid, d) for cid, d in visited.items()]
        result.sort(key=lambda x: x[1])
        return result

    def get_prerequisite_depth(self, concept_id: UUID) -> int:
        """
        Get prerequisite depth for a concept. O(1) lookup.

        Args:
            concept_id: Concept UUID

        Returns:
            Prerequisite depth (0 = foundational)
        """
        return self.depths.get(concept_id, 0)

    def get_dependents(self, concept_id: UUID) -> List[UUID]:
        """
        Get concepts that depend on this one. O(1) lookup.

        Args:
            concept_id: Prerequisite concept UUID

        Returns:
            List of dependent concept UUIDs
        """
        return self.dependents.get(concept_id, [])

    def get_root_concepts(self) -> List[UUID]:
        """
        Get all root concepts (no prerequisites).

        Returns:
            List of root concept UUIDs
        """
        return list(self.root_concepts)

    def get_concept(self, concept_id: UUID) -> Optional[CachedConcept]:
        """
        Get cached concept data. O(1) lookup.

        Args:
            concept_id: Concept UUID

        Returns:
            CachedConcept or None
        """
        return self.concepts.get(concept_id)

    def get_statistics(self) -> Dict:
        """Get graph statistics."""
        return {
            "loaded": self.is_loaded(),
            "loaded_at": self.loaded_at,
            "load_time_ms": self.load_time_ms,
            "concept_count": self.concept_count,
            "edge_count": self.edge_count,
            "root_concept_count": len(self.root_concepts),
            "course_ids": list(self.course_ids),
            "memory_estimate_kb": self._estimate_memory(),
        }

    def _estimate_memory(self) -> float:
        """Estimate memory usage in KB."""
        import sys

        total = 0
        total += sys.getsizeof(self.concepts)
        total += sys.getsizeof(self.prerequisites)
        total += sys.getsizeof(self.dependents)
        total += sys.getsizeof(self.depths)

        # Rough estimate for graph
        if self.graph:
            total += self.concept_count * 200  # ~200 bytes per node
            total += self.edge_count * 100  # ~100 bytes per edge

        return total / 1024


# Global service instance accessor
async def get_prerequisite_graph_service() -> PrerequisiteGraphService:
    """FastAPI dependency for graph service."""
    return await PrerequisiteGraphService.get_instance()


async def load_prerequisite_graph(session: AsyncSession, course_id: Optional[UUID] = None) -> None:
    """
    Load prerequisite graph on startup.

    Called from application lifespan handler.
    """
    service = await PrerequisiteGraphService.get_instance()
    await service.load_graph(session, course_id)


async def refresh_prerequisite_graph(session: AsyncSession, course_id: Optional[UUID] = None) -> None:
    """
    Refresh prerequisite graph.

    Can be called after graph modifications.
    """
    service = await PrerequisiteGraphService.get_instance()
    await service.load_graph(session, course_id)
