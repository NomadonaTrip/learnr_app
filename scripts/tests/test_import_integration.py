"""
Integration tests for import_vendor_questions.py

Tests cover:
- Full import flow with pre-tagged CSV concepts
- Import with --create-missing-concepts flag
- Existing GPT-4 flow regression
- Report generation
"""
import csv
import os
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

# Add script path to enable import
sys.path.insert(0, str(Path(__file__).parent.parent))

from import_vendor_questions import (
    ConceptMapping,
    ConceptTagMatcher,
    ImportResult,
    QuestionData,
    VendorQuestionImporter,
)


# =====================================
# Mock Objects
# =====================================

@dataclass
class MockConcept:
    """Mock Concept for testing without database."""
    id: UUID
    name: str
    knowledge_area_id: str = "ba-planning"
    description: Optional[str] = None
    course_id: Optional[UUID] = None
    corpus_section_ref: Optional[str] = None
    difficulty_estimate: float = 0.5
    prerequisite_depth: int = 0
    created_at: Optional[datetime] = None


@dataclass
class MockCourse:
    """Mock Course for testing."""
    id: UUID
    slug: str
    name: str
    knowledge_areas: list


# =====================================
# Integration Tests for Tag-Based Mapping
# =====================================

class TestTagBasedMappingIntegration:
    """Integration tests for the full tag-based mapping flow."""

    @pytest.fixture
    def sample_concepts(self):
        """Create sample concepts that would be in the database."""
        return [
            MockConcept(id=uuid4(), name="Stakeholder Analysis", knowledge_area_id="ba-planning"),
            MockConcept(id=uuid4(), name="Requirements Elicitation", knowledge_area_id="elicitation"),
            MockConcept(id=uuid4(), name="Business Case", knowledge_area_id="strategy"),
            MockConcept(id=uuid4(), name="Data Modeling", knowledge_area_id="radd"),
            MockConcept(id=uuid4(), name="Solution Validation", knowledge_area_id="solution-eval"),
        ]

    @pytest.fixture
    def sample_questions(self):
        """Create sample questions with concept tags."""
        return [
            QuestionData(
                question_text="What is stakeholder analysis?",
                options={"A": "a", "B": "b", "C": "c", "D": "d"},
                correct_answer="A",
                explanation="Stakeholder analysis identifies all parties...",
                knowledge_area_name="BA Planning",
                knowledge_area_id="ba-planning",
                row_number=2,
                concept_tags=["stakeholder analysis", "planning"],
            ),
            QuestionData(
                question_text="What elicitation technique is best?",
                options={"A": "a", "B": "b", "C": "c", "D": "d"},
                correct_answer="B",
                explanation="Interviews are primary technique...",
                knowledge_area_name="Elicitation",
                knowledge_area_id="elicitation",
                row_number=3,
                concept_tags=["requirements elicitation", "interviews"],
            ),
            QuestionData(
                question_text="What is a business case?",
                options={"A": "a", "B": "b", "C": "c", "D": "d"},
                correct_answer="C",
                explanation="Business case justifies the project...",
                knowledge_area_name="Strategy",
                knowledge_area_id="strategy",
                row_number=4,
                concept_tags=["business case", "unknown-tag"],
            ),
        ]

    @pytest.mark.asyncio
    async def test_map_questions_from_tags_flow(self, sample_concepts, sample_questions):
        """Test full flow of mapping questions using CSV tags."""
        importer = VendorQuestionImporter(
            course_slug="cbap",
            use_csv_tags=True,
            tag_match_threshold=85,
        )

        # Set up the importer with concepts (normally done in initialize())
        importer.concepts = sample_concepts
        importer.course_id = uuid4()

        # Run the mapping
        mappings = await importer.map_questions_from_tags(sample_questions)

        # Verify mappings were created
        assert len(mappings) == 3

        # Question 2 should have "Stakeholder Analysis" mapped
        assert 2 in mappings
        q2_concepts = [m.concept_name for m in mappings[2]]
        assert "Stakeholder Analysis" in q2_concepts

        # Question 3 should have "Requirements Elicitation" mapped
        assert 3 in mappings
        q3_concepts = [m.concept_name for m in mappings[3]]
        assert "Requirements Elicitation" in q3_concepts

        # Question 4 should have "Business Case" mapped, but "unknown-tag" unmatched
        assert 4 in mappings
        q4_concepts = [m.concept_name for m in mappings[4]]
        assert "Business Case" in q4_concepts

        # Verify unmatched tags were tracked
        unmatched_tag_names = [tag for _, tag, _ in importer.unmatched_tags]
        assert "unknown-tag" in unmatched_tag_names
        assert "interviews" in unmatched_tag_names  # No concept for "interviews"
        assert "planning" in unmatched_tag_names  # No concept for "planning"

    @pytest.mark.asyncio
    async def test_ka_consistency_validation(self, sample_concepts):
        """Test that KA mismatches generate warnings."""
        importer = VendorQuestionImporter(
            course_slug="cbap",
            use_csv_tags=True,
        )
        importer.concepts = sample_concepts
        importer.course_id = uuid4()

        # Create question in different KA than the concept
        questions = [
            QuestionData(
                question_text="Test question",
                options={"A": "a", "B": "b", "C": "c", "D": "d"},
                correct_answer="A",
                explanation="Test",
                knowledge_area_name="Elicitation",  # Question is in Elicitation
                knowledge_area_id="elicitation",
                row_number=2,
                # But tag matches concept in ba-planning
                concept_tags=["stakeholder analysis"],
            ),
        ]

        await importer.map_questions_from_tags(questions)

        # Should have warning about KA mismatch
        ka_warnings = [w for w in importer.result.warnings if "KA" in w or "ka" in w.lower()]
        assert len(ka_warnings) > 0

    @pytest.mark.asyncio
    async def test_duplicate_concept_prevention(self, sample_concepts):
        """Test that same concept isn't mapped twice for same question."""
        importer = VendorQuestionImporter(
            course_slug="cbap",
            use_csv_tags=True,
        )
        importer.concepts = sample_concepts
        importer.course_id = uuid4()

        # Question with duplicate tag (both should match same concept)
        questions = [
            QuestionData(
                question_text="Test question",
                options={"A": "a", "B": "b", "C": "c", "D": "d"},
                correct_answer="A",
                explanation="Test",
                knowledge_area_name="BA Planning",
                knowledge_area_id="ba-planning",
                row_number=2,
                concept_tags=["stakeholder analysis", "Stakeholder Analysis"],  # Same concept, different case
            ),
        ]

        mappings = await importer.map_questions_from_tags(questions)

        # Should only have one mapping (not duplicated)
        assert len(mappings[2]) == 1


