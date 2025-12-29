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
from src.dependencies import get_active_enrollment, get_current_user
from src.models.enrollment import Enrollment
from src.models.user import User
from src.repositories.concept_repository import ConceptRepository
from src.repositories.course_repository import CourseRepository
from src.repositories.reading_chunk_repository import ReadingChunkRepository
from src.repositories.reading_queue_repository import ReadingQueueRepository
from src.schemas.reading import (
    BatchDismissRequest,
    BatchDismissResponse,
    EngagementUpdateRequest,
    EngagementUpdateResponse,
    PaginationMeta,
    QuestionContextResponse,
    ReadingQueueDetailResponse,
    ReadingQueueFilterPriority,
    ReadingQueueFilterStatus,
    ReadingQueueItemResponse,
    ReadingQueueListResponse,
    ReadingQueueSortBy,
    ReadingQueueStatusUpdate,
    ReadingStatsResponse,
    StatusUpdateRequest,
    StatusUpdateResponse,
)
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


def get_reading_queue_repository(
    db: AsyncSession = Depends(get_db),
) -> ReadingQueueRepository:
    """Dependency for ReadingQueueRepository."""
    return ReadingQueueRepository(db)


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


@router.get(
    "/reading/stats",
    response_model=ReadingStatsResponse,
    summary="Get reading queue statistics",
    description=(
        "Returns aggregated reading queue statistics (unread count, high-priority count) "
        "for the current user's active enrollment. Used by the navigation badge. "
        "Requires authentication."
    ),
    responses={
        200: {"description": "Reading stats retrieved successfully"},
        401: {"description": "Authentication required"},
        404: {"description": "No active enrollment found"},
    },
)
async def get_reading_stats(
    enrollment: Enrollment = Depends(get_active_enrollment),
    queue_repo: ReadingQueueRepository = Depends(get_reading_queue_repository),
) -> ReadingStatsResponse:
    """
    Get reading queue statistics for badge display.
    Story 5.6: Silent Badge Updates in Navigation

    Returns unread_count and high_priority_count for the user's active enrollment.
    Optimized to use a single database query with conditional counts.
    Leverages the idx_reading_queue_enrollment_status index.

    **Performance target:** <50ms response time
    """
    stats = await queue_repo.get_unread_stats(enrollment.id)

    logger.debug(
        "reading_stats: enrollment=%s unread=%d high_priority=%d",
        str(enrollment.id),
        stats["unread_count"],
        stats["high_priority_count"],
    )

    return ReadingStatsResponse(
        unread_count=stats["unread_count"],
        high_priority_count=stats["high_priority_count"],
    )


def get_ka_name_from_course(course_knowledge_areas: list, ka_id: str) -> str:
    """
    Look up knowledge area name from course's knowledge_areas JSONB.

    Args:
        course_knowledge_areas: List of KA dicts from course.knowledge_areas
        ka_id: Knowledge area ID to look up

    Returns:
        Knowledge area name, or ka_id if not found
    """
    if not course_knowledge_areas:
        return ka_id
    for ka in course_knowledge_areas:
        if ka.get("id") == ka_id:
            return ka.get("name", ka_id)
    return ka_id


