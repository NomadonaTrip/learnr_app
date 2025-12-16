"""
Unit tests for concept linking logic (parse_corpus.py).

Tests exact match, parent match, and child match for concept-chunk linking.
"""
import sys
from pathlib import Path
from uuid import uuid4

import pytest

# Add scripts to path for testing
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root / "scripts"))
sys.path.append(str(project_root / "apps" / "api"))

from parse_corpus import link_chunk_to_concepts
from src.models.concept import Concept


@pytest.fixture
def course_id():
    """Generate a test course ID."""
    return uuid4()


@pytest.fixture
def other_course_id():
    """Generate another course ID for cross-course filtering."""
    return uuid4()


@pytest.fixture
def sample_concepts(course_id, other_course_id):
    """Create sample concepts for testing."""
    concepts = [
        # Course 1 concepts (main course)
        Concept(
            id=uuid4(),
            course_id=course_id,
            name="Business Analysis Planning",
            description="Overall BA planning process",
            corpus_section_ref="3",
            knowledge_area_id="ba-planning",
            difficulty_estimate=0.5,
            prerequisite_depth=0,
        ),
        Concept(
            id=uuid4(),
            course_id=course_id,
            name="Plan Business Analysis Approach",
            description="Planning the BA approach",
            corpus_section_ref="3.1",
            knowledge_area_id="ba-planning",
            difficulty_estimate=0.6,
            prerequisite_depth=1,
        ),
        Concept(
            id=uuid4(),
            course_id=course_id,
            name="Stakeholder List Creation",
            description="Creating stakeholder lists",
            corpus_section_ref="3.2.1",
            knowledge_area_id="ba-planning",
            difficulty_estimate=0.4,
            prerequisite_depth=2,
        ),
        Concept(
            id=uuid4(),
            course_id=course_id,
            name="RACI Matrix",
            description="RACI responsibility assignment",
            corpus_section_ref="3.2.1",
            knowledge_area_id="ba-planning",
            difficulty_estimate=0.5,
            prerequisite_depth=2,
        ),
        Concept(
            id=uuid4(),
            course_id=course_id,
            name="Stakeholder Analysis Techniques",
            description="Techniques for analyzing stakeholders",
            corpus_section_ref="3.2.1.1",
            knowledge_area_id="ba-planning",
            difficulty_estimate=0.7,
            prerequisite_depth=3,
        ),
        # Course 2 concepts (should not match)
        Concept(
            id=uuid4(),
            course_id=other_course_id,
            name="Other Course Concept",
            description="From different course",
            corpus_section_ref="3.2.1",
            knowledge_area_id="ba-planning",
            difficulty_estimate=0.5,
            prerequisite_depth=0,
        ),
    ]
    return concepts


def test_exact_match(sample_concepts, course_id):
    """Test exact section reference match."""
    chunk_section_ref = "3.2.1"

    matched_ids = link_chunk_to_concepts(chunk_section_ref, sample_concepts, course_id)

    # Should match concepts with exact ref "3.2.1"
    matched_refs = [
        c.corpus_section_ref
        for c in sample_concepts
        if c.id in matched_ids and c.course_id == course_id
    ]

    assert "3.2.1" in matched_refs
    # Should have multiple matches (Stakeholder List + RACI Matrix)
    exact_matches = [ref for ref in matched_refs if ref == "3.2.1"]
    assert len(exact_matches) >= 2


def test_parent_match(sample_concepts, course_id):
    """Test parent section match (chunk is child of concept)."""
    chunk_section_ref = "3.2.1"

    matched_ids = link_chunk_to_concepts(chunk_section_ref, sample_concepts, course_id)

    # Should match parent concepts: "3" (parent of 3.2.1)
    # Note: "3.1" is NOT a parent of "3.2.1", it's a sibling
    matched_concepts = [c for c in sample_concepts if c.id in matched_ids]
    matched_refs = [c.corpus_section_ref for c in matched_concepts]

    assert "3" in matched_refs  # Top-level parent
    assert "3.1" not in matched_refs  # Not a parent (it's a sibling)


