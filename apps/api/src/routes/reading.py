"""
Reading content retrieval API endpoints.
Endpoints for retrieving reading chunks filtered by concept with semantic search fallback.
"""
import logging
import time
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.dependencies import get_current_user
from src.models.user import User
from src.repositories.concept_repository import ConceptRepository
from src.repositories.course_repository import CourseRepository
from src.repositories.reading_chunk_repository import ReadingChunkRepository
from src.schemas.reading_chunk import (
    ReadingChunkResponse,
    ReadingListResponse,
    ReadingQueryParams,
)
from src.services.reading_search_service import ReadingSearchService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Reading"])


def get_reading_chunk_repository(
    db: AsyncSession = Depends(get_db),
) -> ReadingChunkRepository:
    """Dependency for ReadingChunkRepository."""
    return ReadingChunkRepository(db)


def get_course_repository(db: AsyncSession = Depends(get_db)) -> CourseRepository:
    """Dependency for CourseRepository."""
    return CourseRepository(db)


def get_concept_repository(db: AsyncSession = Depends(get_db)) -> ConceptRepository:
    """Dependency for ConceptRepository."""
    return ConceptRepository(db)


async def get_concept_names_batch(
    concept_ids: list[UUID], concept_repo: ConceptRepository
) -> dict[UUID, str]:
    """
    Batch fetch concept names for multiple IDs in a single query.

    Args:
        concept_ids: List of concept UUIDs
        concept_repo: Concept repository for database access

    Returns:
        Dictionary mapping concept_id to concept_name
    """
    if not concept_ids:
        return {}

    concepts = await concept_repo.get_by_ids(concept_ids)
    return {concept.id: concept.name for concept in concepts}


@router.get(
    "/courses/{course_slug}/reading",
    response_model=ReadingListResponse,
    summary="Get reading content by concept",
    description=(
        "Retrieve reading chunks for specific concepts within a course. "
        "Uses direct concept filtering with semantic search fallback. "
        "Chunks are ranked by relevance (number of matching concepts). "
        "Requires authentication."
    ),
    responses={
        200: {"description": "Reading content retrieved successfully"},
        404: {"description": "Course not found"},
    },
)
async def get_reading_content(
    request: Request,
    course_slug: str,
    concept_ids: list[UUID] = Query(
        ..., description="Concept IDs to find reading for (required)"
    ),
    knowledge_area_id: str | None = Query(
        None, max_length=50, description="Filter by knowledge area ID"
    ),
    limit: int = Query(
        5, ge=1, le=20, description="Maximum number of chunks to return"
    ),
    chunk_repo: ReadingChunkRepository = Depends(get_reading_chunk_repository),
    course_repo: CourseRepository = Depends(get_course_repository),
    concept_repo: ConceptRepository = Depends(get_concept_repository),
    current_user: User = Depends(get_current_user),
) -> ReadingListResponse:
    """
    Get reading chunks for specified concepts with semantic search fallback.

    This endpoint is used by the adaptive learning engine to recommend reading
    content for knowledge gaps in the user's enrolled course.

    **Performance target:** <200ms response time

    **Fallback behavior:** If no chunks match the concept_ids directly,
    uses semantic search with concept names to find relevant content.
    """
    # Track request timing
    start_time = time.time()

    # Lookup course by slug
    course = await course_repo.get_active_by_slug(course_slug)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "COURSE_NOT_FOUND",
                    "message": f"Course '{course_slug}' not found or inactive",
                }
            },
        )

    # Build query params
    query_params = ReadingQueryParams(
        concept_ids=concept_ids,
        knowledge_area_id=knowledge_area_id,
        limit=limit,
    )

    # Try direct concept filtering first
    chunks, total = await chunk_repo.get_chunks_by_concepts(
        course_id=course.id, params=query_params
    )

    fallback_used = False

    # Fallback to semantic search if no results
    if not chunks:
        logger.info(
            "reading_fallback_to_semantic_search: course=%s concepts=%s",
            str(course.id),
            [str(cid) for cid in concept_ids],
        )

        # Batch fetch concept names for semantic search (single query)
        concept_name_map = await get_concept_names_batch(concept_ids, concept_repo)
        concept_names = list(concept_name_map.values())

        if concept_names:
            # Initialize semantic search service
            search_service = ReadingSearchService()

            try:
                chunks = await search_service.search_chunks_by_concept_names(
                    course_id=course.id,
                    concept_names=concept_names,
                    chunk_repository=chunk_repo,
                    limit=limit,
                )
                total = len(chunks)
                fallback_used = True
            finally:
                await search_service.close()

    # Batch fetch all concept names upfront (single query for all chunks)
    all_concept_ids = set(concept_ids)  # Start with requested concepts
    for chunk in chunks:
        all_concept_ids.update(chunk.concept_ids)

    concept_name_map = await get_concept_names_batch(list(all_concept_ids), concept_repo)

    # Build response items with concept names
    items = []
    for chunk in chunks:
        # Resolve concept names from pre-fetched map (no additional queries)
        chunk_concept_names = [
            concept_name_map.get(cid)
            for cid in chunk.concept_ids
            if cid in concept_name_map
        ]

        # Calculate relevance score (number of matching concepts)
        # Only for direct filtering (fallback uses semantic similarity)
        relevance_score = None
        if not fallback_used and chunk.concept_ids:
            # Count how many requested concepts are in this chunk
            matching_count = len(
                {str(cid) for cid in concept_ids}
                & {str(cid) for cid in chunk.concept_ids}
            )
            relevance_score = float(matching_count)

        items.append(
            ReadingChunkResponse(
                id=chunk.id,
                course_id=chunk.course_id,
                title=chunk.title,
                content=chunk.content,
                corpus_section=chunk.corpus_section,
                knowledge_area_id=chunk.knowledge_area_id,
                concept_ids=chunk.concept_ids,
                concept_names=chunk_concept_names,
                estimated_read_time_minutes=chunk.estimated_read_time_minutes,
                relevance_score=relevance_score,
            )
        )

    # Calculate response time
    response_time_ms = (time.time() - start_time) * 1000

    # Log performance warning if slow
    if response_time_ms > 200:
        logger.warning(
            "slow_reading_query: course=%s time=%.2fms concepts=%d results=%d fallback=%s",
            course_slug,
            response_time_ms,
            len(concept_ids),
            len(items),
            fallback_used,
        )

    # Add timing to response headers
    request.state.response_time_ms = response_time_ms

    logger.info(
        "reading_query_complete: course=%s time=%.2fms results=%d fallback=%s",
        course_slug,
        response_time_ms,
        len(items),
        fallback_used,
    )

    return ReadingListResponse(
        items=items,
        total=total,
        fallback_used=fallback_used,
    )
