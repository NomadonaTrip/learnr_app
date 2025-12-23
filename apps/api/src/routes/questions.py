"""
Question retrieval API endpoints.
Endpoints for retrieving questions filtered by concept, knowledge area, and difficulty.
"""
import logging
import time
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.dependencies import get_current_user
from src.models.user import User
from src.repositories.course_repository import CourseRepository
from src.repositories.question_repository import QuestionRepository
from src.schemas.question import (
    PaginatedQuestionResponse,
    QuestionListResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Questions"])


def get_question_repository(db: AsyncSession = Depends(get_db)) -> QuestionRepository:
    """Dependency for QuestionRepository."""
    return QuestionRepository(db)


def get_course_repository(db: AsyncSession = Depends(get_db)) -> CourseRepository:
    """Dependency for CourseRepository."""
    return CourseRepository(db)


@router.get(
    "/courses/{course_slug}/questions",
    response_model=PaginatedQuestionResponse,
    summary="Get questions by concept",
    description=(
        "Retrieve questions filtered by concept, knowledge area, difficulty, "
        "perspectives, and competencies. "
        "Questions are scoped to the specified course. "
        "Excludes correct_answer and explanation (revealed after answer). "
        "Requires authentication."
    ),
    responses={
        200: {"description": "Questions retrieved successfully"},
        404: {"description": "Course not found"},
    },
)
async def get_questions(
    request: Request,
    course_slug: str,
    concept_ids: list[UUID] | None = Query(
        None,
        description="Filter by concept IDs (ANY match)"
    ),
    knowledge_area_id: str | None = Query(
        None,
        max_length=50,
        description="Filter by knowledge area ID"
    ),
    difficulty_min: float = Query(
        0.0,
        ge=0.0,
        le=1.0,
        description="Minimum difficulty (0.0-1.0)"
    ),
    difficulty_max: float = Query(
        1.0,
        ge=0.0,
        le=1.0,
        description="Maximum difficulty (0.0-1.0)"
    ),
    exclude_ids: list[UUID] | None = Query(
        None,
        description="Question IDs to exclude (recently asked)"
    ),
    perspectives: list[str] | None = Query(
        None,
        description="Filter by perspective IDs (e.g., 'agile', 'bi') - Story 2.15"
    ),
    competencies: list[str] | None = Query(
        None,
        description="Filter by competency IDs (e.g., 'analytical') - Story 2.15"
    ),
    limit: int = Query(
        10,
        ge=1,
        le=100,
        description="Maximum number of results"
    ),
    offset: int = Query(
        0,
        ge=0,
        description="Number of results to skip (pagination)"
    ),
    question_repo: QuestionRepository = Depends(get_question_repository),
    course_repo: CourseRepository = Depends(get_course_repository),
    current_user: User = Depends(get_current_user),
) -> PaginatedQuestionResponse:
    """
    Get questions filtered by concept, knowledge area, and difficulty.

    This endpoint is used by the BKT engine to select questions for specific
    concepts in the user's enrolled course.

    **Performance target:** <100ms response time

    **Security:** Questions returned exclude correct_answer and explanation
    to prevent answer leakage.
    """
    # Track request timing
    start_time = time.time()

    # Validate difficulty range
    if difficulty_min > difficulty_max:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "INVALID_DIFFICULTY_RANGE",
                    "message": f"difficulty_min ({difficulty_min}) cannot be greater than difficulty_max ({difficulty_max})",
                }
            },
        )

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

    # Get filtered questions with concept IDs
    questions_with_concepts, total = await question_repo.get_questions_filtered(
        course_id=course.id,
        concept_ids=concept_ids,
        knowledge_area_id=knowledge_area_id,
        difficulty_min=difficulty_min,
        difficulty_max=difficulty_max,
        exclude_ids=exclude_ids,
        perspectives=perspectives,
        competencies=competencies,
        limit=limit,
        offset=offset,
    )

    # Build response items (exclude correct_answer and explanation)
    items = [
        QuestionListResponse(
            id=question.id,
            course_id=question.course_id,
            question_text=question.question_text,
            options=question.options,
            knowledge_area_id=question.knowledge_area_id,
            difficulty=question.difficulty,
            discrimination=question.discrimination,
            concept_ids=concept_ids_list,
            # Story 2.15: Include secondary tags in response
            perspectives=question.perspectives or [],
            competencies=question.competencies or [],
        )
        for question, concept_ids_list in questions_with_concepts
    ]

    # Calculate response time and log if slow
    response_time_ms = (time.time() - start_time) * 1000

    if response_time_ms > 100:
        logger.warning(
            f"Slow question query: {response_time_ms:.2f}ms "
            f"(course={course_slug}, limit={limit}, filters={bool(concept_ids)})"
        )
    else:
        logger.info(
            f"Question query completed in {response_time_ms:.2f}ms "
            f"(returned {len(items)}/{total} questions)"
        )

    # Add response time header
    request.state.response_time_ms = response_time_ms

    # Build paginated response
    has_more = (offset + len(items)) < total

    return PaginatedQuestionResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
        has_more=has_more,
    )
