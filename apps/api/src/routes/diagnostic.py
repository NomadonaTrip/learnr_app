"""
Diagnostic API endpoints.
Provides endpoints for diagnostic assessment question selection and answer submission.
Implements belief state updates using Bayesian Knowledge Tracing (BKT).
Includes session management for resumable diagnostics.
"""
import json
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.redis_client import get_redis
from src.db.session import get_db
from src.dependencies import get_current_user
from src.models.belief_state import BeliefState
from src.models.concept import Concept
from src.models.enrollment import Enrollment
from src.models.user import User
from src.repositories.belief_repository import BeliefRepository
from src.repositories.concept_repository import ConceptRepository
from src.repositories.diagnostic_session_repository import DiagnosticSessionRepository
from src.repositories.question_repository import QuestionRepository
from src.schemas.diagnostic import (
    DiagnosticAnswerRequest,
    DiagnosticAnswerResponse,
    DiagnosticQuestionResponse,
    DiagnosticQuestionsResponse,
)
from src.schemas.diagnostic_results import (
    DiagnosticFeedbackRequest,
    DiagnosticFeedbackResponse,
    DiagnosticResultsResponse,
)
from src.schemas.diagnostic_session import (
    DiagnosticResetRequest,
    DiagnosticResetResponse,
    DiagnosticSessionStatus,
)
from src.services.belief_initialization_service import BeliefInitializationService
from src.services.belief_updater import BeliefUpdater
from src.services.diagnostic_results_service import DiagnosticResultsService
from src.services.diagnostic_service import DiagnosticService
from src.services.diagnostic_session_service import DiagnosticSessionService

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


def get_belief_initialization_service(
    belief_repo: BeliefRepository = Depends(get_belief_repository),
    concept_repo: ConceptRepository = Depends(get_concept_repository),
) -> BeliefInitializationService:
    """Dependency for BeliefInitializationService."""
    return BeliefInitializationService(belief_repo, concept_repo)


def get_diagnostic_session_repository(
    db: AsyncSession = Depends(get_db),
) -> DiagnosticSessionRepository:
    """Dependency for DiagnosticSessionRepository."""
    return DiagnosticSessionRepository(db)


def get_diagnostic_session_service(
    session_repo: DiagnosticSessionRepository = Depends(get_diagnostic_session_repository),
    belief_repo: BeliefRepository = Depends(get_belief_repository),
    question_repo: QuestionRepository = Depends(get_question_repository),
    diagnostic_service: DiagnosticService = Depends(get_diagnostic_service),
) -> DiagnosticSessionService:
    """Dependency for DiagnosticSessionService."""
    return DiagnosticSessionService(
        session_repo=session_repo,
        belief_repo=belief_repo,
        question_repo=question_repo,
        diagnostic_service=diagnostic_service,
    )


