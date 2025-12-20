"""
Unit tests for KAMapper.

Story 2.16: Non-Conventional KA Mapping for Import
Tests KA mapping for perspectives and underlying competencies.
"""
import pytest
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "scripts"))

from import_vendor_questions import KAMapper


class MockCourse:
    """Mock Course model for testing KAMapper."""

    def __init__(self, perspectives: list[dict] | None = None):
        self.perspectives = perspectives


# Test data: CBAP-style perspectives with primary_ka mapping
CBAP_PERSPECTIVES = [
    {
        "id": "agile",
        "name": "Agile",
        "primary_ka": "strategy",
        "keywords": ["agile", "scrum", "kanban"]
    },
    {
        "id": "bi",
        "name": "Business Intelligence",
        "primary_ka": "solution-eval",
        "keywords": ["bi", "business-intelligence", "analytics"]
    },
    {
        "id": "it",
        "name": "Information Technology",
        "primary_ka": "radd",
        "keywords": ["it", "information-technology", "software"]
    },
    {
        "id": "bpm",
        "name": "Business Process Management",
        "primary_ka": "radd",
        "keywords": ["bpm", "business-process", "process-improvement"]
    },
    {
        "id": "ba",
        "name": "Business Architecture",
        "primary_ka": "strategy",
        "keywords": ["business-architecture", "capability", "value-stream"]
    }
]


class TestKAMapperInitialization:
    """Tests for KAMapper initialization from course config."""

    def test_init_with_perspectives(self):
        """Test initialization with perspectives containing primary_ka."""
        course = MockCourse(perspectives=CBAP_PERSPECTIVES)
        mapper = KAMapper(course)

        assert len(mapper.perspective_to_ka) == 5
        assert mapper.perspective_to_ka["agile"] == "strategy"
        assert mapper.perspective_to_ka["bi"] == "solution-eval"
        assert mapper.perspective_to_ka["it"] == "radd"
        assert mapper.perspective_to_ka["bpm"] == "radd"
        assert mapper.perspective_to_ka["ba"] == "strategy"

    def test_init_with_no_perspectives(self):
        """Test initialization with no perspectives."""
        course = MockCourse(perspectives=None)
        mapper = KAMapper(course)

        assert len(mapper.perspective_to_ka) == 0
        assert len(mapper.perspective_name_to_id) == 0

    def test_init_builds_name_variants(self):
        """Test that multiple name variants are registered for matching."""
        course = MockCourse(perspectives=CBAP_PERSPECTIVES)
        mapper = KAMapper(course)

        # Check multiple variants are registered
        assert "agile" in mapper.perspective_name_to_id
        assert "agile perspective" in mapper.perspective_name_to_id
        assert mapper.perspective_name_to_id["agile"] == "agile"
        assert mapper.perspective_name_to_id["agile perspective"] == "agile"

    def test_init_missing_primary_ka_defaults(self):
        """Test that missing primary_ka defaults to ba-planning."""
        course = MockCourse(perspectives=[
            {"id": "test", "name": "Test", "keywords": ["test"]}
        ])
        mapper = KAMapper(course)

        assert mapper.perspective_to_ka["test"] == "ba-planning"


