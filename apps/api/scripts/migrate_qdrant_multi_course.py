#!/usr/bin/env python3
"""
Qdrant Multi-Course Migration Script

Migrates vectors from old collections (cbap_questions, babok_chunks) to new
multi-course collections (questions, reading_chunks) with updated payload schema.

This script:
1. Scrolls through all vectors in old collections
2. Transforms payloads to new schema (ka -> knowledge_area_id, etc.)
3. Adds course_id to each vector (default: CBAP course)
4. Inserts into new collections
5. Optionally deletes old collections

Usage:
    python apps/api/scripts/migrate_qdrant_multi_course.py [--delete-old]

Options:
    --delete-old    Delete old collections after successful migration

Note: For fresh environments, it's simpler to just run init_qdrant_collections.py
and re-import data. This script is for preserving existing dev data.
"""

import sys
import argparse
from pathlib import Path
from uuid import uuid4

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import PointStruct
from src.config import settings
import asyncio

# Old collection names
OLD_QUESTIONS_COLLECTION = "cbap_questions"
OLD_CHUNKS_COLLECTION = "babok_chunks"

# New collection names
NEW_QUESTIONS_COLLECTION = "questions"
NEW_CHUNKS_COLLECTION = "reading_chunks"

# Default course ID for migration (CBAP course)
# In production, this should come from the courses table
DEFAULT_COURSE_ID = str(uuid4())


def transform_question_payload(old_payload: dict, course_id: str) -> dict:
    """Transform old question payload to new multi-course schema."""
    new_payload = {
        "question_id": old_payload.get("question_id", str(uuid4())),
        "course_id": course_id,
        "knowledge_area_id": old_payload.get("ka", "unknown"),
        "difficulty": convert_difficulty(old_payload.get("difficulty", "Medium")),
        "concept_ids": old_payload.get("concept_tags", []),
        "question_text": old_payload.get("question_text", ""),
        "options": old_payload.get("options", ""),
        "correct_answer": old_payload.get("correct_answer", ""),
    }
    return new_payload


def transform_chunk_payload(old_payload: dict, course_id: str) -> dict:
    """Transform old chunk payload to new multi-course schema."""
    new_payload = {
        "chunk_id": old_payload.get("chunk_id", str(uuid4())),
        "course_id": course_id,
        "knowledge_area_id": old_payload.get("ka", "unknown"),
        "section_ref": old_payload.get("section_ref", ""),
        "difficulty": convert_difficulty(old_payload.get("difficulty", "Medium")),
        "concept_ids": old_payload.get("concept_tags", []),
        "text_content": old_payload.get("text_content", ""),
    }
    return new_payload


def convert_difficulty(difficulty: str | float) -> float:
    """Convert string difficulty to float (0.0-1.0)."""
    if isinstance(difficulty, (int, float)):
        return float(difficulty)

    difficulty_map = {
        "easy": 0.3,
        "medium": 0.5,
        "hard": 0.8,
    }
    return difficulty_map.get(str(difficulty).lower(), 0.5)


async def migrate_collection(
    client: AsyncQdrantClient,
    old_collection: str,
    new_collection: str,
    transform_fn: callable,
    course_id: str
) -> int:
    """Migrate vectors from old collection to new collection."""
    # Check if old collection exists
    collections = await client.get_collections()
    collection_names = [c.name for c in collections.collections]

    if old_collection not in collection_names:
        print(f"  Old collection '{old_collection}' does not exist. Skipping.")
        return 0

    if new_collection not in collection_names:
        print(f"  New collection '{new_collection}' does not exist. Run init script first.")
        return 0

    # Scroll through all vectors in old collection
    migrated_count = 0
    offset = None
    batch_size = 100

    print(f"  Migrating {old_collection} -> {new_collection}...")

    while True:
        # Scroll batch
        records, next_offset = await client.scroll(
            collection_name=old_collection,
            limit=batch_size,
            offset=offset,
            with_vectors=True,
            with_payload=True
        )

        if not records:
            break

        # Transform and insert
        points = []
        for record in records:
            new_payload = transform_fn(record.payload, course_id)
            points.append(
                PointStruct(
                    id=record.id,
                    vector=record.vector,
                    payload=new_payload
                )
            )

        if points:
            await client.upsert(
                collection_name=new_collection,
                points=points
            )
            migrated_count += len(points)
            print(f"    Migrated {migrated_count} vectors...")

        if next_offset is None:
            break
        offset = next_offset

    return migrated_count


async def migrate_all(delete_old: bool = False):
    """Run the full migration."""
    print("=" * 60)
    print("Qdrant Multi-Course Migration")
    print("=" * 60)
    print(f"Connecting to Qdrant at: {settings.QDRANT_URL}")
    print(f"Default course ID: {DEFAULT_COURSE_ID}\n")

    try:
        client = AsyncQdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
            timeout=settings.QDRANT_TIMEOUT
        )
    except Exception as e:
        print(f"Failed to connect to Qdrant: {str(e)}")
        sys.exit(1)

    # Migrate questions
    print("\n[1/2] Migrating questions...")
    questions_count = await migrate_collection(
        client,
        OLD_QUESTIONS_COLLECTION,
        NEW_QUESTIONS_COLLECTION,
        transform_question_payload,
        DEFAULT_COURSE_ID
    )

    # Migrate chunks
    print("\n[2/2] Migrating reading chunks...")
    chunks_count = await migrate_collection(
        client,
        OLD_CHUNKS_COLLECTION,
        NEW_CHUNKS_COLLECTION,
        transform_chunk_payload,
        DEFAULT_COURSE_ID
    )

    # Summary
    print("\n" + "=" * 60)
    print("Migration Summary")
    print("=" * 60)
    print(f"  Questions migrated: {questions_count}")
    print(f"  Chunks migrated: {chunks_count}")

    # Optionally delete old collections
    if delete_old and (questions_count > 0 or chunks_count > 0):
        print("\n  Deleting old collections...")
        collections = await client.get_collections()
        collection_names = [c.name for c in collections.collections]

        for old_col in [OLD_QUESTIONS_COLLECTION, OLD_CHUNKS_COLLECTION]:
            if old_col in collection_names:
                await client.delete_collection(collection_name=old_col)
                print(f"    Deleted: {old_col}")

    print("\n" + "=" * 60)
    print("Migration Complete!")
    print("=" * 60)
    print("\nNote: Update the course_id in migrated vectors to match")
    print("actual course UUIDs from your courses table.")

    await client.close()


def main():
    parser = argparse.ArgumentParser(description="Migrate Qdrant to multi-course schema")
    parser.add_argument(
        "--delete-old",
        action="store_true",
        help="Delete old collections after migration"
    )
    args = parser.parse_args()

    asyncio.run(migrate_all(delete_old=args.delete_old))


if __name__ == "__main__":
    main()
