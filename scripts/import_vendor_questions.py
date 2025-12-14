"""
Import vendor questions with concept mapping for multi-course architecture.

This script:
1. Looks up course by slug from the database
2. Parses questions from CSV/JSON
3. Maps vendor KA names to course knowledge_area_id values
4. Generates question embeddings
5. Uses semantic search + GPT-4 to map questions to concepts
6. Validates and inserts questions with concept mappings
7. Exports mappings for SME review
"""
import argparse
import asyncio
import csv
import json
import logging
import os
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

import httpx
from openai import AsyncOpenAI, APIError, RateLimitError, APIConnectionError
from qdrant_client import AsyncQdrantClient
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from qdrant_client.models import Distance, Filter, FieldCondition, MatchValue, VectorParams

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "apps" / "api"))

from src.config import settings
from src.db.session import AsyncSessionLocal
from src.models.concept import Concept
from src.models.course import Course
from src.repositories.concept_repository import ConceptRepository
from src.repositories.question_repository import QuestionRepository

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

# Difficulty string to float mapping
DIFFICULTY_MAP = {
    "easy": 0.3,
    "medium": 0.5,
    "hard": 0.7,
}

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
    difficulty: float = 0.5
    source: str = "vendor"
    corpus_reference: Optional[str] = None
    row_number: int = 0


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


class VendorQuestionImporter:
    """
    Orchestrates the vendor question import process with concept mapping.
    """

    def __init__(
        self,
        course_slug: str,
        dry_run: bool = False,
        skip_concept_mapping: bool = False,
        batch_size: int = 50
    ):
        self.course_slug = course_slug
        self.dry_run = dry_run
        self.skip_concept_mapping = skip_concept_mapping
        self.batch_size = batch_size

        self.course: Optional[Course] = None
        self.course_id: Optional[UUID] = None
        self.ka_name_to_id: Dict[str, str] = {}
        self.concepts: List[Concept] = []
        self.concept_embeddings: Dict[UUID, List[float]] = {}

        self.openai_client: Optional[AsyncOpenAI] = None
        self.qdrant_client: Optional[AsyncQdrantClient] = None

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

        # Map KA name to ID
        ka_id = self.map_ka_name_to_id(ka_name)
        if not ka_id:
            self.result.warnings.append(f"Row {row_num}: Unknown KA '{ka_name}', skipping")
            return None

        # Difficulty
        difficulty_str = row.get("difficulty", "Medium").strip().lower()
        difficulty = DIFFICULTY_MAP.get(difficulty_str, 0.5)
        try:
            # Also support float values
            difficulty = float(difficulty_str)
            difficulty = max(0.0, min(1.0, difficulty))
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
            source=row.get("source", "vendor"),
            corpus_reference=row.get("corpus_reference", row.get("babok_reference")),
            row_number=row_num,
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

        difficulty = item.get("difficulty", 0.5)
        if isinstance(difficulty, str):
            difficulty = DIFFICULTY_MAP.get(difficulty.lower(), 0.5)

        return QuestionData(
            question_text=question_text,
            options=options,
            correct_answer=correct_answer,
            explanation=explanation,
            knowledge_area_name=ka_name,
            knowledge_area_id=ka_id,
            difficulty=difficulty,
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

        report = {
            "total_questions": len(questions),
            "mapped_questions": len(questions) - len(unmapped),
            "unmapped_questions": len(unmapped),
            "distribution_by_ka": dict(ka_counts),
            "total_concepts": len(self.concepts),
            "concepts_with_questions": len([c for c in self.concepts if concept_question_count.get(str(c.id), 0) > 0]),
            "concepts_needing_content": len(concepts_needing_content),
            "avg_mappings_per_question": sum(len(m) for m in mappings.values()) / max(1, len(mappings)),
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
                        "difficulty": question.difficulty,
                        "source": question.source,
                        "corpus_reference": question.corpus_reference,
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

    # =====================================
    # Main Import Pipeline
    # =====================================

    async def run(
        self,
        input_file: str,
        file_format: Optional[str] = None,
        output_csv: Optional[str] = None
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
        logger.info("=" * 60)

        if self.result.errors:
            logger.warning("ERRORS:")
            for error in self.result.errors[:10]:
                logger.warning(f"  - {error}")

        if self.result.warnings:
            logger.warning(f"WARNINGS ({len(self.result.warnings)} total):")
            for warning in self.result.warnings[:10]:
                logger.warning(f"  - {warning}")


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
        skip_concept_mapping=args.skip_concept_mapping
    )

    result = await importer.run(
        input_file=args.input_file,
        file_format=args.format,
        output_csv=output_csv
    )

    # Exit with error code if errors occurred
    if result.errors:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
