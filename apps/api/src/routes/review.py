"""
Review API endpoints.
Provides endpoints for post-quiz review sessions.

Story 4.9: Post-Session Review Mode
"""
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.dependencies import get_current_user
from src.models.user import User
from src.repositories.belief_repository import BeliefRepository
from src.repositories.concept_repository import ConceptRepository
from src.repositories.review_session_repository import ReviewSessionRepository
from src.schemas.review import (
    ReviewAnswerResponse,
    ReviewAnswerSubmission,
    ReviewAvailableResponse,
    ReviewQuestionResponse,
    ReviewSessionResponse,
    ReviewSkipResponse,
    ReviewSummaryResponse,
)
from src.services.belief_updater import BeliefUpdater
from src.services.review_session_service import ReviewSessionService

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/quiz", tags=["Review"])


def get_review_session_service(
    db: AsyncSession = Depends(get_db),
) -> ReviewSessionService:
    """Dependency injection for ReviewSessionService."""
    review_repo = ReviewSessionRepository(db)
    belief_repo = BeliefRepository(db)
    concept_repo = ConceptRepository(db)
    belief_updater = BeliefUpdater(
        belief_repository=belief_repo,
        concept_repository=concept_repo,
    )
    return ReviewSessionService(
        review_repo=review_repo,
        belief_repo=belief_repo,
        concept_repo=concept_repo,
        belief_updater=belief_updater,
    )


@router.get(
    "/session/{session_id}/review-available",
    response_model=ReviewAvailableResponse,
    summary="Check if review is available for a session",
    description=(
        "Checks if a completed quiz session has incorrect answers that can be reviewed. "
        "Returns the count of incorrect questions and their IDs."
    ),
    responses={
        200: {"description": "Review availability checked"},
        401: {"description": "Authentication required"},
        404: {"description": "Session not found"},
    },
)
async def check_review_available(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    review_service: ReviewSessionService = Depends(get_review_session_service),
) -> ReviewAvailableResponse:
    """
    Check if review is available for a completed quiz session.

    Returns whether review is available, the count of incorrect answers,
    and the list of question IDs that can be reviewed.
    """
    try:
        return await review_service.check_review_available(session_id)
    except Exception as e:
        logger.error(
            "review_availability_check_failed",
            session_id=str(session_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "REVIEW_CHECK_FAILED",
                    "message": "Failed to check review availability",
                }
            },
        ) from e


@router.post(
    "/session/{session_id}/review/start",
    response_model=ReviewSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a review session",
    description=(
        "Starts a new review session for incorrect answers from a completed quiz session. "
        "If a review session already exists, it will be resumed."
    ),
    responses={
        201: {"description": "Review session created"},
        200: {"description": "Existing review session resumed"},
        400: {"description": "No incorrect answers to review"},
        401: {"description": "Authentication required"},
        404: {"description": "Session not found"},
    },
)
async def start_review(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    review_service: ReviewSessionService = Depends(get_review_session_service),
    db: AsyncSession = Depends(get_db),
) -> ReviewSessionResponse:
    """
    Start a review session for incorrect answers from a quiz session.

    Creates a new review session or resumes an existing one.
    The review session contains all incorrectly answered questions.
    """
    try:
        response = await review_service.start_review(
            user_id=current_user.id,
            original_session_id=session_id,
        )
        await db.commit()
        return response
    except ValueError as e:
        await db.rollback()
        error_msg = str(e)
        if "no incorrect" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "code": "NO_INCORRECT_ANSWERS",
                        "message": "No incorrect answers to review",
                    }
                },
            ) from e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "REVIEW_START_FAILED",
                    "message": error_msg,
                }
            },
        ) from e
    except Exception as e:
        await db.rollback()
        logger.error(
            "review_start_failed",
            session_id=str(session_id),
            user_id=str(current_user.id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "REVIEW_START_FAILED",
                    "message": "Failed to start review session",
                }
            },
        ) from e


@router.get(
    "/review/{review_session_id}/next-question",
    response_model=ReviewQuestionResponse | None,
    summary="Get next review question",
    description=(
        "Returns the next question to review. Does not include the correct answer. "
        "Returns null if all questions have been reviewed."
    ),
    responses={
        200: {"description": "Next question returned or null if complete"},
        401: {"description": "Authentication required"},
        404: {"description": "Review session not found"},
    },
)
async def get_next_review_question(
    review_session_id: UUID,
    current_user: User = Depends(get_current_user),
    review_service: ReviewSessionService = Depends(get_review_session_service),
) -> ReviewQuestionResponse | None:
    """
    Get the next question to review.

    Returns the question text and options without the correct answer.
    Returns null if all questions have been reviewed.
    """
    try:
        return await review_service.get_next_review_question(
            review_session_id=review_session_id,
            user_id=current_user.id,
        )
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "code": "REVIEW_SESSION_NOT_FOUND",
                        "message": "Review session not found",
                    }
                },
            ) from e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "NEXT_QUESTION_FAILED",
                    "message": error_msg,
                }
            },
        ) from e
    except Exception as e:
        logger.error(
            "next_review_question_failed",
            review_session_id=str(review_session_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "NEXT_QUESTION_FAILED",
                    "message": "Failed to get next question",
                }
            },
        ) from e


