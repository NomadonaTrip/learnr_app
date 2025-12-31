"""
Corpus Parsing and Chunking Script (Multi-Course Support).

Parses course corpus documents (e.g., BABOK v3 PDF), chunks content using
hybrid strategy, and links chunks to concepts within a specific course.

Usage:
    python scripts/parse_corpus.py --course-slug cbap --pdf-path path/to/babok.pdf
    python scripts/parse_corpus.py --course-slug cbap --pdf-path path/to/babok.pdf --dry-run
"""
import argparse
import asyncio
import csv
import logging
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from uuid import UUID

import fitz  # PyMuPDF
import tiktoken

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "apps" / "api"))

# Load environment variables from apps/api/.env
from dotenv import load_dotenv
load_dotenv(project_root / "apps" / "api" / ".env")

from src.config import settings
from src.db.session import AsyncSessionLocal
from src.models.concept import Concept
from src.models.course import Course
from src.repositories.concept_repository import ConceptRepository
from src.repositories.course_repository import CourseRepository
from src.repositories.reading_chunk_repository import ReadingChunkRepository
from src.schemas.reading_chunk import ChunkCreate

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize tiktoken encoder for token counting
enc = tiktoken.get_encoding("cl100k_base")


@dataclass
class CorpusSection:
    """Represents a parsed corpus section."""

    section_ref: str  # e.g., "3.2.1"
    title: str
    content: str
    knowledge_area_id: str
    page_numbers: List[int]


@dataclass
class Chunk:
    """Represents a content chunk before database insertion."""

    course_id: UUID
    title: str
    content: str
    corpus_section: str
    knowledge_area_id: str
    concept_ids: List[UUID]
    estimated_read_time_minutes: int
    chunk_index: int
    token_count: int = 0  # For validation


@dataclass
class ParseStats:
    """Statistics from the parsing and chunking process."""

    total_sections: int = 0
    total_chunks: int = 0
    chunks_by_ka: Dict[str, int] = field(default_factory=dict)
    chunks_without_concepts: int = 0
    total_tokens: int = 0
    min_tokens: int = 9999
    max_tokens: int = 0
    avg_tokens: float = 0.0


def get_ka_mapping(course: Course) -> Dict[str, str]:
    """
    Build section→KA mapping from course knowledge_areas JSONB.

    Args:
        course: Course model with knowledge_areas JSONB

    Returns:
        Dict mapping section prefix (e.g., "3") to knowledge_area_id
    """
    ka_mapping = {}
    for ka in course.knowledge_areas:
        if "section_prefix" in ka:
            ka_mapping[ka["section_prefix"]] = ka["id"]
    return ka_mapping


def get_ka_from_section(section_ref: str, ka_mapping: Dict[str, str]) -> str:
    """
    Get Knowledge Area ID from section reference using dynamic mapping.

    Args:
        section_ref: Section reference (e.g., "3.2.1")
        ka_mapping: Mapping from section prefix to KA ID

    Returns:
        Knowledge area ID or "unknown"
    """
    first_digit = section_ref.split(".")[0]
    return ka_mapping.get(first_digit, "unknown")


