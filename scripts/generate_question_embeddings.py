"""
Generate embeddings for all questions and upload to Qdrant.

This script reads questions from PostgreSQL (filtered by course), generates
embeddings using OpenAI text-embedding-3-large with concept mappings, and
uploads vectors to Qdrant questions collection with multi-course support.

Usage:
    python scripts/generate_question_embeddings.py --course-slug cbap
    python scripts/generate_question_embeddings.py --course-slug cbap --batch-size 50 --verbose
    python scripts/generate_question_embeddings.py --course-slug cbap --dry-run
    python scripts/generate_question_embeddings.py --course-slug cbap --verify-only
    python scripts/generate_question_embeddings.py --course-slug cbap --force
"""
import argparse
import asyncio
import logging
import sys
import time
from pathlib import Path
from typing import List, Tuple
from uuid import UUID

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "apps" / "api"))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.orm import selectinload  # noqa: E402

from src.config import settings  # noqa: E402
from src.db.session import AsyncSessionLocal  # noqa: E402
from src.models.concept import Concept  # noqa: E402
from src.models.course import Course  # noqa: E402
from src.models.question import Question  # noqa: E402
from src.models.question_concept import QuestionConcept  # noqa: E402
from src.services.embedding_service import EmbeddingService  # noqa: E402
from src.services.qdrant_upload_service import (  # noqa: E402
    QdrantUploadService,
    QuestionVectorItem,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Constants
PROGRESS_LOG_INTERVAL = 50


# =============================================================================
# Course Lookup (Task 4)
# =============================================================================

async def lookup_course_by_slug(db, course_slug: str) -> Course | None:
    """
    Look up course by slug.

    Args:
        db: AsyncSession database session
        course_slug: Course slug (e.g., 'cbap')

    Returns:
        Course object or None if not found
    """
    result = await db.execute(
        select(Course).where(Course.slug == course_slug)
    )
    course = result.scalar_one_or_none()

    if course:
        logger.info(f"Found course: {course.name} (ID: {course.id})")
    else:
        logger.error(f"Course not found: {course_slug}")

    return course


# =============================================================================
# Question Loading with Concepts (Task 4)
# =============================================================================

async def load_questions_with_concepts(
    db,
    course_id: UUID,
    limit: int | None = None
) -> List[Tuple[Question, List[Concept]]]:
    """
    Load all active questions with their concepts for a course.

    Args:
        db: AsyncSession database session
        course_id: Course UUID to filter by
        limit: Optional limit on number of questions (for testing)

    Returns:
        List of tuples (Question, List[Concept])
    """
    # Build query with eager loading of concepts
    query = (
        select(Question)
        .where(Question.course_id == course_id)
        .where(Question.is_active == True)  # noqa: E712
        .options(selectinload(Question.question_concepts).selectinload(QuestionConcept.concept))
    )

    if limit:
        query = query.limit(limit)

    result = await db.execute(query)
    questions = list(result.scalars().all())

    # Build list of (question, concepts) tuples
    questions_with_concepts = []
    for question in questions:
        concepts = [qc.concept for qc in question.question_concepts]
        questions_with_concepts.append((question, concepts))

    logger.info(
        f"Loaded {len(questions_with_concepts)} questions with concepts "
        f"for course {course_id}"
    )

    return questions_with_concepts


# =============================================================================
# Embedding Text Builder (Task 2)
# =============================================================================

def build_embedding_text(question: Question, concepts: List[Concept]) -> str:
    """
    Build text for embedding generation with concepts.

    Format: "{question_text} Options: A: {opt_a}, B: {opt_b}, C: {opt_c}, D: {opt_d} Concepts: {concept_names}"

    Args:
        question: Question model instance
        concepts: List of Concept model instances

    Returns:
        Formatted embedding text string
    """
    # Format options
    options_parts = []
    for key in ["A", "B", "C", "D"]:
        if key in question.options:
            options_parts.append(f"{key}: {question.options[key]}")

    options_text = ", ".join(options_parts)

    # Format concepts
    if concepts:
        concept_names = ", ".join([c.name for c in concepts])
        concepts_text = f" Concepts: {concept_names}"
    else:
        # Fallback to knowledge area if no concepts
        concepts_text = f" Knowledge Area: {question.knowledge_area_id}"

    # Combine all parts
    text = f"{question.question_text} Options: {options_text}{concepts_text}"

    # Truncate if too long (OpenAI has 8191 token limit for embeddings)
    # Rough estimate: 1 token ≈ 4 characters
    MAX_CHARS = 8000 * 4
    if len(text) > MAX_CHARS:
        logger.warning(
            f"Embedding text for question {question.id} is {len(text)} chars, "
            f"truncating to {MAX_CHARS}"
        )
        text = text[:MAX_CHARS]

    return text


# =============================================================================
# Vector Item Builder (Task 3)
# =============================================================================

def build_vector_item(
    question: Question,
    concepts: List[Concept],
    embedding: List[float]
) -> QuestionVectorItem:
    """
    Build QuestionVectorItem from question, concepts, and embedding.

    Args:
        question: Question model instance
        concepts: List of Concept model instances
        embedding: Embedding vector

    Returns:
        QuestionVectorItem ready for upload
    """
    concept_ids = [str(c.id) for c in concepts]
    concept_names = [c.name for c in concepts]

    # Using keyword arguments (required by kw_only=True dataclass)
    return QuestionVectorItem(
        question_id=question.id,
        course_id=question.course_id,
        vector=embedding,
        knowledge_area_id=question.knowledge_area_id,
        difficulty=question.difficulty,
        discrimination=question.discrimination,
        concept_ids=concept_ids,
        concept_names=concept_names,
        question_text=question.question_text,
        options=question.options,
        correct_answer=question.correct_answer
    )


# =============================================================================
# Progress Tracking (Task 5)
# =============================================================================

class ProgressTracker:
    """Track and log progress during embedding generation."""

    def __init__(self, total: int, log_interval: int = PROGRESS_LOG_INTERVAL):
        self.total = total
        self.log_interval = log_interval
        self.start_time = time.time()
        self.last_log_time = self.start_time

    def log_progress(self, processed: int, stage: str = "Processing"):
        """Log progress if interval reached or complete."""
        if processed % self.log_interval == 0 or processed == self.total:
            elapsed = time.time() - self.start_time
            percentage = (processed / self.total) * 100 if self.total > 0 else 0

            # Estimate remaining time
            if processed > 0:
                avg_time_per_item = elapsed / processed
                remaining_items = self.total - processed
                est_remaining = avg_time_per_item * remaining_items
                eta_msg = f", ETA: {est_remaining:.0f}s"
            else:
                eta_msg = ""

            logger.info(
                f"{stage}: {processed}/{self.total} ({percentage:.0f}%){eta_msg}"
            )


# =============================================================================
# Verification (Task 6)
# =============================================================================

async def verify_embeddings(
    db,
    upload_service: QdrantUploadService,
    course_id: UUID
) -> dict:
    """
    Verify embeddings were uploaded correctly for a course.

    Args:
        db: AsyncSession database session
        upload_service: QdrantUploadService instance
        course_id: Course UUID

    Returns:
        Verification report dictionary
    """
    logger.info("Verifying embeddings...")

    # Count questions in PostgreSQL for this course
    result = await db.execute(
        select(Question)
        .where(Question.course_id == course_id)
        .where(Question.is_active == True)  # noqa: E712
    )
    questions = list(result.scalars().all())
    pg_count = len(questions)

    # Verify vectors in Qdrant for this course
    qdrant_result = await upload_service.verify_course_vectors(course_id, pg_count)

    report = {
        "course_id": str(course_id),
        "questions_in_postgresql": pg_count,
        "vectors_in_qdrant": qdrant_result["actual_count"],
        "verified": qdrant_result["verified"],
        "match": pg_count == qdrant_result["actual_count"]
    }

    if report["match"]:
        logger.info(
            f"✓ Verification PASSED: {pg_count} questions match {qdrant_result['actual_count']} vectors"
        )
    else:
        logger.warning(
            f"✗ Verification FAILED: {pg_count} questions != {qdrant_result['actual_count']} vectors"
        )

    return report


# =============================================================================
# Main Orchestrator (Task 8)
# =============================================================================

async def main(
    course_slug: str,
    batch_size: int,
    dry_run: bool,
    verbose: bool,
    verify_only: bool,
    force: bool,
    limit: int | None
) -> None:
    """
    Main workflow for embedding generation and upload.

    Args:
        course_slug: Course slug (e.g., 'cbap')
        batch_size: Number of texts per OpenAI API call
        dry_run: If True, skip actual operations
        verbose: If True, enable debug logging
        verify_only: If True, only run verification
        force: If True, regenerate all embeddings even if exist
        limit: Optional limit on number of questions (for testing)
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    start_time = time.time()

    # Initialize services
    upload_service = QdrantUploadService()

    try:
        # Step 1: Lookup course by slug
        logger.info(f"Step 1: Looking up course '{course_slug}'...")
        async with AsyncSessionLocal() as db:
            course = await lookup_course_by_slug(db, course_slug)
            if not course:
                logger.error(f"Course not found: {course_slug}")
                return

            course_id = course.id

        # Verify-only mode
        if verify_only:
            logger.info("Running verification only...")
            async with AsyncSessionLocal() as db:
                await verify_embeddings(db, upload_service, course_id)
            return

        # Initialize embedding service (only if not dry-run)
        embedding_service = None
        if not dry_run:
            embedding_service = EmbeddingService()

        logger.info(
            f"Starting embedding generation for course '{course_slug}' "
            f"(batch_size={batch_size}, dry_run={dry_run}, force={force})"
        )

        # Step 2: Load all questions with concept mappings
        logger.info("Step 2: Loading questions with concepts from PostgreSQL...")
        async with AsyncSessionLocal() as db:
            questions_with_concepts = await load_questions_with_concepts(
                db, course_id, limit
            )

        if not questions_with_concepts:
            logger.error("No questions found for this course. Exiting.")
            return

        total_questions = len(questions_with_concepts)
        logger.info(f"Found {total_questions} questions to process")

        # Step 3: Build embedding texts
        logger.info("Step 3: Building embedding texts...")
        embedding_texts = []
        for question, concepts in questions_with_concepts:
            text = build_embedding_text(question, concepts)
            embedding_texts.append(text)

        logger.info(f"Built {len(embedding_texts)} embedding texts")

        # Step 4: Generate embeddings in batches
        logger.info("Step 4: Generating embeddings with OpenAI API...")
        progress = ProgressTracker(total_questions)

        def embedding_progress(processed, total):
            progress.log_progress(processed, "Embedding")

        if dry_run:
            logger.info("DRY RUN - Skipping OpenAI API calls")
            embeddings = [[0.0] * 3072 for _ in range(total_questions)]
            total_tokens = 0
        else:
            embeddings, total_tokens = await embedding_service.batch_generate_embeddings(
                embedding_texts,
                batch_size=batch_size,
                progress_callback=embedding_progress
            )

        # Step 5: Build vector items
        logger.info("Step 5: Building vector items...")
        vector_items = []
        for (question, concepts), embedding in zip(questions_with_concepts, embeddings):
            item = build_vector_item(question, concepts, embedding)
            vector_items.append(item)

        # Step 6: Upload embeddings to Qdrant
        logger.info("Step 6: Uploading vectors to Qdrant...")
        upload_progress = ProgressTracker(total_questions)

        def upload_progress_callback(uploaded, skipped, total):
            upload_progress.log_progress(uploaded + skipped, "Upload")

        if dry_run:
            logger.info("DRY RUN - Skipping Qdrant upload")
            uploaded_count = total_questions
            skipped_count = 0
        else:
            uploaded_count, skipped_count = await upload_service.batch_upload_question_vectors(
                vector_items,
                skip_if_exists=not force,  # If force=True, don't skip
                batch_size=batch_size,
                progress_callback=upload_progress_callback
            )

        # Step 7: Verify upload
        logger.info("Step 7: Verifying Qdrant upload...")
        if dry_run:
            logger.info("DRY RUN - Skipping verification")
            verification_report = {"verified": True, "match": True}
        else:
            async with AsyncSessionLocal() as db:
                verification_report = await verify_embeddings(db, upload_service, course_id)

        # Step 8: Log final summary
        elapsed_time = time.time() - start_time
        cost = calculate_cost(total_tokens)

        logger.info("=" * 60)
        logger.info("EMBEDDING GENERATION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Course: {course_slug} (ID: {course_id})")
        logger.info(f"Total questions processed: {total_questions}")
        logger.info(f"Vectors uploaded: {uploaded_count}")
        logger.info(f"Vectors skipped (already existed): {skipped_count}")
        logger.info(f"Total OpenAI tokens used: {total_tokens:,}")
        logger.info(f"Estimated OpenAI cost: ${cost:.4f}")
        logger.info(f"Total time elapsed: {elapsed_time:.2f}s")
        logger.info(f"Verification: {'PASSED ✓' if verification_report['verified'] else 'FAILED ✗'}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Error during embedding generation: {e}", exc_info=True)
        raise
    finally:
        if embedding_service:
            await embedding_service.close()
        await upload_service.close()


def calculate_cost(total_tokens: int) -> float:
    """
    Calculate estimated OpenAI API cost for embeddings.

    Cost: $0.13 per 1M tokens for text-embedding-3-large

    Args:
        total_tokens: Total tokens used

    Returns:
        Estimated cost in USD
    """
    cost_per_million = 0.13
    return (total_tokens / 1_000_000) * cost_per_million


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate embeddings for questions and upload to Qdrant"
    )
    parser.add_argument(
        "--course-slug",
        type=str,
        required=True,
        help="Course slug (e.g., 'cbap')"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Number of texts per OpenAI API call (default: 100)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate without making API calls or uploading"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging"
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify Qdrant collection count for course"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate all embeddings even if they exist"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Process only first N questions (for testing)"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(main(
        course_slug=args.course_slug,
        batch_size=args.batch_size,
        dry_run=args.dry_run,
        verbose=args.verbose,
        verify_only=args.verify_only,
        force=args.force,
        limit=args.limit
    ))
