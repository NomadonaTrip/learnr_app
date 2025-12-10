"""
Qdrant utility functions
Helper functions for working with Qdrant vector database with multi-course support
"""

import logging
from typing import Dict, Any, List, Optional
from uuid import UUID
from qdrant_client.models import Filter, FieldCondition, MatchValue, MatchAny, Range

logger = logging.getLogger(__name__)


def build_filter_conditions(
    course_id: Optional[UUID] = None,
    knowledge_area_id: Optional[str] = None,
    difficulty_min: Optional[float] = None,
    difficulty_max: Optional[float] = None,
    concept_ids: Optional[List[UUID]] = None,
    section_ref: Optional[str] = None,
) -> Filter | None:
    """
    Build Qdrant filter conditions for multi-course queries.

    Args:
        course_id: UUID of course to filter by (recommended for all queries)
        knowledge_area_id: Knowledge area ID (matches course.knowledge_areas[].id)
        difficulty_min: Minimum difficulty (0.0-1.0)
        difficulty_max: Maximum difficulty (0.0-1.0)
        concept_ids: List of concept UUIDs to filter by (any match)
        section_ref: Section reference (for reading chunks)

    Returns:
        Filter object with conditions, or None if no filters provided

    Examples:
        >>> build_filter_conditions(course_id=uuid4(), knowledge_area_id="ba-planning")
        Filter(must=[...])

        >>> build_filter_conditions(course_id=uuid4(), difficulty_min=0.3, difficulty_max=0.7)
        Filter(must=[...])

        >>> build_filter_conditions()
        None
    """
    must_conditions = []

    # Course filter (should almost always be set for multi-course)
    if course_id:
        must_conditions.append(
            FieldCondition(
                key="course_id",
                match=MatchValue(value=str(course_id))
            )
        )
        logger.debug(f"Added course_id filter: {course_id}")

    # Knowledge Area filter
    if knowledge_area_id:
        must_conditions.append(
            FieldCondition(
                key="knowledge_area_id",
                match=MatchValue(value=knowledge_area_id)
            )
        )
        logger.debug(f"Added knowledge_area_id filter: {knowledge_area_id}")

    # Difficulty range filter
    if difficulty_min is not None or difficulty_max is not None:
        must_conditions.append(
            FieldCondition(
                key="difficulty",
                range=Range(
                    gte=difficulty_min,
                    lte=difficulty_max
                )
            )
        )
        logger.debug(f"Added difficulty filter: {difficulty_min}-{difficulty_max}")

    # Concept IDs filter (any match)
    if concept_ids:
        must_conditions.append(
            FieldCondition(
                key="concept_ids",
                match=MatchAny(any=[str(c) for c in concept_ids])
            )
        )
        logger.debug(f"Added concept_ids filter: {len(concept_ids)} concepts")

    # Section reference filter (for reading chunks)
    if section_ref:
        must_conditions.append(
            FieldCondition(
                key="section_ref",
                match=MatchValue(value=section_ref)
            )
        )
        logger.debug(f"Added section_ref filter: {section_ref}")

    # Return Filter object if we have conditions, None otherwise
    if must_conditions:
        logger.debug(f"Built filter with {len(must_conditions)} conditions")
        return Filter(must=must_conditions)

    return None


def build_multi_course_query(
    course_ids: List[UUID],
    knowledge_area_id: Optional[str] = None,
    difficulty_min: Optional[float] = None,
    difficulty_max: Optional[float] = None,
) -> Filter | None:
    """
    Build Qdrant filter for querying across multiple courses.

    Useful for cross-course analytics or searches spanning multiple courses.

    Args:
        course_ids: List of course UUIDs to include
        knowledge_area_id: Optional knowledge area filter
        difficulty_min: Minimum difficulty (0.0-1.0)
        difficulty_max: Maximum difficulty (0.0-1.0)

    Returns:
        Filter object with conditions, or None if no course_ids provided

    Examples:
        >>> build_multi_course_query([course1_id, course2_id])
        Filter(must=[FieldCondition(key='course_id', match=MatchAny(...))])
    """
    if not course_ids:
        return None

    must_conditions = []

    # Multi-course filter using MatchAny
    must_conditions.append(
        FieldCondition(
            key="course_id",
            match=MatchAny(any=[str(c) for c in course_ids])
        )
    )
    logger.debug(f"Added multi-course filter: {len(course_ids)} courses")

    # Knowledge area filter
    if knowledge_area_id:
        must_conditions.append(
            FieldCondition(
                key="knowledge_area_id",
                match=MatchValue(value=knowledge_area_id)
            )
        )

    # Difficulty range filter
    if difficulty_min is not None or difficulty_max is not None:
        must_conditions.append(
            FieldCondition(
                key="difficulty",
                range=Range(
                    gte=difficulty_min,
                    lte=difficulty_max
                )
            )
        )

    return Filter(must=must_conditions)


