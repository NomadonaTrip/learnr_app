"""
API routes for prerequisite status and mastery gates.
Story 4.11: Prerequisite-Based Curriculum Navigation
"""
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.dependencies import get_current_user
from src.models.user import User
from src.repositories.belief_repository import BeliefRepository
from src.repositories.concept_repository import ConceptRepository
from src.schemas.mastery_gate import (
    BulkUnlockStatusResponse,
    GateCheckResult,
    OverrideAttemptResponse,
    RecentUnlocksResponse,
)
from src.services.mastery_gate import MasteryGateService

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/concepts", tags=["prerequisites"])


def get_mastery_gate_service(
    session: AsyncSession = Depends(get_db),
) -> MasteryGateService:
    """Dependency to get MasteryGateService instance."""
    belief_repo = BeliefRepository(session)
    concept_repo = ConceptRepository(session)
    return MasteryGateService(
        session=session,
        belief_repository=belief_repo,
        concept_repository=concept_repo,
    )


@router.get(
    "/{concept_id}/prerequisites/status",
    response_model=GateCheckResult,
    summary="Get prerequisite status for a concept",
    description="""
    Check if all prerequisites for a concept are mastered.

    Returns unlock status, blocking prerequisites, and progress toward unlocking.

    **Mastery Gate Thresholds:**
    - P(mastery) >= 0.7
    - Confidence >= 0.6
    - Minimum 3 responses
    """,
)
async def get_prerequisite_status(
    concept_id: UUID,
    current_user: User = Depends(get_current_user),
    service: MasteryGateService = Depends(get_mastery_gate_service),
) -> GateCheckResult:
    """
    Get prerequisite mastery status for a specific concept.

    Returns whether the concept is unlocked and which prerequisites are blocking.
    """
    logger.info(
        "prerequisite_status_requested",
        user_id=str(current_user.id),
        concept_id=str(concept_id),
    )

    result = await service.check_prerequisites_mastered(
        user_id=current_user.id,
        concept_id=concept_id,
    )

    return result


@router.get(
    "/unlock-status",
    response_model=BulkUnlockStatusResponse,
    summary="Get unlock status for all concepts",
    description="""
    Get unlock status for all concepts in a course or knowledge area.

    Used by the dashboard to display curriculum progress and concept lock status.
    """,
)
async def get_bulk_unlock_status(
    course_id: UUID = Query(..., description="Course UUID"),
    ka_id: str | None = Query(None, description="Knowledge area ID filter"),
    current_user: User = Depends(get_current_user),
    service: MasteryGateService = Depends(get_mastery_gate_service),
) -> BulkUnlockStatusResponse:
    """
    Get unlock status for all concepts in a course or knowledge area.

    Returns counts of locked/unlocked concepts and per-concept status.
    """
    logger.info(
        "bulk_unlock_status_requested",
        user_id=str(current_user.id),
        course_id=str(course_id),
        knowledge_area_id=ka_id,
    )

    result = await service.get_bulk_unlock_status(
        user_id=current_user.id,
        course_id=course_id,
        knowledge_area_id=ka_id,
    )

    return result


@router.get(
    "/recent-unlocks",
    response_model=RecentUnlocksResponse,
    summary="Get recently unlocked concepts",
    description="""
    Get the most recently unlocked concepts for the current user.

    Useful for showing unlock notifications and celebrations.
    """,
)
async def get_recent_unlocks(
    limit: int = Query(5, ge=1, le=20, description="Maximum results to return"),
    current_user: User = Depends(get_current_user),
    service: MasteryGateService = Depends(get_mastery_gate_service),
) -> RecentUnlocksResponse:
    """
    Get recently unlocked concepts for the current user.

    Returns the most recent unlock events with concept names.
    """
    logger.info(
        "recent_unlocks_requested",
        user_id=str(current_user.id),
        limit=limit,
    )

    result = await service.get_recent_unlocks(
        user_id=current_user.id,
        limit=limit,
    )

    return result


@router.post(
    "/{concept_id}/attempt-locked",
    response_model=OverrideAttemptResponse,
    summary="Attempt to access a locked concept",
    description="""
    Allow advanced users to attempt questions on locked concepts.

    This endpoint logs the override attempt for analysis and returns
    the concept's current lock status. Override attempts are always
    allowed but are tracked for analytics.

    **Use Cases:**
    - Advanced learners who want to skip prerequisites
    - Users who already have domain knowledge
    - A/B testing prerequisite enforcement effectiveness
    """,
)
async def attempt_locked_concept(
    concept_id: UUID,
    current_user: User = Depends(get_current_user),
    service: MasteryGateService = Depends(get_mastery_gate_service),
) -> OverrideAttemptResponse:
    """
    Attempt to access a concept that may be locked.

    Logs the override attempt and returns current lock status.
    Advanced users can proceed even if prerequisites aren't mastered.
    """
    # Get current lock status
    gate_result = await service.check_prerequisites_mastered(
        user_id=current_user.id,
        concept_id=concept_id,
    )

    was_locked = not gate_result.is_unlocked

    # Log the override attempt for analysis
    logger.info(
        "prerequisite_override_attempt",
        user_id=str(current_user.id),
        concept_id=str(concept_id),
        concept_name=gate_result.concept_name,
        was_locked=was_locked,
        blocking_count=len(gate_result.blocking_prerequisites),
        mastery_progress=gate_result.mastery_progress,
    )

    # Build response message
    if was_locked:
        blocking_names = [p.name for p in gate_result.blocking_prerequisites[:3]]
        if len(gate_result.blocking_prerequisites) > 3:
            blocking_names.append(
                f"and {len(gate_result.blocking_prerequisites) - 3} more"
            )
        message = (
            f"Proceeding with locked concept. "
            f"Blocking prerequisites: {', '.join(blocking_names)}. "
            f"Consider mastering these first for better learning outcomes."
        )
    else:
        message = "Concept is already unlocked. No override needed."

    return OverrideAttemptResponse(
        concept_id=gate_result.concept_id,
        concept_name=gate_result.concept_name,
        was_locked=was_locked,
        override_allowed=True,
        blocking_prerequisites=gate_result.blocking_prerequisites,
        mastery_progress=gate_result.mastery_progress,
        message=message,
    )
