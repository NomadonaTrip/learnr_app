"""
Import vendor questions with concept mapping for multi-course architecture.

This script:
1. Looks up course by slug from the database
2. Parses questions from CSV/JSON
3. Maps vendor KA names to course knowledge_area_id values
4. Maps questions to concepts using one of two methods:
   a. GPT-4 semantic mapping (default) - generates embeddings and uses AI
   b. CSV tag matching (--use-csv-tags) - uses pre-tagged concept_tags column
5. Validates and inserts questions with concept mappings
6. Exports mappings and reports for SME review

USAGE:
------
# Standard GPT-4 semantic mapping (existing behavior):
python scripts/import_vendor_questions.py \\
    --course-slug cbap \\
    --input-file data/questions.csv

# Use pre-tagged concepts from CSV (new in Story 2.13):
python scripts/import_vendor_questions.py \\
    --course-slug cbap \\
    --input-file data/questions.csv \\
    --use-csv-tags \\
    --tag-match-threshold 85

# Create new concepts for unmatched tags:
python scripts/import_vendor_questions.py \\
    --course-slug cbap \\
    --input-file data/questions.csv \\
    --use-csv-tags \\
    --create-missing-concepts \\
    --unmatched-report output/unmatched.csv \\
    --created-concepts-report output/created.csv

CSV FORMAT:
-----------
Required columns: question_text, option_a/b/c/d, correct_answer, explanation, ka
Optional columns: concept_tags, difficulty, source, corpus_reference

concept_tags column supports two delimiter styles:
- Comma-separated: "stakeholder,analysis,planning"
- Semicolon-separated: "BA-Planning;Stakeholder-Engagement;Adaptability;"

CLI OPTIONS:
------------
--use-csv-tags           Use concept_tags column instead of GPT-4 mapping
--tag-match-threshold    Fuzzy match threshold 50-100 (default: 85)
--create-missing-concepts Create new concepts for unmatched tags
--unmatched-report       Export unmatched tags to CSV for review
--created-concepts-report Export created concepts to CSV for review
"""
import argparse
import asyncio
import csv
import json
import logging
import os
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from openai import AsyncOpenAI, APIError, RateLimitError, APIConnectionError
from thefuzz import fuzz
from qdrant_client import AsyncQdrantClient
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from qdrant_client.models import Distance, Filter, FieldCondition, MatchValue, VectorParams

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "apps" / "api"))

from src.db.session import AsyncSessionLocal
from src.models.concept import Concept
from src.models.course import Course
from src.repositories.concept_repository import ConceptRepository
from src.repositories.question_repository import QuestionRepository
from src.schemas.concept import ConceptCreate

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# =====================================
# Constants
# =====================================

# Knowledge area name to ID mapping for CBAP (loaded dynamically from course)
DEFAULT_KA_MAPPINGS = {
    "business analysis planning and monitoring": "ba-planning",
    "ba planning and monitoring": "ba-planning",
    "ba planning": "ba-planning",
    "planning and monitoring": "ba-planning",
    "elicitation and collaboration": "elicitation",
    "elicitation": "elicitation",
    "requirements life cycle management": "rlcm",
    "requirements lifecycle management": "rlcm",
    "rlcm": "rlcm",
    "strategy analysis": "strategy",
    "strategy": "strategy",
    "requirements analysis and design definition": "radd",
    "requirements analysis": "radd",
    "radd": "radd",
    "solution evaluation": "solution-eval",
    "solution eval": "solution-eval",
}

# Difficulty string to IRT b-parameter mapping (-3.0 to +3.0)
DIFFICULTY_MAP = {
    "easy": -1.5,
    "medium": 0.0,
    "hard": 1.5,
}

# IRT difficulty tier boundaries
DIFFICULTY_TIERS = {
    "easy": (-3.0, -1.0),
    "medium": (-1.0, 1.0),
    "hard": (1.0, 3.0),
}


def classify_difficulty_label(difficulty: float) -> str:
    """Classify IRT b-parameter into human-readable label."""
    if difficulty < -1.0:
        return "Easy"
    elif difficulty <= 1.0:
        return "Medium"
    else:
        return "Hard"

# GPT-4 prompt for concept selection
CONCEPT_SELECTION_PROMPT = """You are mapping certification exam questions to course concepts.

Question:
{question_text}

Options:
A: {option_a}
B: {option_b}
C: {option_c}
D: {option_d}

Correct Answer: {correct_answer}
Explanation: {explanation}

Candidate Concepts (from semantic search):
{candidates}

Select 1-5 concepts that this question DIRECTLY tests. For each selected concept, assign a relevance score:
- 1.0: Question directly tests this concept (primary focus)
- 0.7-0.9: Question significantly involves this concept
- 0.5-0.6: Question indirectly relates to this concept

Output as JSON array:
[
  {{
    "concept_id": "uuid",
    "concept_name": "name",
    "relevance": 0.9,
    "reasoning": "Brief explanation of why this concept is tested"
  }}
]

Rules:
- Select at least 1 concept, maximum 5
- Only select concepts the question genuinely tests
- Higher relevance = more directly tested
- Consider both the question and the correct answer
"""


@dataclass
class QuestionData:
    """Parsed question data structure."""
    question_text: str
    options: Dict[str, str]
    correct_answer: str
    explanation: str
    knowledge_area_name: str
    knowledge_area_id: Optional[str] = None
    difficulty: float = 0.0  # IRT b-parameter (-3.0 to +3.0)
    difficulty_label: Optional[str] = None  # Human-readable: Easy/Medium/Hard
    # IRT parameters
    discrimination: float = 1.0  # IRT a-parameter (0.0 to 5.0)
    guess_rate: float = 0.25  # P(correct | not mastered)
    slip_rate: float = 0.10  # P(incorrect | mastered)
    source: str = "vendor"
    corpus_reference: Optional[str] = None
    row_number: int = 0
    concept_tags: List[str] = field(default_factory=list)
    # Story 2.15: Secondary tags for filtering/analysis
    perspectives: List[str] = field(default_factory=list)
    competencies: List[str] = field(default_factory=list)


@dataclass
class ConceptMapping:
    """Concept mapping result."""
    concept_id: UUID
    concept_name: str
    relevance: float
    reasoning: str


@dataclass
class ImportResult:
    """Import operation result."""
    questions_parsed: int = 0
    questions_valid: int = 0
    questions_inserted: int = 0
    questions_skipped: int = 0
    mappings_created: int = 0
    errors: List[str] = None
    warnings: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


class ConceptTagMatcher:
    """
    Matches CSV concept tags to existing concepts using fuzzy string matching.

    Relevance scoring:
    - Exact match (100%): relevance = 1.0
    - High match (95-99%): relevance = 0.9
    - Good match (85-94%): relevance = 0.8
    """

    def __init__(self, concepts: List[Concept], threshold: int = 85):
        """
        Initialize the matcher with concepts and threshold.

        Args:
            concepts: List of Concept models to match against
            threshold: Minimum fuzzy match score (0-100) for a valid match
        """
        self.concepts = concepts
        self.threshold = threshold
        # Build lookup dict for O(1) exact match (case-insensitive)
        self.concept_by_name: Dict[str, Concept] = {
            c.name.lower(): c for c in concepts
        }

    def match_tag(self, tag: str) -> Optional[Tuple[Concept, float, float]]:
        """
        Match a tag to the best concept.

        Args:
            tag: The concept tag string to match

        Returns:
            Tuple of (concept, match_score, relevance) or None if no match found
            - match_score: 0-100 indicating match quality
            - relevance: 0.0-1.0 relevance score for question-concept mapping
        """
        normalized = tag.lower().strip()

        # Try exact match first (O(1) lookup)
        if normalized in self.concept_by_name:
            return (self.concept_by_name[normalized], 100.0, 1.0)

        # Fuzzy match against all concepts
        best_match: Optional[Concept] = None
        best_score: float = 0.0

        for name, concept in self.concept_by_name.items():
            score = fuzz.ratio(normalized, name)
            if score > best_score and score >= self.threshold:
                best_match = concept
                best_score = score

        if best_match:
            # Calculate relevance based on match score
            if best_score >= 95:
                relevance = 0.9
            else:  # 85-94
                relevance = 0.8
            return (best_match, best_score, relevance)

        return None

    def match_tags(self, tags: List[str]) -> List[Tuple[str, Optional[Tuple[Concept, float, float]]]]:
        """
        Match multiple tags and return results for each.

        Args:
            tags: List of tag strings to match

        Returns:
            List of tuples (tag, match_result) where match_result is
            (concept, score, relevance) or None
        """
        return [(tag, self.match_tag(tag)) for tag in tags]


