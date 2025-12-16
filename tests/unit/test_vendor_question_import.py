"""
Unit tests for vendor question import functionality.
Tests the VendorQuestionImporter class and related utilities.
"""
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

# Add scripts to path for imports
scripts_path = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(scripts_path))

from import_vendor_questions import (
    DIFFICULTY_MAP,
    ConceptMapping,
    ImportResult,
    QuestionData,
    VendorQuestionImporter,
)


class TestQuestionData:
    """Tests for QuestionData dataclass."""

    def test_create_question_data(self):
        """Test creating a QuestionData instance."""
        q = QuestionData(
            question_text="What is BA planning?",
            options={"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"},
            correct_answer="A",
            explanation="Explanation here",
            knowledge_area_name="Business Analysis Planning and Monitoring",
            knowledge_area_id="ba-planning",
            difficulty=0.5,
            source="vendor",
            corpus_reference="BABOK 3.1",
            row_number=1,
        )
        assert q.question_text == "What is BA planning?"
        assert q.correct_answer == "A"
        assert q.knowledge_area_id == "ba-planning"
        assert q.difficulty == 0.5

    def test_question_data_defaults(self):
        """Test QuestionData default values."""
        q = QuestionData(
            question_text="Test",
            options={"A": "A", "B": "B", "C": "C", "D": "D"},
            correct_answer="A",
            explanation="Test",
            knowledge_area_name="Test KA",
        )
        assert q.knowledge_area_id is None
        assert q.difficulty == 0.5
        assert q.source == "vendor"
        assert q.corpus_reference is None
        assert q.row_number == 0


class TestConceptMapping:
    """Tests for ConceptMapping dataclass."""

    def test_create_concept_mapping(self):
        """Test creating a ConceptMapping instance."""
        concept_id = uuid4()
        m = ConceptMapping(
            concept_id=concept_id,
            concept_name="Stakeholder Analysis",
            relevance=0.9,
            reasoning="Question directly tests this concept",
        )
        assert m.concept_id == concept_id
        assert m.concept_name == "Stakeholder Analysis"
        assert m.relevance == 0.9


class TestImportResult:
    """Tests for ImportResult dataclass."""

    def test_import_result_defaults(self):
        """Test ImportResult default values."""
        r = ImportResult()
        assert r.questions_parsed == 0
        assert r.questions_valid == 0
        assert r.questions_inserted == 0
        assert r.questions_skipped == 0
        assert r.mappings_created == 0
        assert r.errors == []
        assert r.warnings == []

    def test_import_result_mutable_defaults(self):
        """Test that errors and warnings lists are independent."""
        r1 = ImportResult()
        r2 = ImportResult()
        r1.errors.append("Error 1")
        assert r2.errors == []


class TestDifficultyMapping:
    """Tests for difficulty string to float mapping."""

    def test_difficulty_map_values(self):
        """Test difficulty map contains expected values."""
        assert DIFFICULTY_MAP["easy"] == 0.3
        assert DIFFICULTY_MAP["medium"] == 0.5
        assert DIFFICULTY_MAP["hard"] == 0.7


class TestVendorQuestionImporter:
    """Tests for VendorQuestionImporter class."""

    def test_init(self):
        """Test importer initialization."""
        importer = VendorQuestionImporter(
            course_slug="cbap",
            dry_run=True,
            skip_concept_mapping=False,
            batch_size=50,
        )
        assert importer.course_slug == "cbap"
        assert importer.dry_run is True
        assert importer.skip_concept_mapping is False
        assert importer.batch_size == 50
        assert importer.course is None
        assert importer.concepts == []

    def test_map_ka_name_to_id_lowercase(self):
        """Test KA name mapping is case-insensitive."""
        importer = VendorQuestionImporter(course_slug="cbap")
        # Add some mappings
        importer.ka_name_to_id = {
            "elicitation and collaboration": "elicitation",
            "strategy analysis": "strategy",
        }

        assert importer.map_ka_name_to_id("Elicitation and Collaboration") == "elicitation"
        assert importer.map_ka_name_to_id("STRATEGY ANALYSIS") == "strategy"

    def test_map_ka_name_to_id_not_found(self):
        """Test KA name mapping returns None for unknown KA."""
        importer = VendorQuestionImporter(course_slug="cbap")
        importer.ka_name_to_id = {}
        assert importer.map_ka_name_to_id("Unknown KA") is None


