"""
Belief state API endpoints.
Provides endpoints for belief state initialization status and management.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.dependencies import get_current_user
from src.exceptions import BeliefInitializationError
from src.models.user import User
from src.repositories.belief_repository import BeliefRepository
from src.repositories.concept_repository import ConceptRepository
from src.schemas.belief_state import BeliefInitializationStatus, InitializationResult
from src.services.belief_initialization_service import BeliefInitializationService

router = APIRouter(prefix="/beliefs", tags=["Beliefs"])


def get_belief_repository(db: AsyncSession = Depends(get_db)) -> BeliefRepository:
    """Dependency for BeliefRepository."""
    return BeliefRepository(db)


def get_concept_repository(db: AsyncSession = Depends(get_db)) -> ConceptRepository:
    """Dependency for ConceptRepository."""
    return ConceptRepository(db)


def get_belief_initialization_service(
    belief_repo: BeliefRepository = Depends(get_belief_repository),
    concept_repo: ConceptRepository = Depends(get_concept_repository),
) -> BeliefInitializationService:
    """Dependency for BeliefInitializationService."""
    return BeliefInitializationService(belief_repo, concept_repo)


@router.get(
    "/stats",
    response_model=BeliefInitializationStatus,
    summary="Get belief initialization status",
    description="Returns the initialization status of belief states for the current user. Requires authentication.",
    responses={
        200: {"description": "Initialization status retrieved successfully"},
        401: {"description": "Authentication required"},
        500: {"description": "Internal server error"},
    }
)
async def get_belief_stats(
    course_id: UUID = Query(..., description="Course UUID to check belief status for"),
    current_user: User = Depends(get_current_user),
    service: BeliefInitializationService = Depends(get_belief_initialization_service),
) -> BeliefInitializationStatus:
    """
    Get belief initialization status for the current user.

    Returns information about whether beliefs have been initialized, including:
    - initialized: Whether belief states exist
    - total_concepts: Total concepts in the course corpus
    - belief_count: Number of belief_states records for the user
    - coverage_percentage: Percentage of concepts with belief states
    - created_at: When initialization occurred (earliest belief created_at)
    """
    return await service.get_initialization_status(current_user.id, course_id)


@router.post(
    "/initialize",
    response_model=InitializationResult,
    summary="Initialize belief states",
    description="Manually initialize belief states for the current user. Idempotent - safe to call multiple times.",
    responses={
        200: {"description": "Beliefs initialized successfully (or already initialized)"},
        401: {"description": "Authentication required"},
        500: {"description": "Initialization failed"},
    }
)
async def initialize_beliefs(
    course_id: UUID = Query(..., description="Course UUID to initialize beliefs for"),
    current_user: User = Depends(get_current_user),
    service: BeliefInitializationService = Depends(get_belief_initialization_service),
) -> InitializationResult:
    """
    Initialize belief states for the current user.

    Creates belief states with uninformative prior Beta(1, 1) for all concepts
    in the specified course.

    This endpoint is idempotent - calling it multiple times will not create
    duplicate beliefs. If beliefs are already initialized, returns success
    with already_initialized=True.
    """
    try:
        return await service.initialize_beliefs_for_user(current_user.id, course_id)
    except BeliefInitializationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "BELIEF_INITIALIZATION_FAILED",
                    "message": str(e),
                }
            },
        ) from e


@router.get(
    "/summary",
    summary="Get belief summary",
    description="Returns a summary of the user's belief states including counts by status.",
    responses={
        200: {"description": "Belief summary retrieved successfully"},
        401: {"description": "Authentication required"},
    }
)
async def get_belief_summary(
    current_user: User = Depends(get_current_user),
    belief_repo: BeliefRepository = Depends(get_belief_repository),
):
    """
    Get a summary of the user's belief states.

    Returns counts of beliefs grouped by status (mastered, gap, borderline, uncertain)
    along with average mastery mean across all beliefs.
    """
    summary = await belief_repo.get_belief_summary(current_user.id)
    return {
        "user_id": str(current_user.id),
        **summary
    }
