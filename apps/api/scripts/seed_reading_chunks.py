#!/usr/bin/env python3
"""
Seed Reading Chunks Script

Creates sample reading chunks for testing the reading queue feature.
Inserts chunks into PostgreSQL and uploads embeddings to Qdrant.

Usage:
    cd apps/api
    python scripts/seed_reading_chunks.py
"""

import asyncio
import sys
from pathlib import Path
from uuid import UUID

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config import settings
from src.models.course import Course
from src.models.concept import Concept
from src.models.reading_chunk import ReadingChunk
from src.services.embedding_service import EmbeddingService
from src.services.qdrant_upload_service import ChunkVectorItem, QdrantUploadService


# Target course ID (use None to auto-detect first course)
TARGET_COURSE_ID = "1b8a4860-156f-4d06-8393-85c4088db2d9"

# Sample reading content for Business Analysis (CBAP-style)
# knowledge_area_id values must match the course's actual KA IDs (lowercase with hyphens)
SAMPLE_CHUNKS = [
    {
        "title": "Understanding Stakeholder Analysis",
        "corpus_section": "3.1",
        "knowledge_area_id": "ba-planning",
        "content": """
Stakeholder analysis is a fundamental technique in business analysis that involves identifying
all individuals, groups, or organizations that may affect or be affected by a project or initiative.

Key aspects of stakeholder analysis include:

1. **Identification**: Finding all relevant stakeholders through interviews, document analysis,
   and organizational charts.

2. **Classification**: Grouping stakeholders by their level of influence, interest, and impact
   on the project.

3. **Analysis**: Understanding each stakeholder's needs, expectations, attitudes, and potential
   concerns.

4. **Engagement Strategy**: Developing appropriate communication and involvement approaches
   for different stakeholder groups.

The RACI matrix (Responsible, Accountable, Consulted, Informed) is commonly used to clarify
stakeholder roles and responsibilities. Effective stakeholder analysis ensures that the right
people are involved at the right time, reducing project risks and increasing buy-in.
        """,
        "concepts": ["Stakeholder Analysis", "RACI Matrix", "Stakeholder Engagement"],
    },
    {
        "title": "Requirements Elicitation Techniques",
        "corpus_section": "4.2",
        "knowledge_area_id": "elicitation",
        "content": """
Requirements elicitation is the process of gathering information from stakeholders and other
sources to understand business needs and desired solutions.

Common elicitation techniques include:

1. **Interviews**: One-on-one or group discussions with stakeholders to gather detailed
   information about their needs and expectations.

2. **Workshops**: Facilitated sessions bringing together multiple stakeholders to collaboratively
   define requirements and resolve conflicts.

3. **Document Analysis**: Reviewing existing documentation, systems, and processes to understand
   current state and identify gaps.

4. **Observation**: Watching users perform their work to understand actual processes and
   identify improvement opportunities.

5. **Surveys and Questionnaires**: Collecting information from a large number of stakeholders
   efficiently.

6. **Prototyping**: Creating mockups or models to help stakeholders visualize and refine
   requirements.

The choice of technique depends on factors like stakeholder availability, project complexity,
and the type of information needed.
        """,
        "concepts": ["Elicitation", "Interviews", "Workshops", "Requirements Gathering"],
    },
    {
        "title": "Use Cases and User Stories",
        "corpus_section": "5.1",
        "knowledge_area_id": "requirements-analysis",
        "content": """
Use cases and user stories are two popular techniques for documenting functional requirements
in a way that focuses on user interactions and business value.

**Use Cases**:
- Describe a sequence of actions that provide value to an actor (user or system)
- Include preconditions, main flow, alternative flows, and postconditions
- Often documented using UML use case diagrams
- Well-suited for complex interactions and system behavior

**User Stories**:
- Short, simple descriptions following the format: "As a [role], I want [feature], so that [benefit]"
- Accompanied by acceptance criteria that define when the story is complete
- Emphasize conversation and collaboration over documentation
- Popular in Agile methodologies

Both techniques can be used together - user stories for high-level requirements and use cases
for detailed interaction specifications. The key is to choose the technique that best fits
your project's methodology and stakeholder communication needs.
        """,
        "concepts": ["Use Cases", "User Stories", "Requirements Documentation", "Agile"],
    },
    {
        "title": "Data Flow Diagrams and Process Modeling",
        "corpus_section": "5.3",
        "knowledge_area_id": "requirements-analysis",
        "content": """
Data Flow Diagrams (DFDs) are a visual representation of how data moves through a system,
showing processes, data stores, external entities, and data flows.

**DFD Components**:
- **Processes**: Transformations applied to data (shown as circles or rounded rectangles)
- **Data Stores**: Repositories where data is held (shown as open-ended rectangles)
- **External Entities**: Sources or destinations of data outside the system (shown as squares)
- **Data Flows**: Movement of data between components (shown as arrows)

**DFD Levels**:
- Context Diagram (Level 0): Shows the system as a single process with external entities
- Level 1: Breaks down the main process into sub-processes
- Level 2+: Further decomposition for detailed analysis

**Best Practices**:
1. Start with the context diagram to establish scope
2. Number processes consistently (e.g., 1.0, 1.1, 1.2)
3. Balance the diagram - avoid too many or too few processes per level
4. Ensure data conservation - inputs must account for outputs

DFDs help business analysts communicate system behavior to both technical and non-technical
stakeholders effectively.
        """,
        "concepts": ["Data Flow Diagrams", "Process Modeling", "System Analysis"],
    },
    {
        "title": "Inputs and Outputs in Business Analysis",
        "corpus_section": "2.1",
        "knowledge_area_id": "ba-planning",
        "content": """
Understanding inputs and outputs is fundamental to business analysis planning and execution.
Each business analysis task consumes inputs and produces outputs that may feed into other tasks.

**Common Inputs**:
- Business objectives and goals
- Organizational process assets (templates, guidelines)
- Stakeholder lists and analysis
- Existing system documentation
- Regulatory and compliance requirements

**Common Outputs**:
- Requirements documentation (functional, non-functional)
- Business analysis plans
- Stakeholder engagement approaches
- Traceability matrices
- Solution recommendations

**Traceability**:
Maintaining clear traceability between inputs and outputs ensures:
1. Requirements can be traced back to business objectives
2. Changes can be impact-assessed effectively
3. Test cases cover all requirements
4. Stakeholder needs are addressed

The BABOK (Business Analysis Body of Knowledge) provides detailed guidance on the inputs and
outputs for each knowledge area and task in business analysis.
        """,
        "concepts": ["Inputs", "Outputs", "Traceability", "Business Analysis Planning"],
    },
    {
        "title": "Solution Evaluation and Validation",
        "corpus_section": "8.1",
        "knowledge_area_id": "solution-evaluation",
        "content": """
Solution evaluation assesses how well a delivered solution meets the business need and delivers
expected value. This is an ongoing process throughout the solution lifecycle.

**Evaluation Activities**:

1. **Measure Solution Performance**: Define and track key performance indicators (KPIs) that
   indicate whether the solution is meeting its objectives.

2. **Analyze Performance Measures**: Compare actual results against expected outcomes and
   identify gaps or opportunities for improvement.

3. **Assess Solution Limitations**: Identify constraints, defects, or issues that prevent
   the solution from fully meeting the business need.

4. **Recommend Actions**: Propose changes, enhancements, or retirement based on evaluation
   findings.

**Validation vs. Verification**:
- **Validation**: Confirms the solution meets the business need ("building the right thing")
- **Verification**: Confirms the solution meets specifications ("building the thing right")

Effective solution evaluation requires ongoing collaboration between business analysts,
stakeholders, and the implementation team to ensure continuous value delivery.
        """,
        "concepts": ["Solution Evaluation", "KPIs", "Validation", "Performance Measurement"],
    },
]


