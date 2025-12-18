"""
Quiz API endpoints.
Provides endpoints for adaptive quiz session management.
Implements session lifecycle: create, get, pause, resume, end.
Also includes question selection and answer submission endpoints.

Story 4.3: Answer Submission and Immediate Feedback
"""
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.dependencies import (
    get_active_enrollment,
    get_belief_repository,
    get_current_user,
    get_question_repository,
    get_question_selector,
    get_quiz_answer_service,
    get_quiz_session_service,
)
from src.exceptions import AlreadyAnsweredError, InvalidQuestionError, InvalidSessionError
from src.models.enrollment import Enrollment
from src.models.user import User
from src.repositories.belief_repository import BeliefRepository
from src.repositories.question_repository import QuestionRepository
from src.schemas.question_selection import (
    QuestionSelectionRequest,
    QuestionSelectionResponse,
    SelectedQuestion,
)
from src.schemas.quiz import AnswerResponse, AnswerSubmission
from src.schemas.quiz_session import (
    QuestionStrategy,
    QuizSessionCreate,
    QuizSessionEndRequest,
    QuizSessionEndResponse,
    QuizSessionPauseResponse,
    QuizSessionResponse,
    QuizSessionResumeResponse,
    QuizSessionStartResponse,
    QuizSessionStatus,
    QuizSessionType,
)
from src.services.question_selector import QuestionSelector
from src.services.quiz_answer_service import QuizAnswerService
from src.services.quiz_session_service import QuizSessionService

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/quiz", tags=["Quiz"])


@router.post(
    "/session/start",
    response_model=QuizSessionStartResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a quiz session",
    description=(
        "Starts a new adaptive quiz session or returns an existing active session. "
        "Only one active session per user is allowed. If an active session exists "
        "and is not expired, it will be returned (is_resumed=true)."
    ),
    responses={
        201: {"description": "New session created"},
        200: {"description": "Existing session resumed (is_resumed=true)"},
        401: {"description": "Authentication required"},
        404: {"description": "No active enrollment found"},
        500: {"description": "Internal server error"},
    },
)
async def start_quiz_session(
    request: QuizSessionCreate = QuizSessionCreate(),
    current_user: User = Depends(get_current_user),
    enrollment: Enrollment = Depends(get_active_enrollment),
    session_service: QuizSessionService = Depends(get_quiz_session_service),
    db: AsyncSession = Depends(get_db),
) -> QuizSessionStartResponse:
    """
    Start or resume a quiz session.

    Creates a new adaptive quiz session with the specified configuration.
    If the user already has an active session (not ended), that session
    is returned instead (with is_resumed=true).

    Session types:
    - adaptive: Standard adaptive learning session (default)
    - focused: Focus on a specific knowledge area
    - review: Review previously seen questions
    - diagnostic: Diagnostic assessment (typically used via /diagnostic endpoint)

    Question strategies:
    - max_info_gain: Select questions that maximize information gain (default)
    - max_uncertainty: Select questions where user knowledge is most uncertain
    - prerequisite_first: Prioritize prerequisite concepts before advanced
    - balanced: Balance across all knowledge areas
    """
    try:
        session, is_resumed = await session_service.start_session(
            user_id=current_user.id,
            enrollment_id=enrollment.id,
            session_data=request,
        )
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.error(
            "Failed to start quiz session",
            error=str(e),
            user_id=str(current_user.id),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "SESSION_START_FAILED",
                    "message": "Failed to start quiz session",
                }
            },
        ) from e

    return QuizSessionStartResponse(
        session_id=session.id,
        session_type=QuizSessionType(session.session_type),
        question_strategy=QuestionStrategy(session.question_strategy),
        started_at=session.started_at,
        is_resumed=is_resumed,
        status=QuizSessionStatus(session.status),
        first_question=None,  # Placeholder for Story 4.2
    )


