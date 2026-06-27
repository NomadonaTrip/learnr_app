"""
Re-map existing questions to the (re-extracted) concept set, in place.

After a concept re-extraction the `question_concepts` link table is wiped by
cascade, but the `questions` rows survive with their original UUIDs. This
script repopulates `question_concepts` for the existing questions WITHOUT
deleting or re-importing them (question UUIDs and any answer history are
preserved). It reuses the semantic-search + GPT-4 mapping logic from
import_vendor_questions.py over the new concept embeddings.

Usage:
    python scripts/remap_question_concepts.py --course-slug cbap [--dry-run] [--limit N]

Requires: OPENAI_API_KEY, a running Postgres and Qdrant.
"""
import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Make `src` and the sibling import script importable (mirrors other scripts).
sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "api"))
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select

from import_vendor_questions import VendorQuestionImporter, QuestionData
from src.db.session import AsyncSessionLocal
from src.models.question import Question
from src.models.question_concept import QuestionConcept
from src.repositories.question_repository import QuestionRepository

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def _question_to_data(question: Question, row_number: int) -> QuestionData:
    """Adapt an ORM Question into the QuestionData shape the mapper expects."""
    options = question.options if isinstance(question.options, dict) else {}
    return QuestionData(
        question_text=question.question_text,
        options=options,
        correct_answer=question.correct_answer,
        explanation=question.explanation or "",
        knowledge_area_name="",
        knowledge_area_id=question.knowledge_area_id,
        row_number=row_number,
    )


async def remap(course_slug: str, dry_run: bool, limit: int | None) -> int:
    importer = VendorQuestionImporter(course_slug=course_slug)
    if not await importer.initialize():
        logger.error("Importer initialization failed (check OPENAI_API_KEY / DB).")
        return 1

    # Build / refresh the 'concepts' Qdrant collection from the current concepts.
    await importer.ensure_concept_embeddings()
    valid_concept_ids = {c.id for c in importer.concepts}
    logger.info(f"{len(valid_concept_ids)} concepts available for mapping")

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Question).where(
                Question.course_id == importer.course_id,
                Question.is_active.is_(True),
            )
        )
        questions = list(result.scalars().all())
        if limit:
            questions = questions[:limit]

        # Resume support: skip questions that already have mappings.
        existing = await db.execute(select(QuestionConcept.question_id).distinct())
        already_mapped = {row[0] for row in existing.all()}
        pending = [q for q in questions if q.id not in already_mapped]
        logger.info(
            f"Re-mapping {len(pending)} questions "
            f"({len(questions) - len(pending)} already mapped, skipped)..."
        )

        repo = QuestionRepository(db)
        total_mappings = 0
        unmapped = 0

        for idx, question in enumerate(pending, start=1):
            data = _question_to_data(question, idx)
            embedding = await importer.generate_question_embedding(data)
            mappings = await importer.map_question_to_concepts(data, embedding)

            # Keep only mappings to a real, current concept, and dedupe by
            # concept (GPT-4 can return the same concept twice; the table PK is
            # (question_id, concept_id)).
            seen: set = set()
            deduped = []
            for m in mappings:
                if m.concept_id in valid_concept_ids and m.concept_id not in seen:
                    seen.add(m.concept_id)
                    deduped.append(m)
            mappings = deduped
            if not mappings:
                unmapped += 1
            for mapping in mappings:
                if not dry_run:
                    await repo.add_concept_mapping(
                        question_id=question.id,
                        concept_id=mapping.concept_id,
                        relevance=mapping.relevance,
                    )
                total_mappings += 1

            if idx % 25 == 0:
                logger.info(f"  {idx}/{len(questions)} questions processed")

    logger.info(
        f"Done: {total_mappings} mappings across {len(questions)} questions "
        f"({unmapped} questions with no mapping){' [DRY RUN]' if dry_run else ''}"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Re-map existing questions to current concepts")
    parser.add_argument("--course-slug", default="cbap")
    parser.add_argument("--dry-run", action="store_true", help="Map but do not write question_concepts")
    parser.add_argument("--limit", type=int, help="Process only the first N questions (testing)")
    args = parser.parse_args()
    return asyncio.run(remap(args.course_slug, args.dry_run, args.limit))


if __name__ == "__main__":
    sys.exit(main())