@router.get(
    "/reading/queue",
    response_model=ReadingQueueListResponse,
    summary="Get reading queue items",
    description=(
        "Returns paginated list of reading queue items for the current user's "
        "active enrollment. Supports filtering by status, priority, and knowledge area. "
        "Supports sorting by priority, date, or relevance. "
        "Requires authentication."
    ),
    responses={
        200: {"description": "Reading queue retrieved successfully"},
        401: {"description": "Authentication required"},
        404: {"description": "No active enrollment found"},
    },
)
async def get_reading_queue(
    status: ReadingQueueFilterStatus = Query(
        ReadingQueueFilterStatus.UNREAD,
        description="Filter by status: unread, reading, completed, dismissed, all",
    ),
    ka_id: str | None = Query(
        None,
        max_length=50,
        description="Filter by Knowledge Area ID",
    ),
    priority: ReadingQueueFilterPriority | None = Query(
        None,
        description="Filter by priority: High, Medium, Low",
    ),
    sort_by: ReadingQueueSortBy = Query(
        ReadingQueueSortBy.PRIORITY,
        description="Sort order: priority, date, relevance",
    ),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    enrollment: Enrollment = Depends(get_active_enrollment),
    queue_repo: ReadingQueueRepository = Depends(get_reading_queue_repository),
    course_repo: CourseRepository = Depends(get_course_repository),
) -> ReadingQueueListResponse:
    """
    Get paginated reading queue items for the reading library page.
    Story 5.7: Reading Library Page with Queue Display

    Returns queue items with full metadata including:
    - Chunk title, preview, BABOK section
    - Knowledge area name
    - Priority and status
    - Word count and estimated read time
    - Question preview for context (why this was recommended)

    **Performance target:** <200ms response time
    """
    # Fetch queue items with joined details
    items_with_details, total_count = await queue_repo.get_queue_items(
        enrollment_id=enrollment.id,
        status=status,
        ka_id=ka_id,
        priority=priority,
        sort_by=sort_by,
        page=page,
        per_page=per_page,
    )

    # Fetch course for KA name lookup
    course = await course_repo.get_by_id(enrollment.course_id)
    course_kas = course.knowledge_areas if course else []

    # Build response items
    items = []
    for item in items_with_details:
        chunk = item.chunk
        question = item.question
        queue = item.queue

        # Calculate word count and read time
        word_count = len(chunk.content.split()) if chunk.content else 0
        estimated_read_minutes = max(1, word_count // 200)

        # Get preview (first 100 chars)
        preview = chunk.content[:100] if chunk.content else ""
        if len(chunk.content) > 100:
            preview = preview.rstrip() + "..."

        # Get question preview if available
        question_preview = None
        if question and question.question_text:
            question_preview = question.question_text[:80]
            if len(question.question_text) > 80:
                question_preview = question_preview.rstrip() + "..."

        # Look up KA name from course
        ka_name = get_ka_name_from_course(course_kas, chunk.knowledge_area_id)

        items.append(
            ReadingQueueItemResponse(
                queue_id=queue.id,
                chunk_id=chunk.id,
                title=chunk.title,
                preview=preview,
                babok_section=chunk.corpus_section,
                ka_name=ka_name,
                ka_id=chunk.knowledge_area_id,
                relevance_score=None,  # Could be computed if needed
                priority=queue.priority,
                status=queue.status,
                word_count=word_count,
                estimated_read_minutes=estimated_read_minutes,
                question_preview=question_preview,
                was_incorrect=True,  # Items are triggered by incorrect answers
                added_at=queue.added_at,
            )
        )

    # Calculate pagination metadata
    total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 0

    logger.debug(
        "reading_queue: enrollment=%s status=%s items=%d total=%d page=%d/%d",
        str(enrollment.id),
        status.value,
        len(items),
        total_count,
        page,
        total_pages,
    )

    return ReadingQueueListResponse(
        items=items,
        pagination=PaginationMeta(
            page=page,
            per_page=per_page,
            total_items=total_count,
            total_pages=total_pages,
        ),
    )


@router.get(
    "/reading/queue/{queue_id}",
    response_model=ReadingQueueDetailResponse,
    summary="Get reading queue item detail",
    description=(
        "Returns full details for a single reading queue item including the complete "
        "reading content. Tracks engagement by incrementing times_opened and setting "
        "first_opened_at on first view. Requires authentication."
    ),
    responses={
        200: {"description": "Reading item retrieved successfully"},
        401: {"description": "Authentication required"},
        404: {"description": "Queue item not found or access denied"},
    },
)
async def get_reading_queue_item(
    queue_id: UUID,
    enrollment: Enrollment = Depends(get_active_enrollment),
    queue_repo: ReadingQueueRepository = Depends(get_reading_queue_repository),
    course_repo: CourseRepository = Depends(get_course_repository),
    db: AsyncSession = Depends(get_db),
) -> ReadingQueueDetailResponse:
    """
    Get full reading queue item details including content.
    Story 5.8: Reading Item Detail View and Engagement Tracking

    Returns the complete reading chunk content along with queue metadata.
    Automatically increments times_opened and sets first_opened_at on first view.

    **Performance target:** <100ms response time
    """
    # Fetch the queue item with enrollment authorization check
    item = await queue_repo.get_queue_item_detail(enrollment.id, queue_id)

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "QUEUE_ITEM_NOT_FOUND",
                    "message": "Reading queue item not found",
                }
            },
        )

    # Increment times_opened and set first_opened_at (side effect)
    await queue_repo.increment_times_opened(queue_id, enrollment.id)
    await db.commit()

    # Refresh to get updated values
    item = await queue_repo.get_queue_item_detail(enrollment.id, queue_id)

    chunk = item.chunk
    question = item.question
    queue = item.queue

    # Fetch course for KA name lookup
    course = await course_repo.get_by_id(enrollment.course_id)
    course_kas = course.knowledge_areas if course else []

    # Calculate word count and read time
    word_count = len(chunk.content.split()) if chunk.content else 0
    estimated_read_minutes = max(1, word_count // 200)

    # Look up KA name from course
    ka_name = get_ka_name_from_course(course_kas, chunk.knowledge_area_id)

    # Build question context
    question_preview = None
    if question and question.question_text:
        question_preview = question.question_text[:80]
        if len(question.question_text) > 80:
            question_preview = question_preview.rstrip() + "..."

    question_context = QuestionContextResponse(
        question_id=question.id if question else None,
        question_preview=question_preview,
        was_incorrect=True,  # Items are triggered by incorrect answers
    )

    logger.debug(
        "reading_queue_detail: queue_id=%s chunk_id=%s enrollment=%s times_opened=%d",
        str(queue_id),
        str(chunk.id),
        str(enrollment.id),
        queue.times_opened,
    )

    return ReadingQueueDetailResponse(
        queue_id=queue.id,
        chunk_id=chunk.id,
        title=chunk.title,
        text_content=chunk.content,
        babok_section=chunk.corpus_section,
        ka_name=ka_name,
        priority=queue.priority,
        status=queue.status,
        word_count=word_count,
        estimated_read_minutes=estimated_read_minutes,
        times_opened=queue.times_opened,
        total_reading_time_seconds=queue.total_reading_time_seconds,
        first_opened_at=queue.first_opened_at,
        question_context=question_context,
        added_at=queue.added_at,
    )


@router.put(
    "/reading/queue/{queue_id}/engagement",
    response_model=EngagementUpdateResponse,
    summary="Update reading engagement metrics",
    description=(
        "Updates reading engagement by adding time spent to total_reading_time_seconds. "
        "Called when user navigates away from reading detail view. Requires authentication."
    ),
    responses={
        200: {"description": "Engagement updated successfully"},
        401: {"description": "Authentication required"},
        404: {"description": "Queue item not found or access denied"},
    },
)
async def update_reading_engagement(
    queue_id: UUID,
    engagement_data: EngagementUpdateRequest,
    enrollment: Enrollment = Depends(get_active_enrollment),
    queue_repo: ReadingQueueRepository = Depends(get_reading_queue_repository),
    db: AsyncSession = Depends(get_db),
) -> EngagementUpdateResponse:
    """
    Update reading engagement metrics.
    Story 5.8: Reading Item Detail View and Engagement Tracking

    Adds time_spent_seconds to total_reading_time_seconds.
    Time is capped at 30 minutes per session to prevent stale tab inflation.
    """
    # Update engagement with authorization check
    queue_item = await queue_repo.update_engagement(
        queue_id=queue_id,
        enrollment_id=enrollment.id,
        time_spent_seconds=engagement_data.time_spent_seconds,
    )

    if not queue_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "QUEUE_ITEM_NOT_FOUND",
                    "message": "Reading queue item not found",
                }
            },
        )

    await db.commit()

    logger.info(
        "reading_engagement_updated: queue_id=%s time_added=%d total=%d enrollment=%s",
        str(queue_id),
        engagement_data.time_spent_seconds,
        queue_item.total_reading_time_seconds,
        str(enrollment.id),
    )

    return EngagementUpdateResponse(
        queue_id=queue_item.id,
        total_reading_time_seconds=queue_item.total_reading_time_seconds,
        times_opened=queue_item.times_opened,
    )


