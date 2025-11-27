#!/usr/bin/env python3
"""
Qdrant Collection Initialization Script

Creates the required Qdrant collections for LearnR:
- cbap_questions: CBAP exam questions with embeddings
- babok_chunks: BABOK reading content chunks with embeddings

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


async def init_collections():
    """Initialize Qdrant collections for questions and BABOK chunks."""
    print("="*60)
    print("Qdrant Collection Initialization")
    print("="*60)
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
    # Collection 1: CBAP Questions
    # =========================================================================
    questions_collection = "cbap_questions"
    print(f"Processing collection: {questions_collection}")

    if questions_collection not in collection_names:
        try:
            # Create collection
            await client.create_collection(
                collection_name=questions_collection,
                vectors_config=VectorParams(
                    size=3072,  # text-embedding-3-large dimensions
                    distance=Distance.COSINE
                )
            )
            print(f"  ✓ Created collection: {questions_collection}")

            # Create payload indexes for filtering
            await client.create_payload_index(
                collection_name=questions_collection,
                field_name="question_id",
                field_schema=PayloadSchemaType.KEYWORD
            )
            print(f"  ✓ Created index: question_id")

            await client.create_payload_index(
                collection_name=questions_collection,
                field_name="ka",
                field_schema=PayloadSchemaType.KEYWORD
            )
            print(f"  ✓ Created index: ka")

            await client.create_payload_index(
                collection_name=questions_collection,
                field_name="difficulty",
                field_schema=PayloadSchemaType.KEYWORD
            )
            print(f"  ✓ Created index: difficulty")

            await client.create_payload_index(
                collection_name=questions_collection,
                field_name="concept_tags",
                field_schema=PayloadSchemaType.KEYWORD
            )
            print(f"  ✓ Created index: concept_tags")

        except Exception as e:
            print(f"  ✗ Failed to create collection {questions_collection}: {str(e)}")
            sys.exit(1)
    else:
        print(f"  ⊙ Collection {questions_collection} already exists (skipping)")

    # =========================================================================
    # Collection 2: BABOK Chunks
    # =========================================================================
    babok_collection = "babok_chunks"
    print(f"\nProcessing collection: {babok_collection}")

    if babok_collection not in collection_names:
        try:
            # Create collection
            await client.create_collection(
                collection_name=babok_collection,
                vectors_config=VectorParams(
                    size=3072,  # text-embedding-3-large dimensions
                    distance=Distance.COSINE
                )
            )
            print(f"  ✓ Created collection: {babok_collection}")

            # Create payload indexes for filtering
            await client.create_payload_index(
                collection_name=babok_collection,
                field_name="chunk_id",
                field_schema=PayloadSchemaType.KEYWORD
            )
            print(f"  ✓ Created index: chunk_id")

            await client.create_payload_index(
                collection_name=babok_collection,
                field_name="ka",
                field_schema=PayloadSchemaType.KEYWORD
            )
            print(f"  ✓ Created index: ka")

            await client.create_payload_index(
                collection_name=babok_collection,
                field_name="section_ref",
                field_schema=PayloadSchemaType.KEYWORD
            )
            print(f"  ✓ Created index: section_ref")

            await client.create_payload_index(
                collection_name=babok_collection,
                field_name="difficulty",
                field_schema=PayloadSchemaType.KEYWORD
            )
            print(f"  ✓ Created index: difficulty")

        except Exception as e:
            print(f"  ✗ Failed to create collection {babok_collection}: {str(e)}")
            sys.exit(1)
    else:
        print(f"  ⊙ Collection {babok_collection} already exists (skipping)")

    # =========================================================================
    # Verify Collections
    # =========================================================================
    print("\n" + "="*60)
    print("Collection Verification")
    print("="*60)

    try:
        # Verify questions collection
        info = await client.get_collection(collection_name=questions_collection)
        print(f"\n{questions_collection}:")
        print(f"  Vectors count: {info.vectors_count}")
        print(f"  Vector size: {info.config.params.vectors.size}")
        print(f"  Distance metric: {info.config.params.vectors.distance}")

        # Verify BABOK chunks collection
        info = await client.get_collection(collection_name=babok_collection)
        print(f"\n{babok_collection}:")
        print(f"  Vectors count: {info.vectors_count}")
        print(f"  Vector size: {info.config.params.vectors.size}")
        print(f"  Distance metric: {info.config.params.vectors.distance}")

        print("\n" + "="*60)
        print("✓ Initialization Complete!")
        print("="*60)
        print(f"\nQdrant collections ready at: {settings.QDRANT_URL}")
        print(f"Web UI: {settings.QDRANT_URL}/dashboard\n")

    except Exception as e:
        print(f"\n✗ Collection verification failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(init_collections())
