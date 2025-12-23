"""
Unit tests for TagClassifier.

Story 2.15: Secondary Tagging for Perspectives and Underlying Competencies
Tests tag classification with course-configurable keywords.
"""
import pytest
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "scripts"))

from import_vendor_questions import TagClassifier


class MockCourse:
    """Mock Course model for testing TagClassifier."""

    def __init__(
        self,
        perspectives: list[dict] | None = None,
        competencies: list[dict] | None = None,
    ):
        self.perspectives = perspectives
        self.competencies = competencies


# Test data: CBAP-style perspectives and competencies
CBAP_PERSPECTIVES = [
    {
        "id": "agile",
        "name": "Agile",
        "keywords": ["agile", "scrum", "kanban", "iterative", "adaptive"]
    },
    {
        "id": "bi",
        "name": "Business Intelligence",
        "keywords": ["bi", "business-intelligence", "analytics", "reporting"]
    },
    {
        "id": "it",
        "name": "Information Technology",
        "keywords": ["it", "information-technology", "software", "systems"]
    },
    {
        "id": "bpm",
        "name": "Business Process Management",
        "keywords": ["bpm", "business-process", "process-improvement", "workflow"]
    }
]

CBAP_COMPETENCIES = [
    {
        "id": "analytical",
        "name": "Analytical Thinking and Problem Solving",
        "keywords": ["analytical", "problem-solving", "critical-thinking", "decision-making"]
    },
    {
        "id": "behavioral",
        "name": "Behavioral Characteristics",
        "keywords": ["behavioral", "behavioural", "adaptability", "ethics"]
    },
    {
        "id": "communication",
        "name": "Communication Skills",
        "keywords": ["communication", "verbal", "written", "listening"]
    },
    {
        "id": "interaction",
        "name": "Interaction Skills",
        "keywords": ["interaction", "facilitation", "leadership", "negotiation"]
    }
]


class TestTagClassifierInitialization:
    """Tests for TagClassifier initialization from course config."""

    def test_init_with_perspectives_and_competencies(self):
        """Test initialization with both perspectives and competencies."""
        course = MockCourse(
            perspectives=CBAP_PERSPECTIVES,
            competencies=CBAP_COMPETENCIES,
        )
        classifier = TagClassifier(course)

        assert len(classifier.perspective_keywords) > 0
        assert len(classifier.competency_keywords) > 0
        assert "agile" in classifier.perspective_keywords
        assert "analytical" in classifier.competency_keywords

    def test_init_with_empty_config(self):
        """Test initialization with no perspectives or competencies."""
        course = MockCourse(perspectives=None, competencies=None)
        classifier = TagClassifier(course)

        assert len(classifier.perspective_keywords) == 0
        assert len(classifier.competency_keywords) == 0

    def test_init_with_perspectives_only(self):
        """Test initialization with only perspectives."""
        course = MockCourse(perspectives=CBAP_PERSPECTIVES, competencies=None)
        classifier = TagClassifier(course)

        assert len(classifier.perspective_keywords) > 0
        assert len(classifier.competency_keywords) == 0

    def test_init_builds_keyword_to_id_mapping(self):
        """Test that keyword to ID mapping is built correctly."""
        course = MockCourse(
            perspectives=CBAP_PERSPECTIVES,
            competencies=CBAP_COMPETENCIES,
        )
        classifier = TagClassifier(course)

        assert classifier.perspective_id_map.get("agile") == "agile"
        assert classifier.perspective_id_map.get("scrum") == "agile"
        assert classifier.competency_id_map.get("analytical") == "analytical"
        assert classifier.competency_id_map.get("problem-solving") == "analytical"


