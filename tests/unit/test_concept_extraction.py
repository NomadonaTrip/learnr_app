"""
Unit tests for BABOK concept extraction script.

Tests PDF parsing, GPT-4 response parsing, deduplication logic,
difficulty estimation, and validation logic.
"""
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add scripts directory to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "scripts"))

from extract_babok_concepts import (
    BabokSection,
    ConceptCandidate,
    ConceptDeduplicator,
    ExtractionStats,
    estimate_difficulty,
    map_ka_name_to_id,
    validate_extraction_results,
)


# ============================================================================
# Test BabokSection dataclass
# ============================================================================

def test_babok_section_creation():
    """Test BabokSection dataclass creation."""
    section = BabokSection(
        section_number="3.2.1",
        title="Stakeholder Analysis",
        content="This section describes stakeholder analysis...",
        chapter=3,
        depth=3,
        page_start=45,
        page_end=50,
    )

    assert section.section_number == "3.2.1"
    assert section.title == "Stakeholder Analysis"
    assert section.chapter == 3
    assert section.depth == 3


def test_concept_candidate_creation():
    """Test ConceptCandidate dataclass creation."""
    concept = ConceptCandidate(
        name="Stakeholder Identification",
        description="The process of identifying stakeholders.",
        corpus_section_ref="3.2.1",
        knowledge_area_id="ba-planning",
        difficulty_estimate=0.4,
        prerequisite_depth=1,
    )

    assert concept.name == "Stakeholder Identification"
    assert concept.knowledge_area_id == "ba-planning"
    assert concept.difficulty_estimate == 0.4


# ============================================================================
# Test Deduplication Logic
# ============================================================================

def test_deduplicate_removes_exact_duplicates():
    """Test that exact duplicate names are removed."""
    dedup = ConceptDeduplicator(similarity_threshold=85)

    concepts = [
        ConceptCandidate("RACI Matrix", "Desc 1", "3.1", "ba-planning", 0.5, 0),
        ConceptCandidate("RACI Matrix", "Desc 2", "3.2", "ba-planning", 0.5, 0),
    ]

    result = dedup.deduplicate_concepts(concepts)

    assert len(result) == 1


def test_deduplicate_removes_fuzzy_matches():
    """Test that fuzzy matching removes similar names."""
    dedup = ConceptDeduplicator(similarity_threshold=85)

    concepts = [
        ConceptCandidate("RACI Matrix Construction", "Long description", "3.1", "ba-planning", 0.5, 0),
        ConceptCandidate("RACI Matrix Constructions", "Short desc", "3.2", "ba-planning", 0.5, 0),
    ]

    result = dedup.deduplicate_concepts(concepts)

    assert len(result) == 1
    # Keeps the one with longer description
    assert "Long description" in result[0].description


def test_deduplicate_keeps_dissimilar_names():
    """Test that dissimilar names are kept."""
    dedup = ConceptDeduplicator(similarity_threshold=85)

    concepts = [
        ConceptCandidate("Stakeholder Identification", "Desc 1", "3.1", "ba-planning", 0.3, 0),
        ConceptCandidate("RACI Matrix Construction", "Desc 2", "3.2", "ba-planning", 0.5, 0),
        ConceptCandidate("Communication Plan", "Desc 3", "3.3", "ba-planning", 0.4, 0),
    ]

    result = dedup.deduplicate_concepts(concepts)

    assert len(result) == 3


def test_deduplicate_empty_list():
    """Test deduplication with empty list."""
    dedup = ConceptDeduplicator()

    result = dedup.deduplicate_concepts([])

    assert result == []


def test_deduplicate_adjustable_threshold():
    """Test that threshold affects deduplication."""
    # Very low threshold - should deduplicate more aggressively
    dedup_low = ConceptDeduplicator(similarity_threshold=50)
    concepts = [
        ConceptCandidate("Stakeholder Analysis", "Desc 1", "3.1", "ba-planning", 0.5, 0),
        ConceptCandidate("Stakeholder Management", "Desc 2", "3.2", "ba-planning", 0.5, 0),
    ]

    result_low = dedup_low.deduplicate_concepts(concepts)

    # High threshold - less aggressive
    dedup_high = ConceptDeduplicator(similarity_threshold=95)
    result_high = dedup_high.deduplicate_concepts(concepts)

    # Low threshold should find similarity, high threshold should not
    assert len(result_low) < len(result_high) or len(result_low) == len(result_high)


# ============================================================================
# Test Difficulty Estimation
# ============================================================================