class TestCSVParsing:
    """Tests for CSV file parsing."""

    def test_parse_csv_valid_file(self):
        """Test parsing a valid CSV file."""
        importer = VendorQuestionImporter(course_slug="cbap")
        importer.ka_name_to_id = {
            "business analysis planning and monitoring": "ba-planning",
        }

        csv_content = """question_text,option_a,option_b,option_c,option_d,correct_answer,explanation,knowledge_area,difficulty
What is BA planning?,Plan A,Plan B,Plan C,Plan D,A,Because A is correct,Business Analysis Planning and Monitoring,Easy"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            f.flush()

            questions = importer.parse_csv(f.name)

        assert len(questions) == 1
        assert questions[0].question_text == "What is BA planning?"
        assert questions[0].correct_answer == "A"
        assert questions[0].knowledge_area_id == "ba-planning"
        assert questions[0].difficulty == 0.3  # "Easy" maps to 0.3

    def test_parse_csv_missing_required_field(self):
        """Test parsing CSV with missing required field adds error."""
        importer = VendorQuestionImporter(course_slug="cbap")
        importer.ka_name_to_id = {"test ka": "test-ka"}

        # Missing explanation
        csv_content = """question_text,option_a,option_b,option_c,option_d,correct_answer,explanation,knowledge_area