@router.get(
    "/session/{session_id}",
    response_model=QuizSessionResponse,
    summary="Get quiz session details",
    description=(
        "Returns the current state of a quiz session including progress, "
        "accuracy, and derived status."
    ),
    responses={
        200: {"description": "Session details retrieved successfully"},
        401: {"description": "Authentication required"},
        403: {"description": "User does not own this session"},
        404: {"description": "Session not found"},
    },
)
async def get_quiz_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    session_service: QuizSessionService = Depends(get_quiz_session_service),
) -> QuizSessionResponse:
    """
    Get quiz session details.

    Returns the full session state including:
    - Configuration (type, strategy, knowledge area filter)
    - Progress (total questions, correct count, accuracy)
    - Status (active, paused, completed, or expired)
    - Timestamps and version for optimistic locking
    """
    try:
        session = await session_service.get_session(session_id, current_user.id)
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "code": "SESSION_NOT_FOUND",
                        "message": "Quiz session not found",
                    }
                },
            ) from e
        if "unauthorized" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "code": "SESSION_ACCESS_DENIED",
                        "message": "You do not have access to this session",
                    }
                },
            ) from e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "SESSION_ERROR", "message": error_msg}},
        ) from e

    return QuizSessionResponse(
        id=session.id,
        user_id=session.user_id,
        enrollment_id=session.enrollment_id,
        session_type=QuizSessionType(session.session_type),
        question_strategy=QuestionStrategy(session.question_strategy),
        knowledge_area_filter=session.knowledge_area_filter,
        status=QuizSessionStatus(session.status),
        started_at=session.started_at,
        ended_at=session.ended_at,
        total_questions=session.total_questions,
        correct_count=session.correct_count,
        accuracy=session.accuracy,
        is_paused=session.is_paused,
        version=session.version,
    )


@router.post(
    "/session/{session_id}/pause",
    response_model=QuizSessionPauseResponse,
    summary="Pause a quiz session",
    description=(
        "Pauses an active quiz session. The session can be resumed later. "
        "Sessions auto-expire after 2 hours of inactivity."
    ),
    responses={
        200: {"description": "Session paused successfully"},
        400: {"description": "Session cannot be paused (already paused, ended, or expired)"},
        401: {"description": "Authentication required"},
        403: {"description": "User does not own this session"},
        404: {"description": "Session not found"},
    },
)
async def pause_quiz_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    session_service: QuizSessionService = Depends(get_quiz_session_service),
    db: AsyncSession = Depends(get_db),
) -> QuizSessionPauseResponse:
    """
    Pause an active quiz session.

    The session will remain paused until explicitly resumed or until it
    expires (2 hours after last activity). Progress is preserved.
    """
    try:
        session = await session_service.pause_session(session_id, current_user.id)
        await db.commit()
    except ValueError as e:
        await db.rollback()
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "code": "SESSION_NOT_FOUND",
                        "message": "Quiz session not found",
                    }
                },
            ) from e
        if "unauthorized" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "code": "SESSION_ACCESS_DENIED",
                        "message": "You do not have access to this session",
                    }
                },
            ) from e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "SESSION_PAUSE_FAILED", "message": error_msg}},
        ) from e

    return QuizSessionPauseResponse(
        session_id=session.id,
        status=QuizSessionStatus(session.status),
        is_paused=session.is_paused,
        message="Session paused successfully",
    )


@router.post(
    "/session/{session_id}/resume",
    response_model=QuizSessionResumeResponse,
    summary="Resume a paused quiz session",
    description=(
        "Resumes a previously paused quiz session. "
        "Cannot resume ended or expired sessions."
    ),
    responses={
        200: {"description": "Session resumed successfully"},
        400: {"description": "Session cannot be resumed (not paused, ended, or expired)"},
        401: {"description": "Authentication required"},
        403: {"description": "User does not own this session"},
        404: {"description": "Session not found"},
    },
)
async def resume_quiz_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    session_service: QuizSessionService = Depends(get_quiz_session_service),
    db: AsyncSession = Depends(get_db),
) -> QuizSessionResumeResponse:
    """
    Resume a paused quiz session.

    The session continues from where it was paused. Progress and configuration
    are preserved.
    """
    try:
        session = await session_service.resume_session(session_id, current_user.id)
        await db.commit()
    except ValueError as e:
        await db.rollback()
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "code": "SESSION_NOT_FOUND",
                        "message": "Quiz session not found",
                    }
                },
            ) from e
        if "unauthorized" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "code": "SESSION_ACCESS_DENIED",
                        "message": "You do not have access to this session",
                    }
                },
            ) from e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "SESSION_RESUME_FAILED", "message": error_msg}},
        ) from e

    return QuizSessionResumeResponse(
        session_id=session.id,
        status=QuizSessionStatus(session.status),
        is_paused=session.is_paused,
        total_questions=session.total_questions,
        correct_count=session.correct_count,
        message="Session resumed successfully",
    )


