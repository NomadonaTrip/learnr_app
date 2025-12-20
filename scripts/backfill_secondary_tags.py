"""
Backfill secondary tags (perspectives, competencies) for existing questions.

Story 2.15: Secondary Tagging for Perspectives and Underlying Competencies

This script processes existing questions and populates their perspectives and
competencies arrays based on their linked concept names, using the course-configured
keyword matching via TagClassifier.

USAGE:
------
# Preview changes (dry run):
python scripts/backfill_secondary_tags.py --course-slug cbap --dry-run --verbose

# Apply changes:
python scripts/backfill_secondary_tags.py --course-slug cbap

# With verbose output:
python scripts/backfill_secondary_tags.py --course-slug cbap --verbose
"""
import argparse
import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set
from uuid import UUID

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "apps" / "api"))

from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from src.db.session import AsyncSessionLocal
from src.models.course import Course
from src.models.question import Question
from src.models.question_concept import QuestionConcept

# Import TagClassifier from import_vendor_questions
sys.path.insert(0, str(project_root / "scripts"))
from import_vendor_questions import TagClassifier

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SecondaryTagBackfiller:
    """
    Backfills perspectives and competencies arrays for existing questions.

    Uses linked concept names to derive secondary tags via TagClassifier.
    """

    def __init__(
        self,
        course_slug: str,
        dry_run: bool = False,
        verbose: bool = False,
    ):
        self.course_slug = course_slug
        self.dry_run = dry_run
        self.verbose = verbose

        self.course: Optional[Course] = None
        self.tag_classifier: Optional[TagClassifier] = None

        # Statistics
        self.questions_processed = 0
        self.questions_updated = 0
        self.perspectives_assigned = 0
        self.competencies_assigned = 0

    async def run(self) -> bool:
        """Run the backfill process."""
        logger.info(f"Starting secondary tag backfill for course: {self.course_slug}")
        if self.dry_run:
            logger.info("DRY RUN - No database changes will be made")

        async with AsyncSessionLocal() as db:
            # Load course
            result = await db.execute(
                select(Course).where(Course.slug == self.course_slug)
            )
            self.course = result.scalar_one_or_none()

            if not self.course:
                logger.error(f"Course not found: {self.course_slug}")
                return False

            logger.info(f"Loaded course: {self.course.name}")

            # Check if course has perspectives/competencies configured
            if not self.course.perspectives and not self.course.competencies:
                logger.warning(
                    f"Course '{self.course_slug}' has no perspectives or competencies configured. "
                    "Nothing to backfill."
                )
                return True

            # Initialize TagClassifier
            self.tag_classifier = TagClassifier(self.course)
            logger.info(
                f"TagClassifier initialized with "
                f"{len(self.tag_classifier.competency_keywords)} competency keywords, "
                f"{len(self.tag_classifier.perspective_keywords)} perspective keywords"
            )

            # Load all questions for the course with their concept relationships
            questions_result = await db.execute(
                select(Question)
                .where(Question.course_id == self.course.id)
                .options(selectinload(Question.question_concepts).selectinload(QuestionConcept.concept))
            )
            questions = list(questions_result.scalars().all())
            logger.info(f"Loaded {len(questions)} questions to process")

            if not questions:
                logger.info("No questions to process")
                return True

            # Process each question
            updates: List[Dict] = []
            for question in questions:
                self.questions_processed += 1

                # Get linked concept names
                concept_names = [qc.concept.name for qc in question.question_concepts if qc.concept]

                if not concept_names:
                    if self.verbose:
                        logger.debug(f"Question {question.id}: No linked concepts")
                    continue

                # Classify concept names through TagClassifier
                classified = self.tag_classifier.classify_tags(concept_names)
                perspectives = classified["perspectives"]
                competencies = classified["competencies"]

                # Check if there are any changes
                current_perspectives = question.perspectives or []
                current_competencies = question.competencies or []

                if set(perspectives) != set(current_perspectives) or set(competencies) != set(current_competencies):
                    updates.append({
                        "id": question.id,
                        "perspectives": perspectives,
                        "competencies": competencies,
                    })
                    self.questions_updated += 1
                    self.perspectives_assigned += len(perspectives)
                    self.competencies_assigned += len(competencies)

                    if self.verbose:
                        logger.info(
                            f"Question {question.id}: "
                            f"perspectives={perspectives}, competencies={competencies} "
                            f"(from concepts: {concept_names})"
                        )

            # Apply updates
            if updates and not self.dry_run:
                logger.info(f"Applying {len(updates)} updates...")
                for update_data in updates:
                    await db.execute(
                        update(Question)
                        .where(Question.id == update_data["id"])
                        .values(
                            perspectives=update_data["perspectives"],
                            competencies=update_data["competencies"],
                        )
                    )
                await db.commit()
                logger.info("Updates committed to database")

            # Log summary
            self._log_summary()

            return True

    def _log_summary(self):
        """Log backfill summary."""
        logger.info("=" * 60)
        logger.info("BACKFILL SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Course: {self.course_slug}")
        logger.info(f"Questions processed: {self.questions_processed}")
        logger.info(f"Questions updated: {self.questions_updated}")
        logger.info(f"Perspectives assigned: {self.perspectives_assigned}")
        logger.info(f"Competencies assigned: {self.competencies_assigned}")
        if self.dry_run:
            logger.info("DRY RUN - No changes were made")
        logger.info("=" * 60)

        # Distribution by tag
        if self.verbose and self.course:
            if self.course.perspectives:
                logger.info("\nPerspectives defined in course:")
                for p in self.course.perspectives:
                    logger.info(f"  - {p.get('id')}: {p.get('name')}")

            if self.course.competencies:
                logger.info("\nCompetencies defined in course:")
                for c in self.course.competencies:
                    logger.info(f"  - {c.get('id')}: {c.get('name')}")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Backfill secondary tags (perspectives, competencies) for existing questions"
    )
    parser.add_argument(
        "--course-slug",
        required=True,
        help="Course slug (e.g., 'cbap')"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying database"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    backfiller = SecondaryTagBackfiller(
        course_slug=args.course_slug,
        dry_run=args.dry_run,
        verbose=args.verbose,
    )

    success = await backfiller.run()
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
