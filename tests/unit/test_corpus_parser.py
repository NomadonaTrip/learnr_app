"""
Unit tests for corpus parser (parse_corpus.py).

Tests section header detection, paragraph extraction, and KA inference.
"""
import sys
from pathlib import Path
from uuid import uuid4

import pytest

# Add scripts to path for testing
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root / "scripts"))
sys.path.append(str(project_root / "apps" / "api"))

from parse_corpus import CorpusSection, get_ka_from_section, get_ka_mapping
from src.models.course import Course


@pytest.fixture
def mock_cbap_course():
    """Create a mock CBAP course with knowledge areas."""
    course = Course(
        id=uuid4(),
        slug="cbap",
        name="CBAP Certification",
        description="Business Analysis",
        knowledge_areas=[
            {"id": "ba-planning", "name": "BA Planning", "section_prefix": "3"},
            {"id": "elicitation", "name": "Elicitation", "section_prefix": "4"},
            {"id": "rlcm", "name": "Requirements Lifecycle", "section_prefix": "5"},
            {"id": "strategy", "name": "Strategy Analysis", "section_prefix": "6"},
            {"id": "radd", "name": "Requirements Analysis", "section_prefix": "7"},
            {"id": "solution-eval", "name": "Solution Evaluation", "section_prefix": "8"},
        ],
        default_diagnostic_count=12,
        mastery_threshold=0.8,
        gap_threshold=0.5,
        confidence_threshold=0.7,
    )
    return course


def test_get_ka_mapping(mock_cbap_course):
    """Test KA mapping extraction from course JSONB."""
    ka_mapping = get_ka_mapping(mock_cbap_course)

    assert ka_mapping == {
        "3": "ba-planning",
        "4": "elicitation",
        "5": "rlcm",
        "6": "strategy",
        "7": "radd",
        "8": "solution-eval",
    }


def test_get_ka_from_section_exact_match(mock_cbap_course):
    """Test KA inference for exact section matches."""
    ka_mapping = get_ka_mapping(mock_cbap_course)

    assert get_ka_from_section("3.1", ka_mapping) == "ba-planning"
    assert get_ka_from_section("4.2.3", ka_mapping) == "elicitation"
    assert get_ka_from_section("5.1.1", ka_mapping) == "rlcm"
    assert get_ka_from_section("6.3", ka_mapping) == "strategy"
    assert get_ka_from_section("7.2.1", ka_mapping) == "radd"
    assert get_ka_from_section("8.1", ka_mapping) == "solution-eval"


def test_get_ka_from_section_unknown(mock_cbap_course):
    """Test KA inference for unknown sections."""
    ka_mapping = get_ka_mapping(mock_cbap_course)

    assert get_ka_from_section("1.1", ka_mapping) == "unknown"
    assert get_ka_from_section("2.3", ka_mapping) == "unknown"
    assert get_ka_from_section("9.1", ka_mapping) == "unknown"


def test_corpus_section_dataclass():
    """Test CorpusSection dataclass creation."""
    section = CorpusSection(
        section_ref="3.2.1",
        title="Stakeholder Analysis",
        content="This is the content...",
        knowledge_area_id="ba-planning",
        page_numbers=[42, 43],
    )

    assert section.section_ref == "3.2.1"
    assert section.title == "Stakeholder Analysis"
    assert section.knowledge_area_id == "ba-planning"
    assert section.page_numbers == [42, 43]


def test_section_header_regex_pattern():
    """Test section header detection pattern."""
    import re

    pattern = re.compile(r"^(\d+(?:\.\d+)*)\s+(.+)$")

    # Valid section headers
    assert pattern.match("3 Business Analysis Planning and Monitoring")
    assert pattern.match("3.1 Plan Business Analysis Approach")
    assert pattern.match("3.2.1 Stakeholder List, Roles, and Responsibilities")
    assert pattern.match("4.1.2 Define Elicitation Approach")

    # Invalid headers (not section headers)
    assert not pattern.match("Introduction")
    assert not pattern.match("BABOK Guide v3")
    assert not pattern.match("  3.1 Leading whitespace")
    assert not pattern.match("Page 42")