What is BA?,A,B,C,D,A,,Test KA"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            f.flush()

            questions = importer.parse_csv(f.name)

        assert len(questions) == 0
        assert len(importer.result.errors) == 1
        assert "Missing explanation" in importer.result.errors[0]

    def test_parse_csv_invalid_correct_answer(self):
        """Test parsing CSV with invalid correct_answer."""
        importer = VendorQuestionImporter(course_slug="cbap")
        importer.ka_name_to_id = {"test ka": "test-ka"}

        csv_content = """question_text,option_a,option_b,option_c,option_d,correct_answer,explanation,knowledge_area
What is BA?,A,B,C,D,E,Explanation,Test KA"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            f.flush()

            questions = importer.parse_csv(f.name)

        assert len(questions) == 0
        assert "Invalid correct_answer" in importer.result.errors[0]


class TestJSONParsing:
    """Tests for JSON file parsing."""

    def test_parse_json_valid_file(self):
        """Test parsing a valid JSON file."""
        importer = VendorQuestionImporter(course_slug="cbap")
        importer.ka_name_to_id = {
            "elicitation": "elicitation",
        }

        json_content = [
            {
                "question_text": "What is elicitation?",
                "options": {"A": "A", "B": "B", "C": "C", "D": "D"},
                "correct_answer": "A",
                "explanation": "Because A",
                "knowledge_area": "Elicitation",
                "difficulty": 0.6,
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(json_content, f)
            f.flush()

            questions = importer.parse_json(f.name)

        assert len(questions) == 1
        assert questions[0].question_text == "What is elicitation?"
        assert questions[0].difficulty == 0.6

    def test_parse_json_with_separate_options(self):
        """Test parsing JSON with separate option fields."""
        importer = VendorQuestionImporter(course_slug="cbap")
        importer.ka_name_to_id = {"test": "test"}

        json_content = [
            {
                "question_text": "Test?",
                "option_a": "A text",
                "option_b": "B text",
                "option_c": "C text",
                "option_d": "D text",
                "correct_answer": "B",
                "explanation": "Because B",
                "knowledge_area": "Test",
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(json_content, f)
            f.flush()

            questions = importer.parse_json(f.name)

        assert len(questions) == 1
        assert questions[0].options["A"] == "A text"
        assert questions[0].options["B"] == "B text"


class TestValidation:
    """Tests for import validation."""

    def test_validate_import_results_all_mapped(self):
        """Test validation with all questions mapped."""
        importer = VendorQuestionImporter(course_slug="cbap")

        # Create mock concepts
        concept1 = MagicMock()
        concept1.id = uuid4()
        concept1.name = "Concept 1"
        concept2 = MagicMock()
        concept2.id = uuid4()
        concept2.name = "Concept 2"
        importer.concepts = [concept1, concept2]

        questions = [
            QuestionData(
                question_text="Q1",
                options={"A": "A", "B": "B", "C": "C", "D": "D"},
                correct_answer="A",
                explanation="E1",
                knowledge_area_name="Test",
                knowledge_area_id="test",
                row_number=1,
            ),
        ]

        mappings = {
            1: [
                ConceptMapping(
                    concept_id=concept1.id,
                    concept_name="Concept 1",
                    relevance=0.9,
                    reasoning="Test",
                )
            ]
        }

        report = importer.validate_import_results(questions, mappings)

        assert report["total_questions"] == 1
        assert report["mapped_questions"] == 1
        assert report["unmapped_questions"] == 0

    def test_validate_import_results_missing_mapping(self):
        """Test validation identifies unmapped questions."""
        importer = VendorQuestionImporter(course_slug="cbap")
        importer.concepts = []

        questions = [
            QuestionData(
                question_text="Q1",
                options={"A": "A", "B": "B", "C": "C", "D": "D"},
                correct_answer="A",
                explanation="E1",
                knowledge_area_name="Test",
                knowledge_area_id="test",
                row_number=1,
            ),
        ]

        mappings = {}  # No mappings

        report = importer.validate_import_results(questions, mappings)

        assert report["unmapped_questions"] == 1


class TestCSVExport:
    """Tests for CSV export functionality."""

    def test_export_mappings_to_csv(self):
        """Test exporting mappings to CSV."""
        importer = VendorQuestionImporter(course_slug="cbap")

        questions = [
            QuestionData(
                question_text="Test question text here",
                options={"A": "A", "B": "B", "C": "C", "D": "D"},
                correct_answer="A",
                explanation="Explanation",
                knowledge_area_name="Test KA",
                knowledge_area_id="test-ka",
                row_number=1,
            ),
        ]

        concept_id = uuid4()
        mappings = {
            1: [
                ConceptMapping(
                    concept_id=concept_id,
                    concept_name="Test Concept",
                    relevance=0.9,
                    reasoning="Direct test",
                )
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = f.name

        importer.export_mappings_to_csv(questions, mappings, output_path)

        # Read and verify
        with open(output_path, "r") as f:
            content = f.read()

        assert "Test question text" in content
        assert "Test Concept" in content
        assert "0.9" in content


class TestFileFormatDetection:
    """Tests for file format detection."""

    def test_parse_file_detects_csv(self):
        """Test that CSV extension is detected."""
        importer = VendorQuestionImporter(course_slug="cbap")
        importer.ka_name_to_id = {}

        csv_content = """question_text,option_a,option_b,option_c,option_d,correct_answer,explanation,knowledge_area
Q,A,B,C,D,A,E,KA"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            f.flush()

            # Should not raise, even if no valid questions
            questions = importer.parse_file(f.name)

        # Will have warnings about unknown KA, but should parse
        assert len(importer.result.warnings) > 0 or len(questions) == 0

    def test_parse_file_detects_json(self):
        """Test that JSON extension is detected."""
        importer = VendorQuestionImporter(course_slug="cbap")
        importer.ka_name_to_id = {}

        json_content = []

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(json_content, f)
            f.flush()

            questions = importer.parse_file(f.name)

        assert questions == []