class TestIsNonConventionalKA:
    """Tests for is_non_conventional_ka method."""

    @pytest.fixture
    def mapper(self):
        """Create mapper with CBAP-style config."""
        course = MockCourse(perspectives=CBAP_PERSPECTIVES)
        return KAMapper(course)

    def test_underlying_competencies_exact(self, mapper):
        """Test exact match for 'Underlying Competencies'."""
        assert mapper.is_non_conventional_ka("Underlying Competencies") is True

    def test_underlying_competencies_case_insensitive(self, mapper):
        """Test case insensitivity for 'Underlying Competencies' (AC 14)."""
        assert mapper.is_non_conventional_ka("underlying competencies") is True
        assert mapper.is_non_conventional_ka("UNDERLYING COMPETENCIES") is True
        assert mapper.is_non_conventional_ka("Underlying competencies") is True

    def test_underlying_competencies_whitespace(self, mapper):
        """Test whitespace normalization for 'Underlying Competencies' (AC 16)."""
        assert mapper.is_non_conventional_ka("  Underlying Competencies  ") is True

    def test_perspective_exact_match(self, mapper):
        """Test exact match for perspective names."""
        assert mapper.is_non_conventional_ka("Agile") is True
        assert mapper.is_non_conventional_ka("Business Intelligence") is True

    def test_perspective_with_suffix(self, mapper):
        """Test perspective names with 'Perspective' suffix (AC 15)."""
        assert mapper.is_non_conventional_ka("Agile Perspective") is True
        assert mapper.is_non_conventional_ka("Business Intelligence Perspective") is True
        assert mapper.is_non_conventional_ka("Information Technology Perspective") is True
        assert mapper.is_non_conventional_ka("Business Process Management Perspective") is True
        assert mapper.is_non_conventional_ka("Business Architecture Perspective") is True

    def test_perspective_case_insensitive(self, mapper):
        """Test case insensitivity for perspectives (AC 14)."""
        assert mapper.is_non_conventional_ka("AGILE PERSPECTIVE") is True
        assert mapper.is_non_conventional_ka("agile perspective") is True
        assert mapper.is_non_conventional_ka("Agile perspective") is True

    def test_perspective_whitespace(self, mapper):
        """Test whitespace normalization for perspectives (AC 16)."""
        assert mapper.is_non_conventional_ka("  Agile Perspective  ") is True
        assert mapper.is_non_conventional_ka("  Business Intelligence  ") is True

    def test_standard_kas_return_false(self, mapper):
        """Test standard 6 KAs return False."""
        assert mapper.is_non_conventional_ka("Strategy Analysis") is False
        assert mapper.is_non_conventional_ka("Elicitation and Collaboration") is False
        assert mapper.is_non_conventional_ka("Requirements Life Cycle Management") is False
        assert mapper.is_non_conventional_ka("Solution Evaluation") is False
        assert mapper.is_non_conventional_ka("Requirements Analysis and Design Definition") is False
        assert mapper.is_non_conventional_ka("BA Planning and Monitoring") is False

    def test_unknown_perspective_like_returns_false(self, mapper):
        """Test unknown values return False (AC 17 - handled in map_ka)."""
        assert mapper.is_non_conventional_ka("Unknown Perspective") is False
        assert mapper.is_non_conventional_ka("Random Value") is False


