"""
Sync belief states for all users enrolled in a course.

Story 2.14: Belief State Sync for New Concepts

This script ensures all enrolled users have belief states for all concepts
in a course. When new concepts are added (e.g., via import_vendor_questions.py
with --create-missing-concepts), existing users need belief states created
for those new concepts.

USAGE:
------
# Standard sync for a course:
python scripts/sync_belief_states.py --course-slug cbap

# Dry run (no database changes):
python scripts/sync_belief_states.py --course-slug cbap --dry-run

# Verbose logging:
python scripts/sync_belief_states.py --course-slug cbap --verbose

PERFORMANCE:
------------
Target: Sync 1000 users × 50 concepts in <30 seconds
Uses batch inserts with ON CONFLICT DO NOTHING for idempotency.
"""
import argparse
import asyncio
import logging
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "apps" / "api"))

from sqlalchemy import select

from src.db.session import AsyncSessionLocal
from src.models.concept import Concept
from src.models.course import Course
from src.models.enrollment import Enrollment
from src.repositories.belief_repository import BeliefRepository


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class SyncResult:
    """Result of belief state sync operation."""
    users_synced: int = 0
    beliefs_created: int = 0
    duration_ms: float = 0.0
    errors: int = 0


async def get_course_by_slug(slug: str) -> Course | None:
    """Look up course by slug."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Course).where(Course.slug == slug)
        )
        return result.scalar_one_or_none()


async def get_all_concept_ids_for_course(course_id: UUID) -> list[UUID]:
    """Get all concept IDs for a course."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Concept.id).where(Concept.course_id == course_id)
        )
        return [row[0] for row in result.all()]


async def get_enrolled_user_ids(course_id: UUID) -> list[UUID]:
    """Get all user IDs enrolled in a course with active status."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Enrollment.user_id)
            .where(Enrollment.course_id == course_id)
            .where(Enrollment.status == 'active')
        )
        return [row[0] for row in result.all()]


async def sync_beliefs_for_user(
    db_session,
    belief_repo: BeliefRepository,
    user_id: UUID,
    all_concept_ids: list[UUID],
    dry_run: bool = False,
) -> int:
    """
    Sync beliefs for a single user, creating any missing belief states.

    Uses bulk_create_from_concepts which has ON CONFLICT DO NOTHING
    for idempotency - existing beliefs are not modified.

    Args:
        db_session: Database session
        belief_repo: BeliefRepository instance
        user_id: User UUID
        all_concept_ids: All concept IDs in the course
        dry_run: If True, don't actually create beliefs

    Returns:
        Number of beliefs created
    """
    if dry_run:
        # In dry run, we just count what would be created
        existing_beliefs = await belief_repo.get_beliefs_as_dict(user_id)
        existing_concept_ids = set(existing_beliefs.keys())
        missing_count = len(set(all_concept_ids) - existing_concept_ids)
        return missing_count

    # Use bulk_create_from_concepts - it handles ON CONFLICT DO NOTHING
    # so we can safely pass all concepts and only missing ones are created
    created_count = await belief_repo.bulk_create_from_concepts(
        user_id=user_id,
        concept_ids=all_concept_ids,
        alpha=1.0,  # Uninformative prior Beta(1,1)
        beta=1.0,
    )
    return created_count


async def sync_beliefs_for_course(
    course_id: UUID,
    dry_run: bool = False,
    verbose: bool = False,
) -> SyncResult:
    """
    Sync belief states for all users enrolled in a course.

    Ensures every user has a belief state for every concept in the course.
    Uses uninformative prior Beta(1,1) for new beliefs.

    Args:
        course_id: Course UUID
        dry_run: If True, log what would happen without making changes
        verbose: Enable verbose logging

    Returns:
        SyncResult with statistics
    """
    start_time = time.perf_counter()
    result = SyncResult()

    # Get all concepts for the course
    all_concept_ids = await get_all_concept_ids_for_course(course_id)
    if not all_concept_ids:
        logger.warning(f"No concepts found for course {course_id}")
        return result

    logger.info(f"Found {len(all_concept_ids)} concepts for course")

    # Get all enrolled users
    user_ids = await get_enrolled_user_ids(course_id)
    if not user_ids:
        logger.warning(f"No enrolled users found for course {course_id}")
        return result

    logger.info(f"Found {len(user_ids)} enrolled users to sync")

    if dry_run:
        logger.info("DRY RUN - No database changes will be made")

    # Process users in batches with progress logging
    async with AsyncSessionLocal() as db:
        belief_repo = BeliefRepository(db)

        for idx, user_id in enumerate(user_ids, start=1):
            try:
                created = await sync_beliefs_for_user(
                    db_session=db,
                    belief_repo=belief_repo,
                    user_id=user_id,
                    all_concept_ids=all_concept_ids,
                    dry_run=dry_run,
                )
                result.beliefs_created += created
                result.users_synced += 1

                if verbose and created > 0:
                    logger.debug(
                        f"User {user_id}: created {created} beliefs"
                    )

            except Exception as e:
                logger.error(f"Failed to sync user {user_id}: {e}")
                result.errors += 1

            # Progress logging every 100 users
            if idx % 100 == 0:
                elapsed = (time.perf_counter() - start_time) * 1000
                logger.info(
                    f"Progress: {idx}/{len(user_ids)} users processed, "
                    f"{result.beliefs_created} beliefs created, "
                    f"{elapsed:.0f}ms elapsed"
                )

        # Commit all changes (only if not dry run)
        if not dry_run:
            await db.commit()

    result.duration_ms = (time.perf_counter() - start_time) * 1000

    # Summary logging
    logger.info("=" * 60)
    logger.info("BELIEF STATE SYNC SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    logger.info(f"Course ID: {course_id}")
    logger.info(f"Total concepts: {len(all_concept_ids)}")
    logger.info(f"Total enrolled users: {len(user_ids)}")
    logger.info(f"Users synced: {result.users_synced}")
    logger.info(f"Beliefs created: {result.beliefs_created}")
    logger.info(f"Errors: {result.errors}")
    logger.info(f"Duration: {result.duration_ms:.0f}ms ({result.duration_ms/1000:.2f}s)")
    logger.info("=" * 60)

    return result


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Sync belief states for all users in a course"
    )
    parser.add_argument(
        "--course-slug",
        required=True,
        help="Course slug (e.g., 'cbap')"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without making changes"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Look up course
    logger.info(f"Looking up course: {args.course_slug}")
    course = await get_course_by_slug(args.course_slug)

    if not course:
        logger.error(f"Course not found: {args.course_slug}")
        sys.exit(1)

    logger.info(f"Found course: {course.name} (ID: {course.id})")

    # Run sync
    result = await sync_beliefs_for_course(
        course_id=course.id,
        dry_run=args.dry_run,
        verbose=args.verbose,
    )

    # Exit with error code if there were errors
    if result.errors > 0:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
