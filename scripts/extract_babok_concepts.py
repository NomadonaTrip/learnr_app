"""
BABOK v3 Concept Extraction Script.

Extracts discrete, testable concepts from BABOK v3 PDF and stores them
in PostgreSQL scoped to the CBAP course.

Uses hybrid approach:
- Structural extraction: Parse section numbers and titles
- Semantic extraction: GPT-4 identifies concept boundaries within sections
- Deduplication: Fuzzy matching to remove duplicate concepts
"""
import argparse
import asyncio
import csv
import json
import logging
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

import fitz  # PyMuPDF
from openai import OpenAI
from thefuzz import fuzz

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "apps" / "api"))

from src.config import settings
from src.db.session import AsyncSessionLocal
from src.repositories.concept_repository import ConceptRepository
from src.repositories.course_repository import CourseRepository
from src.schemas.concept import ConceptCreate

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def _sanitize_error_message(error_msg: str) -> str:
    """
    Sanitize error messages to prevent sensitive data exposure.

    SEC-001: Removes API keys, tokens, and other sensitive patterns from error messages.

    Args:
        error_msg: Original error message string

    Returns:
        Sanitized error message with sensitive data redacted
    """
    import re

    # Pattern for API keys (sk-..., api-key, bearer tokens, etc.)
    patterns = [
        (r'sk-[a-zA-Z0-9]{32,}', '[REDACTED_API_KEY]'),
        (r'api[_-]?key[=:]\s*["\']?[\w-]+["\']?', 'api_key=[REDACTED]'),
        (r'bearer\s+[\w.-]+', 'Bearer [REDACTED]'),
        (r'authorization[=:]\s*["\']?[\w.-]+["\']?', 'authorization=[REDACTED]'),
        (r'openai[_-]?api[_-]?key[=:]\s*[\w-]+', 'OPENAI_API_KEY=[REDACTED]'),
        # Generic key patterns that might appear in exception messages
        (r'key["\']?\s*[=:]\s*["\']?[a-zA-Z0-9_-]{20,}["\']?', 'key=[REDACTED]'),
    ]

    sanitized = error_msg
    for pattern, replacement in patterns:
        sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)

    return sanitized

# BABOK v3 Knowledge Areas with chapter mappings
BABOK_KA_CHAPTERS = {
    3: "ba-planning",      # Chapter 3: Business Analysis Planning and Monitoring
    4: "elicitation",      # Chapter 4: Elicitation and Collaboration
    5: "rlcm",             # Chapter 5: Requirements Life Cycle Management
    6: "strategy",         # Chapter 6: Strategy Analysis
    7: "radd",             # Chapter 7: Requirements Analysis and Design Definition
    8: "solution-eval",    # Chapter 8: Solution Evaluation
}

# Concept extraction prompt template
CONCEPT_EXTRACTION_PROMPT = """Given this BABOK v3 section, identify distinct testable concepts.

Section: {section_number} - {section_title}
Knowledge Area: {knowledge_area}
Content:
{section_content}

For each concept, provide:
1. name: Clear, specific, testable name (e.g., "RACI Matrix Construction" not "RACI")
2. description: 1-2 sentence definition that explains what the learner should know
3. difficulty_estimate: 0.0-1.0 (0.0 = foundational, 1.0 = advanced)

Output as JSON array:
[
  {{
    "name": "Concept Name",
    "description": "What the learner should understand...",
    "difficulty_estimate": 0.5
  }}
]

Rules:
- Each concept must represent a single, distinct piece of knowledge
- Concepts must be testable with a multiple-choice question
- Avoid overly broad concepts (e.g., "Business Analysis" is too broad)
- Avoid overly narrow concepts (e.g., "RACI Matrix Row 3" is too narrow)
- Target 3-10 concepts per major section, 1-3 per minor section
- Return ONLY the JSON array, no additional text"""


@dataclass
class BabokSection:
    """Represents a parsed BABOK section."""
    section_number: str  # e.g., "3.2.1"
    title: str
    content: str
    chapter: int  # 3-8 for KA chapters
    depth: int  # 1=chapter, 2=section, 3=subsection, etc.
    page_start: int
    page_end: int


@dataclass
class ConceptCandidate:
    """Represents an extracted concept before validation."""
    name: str
    description: str
    corpus_section_ref: str
    knowledge_area_id: str
    difficulty_estimate: float
    prerequisite_depth: int = 0