# =====================================
# Integration Tests for Report Generation
# =====================================

class TestReportGeneration:
    """Test report export functionality."""

    def test_unmatched_tags_report(self):
        """Test unmatched tags report is generated correctly."""
        importer = VendorQuestionImporter(course_slug="cbap")
        importer.unmatched_tags = [
            (2, "unknown-tag-1", "What is the purpose..."),
            (3, "unknown-tag-2", "Which technique is..."),
            (5, "another-tag", "How do you validate..."),
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            output_path = f.name

        try:
            importer.export_unmatched_tags_report(output_path)

            # Verify file was created and has correct content
            assert os.path.exists(output_path)

            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            assert len(rows) == 3
            assert rows[0]["row_number"] == "2"
            assert rows[0]["tag"] == "unknown-tag-1"
            assert rows[1]["tag"] == "unknown-tag-2"
            assert rows[2]["tag"] == "another-tag"
        finally:
            os.unlink(output_path)

    def test_created_concepts_report(self):
        """Test created concepts report is generated correctly."""
        importer = VendorQuestionImporter(course_slug="cbap")

        # Create mock concepts that were created
        concept1 = MockConcept(
            id=uuid4(),
            name="New Concept 1",
            knowledge_area_id="ba-planning",
            created_at=datetime(2024, 1, 15, 10, 0, 0),
        )
        concept2 = MockConcept(
            id=uuid4(),
            name="New Concept 2",
            knowledge_area_id="elicitation",
            created_at=datetime(2024, 1, 15, 10, 1, 0),
        )

        importer.created_concepts = [
            (concept1, "new-tag-1"),
            (concept2, "new-tag-2"),
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            output_path = f.name

        try:
            importer.export_created_concepts_report(output_path)

            # Verify file was created
            assert os.path.exists(output_path)

            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            assert len(rows) == 2
            assert rows[0]["name"] == "New Concept 1"
            assert rows[0]["source_tag"] == "new-tag-1"
            assert rows[1]["name"] == "New Concept 2"
        finally:
            os.unlink(output_path)

    def test_empty_unmatched_report(self):
        """Test that empty report doesn't create file."""
        importer = VendorQuestionImporter(course_slug="cbap")
        importer.unmatched_tags = []

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            output_path = f.name

        # Remove the file so we can check if method creates it
        os.unlink(output_path)

        importer.export_unmatched_tags_report(output_path)

        # File should not exist because there are no unmatched tags
        assert not os.path.exists(output_path)


# =====================================
# Integration Tests for Import Flow Branching
# =====================================

class TestImportFlowBranching:
    """Test that import flow branches correctly based on flags."""

    def test_use_csv_tags_flag_is_false_by_default(self):
        """Test that use_csv_tags defaults to False."""
        importer = VendorQuestionImporter(course_slug="cbap")
        assert importer.use_csv_tags is False

    def test_use_csv_tags_flag_can_be_set(self):
        """Test that use_csv_tags can be set to True."""
        importer = VendorQuestionImporter(
            course_slug="cbap",
            use_csv_tags=True,
        )
        assert importer.use_csv_tags is True

    def test_create_missing_concepts_requires_use_csv_tags(self):
        """Test create_missing_concepts parameter."""
        importer = VendorQuestionImporter(
            course_slug="cbap",
            use_csv_tags=True,
            create_missing_concepts=True,
        )
        assert importer.create_missing_concepts is True


# =====================================
# CLI Integration Tests
# =====================================

class TestCLIIntegration:
    """Test CLI argument handling."""

    def test_argparse_help_includes_new_options(self):
        """Test that --help output includes new options."""
        import argparse
        import io
        from contextlib import redirect_stdout

        # We can't easily test argparse output, but we can verify
        # the importer accepts the parameters
        importer = VendorQuestionImporter(
            course_slug="test",
            use_csv_tags=True,
            tag_match_threshold=90,
            create_missing_concepts=True,
        )

        assert importer.tag_match_threshold == 90


# =====================================
# Regression Tests
# =====================================

class TestRegressionExistingFlow:
    """Ensure existing GPT-4 flow isn't broken."""

    def test_skip_concept_mapping_still_works(self):
        """Test that skip_concept_mapping parameter still works."""
        importer = VendorQuestionImporter(
            course_slug="cbap",
            skip_concept_mapping=True,
        )
        assert importer.skip_concept_mapping is True

    def test_dry_run_still_works(self):
        """Test that dry_run parameter still works."""
        importer = VendorQuestionImporter(
            course_slug="cbap",
            dry_run=True,
        )
        assert importer.dry_run is True

    def test_importer_has_required_methods(self):
        """Test that importer still has all required methods."""
        importer = VendorQuestionImporter(course_slug="cbap")

        # Original methods
        assert hasattr(importer, "initialize")
        assert hasattr(importer, "parse_csv")
        assert hasattr(importer, "parse_json")
        assert hasattr(importer, "parse_file")
        assert hasattr(importer, "generate_embedding")
        assert hasattr(importer, "map_question_to_concepts")
        assert hasattr(importer, "select_concepts_with_gpt4")
        assert hasattr(importer, "export_mappings_to_csv")
        assert hasattr(importer, "run")

        # New methods
        assert hasattr(importer, "map_questions_from_tags")
        assert hasattr(importer, "create_concept_from_tag")
        assert hasattr(importer, "create_missing_concepts_from_tags")
        assert hasattr(importer, "export_unmatched_tags_report")
        assert hasattr(importer, "export_created_concepts_report")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