def parse_pdf(pdf_path: str, course: Course) -> List[CorpusSection]:
    """
    Parse PDF and extract structured sections.

    Args:
        pdf_path: Path to corpus PDF
        course: Course model for KA mapping

    Returns:
        List of CorpusSection objects
    """
    logger.info(f"Parsing PDF: {pdf_path}")
    ka_mapping = get_ka_mapping(course)

    sections: List[CorpusSection] = []
    current_section: Optional[Dict] = None

    try:
        doc = fitz.open(pdf_path)
        section_pattern = re.compile(r"^(\d+(?:\.\d+)*)\s+(.+)$")

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()

            # Process each line to detect section headers
            for line in text.split("\n"):
                line = line.strip()
                if not line:
                    continue

                # Check if line is a section header
                match = section_pattern.match(line)
                if match:
                    # Save previous section if exists
                    if current_section:
                        ka_id = get_ka_from_section(
                            current_section["section_ref"], ka_mapping
                        )
                        sections.append(
                            CorpusSection(
                                section_ref=current_section["section_ref"],
                                title=current_section["title"],
                                content=current_section["content"].strip(),
                                knowledge_area_id=ka_id,
                                page_numbers=current_section["pages"],
                            )
                        )

                    # Start new section
                    section_num, section_title = match.groups()
                    current_section = {
                        "section_ref": section_num,
                        "title": section_title.strip(),
                        "content": "",
                        "pages": [page_num + 1],
                    }
                    logger.debug(f"Found section: {section_num} - {section_title}")
                elif current_section:
                    # Append content to current section
                    current_section["content"] += f"{line}\n"
                    if page_num + 1 not in current_section["pages"]:
                        current_section["pages"].append(page_num + 1)

        # Save final section
        if current_section:
            ka_id = get_ka_from_section(current_section["section_ref"], ka_mapping)
            sections.append(
                CorpusSection(
                    section_ref=current_section["section_ref"],
                    title=current_section["title"],
                    content=current_section["content"].strip(),
                    knowledge_area_id=ka_id,
                    page_numbers=current_section["pages"],
                )
            )

        doc.close()
        logger.info(f"Parsed {len(sections)} sections from PDF")
        return sections

    except Exception as e:
        logger.error(f"Error parsing PDF: {e}")
        raise


def chunk_section(
    section: CorpusSection,
    min_tokens: int = 200,
    max_tokens: int = 500,
    overlap_tokens: int = 50,
) -> List[Tuple[str, int]]:
    """
    Chunk a section using hybrid strategy.

    Rules:
    1. Never split across section boundaries
    2. Target 200-500 tokens per chunk
    3. Prefer splitting at paragraph boundaries
    4. Add 50-token overlap for context

    Args:
        section: CorpusSection to chunk
        min_tokens: Minimum tokens per chunk
        max_tokens: Maximum tokens per chunk
        overlap_tokens: Overlap between chunks

    Returns:
        List of (content, chunk_index) tuples
    """
    paragraphs = [p.strip() for p in section.content.split("\n\n") if p.strip()]
    chunks: List[Tuple[str, int]] = []
    current_chunk: List[str] = []
    current_tokens = 0

    for para in paragraphs:
        para_tokens = len(enc.encode(para))

        if current_tokens + para_tokens > max_tokens and current_chunk:
            # Emit current chunk
            chunk_content = "\n\n".join(current_chunk)
            chunks.append((chunk_content, len(chunks)))

            # Start new chunk with overlap
            overlap_text = get_overlap(current_chunk, overlap_tokens)
            current_chunk = [overlap_text, para] if overlap_text else [para]
            current_tokens = len(enc.encode("\n\n".join(current_chunk)))
        else:
            current_chunk.append(para)
            current_tokens += para_tokens

    # Emit final chunk if not empty
    if current_chunk:
        chunk_content = "\n\n".join(current_chunk)
        chunks.append((chunk_content, len(chunks)))

    return chunks


def get_overlap(chunks: List[str], overlap_tokens: int) -> str:
    """
    Get overlap text from previous chunk.

    Args:
        chunks: List of paragraph strings
        overlap_tokens: Number of tokens to overlap

    Returns:
        Overlap text (last N tokens from chunks)
    """
    if not chunks:
        return ""

    # Get text from last paragraph(s)
    combined = "\n\n".join(chunks)
    tokens = enc.encode(combined)

    if len(tokens) <= overlap_tokens:
        return combined

    # Take last N tokens
    overlap = enc.decode(tokens[-overlap_tokens:])
    return overlap


def generate_chunk_title(section: CorpusSection, chunk_index: int, total_chunks: int) -> str:
    """
    Generate title for chunk.

    Format:
    - Single chunk: "{Section Title}"
    - Multiple chunks: "{Section Title} - Part {N}"

    Args:
        section: CorpusSection being chunked
        chunk_index: Index of this chunk (0-based)
        total_chunks: Total number of chunks for this section

    Returns:
        Generated title (max 255 chars)
    """
    if total_chunks == 1:
        title = section.title
    else:
        title = f"{section.title} - Part {chunk_index + 1}"

    # Truncate if needed
    if len(title) > 255:
        title = title[:252] + "..."

    return title


