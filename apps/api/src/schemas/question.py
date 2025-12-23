"""
Question Pydantic schemas for request/response validation.
Supports multi-course architecture with concept mapping.
"""
from datetime import datetime
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
    difficulty: float = Field(0.0, ge=-3.0, le=3.0, description="IRT b-parameter (-3.0 to +3.0)")
    difficulty_label: str | None = Field(None, max_length=10, description="Human-readable: Easy/Medium/Hard")
    source: str = Field("vendor", max_length=50, description="Question source")
    corpus_reference: str | None = Field(None, max_length=100, description="Source reference")
    # Story 2.15: Secondary tags for filtering/analysis
    perspectives: list[str] | None = Field(None, description="Perspective IDs (e.g., 'agile', 'bi')")
    competencies: list[str] | None = Field(None, description="Competency IDs (e.g., 'analytical', 'communication')")


class QuestionCreate(QuestionBase):
    """Schema for creating a new question."""
    course_id: UUID = Field(..., description="Course UUID this question belongs to")
    discrimination: float = Field(1.0, ge=0.0, le=5.0, description="IRT discrimination (0-5)")
    guess_rate: float = Field(0.25, ge=0.0, le=1.0, description="P(correct | not mastered)")
    slip_rate: float = Field(0.10, ge=0.0, le=1.0, description="P(incorrect | mastered)")


class QuestionUpdate(BaseModel):
    """Schema for updating a question."""
    question_text: str | None = Field(None, min_length=10)
    options: QuestionOptionsSchema | None = None
    correct_answer: str | None = Field(None, pattern="^[ABCD]$")
    explanation: str | None = Field(None, min_length=10)
    knowledge_area_id: str | None = Field(None, max_length=50)
    difficulty: float | None = Field(None, ge=-3.0, le=3.0)
    difficulty_label: str | None = Field(None, max_length=10)
    discrimination: float | None = Field(None, ge=0.0, le=5.0)
    guess_rate: float | None = Field(None, ge=0.0, le=1.0)
    slip_rate: float | None = Field(None, ge=0.0, le=1.0)
    corpus_reference: str | None = Field(None, max_length=100)
    is_active: bool | None = None


class QuestionResponse(QuestionBase):
    """Schema for question response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    course_id: UUID
    difficulty_label: str | None
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
    concepts: list["ConceptMappingResponse"] = Field(default_factory=list)


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
    options: dict[str, str] | None = None  # JSONB format
    option_a: str | None = None  # CSV format
    option_b: str | None = None
    option_c: str | None = None
    option_d: str | None = None

    # Optional fields
    difficulty: str | None = None  # Can be "Easy"/"Medium"/"Hard" or float string
    source: str = Field("vendor", max_length=50)
    corpus_reference: str | None = Field(None, alias="babok_reference")

    @field_validator("correct_answer")
    @classmethod
    def normalize_correct_answer(cls, v: str) -> str:
        return v.upper()

    def get_options_dict(self) -> dict[str, str]:
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
        """Convert difficulty to IRT b-parameter (-3.0 to +3.0)."""
        if self.difficulty is None:
            return 0.0  # Medium difficulty

        # Try parsing as float first (assume IRT scale if numeric)
        try:
            val = float(self.difficulty)
            return max(-3.0, min(3.0, val))
        except ValueError:
            pass

        # Map string difficulty to IRT b-parameter
        difficulty_map = {
            "easy": -1.5,
            "medium": 0.0,
            "hard": 1.5,
        }
        return difficulty_map.get(self.difficulty.lower(), 0.0)

    def get_difficulty_label(self) -> str:
        """Get human-readable difficulty label."""
        if self.difficulty is None:
            return "Medium"

        # If already a string label, normalize it
        if isinstance(self.difficulty, str):
            label = self.difficulty.lower()
            if label in ("easy", "medium", "hard"):
                return label.capitalize()

        # Classify from numeric value
        try:
            val = float(self.difficulty)
            if val < -1.0:
                return "Easy"
            elif val <= 1.0:
                return "Medium"
            else:
                return "Hard"
        except ValueError:
            return "Medium"


class QuestionImportResult(BaseModel):
    """Schema for import result summary."""
    total_parsed: int
    valid_questions: int
    invalid_questions: int
    inserted_questions: int
    skipped_duplicates: int
    errors: list[str]


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
    mappings: list[ConceptMappingWithReasoning]
    success: bool
    error: str | None = None


# =====================================
# Question Retrieval API schemas
# =====================================

class QuestionListParams(BaseModel):
    """Query parameters for filtering questions."""
    concept_ids: list[UUID] | None = Field(None, description="Filter by concept IDs")
    knowledge_area_id: str | None = Field(None, max_length=50, description="Filter by knowledge area")
    difficulty_min: float = Field(-3.0, ge=-3.0, le=3.0, description="Minimum IRT difficulty")
    difficulty_max: float = Field(3.0, ge=-3.0, le=3.0, description="Maximum IRT difficulty")
    difficulty_tier: str | None = Field(None, pattern="^(easy|medium|hard)$", description="Filter by tier: easy/medium/hard")
    exclude_ids: list[UUID] | None = Field(None, description="Question IDs to exclude")
    # Story 2.15: Secondary tag filters
    perspectives: list[str] | None = Field(None, description="Filter by perspective IDs (e.g., 'agile', 'bi')")
    competencies: list[str] | None = Field(None, description="Filter by competency IDs (e.g., 'analytical')")
    limit: int = Field(10, ge=1, le=100, description="Result limit")
    offset: int = Field(0, ge=0, description="Result offset")


class QuestionListResponse(BaseModel):
    """Schema for question list response (excludes correct_answer and explanation)."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    course_id: UUID
    question_text: str
    options: dict[str, str]  # {"A": "...", "B": "...", "C": "...", "D": "..."}
    knowledge_area_id: str
    difficulty: float  # IRT b-parameter (-3.0 to +3.0)
    difficulty_label: str | None = Field(None, description="Human-readable: Easy/Medium/Hard")
    discrimination: float
    concept_ids: list[UUID] = Field(default_factory=list, description="Mapped concept IDs")
    # Story 2.15: Secondary tags
    perspectives: list[str] = Field(default_factory=list, description="Perspective IDs")
    competencies: list[str] = Field(default_factory=list, description="Competency IDs")


class PaginatedQuestionResponse(BaseModel):
    """Paginated response wrapper for question lists."""
    items: list[QuestionListResponse]
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
    concepts_needing_content: list[str]  # Concept names with < 3 questions


class QuestionDistributionStats(BaseModel):
    """Statistics about question distribution."""
    total_questions: int
    by_knowledge_area: dict[str, int]
    by_difficulty: dict[str, int]
    questions_with_concepts: int
    questions_without_concepts: int
    average_concepts_per_question: float


class ImportValidationReport(BaseModel):
    """Comprehensive validation report for question import."""
    course_slug: str
    course_id: UUID
    question_stats: QuestionDistributionStats
    concept_stats: ConceptCoverageStats
    warnings: list[str]
    errors: list[str]
    is_valid: bool


# Forward reference resolution
QuestionWithConceptsResponse.model_rebuild()
