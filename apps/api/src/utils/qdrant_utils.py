"""
Qdrant utility functions
Helper functions for working with Qdrant vector database
"""

import logging
from typing import Dict, Any, List
from qdrant_client.models import Filter, FieldCondition, MatchValue

logger = logging.getLogger(__name__)


def build_filter_conditions(filters: Dict[str, Any] | None) -> Filter | None:
    """
    Build Qdrant filter conditions from a dictionary.

    Args:
        filters: Dictionary of filter conditions with keys:
            - ka: str (Knowledge Area)
            - difficulty: str (Easy/Medium/Hard)
            - concept_tags: str (single tag to match)
            - section_ref: str (BABOK section reference)

    Returns:
        Filter object with conditions, or None if no filters provided

    Examples:
        >>> build_filter_conditions({"ka": "Requirements Life Cycle Management"})
        Filter(must=[FieldCondition(key='ka', match=MatchValue(value='Requirements Life Cycle Management'))])

        >>> build_filter_conditions({"ka": "Strategy Analysis", "difficulty": "Hard"})
        Filter(must=[...]) # Multiple conditions

        >>> build_filter_conditions(None)
        None
    """
    if not filters:
        return None

    must_conditions = []

    # Knowledge Area filter
    if "ka" in filters and filters["ka"]:
        must_conditions.append(
            FieldCondition(
                key="ka",
                match=MatchValue(value=filters["ka"])
            )
        )
        logger.debug(f"Added KA filter: {filters['ka']}")

    # Difficulty filter
    if "difficulty" in filters and filters["difficulty"]:
        must_conditions.append(
            FieldCondition(
                key="difficulty",
                match=MatchValue(value=filters["difficulty"])
            )
        )
        logger.debug(f"Added difficulty filter: {filters['difficulty']}")

    # Concept tags filter
    if "concept_tags" in filters and filters["concept_tags"]:
        must_conditions.append(
            FieldCondition(
                key="concept_tags",
                match=MatchValue(value=filters["concept_tags"])
            )
        )
        logger.debug(f"Added concept_tags filter: {filters['concept_tags']}")

    # Section reference filter (for BABOK chunks)
    if "section_ref" in filters and filters["section_ref"]:
        must_conditions.append(
            FieldCondition(
                key="section_ref",
                match=MatchValue(value=filters["section_ref"])
            )
        )
        logger.debug(f"Added section_ref filter: {filters['section_ref']}")

    # Return Filter object if we have conditions, None otherwise
    if must_conditions:
        logger.debug(f"Built filter with {len(must_conditions)} conditions")
        return Filter(must=must_conditions)

    return None


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