class TagClassifier:
    """
    Classifies tags into concepts, competencies, or perspectives based on course config.

    Story 2.15: Secondary Tagging for Perspectives and Underlying Competencies.
    Keywords are loaded from course.perspectives and course.competencies JSONB.
    """

    def __init__(self, course: Course):
        """
        Initialize with course configuration.

        Args:
            course: Course model with perspectives and competencies JSONB
        """
        self.competency_keywords: set[str] = set()
        self.perspective_keywords: set[str] = set()
        self.competency_id_map: Dict[str, str] = {}  # keyword -> competency id
        self.perspective_id_map: Dict[str, str] = {}  # keyword -> perspective id

        # Build keyword sets from course JSONB
        if course.competencies:
            for comp in course.competencies:
                comp_id = comp.get("id", "")
                for kw in comp.get("keywords", []):
                    kw_lower = kw.lower()
                    self.competency_keywords.add(kw_lower)
                    self.competency_id_map[kw_lower] = comp_id

        if course.perspectives:
            for persp in course.perspectives:
                persp_id = persp.get("id", "")
                for kw in persp.get("keywords", []):
                    kw_lower = kw.lower()
                    self.perspective_keywords.add(kw_lower)
                    self.perspective_id_map[kw_lower] = persp_id

        logger.debug(
            f"TagClassifier initialized with {len(self.competency_keywords)} competency keywords, "
            f"{len(self.perspective_keywords)} perspective keywords"
        )

    def classify_tag(self, tag: str) -> Tuple[str, str, Optional[str]]:
        """
        Classify a tag as concept, competency, or perspective.

        Args:
            tag: The tag string to classify

        Returns:
            Tuple of (category, normalized_tag, id) where:
            - category: "concept", "competency", or "perspective"
            - normalized_tag: lowercase, hyphenated, stripped
            - id: The competency/perspective ID if matched, None for concepts
        """
        normalized = tag.lower().replace("_", "-").strip()

        # Check for competency keyword match (partial matching)
        for kw in self.competency_keywords:
            if kw in normalized:
                comp_id = self.competency_id_map.get(kw)
                return ("competency", normalized, comp_id)

        # Check for perspective keyword match (partial matching)
        for kw in self.perspective_keywords:
            if kw in normalized:
                persp_id = self.perspective_id_map.get(kw)
                return ("perspective", normalized, persp_id)

        # Not a secondary tag - it's a concept
        return ("concept", tag, None)  # Keep original for concept matching

    def classify_tags(self, tags: List[str]) -> Dict[str, List[str]]:
        """
        Classify multiple tags and return them grouped by category.

        Args:
            tags: List of tag strings to classify

        Returns:
            Dict with keys "concepts", "competencies", "perspectives"
            containing lists of classified tags/IDs
        """
        result = {
            "concepts": [],
            "competencies": [],
            "perspectives": [],
        }
        seen_competencies = set()
        seen_perspectives = set()

        for tag in tags:
            category, normalized, tag_id = self.classify_tag(tag)

            if category == "competency" and tag_id:
                if tag_id not in seen_competencies:
                    result["competencies"].append(tag_id)
                    seen_competencies.add(tag_id)
            elif category == "perspective" and tag_id:
                if tag_id not in seen_perspectives:
                    result["perspectives"].append(tag_id)
                    seen_perspectives.add(tag_id)
            else:
                result["concepts"].append(tag)  # Keep original tag for concept matching

        return result


class KAMapper:
    """
    Maps non-conventional KA values to primary KAs for BKT scoring.

    Story 2.16: Non-Conventional KA Mapping for Import

    Handles two types of non-conventional KAs:
    1. Perspectives (BABOK Chapter 10): e.g., "Agile Perspective" -> "strategy"
    2. Underlying Competencies (BABOK Chapter 9): infers KA from concept_tags
    """

    # Competency tag inference keywords (AC 8-13)
    ELICITATION_KEYWORDS = {
        'elicitation', 'interview', 'workshop', 'collaboration',
        'communication', 'facilitation', 'listening'
    }
    STRATEGY_KEYWORDS = {
        'strategy', 'conceptual', 'systems-thinking', 'business-acumen',
        'industry', 'organization', 'vision'
    }
    RLCM_KEYWORDS = {
        'decision', 'prioritiz', 'approval', 'traceability', 'change',
        'governance', 'baseline'
    }
    RADD_KEYWORDS = {
        'model', 'design', 'data', 'analysis', 'specification',
        'diagram', 'prototype'
    }
    SOLUTION_EVAL_KEYWORDS = {
        'evaluation', 'metric', 'performance', 'assessment',
        'measure', 'kpi'
    }

    def __init__(self, course: Course):
        """
        Load perspective-to-KA mappings from course config.

        Args:
            course: Course model with perspectives JSONB containing primary_ka
        """
        self.perspective_to_ka: Dict[str, str] = {}  # persp_id -> primary_ka
        self.perspective_name_to_id: Dict[str, str] = {}  # normalized name -> persp_id

        if course.perspectives:
            for persp in course.perspectives:
                persp_id = persp.get("id", "")
                primary_ka = persp.get("primary_ka", "ba-planning")
                name = persp.get("name", "").lower().strip()

                self.perspective_to_ka[persp_id] = primary_ka

                # AC 14-16: Case-insensitive, partial matches, whitespace normalized
                # Register multiple variants for flexible matching
                self.perspective_name_to_id[name] = persp_id                    # "agile"
                self.perspective_name_to_id[f"{name} perspective"] = persp_id   # "agile perspective"
                self.perspective_name_to_id[persp_id] = persp_id                # "agile" (by id)

        logger.debug(
            f"KAMapper initialized with {len(self.perspective_to_ka)} perspective mappings"
        )

    def is_non_conventional_ka(self, ka_name: str) -> bool:
        """
        Check if KA is a perspective or competency category.

        AC 14-16: Case-insensitive, whitespace normalized

        Args:
            ka_name: The KA value from CSV

        Returns:
            True if this is a non-conventional KA (perspective or "Underlying Competencies")
        """
        normalized = ka_name.lower().strip()

        # Check for "Underlying Competencies"
        if normalized == "underlying competencies":
            return True

        # Check against all registered perspective name variants
        return normalized in self.perspective_name_to_id

    def infer_ka_from_tags(self, tags: List[str]) -> str:
        """
        Infer primary KA from concept tags for competency questions.

        AC 8-13: Keyword-based inference rules

        Args:
            tags: List of concept tag strings

        Returns:
            Primary KA ID (defaults to "ba-planning" if no match)
        """
        tag_text = " ".join(t.lower() for t in tags)

        if any(kw in tag_text for kw in self.ELICITATION_KEYWORDS):
            return "elicitation"
        if any(kw in tag_text for kw in self.STRATEGY_KEYWORDS):
            return "strategy"
        if any(kw in tag_text for kw in self.RLCM_KEYWORDS):
            return "rlcm"
        if any(kw in tag_text for kw in self.RADD_KEYWORDS):
            return "radd"
        if any(kw in tag_text for kw in self.SOLUTION_EVAL_KEYWORDS):
            return "solution-eval"

        return "ba-planning"  # Default fallback (AC 13)

    def map_ka(
        self, ka_name: str, concept_tags: List[str]
    ) -> Tuple[str, Optional[str]]:
        """
        Map non-conventional KA to primary KA.

        Args:
            ka_name: The KA value from CSV (e.g., "Agile Perspective", "Underlying Competencies")
            concept_tags: List of concept tags for KA inference

        Returns:
            Tuple of (primary_ka_id, perspective_id or None)
            - For perspectives: (mapped_ka, perspective_id)
            - For competencies: (inferred_ka, None)  # competency IDs come from TagClassifier
        """
        # AC 14-16: Case-insensitive, whitespace normalized
        normalized = ka_name.lower().strip()

        # Handle "Underlying Competencies" - infer KA from tags
        if normalized == "underlying competencies":
            inferred_ka = self.infer_ka_from_tags(concept_tags)
            logger.debug(
                f"Inferred KA '{inferred_ka}' from tags for 'Underlying Competencies'"
            )
            return (inferred_ka, None)

        # AC 15: Handle perspective KAs - supports partial matches
        if normalized in self.perspective_name_to_id:
            persp_id = self.perspective_name_to_id[normalized]
            primary_ka = self.perspective_to_ka.get(persp_id, "ba-planning")
            logger.debug(
                f"Mapped perspective '{ka_name}' -> KA '{primary_ka}', perspective_id '{persp_id}'"
            )
            return (primary_ka, persp_id)

        # AC 17: Fallback for unknown non-conventional KA
        logger.warning(
            f"Unknown non-conventional KA: '{ka_name}', defaulting to 'ba-planning'"
        )
        return ("ba-planning", None)


