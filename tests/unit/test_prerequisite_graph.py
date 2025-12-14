"""
Unit tests for prerequisite graph building logic.
Tests DAG validation, depth calculation, and graph statistics.
"""
import pytest
from uuid import uuid4

import networkx as nx


class TestDAGValidation:
    """Tests for DAG validation logic."""

    def test_valid_dag_passes(self):
        """Test that a valid DAG passes topological sort."""
        G = nx.DiGraph()
        G.add_edges_from([
            ("A", "B"),
            ("A", "C"),
            ("B", "D"),
            ("C", "D"),
        ])

        try:
            order = list(nx.topological_sort(G))
            is_valid = True
        except nx.NetworkXUnfeasible:
            is_valid = False

        assert is_valid
        assert len(order) == 4

    def test_cycle_detection(self):
        """Test that cycles are detected and reported."""
        G = nx.DiGraph()
        G.add_edges_from([
            ("A", "B"),
            ("B", "C"),
            ("C", "A"),  # Creates cycle
        ])

        with pytest.raises(nx.NetworkXUnfeasible):
            list(nx.topological_sort(G))

        cycles = list(nx.simple_cycles(G))
        assert len(cycles) == 1
        assert set(cycles[0]) == {"A", "B", "C"}

    def test_self_loop_detection(self):
        """Test that self-loops are detected."""
        G = nx.DiGraph()
        G.add_edge("A", "A")  # Self-loop

        with pytest.raises(nx.NetworkXUnfeasible):
            list(nx.topological_sort(G))

    def test_multiple_cycles(self):
        """Test detection of multiple cycles."""
        G = nx.DiGraph()
        G.add_edges_from([
            ("A", "B"),
            ("B", "A"),  # Cycle 1
            ("C", "D"),
            ("D", "E"),
            ("E", "C"),  # Cycle 2
        ])

        cycles = list(nx.simple_cycles(G))
        assert len(cycles) == 2


class TestDepthCalculation:
    """Tests for prerequisite depth calculation."""

    def test_depth_from_single_root(self):
        """Test depth calculation from single root."""
        G = nx.DiGraph()
        G.add_edges_from([
            ("A", "B"),
            ("B", "C"),
            ("C", "D"),
        ])

        # Find root (no incoming edges)
        roots = [n for n in G.nodes() if G.in_degree(n) == 0]
        assert roots == ["A"]

        # BFS from root
        depths = {}
        for root in roots:
            for node, depth in nx.single_source_shortest_path_length(G, root).items():
                if node not in depths or depth < depths[node]:
                    depths[node] = depth

        assert depths["A"] == 0
        assert depths["B"] == 1
        assert depths["C"] == 2
        assert depths["D"] == 3

    def test_depth_from_multiple_roots(self):
        """Test depth with multiple root nodes."""
        G = nx.DiGraph()
        G.add_edges_from([
            ("A", "C"),
            ("B", "C"),
            ("C", "D"),
        ])

        roots = [n for n in G.nodes() if G.in_degree(n) == 0]
        assert set(roots) == {"A", "B"}

        depths = {}
        for root in roots:
            for node, depth in nx.single_source_shortest_path_length(G, root).items():
                if node not in depths or depth < depths[node]:
                    depths[node] = depth

        assert depths["A"] == 0
        assert depths["B"] == 0
        assert depths["C"] == 1  # Min of paths from A and B
        assert depths["D"] == 2

    def test_depth_diamond_pattern(self):
        """Test depth calculation with diamond dependency pattern."""
        #     A
        #    / \
        #   B   C
        #    \ /
        #     D
        G = nx.DiGraph()
        G.add_edges_from([
            ("A", "B"),
            ("A", "C"),
            ("B", "D"),
            ("C", "D"),
        ])

        roots = [n for n in G.nodes() if G.in_degree(n) == 0]
        assert roots == ["A"]

        depths = {}
        for root in roots:
            for node, depth in nx.single_source_shortest_path_length(G, root).items():
                if node not in depths or depth < depths[node]:
                    depths[node] = depth

        assert depths["A"] == 0
        assert depths["B"] == 1
        assert depths["C"] == 1
        assert depths["D"] == 2  # Both paths have same length


