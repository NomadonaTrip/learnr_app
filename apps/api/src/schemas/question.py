"""
Question Pydantic schemas for request/response validation.
Supports multi-course architecture with concept mapping.
"""
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class QuestionOptionsSchema(BaseModel):
    """Schema for question answer options."""
    A: str = Field(..., min_length=1, description="Option A text")
    B: str = Field(..., min_length=1, description="Option B text")
    C: str = Field(..., min_length=1, description="Option C text")
    D: str = Field(..., min_length=1, description="Option D text")


class QuestionBase(BaseModel):
    """Base question schema with shared fields."""
    question_text: str = Field(..., min_length=10, description="Question text")
    options: QuestionOptionsSchema = Field(..., description="Answer options A-D")
    correct_answer: str = Field(..., pattern="^[ABCD]$", description="Correct answer (A/B/C/D)")
    explanation: str = Field(..., min_length=10, description="Answer explanation")
    knowledge_area_id: str = Field(..., max_length=50, description="Knowledge area ID")
    difficulty: float = Field(0.5, ge=0.0, le=1.0, description="IRT difficulty (0.0-1.0)")
    source: str = Field("vendor", max_length=50, description="Question source")
    corpus_reference: Optional[str] = Field(None, max_length=100, description="Source reference")


class QuestionCreate(QuestionBase):
    """Schema for creating a new question."""
    course_id: UUID = Field(..., description="Course UUID this question belongs to")
    discrimination: float = Field(1.0, ge=0.0, le=5.0, description="IRT discrimination (0-5)")
    guess_rate: float = Field(0.25, ge=0.0, le=1.0, description="P(correct | not mastered)")
    slip_rate: float = Field(0.10, ge=0.0, le=1.0, description="P(incorrect | mastered)")


class QuestionUpdate(BaseModel):
    """Schema for updating a question."""
    question_text: Optional[str] = Field(None, min_length=10)
    options: Optional[QuestionOptionsSchema] = None
    correct_answer: Optional[str] = Field(None, pattern="^[ABCD]$")
    explanation: Optional[str] = Field(None, min_length=10)
    knowledge_area_id: Optional[str] = Field(None, max_length=50)
    difficulty: Optional[float] = Field(None, ge=0.0, le=1.0)
    discrimination: Optional[float] = Field(None, ge=0.0, le=5.0)
    guess_rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    slip_rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    corpus_reference: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None