@router.get(
    "/questions",
    response_model=DiagnosticQuestionsResponse,
    summary="Get diagnostic questions",
    description=(
        "Returns diagnostic questions for assessment. Creates a new session or "
        "resumes an existing one. Questions are selected to maximize concept "
        "coverage across the course corpus."
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
    current_user: User = Depends(get_current_user),
    session_service: DiagnosticSessionService = Depends(get_diagnostic_session_service),
    belief_init_service: BeliefInitializationService = Depends(get_belief_initialization_service),
    concept_repo: ConceptRepository = Depends(get_concept_repository),
    db: AsyncSession = Depends(get_db),
) -> DiagnosticQuestionsResponse:
    """
    Get diagnostic questions for initial assessment.

    Creates a new diagnostic session or resumes an existing one:
    - If active session exists and not expired: resumes with remaining questions
    - If active session exists and expired: creates new session
    - If no active session: creates new session with optimal questions

    Automatically initializes belief states if not already initialized.
    """
    # Auto-initialize beliefs if not already done (idempotent)
    try:
        init_result = await belief_init_service.initialize_beliefs_for_user(
            current_user.id, course_id
        )
        # Commit the initialization (enrollment + belief states)
        await db.commit()
        if not init_result.already_initialized:
            logger.info(
                "Auto-initialized beliefs for diagnostic",
                user_id=str(current_user.id),
                course_id=str(course_id),
                belief_count=init_result.belief_count,
            )
        enrollment_id = init_result.enrollment_id
    except Exception as e:
        await db.rollback()
        logger.error(
            "Failed to auto-initialize beliefs",
            error=str(e),
            user_id=str(current_user.id),
            course_id=str(course_id),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "BELIEF_INITIALIZATION_FAILED",
                    "message": "Failed to initialize belief states for diagnostic",
                }
            },
        ) from e

    # Start or resume diagnostic session
    try:
        session, questions, is_resumed = await session_service.start_or_resume_session(
            user_id=current_user.id,
            enrollment_id=enrollment_id,
            course_id=course_id,
        )
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.error(
            "Failed to start/resume diagnostic session",
            error=str(e),
            user_id=str(current_user.id),
            course_id=str(course_id),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "SESSION_ERROR",
                    "message": "Failed to start diagnostic session",
                }
            },
        ) from e

    if not questions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "NO_QUESTIONS_AVAILABLE",
                    "message": "No active questions found for this course",
                }
            },
        )

    # Calculate coverage statistics
    total_concepts = await concept_repo.get_concept_count(course_id)
    covered_concepts: set[UUID] = set()
    for q in questions:
        if hasattr(q, 'question_concepts') and q.question_concepts:
            covered_concepts.update(qc.concept_id for qc in q.question_concepts)

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
        for q in questions
    ]

    return DiagnosticQuestionsResponse(
        questions=question_responses,
        session_id=session.id,
        session_status=DiagnosticSessionStatus(session.status),
        current_index=session.current_index,
        total=session.questions_total,
        concepts_covered=len(covered_concepts),
        coverage_percentage=round(coverage_percentage, 3),
        is_resumed=is_resumed,
    )


