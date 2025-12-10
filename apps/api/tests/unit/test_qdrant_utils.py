"""
Unit tests for Qdrant utility functions

Tests helper functions for building filters, pagination, scoring, and validation.
"""

import pytest
from uuid import uuid4, UUID

from src.utils.qdrant_utils import (
    build_filter_conditions,
    build_multi_course_query,
    paginate_results,
    interpret_similarity_score,
    calculate_score_percentage,
    validate_vector_dimensions,
    format_search_result,
)


# =============================================================================
# build_filter_conditions Tests
# =============================================================================

class TestBuildFilterConditions:
    """Tests for build_filter_conditions function."""

    def test_returns_none_when_no_filters(self):
        """Should return None when no filters provided."""
        result = build_filter_conditions()
        assert result is None

    def test_builds_course_id_filter(self):
        """Should build filter with course_id condition."""
        course_id = uuid4()
        result = build_filter_conditions(course_id=course_id)

        assert result is not None
        assert len(result.must) == 1
        assert result.must[0].key == "course_id"
        assert result.must[0].match.value == str(course_id)

    def test_builds_knowledge_area_filter(self):
        """Should build filter with knowledge_area_id condition."""
        result = build_filter_conditions(knowledge_area_id="ba-planning")

        assert result is not None
        assert len(result.must) == 1
        assert result.must[0].key == "knowledge_area_id"
        assert result.must[0].match.value == "ba-planning"

    def test_builds_difficulty_range_filter_both_bounds(self):
        """Should build filter with difficulty range (min and max)."""
        result = build_filter_conditions(difficulty_min=0.3, difficulty_max=0.7)

        assert result is not None
        assert len(result.must) == 1
        assert result.must[0].key == "difficulty"
        assert result.must[0].range.gte == 0.3
        assert result.must[0].range.lte == 0.7

    def test_builds_difficulty_range_filter_min_only(self):
        """Should build filter with difficulty range (min only)."""
        result = build_filter_conditions(difficulty_min=0.5)

        assert result is not None
        assert result.must[0].range.gte == 0.5
        assert result.must[0].range.lte is None

    def test_builds_difficulty_range_filter_max_only(self):
        """Should build filter with difficulty range (max only)."""
        result = build_filter_conditions(difficulty_max=0.8)

        assert result is not None
        assert result.must[0].range.gte is None
        assert result.must[0].range.lte == 0.8

    def test_builds_concept_ids_filter(self):
        """Should build filter with concept_ids condition (MatchAny)."""
        concept1 = uuid4()
        concept2 = uuid4()
        result = build_filter_conditions(concept_ids=[concept1, concept2])

        assert result is not None
        assert len(result.must) == 1
        assert result.must[0].key == "concept_ids"
        assert str(concept1) in result.must[0].match.any
        assert str(concept2) in result.must[0].match.any

    def test_builds_section_ref_filter(self):
        """Should build filter with section_ref condition."""
        result = build_filter_conditions(section_ref="3.2.1")

        assert result is not None
        assert len(result.must) == 1
        assert result.must[0].key == "section_ref"
        assert result.must[0].match.value == "3.2.1"

    def test_builds_multiple_filters(self):
        """Should combine multiple filter conditions."""
        course_id = uuid4()
        result = build_filter_conditions(
            course_id=course_id,
            knowledge_area_id="elicitation",
            difficulty_min=0.3,
            difficulty_max=0.7
        )

        assert result is not None
        assert len(result.must) == 3  # course_id, knowledge_area_id, difficulty

        keys = [cond.key for cond in result.must]
        assert "course_id" in keys
        assert "knowledge_area_id" in keys
        assert "difficulty" in keys


# =============================================================================
# build_multi_course_query Tests
# =============================================================================