@router.post(
    "/review/{review_session_id}/answer",
    response_model=ReviewAnswerResponse,
    summary="Submit review answer",
    description=(
        "Submit an answer to a review question. Returns feedback including "
        "whether the answer was reinforced (incorrect→correct)."
    ),
    responses={
        200: {"description": "Answer processed successfully"},
        400: {"description": "Invalid answer or question already reviewed"},
        401: {"description": "Authentication required"},
        404: {"description": "Review session or question not found"},
        409: {"description": "Answer already submitted for this question"},
    },
)
async def submit_review_answer(
    review_session_id: UUID,
    answer_data: ReviewAnswerSubmission,
    current_user: User = Depends(get_current_user),
    review_service: ReviewSessionService = Depends(get_review_session_service),
    db: AsyncSession = Depends(get_db),
) -> ReviewAnswerResponse:
    """
    Submit an answer for a review question.

    Processes the answer, determines if it was reinforced (incorrect→correct),
    updates beliefs with reinforcement modifiers, and returns feedback.
    """
    try:
        response = await review_service.submit_review_answer(
            review_session_id=review_session_id,
            user_id=current_user.id,
            question_id=UUID(answer_data.question_id),
            selected_answer=answer_data.selected_answer,
        )
        await db.commit()
        return response
    except ValueError as e:
        await db.rollback()
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "code": "NOT_FOUND",
                        "message": error_msg,
                    }
                },
            ) from e
        if "already reviewed" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": {
                        "code": "ALREADY_REVIEWED",
                        "message": error_msg,
                    }
                },
            ) from e
        if "invalid answer" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "code": "INVALID_ANSWER",
                        "message": error_msg,
                    }
                },
            ) from e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "ANSWER_SUBMISSION_FAILED",
                    "message": error_msg,
                }
            },
        ) from e
    except Exception as e:
        await db.rollback()
        logger.error(
            "review_answer_submission_failed",
            review_session_id=str(review_session_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "ANSWER_SUBMISSION_FAILED",
                    "message": "Failed to process review answer",
                }
            },
        ) from e


@router.post(
    "/review/{review_session_id}/skip",
    response_model=ReviewSkipResponse,
    summary="Skip review session",
    description=(
        "Skip the review session. Marks the session as skipped and logs the event for analytics."
    ),
    responses={
        200: {"description": "Review session skipped"},
        401: {"description": "Authentication required"},
        404: {"description": "Review session not found"},
    },
)
async def skip_review(
    review_session_id: UUID,
    current_user: User = Depends(get_current_user),
    review_service: ReviewSessionService = Depends(get_review_session_service),
    db: AsyncSession = Depends(get_db),
) -> ReviewSkipResponse:
    """
    Skip the review session.

    Marks the review session as skipped and logs analytics event.
    The skipped questions remain available for future review.
    """
    try:
        response = await review_service.skip_review(
            review_session_id=review_session_id,
            user_id=current_user.id,
        )
        await db.commit()
        return response
    except ValueError as e:
        await db.rollback()
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "code": "REVIEW_SESSION_NOT_FOUND",
                        "message": "Review session not found",
                    }
                },
            ) from e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "SKIP_FAILED",
                    "message": error_msg,
                }
            },
        ) from e
    except Exception as e:
        await db.rollback()
        logger.error(
            "review_skip_failed",
            review_session_id=str(review_session_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "SKIP_FAILED",
                    "message": "Failed to skip review session",
                }
            },
        ) from e


@router.get(
    "/review/{review_session_id}/summary",
    response_model=ReviewSummaryResponse,
    summary="Get review session summary",
    description=(
        "Returns the summary of a completed review session including "
        "reinforcement rate and study links for still-incorrect concepts."
    ),
    responses={
        200: {"description": "Review summary returned"},
        401: {"description": "Authentication required"},
        404: {"description": "Review session not found"},
    },
)
async def get_review_summary(
    review_session_id: UUID,
    current_user: User = Depends(get_current_user),
    review_service: ReviewSessionService = Depends(get_review_session_service),
) -> ReviewSummaryResponse:
    """
    Get the summary of a completed review session.

    Returns review statistics including:
    - Total questions reviewed
    - Reinforcement count and rate
    - List of still-incorrect concepts with study links
    """
    try:
        return await review_service.get_review_summary(
            review_session_id=review_session_id,
            user_id=current_user.id,
        )
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "code": "REVIEW_SESSION_NOT_FOUND",
                        "message": "Review session not found",
                    }
                },
            ) from e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "SUMMARY_FAILED",
                    "message": error_msg,
                }
            },
        ) from e
    except Exception as e:
        logger.error(
            "review_summary_failed",
            review_session_id=str(review_session_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "SUMMARY_FAILED",
                    "message": "Failed to get review summary",
                }
            },
        ) from e