@dataclass
class ExtractionStats:
    """Statistics from the extraction process."""
    total_sections_parsed: int = 0
    total_concepts_extracted: int = 0
    concepts_after_dedup: int = 0
    concepts_by_ka: Dict[str, int] = field(default_factory=dict)
    sections_without_concepts: List[str] = field(default_factory=list)
    all_sections: List[str] = field(default_factory=list)
    api_calls: int = 0
    total_tokens: int = 0


class BabokPdfParser:
    """Parses BABOK v3 PDF to extract sections."""

    # Regex pattern for section numbers (e.g., "3.2.1")
    SECTION_PATTERN = re.compile(r'^(\d+(?:\.\d+)*)\s+(.+)$', re.MULTILINE)

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.doc = None

    def open(self) -> None:
        """Open the PDF document."""
        self.doc = fitz.open(self.pdf_path)
        logger.info(f"Opened PDF: {self.pdf_path} ({len(self.doc)} pages)")

    def close(self) -> None:
        """Close the PDF document."""
        if self.doc:
            self.doc.close()

    def parse_babok_pdf(self) -> List[BabokSection]:
        """
        Parse BABOK v3 PDF and extract sections.

        Returns:
            List of BabokSection objects
        """
        if not self.doc:
            self.open()

        sections = []
        current_section = None
        current_content = []

        for page_num in range(len(self.doc)):
            page = self.doc[page_num]
            text = page.get_text()

            # Find section headers in the text
            for match in self.SECTION_PATTERN.finditer(text):
                section_num = match.group(1)
                title = match.group(2).strip()

                # Only process KA chapters (3-8)
                chapter = int(section_num.split('.')[0])
                if chapter not in BABOK_KA_CHAPTERS:
                    continue

                # Save previous section if exists
                if current_section:
                    current_section.content = '\n'.join(current_content)
                    current_section.page_end = page_num
                    if len(current_section.content.strip()) > 50:  # Minimum content
                        sections.append(current_section)
                    current_content = []

                # Calculate depth
                depth = len(section_num.split('.'))

                # Start new section
                current_section = BabokSection(
                    section_number=section_num,
                    title=title,
                    content='',
                    chapter=chapter,
                    depth=depth,
                    page_start=page_num,
                    page_end=page_num,
                )

            # Accumulate content for current section
            if current_section:
                current_content.append(text)

        # Don't forget the last section
        if current_section and current_content:
            current_section.content = '\n'.join(current_content)
            current_section.page_end = len(self.doc) - 1
            if len(current_section.content.strip()) > 50:
                sections.append(current_section)

        logger.info(f"Parsed {len(sections)} sections from PDF")
        return sections


