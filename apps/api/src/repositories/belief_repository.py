"""
Belief repository for database operations on BeliefState model.
Implements repository pattern for BKT belief state data access.
"""
from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, func, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.exceptions import DatabaseError
from src.models.belief_state import BeliefState


class BeliefRepository:
    """Repository for BeliefState database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def bulk_create(self, beliefs: list[BeliefState]) -> int:
        """
        Bulk create belief states using optimized insert.

        Uses PostgreSQL's INSERT ... ON CONFLICT DO NOTHING for idempotency.

        Args:
            beliefs: List of BeliefState models to create

        Returns:
            Number of beliefs created

        Raises:
            DatabaseError: If database operation fails
        """
        if not beliefs:
            return 0

        try:
            # Use bulk insert with ON CONFLICT DO NOTHING for idempotency
            belief_dicts = [
                {
                    "user_id": b.user_id,
                    "concept_id": b.concept_id,
                    "alpha": b.alpha,
                    "beta": b.beta,
                    "response_count": b.response_count,
                }
                for b in beliefs
            ]

            stmt = insert(BeliefState).values(belief_dicts)
            stmt = stmt.on_conflict_do_nothing(
                index_elements=["user_id", "concept_id"]
            )

            result = await self.session.execute(stmt)
            await self.session.flush()

            return result.rowcount
        except Exception as e:
            raise DatabaseError(f"Failed to bulk create beliefs: {str(e)}") from e

    async def bulk_create_from_concepts(
        self,
        user_id: UUID,
        concept_ids: list[UUID],
        alpha: float = 1.0,
        beta: float = 1.0
    ) -> int:
        """
        Bulk create belief states for a user from a list of concept IDs.

        Uses PostgreSQL's INSERT ... ON CONFLICT DO NOTHING for idempotency.

        Args:
            user_id: User UUID
            concept_ids: List of concept UUIDs
            alpha: Initial alpha value (default 1.0)
            beta: Initial beta value (default 1.0)

        Returns:
            Number of beliefs created

        Raises:
            DatabaseError: If database operation fails
        """
        if not concept_ids:
            return 0

        try:
            belief_dicts = [
                {
                    "user_id": user_id,
                    "concept_id": cid,
                    "alpha": alpha,
                    "beta": beta,
                    "response_count": 0,
                }
                for cid in concept_ids
            ]

            stmt = insert(BeliefState).values(belief_dicts)
            stmt = stmt.on_conflict_do_nothing(
                index_elements=["user_id", "concept_id"]
            )

            result = await self.session.execute(stmt)
            await self.session.flush()

            return result.rowcount
        except Exception as e:
            raise DatabaseError(f"Failed to bulk create beliefs: {str(e)}") from e

    async def initialize_via_db_function(self, user_id: UUID) -> int:
        """
        Initialize beliefs using the database function for maximum performance.

        Uses the PostgreSQL function `initialize_beliefs(p_user_id UUID)` which
        inserts all concepts in a single query with ON CONFLICT DO NOTHING.

        Args:
            user_id: User UUID

        Returns:
            Number of beliefs created

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            result = await self.session.execute(
                text("SELECT initialize_beliefs(:user_id)"),
                {"user_id": str(user_id)}
            )
            count = result.scalar_one()
            await self.session.flush()
            return count
        except Exception as e:
            raise DatabaseError(f"Failed to initialize beliefs: {str(e)}") from e

    async def get_all_beliefs(self, user_id: UUID) -> list[BeliefState]:
        """
        Get all belief states for a user.

        Args:
            user_id: User UUID

        Returns:
            List of BeliefState models
        """
        result = await self.session.execute(
            select(BeliefState)
            .where(BeliefState.user_id == user_id)
            .order_by(BeliefState.created_at)
        )
        return list(result.scalars().all())

    async def get_beliefs_as_dict(self, user_id: UUID) -> dict[UUID, BeliefState]:
        """
        Get all belief states for a user as a dictionary keyed by concept_id.

        Args:
            user_id: User UUID

        Returns:
            Dictionary mapping concept_id to BeliefState
        """
        beliefs = await self.get_all_beliefs(user_id)
        return {b.concept_id: b for b in beliefs}

    async def get_belief(self, user_id: UUID, concept_id: UUID) -> BeliefState | None:
        """
        Get a specific belief state for a user and concept.

        Args:
            user_id: User UUID
            concept_id: Concept UUID

        Returns:
            BeliefState model if found, None otherwise
        """
        result = await self.session.execute(
            select(BeliefState)
            .where(BeliefState.user_id == user_id)
            .where(BeliefState.concept_id == concept_id)
        )
        return result.scalar_one_or_none()

    async def get_belief_count(self, user_id: UUID) -> int:
        """
        Get count of belief states for a user.

        Args:
            user_id: User UUID

        Returns:
            Number of belief states
        """
        result = await self.session.execute(
            select(func.count(BeliefState.id))
            .where(BeliefState.user_id == user_id)
        )
        return result.scalar_one()

    async def check_initialization_status(self, user_id: UUID) -> bool:
        """
        Check if belief states have been initialized for a user.

        Args:
            user_id: User UUID

        Returns:
            True if at least one belief state exists
        """
        count = await self.get_belief_count(user_id)
        return count > 0

    async def get_earliest_created_at(self, user_id: UUID) -> datetime | None:
        """
        Get the earliest created_at timestamp for a user's beliefs.

        Args:
            user_id: User UUID

        Returns:
            Earliest created_at datetime, or None if no beliefs exist
        """
        result = await self.session.execute(
            select(func.min(BeliefState.created_at))
            .where(BeliefState.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def update_belief(
        self,
        user_id: UUID,
        concept_id: UUID,
        alpha: float,
        beta: float,
        increment_response: bool = True
    ) -> BeliefState | None:
        """
        Update a belief state after a response.

        Args:
            user_id: User UUID
            concept_id: Concept UUID
            alpha: New alpha value
            beta: New beta value
            increment_response: Whether to increment response_count

        Returns:
            Updated BeliefState, or None if not found
        """
        belief = await self.get_belief(user_id, concept_id)
        if not belief:
            return None

        belief.alpha = alpha
        belief.beta = beta
        belief.last_response_at = func.now()
        if increment_response:
            belief.response_count += 1

        await self.session.flush()
        return belief

    async def bulk_update(self, updates: dict[UUID, dict]) -> int:
        """
        Batch update belief states.

        Args:
            updates: Dictionary mapping belief_id to update fields
                     (alpha, beta, response_count, last_response_at)

        Returns:
            Number of beliefs updated
        """
        if not updates:
            return 0

        updated = 0
        for belief_id, fields in updates.items():
            result = await self.session.execute(
                select(BeliefState).where(BeliefState.id == belief_id)
            )
            belief = result.scalar_one_or_none()
            if belief:
                for key, value in fields.items():
                    setattr(belief, key, value)
                updated += 1

        await self.session.flush()
        return updated

    async def delete_all_for_user(self, user_id: UUID) -> int:
        """
        Delete all belief states for a user.

        Args:
            user_id: User UUID

        Returns:
            Number of beliefs deleted
        """
        result = await self.session.execute(
            delete(BeliefState).where(BeliefState.user_id == user_id)
        )
        await self.session.flush()
        return result.rowcount

    async def get_beliefs_by_status(
        self,
        user_id: UUID
    ) -> dict[str, list[BeliefState]]:
        """
        Get beliefs grouped by status (mastered, gap, borderline, uncertain).

        Args:
            user_id: User UUID

        Returns:
            Dictionary with keys: mastered, gap, borderline, uncertain
        """
        beliefs = await self.get_all_beliefs(user_id)

        grouped = {
            "mastered": [],
            "gap": [],
            "borderline": [],
            "uncertain": []
        }

        for belief in beliefs:
            grouped[belief.status].append(belief)

        return grouped

    async def get_belief_summary(self, user_id: UUID) -> dict:
        """
        Get summary statistics for a user's beliefs.

        Args:
            user_id: User UUID

        Returns:
            Dictionary with summary statistics
        """
        beliefs = await self.get_all_beliefs(user_id)

        if not beliefs:
            return {
                "total": 0,
                "mastered": 0,
                "gap": 0,
                "borderline": 0,
                "uncertain": 0,
                "average_mean": 0.0
            }

        status_counts = {"mastered": 0, "gap": 0, "borderline": 0, "uncertain": 0}
        total_mean = 0.0

        for belief in beliefs:
            status_counts[belief.status] += 1
            total_mean += belief.mean

        return {
            "total": len(beliefs),
            "mastered": status_counts["mastered"],
            "gap": status_counts["gap"],
            "borderline": status_counts["borderline"],
            "uncertain": status_counts["uncertain"],
            "average_mean": round(total_mean / len(beliefs), 4)
        }
