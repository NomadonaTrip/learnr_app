"""
Unit tests for PrerequisiteGraphService.
Tests the in-memory prerequisite graph cache for BKT lookups.
"""
import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.services.prerequisite_graph_service import (
    CachedConcept,
    CachedPrerequisite,
    PrerequisiteGraphService,
    get_prerequisite_graph_service,
    load_prerequisite_graph,
    refresh_prerequisite_graph,
)


class TestCachedConcept:
    """Tests for CachedConcept dataclass."""

    def test_create_cached_concept(self):
        """Test creating a CachedConcept."""
        concept_id = uuid4()
        concept = CachedConcept(
            id=concept_id,
            name="Stakeholder Analysis",
            knowledge_area_id="KA1",
            difficulty_estimate=0.5,
            prerequisite_depth=2,
        )
        assert concept.id == concept_id
        assert concept.name == "Stakeholder Analysis"
        assert concept.knowledge_area_id == "KA1"
        assert concept.difficulty_estimate == 0.5
        assert concept.prerequisite_depth == 2


class TestCachedPrerequisite:
    """Tests for CachedPrerequisite dataclass."""

    def test_create_cached_prerequisite(self):
        """Test creating a CachedPrerequisite."""
        prereq_id = uuid4()
        prereq = CachedPrerequisite(
            prerequisite_id=prereq_id,
            strength=0.8,
            relationship_type="required",
        )
        assert prereq.prerequisite_id == prereq_id
        assert prereq.strength == 0.8
        assert prereq.relationship_type == "required"


class TestPrerequisiteGraphServiceInit:
    """Tests for PrerequisiteGraphService initialization."""

    def test_initial_state(self):
        """Test service initializes with empty state."""
        service = PrerequisiteGraphService()

        assert service.graph is None
        assert service.concepts == {}
        assert len(service.prerequisites) == 0
        assert len(service.dependents) == 0
        assert service.depths == {}
        assert service.root_concepts == set()
        assert service.loaded_at is None
        assert service.concept_count == 0
        assert service.edge_count == 0

    def test_is_loaded_false_initially(self):
        """Test is_loaded returns False initially."""
        service = PrerequisiteGraphService()
        assert service.is_loaded() is False


class TestPrerequisiteGraphServiceSingleton:
    """Tests for singleton pattern."""

    @pytest.fixture(autouse=True)
    async def reset_singleton(self):
        """Reset singleton before each test."""
        await PrerequisiteGraphService.reset_instance()
        yield
        await PrerequisiteGraphService.reset_instance()

    @pytest.mark.asyncio
    async def test_get_instance_creates_singleton(self):
        """Test get_instance creates a singleton."""
        instance1 = await PrerequisiteGraphService.get_instance()
        instance2 = await PrerequisiteGraphService.get_instance()

        assert instance1 is instance2

    @pytest.mark.asyncio
    async def test_reset_instance_clears_singleton(self):
        """Test reset_instance clears the singleton."""
        instance1 = await PrerequisiteGraphService.get_instance()
        await PrerequisiteGraphService.reset_instance()
        instance2 = await PrerequisiteGraphService.get_instance()

        assert instance1 is not instance2