class TestTagClassification:
    """Tests for classify_tag method."""

    @pytest.fixture
    def classifier(self):
        """Create classifier with CBAP-style config."""
        course = MockCourse(
            perspectives=CBAP_PERSPECTIVES,
            competencies=CBAP_COMPETENCIES,
        )
        return TagClassifier(course)

    def test_classify_perspective_exact_match(self, classifier):
        """Test exact match for perspective keyword."""
        category, normalized, tag_id = classifier.classify_tag("agile")
        assert category == "perspective"
        assert tag_id == "agile"

    def test_classify_competency_exact_match(self, classifier):
        """Test exact match for competency keyword."""
        category, normalized, tag_id = classifier.classify_tag("analytical")
        assert category == "competency"
        assert tag_id == "analytical"

    def test_classify_concept_passthrough(self, classifier):
        """Test that non-matching tags pass through as concepts."""
        category, normalized, tag_id = classifier.classify_tag("Stakeholder-Analysis")
        assert category == "concept"
        assert tag_id is None

    def test_classify_partial_match_perspective(self, classifier):
        """Test partial matching for perspectives."""
        # "agile-methodology" contains "agile"
        category, normalized, tag_id = classifier.classify_tag("agile-methodology")
        assert category == "perspective"
        assert tag_id == "agile"

    def test_classify_partial_match_competency(self, classifier):
        """Test partial matching for competencies."""
        # "problem-solving-techniques" contains "problem-solving"
        category, normalized, tag_id = classifier.classify_tag("problem-solving-techniques")
        assert category == "competency"
        assert tag_id == "analytical"

    def test_classify_case_insensitive(self, classifier):
        """Test case insensitive matching."""
        category1, _, _ = classifier.classify_tag("AGILE")
        category2, _, _ = classifier.classify_tag("Analytical")
        category3, _, _ = classifier.classify_tag("BiZ-analytics")

        assert category1 == "perspective"
        assert category2 == "competency"
        assert category3 == "perspective"  # contains "analytics"

    def test_classify_underscore_normalization(self, classifier):
        """Test that underscores are converted to hyphens."""
        # "problem_solving" should match "problem-solving"
        category, normalized, tag_id = classifier.classify_tag("problem_solving")
        assert category == "competency"
        assert normalized == "problem-solving"

    def test_classify_whitespace_stripping(self, classifier):
        """Test that whitespace is stripped."""
        category, normalized, _ = classifier.classify_tag("  agile  ")
        assert category == "perspective"
        assert normalized == "agile"

    def test_classify_british_spelling(self, classifier):
        """Test British spelling variant (behavioural vs behavioral)."""
        category, _, tag_id = classifier.classify_tag("behavioural-characteristics")
        assert category == "competency"
        assert tag_id == "behavioral"


class TestTagsClassification:
    """Tests for classify_tags method (batch classification)."""

    @pytest.fixture
    def classifier(self):
        """Create classifier with CBAP-style config."""
        course = MockCourse(
            perspectives=CBAP_PERSPECTIVES,
            competencies=CBAP_COMPETENCIES,
        )
        return TagClassifier(course)

    def test_classify_tags_mixed(self, classifier):
        """Test classification of mixed tag list."""
        tags = [
            "Stakeholder-Analysis",  # concept
            "agile",                  # perspective
            "analytical",            # competency
            "Use-Case-Modeling",     # concept (doesn't match any keyword)
            "scrum",                 # perspective (same as agile)
            "communication",         # competency
        ]
        result = classifier.classify_tags(tags)

        assert "Stakeholder-Analysis" in result["concepts"]
        assert "Use-Case-Modeling" in result["concepts"]
        assert "agile" in result["perspectives"]
        assert "analytical" in result["competencies"]
        assert "communication" in result["competencies"]

    def test_classify_tags_deduplication(self, classifier):
        """Test that duplicate perspective/competency IDs are deduplicated."""
        tags = [
            "agile",
            "scrum",      # Both map to "agile" perspective
            "kanban",     # Also maps to "agile" perspective
        ]
        result = classifier.classify_tags(tags)

        # Should only have one "agile" entry
        assert result["perspectives"].count("agile") == 1

    def test_classify_tags_empty_input(self, classifier):
        """Test with empty tag list."""
        result = classifier.classify_tags([])

        assert result["concepts"] == []
        assert result["perspectives"] == []
        assert result["competencies"] == []

    def test_classify_tags_all_concepts(self, classifier):
        """Test when all tags are concepts (no matches)."""
        tags = [
            "Requirements-Documentation",
            "Use-Case-Modeling",
            "Data-Flow-Diagram",
        ]
        result = classifier.classify_tags(tags)

        assert len(result["concepts"]) == 3
        assert len(result["perspectives"]) == 0
        assert len(result["competencies"]) == 0

    def test_classify_tags_preserves_concept_original(self, classifier):
        """Test that concept tags preserve original casing."""
        tags = ["Stakeholder-Analysis", "DATA-FLOW-DIAGRAM"]
        result = classifier.classify_tags(tags)

        # Original tags should be preserved for concepts
        assert "Stakeholder-Analysis" in result["concepts"]
        assert "DATA-FLOW-DIAGRAM" in result["concepts"]


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_keyword_list(self):
        """Test with perspective that has empty keywords list."""
        course = MockCourse(
            perspectives=[{"id": "empty", "name": "Empty", "keywords": []}],
            competencies=None,
        )
        classifier = TagClassifier(course)

        # Should not crash, just have no keywords
        assert len(classifier.perspective_keywords) == 0

    def test_missing_keywords_field(self):
        """Test with perspective missing keywords field."""
        course = MockCourse(
            perspectives=[{"id": "missing", "name": "Missing Keywords"}],
            competencies=None,
        )
        classifier = TagClassifier(course)

        # Should handle gracefully
        assert len(classifier.perspective_keywords) == 0

    def test_missing_id_field(self):
        """Test with perspective missing id field."""
        course = MockCourse(
            perspectives=[{"name": "No ID", "keywords": ["test"]}],
            competencies=None,
        )
        classifier = TagClassifier(course)

        # Should handle gracefully (empty string ID)
        category, _, tag_id = classifier.classify_tag("test")
        assert category == "perspective"
        assert tag_id == ""  # Empty string since ID was missing

    def test_special_characters_in_tag(self):
        """Test tags with special characters."""
        course = MockCourse(
            perspectives=CBAP_PERSPECTIVES,
            competencies=CBAP_COMPETENCIES,
        )
        classifier = TagClassifier(course)

        # Should handle gracefully
        category, _, _ = classifier.classify_tag("agile/scrum")
        assert category == "perspective"