class QuestionResponse(QuestionBase):
    """Schema for question response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    course_id: UUID
    discrimination: float
    guess_rate: float
    slip_rate: float
    times_asked: int
    times_correct: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class QuestionWithConceptsResponse(QuestionResponse):
    """Schema for question with mapped concepts."""
    concepts: List["ConceptMappingResponse"] = Field(default_factory=list)


# =====================================
# Import-related schemas
# =====================================

class QuestionImport(BaseModel):
    """
    Schema for importing questions from CSV/JSON.
    Supports both JSONB options and separate column formats.
    """
    question_text: str = Field(..., min_length=10)
    correct_answer: str = Field(..., pattern="^[ABCDabcd]$")
    explanation: str = Field(..., min_length=1)
    knowledge_area: str = Field(..., description="Knowledge area name (will be mapped to ID)")

    # Support both formats for options
    options: Optional[Dict[str, str]] = None  # JSONB format
    option_a: Optional[str] = None  # CSV format
    option_b: Optional[str] = None
    option_c: Optional[str] = None
    option_d: Optional[str] = None

    # Optional fields
    difficulty: Optional[str] = None  # Can be "Easy"/"Medium"/"Hard" or float string
    source: str = Field("vendor", max_length=50)
    corpus_reference: Optional[str] = Field(None, alias="babok_reference")

    @field_validator("correct_answer")
    @classmethod
    def normalize_correct_answer(cls, v: str) -> str:
        return v.upper()

    def get_options_dict(self) -> Dict[str, str]:
        """Convert to options dict regardless of input format."""
        if self.options:
            return self.options
        return {
            "A": self.option_a or "",
            "B": self.option_b or "",
            "C": self.option_c or "",
            "D": self.option_d or "",
        }

    def get_difficulty_float(self) -> float:
        """Convert difficulty to float (0.0-1.0)."""
        if self.difficulty is None:
            return 0.5

        # Try parsing as float first
        try:
            val = float(self.difficulty)
            return max(0.0, min(1.0, val))
        except ValueError:
            pass

        # Map string difficulty to float
        difficulty_map = {
            "easy": 0.3,
            "medium": 0.5,
            "hard": 0.7,
        }
        return difficulty_map.get(self.difficulty.lower(), 0.5)


class QuestionImportResult(BaseModel):
    """Schema for import result summary."""
    total_parsed: int
    valid_questions: int
    invalid_questions: int
    inserted_questions: int
    skipped_duplicates: int
    errors: List[str]


# =====================================
# Concept Mapping schemas
# =====================================

class QuestionConceptCreate(BaseModel):
    """Schema for creating a question-concept mapping."""
    question_id: UUID
    concept_id: UUID
    relevance: float = Field(1.0, ge=0.0, le=1.0, description="Relevance score (0.0-1.0)")


class QuestionConceptResponse(BaseModel):
    """Schema for question-concept mapping response."""
    model_config = ConfigDict(from_attributes=True)

    question_id: UUID
    concept_id: UUID
    relevance: float
    created_at: datetime


class ConceptMappingResponse(BaseModel):
    """Simplified concept info for question response."""
    model_config = ConfigDict(from_attributes=True)

    concept_id: UUID
    concept_name: str
    relevance: float


class ConceptMappingWithReasoning(BaseModel):
    """Schema for GPT-4 concept mapping output."""
    concept_id: UUID
    concept_name: str
    relevance: float = Field(..., ge=0.0, le=1.0)
    reasoning: str


class QuestionConceptMappingResult(BaseModel):
    """Schema for concept mapping result per question."""
    question_id: UUID
    question_text: str
    mappings: List[ConceptMappingWithReasoning]
    success: bool
    error: Optional[str] = None


# =====================================
# Question Retrieval API schemas
# =====================================

class QuestionListParams(BaseModel):
    """Query parameters for filtering questions."""
    concept_ids: Optional[List[UUID]] = Field(None, description="Filter by concept IDs")
    knowledge_area_id: Optional[str] = Field(None, max_length=50, description="Filter by knowledge area")
    difficulty_min: float = Field(0.0, ge=0.0, le=1.0, description="Minimum difficulty")
    difficulty_max: float = Field(1.0, ge=0.0, le=1.0, description="Maximum difficulty")
    exclude_ids: Optional[List[UUID]] = Field(None, description="Question IDs to exclude")
    limit: int = Field(10, ge=1, le=100, description="Result limit")
    offset: int = Field(0, ge=0, description="Result offset")


class QuestionListResponse(BaseModel):
    """Schema for question list response (excludes correct_answer and explanation)."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    course_id: UUID
    question_text: str
    options: Dict[str, str]  # {"A": "...", "B": "...", "C": "...", "D": "..."}
    knowledge_area_id: str
    difficulty: float
    discrimination: float
    concept_ids: List[UUID] = Field(default_factory=list, description="Mapped concept IDs")


class PaginatedQuestionResponse(BaseModel):
    """Paginated response wrapper for question lists."""
    items: List[QuestionListResponse]
    total: int
    limit: int
    offset: int
    has_more: bool


# =====================================
# Validation/Stats schemas
# =====================================

class ConceptCoverageStats(BaseModel):
    """Statistics about concept coverage from questions."""
    total_concepts: int
    concepts_with_questions: int
    concepts_without_questions: int
    concepts_with_few_questions: int  # < 3 questions
    average_questions_per_concept: float
    concepts_needing_content: List[str]  # Concept names with < 3 questions


class QuestionDistributionStats(BaseModel):
    """Statistics about question distribution."""
    total_questions: int
    by_knowledge_area: Dict[str, int]
    by_difficulty: Dict[str, int]
    questions_with_concepts: int
    questions_without_concepts: int
    average_concepts_per_question: float


class ImportValidationReport(BaseModel):
    """Comprehensive validation report for question import."""
    course_slug: str
    course_id: UUID
    question_stats: QuestionDistributionStats
    concept_stats: ConceptCoverageStats
    warnings: List[str]
    errors: List[str]
    is_valid: bool


# Forward reference resolution
QuestionWithConceptsResponse.model_rebuild()