class TestInferKAFromTags:
    """Tests for infer_ka_from_tags method (AC 8-13)."""

    @pytest.fixture
    def mapper(self):
        """Create mapper with CBAP-style config."""
        course = MockCourse(perspectives=CBAP_PERSPECTIVES)
        return KAMapper(course)

    def test_elicitation_keywords(self, mapper):
        """Test elicitation keyword detection (AC 8)."""
        assert mapper.infer_ka_from_tags(["elicitation-techniques"]) == "elicitation"
        assert mapper.infer_ka_from_tags(["interview-skills"]) == "elicitation"
        assert mapper.infer_ka_from_tags(["workshop-facilitation"]) == "elicitation"
        assert mapper.infer_ka_from_tags(["collaboration-methods"]) == "elicitation"
        assert mapper.infer_ka_from_tags(["communication-skills"]) == "elicitation"
        assert mapper.infer_ka_from_tags(["facilitation"]) == "elicitation"
        assert mapper.infer_ka_from_tags(["active-listening"]) == "elicitation"

    def test_strategy_keywords(self, mapper):
        """Test strategy keyword detection (AC 9)."""
        assert mapper.infer_ka_from_tags(["strategy-planning"]) == "strategy"
        assert mapper.infer_ka_from_tags(["conceptual-thinking"]) == "strategy"
        assert mapper.infer_ka_from_tags(["systems-thinking"]) == "strategy"
        assert mapper.infer_ka_from_tags(["business-acumen"]) == "strategy"
        assert mapper.infer_ka_from_tags(["industry-knowledge"]) == "strategy"
        assert mapper.infer_ka_from_tags(["organization-knowledge"]) == "strategy"
        assert mapper.infer_ka_from_tags(["vision-alignment"]) == "strategy"

    def test_rlcm_keywords(self, mapper):
        """Test RLCM keyword detection (AC 10)."""
        assert mapper.infer_ka_from_tags(["decision-making"]) == "rlcm"
        assert mapper.infer_ka_from_tags(["prioritization"]) == "rlcm"
        assert mapper.infer_ka_from_tags(["prioritize-requirements"]) == "rlcm"
        assert mapper.infer_ka_from_tags(["approval-process"]) == "rlcm"
        assert mapper.infer_ka_from_tags(["traceability-matrix"]) == "rlcm"
        assert mapper.infer_ka_from_tags(["change-management"]) == "rlcm"
        assert mapper.infer_ka_from_tags(["governance"]) == "rlcm"
        assert mapper.infer_ka_from_tags(["baseline-management"]) == "rlcm"

    def test_radd_keywords(self, mapper):
        """Test RADD keyword detection (AC 11)."""
        assert mapper.infer_ka_from_tags(["data-modeling"]) == "radd"
        assert mapper.infer_ka_from_tags(["design-patterns"]) == "radd"
        assert mapper.infer_ka_from_tags(["data-analysis"]) == "radd"
        assert mapper.infer_ka_from_tags(["requirements-analysis"]) == "radd"
        assert mapper.infer_ka_from_tags(["specification-document"]) == "radd"
        assert mapper.infer_ka_from_tags(["use-case-diagram"]) == "radd"
        assert mapper.infer_ka_from_tags(["prototype-development"]) == "radd"

    def test_solution_eval_keywords(self, mapper):
        """Test solution-eval keyword detection (AC 12)."""
        assert mapper.infer_ka_from_tags(["evaluation-criteria"]) == "solution-eval"
        assert mapper.infer_ka_from_tags(["metric-definition"]) == "solution-eval"
        # Note: "performance-analysis" matches "analysis" (RADD) first due to check order
        assert mapper.infer_ka_from_tags(["performance-review"]) == "solution-eval"
        assert mapper.infer_ka_from_tags(["assessment-methods"]) == "solution-eval"
        assert mapper.infer_ka_from_tags(["measure-success"]) == "solution-eval"
        assert mapper.infer_ka_from_tags(["kpi-tracking"]) == "solution-eval"

    def test_default_fallback(self, mapper):
        """Test default fallback to ba-planning (AC 13)."""
        assert mapper.infer_ka_from_tags(["unknown-tag"]) == "ba-planning"
        assert mapper.infer_ka_from_tags(["random-concept"]) == "ba-planning"
        assert mapper.infer_ka_from_tags([]) == "ba-planning"

    def test_case_insensitive_matching(self, mapper):
        """Test case insensitive keyword matching."""
        assert mapper.infer_ka_from_tags(["ELICITATION"]) == "elicitation"
        assert mapper.infer_ka_from_tags(["Strategy-Analysis"]) == "strategy"
        assert mapper.infer_ka_from_tags(["DECISION-MAKING"]) == "rlcm"

    def test_multiple_tags_first_match_wins(self, mapper):
        """Test that first matching keyword wins."""
        # Elicitation comes before Strategy in the check order
        assert mapper.infer_ka_from_tags(["elicitation", "strategy"]) == "elicitation"

    def test_partial_keyword_matching(self, mapper):
        """Test partial keyword matching in tags."""
        # "prioritize" matches "prioritiz" pattern
        assert mapper.infer_ka_from_tags(["how-to-prioritize"]) == "rlcm"