@router.post(
    "/answer",
    response_model=DiagnosticAnswerResponse,
    summary="Submit diagnostic answer",
    description=(
        "Records an answer for a diagnostic question and updates belief states. "
        "Validates that the answer matches the expected session position. "
        "No immediate feedback (correct/incorrect) is provided during diagnostic."
    ),
    responses={
        200: {"description": "Answer recorded and beliefs updated successfully"},
        400: {"description": "Invalid session or question position"},
        401: {"description": "Authentication required"},
        404: {"description": "Question or session not found"},
        500: {"description": "Internal server error"},
    },
)
async def submit_diagnostic_answer(
    request: DiagnosticAnswerRequest,
    current_user: User = Depends(get_current_user),
    question_repo: QuestionRepository = Depends(get_question_repository),
    session_service: DiagnosticSessionService = Depends(get_diagnostic_session_service),
    belief_updater: BeliefUpdater = Depends(get_belief_updater),
    db: AsyncSession = Depends(get_db),
) -> DiagnosticAnswerResponse:
    """
    Submit an answer for a diagnostic question.

    This endpoint:
    1. Validates the session belongs to the user and is active
    2. Validates the question matches the expected position in session
    3. Updates belief states for all concepts linked to the question using BKT
    4. Advances session progress
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

    # Determine correctness (compare with stored correct answer)
    is_correct = request.selected_answer == question.correct_answer

    # Update belief states using BKT
    try:
        updated_concept_ids = await belief_updater.update_beliefs(
            user_id=current_user.id,
            question=question,
            is_correct=is_correct,
        )
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

    # Update session progress
    try:
        session = await session_service.record_answer(
            session_id=request.session_id,
            question_id=request.question_id,
            user_id=current_user.id,
        )
        await db.commit()
    except ValueError as e:
        await db.rollback()
        logger.warning(
            "Session validation failed",
            error=str(e),
            user_id=str(current_user.id),
            session_id=str(request.session_id),
            question_id=str(request.question_id),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "SESSION_VALIDATION_FAILED",
                    "message": str(e),
                }
            },
        ) from e
    except Exception as e:
        await db.rollback()
        logger.error(
            "Failed to record answer in session",
            error=str(e),
            user_id=str(current_user.id),
            session_id=str(request.session_id),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "SESSION_UPDATE_FAILED",
                    "message": "Failed to update session progress",
                }
            },
        ) from e

    # Also store answer in Redis for results calculation
    try:
        redis = await get_redis()
        redis_key = f"diagnostic:session:{current_user.id}"
        session_data = await redis.get(redis_key)
        if session_data:
            redis_session = json.loads(session_data)
        else:
            redis_session = {"answers": {}, "total": session.questions_total}

        redis_session["answers"][str(request.question_id)] = request.selected_answer
        await redis.setex(redis_key, DIAGNOSTIC_CACHE_TTL, json.dumps(redis_session))
    except Exception as e:
        # Log but don't fail - session progress already saved
        logger.warning(
            "Failed to update Redis session (session progress already saved)",
            error=str(e),
            user_id=str(current_user.id),
        )

    logger.info(
        "Diagnostic answer recorded",
        user_id=str(current_user.id),
        session_id=str(request.session_id),
        question_id=str(request.question_id),
        progress=session.current_index,
        total=session.questions_total,
        concepts_updated=len(updated_concept_ids),
    )

    return DiagnosticAnswerResponse(
        is_recorded=True,
        concepts_updated=[str(cid) for cid in updated_concept_ids],
        diagnostic_progress=session.current_index,
        diagnostic_total=session.questions_total,
        session_status=DiagnosticSessionStatus(session.status),
    )


@router.get(
    "/results",
    response_model=DiagnosticResultsResponse,
    summary="Get diagnostic results",
    description=(
        "Returns comprehensive diagnostic results after completing the assessment. "
        "Includes session status, coverage statistics, knowledge area breakdown, "
        "identified gaps, and personalized recommendations."
    ),
    responses={
        200: {"description": "Diagnostic results retrieved successfully"},
        401: {"description": "Authentication required"},
        404: {"description": "No completed diagnostic found"},
        500: {"description": "Internal server error"},
    },
)
async def get_diagnostic_results(
    course_id: UUID = Query(..., description="Course UUID to get results for"),
    current_user: User = Depends(get_current_user),
    belief_repo: BeliefRepository = Depends(get_belief_repository),
    session_repo: DiagnosticSessionRepository = Depends(get_diagnostic_session_repository),
    db: AsyncSession = Depends(get_db),
) -> DiagnosticResultsResponse:
    """
    Get diagnostic results after completing the assessment.

    Returns comprehensive knowledge profile including:
    - Overall coverage statistics (total, touched, percentage)
    - Classification counts (mastered, gaps, uncertain)
    - Per-knowledge area breakdown with estimated mastery
    - Top 10 identified knowledge gaps
    - Personalized recommendations for next steps

    Requires at least one diagnostic answer to have been submitted.
    """
    # Verify user has an enrollment for this course (or create one if beliefs exist)
    from sqlalchemy import select
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    enrollment_result = await db.execute(
        select(Enrollment)
        .where(Enrollment.user_id == current_user.id)
        .where(Enrollment.course_id == course_id)
        .where(Enrollment.status == "active")
    )
    enrollment = enrollment_result.scalar_one_or_none()

    if not enrollment:
        # Check if user has beliefs for this course - if so, create enrollment
        # This handles legacy users who completed diagnostic before enrollment was enforced
        belief_check = await db.execute(
            select(BeliefState)
            .join(Concept, BeliefState.concept_id == Concept.id)
            .where(BeliefState.user_id == current_user.id)
            .where(Concept.course_id == course_id)
            .limit(1)
        )
        has_beliefs = belief_check.scalar_one_or_none() is not None

        if has_beliefs:
            # User has beliefs but no enrollment - create enrollment
            enrollment_stmt = pg_insert(Enrollment).values(
                user_id=current_user.id,
                course_id=course_id,
                status="active",
            ).on_conflict_do_nothing(
                index_elements=["user_id", "course_id"]
            )
            await db.execute(enrollment_stmt)
            await db.commit()

            logger.info(
                "Created missing enrollment for user with existing beliefs",
                user_id=str(current_user.id),
                course_id=str(course_id),
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "code": "NO_ENROLLMENT",
                        "message": "No active enrollment found for this course",
                    }
                },
            )

    # Check if user has completed any diagnostic answers (has touched concepts)
    # This is determined by checking if any belief states have response_count > 0
    summary = await belief_repo.get_belief_summary(current_user.id)

    if summary["total"] == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "NO_DIAGNOSTIC_COMPLETED",
                    "message": "No diagnostic data found. Please complete the diagnostic assessment first.",
                }
            },
        )

    # Check for at least some responses
    touched_count = (
        summary["mastered"] + summary["gap"] + summary["borderline"]
    )
    # Also check Redis session for answer count and retrieve answers for scoring
    answers: dict[str, str] = {}
    try:
        redis = await get_redis()
        session_key = f"diagnostic:session:{current_user.id}"
        session_data = await redis.get(session_key)
        if session_data:
            session = json.loads(session_data)
            answers = session.get("answers", {})
            if len(answers) == 0 and touched_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "error": {
                            "code": "NO_DIAGNOSTIC_COMPLETED",
                            "message": "No diagnostic answers recorded. Please complete the diagnostic assessment first.",
                        }
                    },
                )
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(
            "Redis session check failed, proceeding with belief check only",
            error=str(e),
            user_id=str(current_user.id),
        )

    # Look up session status
    session_id = None
    session_status = None
    try:
        # Check for completed session first
        completed_session = await session_repo.get_completed_session(
            user_id=current_user.id,
            enrollment_id=enrollment.id if enrollment else None,
        )
        if completed_session:
            session_id = completed_session.id
            session_status = DiagnosticSessionStatus(completed_session.status)
        else:
            # Check for active session
            active_session = await session_repo.get_active_session(
                user_id=current_user.id,
                enrollment_id=enrollment.id if enrollment else None,
            )
            if active_session:
                session_id = active_session.id
                session_status = DiagnosticSessionStatus(active_session.status)
    except Exception as e:
        logger.warning(
            "Failed to fetch session status for results",
            error=str(e),
            user_id=str(current_user.id),
        )

    # Compute and return results (pass answers for score calculation)
    results_service = DiagnosticResultsService(db)
    try:
        results = await results_service.compute_diagnostic_results(
            user_id=current_user.id,
            course_id=course_id,
            answers=answers,
        )
        # Add session info to results
        results.session_id = session_id
        results.session_status = session_status
        return results
    except Exception as e:
        logger.error(
            "Failed to compute diagnostic results",
            error=str(e),
            user_id=str(current_user.id),
            course_id=str(course_id),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "RESULTS_COMPUTATION_FAILED",
                    "message": "Failed to compute diagnostic results",
                }
            },
        ) from e


@router.post(
    "/feedback",
    response_model=DiagnosticFeedbackResponse,
    summary="Submit diagnostic feedback",
    description=(
        "Submit post-diagnostic survey feedback. "
        "Records user's accuracy rating (1-5) and optional comment."
    ),
    responses={
        200: {"description": "Feedback recorded successfully"},
        401: {"description": "Authentication required"},
        500: {"description": "Internal server error"},
    },
)
async def submit_diagnostic_feedback(
    request: DiagnosticFeedbackRequest,
    course_id: UUID = Query(..., description="Course UUID for the diagnostic"),
    current_user: User = Depends(get_current_user),
) -> DiagnosticFeedbackResponse:
    """
    Submit post-diagnostic feedback survey.

    Records:
    - Accuracy rating (1-5 stars): "How accurate does this feel?"
    - Optional comment for additional feedback

    Feedback is stored in Redis for analytics (MVP implementation).
    Future: Store in dedicated diagnostic_feedback table.
    """
    feedback_key = f"diagnostic:feedback:{current_user.id}:{course_id}"

    try:
        redis = await get_redis()

        feedback_data = {
            "user_id": str(current_user.id),
            "course_id": str(course_id),
            "rating": request.rating,
            "comment": request.comment,
            "submitted_at": json.dumps(None),  # Placeholder for timestamp
        }

        # Store feedback in Redis (24 hour TTL for MVP)
        await redis.setex(feedback_key, 86400, json.dumps(feedback_data))

        logger.info(
            "Diagnostic feedback submitted",
            user_id=str(current_user.id),
            course_id=str(course_id),
            rating=request.rating,
        )

        return DiagnosticFeedbackResponse(
            success=True,
            message="Thank you for your feedback!",
        )

    except Exception as e:
        logger.error(
            "Failed to store diagnostic feedback",
            error=str(e),
            user_id=str(current_user.id),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "FEEDBACK_STORAGE_FAILED",
                    "message": "Failed to store feedback",
                }
            },
        ) from e


@router.post(
    "/reset",
    response_model=DiagnosticResetResponse,
    summary="Reset diagnostic",
    description=(
        "Reset diagnostic session and all belief states. "
        "Requires confirmation string 'RESET DIAGNOSTIC' to prevent accidental resets. "
        "This allows the user to retake the diagnostic from scratch."
    ),
    responses={
        200: {"description": "Diagnostic reset successfully"},
        400: {"description": "Confirmation required or enrollment not found"},
        401: {"description": "Authentication required"},
        500: {"description": "Internal server error"},
    },
)
async def reset_diagnostic(
    request: DiagnosticResetRequest,
    course_id: UUID = Query(..., description="Course UUID for the diagnostic to reset"),
    current_user: User = Depends(get_current_user),
    session_service: DiagnosticSessionService = Depends(get_diagnostic_session_service),
    db: AsyncSession = Depends(get_db),
) -> DiagnosticResetResponse:
    """
    Reset diagnostic session and belief states.

    This endpoint:
    1. Requires explicit confirmation ('RESET DIAGNOSTIC') to prevent accidents
    2. Marks any active session as 'reset'
    3. Resets all belief states to Beta(1,1) for the course
    4. Clears Redis session data

    After reset, the user can start a fresh diagnostic assessment.
    """
    # Validate confirmation
    if request.confirmation != "RESET DIAGNOSTIC":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "CONFIRMATION_REQUIRED",
                    "message": "Confirmation text must be 'RESET DIAGNOSTIC'",
                }
            },
        )

    # Get enrollment for this course
    enrollment_result = await db.execute(
        select(Enrollment)
        .where(Enrollment.user_id == current_user.id)
        .where(Enrollment.course_id == course_id)
        .where(Enrollment.status == "active")
    )
    enrollment = enrollment_result.scalar_one_or_none()

    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "NO_ENROLLMENT",
                    "message": "No active enrollment found for this course",
                }
            },
        )

    # Reset diagnostic
    try:
        result = await session_service.reset_diagnostic(
            user_id=current_user.id,
            enrollment_id=enrollment.id,
        )
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.error(
            "Failed to reset diagnostic",
            error=str(e),
            user_id=str(current_user.id),
            course_id=str(course_id),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "RESET_FAILED",
                    "message": "Failed to reset diagnostic",
                }
            },
        ) from e

    # Clear Redis session data
    try:
        redis = await get_redis()
        await redis.delete(f"diagnostic:session:{current_user.id}")
        await redis.delete(f"diagnostic:questions:{current_user.id}:{course_id}")
    except Exception as e:
        # Log but don't fail - database reset already succeeded
        logger.warning(
            "Failed to clear Redis session data",
            error=str(e),
            user_id=str(current_user.id),
        )

    logger.info(
        "Diagnostic reset completed",
        user_id=str(current_user.id),
        course_id=str(course_id),
        session_cleared=result["session_cleared"],
        beliefs_reset=result["beliefs_reset_count"],
    )

    return DiagnosticResetResponse(
        message="Diagnostic reset successfully",
        session_cleared=result["session_cleared"],
        beliefs_reset_count=result["beliefs_reset_count"],
        can_retake=True,
    )