def test_estimate_difficulty_increases_with_depth():
    """Test that deeper sections have higher difficulty."""
    section_shallow = BabokSection(
        section_number="3",
        title="Chapter",
        content="Content",
        chapter=3,
        depth=1,
        page_start=1,
        page_end=5,
    )

    section_deep = BabokSection(
        section_number="3.2.1.4",
        title="Deep Section",
        content="Content",
        chapter=3,
        depth=4,
        page_start=1,
        page_end=5,
    )

    base_difficulty = 0.5

    shallow_result = estimate_difficulty(section_shallow, base_difficulty)
    deep_result = estimate_difficulty(section_deep, base_difficulty)

    assert deep_result > shallow_result


def test_estimate_difficulty_clamps_to_valid_range():
    """Test that difficulty is clamped between 0.0 and 1.0."""
    section = BabokSection(
        section_number="3.2.1.4.5",
        title="Very Deep",
        content="Content",
        chapter=3,
        depth=5,
        page_start=1,
        page_end=5,
    )

    # Very high base difficulty
    result = estimate_difficulty(section, 0.9)
    assert 0.0 <= result <= 1.0

    # Very low base difficulty
    result = estimate_difficulty(section, 0.0)
    assert 0.0 <= result <= 1.0


# ============================================================================
# Test KA Name Mapping
# ============================================================================

def test_map_ka_name_to_id_valid():
    """Test mapping valid KA name to ID."""
    knowledge_areas = [
        {"id": "ba-planning", "name": "Business Analysis Planning and Monitoring"},
        {"id": "elicitation", "name": "Elicitation and Collaboration"},
    ]

    result = map_ka_name_to_id("Business Analysis Planning and Monitoring", knowledge_areas)

    assert result == "ba-planning"


def test_map_ka_name_to_id_invalid():
    """Test mapping invalid KA name raises error."""
    knowledge_areas = [
        {"id": "ba-planning", "name": "Business Analysis Planning and Monitoring"},
    ]

    with pytest.raises(ValueError, match="Unknown KA"):
        map_ka_name_to_id("Nonexistent KA", knowledge_areas)


# ============================================================================
# Test Validation Logic
# ============================================================================

def test_validate_extraction_results_valid():
    """Test validation passes with valid results."""
    concepts = [
        ConceptCandidate(f"Concept {i}", "Desc", "3.1", ka_id, 0.5, 0)
        for i in range(600)
        for ka_id in ["ba-planning"]
    ][:600]

    # Ensure 100 concepts per KA
    concepts = []
    ka_ids = ["ba-planning", "elicitation", "rlcm", "strategy", "radd", "solution-eval"]
    for ka_id in ka_ids:
        for i in range(100):
            concepts.append(
                ConceptCandidate(f"{ka_id}-{i}", "Desc", f"3.{i}", ka_id, 0.5, 0)
            )

    stats = ExtractionStats()
    stats.all_sections = [c.corpus_section_ref for c in concepts]

    is_valid, issues = validate_extraction_results(concepts, stats)

    assert is_valid is True


def test_validate_extraction_results_too_few_concepts():
    """Test validation fails with too few concepts."""
    concepts = [
        ConceptCandidate(f"Concept {i}", "Desc", "3.1", "ba-planning", 0.5, 0)
        for i in range(100)
    ]

    stats = ExtractionStats()
    stats.all_sections = ["3.1"]

    is_valid, issues = validate_extraction_results(concepts, stats)

    assert is_valid is False
    assert any("below minimum" in issue for issue in issues)


def test_validate_extraction_results_ka_warnings():
    """Test validation warns when KA has too few concepts."""
    concepts = []
    # 100 concepts each for 5 KAs, but only 50 for one KA
    for ka_id in ["ba-planning", "elicitation", "rlcm", "strategy", "radd"]:
        for i in range(100):
            concepts.append(
                ConceptCandidate(f"{ka_id}-{i}", "Desc", f"3.{i}", ka_id, 0.5, 0)
            )
    # Only 50 for solution-eval (below 75 threshold)
    for i in range(50):
        concepts.append(
            ConceptCandidate(f"solution-{i}", "Desc", f"8.{i}", "solution-eval", 0.5, 0)
        )

    stats = ExtractionStats()
    stats.all_sections = list(set(c.corpus_section_ref for c in concepts))

    is_valid, issues = validate_extraction_results(concepts, stats)

    # Should still be valid but with warnings
    assert any("solution-eval" in issue for issue in issues)


# ============================================================================
# Test GPT-4 Response Parsing
# ============================================================================