class TestPrerequisiteGraphServiceLoadGraph:
    """Tests for load_graph method."""

    @pytest.fixture(autouse=True)
    async def reset_singleton(self):
        """Reset singleton before each test."""
        await PrerequisiteGraphService.reset_instance()
        yield
        await PrerequisiteGraphService.reset_instance()

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        return AsyncMock()

    @pytest.fixture
    def sample_concepts(self):
        """Create sample concept data."""
        course_id = uuid4()
        concept1_id = uuid4()
        concept2_id = uuid4()
        concept3_id = uuid4()

        concept1 = MagicMock()
        concept1.id = concept1_id
        concept1.name = "Root Concept"
        concept1.knowledge_area_id = "KA1"
        concept1.difficulty_estimate = 0.3
        concept1.prerequisite_depth = 0
        concept1.course_id = course_id

        concept2 = MagicMock()
        concept2.id = concept2_id
        concept2.name = "Intermediate Concept"
        concept2.knowledge_area_id = "KA1"
        concept2.difficulty_estimate = 0.5
        concept2.prerequisite_depth = 1
        concept2.course_id = course_id

        concept3 = MagicMock()
        concept3.id = concept3_id
        concept3.name = "Advanced Concept"
        concept3.knowledge_area_id = "KA2"
        concept3.difficulty_estimate = 0.8
        concept3.prerequisite_depth = 2
        concept3.course_id = course_id

        return [concept1, concept2, concept3], course_id

    @pytest.fixture
    def sample_prerequisites(self, sample_concepts):
        """Create sample prerequisite data."""
        concepts, _ = sample_concepts
        concept1_id = concepts[0].id
        concept2_id = concepts[1].id
        concept3_id = concepts[2].id

        # concept2 requires concept1
        prereq1 = MagicMock()
        prereq1.concept_id = concept2_id
        prereq1.prerequisite_concept_id = concept1_id
        prereq1.strength = 0.9
        prereq1.relationship_type = "required"

        # concept3 requires concept2
        prereq2 = MagicMock()
        prereq2.concept_id = concept3_id
        prereq2.prerequisite_concept_id = concept2_id
        prereq2.strength = 0.8
        prereq2.relationship_type = "recommended"

        return [prereq1, prereq2]

    @pytest.mark.asyncio
    async def test_load_graph_with_concepts(self, mock_session, sample_concepts):
        """Test loading graph with concepts."""
        concepts, course_id = sample_concepts

        # Mock database results
        concept_result = MagicMock()
        concept_result.scalars.return_value.all.return_value = concepts

        prereq_result = MagicMock()
        prereq_result.scalars.return_value.all.return_value = []

        mock_session.execute = AsyncMock(side_effect=[concept_result, prereq_result])

        service = PrerequisiteGraphService()
        await service.load_graph(mock_session)

        assert service.is_loaded() is True
        assert service.concept_count == 3
        assert len(service.concepts) == 3
        assert course_id in service.course_ids

    @pytest.mark.asyncio
    async def test_load_graph_with_prerequisites(
        self, mock_session, sample_concepts, sample_prerequisites
    ):
        """Test loading graph with prerequisites."""
        concepts, course_id = sample_concepts

        # Mock database results
        concept_result = MagicMock()
        concept_result.scalars.return_value.all.return_value = concepts

        prereq_result = MagicMock()
        prereq_result.scalars.return_value.all.return_value = sample_prerequisites

        mock_session.execute = AsyncMock(side_effect=[concept_result, prereq_result])

        service = PrerequisiteGraphService()
        await service.load_graph(mock_session)

        assert service.edge_count == 2
        # Root concept should have no prerequisites
        assert concepts[0].id in service.root_concepts
        # Intermediate and advanced should not be roots
        assert concepts[1].id not in service.root_concepts
        assert concepts[2].id not in service.root_concepts

    @pytest.mark.asyncio
    async def test_load_graph_empty(self, mock_session):
        """Test loading graph with no concepts."""
        concept_result = MagicMock()
        concept_result.scalars.return_value.all.return_value = []

        mock_session.execute = AsyncMock(return_value=concept_result)

        service = PrerequisiteGraphService()
        await service.load_graph(mock_session)

        assert service.is_loaded() is True
        assert service.concept_count == 0
        assert service.edge_count == 0

    @pytest.mark.asyncio
    async def test_load_graph_clears_previous_data(self, mock_session, sample_concepts):
        """Test that load_graph clears previous data."""
        concepts, _ = sample_concepts

        concept_result = MagicMock()
        concept_result.scalars.return_value.all.return_value = concepts

        prereq_result = MagicMock()
        prereq_result.scalars.return_value.all.return_value = []

        mock_session.execute = AsyncMock(side_effect=[concept_result, prereq_result])

        service = PrerequisiteGraphService()
        # Pre-populate with dummy data
        service.concepts[uuid4()] = CachedConcept(
            id=uuid4(),
            name="Old Concept",
            knowledge_area_id="OLD",
            difficulty_estimate=0.1,
            prerequisite_depth=0,
        )

        await service.load_graph(mock_session)

        # Old data should be cleared
        assert service.concept_count == 3
        assert "OLD" not in [c.knowledge_area_id for c in service.concepts.values()]