def estimate_read_time(content: str) -> int:
    """
    Estimate read time based on word count.

    Average reading speed: 200 words per minute.

    Args:
        content: Chunk content text

    Returns:
        Estimated minutes (minimum 1)
    """
    word_count = len(content.split())
    minutes = max(1, word_count // 200)
    return minutes


def link_chunk_to_concepts(
    chunk_section_ref: str, concepts: List[Concept], course_id: UUID
) -> List[UUID]:
    """
    Link a chunk to concepts based on section reference.

    Matching rules:
    1. Course filter: Only concepts from same course
    2. Exact match: chunk 3.2.1 → concept 3.2.1
    3. Parent match: chunk 3.2.1 → concept 3.2 (parent)
    4. Child match: chunk 3.2 → concepts 3.2.1, 3.2.2 (children)

    Args:
        chunk_section_ref: Section reference (e.g., "3.2.1")
        concepts: List of all concepts for the course
        course_id: Course UUID to filter by

    Returns:
        List of matched concept UUIDs
    """
    matched_ids: List[UUID] = []

    for concept in concepts:
        # Filter by course
        if concept.course_id != course_id:
            continue

        if not concept.corpus_section_ref:
            continue

        concept_ref = concept.corpus_section_ref

        # Exact match
        if concept_ref == chunk_section_ref:
            matched_ids.append(concept.id)
            continue

        # Chunk is child of concept (parent match)
        if chunk_section_ref.startswith(concept_ref + "."):
            matched_ids.append(concept.id)
            continue

        # Concept is child of chunk (child match)
        if concept_ref.startswith(chunk_section_ref + "."):
            matched_ids.append(concept.id)
            continue

    return matched_ids


async def process_sections(
    sections: List[CorpusSection],
    course: Course,
    concepts: List[Concept],
    min_tokens: int,
    max_tokens: int,
) -> List[Chunk]:
    """
    Process sections into chunks with concept linking.

    Args:
        sections: List of parsed sections
        course: Course model
        concepts: List of concepts for linking
        min_tokens: Minimum tokens per chunk
        max_tokens: Maximum tokens per chunk

    Returns:
        List of Chunk objects ready for database insertion
    """
    logger.info(f"Processing {len(sections)} sections into chunks...")
    all_chunks: List[Chunk] = []

    for section in sections:
        # Chunk the section
        chunk_tuples = chunk_section(section, min_tokens, max_tokens)

        # Create Chunk objects
        for content, chunk_index in chunk_tuples:
            # Generate title
            title = generate_chunk_title(section, chunk_index, len(chunk_tuples))

            # Link to concepts
            concept_ids = link_chunk_to_concepts(
                section.section_ref, concepts, course.id
            )

            # Estimate read time
            read_time = estimate_read_time(content)

            # Calculate token count for validation
            token_count = len(enc.encode(content))

            chunk = Chunk(
                course_id=course.id,
                title=title,
                content=content,
                corpus_section=section.section_ref,
                knowledge_area_id=section.knowledge_area_id,
                concept_ids=concept_ids,
                estimated_read_time_minutes=read_time,
                chunk_index=chunk_index,
                token_count=token_count,
            )
            all_chunks.append(chunk)

    logger.info(f"Created {len(all_chunks)} chunks from {len(sections)} sections")
    return all_chunks


def validate_chunks(
    chunks: List[Chunk], min_tokens: int, max_tokens: int
) -> Dict:
    """
    Validate chunks and generate coverage report.

    Validation rules:
    - Each chunk has at least 1 concept
    - Each KA has 20+ chunks
    - Total chunks in range 200-500
    - Token counts within min/max

    Args:
        chunks: List of Chunk objects
        min_tokens: Minimum tokens per chunk
        max_tokens: Maximum tokens per chunk

    Returns:
        Validation report dictionary
    """
    logger.info("Validating chunks...")

    # Count chunks by KA
    chunks_by_ka = {}
    for chunk in chunks:
        ka = chunk.knowledge_area_id
        chunks_by_ka[ka] = chunks_by_ka.get(ka, 0) + 1

    # Find orphan chunks
    orphan_chunks = [c for c in chunks if not c.concept_ids]

    # Token validation
    chunks_below_min = [c for c in chunks if c.token_count < min_tokens]
    chunks_above_max = [c for c in chunks if c.token_count > max_tokens]

    # KA validation
    kas_below_threshold = {
        ka: count for ka, count in chunks_by_ka.items() if count < 20
    }

    # Generate validation report
    report = {
        "total_chunks": len(chunks),
        "chunks_per_ka": chunks_by_ka,
        "chunks_without_concepts": len(orphan_chunks),
        "orphan_sections": [c.corpus_section for c in orphan_chunks],
        "chunks_below_min_tokens": len(chunks_below_min),
        "chunks_above_max_tokens": len(chunks_above_max),
        "kas_below_threshold": kas_below_threshold,
        "validation_passed": True,
    }

    # Check validation criteria
    errors = []
    if len(chunks) < 200:
        errors.append(f"Total chunks ({len(chunks)}) below minimum (200)")
    if len(chunks) > 500:
        errors.append(f"Total chunks ({len(chunks)}) above maximum (500)")
    if len(orphan_chunks) > 0:
        errors.append(
            f"{len(orphan_chunks)} chunks without concepts (see orphan_sections)"
        )
    if kas_below_threshold:
        errors.append(
            f"Knowledge areas below 20 chunks threshold: {list(kas_below_threshold.keys())}"
        )

    report["errors"] = errors
    report["validation_passed"] = len(errors) == 0

    # Log results
    if report["validation_passed"]:
        logger.info("✓ Validation PASSED")
    else:
        logger.warning("✗ Validation FAILED:")
        for error in errors:
            logger.warning(f"  - {error}")

    # Log statistics
    total_concepts = sum(len(c.concept_ids) for c in chunks)
    avg_concepts = total_concepts / len(chunks) if chunks else 0
    logger.info(f"Total chunks: {len(chunks)}")
    logger.info(f"Chunks by KA: {chunks_by_ka}")
    logger.info(f"Average concepts per chunk: {avg_concepts:.2f}")

    return report


def export_chunks_to_csv(chunks: List[Chunk], concepts: List[Concept], output_path: str):
    """
    Export chunks to CSV for SME review.

    Columns: id, title, corpus_section, knowledge_area, concept_count,
             concept_names, content_preview, estimated_read_time

    Args:
        chunks: List of Chunk objects
        concepts: List of Concept objects for name lookup
        output_path: Output CSV file path
    """
    logger.info(f"Exporting chunks to CSV: {output_path}")

    # Build concept ID → name mapping
    concept_map = {c.id: c.name for c in concepts}

    # Sort chunks by section for easy review
    sorted_chunks = sorted(chunks, key=lambda c: c.corpus_section)

    # Write CSV
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "course_id",
                "title",
                "corpus_section",
                "knowledge_area",
                "concept_count",
                "concept_names",
                "content_preview",
                "estimated_read_time",
            ],
        )
        writer.writeheader()

        for chunk in sorted_chunks:
            concept_names = ", ".join(
                concept_map.get(cid, "Unknown") for cid in chunk.concept_ids
            )
            content_preview = chunk.content[:100] + "..." if len(chunk.content) > 100 else chunk.content

            writer.writerow(
                {
                    "course_id": str(chunk.course_id),
                    "title": chunk.title,
                    "corpus_section": chunk.corpus_section,
                    "knowledge_area": chunk.knowledge_area_id,
                    "concept_count": len(chunk.concept_ids),
                    "concept_names": concept_names,
                    "content_preview": content_preview,
                    "estimated_read_time": chunk.estimated_read_time_minutes,
                }
            )

    logger.info(f"Exported {len(sorted_chunks)} chunks to {output_path}")