class Gpt4ConceptExtractor:
    """Extracts concepts from sections using GPT-4."""

    def __init__(self, api_key: str = None):
        self.client = OpenAI(api_key=api_key or settings.openai_api_key)
        self.model = "gpt-4-turbo-preview"
        self.max_retries = 3
        self.stats = ExtractionStats()

    def _get_knowledge_area_name(self, ka_id: str) -> str:
        """Get human-readable KA name from ID."""
        ka_names = {
            "ba-planning": "Business Analysis Planning and Monitoring",
            "elicitation": "Elicitation and Collaboration",
            "rlcm": "Requirements Life Cycle Management",
            "strategy": "Strategy Analysis",
            "radd": "Requirements Analysis and Design Definition",
            "solution-eval": "Solution Evaluation",
        }
        return ka_names.get(ka_id, ka_id)

    def _chunk_content(self, content: str, max_chars: int = 24000) -> List[str]:
        """
        Split large content into chunks that fit context window.

        Args:
            content: Text content to chunk
            max_chars: Maximum characters per chunk (~8k tokens)

        Returns:
            List of content chunks
        """
        if len(content) <= max_chars:
            return [content]

        chunks = []
        paragraphs = content.split('\n\n')
        current_chunk = []
        current_length = 0

        for para in paragraphs:
            if current_length + len(para) > max_chars:
                if current_chunk:
                    chunks.append('\n\n'.join(current_chunk))
                current_chunk = [para]
                current_length = len(para)
            else:
                current_chunk.append(para)
                current_length += len(para)

        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))

        return chunks

    def extract_concepts_from_section(
        self, section: BabokSection
    ) -> List[ConceptCandidate]:
        """
        Extract concepts from a BABOK section using GPT-4.

        Args:
            section: BabokSection to extract concepts from

        Returns:
            List of ConceptCandidate objects
        """
        ka_id = BABOK_KA_CHAPTERS.get(section.chapter)
        if not ka_id:
            logger.warning(f"Unknown chapter {section.chapter}, skipping")
            return []

        ka_name = self._get_knowledge_area_name(ka_id)
        concepts = []

        # Chunk content if needed
        chunks = self._chunk_content(section.content)

        for chunk_idx, chunk in enumerate(chunks):
            prompt = CONCEPT_EXTRACTION_PROMPT.format(
                section_number=section.section_number,
                section_title=section.title,
                knowledge_area=ka_name,
                section_content=chunk,
            )

            for attempt in range(self.max_retries):
                try:
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {
                                "role": "system",
                                "content": "You are an expert in BABOK v3 and business analysis. "
                                "Extract testable concepts from the provided content. "
                                "Output ONLY valid JSON arrays.",
                            },
                            {"role": "user", "content": prompt},
                        ],
                        temperature=0.3,
                        response_format={"type": "json_object"},
                    )

                    self.stats.api_calls += 1
                    if response.usage:
                        self.stats.total_tokens += response.usage.total_tokens

                    # Parse response
                    content = response.choices[0].message.content
                    parsed = json.loads(content)

                    # Handle both direct array and wrapped array
                    if isinstance(parsed, list):
                        raw_concepts = parsed
                    elif isinstance(parsed, dict) and "concepts" in parsed:
                        raw_concepts = parsed["concepts"]
                    else:
                        raw_concepts = list(parsed.values())[0] if parsed else []

                    # Convert to ConceptCandidate objects
                    for raw in raw_concepts:
                        if not raw.get("name"):
                            continue
                        concepts.append(
                            ConceptCandidate(
                                name=raw["name"],
                                description=raw.get("description", ""),
                                corpus_section_ref=section.section_number,
                                knowledge_area_id=ka_id,
                                difficulty_estimate=float(
                                    raw.get("difficulty_estimate", 0.5)
                                ),
                                prerequisite_depth=section.depth - 1,
                            )
                        )

                    break  # Success, exit retry loop

                except json.JSONDecodeError as e:
                    logger.warning(
                        f"JSON parse error for section {section.section_number} "
                        f"(attempt {attempt + 1}): {e}"
                    )
                except Exception as e:
                    # SEC-001: Sanitize error message to prevent API key exposure
                    error_msg = _sanitize_error_message(str(e))
                    logger.warning(
                        f"API error for section {section.section_number} "
                        f"(attempt {attempt + 1}): {error_msg}"
                    )
                    if attempt < self.max_retries - 1:
                        import time
                        time.sleep(2 ** attempt)  # Exponential backoff

        logger.debug(
            f"Extracted {len(concepts)} concepts from section {section.section_number}"
        )
        return concepts


class ConceptDeduplicator:
    """Deduplicates concepts using fuzzy string matching."""

    def __init__(self, similarity_threshold: int = 85):
        """
        Initialize deduplicator.

        Args:
            similarity_threshold: Minimum fuzzy match ratio to consider duplicate
        """
        self.similarity_threshold = similarity_threshold

    def deduplicate_concepts(
        self, concepts: List[ConceptCandidate]
    ) -> List[ConceptCandidate]:
        """
        Remove duplicate concepts using fuzzy string matching.

        Args:
            concepts: List of concept candidates

        Returns:
            Deduplicated list of concepts
        """
        if not concepts:
            return []

        unique_concepts = []
        seen_names = []

        for concept in concepts:
            is_duplicate = False
            name_lower = concept.name.lower()

            for seen_idx, seen_name in enumerate(seen_names):
                ratio = fuzz.ratio(name_lower, seen_name.lower())
                if ratio >= self.similarity_threshold:
                    is_duplicate = True
                    # Keep the one with longer description
                    existing = unique_concepts[seen_idx]
                    if len(concept.description) > len(existing.description):
                        unique_concepts[seen_idx] = concept
                        seen_names[seen_idx] = concept.name
                    logger.debug(
                        f"Duplicate found: '{concept.name}' ~ '{seen_name}' "
                        f"(ratio={ratio})"
                    )
                    break

            if not is_duplicate:
                unique_concepts.append(concept)
                seen_names.append(concept.name)

        duplicates_removed = len(concepts) - len(unique_concepts)
        logger.info(f"Deduplication: {duplicates_removed} duplicates removed")
        return unique_concepts