def test_child_match(sample_concepts, course_id):
    """Test child section match (chunk is parent of concept)."""
    chunk_section_ref = "3.2"

    matched_ids = link_chunk_to_concepts(chunk_section_ref, sample_concepts, course_id)

    # Should match child concepts: "3.2.1" and "3.2.1.1"
    matched_concepts = [c for c in sample_concepts if c.id in matched_ids]
    matched_refs = [c.corpus_section_ref for c in matched_concepts]

    assert "3.2.1" in matched_refs  # Direct child
    assert "3.2.1.1" in matched_refs  # Grandchild


def test_course_filtering(sample_concepts, course_id, other_course_id):
    """Test that only concepts from same course are matched."""
    chunk_section_ref = "3.2.1"

    matched_ids = link_chunk_to_concepts(chunk_section_ref, sample_concepts, course_id)

    # All matched concepts should be from course_id, not other_course_id
    matched_concepts = [c for c in sample_concepts if c.id in matched_ids]

    for concept in matched_concepts:
        assert concept.course_id == course_id
        assert concept.course_id != other_course_id


def test_no_match(sample_concepts, course_id):
    """Test when no concepts match the chunk section."""
    chunk_section_ref = "9.9.9"  # Non-existent section

    matched_ids = link_chunk_to_concepts(chunk_section_ref, sample_concepts, course_id)

    assert len(matched_ids) == 0


def test_concepts_without_section_ref(course_id):
    """Test that concepts without corpus_section_ref are skipped."""
    concepts = [
        Concept(
            id=uuid4(),
            course_id=course_id,
            name="Concept Without Section",
            description="No section reference",
            corpus_section_ref=None,  # No section ref
            knowledge_area_id="ba-planning",
            difficulty_estimate=0.5,
            prerequisite_depth=0,
        ),
    ]

    chunk_section_ref = "3.2.1"
    matched_ids = link_chunk_to_concepts(chunk_section_ref, concepts, course_id)

    assert len(matched_ids) == 0


def test_hierarchical_matching(sample_concepts, course_id):
    """Test full hierarchical matching (all levels)."""
    chunk_section_ref = "3.2.1.1"

    matched_ids = link_chunk_to_concepts(chunk_section_ref, sample_concepts, course_id)

    matched_concepts = [c for c in sample_concepts if c.id in matched_ids]
    matched_refs = [c.corpus_section_ref for c in matched_concepts]

    # Should match:
    # - Exact: 3.2.1.1
    # - Parents: 3.2.1, 3 (note: 3.2 not in sample data, 3.1 is sibling not parent)
    assert "3.2.1.1" in matched_refs  # Exact
    assert "3.2.1" in matched_refs  # Direct parent
    assert "3" in matched_refs  # Root parent
    # Note: "3.1" should NOT match as it's not in the parent hierarchy


def test_multiple_exact_matches(course_id):
    """Test when multiple concepts have same section ref."""
    concepts = [
        Concept(
            id=uuid4(),
            course_id=course_id,
            name="Concept A",
            description="First concept",
            corpus_section_ref="3.2.1",
            knowledge_area_id="ba-planning",
            difficulty_estimate=0.5,
            prerequisite_depth=0,
        ),
        Concept(
            id=uuid4(),
            course_id=course_id,
            name="Concept B",
            description="Second concept",
            corpus_section_ref="3.2.1",
            knowledge_area_id="ba-planning",
            difficulty_estimate=0.6,
            prerequisite_depth=0,
        ),
        Concept(
            id=uuid4(),
            course_id=course_id,
            name="Concept C",
            description="Third concept",
            corpus_section_ref="3.2.1",
            knowledge_area_id="ba-planning",
            difficulty_estimate=0.7,
            prerequisite_depth=0,
        ),
    ]

    chunk_section_ref = "3.2.1"
    matched_ids = link_chunk_to_concepts(chunk_section_ref, concepts, course_id)

    # Should match all 3 concepts
    assert len(matched_ids) == 3
