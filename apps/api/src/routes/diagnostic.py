"""
Diagnostic API endpoints.
Provides endpoints for diagnostic assessment question selection and answer submission.
Implements belief state updates using Bayesian Knowledge Tracing (BKT).
"""
import json
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
from src.repositories.question_repository import QuestionRepository
from src.schemas.diagnostic import (
    DiagnosticAnswerRequest,
    DiagnosticAnswerResponse,
    DiagnosticQuestionResponse,
    DiagnosticQuestionsResponse,
)
from src.services.belief_updater import BeliefUpdater
from src.services.diagnostic_service import DiagnosticService

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/diagnostic", tags=["Diagnostic"])

# Cache configuration
DIAGNOSTIC_CACHE_TTL = 1800  # 30 minutes


def get_question_repository(db: AsyncSession = Depends(get_db)) -> QuestionRepository:
    """Dependency for QuestionRepository."""
    return QuestionRepository(db)


def get_concept_repository(db: AsyncSession = Depends(get_db)) -> ConceptRepository:
    """Dependency for ConceptRepository."""
    return ConceptRepository(db)


def get_diagnostic_service(
    question_repo: QuestionRepository = Depends(get_question_repository),
    concept_repo: ConceptRepository = Depends(get_concept_repository),
) -> DiagnosticService:
    """Dependency for DiagnosticService."""
    return DiagnosticService(question_repo, concept_repo)


def get_belief_repository(db: AsyncSession = Depends(get_db)) -> BeliefRepository:
    """Dependency for BeliefRepository."""
    return BeliefRepository(db)


def get_belief_updater(
    belief_repo: BeliefRepository = Depends(get_belief_repository),
) -> BeliefUpdater:
    """Dependency for BeliefUpdater."""
    return BeliefUpdater(belief_repo)


@router.get(
    "/questions",
    response_model=DiagnosticQuestionsResponse,
    summary="Get diagnostic questions",
    description=(
        "Returns optimally selected diagnostic questions for initial assessment. "
        "Questions are selected to maximize concept coverage across the course corpus. "
        "Results are cached per user for 30 minutes (consistent on page refresh)."
    ),
    responses={
        200: {"description": "Diagnostic questions retrieved successfully"},
        401: {"description": "Authentication required"},
        404: {"description": "No questions available for course"},
        500: {"description": "Internal server error"},
    },
)
async def get_diagnostic_questions(
    course_id: UUID = Query(..., description="Course UUID to get diagnostic questions for"),
    target_count: int = Query(
        15,
        ge=12,
        le=20,
        description="Target number of questions (12-20, default 15)",
    ),
    current_user: User = Depends(get_current_user),
    service: DiagnosticService = Depends(get_diagnostic_service),
) -> DiagnosticQuestionsResponse:
    """
    Get diagnostic questions for initial assessment.

    Selects 12-20 questions using optimal coverage algorithm:
    - Maximizes concept coverage across the course corpus
    - Balances across knowledge areas (max 4 per KA)
    - Prefers high discrimination (informative) questions
    - Returns questions in randomized order

    Results are cached per user+course for 30 minutes to ensure
    consistent questions on page refresh.
    """
    cache_key = f"diagnostic:questions:{current_user.id}:{course_id}"

    # Check cache first
    try:
        redis = await get_redis()
        cached_data = await redis.get(cache_key)

        if cached_data:
            logger.info(
                "Diagnostic questions cache hit",
                user_id=str(current_user.id),
                course_id=str(course_id),
            )
            return DiagnosticQuestionsResponse(**json.loads(cached_data))
    except Exception as e:
        # Log but continue without cache
        logger.warning(
            "Redis cache check failed",
            error=str(e),
            user_id=str(current_user.id),
        )

    # Select questions
    selected_questions, covered_concepts, total_concepts = (
        await service.select_diagnostic_questions(course_id, target_count)
    )

    if not selected_questions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "NO_QUESTIONS_AVAILABLE",
                    "message": "No active questions found for this course",
                }
            },
        )

    # Calculate coverage percentage
    coverage_percentage = (
        len(covered_concepts) / total_concepts if total_concepts > 0 else 0.0
    )

    # Build response (excluding correct_answer and explanation)
    question_responses = [
        DiagnosticQuestionResponse(
            id=q.id,
            question_text=q.question_text,
            options=q.options,
            knowledge_area_id=q.knowledge_area_id,
            difficulty=q.difficulty,
            discrimination=q.discrimination,
        )
        for q in selected_questions
    ]

    response = DiagnosticQuestionsResponse(
        questions=question_responses,
        total=len(question_responses),
        concepts_covered=len(covered_concepts),
        coverage_percentage=round(coverage_percentage, 3),
    )

    # Cache the response
    try:
        redis = await get_redis()
        await redis.setex(
            cache_key,
            DIAGNOSTIC_CACHE_TTL,
            response.model_dump_json(),
        )
        logger.debug(
            "Cached diagnostic questions",
            user_id=str(current_user.id),
            course_id=str(course_id),
            ttl=DIAGNOSTIC_CACHE_TTL,
        )
    except Exception as e:
        # Log but don't fail the request
        logger.warning(
            "Failed to cache diagnostic questions",
            error=str(e),
            user_id=str(current_user.id),
        )

    return response