class TestCompetencyExtraction:
    """
    Tests for competency ID extraction.

    Story 2.16 Task 5b: Verify TagClassifier extracts competency IDs correctly.
    """

    @pytest.fixture
    def classifier(self):
        """Create classifier with CBAP competencies including conceptual-thinking."""
        competencies = [
            {
                "id": "analytical",
                "name": "Analytical Thinking and Problem Solving",
                "keywords": [
                    "analytical", "problem-solving", "critical-thinking",
                    "decision-making", "systems-thinking", "conceptual-thinking"
                ]
            },
            {
                "id": "behavioral",
                "name": "Behavioral Characteristics",
                "keywords": ["behavioral", "behavioural", "adaptability", "ethics"]
            },
            {
                "id": "communication",
                "name": "Communication Skills",
                "keywords": ["communication", "verbal", "written", "listening"]
            },
            {
                "id": "interaction",
                "name": "Interaction Skills",
                "keywords": ["interaction", "facilitation", "leadership", "negotiation"]
            }
        ]
        course = MockCourse(perspectives=None, competencies=competencies)
        return TagClassifier(course)

    def test_conceptual_thinking_extracts_analytical(self, classifier):
        """Test that 'Conceptual-Thinking' tag extracts 'analytical' competency ID."""
        result = classifier.classify_tags(["Conceptual-Thinking"])
        assert "analytical" in result["competencies"]

    def test_communication_skills_extracts_communication(self, classifier):
        """Test that 'Communication-Skills' tag extracts 'communication' competency ID."""
        result = classifier.classify_tags(["Communication-Skills"])
        assert "communication" in result["competencies"]

    def test_adaptability_extracts_behavioral(self, classifier):
        """Test that 'Adaptability' tag extracts 'behavioral' competency ID."""
        result = classifier.classify_tags(["Adaptability"])
        assert "behavioral" in result["competencies"]

    def test_multiple_competency_tags_extract_multiple_ids(self, classifier):
        """Test that multiple competency tags extract multiple IDs."""
        result = classifier.classify_tags([
            "Conceptual-Thinking",
            "Communication-Skills",
            "Adaptability"
        ])
        assert "analytical" in result["competencies"]
        assert "communication" in result["competencies"]
        assert "behavioral" in result["competencies"]
        assert len(result["competencies"]) == 3

    def test_systems_thinking_extracts_analytical(self, classifier):
        """Test that 'Systems-Thinking' tag extracts 'analytical' competency ID."""
        result = classifier.classify_tags(["Systems-Thinking"])
        assert "analytical" in result["competencies"]

    def test_written_communication_extracts_communication(self, classifier):
        """Test that 'Written-Communication' tag extracts 'communication' competency ID."""
        result = classifier.classify_tags(["Written-Communication"])
        assert "communication" in result["competencies"]

    def test_mixed_tags_with_competencies(self, classifier):
        """Test classification with mix of concepts and competencies."""
        result = classifier.classify_tags([
            "Stakeholder-Analysis",     # concept
            "Conceptual-Thinking",      # competency -> analytical
            "Use-Case-Modeling",        # concept
            "Communication-Skills",     # competency -> communication
        ])
        assert "Stakeholder-Analysis" in result["concepts"]
        assert "Use-Case-Modeling" in result["concepts"]
        assert "analytical" in result["competencies"]
        assert "communication" in result["competencies"]
        assert len(result["competencies"]) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