def estimate_difficulty(section: BabokSection, base_difficulty: float) -> float:
    """
    Estimate concept difficulty based on section characteristics.

    Args:
        section: BabokSection the concept belongs to
        base_difficulty: Initial difficulty from GPT-4

    Returns:
        Normalized difficulty between 0.0 and 1.0
    """
    # Adjust based on section depth
    depth_adjustment = (section.depth - 1) * 0.1  # Deeper = harder

    # Combine and clamp
    final_difficulty = base_difficulty + depth_adjustment
    return max(0.0, min(1.0, round(final_difficulty, 2)))


async def get_cbap_course_id() -> Tuple[UUID, List[Dict[str, Any]]]:
    """
    Get CBAP course ID and knowledge areas from database.

    Returns:
        Tuple of (course_id UUID, knowledge_areas list)

    Raises:
        ValueError: If CBAP course not found
    """
    async with AsyncSessionLocal() as db:
        repo = CourseRepository(db)
        course = await repo.get_by_slug("cbap")

        if not course:
            raise ValueError(
                "CBAP course not found in database. "
                "Ensure Story 2.0 (Courses Table Setup) has been completed."
            )

        return course.id, course.knowledge_areas


def map_ka_name_to_id(ka_name: str, course_knowledge_areas: List[dict]) -> str:
    """
    Map BABOK KA name to course knowledge_area_id.

    Args:
        ka_name: Knowledge area name from BABOK
        course_knowledge_areas: List of KA dicts from course.knowledge_areas

    Returns:
        knowledge_area_id string

    Raises:
        ValueError: If KA name not found
    """
    for ka in course_knowledge_areas:
        if ka["name"] == ka_name:
            return ka["id"]
    raise ValueError(f"Unknown KA: {ka_name}")


def export_concepts_to_csv(
    concepts: List[ConceptCandidate], course_id: UUID, output_path: str
) -> None:
    """
    Export concepts to CSV for SME review.

    Args:
        concepts: List of ConceptCandidate objects
        course_id: CBAP course UUID
        output_path: Path for CSV output file
    """
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Sort by KA then section_ref
    sorted_concepts = sorted(
        concepts, key=lambda c: (c.knowledge_area_id, c.corpus_section_ref)
    )

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "id",
            "course_id",
            "name",
            "description",
            "corpus_section_ref",
            "knowledge_area_id",
            "difficulty_estimate",
            "prerequisite_depth",
        ])

        for idx, concept in enumerate(sorted_concepts, start=1):
            writer.writerow([
                f"concept-{idx:04d}",  # Placeholder ID
                str(course_id),
                concept.name,
                concept.description,
                concept.corpus_section_ref,
                concept.knowledge_area_id,
                concept.difficulty_estimate,
                concept.prerequisite_depth,
            ])

    logger.info(f"Exported {len(concepts)} concepts to {output_path}")
    logger.info("SME Review Process:")
    logger.info("  1. Review the CSV file for concept accuracy")
    logger.info("  2. Check concept names are clear and testable")
    logger.info("  3. Verify difficulty estimates are reasonable")
    logger.info("  4. Flag any concepts that need refinement")


def validate_extraction_results(
    concepts: List[ConceptCandidate], stats: ExtractionStats
) -> Tuple[bool, List[str]]:
    """
    Validate extraction results against acceptance criteria.

    Args:
        concepts: List of extracted concepts
        stats: Extraction statistics

    Returns:
        Tuple of (is_valid, list of warnings/errors)
    """
    issues = []
    is_valid = True

    # AC 4: Check total count (500-1500)
    total = len(concepts)
    if total < 500:
        issues.append(f"ERROR: Total concepts ({total}) below minimum (500)")
        is_valid = False
    elif total > 1500:
        issues.append(f"WARNING: Total concepts ({total}) above target max (1500)")

    # AC 5: Check per-KA counts (75-250)
    ka_counts = {}
    for concept in concepts:
        ka_id = concept.knowledge_area_id
        ka_counts[ka_id] = ka_counts.get(ka_id, 0) + 1

    for ka_id, count in ka_counts.items():
        if count < 75:
            issues.append(f"WARNING: KA '{ka_id}' has only {count} concepts (min: 75)")
        elif count > 250:
            issues.append(f"WARNING: KA '{ka_id}' has {count} concepts (max: 250)")

    stats.concepts_by_ka = ka_counts

    # AC 9: Check section coverage (>= 95%)
    sections_with_concepts = set(c.corpus_section_ref for c in concepts)
    all_sections = set(stats.all_sections)
    sections_without = all_sections - sections_with_concepts

    coverage = (
        len(sections_with_concepts) / len(all_sections) * 100
        if all_sections
        else 0
    )

    if coverage < 95:
        issues.append(
            f"WARNING: Section coverage ({coverage:.1f}%) below 95% threshold"
        )
        stats.sections_without_concepts = list(sections_without)
    else:
        logger.info(f"Section coverage: {coverage:.1f}%")

    return is_valid, issues