class TestMapKA:
    """Tests for map_ka method."""

    @pytest.fixture
    def mapper(self):
        """Create mapper with CBAP-style config."""
        course = MockCourse(perspectives=CBAP_PERSPECTIVES)
        return KAMapper(course)

    def test_map_agile_perspective(self, mapper):
        """Test mapping Agile Perspective to strategy."""
        ka_id, persp_id = mapper.map_ka("Agile Perspective", [])
        assert ka_id == "strategy"
        assert persp_id == "agile"

    def test_map_bi_perspective(self, mapper):
        """Test mapping Business Intelligence Perspective to solution-eval."""
        ka_id, persp_id = mapper.map_ka("Business Intelligence Perspective", [])
        assert ka_id == "solution-eval"
        assert persp_id == "bi"

    def test_map_it_perspective(self, mapper):
        """Test mapping Information Technology Perspective to radd."""
        ka_id, persp_id = mapper.map_ka("Information Technology Perspective", [])
        assert ka_id == "radd"
        assert persp_id == "it"

    def test_map_bpm_perspective(self, mapper):
        """Test mapping Business Process Management Perspective to radd."""
        ka_id, persp_id = mapper.map_ka("Business Process Management Perspective", [])
        assert ka_id == "radd"
        assert persp_id == "bpm"

    def test_map_ba_perspective(self, mapper):
        """Test mapping Business Architecture Perspective to strategy."""
        ka_id, persp_id = mapper.map_ka("Business Architecture Perspective", [])
        assert ka_id == "strategy"
        assert persp_id == "ba"

    def test_map_partial_perspective_name(self, mapper):
        """Test mapping partial perspective name without 'Perspective' suffix (AC 15)."""
        ka_id, persp_id = mapper.map_ka("Agile", [])
        assert ka_id == "strategy"
        assert persp_id == "agile"

        ka_id, persp_id = mapper.map_ka("Business Intelligence", [])
        assert ka_id == "solution-eval"
        assert persp_id == "bi"

    def test_map_underlying_competencies_with_elicitation_tags(self, mapper):
        """Test mapping Underlying Competencies with elicitation tags."""
        ka_id, persp_id = mapper.map_ka(
            "Underlying Competencies",
            ["Communication-Skills", "Facilitation"]
        )
        assert ka_id == "elicitation"
        assert persp_id is None  # competency IDs come from TagClassifier

    def test_map_underlying_competencies_with_strategy_tags(self, mapper):
        """Test mapping Underlying Competencies with strategy tags."""
        ka_id, persp_id = mapper.map_ka(
            "Underlying Competencies",
            ["Conceptual-Thinking", "Systems-Thinking"]
        )
        assert ka_id == "strategy"
        assert persp_id is None

    def test_map_underlying_competencies_with_rlcm_tags(self, mapper):
        """Test mapping Underlying Competencies with RLCM tags."""
        ka_id, persp_id = mapper.map_ka(
            "Underlying Competencies",
            ["Decision-Making", "Prioritization"]
        )
        assert ka_id == "rlcm"
        assert persp_id is None

    def test_map_underlying_competencies_with_radd_tags(self, mapper):
        """Test mapping Underlying Competencies with RADD tags."""
        ka_id, persp_id = mapper.map_ka(
            "Underlying Competencies",
            ["Visual-Thinking", "Data-Modeling"]
        )
        assert ka_id == "radd"
        assert persp_id is None

    def test_map_underlying_competencies_with_solution_eval_tags(self, mapper):
        """Test mapping Underlying Competencies with solution-eval tags."""
        ka_id, persp_id = mapper.map_ka(
            "Underlying Competencies",
            ["Performance-Metrics", "Evaluation-Criteria"]
        )
        assert ka_id == "solution-eval"
        assert persp_id is None

    def test_map_underlying_competencies_fallback(self, mapper):
        """Test mapping Underlying Competencies fallback to ba-planning."""
        ka_id, persp_id = mapper.map_ka(
            "Underlying Competencies",
            ["Adaptability", "Ethics"]
        )
        assert ka_id == "ba-planning"
        assert persp_id is None

    def test_map_underlying_competencies_empty_tags(self, mapper):
        """Test mapping Underlying Competencies with no tags."""
        ka_id, persp_id = mapper.map_ka("Underlying Competencies", [])
        assert ka_id == "ba-planning"  # fallback
        assert persp_id is None

    def test_map_case_insensitive(self, mapper):
        """Test case insensitive mapping (AC 14)."""
        ka_id1, _ = mapper.map_ka("AGILE PERSPECTIVE", [])
        ka_id2, _ = mapper.map_ka("agile perspective", [])
        ka_id3, _ = mapper.map_ka("Agile Perspective", [])

        assert ka_id1 == ka_id2 == ka_id3 == "strategy"

    def test_map_whitespace_normalized(self, mapper):
        """Test whitespace normalization (AC 16)."""
        ka_id, persp_id = mapper.map_ka("  Agile Perspective  ", [])
        assert ka_id == "strategy"
        assert persp_id == "agile"

    def test_map_unknown_perspective_fallback(self, mapper):
        """Test unknown perspective-like KA falls back to ba-planning (AC 17)."""
        ka_id, persp_id = mapper.map_ka("Unknown Perspective", [])
        assert ka_id == "ba-planning"
        assert persp_id is None


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_perspectives_config(self):
        """Test with no perspectives configured."""
        course = MockCourse(perspectives=None)
        mapper = KAMapper(course)

        # Should still handle Underlying Competencies
        assert mapper.is_non_conventional_ka("Underlying Competencies") is True

        ka_id, persp_id = mapper.map_ka(
            "Underlying Competencies",
            ["Communication-Skills"]
        )
        assert ka_id == "elicitation"
        assert persp_id is None

    def test_perspective_without_primary_ka(self):
        """Test perspective missing primary_ka defaults correctly."""
        course = MockCourse(perspectives=[
            {"id": "custom", "name": "Custom", "keywords": ["custom"]}
        ])
        mapper = KAMapper(course)

        ka_id, persp_id = mapper.map_ka("Custom Perspective", [])
        assert ka_id == "ba-planning"  # Default
        assert persp_id == "custom"

    def test_special_characters_in_ka_name(self):
        """Test handling of special characters in KA name."""
        course = MockCourse(perspectives=CBAP_PERSPECTIVES)
        mapper = KAMapper(course)

        # Should handle gracefully
        assert mapper.is_non_conventional_ka("Agile/Scrum") is False
        assert mapper.is_non_conventional_ka("Agile-Perspective") is False

    def test_very_long_ka_name(self):
        """Test handling of very long KA names."""
        course = MockCourse(perspectives=CBAP_PERSPECTIVES)
        mapper = KAMapper(course)

        long_name = "A" * 1000
        assert mapper.is_non_conventional_ka(long_name) is False

    def test_numeric_ka_name(self):
        """Test handling of numeric KA names."""
        course = MockCourse(perspectives=CBAP_PERSPECTIVES)
        mapper = KAMapper(course)

        assert mapper.is_non_conventional_ka("123") is False

    def test_empty_ka_name(self):
        """Test handling of empty KA name."""
        course = MockCourse(perspectives=CBAP_PERSPECTIVES)
        mapper = KAMapper(course)

        assert mapper.is_non_conventional_ka("") is False
        assert mapper.is_non_conventional_ka("   ") is False