async def get_or_create_course(session: AsyncSession) -> Course | None:
    """Get the target course or first available course."""
    if TARGET_COURSE_ID:
        result = await session.execute(
            select(Course).where(Course.id == UUID(TARGET_COURSE_ID))
        )
        course = result.scalar_one_or_none()
        if course:
            return course
        print(f"WARNING: Target course {TARGET_COURSE_ID} not found, using first available")

    result = await session.execute(select(Course).limit(1))
    return result.scalar_one_or_none()


async def get_concepts_by_name(session: AsyncSession, names: list[str]) -> list[Concept]:
    """Get concepts by their names (case-insensitive partial match)."""
    if not names:
        return []

    result = await session.execute(select(Concept))
    all_concepts = result.scalars().all()

    matched = []
    for concept in all_concepts:
        for name in names:
            if name.lower() in concept.name.lower():
                matched.append(concept)
                break

    return matched


async def seed_reading_chunks():
    """Main seeding function."""
    print("=" * 60)
    print("Reading Chunks Seeder")
    print("=" * 60)

    # Create database engine
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Get course
        course = await get_or_create_course(session)
        if not course:
            print("ERROR: No course found in database. Please create a course first.")
            return

        print(f"Using course: {course.name} (ID: {course.id})")

        # Check existing chunks for this course
        result = await session.execute(
            select(ReadingChunk).where(ReadingChunk.course_id == course.id)
        )
        existing_chunks = result.scalars().all()
        print(f"Existing chunks for this course: {len(existing_chunks)}")

        # Create new chunks for this course
        print(f"\nCreating {len(SAMPLE_CHUNKS)} sample reading chunks...")
        chunks_to_embed = []

        for i, chunk_data in enumerate(SAMPLE_CHUNKS):
            # Find matching concepts
            concepts = await get_concepts_by_name(session, chunk_data.get("concepts", []))
            concept_ids = [c.id for c in concepts]

            chunk = ReadingChunk(
                course_id=course.id,
                title=chunk_data["title"],
                content=chunk_data["content"].strip(),
                corpus_section=chunk_data["corpus_section"],
                knowledge_area_id=chunk_data["knowledge_area_id"],
                concept_ids=concept_ids,
                estimated_read_time_minutes=5,
                chunk_index=i,
            )
            session.add(chunk)
            chunks_to_embed.append(chunk)
            print(f"  Created: {chunk.title} (KA: {chunk.knowledge_area_id})")

        await session.commit()
        print(f"\n✓ Created {len(chunks_to_embed)} chunks in PostgreSQL")

        # Generate embeddings and upload to Qdrant
        print("\nGenerating embeddings and uploading to Qdrant...")

        async with EmbeddingService() as embedding_service:
            async with QdrantUploadService() as upload_service:
                uploaded = 0
                skipped = 0

                for chunk in chunks_to_embed:
                    # Check if already in Qdrant
                    if await upload_service.chunk_vector_exists(chunk.id):
                        print(f"  Skipped (exists): {chunk.title[:40]}...")
                        skipped += 1
                        continue

                    # Generate embedding
                    try:
                        embedding = await embedding_service.generate_embedding(
                            f"{chunk.title}\n\n{chunk.content}"
                        )
                    except Exception as e:
                        print(f"  ERROR generating embedding for {chunk.title}: {e}")
                        continue

                    # Create vector item
                    concept_names = []
                    if chunk.concept_ids:
                        result = await session.execute(
                            select(Concept).where(Concept.id.in_(chunk.concept_ids))
                        )
                        concept_names = [c.name for c in result.scalars().all()]

                    vector_item = ChunkVectorItem(
                        chunk_id=chunk.id,
                        course_id=course.id,
                        vector=embedding,
                        title=chunk.title,
                        knowledge_area_id=chunk.knowledge_area_id,
                        corpus_section=chunk.corpus_section,
                        concept_ids=[str(c) for c in (chunk.concept_ids or [])],
                        concept_names=concept_names,
                        text_content=chunk.content[:500],  # First 500 chars
                        estimated_read_time=chunk.estimated_read_time_minutes,
                    )

                    # Upload to Qdrant
                    await upload_service.upload_chunk_vector(vector_item, skip_if_exists=False)
                    uploaded += 1
                    print(f"  Uploaded: {chunk.title[:40]}...")

                print(f"\n✓ Uploaded {uploaded} chunks to Qdrant, skipped {skipped}")

        # Verify Qdrant collection
        print("\nVerifying Qdrant collection...")
        async with QdrantUploadService() as upload_service:
            result = await upload_service.verify_chunk_collection_count()
            print(f"  Total chunks in Qdrant: {result['actual_count']}")

    await engine.dispose()

    print("\n" + "=" * 60)
    print("✓ Seeding Complete!")
    print("=" * 60)
    print("\nYou can now test the reading queue by:")
    print("1. Answering quiz questions incorrectly")
    print("2. Checking the Reading Library page")


if __name__ == "__main__":
    asyncio.run(seed_reading_chunks())
