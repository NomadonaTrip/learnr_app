#!/usr/bin/env python3
"""
Qdrant Collection Initialization Script

Creates the required Qdrant collections for LearnR with multi-course support:
- questions: Exam questions with embeddings (course-agnostic)
- reading_chunks: Reading content chunks with embeddings (course-agnostic)

Run this script after starting Qdrant to initialize the collections.

Usage:
    python apps/api/scripts/init_qdrant_collections.py
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, PayloadSchemaType
from src.config import settings
import asyncio

# Collection name constants (course-agnostic)
QUESTIONS_COLLECTION = "questions"
CHUNKS_COLLECTION = "reading_chunks"

# Old collection names for migration
OLD_QUESTIONS_COLLECTION = "cbap_questions"
OLD_CHUNKS_COLLECTION = "babok_chunks"


async def init_collections():
    """Initialize Qdrant collections for multi-course architecture."""
    print("=" * 60)
    print("Qdrant Collection Initialization (Multi-Course)")
    print("=" * 60)
    print(f"Connecting to Qdrant at: {settings.QDRANT_URL}\n")

    try:
        client = AsyncQdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
            timeout=settings.QDRANT_TIMEOUT
        )
    except Exception as e:
        print(f"✗ Failed to connect to Qdrant: {str(e)}")
        print("\nMake sure Qdrant is running:")
        print("  docker-compose -f infrastructure/docker/docker-compose.dev.yml up -d qdrant")
        sys.exit(1)

    # Get existing collections
    try:
        collections = (await client.get_collections()).collections
        collection_names = [col.name for col in collections]
        print(f"Existing collections: {collection_names if collection_names else 'None'}\n")
    except Exception as e:
        print(f"✗ Failed to fetch collections: {str(e)}")
        sys.exit(1)

    # =========================================================================
    # Migration: Delete old collections if they exist
    # =========================================================================
    old_collections = [OLD_QUESTIONS_COLLECTION, OLD_CHUNKS_COLLECTION]
    for old_name in old_collections:
        if old_name in collection_names:
            print(f"⚠️  Deleting old collection: {old_name}")
            await client.delete_collection(collection_name=old_name)
            collection_names.remove(old_name)

    # =========================================================================
    # Collection 1: Questions (was cbap_questions)
    # =========================================================================
    print(f"\nProcessing collection: {QUESTIONS_COLLECTION}")

    if QUESTIONS_COLLECTION not in collection_names:
        try:
            # Create collection
            await client.create_collection(
                collection_name=QUESTIONS_COLLECTION,
                vectors_config=VectorParams(
                    size=3072,  # text-embedding-3-large dimensions
                    distance=Distance.COSINE
                )
            )
            print(f"  ✓ Created collection: {QUESTIONS_COLLECTION}")

            # Create payload indexes for filtering
            await client.create_payload_index(
                collection_name=QUESTIONS_COLLECTION,
                field_name="question_id",
                field_schema=PayloadSchemaType.KEYWORD
            )
            print("  ✓ Created index: question_id")

            await client.create_payload_index(
                collection_name=QUESTIONS_COLLECTION,
                field_name="course_id",
                field_schema=PayloadSchemaType.KEYWORD
            )
            print("  ✓ Created index: course_id (multi-course support)")

            await client.create_payload_index(
                collection_name=QUESTIONS_COLLECTION,
                field_name="knowledge_area_id",
                field_schema=PayloadSchemaType.KEYWORD
            )
            print("  ✓ Created index: knowledge_area_id")

            await client.create_payload_index(
                collection_name=QUESTIONS_COLLECTION,
                field_name="difficulty",
                field_schema=PayloadSchemaType.FLOAT
            )
            print("  ✓ Created index: difficulty (float)")

            await client.create_payload_index(
                collection_name=QUESTIONS_COLLECTION,
                field_name="concept_ids",
                field_schema=PayloadSchemaType.KEYWORD
            )
            print("  ✓ Created index: concept_ids")

        except Exception as e:
            print(f"  ✗ Failed to create collection {QUESTIONS_COLLECTION}: {str(e)}")
            sys.exit(1)
    else:
        print(f"  ⊙ Collection {QUESTIONS_COLLECTION} already exists (skipping)")

    # =========================================================================
    # Collection 2: Reading Chunks (was babok_chunks)
    # =========================================================================
    print(f"\nProcessing collection: {CHUNKS_COLLECTION}")

    if CHUNKS_COLLECTION not in collection_names:
        try:
            # Create collection
            await client.create_collection(
                collection_name=CHUNKS_COLLECTION,
                vectors_config=VectorParams(
                    size=3072,  # text-embedding-3-large dimensions
                    distance=Distance.COSINE
                )
            )
            print(f"  ✓ Created collection: {CHUNKS_COLLECTION}")

            # Create payload indexes for filtering
            await client.create_payload_index(
                collection_name=CHUNKS_COLLECTION,
                field_name="chunk_id",
                field_schema=PayloadSchemaType.KEYWORD
            )
            print("  ✓ Created index: chunk_id")

            await client.create_payload_index(
                collection_name=CHUNKS_COLLECTION,
                field_name="course_id",
                field_schema=PayloadSchemaType.KEYWORD
            )
            print("  ✓ Created index: course_id (multi-course support)")

            await client.create_payload_index(
                collection_name=CHUNKS_COLLECTION,
                field_name="knowledge_area_id",
                field_schema=PayloadSchemaType.KEYWORD
            )
            print("  ✓ Created index: knowledge_area_id")

            await client.create_payload_index(
                collection_name=CHUNKS_COLLECTION,
                field_name="section_ref",
                field_schema=PayloadSchemaType.KEYWORD
            )
            print("  ✓ Created index: section_ref")

            await client.create_payload_index(
                collection_name=CHUNKS_COLLECTION,
                field_name="difficulty",
                field_schema=PayloadSchemaType.FLOAT
            )
            print("  ✓ Created index: difficulty (float)")

            await client.create_payload_index(
                collection_name=CHUNKS_COLLECTION,
                field_name="concept_ids",
                field_schema=PayloadSchemaType.KEYWORD
            )
            print("  ✓ Created index: concept_ids")

        except Exception as e:
            print(f"  ✗ Failed to create collection {CHUNKS_COLLECTION}: {str(e)}")
            sys.exit(1)
    else:
        print(f"  ⊙ Collection {CHUNKS_COLLECTION} already exists (skipping)")

    # =========================================================================
    # Verify Collections
    # =========================================================================
    print("\n" + "=" * 60)
    print("Collection Verification")
    print("=" * 60)

    try:
        # Verify questions collection
        info = await client.get_collection(collection_name=QUESTIONS_COLLECTION)
        print(f"\n{QUESTIONS_COLLECTION}:")
        print(f"  Vectors count: {info.vectors_count}")
        print(f"  Vector size: {info.config.params.vectors.size}")
        print(f"  Distance metric: {info.config.params.vectors.distance}")

        # Verify reading chunks collection
        info = await client.get_collection(collection_name=CHUNKS_COLLECTION)
        print(f"\n{CHUNKS_COLLECTION}:")
        print(f"  Vectors count: {info.vectors_count}")
        print(f"  Vector size: {info.config.params.vectors.size}")
        print(f"  Distance metric: {info.config.params.vectors.distance}")

        print("\n" + "=" * 60)
        print("✓ Initialization Complete!")
        print("=" * 60)
        print(f"\nQdrant collections ready at: {settings.QDRANT_URL}")
        print(f"Web UI: {settings.QDRANT_URL}/dashboard")
        print("\nPayload Schema (Multi-Course):")
        print("  questions: question_id, course_id, knowledge_area_id, difficulty, concept_ids")
        print("  reading_chunks: chunk_id, course_id, knowledge_area_id, section_ref, difficulty, concept_ids\n")

    except Exception as e:
        print(f"\n✗ Collection verification failed: {str(e)}")
        sys.exit(1)

    await client.close()


if __name__ == "__main__":
    asyncio.run(init_collections())