class TestSampleCSVData:
    """Tests based on sample CSV data from Story 2.16."""

    @pytest.fixture
    def mapper(self):
        """Create mapper with CBAP-style config."""
        course = MockCourse(perspectives=CBAP_PERSPECTIVES)
        return KAMapper(course)

    def test_sample_csv_agile_perspective(self, mapper):
        """Test sample CSV: Agile Perspective -> strategy."""
        assert mapper.is_non_conventional_ka("Agile Perspective") is True
        ka_id, persp_id = mapper.map_ka("Agile Perspective", [])
        assert ka_id == "strategy"
        assert persp_id == "agile"

    def test_sample_csv_business_intelligence_perspective(self, mapper):
        """Test sample CSV: Business Intelligence Perspective -> solution-eval."""
        assert mapper.is_non_conventional_ka("Business Intelligence Perspective") is True
        ka_id, persp_id = mapper.map_ka("Business Intelligence Perspective", [])
        assert ka_id == "solution-eval"
        assert persp_id == "bi"

    def test_sample_csv_bpm_perspective(self, mapper):
        """Test sample CSV: Business Process Management Perspective -> radd."""
        assert mapper.is_non_conventional_ka("Business Process Management Perspective") is True
        ka_id, persp_id = mapper.map_ka("Business Process Management Perspective", [])
        assert ka_id == "radd"
        assert persp_id == "bpm"

    def test_sample_csv_it_perspective(self, mapper):
        """Test sample CSV: Information Technology Perspective -> radd."""
        assert mapper.is_non_conventional_ka("Information Technology Perspective") is True
        ka_id, persp_id = mapper.map_ka("Information Technology Perspective", [])
        assert ka_id == "radd"
        assert persp_id == "it"

    def test_sample_csv_ba_perspective(self, mapper):
        """Test sample CSV: Business Architecture Perspective -> strategy."""
        assert mapper.is_non_conventional_ka("Business Architecture Perspective") is True
        ka_id, persp_id = mapper.map_ka("Business Architecture Perspective", [])
        assert ka_id == "strategy"
        assert persp_id == "ba"

    def test_sample_csv_underlying_competencies_analytical(self, mapper):
        """Test sample CSV: Underlying Competencies with Conceptual-Thinking."""
        ka_id, _ = mapper.map_ka(
            "Underlying Competencies",
            ["Conceptual-Thinking", "Strategy-Alignment"]
        )
        assert ka_id == "strategy"  # conceptual matches strategy

    def test_sample_csv_underlying_competencies_communication(self, mapper):
        """Test sample CSV: Underlying Competencies with Communication-Skills."""
        ka_id, _ = mapper.map_ka(
            "Underlying Competencies",
            ["Communication-Skills", "Written-Communication"]
        )
        assert ka_id == "elicitation"  # communication matches elicitation

    def test_sample_csv_underlying_competencies_systems_thinking(self, mapper):
        """Test sample CSV: Underlying Competencies with Systems-Thinking."""
        ka_id, _ = mapper.map_ka(
            "Underlying Competencies",
            ["Systems-Thinking", "Visual-Thinking"]
        )
        assert ka_id == "strategy"  # systems-thinking matches strategy

    def test_sample_csv_underlying_competencies_adaptability(self, mapper):
        """Test sample CSV: Underlying Competencies with Adaptability."""
        ka_id, _ = mapper.map_ka(
            "Underlying Competencies",
            ["Adaptability", "Methodology-Knowledge"]
        )
        assert ka_id == "ba-planning"  # no match, fallback


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
