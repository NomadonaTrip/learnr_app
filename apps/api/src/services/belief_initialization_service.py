"""
Belief initialization service for setting up user belief states.
Handles the initialization of BKT belief states for new users.
"""
import logging
import time
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from src.exceptions import BeliefInitializationError
from src.models.belief_state import BeliefState
from src.models.enrollment import Enrollment
from src.repositories.belief_repository import BeliefRepository
from src.repositories.concept_repository import ConceptRepository
from src.schemas.belief_state import BeliefInitializationStatus, InitializationResult
from src.utils.bkt_math import calculate_alpha_beta

# Performance threshold in milliseconds
PERFORMANCE_THRESHOLD_MS = 2000

# Use structlog for structured logging
logger = structlog.get_logger(__name__)
fallback_logger = logging.getLogger(__name__)


class BeliefInitializationService:
    """
    Service for initializing belief states for new users.

    Initializes belief states with uninformative prior Beta(1, 1)
    for all concepts when a new user registers.
    """

    def __init__(
        self,
        belief_repository: BeliefRepository,
        concept_repository: ConceptRepository
    ):
        self.belief_repo = belief_repository
        self.concept_repo = concept_repository

    async def initialize_beliefs_for_user(
        self,
        user_id: UUID,
        course_id: UUID,
        initial_belief_prior: float | None = None
    ) -> InitializationResult:
        """
        Initialize belief states for a user across all concepts in a course.

        When initial_belief_prior is provided (from onboarding):
            - Converts to Beta distribution using pseudo-observations scaling
            - Prior 0.1 → alpha=1, beta=9 (new to topic)
            - Prior 0.3 → alpha=3, beta=7 (knows basics)
            - Prior 0.5 → alpha=5, beta=5 (intermediate)
            - Prior 0.7 → alpha=7, beta=3 (expert)

        When initial_belief_prior is None (legacy/API-only registration):
            - Uses uninformative prior: Beta(1, 1) = Uniform[0, 1]
            - This represents "we have no information about this user's knowledge."

        Args:
            user_id: UUID of the user
            course_id: UUID of the course to initialize beliefs for
            initial_belief_prior: Initial belief probability [0.0, 1.0] from onboarding,
                                  or None for default Beta(1,1) fallback

        Returns:
            InitializationResult with success status, counts, and timing

        Raises:
            BeliefInitializationError: If initialization fails
        """
        start_time = time.perf_counter()

        try:
            # Check if already initialized (idempotency)
            existing_count = await self.belief_repo.get_belief_count(user_id)
            if existing_count > 0:
                # Ensure enrollment exists even if beliefs were already initialized
                # This handles cases where enrollment was deleted but beliefs remain
                enrollment_stmt = pg_insert(Enrollment).values(
                    user_id=user_id,
                    course_id=course_id,
                    status="active",
                ).on_conflict_do_nothing(
                    index_elements=["user_id", "course_id"]
                )
                await self.belief_repo.session.execute(enrollment_stmt)

                # Get the enrollment_id
                enrollment_result = await self.belief_repo.session.execute(
                    select(Enrollment.id).where(
                        Enrollment.user_id == user_id,
                        Enrollment.course_id == course_id
                    )
                )
                enrollment_id = enrollment_result.scalar_one_or_none()

                duration_ms = (time.perf_counter() - start_time) * 1000

                self._log_info(
                    "Beliefs already initialized, skipping",
                    user_id=user_id,
                    course_id=course_id,
                    existing_count=existing_count,
                    duration_ms=duration_ms
                )

                return InitializationResult(
                    success=True,
                    already_initialized=True,
                    belief_count=existing_count,
                    duration_ms=duration_ms,
                    message=f"Beliefs already initialized ({existing_count} existing)",
                    enrollment_id=enrollment_id
                )

            # Create enrollment if it doesn't exist (idempotent)
            # This ensures the user is enrolled in the course when beliefs are initialized
            enrollment_stmt = pg_insert(Enrollment).values(
                user_id=user_id,
                course_id=course_id,
                status="active",
            ).on_conflict_do_nothing(
                index_elements=["user_id", "course_id"]
            )
            await self.belief_repo.session.execute(enrollment_stmt)

            # Get the enrollment_id
            enrollment_result = await self.belief_repo.session.execute(
                select(Enrollment.id).where(
                    Enrollment.user_id == user_id,
                    Enrollment.course_id == course_id
                )
            )
            enrollment_id = enrollment_result.scalar_one_or_none()

            self._log_info(
                "Ensured enrollment exists for user/course",
                user_id=user_id,
                course_id=course_id,
            )

            # Fetch all concepts for the course
            concepts = await self.concept_repo.get_all_concepts(course_id)

            if not concepts:
                duration_ms = (time.perf_counter() - start_time) * 1000

                self._log_warning(
                    "No concepts found for course",
                    user_id=user_id,
                    course_id=course_id,
                    duration_ms=duration_ms
                )

                return InitializationResult(
                    success=True,
                    already_initialized=False,
                    belief_count=0,
                    duration_ms=duration_ms,
                    message="No concepts found for course",
                    enrollment_id=enrollment_id
                )

            # Calculate alpha/beta from prior or use default Beta(1,1)
            if initial_belief_prior is not None:
                alpha, beta = calculate_alpha_beta(initial_belief_prior)
                self._log_info(
                    "Using familiarity-based prior",
                    user_id=user_id,
                    course_id=course_id,
                    prior=initial_belief_prior,
                    alpha=alpha,
                    beta=beta
                )
            else:
                # Fallback: Uninformative prior Beta(1,1) = Uniform[0,1]
                alpha, beta = 1.0, 1.0

            # Create belief states with calculated alpha/beta
            beliefs = [
                BeliefState(
                    user_id=user_id,
                    concept_id=concept.id,
                    alpha=alpha,
                    beta=beta,
                    response_count=0
                )
                for concept in concepts
            ]

            # Bulk insert for performance
            created_count = await self.belief_repo.bulk_create(beliefs)

            duration_ms = (time.perf_counter() - start_time) * 1000

            # Log success with timing
            self._log_info(
                f"Initialized {created_count} belief states for user",
                user_id=user_id,
                course_id=course_id,
                concept_count=len(concepts),
                created_count=created_count,
                duration_ms=duration_ms
            )

            # Warn if performance threshold exceeded
            if duration_ms > PERFORMANCE_THRESHOLD_MS:
                self._log_warning(
                    f"Belief initialization exceeded threshold ({PERFORMANCE_THRESHOLD_MS}ms)",
                    user_id=user_id,
                    course_id=course_id,
                    duration_ms=duration_ms,
                    threshold_ms=PERFORMANCE_THRESHOLD_MS
                )

            return InitializationResult(
                success=True,
                already_initialized=False,
                belief_count=created_count,
                duration_ms=duration_ms,
                message=f"Initialized {created_count} belief states",
                enrollment_id=enrollment_id
            )

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000

            self._log_error(
                f"Belief initialization failed: {str(e)}",
                user_id=user_id,
                course_id=course_id,
                duration_ms=duration_ms,
                error=str(e)
            )

            raise BeliefInitializationError(
                f"Failed to initialize beliefs for user {user_id}: {str(e)}"
            ) from e

    async def initialize_beliefs_via_db_function(
        self,
        user_id: UUID
    ) -> InitializationResult:
        """
        Initialize beliefs using the database function for maximum performance.

        This uses the PostgreSQL function `initialize_beliefs(p_user_id UUID)`
        which inserts all concepts in a single query.

        Args:
            user_id: UUID of the user

        Returns:
            InitializationResult with success status and counts

        Raises:
            BeliefInitializationError: If initialization fails
        """
        start_time = time.perf_counter()

        try:
            # Check if already initialized
            existing_count = await self.belief_repo.get_belief_count(user_id)
            if existing_count > 0:
                duration_ms = (time.perf_counter() - start_time) * 1000

                return InitializationResult(
                    success=True,
                    already_initialized=True,
                    belief_count=existing_count,
                    duration_ms=duration_ms,
                    message=f"Beliefs already initialized ({existing_count} existing)"
                )

            # Use database function for bulk insert
            created_count = await self.belief_repo.initialize_via_db_function(user_id)

            duration_ms = (time.perf_counter() - start_time) * 1000

            self._log_info(
                f"Initialized {created_count} belief states via DB function",
                user_id=user_id,
                created_count=created_count,
                duration_ms=duration_ms
            )

            if duration_ms > PERFORMANCE_THRESHOLD_MS:
                self._log_warning(
                    f"Belief initialization exceeded threshold ({PERFORMANCE_THRESHOLD_MS}ms)",
                    user_id=user_id,
                    duration_ms=duration_ms,
                    threshold_ms=PERFORMANCE_THRESHOLD_MS
                )

            return InitializationResult(
                success=True,
                already_initialized=False,
                belief_count=created_count,
                duration_ms=duration_ms,
                message=f"Initialized {created_count} belief states"
            )

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000

            self._log_error(
                f"Belief initialization via DB function failed: {str(e)}",
                user_id=user_id,
                duration_ms=duration_ms,
                error=str(e)
            )

            raise BeliefInitializationError(
                f"Failed to initialize beliefs for user {user_id}: {str(e)}"
            ) from e

    async def get_initialization_status(
        self,
        user_id: UUID,
        course_id: UUID
    ) -> BeliefInitializationStatus:
        """
        Get the initialization status for a user's beliefs.

        Args:
            user_id: UUID of the user
            course_id: UUID of the course

        Returns:
            BeliefInitializationStatus with coverage information
        """
        # Get belief count for user
        belief_count = await self.belief_repo.get_belief_count(user_id)

        # Get total concepts for course
        total_concepts = await self.concept_repo.get_concept_count(course_id)

        # Get earliest created_at if beliefs exist
        created_at = None
        if belief_count > 0:
            created_at = await self.belief_repo.get_earliest_created_at(user_id)

        # Calculate coverage
        coverage = (belief_count / total_concepts * 100) if total_concepts > 0 else 0.0

        return BeliefInitializationStatus(
            initialized=belief_count > 0,
            total_concepts=total_concepts,
            belief_count=belief_count,
            coverage_percentage=round(coverage, 2),
            created_at=created_at
        )

    def _log_info(self, message: str, **kwargs) -> None:
        """Log info message with structured data."""
        try:
            # Convert UUIDs to strings for JSON serialization
            log_data = {k: str(v) if isinstance(v, UUID) else v for k, v in kwargs.items()}
            logger.info(message, **log_data)
        except Exception:
            # Fallback to standard logging
            fallback_logger.info(f"{message} - {kwargs}")

    def _log_warning(self, message: str, **kwargs) -> None:
        """Log warning message with structured data."""
        try:
            log_data = {k: str(v) if isinstance(v, UUID) else v for k, v in kwargs.items()}
            logger.warning(message, **log_data)
        except Exception:
            fallback_logger.warning(f"{message} - {kwargs}")

    def _log_error(self, message: str, **kwargs) -> None:
        """Log error message with structured data."""
        try:
            log_data = {k: str(v) if isinstance(v, UUID) else v for k, v in kwargs.items()}
            logger.error(message, **log_data)
        except Exception:
            fallback_logger.error(f"{message} - {kwargs}")