@router.post(
    "/answer",
    response_model=DiagnosticAnswerResponse,
    summary="Submit diagnostic answer",
    description=(
        "Records an answer for a diagnostic question and updates belief states. "
        "No immediate feedback (correct/incorrect) is provided during diagnostic. "
        "Belief states are updated using Bayesian Knowledge Tracing (BKT)."
    ),
    responses={
        200: {"description": "Answer recorded and beliefs updated successfully"},
        401: {"description": "Authentication required"},
        404: {"description": "Question not found"},
        409: {"description": "Answer already submitted for this question"},
        500: {"description": "Internal server error"},
    },
)
async def submit_diagnostic_answer(
    request: DiagnosticAnswerRequest,
    current_user: User = Depends(get_current_user),
    question_repo: QuestionRepository = Depends(get_question_repository),
    belief_updater: BeliefUpdater = Depends(get_belief_updater),
    db: AsyncSession = Depends(get_db),
) -> DiagnosticAnswerResponse:
    """
    Submit an answer for a diagnostic question.

    This endpoint:
    1. Validates the question exists and loads its concept mappings
    2. Determines correctness (compares selected_answer with correct_answer)
    3. Updates belief states for all concepts linked to the question using BKT
    4. Stores answer in Redis session for progress tracking
    5. Returns response WITHOUT correctness feedback (diagnostic mode)

    Belief updates are persisted immediately after each answer (not batched)
    to prevent data loss on session interruption.
    """
    # Verify question exists and load concepts for belief updates
    question = await question_repo.get_question_by_id(
        request.question_id, load_concepts=True
    )
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "QUESTION_NOT_FOUND",
                    "message": f"Question {request.question_id} not found",
                }
            },
        )

    # Check for duplicate submission
    session_key = f"diagnostic:session:{current_user.id}"
    try:
        redis = await get_redis()
        session_data = await redis.get(session_key)
        if session_data:
            session = json.loads(session_data)
            if str(request.question_id) in session.get("answers", {}):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "error": {
                            "code": "DUPLICATE_REQUEST",
                            "message": "Answer already submitted for this question",
                        }
                    },
                )
        else:
            session = {"answers": {}, "total": 15}
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(
            "Redis session check failed, proceeding without duplicate check",
            error=str(e),
            user_id=str(current_user.id),
        )
        session = {"answers": {}, "total": 15}

    # Determine correctness (compare with stored correct answer)
    is_correct = request.selected_answer == question.correct_answer

    # Update belief states using BKT
    try:
        updated_concept_ids = await belief_updater.update_beliefs(
            user_id=current_user.id,
            question=question,
            is_correct=is_correct,
        )

        # Commit the belief updates to database
        await db.commit()

    except Exception as e:
        await db.rollback()
        logger.error(
            "Failed to update beliefs",
            error=str(e),
            user_id=str(current_user.id),
            question_id=str(request.question_id),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "BELIEF_UPDATE_FAILED",
                    "message": "Failed to update belief states",
                }
            },
        ) from e

    # Store answer in Redis session for progress tracking
    try:
        redis = await get_redis()

        # Record answer (question_id -> selected_answer)
        session["answers"][str(request.question_id)] = request.selected_answer

        # Update session in Redis (30 min TTL)
        await redis.setex(session_key, DIAGNOSTIC_CACHE_TTL, json.dumps(session))

        logger.info(
            "Diagnostic answer recorded",
            user_id=str(current_user.id),
            question_id=str(request.question_id),
            progress=len(session["answers"]),
            concepts_updated=len(updated_concept_ids),
        )

    except Exception as e:
        # Log but don't fail - belief updates already committed
        logger.warning(
            "Failed to update Redis session (beliefs already saved)",
            error=str(e),
            user_id=str(current_user.id),
        )

    return DiagnosticAnswerResponse(
        is_recorded=True,
        concepts_updated=[str(cid) for cid in updated_concept_ids],
        diagnostic_progress=len(session["answers"]),
        diagnostic_total=session.get("total", 15),
    )