class TestBuildMultiCourseQuery:
    """Tests for build_multi_course_query function."""

    def test_returns_none_for_empty_course_ids(self):
        """Should return None when course_ids is empty."""
        result = build_multi_course_query(course_ids=[])
        assert result is None

    def test_builds_single_course_filter(self):
        """Should build filter for single course using MatchAny."""
        course_id = uuid4()
        result = build_multi_course_query(course_ids=[course_id])

        assert result is not None
        assert len(result.must) == 1
        assert result.must[0].key == "course_id"
        assert str(course_id) in result.must[0].match.any

    def test_builds_multi_course_filter(self):
        """Should build filter for multiple courses."""
        course1 = uuid4()
        course2 = uuid4()
        course3 = uuid4()
        result = build_multi_course_query(course_ids=[course1, course2, course3])

        assert result is not None
        assert len(result.must[0].match.any) == 3
        assert str(course1) in result.must[0].match.any
        assert str(course2) in result.must[0].match.any
        assert str(course3) in result.must[0].match.any

    def test_combines_course_and_knowledge_area(self):
        """Should combine multi-course with knowledge_area_id filter."""
        course1 = uuid4()
        course2 = uuid4()
        result = build_multi_course_query(
            course_ids=[course1, course2],
            knowledge_area_id="strategy"
        )

        assert result is not None
        assert len(result.must) == 2

        keys = [cond.key for cond in result.must]
        assert "course_id" in keys
        assert "knowledge_area_id" in keys

    def test_combines_course_and_difficulty_range(self):
        """Should combine multi-course with difficulty filter."""
        course_id = uuid4()
        result = build_multi_course_query(
            course_ids=[course_id],
            difficulty_min=0.2,
            difficulty_max=0.8
        )

        assert result is not None
        assert len(result.must) == 2

        # Find difficulty condition
        difficulty_cond = next(c for c in result.must if c.key == "difficulty")
        assert difficulty_cond.range.gte == 0.2
        assert difficulty_cond.range.lte == 0.8


# =============================================================================
# paginate_results Tests
# =============================================================================

class TestPaginateResults:
    """Tests for paginate_results function."""

    def test_paginates_first_page(self):
        """Should return first page of results."""
        results = [{"id": i} for i in range(10)]
        paginated = paginate_results(results, offset=0, limit=3)

        assert paginated["results"] == [{"id": 0}, {"id": 1}, {"id": 2}]
        assert paginated["total"] == 10
        assert paginated["offset"] == 0
        assert paginated["limit"] == 3
        assert paginated["has_more"] is True

    def test_paginates_middle_page(self):
        """Should return middle page of results."""
        results = [{"id": i} for i in range(10)]
        paginated = paginate_results(results, offset=3, limit=3)

        assert paginated["results"] == [{"id": 3}, {"id": 4}, {"id": 5}]
        assert paginated["offset"] == 3
        assert paginated["has_more"] is True

    def test_paginates_last_page(self):
        """Should return last page with has_more=False."""
        results = [{"id": i} for i in range(10)]
        paginated = paginate_results(results, offset=9, limit=3)

        assert paginated["results"] == [{"id": 9}]
        assert paginated["has_more"] is False

    def test_handles_empty_results(self):
        """Should handle empty results list."""
        paginated = paginate_results([], offset=0, limit=10)

        assert paginated["results"] == []
        assert paginated["total"] == 0
        assert paginated["has_more"] is False

    def test_handles_offset_beyond_results(self):
        """Should return empty when offset exceeds total."""
        results = [{"id": i} for i in range(5)]
        paginated = paginate_results(results, offset=10, limit=3)

        assert paginated["results"] == []
        assert paginated["total"] == 5
        assert paginated["has_more"] is False

    def test_uses_default_values(self):
        """Should use default offset=0 and limit=10."""
        results = [{"id": i} for i in range(15)]
        paginated = paginate_results(results)

        assert len(paginated["results"]) == 10
        assert paginated["offset"] == 0
        assert paginated["limit"] == 10
        assert paginated["has_more"] is True


# =============================================================================
# interpret_similarity_score Tests
# =============================================================================