@router.put(
    "/reading/queue/{queue_id}/status",
    response_model=StatusUpdateResponse,
    summary="Update reading queue item status",
    description=(
        "Updates the status of a reading queue item to 'completed' or 'dismissed'. "
        "Sets appropriate timestamp (completed_at or dismissed_at). Requires authentication."
    ),
    responses={
        200: {"description": "Status updated successfully"},
        401: {"description": "Authentication required"},
        404: {"description": "Queue item not found or access denied"},
    },
)
async def update_reading_status(
    queue_id: UUID,
    status_data: StatusUpdateRequest,
    enrollment: Enrollment = Depends(get_active_enrollment),
    queue_repo: ReadingQueueRepository = Depends(get_reading_queue_repository),
    db: AsyncSession = Depends(get_db),
) -> StatusUpdateResponse:
    """
    Update reading queue item status.
    Story 5.8: Reading Item Detail View and Engagement Tracking

    Valid statuses: 'completed' or 'dismissed'.
    Sets completed_at or dismissed_at timestamp accordingly.
    """
    # Update status with authorization check
    queue_item = await queue_repo.update_status(
        queue_id=queue_id,
        enrollment_id=enrollment.id,
        status=status_data.status,
    )

    if not queue_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "QUEUE_ITEM_NOT_FOUND",
                    "message": "Reading queue item not found",
                }
            },
        )

    await db.commit()

    logger.info(
        "reading_status_updated: queue_id=%s status=%s enrollment=%s",
        str(queue_id),
        status_data.status,
        str(enrollment.id),
    )

    return StatusUpdateResponse(
        queue_id=queue_item.id,
        status=queue_item.status,
        completed_at=queue_item.completed_at,
        dismissed_at=queue_item.dismissed_at,
    )


