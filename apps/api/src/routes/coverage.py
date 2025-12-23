"""
Coverage API endpoints (Story 4.5).
Provides endpoints for coverage progress tracking and gap analysis.
"""
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.redis_client import get_redis
from src.db.session import get_db
from src.dependencies import get_current_user
from src.models.user import User
from src.repositories.belief_repository import BeliefRepository
from src.repositories.concept_repository import ConceptRepository
from src.repositories.course_repository import CourseRepository
from src.schemas.coverage import (
    CoverageDetailReport,
    CoverageReport,
    GapConceptList,
)
from src.services.coverage_analyzer import CoverageAnalyzer

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/coverage", tags=["Coverage"])


# Dependency injection
def get_belief_repository(db: AsyncSession = Depends(get_db)) -> BeliefRepository:
    """Dependency for BeliefRepository."""
    return BeliefRepository(db)


def get_concept_repository(db: AsyncSession = Depends(get_db)) -> ConceptRepository:
    """Dependency for ConceptRepository."""
    return ConceptRepository(db)


def get_course_repository(db: AsyncSession = Depends(get_db)) -> CourseRepository:
    """Dependency for CourseRepository."""
    return CourseRepository(db)


async def get_coverage_analyzer(
    belief_repo: BeliefRepository = Depends(get_belief_repository),
    concept_repo: ConceptRepository = Depends(get_concept_repository),
    course_repo: CourseRepository = Depends(get_course_repository),
) -> CoverageAnalyzer:
    """Dependency for CoverageAnalyzer with Redis caching."""
    redis = await get_redis()
    return CoverageAnalyzer(
        belief_repository=belief_repo,
        concept_repository=concept_repo,
        course_repository=course_repo,
        redis_client=redis,
    )


@router.get(
    "",
    response_model=CoverageReport,
    summary="Get coverage summary",
    description=(
        "Returns coverage progress summary with knowledge area breakdown. "
        "Shows mastered, gaps, borderline, and uncertain concept counts. "
        "Results are cached for 5 minutes and invalidated on belief updates."
    ),
    responses={
        200: {"description": "Coverage summary retrieved successfully"},
        401: {"description": "Authentication required"},
        404: {"description": "Course not found"},
        500: {"description": "Internal server error"},
    },
)
async def get_coverage(
    course_id: UUID = Query(..., description="Course UUID to get coverage for"),
    current_user: User = Depends(get_current_user),
    coverage_analyzer: CoverageAnalyzer = Depends(get_coverage_analyzer),
) -> CoverageReport:
    """
    Get coverage progress summary.

    Returns:
    - total_concepts: Total concepts in the course corpus
    - mastered: Count of concepts with P(mastery) >= 0.8 and confidence >= 0.7
    - gaps: Count of concepts with P(mastery) < 0.5 and confidence >= 0.7
    - borderline: Count of concepts with 0.5 <= P(mastery) < 0.8 and confidence >= 0.7
    - uncertain: Count of concepts with confidence < 0.7
    - coverage_percentage: Mastery coverage (mastered / total)
    - confidence_percentage: Classification coverage ((mastered + gaps + borderline) / total)
    - estimated_questions_remaining: Heuristic estimate for full coverage
    - by_knowledge_area: Breakdown per knowledge area
    """
    try:
        report = await coverage_analyzer.analyze_coverage(
            user_id=current_user.id,
            course_id=course_id,
            use_cache=True,
        )
        return report
    except Exception as e:
        logger.error(
            "Failed to analyze coverage",
            error=str(e),
            user_id=str(current_user.id),
            course_id=str(course_id),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "COVERAGE_ANALYSIS_FAILED",
                    "message": "Failed to analyze coverage",
                }
            },
        ) from e


@router.get(
    "/details",
    response_model=CoverageDetailReport,
    summary="Get detailed coverage report",
    description=(
        "Returns full coverage report with concept-level details. "
        "Includes lists of mastered, gap, borderline, and uncertain concepts. "
        "Intended for debugging, analytics, or detailed progress views."
    ),
    responses={
        200: {"description": "Detailed coverage retrieved successfully"},
        401: {"description": "Authentication required"},
        404: {"description": "Course not found"},
        500: {"description": "Internal server error"},
    },
)
async def get_coverage_details(
    course_id: UUID = Query(..., description="Course UUID to get detailed coverage for"),
    current_user: User = Depends(get_current_user),
    coverage_analyzer: CoverageAnalyzer = Depends(get_coverage_analyzer),
) -> CoverageDetailReport:
    """
    Get detailed coverage report with concept lists.

    Returns everything from GET /coverage plus:
    - mastered_concepts: List of mastered concepts (sorted by probability desc)
    - gap_concepts: List of gap concepts (sorted by probability asc)
    - borderline_concepts: List of borderline concepts
    - uncertain_concepts: List of uncertain concepts (sorted by confidence)

    Note: This endpoint bypasses cache to ensure fresh data.
    """
    try:
        report = await coverage_analyzer.get_detailed_coverage(
            user_id=current_user.id,
            course_id=course_id,
        )
        return report
    except Exception as e:
        logger.error(
            "Failed to get detailed coverage",
            error=str(e),
            user_id=str(current_user.id),
            course_id=str(course_id),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "COVERAGE_DETAILS_FAILED",
                    "message": "Failed to get detailed coverage",
                }
            },
        ) from e


@router.get(
    "/gaps",
    response_model=GapConceptList,
    summary="Get gap concepts",
    description=(
        "Returns list of gap concepts sorted by priority (lowest probability first). "
        "Useful for focused practice mode to target weakest areas."
    ),
    responses={
        200: {"description": "Gap concepts retrieved successfully"},
        401: {"description": "Authentication required"},
        404: {"description": "Course not found"},
        500: {"description": "Internal server error"},
    },
)
async def get_gap_concepts(
    course_id: UUID = Query(..., description="Course UUID to get gaps for"),
    limit: int | None = Query(None, ge=1, le=100, description="Optional limit on gaps returned"),
    current_user: User = Depends(get_current_user),
    coverage_analyzer: CoverageAnalyzer = Depends(get_coverage_analyzer),
) -> GapConceptList:
    """
    Get list of gap concepts for focused practice.

    Returns concepts where:
    - P(mastery) < 0.5 (below gap threshold)
    - Confidence >= 0.7 (we're confident this is a gap)

    Sorted by probability ascending (worst gaps first), so the user
    can focus on their weakest areas.

    Args:
        course_id: Course UUID
        limit: Optional limit on number of gaps returned (default: all)

    Returns:
        GapConceptList with total_gaps count and sorted gap list
    """
    try:
        gaps = await coverage_analyzer.get_gap_concepts(
            user_id=current_user.id,
            course_id=course_id,
            limit=limit,
        )
        return gaps
    except Exception as e:
        logger.error(
            "Failed to get gap concepts",
            error=str(e),
            user_id=str(current_user.id),
            course_id=str(course_id),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "GAP_ANALYSIS_FAILED",
                    "message": "Failed to get gap concepts",
                }
            },
        ) from e