class VendorQuestionImporter:
    """
    Orchestrates the vendor question import process with concept mapping.
    """

    def __init__(
        self,
        course_slug: str,
        dry_run: bool = False,
        skip_concept_mapping: bool = False,
        batch_size: int = 50,
        use_csv_tags: bool = False,
        tag_match_threshold: int = 85,
        create_missing_concepts: bool = False,
    ):
        self.course_slug = course_slug
        self.dry_run = dry_run
        self.skip_concept_mapping = skip_concept_mapping
        self.batch_size = batch_size
        self.use_csv_tags = use_csv_tags
        self.tag_match_threshold = tag_match_threshold
        self.create_missing_concepts = create_missing_concepts

        self.course: Optional[Course] = None
        self.course_id: Optional[UUID] = None
        self.ka_name_to_id: Dict[str, str] = {}
        self.concepts: List[Concept] = []
        self.concept_embeddings: Dict[UUID, List[float]] = {}

        self.openai_client: Optional[AsyncOpenAI] = None
        self.qdrant_client: Optional[AsyncQdrantClient] = None

        # Track created concepts and unmatched tags for reporting
        self.created_concepts: List[Tuple[Concept, str]] = []  # (concept, source_tag)
        self.unmatched_tags: List[Tuple[int, str, str]] = []  # (row_number, tag, question_preview)

        # Story 2.15: Tag classifier for secondary tags
        self.tag_classifier: Optional[TagClassifier] = None

        # Story 2.16: KA mapper for non-conventional KAs
        self.ka_mapper: Optional[KAMapper] = None

        self.result = ImportResult()

    async def initialize(self) -> bool:
        """Initialize connections and load course data."""
        try:
            # Initialize OpenAI client
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                logger.error("OPENAI_API_KEY environment variable not set")
                return False
            self.openai_client = AsyncOpenAI(api_key=api_key)

            # Initialize Qdrant client
            qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
            self.qdrant_client = AsyncQdrantClient(url=qdrant_url)

            # Load course from database
            async with AsyncSessionLocal() as db:
                from sqlalchemy import select
                result = await db.execute(
                    select(Course).where(Course.slug == self.course_slug)
                )
                self.course = result.scalar_one_or_none()

                if not self.course:
                    logger.error(f"Course not found: {self.course_slug}")
                    return False

                self.course_id = self.course.id
                logger.info(f"Loaded course: {self.course.name} (ID: {self.course_id})")

                # Build KA name to ID mapping from course
                self._build_ka_mapping()

                # Story 2.15: Initialize tag classifier for secondary tags
                self.tag_classifier = TagClassifier(self.course)

                # Story 2.16: Initialize KA mapper for non-conventional KAs
                self.ka_mapper = KAMapper(self.course)

                # Load concepts for the course
                concept_repo = ConceptRepository(db)
                self.concepts = await concept_repo.get_all_concepts(self.course_id)
                logger.info(f"Loaded {len(self.concepts)} concepts for course")

            return True

        except Exception as e:
            logger.error(f"Failed to initialize: {e}")
            return False

    def _build_ka_mapping(self):
        """Build KA name to ID mapping from course knowledge_areas."""
        if not self.course or not self.course.knowledge_areas:
            return

        # Add mappings from course JSONB
        for ka in self.course.knowledge_areas:
            ka_id = ka.get("id", "")
            ka_name = ka.get("name", "").lower()
            short_name = ka.get("short_name", "").lower()

            if ka_name:
                self.ka_name_to_id[ka_name] = ka_id
            if short_name:
                self.ka_name_to_id[short_name] = ka_id

        # Add default mappings for flexibility
        self.ka_name_to_id.update(DEFAULT_KA_MAPPINGS)

        logger.info(f"Built KA mapping with {len(self.ka_name_to_id)} entries")

    def map_ka_name_to_id(self, ka_name: str) -> Optional[str]:
        """Map a knowledge area name to its ID."""
        normalized = ka_name.lower().strip()
        return self.ka_name_to_id.get(normalized)

    # =====================================
    # File Parsing
    # =====================================

    def parse_csv(self, file_path: str) -> List[QuestionData]:
        """Parse questions from CSV file."""
        questions = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is 1)
                    try:
                        question = self._parse_csv_row(row, row_num)
                        if question:
                            questions.append(question)
                    except Exception as e:
                        self.result.errors.append(f"Row {row_num}: {str(e)}")

            logger.info(f"Parsed {len(questions)} questions from CSV")
        except Exception as e:
            logger.error(f"Failed to parse CSV: {e}")
            raise

        return questions

    def _parse_csv_row(self, row: Dict[str, str], row_num: int) -> Optional[QuestionData]:
        """Parse a single CSV row into QuestionData."""
        # Required fields
        question_text = row.get("question_text", "").strip()
        if not question_text:
            self.result.errors.append(f"Row {row_num}: Missing question_text")
            return None

        # Options - support both formats
        options = {}
        if "options" in row and row["options"]:
            try:
                options = json.loads(row["options"])
            except json.JSONDecodeError:
                pass

        if not options:
            options = {
                "A": row.get("option_a", "").strip(),
                "B": row.get("option_b", "").strip(),
                "C": row.get("option_c", "").strip(),
                "D": row.get("option_d", "").strip(),
            }

        # Validate options
        for key in ["A", "B", "C", "D"]:
            if not options.get(key):
                self.result.errors.append(f"Row {row_num}: Missing option {key}")
                return None

        # Correct answer
        correct_answer = row.get("correct_answer", "").strip().upper()
        if correct_answer not in ["A", "B", "C", "D"]:
            self.result.errors.append(f"Row {row_num}: Invalid correct_answer '{correct_answer}'")
            return None

        # Explanation
        explanation = row.get("explanation", "").strip()
        if not explanation:
            self.result.errors.append(f"Row {row_num}: Missing explanation")
            return None

        # Knowledge area
        ka_name = row.get("knowledge_area", row.get("ka", "")).strip()
        if not ka_name:
            self.result.errors.append(f"Row {row_num}: Missing knowledge_area")
            return None

        # Parse concept_tags column FIRST (needed for non-conventional KA inference)
        # Supports both , and ; delimiters
        concept_tags = []
        perspectives = []
        competencies = []
        raw_tags = []
        tags_raw = row.get("concept_tags", "").strip()
        if tags_raw:
            # Normalize: replace ; with , then split
            raw_tags = [t.strip() for t in tags_raw.replace(";", ",").split(",") if t.strip()]

        # Story 2.16: Check for non-conventional KA (perspectives or competencies)
        ka_id = None
        if self.ka_mapper and self.ka_mapper.is_non_conventional_ka(ka_name):
            # Map non-conventional KA to primary KA
            ka_id, perspective_id = self.ka_mapper.map_ka(ka_name, raw_tags)

            # Add perspective from KA column if applicable
            if perspective_id:
                perspectives.append(perspective_id)

            # For "Underlying Competencies", warn if no tags to extract competency IDs
            if ka_name.lower().strip() == "underlying competencies" and not raw_tags:
                self.result.warnings.append(
                    f"Row {row_num}: 'Underlying Competencies' KA but no concept_tags "
                    "to extract competency IDs"
                )

            logger.info(
                f"Row {row_num}: Mapped non-conventional KA '{ka_name}' -> '{ka_id}'"
            )
        else:
            # Standard KA mapping
            ka_id = self.map_ka_name_to_id(ka_name)
            if not ka_id:
                self.result.warnings.append(f"Row {row_num}: Unknown KA '{ka_name}', skipping")
                return None

        # Story 2.15: Classify tags using course-configurable keywords
        if self.tag_classifier and raw_tags:
            classified = self.tag_classifier.classify_tags(raw_tags)
            concept_tags = classified["concepts"]
            # Extend (not replace) perspectives/competencies to include those from KA mapping
            perspectives.extend(classified["perspectives"])
            competencies.extend(classified["competencies"])

            # Deduplicate while preserving order
            perspectives = list(dict.fromkeys(perspectives))
            competencies = list(dict.fromkeys(competencies))

            logger.debug(
                f"Row {row_num}: Classified {len(raw_tags)} tags -> "
                f"{len(concept_tags)} concepts, {len(perspectives)} perspectives, "
                f"{len(competencies)} competencies"
            )
        elif raw_tags:
            # Fallback if tag_classifier not initialized (shouldn't happen)
            concept_tags = raw_tags
            logger.debug(f"Row {row_num}: Parsed {len(raw_tags)} concept tags (no classifier)")

        # Difficulty - support multiple column formats
        # Priority: difficulty_b (numeric IRT) > difficulty/difficulty_label (string)
        difficulty = 0.0  # Default: medium difficulty
        difficulty_label = None

        # Check for explicit IRT b-parameter (new format)
        if row.get("difficulty_b"):
            try:
                difficulty = float(row.get("difficulty_b"))
                difficulty = max(-3.0, min(3.0, difficulty))
                difficulty_label = classify_difficulty_label(difficulty)
            except ValueError:
                pass
        else:
            # Fall back to difficulty/difficulty_label column (legacy or label format)
            difficulty_str = row.get("difficulty", row.get("difficulty_label", "Medium")).strip().lower()
            if difficulty_str in DIFFICULTY_MAP:
                difficulty = DIFFICULTY_MAP[difficulty_str]
                difficulty_label = difficulty_str.capitalize()
            else:
                try:
                    # Support numeric values (assume IRT scale if in valid range)
                    difficulty = float(difficulty_str)
                    if -3.0 <= difficulty <= 3.0:
                        difficulty_label = classify_difficulty_label(difficulty)
                    else:
                        # Legacy 0-1 scale detected, convert to IRT
                        difficulty = (difficulty - 0.5) * 6
                        difficulty = max(-3.0, min(3.0, difficulty))
                        difficulty_label = classify_difficulty_label(difficulty)
                except ValueError:
                    difficulty = 0.0
                    difficulty_label = "Medium"

        # IRT parameters (with defaults)
        discrimination = 1.0
        guess_rate = 0.25
        slip_rate = 0.10

        if row.get("discrimination"):
            try:
                discrimination = float(row.get("discrimination"))
                discrimination = max(0.0, min(5.0, discrimination))
            except ValueError:
                pass

        if row.get("guess_rate"):
            try:
                guess_rate = float(row.get("guess_rate"))
                guess_rate = max(0.0, min(1.0, guess_rate))
            except ValueError:
                pass

        if row.get("slip_rate"):
            try:
                slip_rate = float(row.get("slip_rate"))
                slip_rate = max(0.0, min(1.0, slip_rate))
            except ValueError:
                pass

        return QuestionData(
            question_text=question_text,
            options=options,
            correct_answer=correct_answer,
            explanation=explanation,
            knowledge_area_name=ka_name,
            knowledge_area_id=ka_id,
            difficulty=difficulty,
            difficulty_label=difficulty_label,
            discrimination=discrimination,
            guess_rate=guess_rate,
            slip_rate=slip_rate,
            source=row.get("source", "vendor"),
            corpus_reference=row.get("corpus_reference", row.get("babok_reference")),
            row_number=row_num,
            concept_tags=concept_tags,
            perspectives=perspectives,
            competencies=competencies,
        )

    def parse_json(self, file_path: str) -> List[QuestionData]:
        """Parse questions from JSON file."""
        questions = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, list):
                data = [data]

            for idx, item in enumerate(data, start=1):
                try:
                    question = self._parse_json_item(item, idx)
                    if question:
                        questions.append(question)
                except Exception as e:
                    self.result.errors.append(f"Item {idx}: {str(e)}")

            logger.info(f"Parsed {len(questions)} questions from JSON")
        except Exception as e:
            logger.error(f"Failed to parse JSON: {e}")
            raise

        return questions

    def _parse_json_item(self, item: Dict[str, Any], idx: int) -> Optional[QuestionData]:
        """Parse a single JSON item into QuestionData."""
        question_text = item.get("question_text", "").strip()
        if not question_text:
            self.result.errors.append(f"Item {idx}: Missing question_text")
            return None

        # Options - support both JSONB format and separate fields
        options = item.get("options")
        if not options or not isinstance(options, dict):
            options = {
                "A": item.get("option_a", ""),
                "B": item.get("option_b", ""),
                "C": item.get("option_c", ""),
                "D": item.get("option_d", ""),
            }

        for key in ["A", "B", "C", "D"]:
            if not options.get(key):
                self.result.errors.append(f"Item {idx}: Missing option {key}")
                return None

        correct_answer = item.get("correct_answer", "").strip().upper()
        if correct_answer not in ["A", "B", "C", "D"]:
            self.result.errors.append(f"Item {idx}: Invalid correct_answer")
            return None

        explanation = item.get("explanation", "").strip()
        if not explanation:
            self.result.errors.append(f"Item {idx}: Missing explanation")
            return None

        ka_name = item.get("knowledge_area", item.get("ka", "")).strip()
        ka_id = self.map_ka_name_to_id(ka_name)
        if not ka_id:
            self.result.warnings.append(f"Item {idx}: Unknown KA '{ka_name}'")
            return None

        # Difficulty - support IRT b-parameter and legacy formats
        difficulty = 0.0  # Default: medium difficulty
        difficulty_label = None

        # Check for explicit IRT b-parameter
        if "difficulty_b" in item:
            try:
                difficulty = float(item.get("difficulty_b"))
                difficulty = max(-3.0, min(3.0, difficulty))
                difficulty_label = classify_difficulty_label(difficulty)
            except (ValueError, TypeError):
                pass
        else:
            raw_difficulty = item.get("difficulty", 0.0)
            if isinstance(raw_difficulty, str):
                raw_difficulty = raw_difficulty.lower()
                if raw_difficulty in DIFFICULTY_MAP:
                    difficulty = DIFFICULTY_MAP[raw_difficulty]
                    difficulty_label = raw_difficulty.capitalize()
                else:
                    try:
                        difficulty = float(raw_difficulty)
                        difficulty = max(-3.0, min(3.0, difficulty))
                        difficulty_label = classify_difficulty_label(difficulty)
                    except ValueError:
                        difficulty = 0.0
                        difficulty_label = "Medium"
            else:
                try:
                    difficulty = float(raw_difficulty)
                    # Detect legacy 0-1 scale and convert
                    if 0.0 <= difficulty <= 1.0 and difficulty not in (-1.5, 0.0, 1.5):
                        difficulty = (difficulty - 0.5) * 6
                    difficulty = max(-3.0, min(3.0, difficulty))
                    difficulty_label = classify_difficulty_label(difficulty)
                except (ValueError, TypeError):
                    difficulty = 0.0
                    difficulty_label = "Medium"

        # IRT parameters
        discrimination = float(item.get("discrimination", 1.0))
        guess_rate = float(item.get("guess_rate", 0.25))
        slip_rate = float(item.get("slip_rate", 0.10))

        return QuestionData(
            question_text=question_text,
            options=options,
            correct_answer=correct_answer,
            explanation=explanation,
            knowledge_area_name=ka_name,
            knowledge_area_id=ka_id,
            difficulty=difficulty,
            difficulty_label=difficulty_label,
            discrimination=discrimination,
            guess_rate=guess_rate,
            slip_rate=slip_rate,
            source=item.get("source", "vendor"),
            corpus_reference=item.get("corpus_reference", item.get("babok_reference")),
            row_number=idx,
        )

    def parse_file(self, file_path: str, file_format: Optional[str] = None) -> List[QuestionData]:
        """Parse questions from file (auto-detect format if not specified)."""
        if not file_format:
            ext = Path(file_path).suffix.lower()
            file_format = "json" if ext == ".json" else "csv"

        if file_format == "json":
            return self.parse_json(file_path)
        return self.parse_csv(file_path)

    # =====================================
    # Embedding Generation
    # =====================================

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        retry=retry_if_exception_type((APIError, RateLimitError, APIConnectionError)),
        before_sleep=lambda retry_state: logger.warning(
            f"Embedding API call failed, retrying in {retry_state.next_action.sleep} seconds..."
        )
    )
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using OpenAI with retry logic."""
        response = await self.openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding

    async def generate_question_embedding(self, question: QuestionData) -> List[float]:
        """Generate embedding for a question (combines text + options)."""
        text = f"{question.question_text}\n"
        for key, value in question.options.items():
            text += f"{key}: {value}\n"
        return await self.generate_embedding(text)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        retry=retry_if_exception_type((APIError, RateLimitError, APIConnectionError)),
        before_sleep=lambda retry_state: logger.warning(
            f"Batch embedding API call failed, retrying in {retry_state.next_action.sleep} seconds..."
        )
    )
    async def _batch_embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Internal method to embed a batch of texts with retry logic."""
        response = await self.openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=texts
        )
        return [emb_data.embedding for emb_data in response.data]

    async def batch_generate_embeddings(
        self,
        questions: List[QuestionData]
    ) -> Dict[int, List[float]]:
        """Generate embeddings for all questions in batches."""
        embeddings = {}
        batch_size = 100  # OpenAI batch limit

        for i in range(0, len(questions), batch_size):
            batch = questions[i:i + batch_size]
            texts = []
            for q in batch:
                text = f"{q.question_text}\n"
                for key, value in q.options.items():
                    text += f"{key}: {value}\n"
                texts.append(text)

            try:
                batch_embeddings = await self._batch_embed_texts(texts)
                for j, embedding in enumerate(batch_embeddings):
                    embeddings[batch[j].row_number] = embedding

                logger.info(f"Generated embeddings for batch {i // batch_size + 1}")
            except Exception as e:
                logger.error(f"Batch embedding failed after retries: {e}")
                # Continue with remaining batches

        return embeddings

    # =====================================
    # Concept Matching
    # =====================================

    async def ensure_concept_embeddings(self):
        """Ensure concepts have embeddings in Qdrant."""
        collection_name = "concepts"

        # Check if collection exists
        try:
            await self.qdrant_client.get_collection(collection_name)
        except Exception:
            # Create collection
            await self.qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=1536,  # text-embedding-3-small dimension
                    distance=Distance.COSINE
                )
            )
            logger.info(f"Created Qdrant collection: {collection_name}")

        # Check if we have embeddings for this course's concepts
        try:
            result = await self.qdrant_client.scroll(
                collection_name=collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="course_id",
                            match=MatchValue(value=str(self.course_id))
                        )
                    ]
                ),
                limit=1
            )
            if result[0]:
                logger.info("Concept embeddings already exist in Qdrant")
                return
        except Exception:
            pass

        # Generate and store concept embeddings
        logger.info("Generating concept embeddings...")
        points = []
        for i, concept in enumerate(self.concepts):
            text = f"{concept.name}: {concept.description or ''}"
            try:
                embedding = await self.generate_embedding(text)
                points.append({
                    "id": i,
                    "vector": embedding,
                    "payload": {
                        "concept_id": str(concept.id),
                        "course_id": str(self.course_id),
                        "name": concept.name,
                        "knowledge_area_id": concept.knowledge_area_id,
                    }
                })
            except Exception as e:
                logger.warning(f"Failed to embed concept {concept.name}: {e}")

            if len(points) >= 100:
                await self.qdrant_client.upsert(
                    collection_name=collection_name,
                    points=points
                )
                points = []

        if points:
            await self.qdrant_client.upsert(
                collection_name=collection_name,
                points=points
            )

        logger.info(f"Stored {len(self.concepts)} concept embeddings in Qdrant")

    async def find_similar_concepts(
        self,
        question_embedding: List[float],
        top_k: int = 10
    ) -> List[Tuple[Concept, float]]:
        """Find similar concepts using Qdrant semantic search."""
        try:
            results = await self.qdrant_client.search(
                collection_name="concepts",
                query_vector=question_embedding,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="course_id",
                            match=MatchValue(value=str(self.course_id))
                        )
                    ]
                ),
                limit=top_k
            )

            # Map back to concepts
            matched = []
            concept_by_id = {str(c.id): c for c in self.concepts}
            for result in results:
                concept_id = result.payload.get("concept_id")
                if concept_id and concept_id in concept_by_id:
                    matched.append((concept_by_id[concept_id], result.score))

            return matched
        except Exception as e:
            logger.error(f"Qdrant search failed: {e}")
            return []

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        retry=retry_if_exception_type((APIError, RateLimitError, APIConnectionError)),
        before_sleep=lambda retry_state: logger.warning(
            f"GPT-4 API call failed, retrying in {retry_state.next_action.sleep} seconds..."
        )
    )
    async def _call_gpt4_for_concepts(self, prompt: str) -> dict:
        """Internal method to call GPT-4 with retry logic."""
        response = await self.openai_client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=1000
        )
        content = response.choices[0].message.content
        return json.loads(content)

    async def select_concepts_with_gpt4(
        self,
        question: QuestionData,
        candidates: List[Tuple[Concept, float]]
    ) -> List[ConceptMapping]:
        """Use GPT-4 to select the most relevant concepts."""
        if not candidates:
            return []

        # Format candidates for prompt
        candidates_text = ""
        for i, (concept, score) in enumerate(candidates, start=1):
            candidates_text += f"{i}. {concept.name} (ID: {concept.id})\n"
            if concept.description:
                candidates_text += f"   Description: {concept.description[:200]}\n"

        prompt = CONCEPT_SELECTION_PROMPT.format(
            question_text=question.question_text,
            option_a=question.options.get("A", ""),
            option_b=question.options.get("B", ""),
            option_c=question.options.get("C", ""),
            option_d=question.options.get("D", ""),
            correct_answer=question.correct_answer,
            explanation=question.explanation,
            candidates=candidates_text
        )

        try:
            data = await self._call_gpt4_for_concepts(prompt)

            # Handle both array and object with array property
            if isinstance(data, dict):
                data = data.get("concepts", data.get("mappings", []))

            mappings = []
            for item in data[:5]:  # Limit to 5
                try:
                    mappings.append(ConceptMapping(
                        concept_id=UUID(item["concept_id"]),
                        concept_name=item["concept_name"],
                        relevance=float(item["relevance"]),
                        reasoning=item.get("reasoning", "")
                    ))
                except (KeyError, ValueError) as e:
                    logger.warning(f"Invalid mapping item: {e}")

            return mappings

        except Exception as e:
            logger.error(f"GPT-4 concept selection failed after retries: {e}")
            # Fallback: use top semantic matches
            return [
                ConceptMapping(
                    concept_id=c.id,
                    concept_name=c.name,
                    relevance=min(0.9, score),
                    reasoning="Semantic similarity fallback"
                )
                for c, score in candidates[:3]
            ]

    async def map_question_to_concepts(
        self,
        question: QuestionData,
        question_embedding: List[float]
    ) -> List[ConceptMapping]:
        """Map a question to concepts using semantic search + GPT-4."""
        # Find similar concepts
        candidates = await self.find_similar_concepts(question_embedding, top_k=10)

        if not candidates:
            self.result.warnings.append(
                f"Row {question.row_number}: No similar concepts found"
            )
            return []

        # Use GPT-4 to select relevant concepts
        mappings = await self.select_concepts_with_gpt4(question, candidates)

        if not mappings:
            self.result.warnings.append(
                f"Row {question.row_number}: GPT-4 returned no mappings"
            )
            # Fallback to top semantic match
            return [
                ConceptMapping(
                    concept_id=candidates[0][0].id,
                    concept_name=candidates[0][0].name,
                    relevance=0.8,
                    reasoning="Fallback to top semantic match"
                )
            ]

        return mappings

    async def map_questions_from_tags(
        self,
        questions: List[QuestionData],
    ) -> Dict[int, List[ConceptMapping]]:
        """
        Map questions to concepts using pre-tagged concept names from CSV.

        This is an alternative to the GPT-4 semantic mapping approach.
        Uses fuzzy string matching to find the best concept match for each tag.

        Args:
            questions: List of QuestionData with concept_tags populated

        Returns:
            Dict mapping row_number to list of ConceptMapping objects
        """
        matcher = ConceptTagMatcher(self.concepts, self.tag_match_threshold)
        mappings: Dict[int, List[ConceptMapping]] = {}

        # Track tag usage across KAs for consistency validation (AC 9)
        tag_ka_usage: Dict[str, Dict[str, List[int]]] = {}  # tag -> {ka_id: [row_numbers]}

        matched_count = 0
        unmatched_count = 0

        for question in questions:
            question_mappings: List[ConceptMapping] = []
            seen_concept_ids = set()  # Avoid duplicate mappings for same concept

            for tag in question.concept_tags:
                result = matcher.match_tag(tag)

                if result:
                    concept, score, relevance = result

                    # Skip if we already mapped this concept for this question
                    if concept.id in seen_concept_ids:
                        continue
                    seen_concept_ids.add(concept.id)

                    # AC 6: Validate KA consistency between question and matched concept
                    if concept.knowledge_area_id and question.knowledge_area_id:
                        if concept.knowledge_area_id != question.knowledge_area_id:
                            self.result.warnings.append(
                                f"Row {question.row_number}: Tag '{tag}' matched concept "
                                f"'{concept.name}' from KA '{concept.knowledge_area_id}' "
                                f"but question is in KA '{question.knowledge_area_id}'"
                            )

                    # Track tag KA usage for cross-question validation (AC 9)
                    tag_lower = tag.lower().strip()
                    if tag_lower not in tag_ka_usage:
                        tag_ka_usage[tag_lower] = {}
                    if question.knowledge_area_id not in tag_ka_usage[tag_lower]:
                        tag_ka_usage[tag_lower][question.knowledge_area_id] = []
                    tag_ka_usage[tag_lower][question.knowledge_area_id].append(question.row_number)

                    question_mappings.append(ConceptMapping(
                        concept_id=concept.id,
                        concept_name=concept.name,
                        relevance=relevance,
                        reasoning=f"Matched from CSV tag '{tag}' (score: {score:.0f}%)"
                    ))
                    matched_count += 1
                    logger.debug(
                        f"Row {question.row_number}: Matched tag '{tag}' -> "
                        f"'{concept.name}' (score: {score:.0f}%, relevance: {relevance})"
                    )
                else:
                    # Track unmatched tag for reporting
                    question_preview = question.question_text[:50]
                    self.unmatched_tags.append((question.row_number, tag, question_preview))
                    unmatched_count += 1
                    logger.debug(f"Row {question.row_number}: No match for tag '{tag}'")

            mappings[question.row_number] = question_mappings

        # AC 9: Warn about tags used across different KAs
        for tag, ka_rows in tag_ka_usage.items():
            if len(ka_rows) > 1:
                ka_list = ", ".join([f"{ka} (rows: {rows})" for ka, rows in ka_rows.items()])
                self.result.warnings.append(
                    f"Tag '{tag}' used across multiple KAs: {ka_list}"
                )

        logger.info(
            f"Tag-based mapping complete: {matched_count} matched, "
            f"{unmatched_count} unmatched from {len(questions)} questions"
        )

        return mappings

    async def create_concept_from_tag(
        self,
        tag: str,
        knowledge_area_id: str,
    ) -> Concept:
        """
        Create a new concept from an unmatched tag.

        Args:
            tag: The tag string to create a concept from
            knowledge_area_id: KA ID from the question (inherited)

        Returns:
            The newly created Concept model
        """
        # Normalize tag to title case for concept name
        name = tag.strip().title()

        concept_data = ConceptCreate(
            course_id=self.course_id,
            name=name,
            description=f"Auto-generated from question tag: {tag}",
            corpus_section_ref=None,
            knowledge_area_id=knowledge_area_id,
            difficulty_estimate=0.5,
            prerequisite_depth=0,
        )

        async with AsyncSessionLocal() as db:
            repo = ConceptRepository(db)
            concept = await repo.create_concept(concept_data)
            await db.commit()
            await db.refresh(concept)

        # Track for reporting
        self.created_concepts.append((concept, tag))

        # Add to local concepts list so future tags can match it
        self.concepts.append(concept)

        logger.warning(
            f"Created new concept '{name}' (ID: {concept.id}) "
            f"from tag '{tag}' in KA '{knowledge_area_id}'"
        )

        return concept

    async def create_missing_concepts_from_tags(
        self,
        questions: List[QuestionData],
        mappings: Dict[int, List[ConceptMapping]],
    ) -> Dict[int, List[ConceptMapping]]:
        """
        Process unmatched tags and create new concepts for them.

        This should be called after map_questions_from_tags when
        --create-missing-concepts flag is set.

        Args:
            questions: List of QuestionData with concept_tags
            mappings: Existing mappings from map_questions_from_tags

        Returns:
            Updated mappings dict with new concept mappings added
        """
        if not self.unmatched_tags:
            logger.info("No unmatched tags to create concepts from")
            return mappings

        logger.info(f"Creating concepts for {len(self.unmatched_tags)} unmatched tags...")

        # Build a lookup for questions by row number
        questions_by_row = {q.row_number: q for q in questions}

        # Track created tags to avoid duplicates
        created_tag_to_concept: Dict[str, Concept] = {}

        # Process unmatched tags
        tags_to_process = list(self.unmatched_tags)
        self.unmatched_tags = []  # Clear for re-population if needed

        for row_num, tag, question_preview in tags_to_process:
            tag_lower = tag.lower().strip()
            question = questions_by_row.get(row_num)

            if not question:
                continue

            # Check if we already created this concept in this run
            if tag_lower in created_tag_to_concept:
                concept = created_tag_to_concept[tag_lower]
            else:
                # Create new concept
                concept = await self.create_concept_from_tag(
                    tag=tag,
                    knowledge_area_id=question.knowledge_area_id,
                )
                created_tag_to_concept[tag_lower] = concept

            # Add mapping for this question
            if row_num not in mappings:
                mappings[row_num] = []

            # Check if we already have this concept mapped (avoid duplicates)
            existing_ids = {m.concept_id for m in mappings[row_num]}
            if concept.id not in existing_ids:
                mappings[row_num].append(ConceptMapping(
                    concept_id=concept.id,
                    concept_name=concept.name,
                    relevance=0.8,  # Default relevance for created concepts
                    reasoning=f"Created from unmatched CSV tag '{tag}'"
                ))

        logger.info(f"Created {len(created_tag_to_concept)} new concepts from unmatched tags")

        return mappings

    # =====================================
    # Validation
    # =====================================

    def validate_import_results(
        self,
        questions: List[QuestionData],
        mappings: Dict[int, List[ConceptMapping]]
    ) -> Dict[str, Any]:
        """Validate import results and generate coverage report."""
        # Questions without mappings
        unmapped = [q for q in questions if q.row_number not in mappings or not mappings[q.row_number]]

        # Count questions per concept
        concept_question_count = Counter()
        for row_mappings in mappings.values():
            for m in row_mappings:
                concept_question_count[str(m.concept_id)] += 1

        # Concepts with < 3 questions
        concepts_needing_content = [
            c.name for c in self.concepts
            if concept_question_count.get(str(c.id), 0) < 3
        ]

        # Distribution by KA
        ka_counts = Counter(q.knowledge_area_id for q in questions)

        # IRT parameter statistics (Story 10.2 AC 6)
        difficulties = [q.difficulty for q in questions]
        discriminations = [q.discrimination for q in questions]
        guess_rates = [q.guess_rate for q in questions]
        slip_rates = [q.slip_rate for q in questions]
        difficulty_labels = Counter(q.difficulty_label for q in questions if q.difficulty_label)

        irt_stats = {
            "difficulty": {
                "min": min(difficulties) if difficulties else 0.0,
                "max": max(difficulties) if difficulties else 0.0,
                "avg": sum(difficulties) / len(difficulties) if difficulties else 0.0,
            },
            "discrimination": {
                "min": min(discriminations) if discriminations else 1.0,
                "max": max(discriminations) if discriminations else 1.0,
                "avg": sum(discriminations) / len(discriminations) if discriminations else 1.0,
            },
            "guess_rate": {
                "min": min(guess_rates) if guess_rates else 0.25,
                "max": max(guess_rates) if guess_rates else 0.25,
                "avg": sum(guess_rates) / len(guess_rates) if guess_rates else 0.25,
            },
            "slip_rate": {
                "min": min(slip_rates) if slip_rates else 0.10,
                "max": max(slip_rates) if slip_rates else 0.10,
                "avg": sum(slip_rates) / len(slip_rates) if slip_rates else 0.10,
            },
            "by_tier": dict(difficulty_labels),
        }

        report = {
            "total_questions": len(questions),
            "mapped_questions": len(questions) - len(unmapped),
            "unmapped_questions": len(unmapped),
            "distribution_by_ka": dict(ka_counts),
            "total_concepts": len(self.concepts),
            "concepts_with_questions": len([c for c in self.concepts if concept_question_count.get(str(c.id), 0) > 0]),
            "concepts_needing_content": len(concepts_needing_content),
            "avg_mappings_per_question": sum(len(m) for m in mappings.values()) / max(1, len(mappings)),
            "irt_parameters": irt_stats,
        }

        # Log warnings for concepts with few questions
        for name in concepts_needing_content[:10]:
            self.result.warnings.append(f"Concept '{name}' has fewer than 3 questions")

        return report

    # =====================================
    # Database Operations
    # =====================================

    async def insert_questions_and_mappings(
        self,
        questions: List[QuestionData],
        mappings: Dict[int, List[ConceptMapping]]
    ) -> Tuple[int, int, List[UUID]]:
        """Insert questions and concept mappings into database."""
        if self.dry_run:
            logger.info("DRY RUN - No database changes made")
            return len(questions), sum(len(m) for m in mappings.values()), []

        inserted_question_ids = []
        mapping_count = 0

        async with AsyncSessionLocal() as db:
            repo = QuestionRepository(db)

            for question in questions:
                try:
                    # Build question dict
                    question_dict = {
                        "course_id": self.course_id,
                        "question_text": question.question_text,
                        "options": question.options,
                        "correct_answer": question.correct_answer,
                        "explanation": question.explanation,
                        "knowledge_area_id": question.knowledge_area_id,
                        # IRT parameters
                        "difficulty": question.difficulty,
                        "difficulty_label": question.difficulty_label,
                        "discrimination": question.discrimination,
                        "guess_rate": question.guess_rate,
                        "slip_rate": question.slip_rate,
                        "source": question.source,
                        "corpus_reference": question.corpus_reference,
                        # Story 2.15: Secondary tags
                        "perspectives": question.perspectives,
                        "competencies": question.competencies,
                    }

                    # Insert question
                    q = await repo.create_question(question_dict)
                    inserted_question_ids.append(q.id)

                    # Insert concept mappings
                    question_mappings = mappings.get(question.row_number, [])
                    for m in question_mappings:
                        await repo.add_concept_mapping(
                            question_id=q.id,
                            concept_id=m.concept_id,
                            relevance=m.relevance
                        )
                        mapping_count += 1

                except Exception as e:
                    logger.error(f"Failed to insert question {question.row_number}: {e}")
                    self.result.errors.append(f"Row {question.row_number}: Insert failed - {e}")

        return len(inserted_question_ids), mapping_count, inserted_question_ids

    async def rollback_import(self, question_ids: List[UUID]):
        """Rollback imported questions."""
        if not question_ids:
            return

        async with AsyncSessionLocal() as db:
            repo = QuestionRepository(db)
            deleted = await repo.delete_questions_by_ids(question_ids)
            logger.info(f"Rolled back {deleted} questions")

    # =====================================
    # Export
    # =====================================

    def export_mappings_to_csv(
        self,
        questions: List[QuestionData],
        mappings: Dict[int, List[ConceptMapping]],
        output_path: str
    ):
        """Export question-concept mappings to CSV for SME review."""
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "row_number",
                "question_text",
                "correct_answer",
                "knowledge_area",
                "concept_id",
                "concept_name",
                "relevance",
                "reasoning"
            ])

            for question in questions:
                question_mappings = mappings.get(question.row_number, [])
                if not question_mappings:
                    writer.writerow([
                        question.row_number,
                        question.question_text[:100] + "...",
                        question.correct_answer,
                        question.knowledge_area_name,
                        "",
                        "NO MAPPING",
                        "",
                        ""
                    ])
                else:
                    for m in question_mappings:
                        writer.writerow([
                            question.row_number,
                            question.question_text[:100] + "...",
                            question.correct_answer,
                            question.knowledge_area_name,
                            str(m.concept_id),
                            m.concept_name,
                            m.relevance,
                            m.reasoning
                        ])

        logger.info(f"Exported mappings to {output_path}")

    def export_unmatched_tags_report(self, output_path: str):
        """
        Export unmatched tags to CSV for SME review.

        CSV columns: row_number, tag, question_preview
        """
        if not self.unmatched_tags:
            logger.info("No unmatched tags to export")
            return

        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["row_number", "tag", "question_preview"])

            for row_num, tag, question_preview in self.unmatched_tags:
                writer.writerow([row_num, tag, question_preview])

        logger.info(f"Exported {len(self.unmatched_tags)} unmatched tags to {output_path}")

    def export_created_concepts_report(self, output_path: str):
        """
        Export created concepts to CSV for SME review.

        CSV columns: concept_id, name, knowledge_area, source_tag, created_at
        """
        if not self.created_concepts:
            logger.info("No created concepts to export")
            return

        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["concept_id", "name", "knowledge_area", "source_tag", "created_at"])

            for concept, source_tag in self.created_concepts:
                writer.writerow([
                    str(concept.id),
                    concept.name,
                    concept.knowledge_area_id,
                    source_tag,
                    concept.created_at.isoformat() if concept.created_at else "",
                ])

        logger.info(f"Exported {len(self.created_concepts)} created concepts to {output_path}")

    # =====================================
    # Main Import Pipeline
    # =====================================

    async def run(
        self,
        input_file: str,
        file_format: Optional[str] = None,
        output_csv: Optional[str] = None,
        unmatched_report: Optional[str] = None,
        created_concepts_report: Optional[str] = None,
    ) -> ImportResult:
        """Run the full import pipeline."""
        logger.info(f"Starting import for course: {self.course_slug}")

        # Initialize
        if not await self.initialize():
            self.result.errors.append("Initialization failed")
            return self.result

        # Parse input file
        try:
            questions = self.parse_file(input_file, file_format)
            self.result.questions_parsed = len(questions)
        except Exception as e:
            self.result.errors.append(f"Parse error: {e}")
            return self.result

        if not questions:
            self.result.errors.append("No valid questions parsed")
            return self.result

        self.result.questions_valid = len(questions)

        # Concept mapping
        mappings: Dict[int, List[ConceptMapping]] = {}

        if not self.skip_concept_mapping:
            if self.use_csv_tags:
                # Use pre-tagged concepts from CSV
                logger.info("Using pre-tagged concepts from CSV (--use-csv-tags)")
                mappings = await self.map_questions_from_tags(questions)

                # Optionally create concepts for unmatched tags
                if self.create_missing_concepts and self.unmatched_tags:
                    logger.info("Creating concepts for unmatched tags (--create-missing-concepts)")
                    mappings = await self.create_missing_concepts_from_tags(questions, mappings)
            else:
                # Use GPT-4 semantic mapping (existing flow)
                # Ensure concept embeddings exist
                await self.ensure_concept_embeddings()

                # Generate question embeddings
                logger.info("Generating question embeddings...")
                question_embeddings = await self.batch_generate_embeddings(questions)

                # Map questions to concepts
                logger.info("Mapping questions to concepts...")
                for question in questions:
                    if question.row_number in question_embeddings:
                        question_mappings = await self.map_question_to_concepts(
                            question,
                            question_embeddings[question.row_number]
                        )
                        mappings[question.row_number] = question_mappings
                    else:
                        self.result.warnings.append(
                            f"Row {question.row_number}: No embedding generated"
                        )

        # Validate
        report = self.validate_import_results(questions, mappings)
        logger.info(f"Validation report: {json.dumps(report, indent=2)}")

        # Insert into database
        inserted, mapping_count, question_ids = await self.insert_questions_and_mappings(
            questions, mappings
        )
        self.result.questions_inserted = inserted
        self.result.mappings_created = mapping_count

        # Export for SME review
        if output_csv:
            self.export_mappings_to_csv(questions, mappings, output_csv)

        # Export unmatched tags report
        if unmatched_report and self.unmatched_tags:
            self.export_unmatched_tags_report(unmatched_report)

        # Export created concepts report
        if created_concepts_report and self.created_concepts:
            self.export_created_concepts_report(created_concepts_report)

        # Summary
        self._log_summary(report)

        return self.result

    def _log_summary(self, report: Dict[str, Any]):
        """Log import summary."""
        logger.info("=" * 60)
        logger.info("IMPORT SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Course: {self.course_slug}")
        logger.info(f"Questions parsed: {self.result.questions_parsed}")
        logger.info(f"Questions valid: {self.result.questions_valid}")
        logger.info(f"Questions inserted: {self.result.questions_inserted}")
        logger.info(f"Concept mappings created: {self.result.mappings_created}")
        logger.info(f"Errors: {len(self.result.errors)}")
        logger.info(f"Warnings: {len(self.result.warnings)}")
        logger.info("")
        logger.info("Distribution by Knowledge Area:")
        for ka, count in report.get("distribution_by_ka", {}).items():
            logger.info(f"  - {ka}: {count}")
        logger.info("")
        logger.info(f"Concepts with questions: {report.get('concepts_with_questions', 0)}/{report.get('total_concepts', 0)}")
        logger.info(f"Concepts needing content: {report.get('concepts_needing_content', 0)}")
        logger.info("")
        # Story 10.2 AC 6: IRT parameter statistics
        irt_params = report.get("irt_parameters", {})
        if irt_params:
            logger.info("IRT Parameter Statistics:")
            difficulty = irt_params.get("difficulty", {})
            logger.info(f"  Difficulty (b-parameter): min={difficulty.get('min', 0):.2f}, max={difficulty.get('max', 0):.2f}, avg={difficulty.get('avg', 0):.2f}")
            discrimination = irt_params.get("discrimination", {})
            logger.info(f"  Discrimination (a-parameter): min={discrimination.get('min', 1):.2f}, max={discrimination.get('max', 1):.2f}, avg={discrimination.get('avg', 1):.2f}")
            guess_rate = irt_params.get("guess_rate", {})
            logger.info(f"  Guess rate: min={guess_rate.get('min', 0.25):.2f}, max={guess_rate.get('max', 0.25):.2f}, avg={guess_rate.get('avg', 0.25):.2f}")
            slip_rate = irt_params.get("slip_rate", {})
            logger.info(f"  Slip rate: min={slip_rate.get('min', 0.10):.2f}, max={slip_rate.get('max', 0.10):.2f}, avg={slip_rate.get('avg', 0.10):.2f}")
            by_tier = irt_params.get("by_tier", {})
            if by_tier:
                logger.info("  Distribution by difficulty tier:")
                for tier, count in sorted(by_tier.items()):
                    logger.info(f"    - {tier}: {count}")
        logger.info("=" * 60)

        if self.result.errors:
            logger.warning("ERRORS:")
            for error in self.result.errors[:10]:
                logger.warning(f"  - {error}")

        if self.result.warnings:
            logger.warning(f"WARNINGS ({len(self.result.warnings)} total):")
            for warning in self.result.warnings[:10]:
                logger.warning(f"  - {warning}")

        # Story 2.14: Remind user to sync belief states when concepts are created
        if self.created_concepts:
            logger.info("")
            logger.info("=" * 60)
            logger.info("ACTION REQUIRED: Sync User Belief States")
            logger.info("=" * 60)
            logger.info(f"New concepts were created ({len(self.created_concepts)} total).")
            logger.info("Existing users need belief states for these new concepts.")
            logger.info("")
            logger.info("Run the following command to sync all users:")
            logger.info(f"  python scripts/sync_belief_states.py --course-slug {self.course_slug}")
            logger.info("")
            logger.info("Or use --dry-run first to preview changes:")
            logger.info(f"  python scripts/sync_belief_states.py --course-slug {self.course_slug} --dry-run")
            logger.info("=" * 60)


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Import vendor questions with concept mapping"
    )
    parser.add_argument(
        "--course-slug",
        required=True,
        help="Course slug (e.g., 'cbap')"
    )
    parser.add_argument(
        "--input-file",
        required=True,
        help="Path to CSV or JSON file"
    )
    parser.add_argument(
        "--format",
        choices=["csv", "json"],
        help="File format (auto-detected if not specified)"
    )
    parser.add_argument(
        "--output-csv",
        help="Path for concept mapping export CSV"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate without inserting into database"
    )
    parser.add_argument(
        "--skip-concept-mapping",
        action="store_true",
        help="Skip concept mapping (just insert questions)"
    )
    parser.add_argument(
        "--use-csv-tags",
        action="store_true",
        help="Use pre-tagged concepts from concept_tags column instead of GPT-4 mapping"
    )
    parser.add_argument(
        "--tag-match-threshold",
        type=int,
        default=85,
        choices=range(50, 101),
        metavar="[50-100]",
        help="Fuzzy match threshold for tag-to-concept matching (default: 85)"
    )
    parser.add_argument(
        "--create-missing-concepts",
        action="store_true",
        help="Create new concepts for tags that don't match existing concepts"
    )
    parser.add_argument(
        "--unmatched-report",
        help="Path for unmatched tags report CSV"
    )
    parser.add_argument(
        "--created-concepts-report",
        help="Path for created concepts report CSV"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Set default output path
    output_csv = args.output_csv
    if not output_csv:
        output_csv = f"scripts/output/question_concept_mappings_{args.course_slug}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    importer = VendorQuestionImporter(
        course_slug=args.course_slug,
        dry_run=args.dry_run,
        skip_concept_mapping=args.skip_concept_mapping,
        use_csv_tags=args.use_csv_tags,
        tag_match_threshold=args.tag_match_threshold,
        create_missing_concepts=args.create_missing_concepts,
    )

    result = await importer.run(
        input_file=args.input_file,
        file_format=args.format,
        output_csv=output_csv,
        unmatched_report=args.unmatched_report,
        created_concepts_report=args.created_concepts_report,
    )

    # Exit with error code if errors occurred
    if result.errors:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