def paginate_results(
    results: List[Dict[str, Any]],
    offset: int = 0,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Paginate search results.

    Args:
        results: List of search results
        offset: Number of results to skip (default: 0)
        limit: Maximum number of results to return (default: 10)

    Returns:
        Dictionary with paginated results and metadata

    Examples:
        >>> results = [{"id": 1}, {"id": 2}, {"id": 3}]
        >>> paginate_results(results, offset=0, limit=2)
        {
            'results': [{'id': 1}, {'id': 2}],
            'total': 3,
            'offset': 0,
            'limit': 2,
            'has_more': True
        }
    """
    total = len(results)
    paginated = results[offset:offset + limit]

    return {
        "results": paginated,
        "total": total,
        "offset": offset,
        "limit": limit,
        "has_more": (offset + limit) < total
    }


def interpret_similarity_score(score: float) -> str:
    """
    Interpret cosine similarity score and return human-readable description.

    Cosine similarity scores range from -1 to 1:
    - 1.0 = identical vectors
    - 0.9-0.99 = very similar
    - 0.7-0.89 = similar
    - 0.5-0.69 = somewhat similar
    - < 0.5 = not very similar

    Args:
        score: Cosine similarity score (0.0 to 1.0)

    Returns:
        String description of similarity level

    Examples:
        >>> interpret_similarity_score(0.95)
        'very_similar'

        >>> interpret_similarity_score(0.75)
        'similar'

        >>> interpret_similarity_score(0.42)
        'not_very_similar'
    """
    if score >= 0.9:
        return "very_similar"
    elif score >= 0.7:
        return "similar"
    elif score >= 0.5:
        return "somewhat_similar"
    else:
        return "not_very_similar"


def calculate_score_percentage(score: float) -> int:
    """
    Convert similarity score to percentage.

    Args:
        score: Similarity score (0.0 to 1.0)

    Returns:
        Integer percentage (0-100)

    Examples:
        >>> calculate_score_percentage(0.95)
        95

        >>> calculate_score_percentage(0.5)
        50
    """
    return int(score * 100)


def log_qdrant_operation(
    operation: str,
    collection: str,
    success: bool,
    duration_ms: int | None = None,
    error: str | None = None,
    metadata: Dict[str, Any] | None = None
) -> None:
    """
    Log Qdrant operations for debugging and monitoring.

    Args:
        operation: Type of operation (e.g., "search", "create", "delete")
        collection: Collection name
        success: Whether operation succeeded
        duration_ms: Operation duration in milliseconds
        error: Error message if operation failed
        metadata: Additional metadata (e.g., filter conditions, result count)

    Examples:
        >>> log_qdrant_operation(
        ...     operation="search",
        ...     collection="cbap_questions",
        ...     success=True,
        ...     duration_ms=15,
        ...     metadata={"filters": {"ka": "Strategy Analysis"}, "results": 5}
        ... )
    """
    log_data = {
        "operation": operation,
        "collection": collection,
        "success": success
    }

    if duration_ms is not None:
        log_data["duration_ms"] = duration_ms

    if error:
        log_data["error"] = error

    if metadata:
        log_data.update(metadata)

    if success:
        logger.info(f"Qdrant operation successful: {log_data}")
    else:
        logger.error(f"Qdrant operation failed: {log_data}")


def validate_vector_dimensions(vector: List[float], expected_dimensions: int = 3072) -> bool:
    """
    Validate that a vector has the expected number of dimensions.

    Args:
        vector: Vector to validate
        expected_dimensions: Expected number of dimensions (default: 3072 for text-embedding-3-large)

    Returns:
        True if vector has correct dimensions, False otherwise

    Examples:
        >>> validate_vector_dimensions([0.1] * 3072)
        True

        >>> validate_vector_dimensions([0.1] * 1536)
        False
    """
    actual_dimensions = len(vector)

    if actual_dimensions != expected_dimensions:
        logger.warning(
            f"Vector dimension mismatch: expected {expected_dimensions}, "
            f"got {actual_dimensions}"
        )
        return False

    return True


def format_search_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format a Qdrant search result for API response.

    Args:
        result: Raw search result from Qdrant

    Returns:
        Formatted result with additional metadata

    Examples:
        >>> raw_result = {
        ...     "id": "123e4567-e89b-12d3-a456-426614174000",
        ...     "score": 0.95,
        ...     "payload": {"question_text": "What is BA?", "ka": "Strategy Analysis"}
        ... }
        >>> format_search_result(raw_result)
        {
            'id': '123e4567-e89b-12d3-a456-426614174000',
            'score': 0.95,
            'score_percentage': 95,
            'similarity': 'very_similar',
            'payload': {...}
        }
    """
    return {
        "id": result["id"],
        "score": result["score"],
        "score_percentage": calculate_score_percentage(result["score"]),
        "similarity": interpret_similarity_score(result["score"]),
        "payload": result["payload"]
    }