@router.post(
    "/session/{session_id}/end",
    response_model=QuizSessionEndResponse,
    summary="End a quiz session",
    description=(
        "Ends a quiz session. Requires the expected version for optimistic "
        "locking to prevent concurrent modifications."
    ),
    responses={
        200: {"description": "Session ended successfully"},
        400: {"description": "Session cannot be ended (already ended)"},
        401: {"description": "Authentication required"},
        403: {"description": "User does not own this session"},
        404: {"description": "Session not found"},
        409: {"description": "Version conflict - session was modified concurrently"},
    },
)
async def end_quiz_session(
    session_id: UUID,
    request: QuizSessionEndRequest,
    current_user: User = Depends(get_current_user),
    session_service: QuizSessionService = Depends(get_quiz_session_service),
    db: AsyncSession = Depends(get_db),
) -> QuizSessionEndResponse:
    """
    End a quiz session.

    Finalizes the quiz session and calculates final statistics.
    Uses optimistic locking to prevent concurrent modification conflicts.

    If the expected_version doesn't match the current version, a 409 Conflict
    error is returned. The client should refetch the session and retry.
    """
    try:
        session = await session_service.end_session(
            session_id, current_user.id, request.expected_version
        )
        await db.commit()
    except ValueError as e:
        await db.rollback()
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "code": "SESSION_NOT_FOUND",
                        "message": "Quiz session not found",
                    }
                },
            ) from e
        if "unauthorized" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "code": "SESSION_ACCESS_DENIED",
                        "message": "You do not have access to this session",
                    }
                },
            ) from e
        if "version conflict" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": {
                        "code": "VERSION_CONFLICT",
                        "message": error_msg,
                    }
                },
            ) from e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "SESSION_END_FAILED", "message": error_msg}},
        ) from e

    return QuizSessionEndResponse(
        session_id=session.id,
        ended_at=session.ended_at,
        total_questions=session.total_questions,
        correct_count=session.correct_count,
        accuracy=session.accuracy,
    )


@router.post(
    "/next-question",
    response_model=QuestionSelectionResponse,
    summary="Get next question for quiz session",
    description=(
        "Selects the next question that maximizes expected information gain "
        "for the adaptive quiz session. Uses Bayesian question selection to "
        "efficiently reduce uncertainty about user knowledge."
    ),
    responses={
        200: {"description": "Question selected successfully"},
        400: {"description": "Invalid session or no questions available"},
        401: {"description": "Authentication required"},
        403: {"description": "User does not own this session"},
        404: {"description": "Session not found"},
    },
)
async def get_next_question(
    request: QuestionSelectionRequest,
    current_user: User = Depends(get_current_user),
    enrollment: Enrollment = Depends(get_active_enrollment),
    session_service: QuizSessionService = Depends(get_quiz_session_service),
    question_selector: QuestionSelector = Depends(get_question_selector),
    question_repo: QuestionRepository = Depends(get_question_repository),
    belief_repo: BeliefRepository = Depends(get_belief_repository),
) -> QuestionSelectionResponse:
    """
    Get the next question for an active quiz session.

    Uses Bayesian question selection to pick the question that will
    provide the maximum expected information gain about user knowledge.

    The response does NOT include correct_answer or explanation.
    Those are revealed only after the user submits their answer.

    Selection strategies:
    - max_info_gain: Select question maximizing expected entropy reduction (default)
    - max_uncertainty: Select question testing most uncertain concepts
    - prerequisite_first: Prioritize foundational concepts
    - balanced: Balance across all knowledge areas
    """
    # Validate session exists and belongs to user
    try:
        session = await session_service.get_session(request.session_id, current_user.id)
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "code": "SESSION_NOT_FOUND",
                        "message": "Quiz session not found",
                    }
                },
            ) from e
        if "unauthorized" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "code": "SESSION_ACCESS_DENIED",
                        "message": "You do not have access to this session",
                    }
                },
            ) from e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "SESSION_ERROR", "message": error_msg}},
        ) from e

    # Check session is active
    if session.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "SESSION_NOT_ACTIVE",
                    "message": f"Session is {session.status}, not active",
                }
            },
        )

    # Load user beliefs
    beliefs = await belief_repo.get_beliefs_as_dict(current_user.id)

    # Load available questions with concepts eager-loaded
    # Get course_id from enrollment
    available_questions = await question_repo.get_questions_with_concepts(
        enrollment.course_id
    )

    if not available_questions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "NO_QUESTIONS_AVAILABLE",
                    "message": "No questions available for this course",
                }
            },
        )

    # Use session's strategy unless override provided
    strategy = request.strategy or session.question_strategy

    # Get knowledge area filter from session
    knowledge_area_filter = session.knowledge_area_filter

    # Select next question
    try:
        question, info_gain = await question_selector.select_next_question(
            user_id=current_user.id,
            session_id=session.id,
            beliefs=beliefs,
            available_questions=available_questions,
            strategy=strategy,
            knowledge_area_filter=knowledge_area_filter,
        )
    except ValueError as e:
        error_msg = str(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "NO_QUESTIONS_AVAILABLE",
                    "message": error_msg,
                }
            },
        ) from e

    # Get concept names for the response
    concept_names = []
    for qc in question.question_concepts:
        if qc.concept:
            concept_names.append(qc.concept.name)

    # Calculate questions remaining (estimate)
    # Filter out already-answered questions from total
    questions_remaining = len(available_questions) - session.total_questions

    # Build response (without correct_answer or explanation)
    selected_question = SelectedQuestion(
        question_id=question.id,
        question_text=question.question_text,
        options=question.options,
        knowledge_area_id=question.knowledge_area_id,
        knowledge_area_name=None,  # Could lookup from course.knowledge_areas if needed
        difficulty=question.difficulty,
        estimated_info_gain=round(info_gain, 4),
        concepts_tested=concept_names,
    )

    logger.info(
        "next_question_served",
        session_id=str(session.id),
        question_id=str(question.id),
        info_gain=round(info_gain, 4),
        strategy=strategy,
    )

    return QuestionSelectionResponse(
        session_id=session.id,
        question=selected_question,
        questions_remaining=max(0, questions_remaining),
    )


