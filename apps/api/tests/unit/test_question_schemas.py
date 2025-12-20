"""
Unit tests for question schemas.
Tests validation, serialization, and helper methods.
"""
from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.schemas.question import (
    ConceptCoverageStats,
    ConceptMappingResponse,
    ConceptMappingWithReasoning,
    ImportValidationReport,
    QuestionBase,
    QuestionConceptCreate,
    QuestionConceptMappingResult,
    QuestionConceptResponse,
    QuestionCreate,
    QuestionDistributionStats,
    QuestionImport,
    QuestionImportResult,
    QuestionOptionsSchema,
    QuestionResponse,
    QuestionUpdate,
    QuestionWithConceptsResponse,
)


class TestQuestionOptionsSchema:
    """Tests for QuestionOptionsSchema."""

    def test_valid_options(self):
        """Test valid options creation."""
        options = QuestionOptionsSchema(
            A="Option A text",
            B="Option B text",
            C="Option C text",
            D="Option D text",
        )
        assert options.A == "Option A text"
        assert options.B == "Option B text"
        assert options.C == "Option C text"
        assert options.D == "Option D text"

    def test_empty_option_fails(self):
        """Test that empty options fail validation."""
        with pytest.raises(ValidationError) as exc_info:
            QuestionOptionsSchema(
                A="",
                B="Option B",
                C="Option C",
                D="Option D",
            )
        assert "min_length" in str(exc_info.value).lower() or "at least 1" in str(exc_info.value).lower()

    def test_missing_option_fails(self):
        """Test that missing options fail validation."""
        with pytest.raises(ValidationError):
            QuestionOptionsSchema(
                A="Option A",
                B="Option B",
                C="Option C",
                # D is missing
            )


class TestQuestionBase:
    """Tests for QuestionBase schema."""

    def test_valid_question_base(self):
        """Test valid question base creation."""
        options = QuestionOptionsSchema(
            A="Option A", B="Option B", C="Option C", D="Option D"
        )
        question = QuestionBase(
            question_text="This is a valid question text for testing",
            options=options,
            correct_answer="A",
            explanation="This is the explanation for the answer",
            knowledge_area_id="KA1",
            difficulty=0.5,
            source="vendor",
        )
        assert question.question_text == "This is a valid question text for testing"
        assert question.correct_answer == "A"
        assert question.difficulty == 0.5

    def test_question_text_too_short(self):
        """Test that short question text fails."""
        options = QuestionOptionsSchema(
            A="Option A", B="Option B", C="Option C", D="Option D"
        )
        with pytest.raises(ValidationError) as exc_info:
            QuestionBase(
                question_text="Short",  # Less than 10 chars
                options=options,
                correct_answer="A",
                explanation="This is the explanation",
                knowledge_area_id="KA1",
            )
        assert "min_length" in str(exc_info.value).lower() or "at least 10" in str(exc_info.value).lower()

    def test_invalid_correct_answer(self):
        """Test that invalid correct answer fails."""
        options = QuestionOptionsSchema(
            A="Option A", B="Option B", C="Option C", D="Option D"
        )
        with pytest.raises(ValidationError) as exc_info:
            QuestionBase(
                question_text="This is a valid question text",
                options=options,
                correct_answer="E",  # Invalid - must be A, B, C, or D
                explanation="This is the explanation",
                knowledge_area_id="KA1",
            )
        assert "pattern" in str(exc_info.value).lower() or "string_pattern" in str(exc_info.value).lower()

    def test_difficulty_range_validation(self):
        """Test difficulty must be between 0.0 and 1.0."""
        options = QuestionOptionsSchema(
            A="Option A", B="Option B", C="Option C", D="Option D"
        )

        # Valid difficulty
        question = QuestionBase(
            question_text="This is a valid question text",
            options=options,
            correct_answer="A",
            explanation="This is the explanation",
            knowledge_area_id="KA1",
            difficulty=0.7,
        )
        assert question.difficulty == 0.7

        # Invalid difficulty > 1.0
        with pytest.raises(ValidationError):
            QuestionBase(
                question_text="This is a valid question text",
                options=options,
                correct_answer="A",
                explanation="This is the explanation",
                knowledge_area_id="KA1",
                difficulty=1.5,
            )

        # Invalid difficulty < 0.0
        with pytest.raises(ValidationError):
            QuestionBase(
                question_text="This is a valid question text",
                options=options,
                correct_answer="A",
                explanation="This is the explanation",
                knowledge_area_id="KA1",
                difficulty=-0.1,
            )

    def test_default_values(self):
        """Test default values are applied."""
        options = QuestionOptionsSchema(
            A="Option A", B="Option B", C="Option C", D="Option D"
        )
        question = QuestionBase(
            question_text="This is a valid question text",
            options=options,
            correct_answer="A",
            explanation="This is the explanation",
            knowledge_area_id="KA1",
        )
        assert question.difficulty == 0.5  # Default
        assert question.source == "vendor"  # Default
        assert question.corpus_reference is None  # Default