class TestPrerequisiteGraphServiceQueries:
    """Tests for query methods."""

    @pytest.fixture
    def populated_service(self):
        """Create a service with pre-populated data."""
        service = PrerequisiteGraphService()

        # Create UUIDs
        concept1_id = uuid4()
        concept2_id = uuid4()
        concept3_id = uuid4()

        # Add concepts
        service.concepts = {
            concept1_id: CachedConcept(
                id=concept1_id,
                name="Root",
                knowledge_area_id="KA1",
                difficulty_estimate=0.3,
                prerequisite_depth=0,
            ),
            concept2_id: CachedConcept(
                id=concept2_id,
                name="Intermediate",
                knowledge_area_id="KA1",
                difficulty_estimate=0.5,
                prerequisite_depth=1,
            ),
            concept3_id: CachedConcept(
                id=concept3_id,
                name="Advanced",
                knowledge_area_id="KA2",
                difficulty_estimate=0.8,
                prerequisite_depth=2,
            ),
        }

        # Add prerequisites
        service.prerequisites[concept2_id] = [
            CachedPrerequisite(
                prerequisite_id=concept1_id,
                strength=0.9,
                relationship_type="required",
            )
        ]
        service.prerequisites[concept3_id] = [
            CachedPrerequisite(
                prerequisite_id=concept2_id,
                strength=0.8,
                relationship_type="recommended",
            )
        ]

        # Add dependents
        service.dependents[concept1_id] = [concept2_id]
        service.dependents[concept2_id] = [concept3_id]

        # Add depths
        service.depths = {
            concept1_id: 0,
            concept2_id: 1,
            concept3_id: 2,
        }

        # Add roots
        service.root_concepts = {concept1_id}

        # Store IDs for tests
        service._test_ids = (concept1_id, concept2_id, concept3_id)

        return service

    def test_get_prerequisites(self, populated_service):
        """Test get_prerequisites returns direct prerequisites."""
        _, concept2_id, _ = populated_service._test_ids
        prereqs = populated_service.get_prerequisites(concept2_id)

        assert len(prereqs) == 1
        assert prereqs[0].strength == 0.9

    def test_get_prerequisites_empty(self, populated_service):
        """Test get_prerequisites returns empty for root concept."""
        concept1_id, _, _ = populated_service._test_ids
        prereqs = populated_service.get_prerequisites(concept1_id)

        assert len(prereqs) == 0

    def test_get_prerequisites_nonexistent(self, populated_service):
        """Test get_prerequisites returns empty for nonexistent concept."""
        prereqs = populated_service.get_prerequisites(uuid4())
        assert len(prereqs) == 0

    def test_get_prerequisite_ids(self, populated_service):
        """Test get_prerequisite_ids returns list of UUIDs."""
        concept1_id, concept2_id, _ = populated_service._test_ids
        prereq_ids = populated_service.get_prerequisite_ids(concept2_id)

        assert len(prereq_ids) == 1
        assert prereq_ids[0] == concept1_id

    def test_get_prerequisite_depth(self, populated_service):
        """Test get_prerequisite_depth returns correct depth."""
        concept1_id, concept2_id, concept3_id = populated_service._test_ids

        assert populated_service.get_prerequisite_depth(concept1_id) == 0
        assert populated_service.get_prerequisite_depth(concept2_id) == 1
        assert populated_service.get_prerequisite_depth(concept3_id) == 2

    def test_get_prerequisite_depth_nonexistent(self, populated_service):
        """Test get_prerequisite_depth returns 0 for nonexistent concept."""
        depth = populated_service.get_prerequisite_depth(uuid4())
        assert depth == 0

    def test_get_dependents(self, populated_service):
        """Test get_dependents returns dependent concepts."""
        concept1_id, concept2_id, _ = populated_service._test_ids
        dependents = populated_service.get_dependents(concept1_id)

        assert len(dependents) == 1
        assert dependents[0] == concept2_id

    def test_get_dependents_empty(self, populated_service):
        """Test get_dependents returns empty for leaf concept."""
        _, _, concept3_id = populated_service._test_ids
        dependents = populated_service.get_dependents(concept3_id)

        assert len(dependents) == 0

    def test_get_root_concepts(self, populated_service):
        """Test get_root_concepts returns root concepts."""
        concept1_id, _, _ = populated_service._test_ids
        roots = populated_service.get_root_concepts()

        assert len(roots) == 1
        assert concept1_id in roots

    def test_get_concept(self, populated_service):
        """Test get_concept returns cached concept."""
        concept1_id, _, _ = populated_service._test_ids
        concept = populated_service.get_concept(concept1_id)

        assert concept is not None
        assert concept.name == "Root"
        assert concept.knowledge_area_id == "KA1"

    def test_get_concept_nonexistent(self, populated_service):
        """Test get_concept returns None for nonexistent concept."""
        concept = populated_service.get_concept(uuid4())
        assert concept is None