class TestInterpretSimilarityScore:
    """Tests for interpret_similarity_score function."""

    def test_very_similar_threshold(self):
        """Should return 'very_similar' for scores >= 0.9."""
        assert interpret_similarity_score(1.0) == "very_similar"
        assert interpret_similarity_score(0.95) == "very_similar"
        assert interpret_similarity_score(0.9) == "very_similar"

    def test_similar_threshold(self):
        """Should return 'similar' for scores 0.7-0.89."""
        assert interpret_similarity_score(0.89) == "similar"
        assert interpret_similarity_score(0.75) == "similar"
        assert interpret_similarity_score(0.7) == "similar"

    def test_somewhat_similar_threshold(self):
        """Should return 'somewhat_similar' for scores 0.5-0.69."""
        assert interpret_similarity_score(0.69) == "somewhat_similar"
        assert interpret_similarity_score(0.55) == "somewhat_similar"
        assert interpret_similarity_score(0.5) == "somewhat_similar"

    def test_not_very_similar_threshold(self):
        """Should return 'not_very_similar' for scores < 0.5."""
        assert interpret_similarity_score(0.49) == "not_very_similar"
        assert interpret_similarity_score(0.25) == "not_very_similar"
        assert interpret_similarity_score(0.0) == "not_very_similar"


# =============================================================================
# calculate_score_percentage Tests
# =============================================================================

class TestCalculateScorePercentage:
    """Tests for calculate_score_percentage function."""

    def test_converts_decimal_to_percentage(self):
        """Should convert decimal score to integer percentage."""
        assert calculate_score_percentage(0.95) == 95
        assert calculate_score_percentage(0.5) == 50
        assert calculate_score_percentage(1.0) == 100
        assert calculate_score_percentage(0.0) == 0

    def test_truncates_decimal(self):
        """Should truncate (not round) to integer."""
        assert calculate_score_percentage(0.999) == 99
        assert calculate_score_percentage(0.555) == 55


# =============================================================================
# validate_vector_dimensions Tests
# =============================================================================

class TestValidateVectorDimensions:
    """Tests for validate_vector_dimensions function."""

    def test_valid_3072_dimensions(self):
        """Should return True for correct 3072 dimensions."""
        vector = [0.1] * 3072
        assert validate_vector_dimensions(vector) is True

    def test_invalid_1536_dimensions(self):
        """Should return False for wrong dimensions (1536)."""
        vector = [0.1] * 1536
        assert validate_vector_dimensions(vector) is False

    def test_custom_expected_dimensions(self):
        """Should validate against custom expected dimensions."""
        vector = [0.1] * 768
        assert validate_vector_dimensions(vector, expected_dimensions=768) is True
        assert validate_vector_dimensions(vector, expected_dimensions=3072) is False

    def test_empty_vector(self):
        """Should return False for empty vector."""
        assert validate_vector_dimensions([]) is False


# =============================================================================
# format_search_result Tests
# =============================================================================

class TestFormatSearchResult:
    """Tests for format_search_result function."""

    def test_formats_result_with_high_score(self):
        """Should format result with very similar score."""
        raw = {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "score": 0.95,
            "payload": {"question_text": "What is BA?"}
        }
        formatted = format_search_result(raw)

        assert formatted["id"] == raw["id"]
        assert formatted["score"] == 0.95
        assert formatted["score_percentage"] == 95
        assert formatted["similarity"] == "very_similar"
        assert formatted["payload"] == raw["payload"]

    def test_formats_result_with_medium_score(self):
        """Should format result with similar score."""
        raw = {
            "id": "test-id",
            "score": 0.75,
            "payload": {"text": "content"}
        }
        formatted = format_search_result(raw)

        assert formatted["score_percentage"] == 75
        assert formatted["similarity"] == "similar"

    def test_formats_result_with_low_score(self):
        """Should format result with not_very_similar score."""
        raw = {
            "id": "test-id",
            "score": 0.35,
            "payload": {}
        }
        formatted = format_search_result(raw)

        assert formatted["score_percentage"] == 35
        assert formatted["similarity"] == "not_very_similar"

    def test_preserves_payload(self):
        """Should preserve all payload fields."""
        payload = {
            "course_id": str(uuid4()),
            "knowledge_area_id": "strategy",
            "difficulty": 0.7,
            "concept_ids": [str(uuid4())],
            "question_text": "Test question"
        }
        raw = {"id": "test", "score": 0.8, "payload": payload}
        formatted = format_search_result(raw)

        assert formatted["payload"] == payload