class TestQuestionCreate:
    """Tests for QuestionCreate schema."""

    def test_valid_question_create(self):
        """Test valid question creation schema."""
        course_id = uuid4()
        options = QuestionOptionsSchema(
            A="Option A", B="Option B", C="Option C", D="Option D"
        )
        question = QuestionCreate(
            question_text="This is a valid question text for testing",
            options=options,
            correct_answer="B",
            explanation="This is the explanation for the answer",
            knowledge_area_id="KA2",
            course_id=course_id,
            discrimination=2.0,
            guess_rate=0.25,
            slip_rate=0.10,
        )
        assert question.course_id == course_id
        assert question.discrimination == 2.0
        assert question.guess_rate == 0.25
        assert question.slip_rate == 0.10

    def test_default_irt_parameters(self):
        """Test default IRT parameters."""
        course_id = uuid4()
        options = QuestionOptionsSchema(
            A="Option A", B="Option B", C="Option C", D="Option D"
        )
        question = QuestionCreate(
            question_text="This is a valid question text for testing",
            options=options,
            correct_answer="C",
            explanation="This is the explanation for the answer",
            knowledge_area_id="KA3",
            course_id=course_id,
        )
        assert question.discrimination == 1.0  # Default
        assert question.guess_rate == 0.25  # Default
        assert question.slip_rate == 0.10  # Default

    def test_discrimination_range(self):
        """Test discrimination must be between 0.0 and 5.0."""
        course_id = uuid4()
        options = QuestionOptionsSchema(
            A="Option A", B="Option B", C="Option C", D="Option D"
        )

        # Valid discrimination
        question = QuestionCreate(
            question_text="This is a valid question text for testing",
            options=options,
            correct_answer="A",
            explanation="This is the explanation",
            knowledge_area_id="KA1",
            course_id=course_id,
            discrimination=4.5,
        )
        assert question.discrimination == 4.5

        # Invalid discrimination > 5.0
        with pytest.raises(ValidationError):
            QuestionCreate(
                question_text="This is a valid question text for testing",
                options=options,
                correct_answer="A",
                explanation="This is the explanation",
                knowledge_area_id="KA1",
                course_id=course_id,
                discrimination=6.0,
            )


class TestQuestionUpdate:
    """Tests for QuestionUpdate schema."""

    def test_empty_update(self):
        """Test empty update is valid."""
        update = QuestionUpdate()
        assert update.question_text is None
        assert update.options is None
        assert update.correct_answer is None

    def test_partial_update(self):
        """Test partial update with some fields."""
        update = QuestionUpdate(
            difficulty=0.8,
            is_active=False,
        )
        assert update.difficulty == 0.8
        assert update.is_active is False
        assert update.question_text is None

    def test_full_update(self):
        """Test update with all fields."""
        options = QuestionOptionsSchema(
            A="New A", B="New B", C="New C", D="New D"
        )
        update = QuestionUpdate(
            question_text="Updated question text here",
            options=options,
            correct_answer="D",
            explanation="Updated explanation text",
            knowledge_area_id="KA5",
            difficulty=0.9,
            discrimination=3.0,
            guess_rate=0.20,
            slip_rate=0.15,
            corpus_reference="Section 5.1",
            is_active=True,
        )
        assert update.question_text == "Updated question text here"
        assert update.correct_answer == "D"
        assert update.difficulty == 0.9