class TestPrerequisiteGraphServiceChain:
    """Tests for prerequisite chain traversal."""

    @pytest.fixture
    def chain_service(self):
        """Create a service with a chain of prerequisites."""
        import networkx as nx

        service = PrerequisiteGraphService()
        service.graph = nx.DiGraph()

        # Create a chain: A -> B -> C -> D
        ids = [uuid4() for _ in range(4)]

        for i, cid in enumerate(ids):
            service.concepts[cid] = CachedConcept(
                id=cid,
                name=f"Concept {chr(65+i)}",
                knowledge_area_id="KA1",
                difficulty_estimate=0.2 * (i + 1),
                prerequisite_depth=i,
            )
            service.graph.add_node(cid, name=f"Concept {chr(65+i)}")

        # Set up prerequisites (reverse order: D needs C needs B needs A)
        for i in range(1, 4):
            service.prerequisites[ids[i]] = [
                CachedPrerequisite(
                    prerequisite_id=ids[i - 1],
                    strength=0.9,
                    relationship_type="required",
                )
            ]
            service.graph.add_edge(ids[i - 1], ids[i])

        service.root_concepts = {ids[0]}
        service._test_ids = ids

        return service

    def test_get_prerequisite_chain(self, chain_service):
        """Test get_prerequisite_chain returns full chain."""
        ids = chain_service._test_ids
        # Get chain for D (should return A, B, C)
        chain = chain_service.get_prerequisite_chain(ids[3])

        assert len(chain) == 3
        # Should be ordered by depth
        chain_ids = [c[0] for c in chain]
        assert ids[2] in chain_ids  # C at depth 1
        assert ids[1] in chain_ids  # B at depth 2
        assert ids[0] in chain_ids  # A at depth 3

    def test_get_prerequisite_chain_with_max_depth(self, chain_service):
        """Test get_prerequisite_chain respects max_depth."""
        ids = chain_service._test_ids
        # Get chain for D with max_depth=2
        chain = chain_service.get_prerequisite_chain(ids[3], max_depth=2)

        assert len(chain) == 2
        # Should only include C and B (depths 1 and 2)
        chain_ids = [c[0] for c in chain]
        assert ids[2] in chain_ids
        assert ids[1] in chain_ids
        assert ids[0] not in chain_ids  # A is at depth 3

    def test_get_prerequisite_chain_root_concept(self, chain_service):
        """Test get_prerequisite_chain returns empty for root."""
        ids = chain_service._test_ids
        chain = chain_service.get_prerequisite_chain(ids[0])

        assert len(chain) == 0

    def test_get_prerequisite_chain_nonexistent(self, chain_service):
        """Test get_prerequisite_chain returns empty for nonexistent concept."""
        chain = chain_service.get_prerequisite_chain(uuid4())
        assert len(chain) == 0

    def test_get_prerequisite_chain_no_graph(self):
        """Test get_prerequisite_chain returns empty when graph not loaded."""
        service = PrerequisiteGraphService()
        chain = service.get_prerequisite_chain(uuid4())
        assert len(chain) == 0