class TestGraphStatistics:
    """Tests for graph statistics computation."""

    def test_basic_statistics(self):
        """Test computation of basic graph statistics."""
        G = nx.DiGraph()
        G.add_edges_from([
            ("A", "B"),
            ("A", "C"),
            ("B", "D"),
            ("C", "D"),
            ("D", "E"),
        ])

        stats = {
            "total_nodes": G.number_of_nodes(),
            "total_edges": G.number_of_edges(),
            "root_count": sum(1 for n in G.nodes() if G.in_degree(n) == 0),
            "leaf_count": sum(1 for n in G.nodes() if G.out_degree(n) == 0),
        }

        assert stats["total_nodes"] == 5
        assert stats["total_edges"] == 5
        assert stats["root_count"] == 1  # A
        assert stats["leaf_count"] == 1  # E

    def test_average_prerequisites(self):
        """Test average prerequisites per concept calculation."""
        G = nx.DiGraph()
        G.add_edges_from([
            ("A", "B"),
            ("A", "C"),
            ("B", "D"),
            ("C", "D"),
        ])

        in_degrees = [G.in_degree(n) for n in G.nodes()]
        avg_prereqs = sum(in_degrees) / len(in_degrees)

        # A: 0, B: 1, C: 1, D: 2
        expected_avg = (0 + 1 + 1 + 2) / 4
        assert avg_prereqs == expected_avg

    def test_max_depth_calculation(self):
        """Test maximum depth (longest path) calculation."""
        G = nx.DiGraph()
        G.add_edges_from([
            ("A", "B"),
            ("B", "C"),
            ("C", "D"),
            ("D", "E"),
        ])

        max_depth = nx.dag_longest_path_length(G)
        assert max_depth == 4  # A->B->C->D->E has length 4

    def test_orphan_detection(self):
        """Test detection of orphan nodes (isolated)."""
        G = nx.DiGraph()
        G.add_edges_from([
            ("A", "B"),
        ])
        G.add_node("C")  # Orphan

        orphans = [
            n for n in G.nodes()
            if G.in_degree(n) == 0 and G.out_degree(n) == 0
        ]

        assert orphans == ["C"]


class TestSectionHierarchyInference:
    """Tests for section hierarchy-based prerequisite inference."""

    def test_get_parent_section(self):
        """Test parent section extraction."""
        def get_parent_section(section_ref: str) -> str:
            parts = section_ref.split('.')
            if len(parts) <= 1:
                return None
            return '.'.join(parts[:-1])

        assert get_parent_section("3.2.1") == "3.2"
        assert get_parent_section("3.2") == "3"
        assert get_parent_section("3") is None
        assert get_parent_section("3.2.1.1") == "3.2.1"

    def test_hierarchy_inference_logic(self):
        """Test that hierarchy inference creates correct relationships."""
        # Simulate concepts with sections
        concepts = [
            {"id": "1", "section": "3"},
            {"id": "2", "section": "3.2"},
            {"id": "3", "section": "3.2.1"},
            {"id": "4", "section": "3.2.2"},
            {"id": "5", "section": "3.3"},
        ]

        section_map = {}
        for c in concepts:
            section = c["section"]
            if section not in section_map:
                section_map[section] = []
            section_map[section].append(c)

        edges = []
        for concept in concepts:
            section = concept["section"]
            parts = section.split('.')
            if len(parts) <= 1:
                continue
            parent_section = '.'.join(parts[:-1])
            parent_concepts = section_map.get(parent_section, [])
            for parent in parent_concepts:
                edges.append((parent["id"], concept["id"]))

        # Expected edges:
        # 3 -> 3.2 (1 -> 2)
        # 3 -> 3.3 (1 -> 5)
        # 3.2 -> 3.2.1 (2 -> 3)
        # 3.2 -> 3.2.2 (2 -> 4)
        assert ("1", "2") in edges
        assert ("1", "5") in edges
        assert ("2", "3") in edges
        assert ("2", "4") in edges
        assert len(edges) == 4


class TestCycleRemoval:
    """Tests for automatic cycle removal."""

    def test_remove_weakest_edge(self):
        """Test that weakest edge is removed to break cycle."""
        G = nx.DiGraph()
        G.add_edge("A", "B", strength=0.9)
        G.add_edge("B", "C", strength=0.5)  # Weakest
        G.add_edge("C", "A", strength=0.7)

        # Find and remove weakest edge in cycle
        cycle = nx.find_cycle(G)
        min_strength = float('inf')
        weakest_edge = None

        for u, v in cycle:
            if G.edges[u, v]['strength'] < min_strength:
                min_strength = G.edges[u, v]['strength']
                weakest_edge = (u, v)

        G.remove_edge(*weakest_edge)

        # Should now be valid DAG
        try:
            list(nx.topological_sort(G))
            is_valid = True
        except nx.NetworkXUnfeasible:
            is_valid = False

        assert is_valid
        assert weakest_edge == ("B", "C")