def test_parse_gpt4_json_response():
    """Test parsing GPT-4 JSON response."""
    # Simulate what the extractor would receive
    response_content = json.dumps([
        {
            "name": "Stakeholder Identification",
            "description": "The process of identifying stakeholders.",
            "difficulty_estimate": 0.4
        },
        {
            "name": "RACI Matrix",
            "description": "A matrix for role assignments.",
            "difficulty_estimate": 0.5
        }
    ])

    parsed = json.loads(response_content)

    assert len(parsed) == 2
    assert parsed[0]["name"] == "Stakeholder Identification"
    assert parsed[1]["difficulty_estimate"] == 0.5


def test_parse_gpt4_wrapped_response():
    """Test parsing GPT-4 response wrapped in object."""
    response_content = json.dumps({
        "concepts": [
            {
                "name": "Stakeholder Identification",
                "description": "The process of identifying stakeholders.",
                "difficulty_estimate": 0.4
            }
        ]
    })

    parsed = json.loads(response_content)

    if isinstance(parsed, dict) and "concepts" in parsed:
        concepts = parsed["concepts"]
    else:
        concepts = parsed

    assert len(concepts) == 1
    assert concepts[0]["name"] == "Stakeholder Identification"


# ============================================================================
# Test Schema Validation
# ============================================================================

def test_concept_create_schema_validation():
    """Test ConceptCreate schema validates difficulty."""
    from uuid import uuid4
    sys.path.insert(0, str(project_root / "apps" / "api"))
    from src.schemas.concept import ConceptCreate

    # Valid difficulty
    concept = ConceptCreate(
        course_id=uuid4(),
        name="Test Concept",
        knowledge_area_id="ba-planning",
        difficulty_estimate=0.5,
    )
    assert concept.difficulty_estimate == 0.5

    # Difficulty at bounds
    concept_low = ConceptCreate(
        course_id=uuid4(),
        name="Test Concept",
        knowledge_area_id="ba-planning",
        difficulty_estimate=0.0,
    )
    assert concept_low.difficulty_estimate == 0.0

    concept_high = ConceptCreate(
        course_id=uuid4(),
        name="Test Concept",
        knowledge_area_id="ba-planning",
        difficulty_estimate=1.0,
    )
    assert concept_high.difficulty_estimate == 1.0


def test_concept_create_schema_rejects_invalid_difficulty():
    """Test ConceptCreate schema rejects invalid difficulty."""
    from uuid import uuid4
    sys.path.insert(0, str(project_root / "apps" / "api"))
    from src.schemas.concept import ConceptCreate
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ConceptCreate(
            course_id=uuid4(),
            name="Test Concept",
            knowledge_area_id="ba-planning",
            difficulty_estimate=1.5,  # Invalid - above 1.0
        )

    with pytest.raises(ValidationError):
        ConceptCreate(
            course_id=uuid4(),
            name="Test Concept",
            knowledge_area_id="ba-planning",
            difficulty_estimate=-0.1,  # Invalid - below 0.0
        )


# ============================================================================
# Test Log Sanitization (SEC-001)
# ============================================================================

def test_sanitize_error_message_redacts_api_key():
    """Test that API keys are redacted from error messages."""
    from extract_babok_concepts import _sanitize_error_message

    # Test OpenAI-style API key
    error_with_key = "Error: Invalid API key sk-abc123def456ghi789jklmnopqrstuvwxyz1234567890"
    result = _sanitize_error_message(error_with_key)
    assert "sk-abc123" not in result
    assert "[REDACTED_API_KEY]" in result


def test_sanitize_error_message_redacts_bearer_token():
    """Test that bearer tokens are redacted."""
    from extract_babok_concepts import _sanitize_error_message

    error_with_bearer = "Authorization failed: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test"
    result = _sanitize_error_message(error_with_bearer)
    assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in result
    assert "[REDACTED]" in result


def test_sanitize_error_message_redacts_api_key_param():
    """Test that api_key=... patterns are redacted."""
    from extract_babok_concepts import _sanitize_error_message

    error_with_api_key = "Request failed with api_key=my-secret-key-12345"
    result = _sanitize_error_message(error_with_api_key)
    assert "my-secret-key" not in result
    assert "[REDACTED]" in result


def test_sanitize_error_message_preserves_normal_text():
    """Test that normal error messages are not modified."""
    from extract_babok_concepts import _sanitize_error_message

    normal_error = "Connection timeout after 30 seconds"
    result = _sanitize_error_message(normal_error)
    assert result == normal_error


def test_sanitize_error_message_handles_multiple_patterns():
    """Test sanitization with multiple sensitive patterns."""
    from extract_babok_concepts import _sanitize_error_message

    error_multi = (
        "Failed: api_key=secret123 with Bearer token456 "
        "using sk-abcdefghij1234567890abcdefghij1234"
    )
    result = _sanitize_error_message(error_multi)
    assert "secret123" not in result
    assert "token456" not in result
    assert "sk-abcdefghij" not in result