class TestPrerequisiteGraphServiceStatistics:
    """Tests for statistics and metadata methods."""

    @pytest.fixture
    def stats_service(self):
        """Create a service with data for statistics."""
        import time

        import networkx as nx

        service = PrerequisiteGraphService()
        service.graph = nx.DiGraph()

        # Add some nodes and edges
        ids = [uuid4() for _ in range(5)]
        for cid in ids:
            service.graph.add_node(cid)
            service.concepts[cid] = CachedConcept(
                id=cid,
                name="Test",
                knowledge_area_id="KA1",
                difficulty_estimate=0.5,
                prerequisite_depth=0,
            )

        # Add edges
        service.graph.add_edge(ids[0], ids[1])
        service.graph.add_edge(ids[1], ids[2])
        service.graph.add_edge(ids[2], ids[3])

        service.concept_count = 5
        service.edge_count = 3
        service.root_concepts = {ids[0], ids[4]}
        service.course_ids = {uuid4()}
        service.loaded_at = time.time()
        service.load_time_ms = 150.0

        return service

    def test_get_statistics(self, stats_service):
        """Test get_statistics returns correct stats."""
        stats = stats_service.get_statistics()

        assert stats["loaded"] is True
        assert stats["concept_count"] == 5
        assert stats["edge_count"] == 3
        assert stats["root_concept_count"] == 2
        assert stats["load_time_ms"] == 150.0
        assert len(stats["course_ids"]) == 1

    def test_get_statistics_not_loaded(self):
        """Test get_statistics when not loaded."""
        service = PrerequisiteGraphService()
        stats = service.get_statistics()

        assert stats["loaded"] is False
        assert stats["concept_count"] == 0
        assert stats["edge_count"] == 0

    def test_estimate_memory(self, stats_service):
        """Test _estimate_memory returns positive value."""
        memory_kb = stats_service._estimate_memory()

        assert memory_kb > 0
        assert isinstance(memory_kb, float)

    def test_estimate_memory_no_graph(self):
        """Test _estimate_memory with no graph."""
        service = PrerequisiteGraphService()
        memory_kb = service._estimate_memory()

        # Should still return something for the empty dicts
        assert memory_kb >= 0


class TestHelperFunctions:
    """Tests for module-level helper functions."""

    @pytest.fixture(autouse=True)
    async def reset_singleton(self):
        """Reset singleton before each test."""
        await PrerequisiteGraphService.reset_instance()
        yield
        await PrerequisiteGraphService.reset_instance()

    @pytest.mark.asyncio
    async def test_get_prerequisite_graph_service(self):
        """Test get_prerequisite_graph_service returns service."""
        service = await get_prerequisite_graph_service()

        assert isinstance(service, PrerequisiteGraphService)

    @pytest.mark.asyncio
    async def test_load_prerequisite_graph(self):
        """Test load_prerequisite_graph loads data."""
        mock_session = AsyncMock()

        concept_result = MagicMock()
        concept_result.scalars.return_value.all.return_value = []

        mock_session.execute = AsyncMock(return_value=concept_result)

        await load_prerequisite_graph(mock_session)

        service = await PrerequisiteGraphService.get_instance()
        assert service.is_loaded() is True

    @pytest.mark.asyncio
    async def test_refresh_prerequisite_graph(self):
        """Test refresh_prerequisite_graph reloads data."""
        mock_session = AsyncMock()

        concept_result = MagicMock()
        concept_result.scalars.return_value.all.return_value = []

        mock_session.execute = AsyncMock(return_value=concept_result)

        # Load initial
        await load_prerequisite_graph(mock_session)
        service = await PrerequisiteGraphService.get_instance()
        first_load_time = service.loaded_at

        # Wait a tiny bit
        await asyncio.sleep(0.01)

        # Refresh
        await refresh_prerequisite_graph(mock_session)
        second_load_time = service.loaded_at

        assert second_load_time > first_load_time


class TestPrerequisiteGraphServiceConcurrency:
    """Tests for concurrent access patterns."""

    @pytest.fixture(autouse=True)
    async def reset_singleton(self):
        """Reset singleton before each test."""
        await PrerequisiteGraphService.reset_instance()
        yield
        await PrerequisiteGraphService.reset_instance()

    @pytest.mark.asyncio
    async def test_concurrent_get_instance(self):
        """Test concurrent calls to get_instance return same instance."""
        # Create multiple concurrent requests
        tasks = [PrerequisiteGraphService.get_instance() for _ in range(10)]
        instances = await asyncio.gather(*tasks)

        # All should be the same instance
        first = instances[0]
        for instance in instances[1:]:
            assert instance is first