def print_summary_report(
    stats: ExtractionStats, concepts: List[ConceptCandidate]
) -> None:
    """Print extraction summary report."""
    logger.info("=" * 60)
    logger.info("EXTRACTION SUMMARY REPORT")
    logger.info("=" * 60)
    logger.info(f"Total sections parsed: {stats.total_sections_parsed}")
    logger.info(f"Total concepts extracted: {stats.total_concepts_extracted}")
    logger.info(f"Concepts after deduplication: {stats.concepts_after_dedup}")
    logger.info(f"API calls made: {stats.api_calls}")
    logger.info(f"Total tokens used: {stats.total_tokens}")
    logger.info("")
    logger.info("Breakdown by Knowledge Area:")
    for ka_id, count in sorted(stats.concepts_by_ka.items()):
        logger.info(f"  - {ka_id}: {count} concepts")
    logger.info("")
    if stats.sections_without_concepts:
        logger.info(f"Sections without concepts ({len(stats.sections_without_concepts)}):")
        for section in stats.sections_without_concepts[:10]:  # Show first 10
            logger.info(f"  - {section}")
        if len(stats.sections_without_concepts) > 10:
            logger.info(f"  ... and {len(stats.sections_without_concepts) - 10} more")
    logger.info("=" * 60)


async def store_concepts_in_db(
    concepts: List[ConceptCandidate], course_id: UUID
) -> int:
    """
    Store concepts in PostgreSQL.

    Args:
        concepts: List of ConceptCandidate objects
        course_id: CBAP course UUID

    Returns:
        Number of concepts stored
    """
    async with AsyncSessionLocal() as db:
        repo = ConceptRepository(db)

        # Convert to ConceptCreate schemas
        concept_creates = [
            ConceptCreate(
                course_id=course_id,
                name=c.name,
                description=c.description,
                corpus_section_ref=c.corpus_section_ref,
                knowledge_area_id=c.knowledge_area_id,
                difficulty_estimate=c.difficulty_estimate,
                prerequisite_depth=c.prerequisite_depth,
            )
            for c in concepts
        ]

        count = await repo.bulk_create(concept_creates)
        await db.commit()

        logger.info(f"Successfully stored {count} concepts in database")
        return count


async def clear_existing_concepts(course_id: UUID) -> int:
    """
    Clear all existing concepts for a course before re-extraction.

    OPS-001: Enables idempotent re-extraction by removing existing concepts.

    Args:
        course_id: Course UUID to clear concepts for

    Returns:
        Number of concepts deleted
    """
    async with AsyncSessionLocal() as db:
        repo = ConceptRepository(db)
        count = await repo.delete_all_for_course(course_id)
        await db.commit()
        return count