class TestQuestionResponse:
    """Tests for QuestionResponse schema."""

    def test_valid_response(self):
        """Test valid question response."""
        question_id = uuid4()
        course_id = uuid4()
        now = datetime.utcnow()

        options = QuestionOptionsSchema(
            A="Option A", B="Option B", C="Option C", D="Option D"
        )
        response = QuestionResponse(
            id=question_id,
            course_id=course_id,
            question_text="This is a valid question text",
            options=options,
            correct_answer="A",
            explanation="This is the explanation",
            knowledge_area_id="KA1",
            difficulty=0.5,
            source="vendor",
            corpus_reference=None,
            discrimination=1.0,
            guess_rate=0.25,
            slip_rate=0.10,
            times_asked=10,
            times_correct=7,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        assert response.id == question_id
        assert response.times_asked == 10
        assert response.times_correct == 7


class TestQuestionWithConceptsResponse:
    """Tests for QuestionWithConceptsResponse schema."""

    def test_response_with_concepts(self):
        """Test question response with concepts."""
        question_id = uuid4()
        course_id = uuid4()
        concept_id = uuid4()
        now = datetime.utcnow()

        options = QuestionOptionsSchema(
            A="Option A", B="Option B", C="Option C", D="Option D"
        )

        concepts = [
            ConceptMappingResponse(
                concept_id=concept_id,
                concept_name="Test Concept",
                relevance=0.9,
            )
        ]

        response = QuestionWithConceptsResponse(
            id=question_id,
            course_id=course_id,
            question_text="This is a valid question text",
            options=options,
            correct_answer="A",
            explanation="This is the explanation",
            knowledge_area_id="KA1",
            difficulty=0.5,
            source="vendor",
            corpus_reference=None,
            discrimination=1.0,
            guess_rate=0.25,
            slip_rate=0.10,
            times_asked=0,
            times_correct=0,
            is_active=True,
            created_at=now,
            updated_at=now,
            concepts=concepts,
        )
        assert len(response.concepts) == 1
        assert response.concepts[0].concept_name == "Test Concept"

    def test_response_with_empty_concepts(self):
        """Test question response with no concepts."""
        question_id = uuid4()
        course_id = uuid4()
        now = datetime.utcnow()

        options = QuestionOptionsSchema(
            A="Option A", B="Option B", C="Option C", D="Option D"
        )

        response = QuestionWithConceptsResponse(
            id=question_id,
            course_id=course_id,
            question_text="This is a valid question text",
            options=options,
            correct_answer="A",
            explanation="This is the explanation",
            knowledge_area_id="KA1",
            difficulty=0.5,
            source="vendor",
            corpus_reference=None,
            discrimination=1.0,
            guess_rate=0.25,
            slip_rate=0.10,
            times_asked=0,
            times_correct=0,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        assert response.concepts == []


class TestQuestionImport:
    """Tests for QuestionImport schema."""

    def test_import_with_jsonb_options(self):
        """Test import with JSONB options format."""
        question = QuestionImport(
            question_text="This is a valid question text for import",
            correct_answer="A",
            explanation="Explanation text",
            knowledge_area="Business Analysis Planning",
            options={"A": "First", "B": "Second", "C": "Third", "D": "Fourth"},
        )

        options_dict = question.get_options_dict()
        assert options_dict == {"A": "First", "B": "Second", "C": "Third", "D": "Fourth"}

    def test_import_with_csv_columns(self):
        """Test import with separate CSV column format."""
        question = QuestionImport(
            question_text="This is a valid question text for import",
            correct_answer="b",  # lowercase - should be normalized
            explanation="Explanation text",
            knowledge_area="Requirements Analysis",
            option_a="First option",
            option_b="Second option",
            option_c="Third option",
            option_d="Fourth option",
        )

        options_dict = question.get_options_dict()
        assert options_dict == {
            "A": "First option",
            "B": "Second option",
            "C": "Third option",
            "D": "Fourth option",
        }

    def test_correct_answer_normalization(self):
        """Test correct answer is normalized to uppercase."""
        question = QuestionImport(
            question_text="This is a valid question text",
            correct_answer="c",
            explanation="Explanation",
            knowledge_area="KA1",
            options={"A": "A", "B": "B", "C": "C", "D": "D"},
        )
        assert question.correct_answer == "C"

    def test_difficulty_float_from_float_string(self):
        """Test difficulty conversion from float string."""
        question = QuestionImport(
            question_text="This is a valid question text",
            correct_answer="A",
            explanation="Explanation",
            knowledge_area="KA1",
            options={"A": "A", "B": "B", "C": "C", "D": "D"},
            difficulty="0.75",
        )
        assert question.get_difficulty_float() == 0.75

    def test_difficulty_float_from_easy(self):
        """Test difficulty conversion from 'Easy' string."""
        question = QuestionImport(
            question_text="This is a valid question text",
            correct_answer="A",
            explanation="Explanation",
            knowledge_area="KA1",
            options={"A": "A", "B": "B", "C": "C", "D": "D"},
            difficulty="Easy",
        )
        assert question.get_difficulty_float() == 0.3

    def test_difficulty_float_from_medium(self):
        """Test difficulty conversion from 'Medium' string."""
        question = QuestionImport(
            question_text="This is a valid question text",
            correct_answer="A",
            explanation="Explanation",
            knowledge_area="KA1",
            options={"A": "A", "B": "B", "C": "C", "D": "D"},
            difficulty="medium",
        )
        assert question.get_difficulty_float() == 0.5

    def test_difficulty_float_from_hard(self):
        """Test difficulty conversion from 'Hard' string."""
        question = QuestionImport(
            question_text="This is a valid question text",
            correct_answer="A",
            explanation="Explanation",
            knowledge_area="KA1",
            options={"A": "A", "B": "B", "C": "C", "D": "D"},
            difficulty="HARD",
        )
        assert question.get_difficulty_float() == 0.7

    def test_difficulty_float_default(self):
        """Test difficulty returns default when None."""
        question = QuestionImport(
            question_text="This is a valid question text",
            correct_answer="A",
            explanation="Explanation",
            knowledge_area="KA1",
            options={"A": "A", "B": "B", "C": "C", "D": "D"},
        )
        assert question.get_difficulty_float() == 0.5

    def test_difficulty_float_unknown_string(self):
        """Test difficulty returns default for unknown string."""
        question = QuestionImport(
            question_text="This is a valid question text",
            correct_answer="A",
            explanation="Explanation",
            knowledge_area="KA1",
            options={"A": "A", "B": "B", "C": "C", "D": "D"},
            difficulty="Very Hard",  # Unknown
        )
        assert question.get_difficulty_float() == 0.5

    def test_difficulty_float_clamped(self):
        """Test difficulty is clamped to 0.0-1.0 range."""
        question = QuestionImport(
            question_text="This is a valid question text",
            correct_answer="A",
            explanation="Explanation",
            knowledge_area="KA1",
            options={"A": "A", "B": "B", "C": "C", "D": "D"},
            difficulty="1.5",  # Above max
        )
        assert question.get_difficulty_float() == 1.0

        question2 = QuestionImport(
            question_text="This is a valid question text",
            correct_answer="A",
            explanation="Explanation",
            knowledge_area="KA1",
            options={"A": "A", "B": "B", "C": "C", "D": "D"},
            difficulty="-0.5",  # Below min
        )
        assert question2.get_difficulty_float() == 0.0

    def test_import_with_babok_reference_alias(self):
        """Test corpus_reference accepts babok_reference alias."""
        question = QuestionImport(
            question_text="This is a valid question text",
            correct_answer="A",
            explanation="Explanation",
            knowledge_area="KA1",
            options={"A": "A", "B": "B", "C": "C", "D": "D"},
            babok_reference="Section 3.2.1",
        )
        assert question.corpus_reference == "Section 3.2.1"

    def test_options_dict_with_missing_csv_columns(self):
        """Test options dict returns empty strings for missing columns."""
        question = QuestionImport(
            question_text="This is a valid question text",
            correct_answer="A",
            explanation="Explanation",
            knowledge_area="KA1",
            option_a="First",
            # Other options missing
        )
        options_dict = question.get_options_dict()
        assert options_dict["A"] == "First"
        assert options_dict["B"] == ""
        assert options_dict["C"] == ""
        assert options_dict["D"] == ""


class TestQuestionImportResult:
    """Tests for QuestionImportResult schema."""

    def test_valid_import_result(self):
        """Test valid import result."""
        result = QuestionImportResult(
            total_parsed=100,
            valid_questions=95,
            invalid_questions=5,
            inserted_questions=90,
            skipped_duplicates=5,
            errors=["Row 10: Invalid correct answer", "Row 25: Missing explanation"],
        )
        assert result.total_parsed == 100
        assert result.valid_questions == 95
        assert result.inserted_questions == 90
        assert len(result.errors) == 2


class TestQuestionConceptCreate:
    """Tests for QuestionConceptCreate schema."""

    def test_valid_create(self):
        """Test valid concept mapping creation."""
        question_id = uuid4()
        concept_id = uuid4()
        mapping = QuestionConceptCreate(
            question_id=question_id,
            concept_id=concept_id,
            relevance=0.85,
        )
        assert mapping.question_id == question_id
        assert mapping.concept_id == concept_id
        assert mapping.relevance == 0.85

    def test_default_relevance(self):
        """Test default relevance is 1.0."""
        question_id = uuid4()
        concept_id = uuid4()
        mapping = QuestionConceptCreate(
            question_id=question_id,
            concept_id=concept_id,
        )
        assert mapping.relevance == 1.0

    def test_relevance_range(self):
        """Test relevance must be between 0.0 and 1.0."""
        question_id = uuid4()
        concept_id = uuid4()

        with pytest.raises(ValidationError):
            QuestionConceptCreate(
                question_id=question_id,
                concept_id=concept_id,
                relevance=1.5,
            )


class TestQuestionConceptResponse:
    """Tests for QuestionConceptResponse schema."""

    def test_valid_response(self):
        """Test valid concept mapping response."""
        question_id = uuid4()
        concept_id = uuid4()
        now = datetime.utcnow()

        response = QuestionConceptResponse(
            question_id=question_id,
            concept_id=concept_id,
            relevance=0.9,
            created_at=now,
        )
        assert response.question_id == question_id
        assert response.relevance == 0.9


class TestConceptMappingResponse:
    """Tests for ConceptMappingResponse schema."""

    def test_valid_response(self):
        """Test valid concept mapping response."""
        concept_id = uuid4()
        response = ConceptMappingResponse(
            concept_id=concept_id,
            concept_name="Test Concept",
            relevance=0.75,
        )
        assert response.concept_name == "Test Concept"
        assert response.relevance == 0.75


class TestConceptMappingWithReasoning:
    """Tests for ConceptMappingWithReasoning schema."""

    def test_valid_mapping_with_reasoning(self):
        """Test valid concept mapping with reasoning."""
        concept_id = uuid4()
        mapping = ConceptMappingWithReasoning(
            concept_id=concept_id,
            concept_name="Stakeholder Analysis",
            relevance=0.9,
            reasoning="This question directly tests understanding of stakeholder identification techniques.",
        )
        assert mapping.concept_name == "Stakeholder Analysis"
        assert mapping.relevance == 0.9
        assert "stakeholder" in mapping.reasoning.lower()


class TestQuestionConceptMappingResult:
    """Tests for QuestionConceptMappingResult schema."""

    def test_successful_result(self):
        """Test successful mapping result."""
        question_id = uuid4()
        concept_id = uuid4()

        mappings = [
            ConceptMappingWithReasoning(
                concept_id=concept_id,
                concept_name="Test Concept",
                relevance=0.8,
                reasoning="Test reasoning",
            )
        ]

        result = QuestionConceptMappingResult(
            question_id=question_id,
            question_text="This is a test question",
            mappings=mappings,
            success=True,
        )
        assert result.success is True
        assert result.error is None
        assert len(result.mappings) == 1

    def test_failed_result(self):
        """Test failed mapping result."""
        question_id = uuid4()

        result = QuestionConceptMappingResult(
            question_id=question_id,
            question_text="This is a test question",
            mappings=[],
            success=False,
            error="Failed to call GPT-4 API",
        )
        assert result.success is False
        assert result.error == "Failed to call GPT-4 API"


class TestConceptCoverageStats:
    """Tests for ConceptCoverageStats schema."""

    def test_valid_stats(self):
        """Test valid concept coverage stats."""
        stats = ConceptCoverageStats(
            total_concepts=50,
            concepts_with_questions=45,
            concepts_without_questions=5,
            concepts_with_few_questions=10,
            average_questions_per_concept=4.5,
            concepts_needing_content=["Concept A", "Concept B"],
        )
        assert stats.total_concepts == 50
        assert stats.concepts_with_questions == 45
        assert len(stats.concepts_needing_content) == 2


class TestQuestionDistributionStats:
    """Tests for QuestionDistributionStats schema."""

    def test_valid_stats(self):
        """Test valid question distribution stats."""
        stats = QuestionDistributionStats(
            total_questions=500,
            by_knowledge_area={"KA1": 100, "KA2": 150, "KA3": 250},
            by_difficulty={"Easy": 100, "Medium": 300, "Hard": 100},
            questions_with_concepts=450,
            questions_without_concepts=50,
            average_concepts_per_question=2.3,
        )
        assert stats.total_questions == 500
        assert stats.by_knowledge_area["KA2"] == 150
        assert stats.questions_with_concepts == 450


class TestImportValidationReport:
    """Tests for ImportValidationReport schema."""

    def test_valid_report(self):
        """Test valid import validation report."""
        course_id = uuid4()

        question_stats = QuestionDistributionStats(
            total_questions=100,
            by_knowledge_area={"KA1": 50, "KA2": 50},
            by_difficulty={"Easy": 30, "Medium": 50, "Hard": 20},
            questions_with_concepts=80,
            questions_without_concepts=20,
            average_concepts_per_question=1.5,
        )

        concept_stats = ConceptCoverageStats(
            total_concepts=20,
            concepts_with_questions=18,
            concepts_without_questions=2,
            concepts_with_few_questions=5,
            average_questions_per_concept=5.0,
            concepts_needing_content=["Concept X", "Concept Y"],
        )

        report = ImportValidationReport(
            course_slug="cbap",
            course_id=course_id,
            question_stats=question_stats,
            concept_stats=concept_stats,
            warnings=["Some concepts have few questions"],
            errors=[],
            is_valid=True,
        )
        assert report.course_slug == "cbap"
        assert report.is_valid is True
        assert len(report.warnings) == 1
        assert len(report.errors) == 0

    def test_invalid_report(self):
        """Test invalid import validation report."""
        course_id = uuid4()

        question_stats = QuestionDistributionStats(
            total_questions=10,
            by_knowledge_area={"KA1": 10},
            by_difficulty={"Easy": 10},
            questions_with_concepts=0,
            questions_without_concepts=10,
            average_concepts_per_question=0.0,
        )

        concept_stats = ConceptCoverageStats(
            total_concepts=20,
            concepts_with_questions=0,
            concepts_without_questions=20,
            concepts_with_few_questions=0,
            average_questions_per_concept=0.0,
            concepts_needing_content=[],
        )

        report = ImportValidationReport(
            course_slug="test",
            course_id=course_id,
            question_stats=question_stats,
            concept_stats=concept_stats,
            warnings=[],
            errors=["No questions mapped to concepts", "Insufficient question count"],
            is_valid=False,
        )
        assert report.is_valid is False
        assert len(report.errors) == 2
