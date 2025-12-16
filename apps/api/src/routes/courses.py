"""
Course API endpoints.
Public endpoints for listing and retrieving course information.
"""
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.repositories.course_repository import CourseRepository
from src.schemas.course import (
    CourseDetailResponse,
    CourseListItem,
    CourseListResponse,
    CourseResponse,
    KnowledgeArea,
)

router = APIRouter(prefix="/courses", tags=["Courses"])


def get_course_repository(db: AsyncSession = Depends(get_db)) -> CourseRepository:
    """Dependency for CourseRepository."""
    return CourseRepository(db)


@router.get(
    "",
    response_model=CourseListResponse,
    summary="List all active courses",
    description="Returns a list of all active courses. No authentication required.",
    responses={
        200: {"description": "List of courses retrieved successfully"}
    }
)
async def list_courses(
    repo: CourseRepository = Depends(get_course_repository),
) -> CourseListResponse:
    """
    List all active courses.

    Returns abbreviated course information suitable for display in a course catalog.
    """
    courses = await repo.get_all_active()

    course_items: list[CourseListItem] = []
    for course in courses:
        knowledge_areas = course.knowledge_areas or []
        course_items.append(
            CourseListItem(
                id=course.id,
                slug=course.slug,
                name=course.name,
                description=course.description,
                corpus_name=course.corpus_name,
                icon_url=course.icon_url,
                color_hex=course.color_hex,
                knowledge_area_count=len(knowledge_areas),
            )
        )

    return CourseListResponse(
        data=course_items,
        meta={
            "timestamp": datetime.now(UTC).isoformat(),
            "version": "v1",
            "count": len(course_items),
        },
    )


@router.get(
    "/{slug}",
    response_model=CourseDetailResponse,
    summary="Get course details by slug",
    description="Returns full course details including knowledge areas. No authentication required.",
    responses={
        200: {"description": "Course details retrieved successfully"},
        404: {"description": "Course not found"},
    }
)
async def get_course_by_slug(
    slug: str,
    repo: CourseRepository = Depends(get_course_repository),
) -> CourseDetailResponse:
    """
    Get course details by slug.

    Returns full course details including all knowledge areas and configuration.
    """
    course = await repo.get_active_by_slug(slug)

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "COURSE_NOT_FOUND",
                    "message": f"Course with slug '{slug}' not found",
                }
            },
        )

    # Parse knowledge areas from JSONB
    knowledge_areas = [
        KnowledgeArea(**ka) for ka in (course.knowledge_areas or [])
    ]

    course_response = CourseResponse(
        id=course.id,
        slug=course.slug,
        name=course.name,
        description=course.description,
        corpus_name=course.corpus_name,
        knowledge_areas=knowledge_areas,
        default_diagnostic_count=course.default_diagnostic_count,
        mastery_threshold=course.mastery_threshold,
        gap_threshold=course.gap_threshold,
        confidence_threshold=course.confidence_threshold,
        icon_url=course.icon_url,
        color_hex=course.color_hex,
        is_active=course.is_active,
        is_public=course.is_public,
        created_at=course.created_at,
        updated_at=course.updated_at,
    )

    return CourseDetailResponse(
        data=course_response,
        meta={
            "timestamp": datetime.now(UTC).isoformat(),
            "version": "v1",
        },
    )