@router.post(
    "/answer",
    response_model=AnswerResponse,
    summary="Submit answer and get feedback",
    description=(
        "Submit an answer to a quiz question and receive immediate feedback. "
        "Includes correctness, explanation, concept updates, and session statistics. "
        "Uses X-Request-ID header for idempotency."
    ),
    responses={
        200: {"description": "Answer processed successfully"},
        400: {"description": "Invalid answer format"},
        401: {"description": "Authentication required"},
        404: {"description": "Session or question not found"},
        409: {"description": "Question already answered in this session"},
    },
)
async def submit_answer(
    answer_data: AnswerSubmission,
    x_request_id: UUID | None = Header(None, alias="X-Request-ID"),
    current_user: User = Depends(get_current_user),
    answer_service: QuizAnswerService = Depends(get_quiz_answer_service),
    db: AsyncSession = Depends(get_db),
) -> AnswerResponse:
    """
    Submit an answer to a quiz question.

    Processes the answer submission, determines correctness, updates beliefs
    (Story 4.4), and returns immediate feedback including:
    - Whether the answer was correct
    - The correct answer
    - An explanation
    - Updated concept mastery levels
    - Session statistics

    **Idempotency:** If X-Request-ID header is provided and a response with
    that ID already exists, returns the cached response. This prevents
    duplicate answer processing on network retries.

    **Error Handling:**
    - 404: Session not found or expired, question not found or inactive
    - 409: Question already answered in this session
    - 400: Invalid answer format (not A, B, C, or D)
    """
    try:
        response, was_cached = await answer_service.submit_answer(
            user_id=current_user.id,
            session_id=answer_data.session_id,
            question_id=answer_data.question_id,
            selected_answer=answer_data.selected_answer,
            request_id=x_request_id,
        )

        if not was_cached:
            # Commit the transaction for new responses
            await db.commit()

        if was_cached:
            logger.debug(
                "answer_returned_from_cache",
                request_id=str(x_request_id),
                session_id=str(answer_data.session_id),
            )

        return response

    except InvalidSessionError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "INVALID_SESSION",
                    "message": e.message,
                    "details": e.details,
                }
            },
        ) from e

    except InvalidQuestionError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "INVALID_QUESTION",
                    "message": e.message,
                    "details": e.details,
                }
            },
        ) from e

    except AlreadyAnsweredError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": {
                    "code": "ALREADY_ANSWERED",
                    "message": e.message,
                    "details": e.details,
                }
            },
        ) from e

    except Exception as e:
        await db.rollback()
        logger.error(
            "answer_submission_failed",
            error=str(e),
            session_id=str(answer_data.session_id),
            question_id=str(answer_data.question_id),
            user_id=str(current_user.id),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "ANSWER_SUBMISSION_FAILED",
                    "message": "Failed to process answer submission",
                }
            },
        ) from e