@router.post(
    "/reading/queue/batch-dismiss",
    response_model=BatchDismissResponse,
    summary="Batch dismiss multiple reading queue items",
    description=(
        "Dismisses multiple reading queue items in a single request. "
        "Invalid or non-existent IDs are silently skipped. "
        "Maximum 100 items per request. Requires authentication."
    ),
    responses={
        200: {"description": "Batch dismiss completed successfully"},
        401: {"description": "Authentication required"},
    },
)
async def batch_dismiss_reading_items(
    dismiss_data: BatchDismissRequest,
    enrollment: Enrollment = Depends(get_active_enrollment),
    queue_repo: ReadingQueueRepository = Depends(get_reading_queue_repository),
    db: AsyncSession = Depends(get_db),
) -> BatchDismissResponse:
    """
    Batch dismiss multiple reading queue items.
    Story 5.8: Reading Item Detail View and Engagement Tracking

    Use case: "Dismiss All Low Priority" button on library page.
    Only dismisses items belonging to the current enrollment (authorization).
    Silently skips invalid or non-existent IDs.
    """
    # Batch dismiss with authorization
    dismissed_count = await queue_repo.batch_dismiss(
        enrollment_id=enrollment.id,
        queue_ids=dismiss_data.queue_ids,
    )

    await db.commit()

    # Get remaining unread count
    remaining_count = await queue_repo.get_remaining_unread_count(enrollment.id)

    logger.info(
        "reading_batch_dismiss: enrollment=%s requested=%d dismissed=%d remaining=%d",
        str(enrollment.id),
        len(dismiss_data.queue_ids),
        dismissed_count,
        remaining_count,
    )

    return BatchDismissResponse(
        dismissed_count=dismissed_count,
        remaining_unread_count=remaining_count,
    )


@router.patch(
    "/reading/queue/{queue_id}",
    response_model=dict,
    summary="Update reading queue item status (legacy)",
    description=(
        "Legacy endpoint - Updates the status of a reading queue item. "
        "Prefer using PUT /reading/queue/{queue_id}/status instead. "
        "Valid statuses: reading, completed, dismissed. Requires authentication."
    ),
    responses={
        200: {"description": "Status updated successfully"},
        400: {"description": "Invalid status value"},
        401: {"description": "Authentication required"},
        404: {"description": "Queue item not found or access denied"},
    },
    deprecated=True,
)
async def update_reading_queue_status_legacy(
    queue_id: UUID,
    update_data: ReadingQueueStatusUpdate,
    enrollment: Enrollment = Depends(get_active_enrollment),
    queue_repo: ReadingQueueRepository = Depends(get_reading_queue_repository),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Legacy endpoint for updating reading queue item status.
    Story 5.8: Reading Detail Page

    Allows marking items as reading, completed, or dismissed.
    Use PUT /reading/queue/{queue_id}/status for new implementations.
    """
    # Validate status
    valid_statuses = {"reading", "completed", "dismissed"}
    if update_data.status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "INVALID_STATUS",
                    "message": f"Status must be one of: {', '.join(valid_statuses)}",
                }
            },
        )

    # Fetch the queue item with authorization
    item = await queue_repo.get_queue_item_detail(enrollment.id, queue_id)

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "QUEUE_ITEM_NOT_FOUND",
                    "message": "Reading queue item not found",
                }
            },
        )

    # Update status using repository method
    await queue_repo.update_status(queue_id, enrollment.id, update_data.status)
    await db.commit()

    logger.info(
        "reading_queue_status_updated: queue_id=%s status=%s enrollment=%s",
        str(queue_id),
        update_data.status,
        str(enrollment.id),
    )

    return {
        "success": True,
        "queue_id": str(queue_id),
        "status": update_data.status,
    }