async def main(
    pdf_path: str,
    output_csv: Optional[str] = None,
    dry_run: bool = False,
    skip_validation: bool = False,
    clear_existing: bool = False,
) -> int:
    """
    Main extraction orchestrator.

    Args:
        pdf_path: Path to BABOK v3 PDF
        output_csv: Optional path for CSV export
        dry_run: If True, skip database insert
        skip_validation: If True, skip validation checks
        clear_existing: If True, delete existing concepts before insert (idempotent)

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    stats = ExtractionStats()

    # Step 1: Lookup CBAP course_id
    logger.info("Step 1: Looking up CBAP course...")
    try:
        course_id, knowledge_areas = await get_cbap_course_id()
        logger.info(f"Found CBAP course: {course_id}")
    except ValueError as e:
        logger.error(str(e))
        return 1

    # Step 1.5: Clear existing concepts if requested (OPS-001 idempotency)
    if clear_existing and not dry_run:
        logger.info("Step 1.5: Clearing existing concepts for idempotent re-extraction...")
        deleted_count = await clear_existing_concepts(course_id)
        logger.info(f"Deleted {deleted_count} existing concepts")

    # Step 2: Parse BABOK PDF
    logger.info("Step 2: Parsing BABOK PDF...")
    parser = BabokPdfParser(pdf_path)
    try:
        parser.open()
        sections = parser.parse_babok_pdf()
        stats.total_sections_parsed = len(sections)
        stats.all_sections = [s.section_number for s in sections]
    except FileNotFoundError:
        logger.error(f"PDF file not found: {pdf_path}")
        return 1
    except Exception as e:
        logger.error(f"Failed to parse PDF: {e}")
        return 1
    finally:
        parser.close()

    if not sections:
        logger.error("No sections found in PDF")
        return 1

    # Step 3: Extract concepts from each section via GPT-4
    logger.info("Step 3: Extracting concepts via GPT-4...")
    extractor = Gpt4ConceptExtractor()
    all_concepts = []

    for idx, section in enumerate(sections, start=1):
        logger.info(
            f"Processing section {idx}/{len(sections)}: {section.section_number} {section.title}"
        )
        concepts = extractor.extract_concepts_from_section(section)
        all_concepts.extend(concepts)

    stats.total_concepts_extracted = len(all_concepts)
    stats.api_calls = extractor.stats.api_calls
    stats.total_tokens = extractor.stats.total_tokens

    logger.info(f"Extracted {len(all_concepts)} raw concepts")

    # Step 4: Deduplicate concepts
    logger.info("Step 4: Deduplicating concepts...")
    deduplicator = ConceptDeduplicator()
    unique_concepts = deduplicator.deduplicate_concepts(all_concepts)
    stats.concepts_after_dedup = len(unique_concepts)

    # Step 5: Apply difficulty adjustments
    logger.info("Step 5: Adjusting difficulty estimates...")
    section_map = {s.section_number: s for s in sections}
    for concept in unique_concepts:
        section = section_map.get(concept.corpus_section_ref)
        if section:
            concept.difficulty_estimate = estimate_difficulty(
                section, concept.difficulty_estimate
            )

    # Step 6: Validate results
    if not skip_validation:
        logger.info("Step 6: Validating extraction results...")
        is_valid, issues = validate_extraction_results(unique_concepts, stats)

        for issue in issues:
            if issue.startswith("ERROR"):
                logger.error(issue)
            else:
                logger.warning(issue)

        if not is_valid:
            logger.error("Validation failed. Fix issues before proceeding.")
            return 1

    # Step 7: Export to CSV for review
    csv_path = output_csv or "scripts/output/concepts_export.csv"
    logger.info(f"Step 7: Exporting to CSV: {csv_path}")
    export_concepts_to_csv(unique_concepts, course_id, csv_path)

    # Step 8: Store in PostgreSQL
    if not dry_run:
        logger.info("Step 8: Storing concepts in PostgreSQL...")
        try:
            await store_concepts_in_db(unique_concepts, course_id)
        except Exception as e:
            logger.error(f"Database insert failed: {e}")
            return 1
    else:
        logger.info("Step 8: DRY RUN - Skipping database insert")

    # Step 9: Print summary report
    print_summary_report(stats, unique_concepts)

    return 0


def cli_main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Extract BABOK v3 concepts and store in PostgreSQL"
    )
    parser.add_argument(
        "--pdf-path",
        required=True,
        help="Path to BABOK v3 PDF file",
    )
    parser.add_argument(
        "--output-csv",
        help="Path for CSV export (default: scripts/output/concepts_export.csv)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip database insert (for testing)",
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip validation checks",
    )
    parser.add_argument(
        "--clear-existing",
        action="store_true",
        help="Delete existing concepts for CBAP course before inserting (idempotent re-extraction)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    exit_code = asyncio.run(
        main(
            pdf_path=args.pdf_path,
            output_csv=args.output_csv,
            dry_run=args.dry_run,
            skip_validation=args.skip_validation,
            clear_existing=args.clear_existing,
        )
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    cli_main()