async def main():
    """Main orchestrator function."""
    parser = argparse.ArgumentParser(
        description="Parse corpus PDF and create reading chunks"
    )
    parser.add_argument(
        "--course-slug",
        required=True,
        help="Course slug (e.g., 'cbap')",
    )
    parser.add_argument(
        "--pdf-path",
        required=True,
        help="Path to corpus PDF file",
    )
    parser.add_argument(
        "--output-csv",
        default="scripts/output/reading_chunks_export.csv",
        help="Path for CSV export",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and chunk without database writes",
    )
    parser.add_argument(
        "--min-tokens",
        type=int,
        default=200,
        help="Minimum tokens per chunk",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=500,
        help="Maximum tokens per chunk",
    )

    args = parser.parse_args()

    # Validate PDF path
    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        logger.error(f"PDF file not found: {pdf_path}")
        sys.exit(1)

    try:
        async with AsyncSessionLocal() as session:
            # Step 1: Look up course by slug
            logger.info(f"Looking up course: {args.course_slug}")
            course_repo = CourseRepository(session)
            course = await course_repo.get_by_slug(args.course_slug)
            if not course:
                logger.error(f"Course not found: {args.course_slug}")
                sys.exit(1)
            logger.info(f"Found course: {course.name} (ID: {course.id})")

            # Step 2: Parse PDF
            sections = parse_pdf(str(pdf_path), course)

            # Step 3: Load concepts for course
            logger.info(f"Loading concepts for course {args.course_slug}...")
            concept_repo = ConceptRepository(session)
            concepts = await concept_repo.get_all_concepts(course.id)
            logger.info(f"Loaded {len(concepts)} concepts")

            # Step 4-7: Process sections into chunks
            chunks = await process_sections(
                sections, course, concepts, args.min_tokens, args.max_tokens
            )

            # Step 8: Validate results
            validation_report = validate_chunks(chunks, args.min_tokens, args.max_tokens)

            # Step 9: Store in PostgreSQL (unless dry-run)
            if not args.dry_run:
                logger.info("Storing chunks in database...")
                chunk_repo = ReadingChunkRepository(session)

                # Convert to ChunkCreate schemas
                chunk_creates = [
                    ChunkCreate(
                        course_id=c.course_id,
                        title=c.title,
                        content=c.content,
                        corpus_section=c.corpus_section,
                        knowledge_area_id=c.knowledge_area_id,
                        concept_ids=c.concept_ids,
                        estimated_read_time_minutes=c.estimated_read_time_minutes,
                        chunk_index=c.chunk_index,
                    )
                    for c in chunks
                ]

                count = await chunk_repo.bulk_create(chunk_creates)
                await session.commit()
                logger.info(f"✓ Inserted {count} chunks into database")
            else:
                logger.info("DRY RUN - Skipping database insert")

            # Step 10: Export to CSV
            export_chunks_to_csv(chunks, concepts, args.output_csv)

            # Step 11: Print comprehensive report
            print("\n" + "=" * 60)
            print("CORPUS PARSING & CHUNKING REPORT")
            print("=" * 60)
            print(f"Course: {course.name} ({args.course_slug})")
            print(f"PDF: {pdf_path}")
            print(f"Sections parsed: {len(sections)}")
            print(f"Total chunks created: {len(chunks)}")
            print(f"Chunks by Knowledge Area:")
            for ka, count in validation_report["chunks_per_ka"].items():
                print(f"  - {ka}: {count}")
            print(f"Chunks without concepts: {validation_report['chunks_without_concepts']}")
            print(f"Chunks below min tokens: {validation_report['chunks_below_min_tokens']}")
            print(f"Chunks above max tokens: {validation_report['chunks_above_max_tokens']}")
            print(f"\nValidation: {'PASSED' if validation_report['validation_passed'] else 'FAILED'}")
            if not validation_report["validation_passed"]:
                print("Errors:")
                for error in validation_report["errors"]:
                    print(f"  - {error}")
            print(f"\nCSV Export: {args.output_csv}")
            print("=" * 60)

    except Exception as e:
        logger.error(f"Error during execution: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
