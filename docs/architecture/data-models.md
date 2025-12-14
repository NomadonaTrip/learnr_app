# Data Models

## Status

**ALIGNED** with BKT Architecture (bkt-architecture.md) and Multi-Course Architecture (multi-course-architecture.md)

---

These core data models form the conceptual foundation of LearnR, defining entities shared between frontend and backend. All models use TypeScript interfaces for type safety across the stack.

---

## Multi-Course Foundation

### Course

**Purpose:** Represents a certification course (CBAP, PSM1, CFA) with its own knowledge areas, concepts, questions, and configuration. Courses are self-describing and contain all metadata needed for the BKT engine.

**Key Attributes:**
- `id`: UUID - Primary key
- `slug`: string - URL-safe identifier (e.g., "cbap", "psm1")
- `name`: string - Display name
- `description`: string - Marketing description
- `corpus_name`: string - Source material name (e.g., "BABOK v3")
- `knowledge_areas`: JSONB - Array of KA definitions (dynamic, not enum)
- `mastery_threshold`: number - P(mastery) threshold for "mastered" (default 0.8)
- `gap_threshold`: number - P(mastery) threshold for "gap" (default 0.5)
- `confidence_threshold`: number - Confidence threshold for classification (default 0.7)
- `default_diagnostic_count`: number - Questions in initial diagnostic
- `is_active`: boolean - Course available for enrollment
- `is_public`: boolean - Visible in course catalog

**TypeScript Interface:**

```typescript
interface KnowledgeAreaConfig {
  id: string;            // 'ba-planning', 'elicitation'
  name: string;          // Full display name
  short_name: string;    // Abbreviated for UI
  display_order: number;
  color: string;         // Hex color for progress bars
  icon?: string;         // Icon identifier
}

interface Course {
  id: string;
  slug: string;
  name: string;
  description: string;
  corpus_name: string;
  knowledge_areas: KnowledgeAreaConfig[];
  mastery_threshold: number;
  gap_threshold: number;
  confidence_threshold: number;
  default_diagnostic_count: number;
  is_active: boolean;
  is_public: boolean;
  icon_url: string | null;
  color_hex: string | null;
  created_at: string;
  updated_at: string;
}
```

**Relationships:**
- 1:N with Concept
- 1:N with Question
- 1:N with ReadingChunk
- 1:N with Enrollment

---

### Enrollment

**Purpose:** Represents a user's enrollment in a specific course. Tracks course-specific settings (exam date, target score) and progress. Replaces per-user exam settings for multi-course support.

**Key Attributes:**
- `id`: UUID - Primary key
- `user_id`: UUID - Foreign key to User
- `course_id`: UUID - Foreign key to Course
- `exam_date`: date | null - Target exam date for this course
- `target_score`: number | null - Target readiness goal
- `daily_study_time`: number | null - Minutes per day commitment
- `enrolled_at`: timestamp - When user enrolled
- `last_activity_at`: timestamp | null - Last quiz/reading activity
- `status`: string - active, paused, completed, archived
- `completion_percentage`: number - Progress through course (0-100)

**TypeScript Interface:**

```typescript
type EnrollmentStatus = 'active' | 'paused' | 'completed' | 'archived';

interface Enrollment {
  id: string;
  user_id: string;
  course_id: string;
  exam_date: string | null;
  target_score: number | null;
  daily_study_time: number | null;
  enrolled_at: string;
  last_activity_at: string | null;
  status: EnrollmentStatus;
  completion_percentage: number;
  created_at: string;
  updated_at: string;

  // Expanded relations (when fetched with course)
  course?: Course;
}
```

**Relationships:**
- N:1 with User
- N:1 with Course
- 1:N with QuizSession
- 1:N with ReadingQueue
- UNIQUE constraint on (user_id, course_id)

---

### User

**Purpose:** Represents a learner account with authentication and global preferences. Course-specific settings (exam_date, target_score) are now stored in Enrollment for multi-course support.

**Key Attributes:**
- `id`: UUID - Primary key, used in all relationships
- `email`: string - Authentication identifier, unique
- `password_hash`: string - Bcrypt-hashed password (never exposed to frontend)
- `created_at`: timestamp - Account creation date
- `knowledge_level`: string | null - Self-reported baseline (onboarding)
- `motivation`: string | null - Why using LearnR
- `referral_source`: string | null - How they found LearnR
- `is_admin`: boolean - Admin access flag for support tools
- `dark_mode`: string - Theme preference ("light" | "dark" | "auto")

**Deprecated (moved to Enrollment):**
- ~~`exam_date`~~ → Now per-enrollment
- ~~`target_score`~~ → Now per-enrollment
- ~~`daily_study_time`~~ → Now per-enrollment

**TypeScript Interface:**

```typescript
interface User {
  id: string; // UUID
  email: string;
  created_at: string; // ISO 8601
  knowledge_level: 'Beginner' | 'Intermediate' | 'Advanced' | null;
  motivation: string | null;
  referral_source: 'Search' | 'Friend' | 'Social' | 'Other' | null;
  is_admin: boolean;
  dark_mode: 'light' | 'dark' | 'auto';

  // Expanded relations
  enrollments?: Enrollment[];
}
```

**Relationships:**
- 1:N with Enrollment (user can enroll in multiple courses)
- 1:N with BeliefState (via concept → course)
- 1:N with Response

---

### Concept

**Purpose:** Represents a discrete knowledge unit within a course's corpus. LearnR tracks 500-1500 concepts per course (vs. 6 Knowledge Areas in traditional apps). This granularity enables precise gap identification.

**Key Attributes:**
- `id`: UUID - Primary key
- `course_id`: UUID - Foreign key to Course (concepts are course-scoped)
- `name`: string - Concept name (e.g., "Stakeholder Analysis Techniques")
- `description`: string - Brief explanation
- `corpus_section_ref`: string - Reference to source material section (e.g., "3.2.1" for BABOK)
- `knowledge_area_id`: string - References course.knowledge_areas[].id (dynamic, not enum)
- `difficulty_estimate`: number - 0.0-1.0 estimated difficulty
- `prerequisite_depth`: number - Distance from root concepts in DAG

**TypeScript Interface:**

```typescript
interface Concept {
  id: string;
  course_id: string;
  name: string;
  description: string;
  corpus_section_ref: string;        // Was babok_section_ref
  knowledge_area_id: string;         // Dynamic reference to course KA config
  difficulty_estimate: number;       // 0.0-1.0
  prerequisite_depth: number;
  created_at: string;
  updated_at: string;

  // Computed/joined
  knowledge_area_name?: string;      // From course.knowledge_areas lookup
}
```

**Relationships:**
- N:1 with Course
- N:M with Question (via question_concepts)
- N:M with self (via concept_prerequisites DAG)
- 1:N with BeliefState

---

### ConceptPrerequisite

**Purpose:** Defines prerequisite relationships between concepts as a Directed Acyclic Graph (DAG). Used for prerequisite propagation during belief updates.

**TypeScript Interface:**

```typescript
interface ConceptPrerequisite {
  concept_id: string;
  prerequisite_concept_id: string;
  strength: number; // 0.0-1.0, how strongly prerequisite is required
}
```

---

### BeliefState

**Purpose:** Tracks a user's mastery probability for a specific concept using Beta distribution parameters. This is the core BKT data structure, replacing the legacy Competency model.

**Key Attributes:**
- `id`: UUID - Primary key
- `user_id`: UUID - Foreign key to User
- `concept_id`: UUID - Foreign key to Concept
- `alpha`: number - Beta distribution α parameter (mastery evidence)
- `beta`: number - Beta distribution β parameter (non-mastery evidence)
- `last_response_at`: timestamp - For decay/recency calculations
- `response_count`: number - Questions answered for this concept

**Derived Properties (computed, not stored):**
- `mean`: α / (α + β) - Point estimate of mastery probability
- `confidence`: (α + β) / (α + β + 10) - How certain we are in estimate
- `entropy`: Beta distribution entropy - Uncertainty measure
- `status`: 'mastered' | 'gap' | 'uncertain' - Classification

**TypeScript Interface:**

```typescript
interface BeliefState {
  id: string;
  user_id: string;
  concept_id: string;
  alpha: number;
  beta: number;
  last_response_at: string | null;
  response_count: number;
  created_at: string;
  updated_at: string;

  // Computed properties (frontend calculates these)
  mean?: number;
  confidence?: number;
  status?: 'mastered' | 'gap' | 'borderline' | 'uncertain';
}

// Classification thresholds
const MASTERY_THRESHOLD = 0.8;   // P(mastery) > 0.8 = mastered
const GAP_THRESHOLD = 0.5;       // P(mastery) < 0.5 = gap
const CONFIDENCE_THRESHOLD = 0.7; // confidence > 0.7 = classified
```

**Relationships:**
- N:1 with User
- N:1 with Concept
- UNIQUE constraint on (user_id, concept_id)

---

### ConceptStatus

**Purpose:** Represents the classification of a concept for a user, derived from BeliefState. Used in coverage reports and gap analysis.

**TypeScript Interface:**

```typescript
interface ConceptStatus {
  concept_id: string;
  concept_name: string;
  knowledge_area: KnowledgeArea;
  status: 'mastered' | 'gap' | 'borderline' | 'uncertain';
  probability: number; // mean = α / (α + β)
  confidence: number;  // (α + β) / (α + β + 10)
}
```

---

### CoverageReport

**Purpose:** Aggregated view of a user's corpus coverage, showing mastered concepts, gaps, and uncertain areas.

**TypeScript Interface:**

```typescript
interface CoverageSummary {
  total_concepts: number;
  mastered_count: number;
  gap_count: number;
  uncertain_count: number;
  coverage_percentage: number; // mastered / total
  confidence_percentage: number; // (mastered + gaps) / total
  estimated_questions_remaining: number;
}

interface CoverageReport extends CoverageSummary {
  mastered: ConceptStatus[];
  gaps: ConceptStatus[];
  uncertain: ConceptStatus[];
}

interface KnowledgeAreaCoverage {
  knowledge_area: KnowledgeArea;
  total_concepts: number;
  mastered_count: number;
  gap_count: number;
  readiness_score: number; // 0-100, for dashboard display
}
```

---

### Question

**Purpose:** Represents an exam question with BKT parameters for adaptive selection and semantic search. Questions belong to a specific course.

**Key Attributes:**
- `id`: UUID
- `course_id`: UUID - Foreign key to Course (questions are course-scoped)
- `text`: string - Question text
- `options`: JSONB - Answer choices {A, B, C, D}
- `correct_answer`: string - Correct option ("A" | "B" | "C" | "D")
- `explanation`: string - Detailed explanation
- `knowledge_area_id`: string - References course.knowledge_areas[].id
- `difficulty`: number - 0.0-1.0 IRT difficulty parameter
- `discrimination`: number - IRT discrimination parameter
- `guess_rate`: number - P(correct | not mastered), default 0.25
- `slip_rate`: number - P(incorrect | mastered), default 0.10
- `times_asked`: number - For calibration
- `times_correct`: number - For calibration
- `source`: string - "vendor" | "llm_generated"
- `corpus_reference`: string | null - Reference to source material

**TypeScript Interface:**

```typescript
// NOTE: KnowledgeArea is now dynamic, loaded from course.knowledge_areas
// No more hardcoded enum - use knowledge_area_id string

interface Question {
  id: string;
  course_id: string;
  text: string;
  options: {
    A: string;
    B: string;
    C: string;
    D: string;
  };
  correct_answer: 'A' | 'B' | 'C' | 'D';
  explanation: string;
  knowledge_area_id: string;    // Dynamic reference to course KA
  difficulty: number;           // 0.0-1.0
  discrimination: number;
  guess_rate: number;           // default 0.25
  slip_rate: number;            // default 0.10
  times_asked: number;
  times_correct: number;
  source: 'vendor' | 'llm_generated';
  corpus_reference: string | null;   // Was babok_reference
  is_active: boolean;
  created_at: string;
  updated_at: string;

  // Computed/joined
  knowledge_area_name?: string;
  concept_ids?: string[];
}
```

**Relationships:**
- N:1 with Course
- N:M with Concept (via question_concepts)
- 1:N with Response

---

### QuestionConcept

**Purpose:** Junction table linking questions to the concepts they test. Each question tests 1-5 concepts.

**TypeScript Interface:**

```typescript
interface QuestionConcept {
  question_id: string;
  concept_id: string;
  relevance: number; // 0.0-1.0, how directly question tests concept
}
```

---

### QuizSession

**Purpose:** Tracks a single quiz session, grouping responses together for analytics and post-session review. Sessions are tied to a specific enrollment for multi-course support.

**TypeScript Interface:**

```typescript
interface QuizSession {
  id: string;
  user_id: string;
  enrollment_id: string;         // Links session to specific course enrollment
  started_at: string;
  ended_at: string | null;
  session_type: 'diagnostic' | 'adaptive' | 'focused' | 'review';
  question_strategy: 'max_info_gain' | 'max_uncertainty' | 'prerequisite_first' | 'balanced';
  knowledge_area_filter: string | null;  // For focused sessions
  total_questions: number;
  correct_count: number;
  is_paused: boolean;
  version: number;               // Optimistic locking

  // Expanded relations
  enrollment?: Enrollment;
}
```

**Relationships:**
- N:1 with User
- N:1 with Enrollment
- 1:N with Response

---

### Response

**Purpose:** Records a single user answer to a question, including belief updates made.

**TypeScript Interface:**

```typescript
interface Response {
  id: string;
  user_id: string;
  session_id: string;
  question_id: string;
  selected_answer: 'A' | 'B' | 'C' | 'D';
  is_correct: boolean;
  time_taken_ms: number;
  answered_at: string;
  request_id: string; // Idempotency key (client-generated UUID)
  belief_updates: BeliefUpdate[]; // Snapshot of updates made
}

interface BeliefUpdate {
  concept_id: string;
  concept_name: string;
  old_alpha: number;
  old_beta: number;
  new_alpha: number;
  new_beta: number;
}
```

---

### ReadingQueue

**Purpose:** Manages asynchronous reading library - content chunks recommended to user based on gaps and incorrect answers. Queue is scoped to enrollment for multi-course support.

**TypeScript Interface:**

```typescript
interface ReadingQueueItem {
  id: string;
  user_id: string;
  enrollment_id: string;             // Links to specific course enrollment
  chunk_id: string;
  triggered_by_question_id: string | null;
  triggered_by_concept_id: string | null;
  priority: 'High' | 'Medium' | 'Low';
  status: 'unread' | 'reading' | 'completed' | 'dismissed';
  added_at: string;
  times_opened: number;
  total_reading_time_seconds: number;
  completed_at: string | null;
  chunk?: ReadingChunk;
}
```

**Relationships:**
- N:1 with User
- N:1 with Enrollment
- N:1 with ReadingChunk

---

### ReadingChunk

**Purpose:** Course corpus content pre-chunked and embedded for semantic search and reading recommendations. Chunks belong to a specific course.

**TypeScript Interface:**

```typescript
interface ReadingChunk {
  id: string;
  course_id: string;                 // Chunks are course-scoped
  title: string;
  content: string;                   // Markdown
  corpus_section: string;            // Was babok_section
  knowledge_area_id: string;         // Dynamic reference to course KA
  concept_ids: string[];             // Concepts this chunk covers
  estimated_read_time_minutes: number;
  created_at: string;
  updated_at: string;
}
```

**Relationships:**
- N:1 with Course
- N:M with Concept (via chunk_concepts)
- 1:N with ReadingQueue

---

### AnswerResponse

**Purpose:** API response after submitting an answer, includes feedback and belief updates.

**TypeScript Interface:**

```typescript
interface AnswerResponse {
  is_correct: boolean;
  correct_answer: 'A' | 'B' | 'C' | 'D';
  explanation: string;
  belief_updates: BeliefUpdate[];
  concepts_affected: number;
}
```

---

## Legacy Models (Deprecated)

The following models are **deprecated** and replaced by BKT equivalents:

| Legacy Model | Replaced By | Notes |
|--------------|-------------|-------|
| `Competency` | `BeliefState` | 6 KA scores → 500-1500 concept beliefs |
| `SpacedRepetition` | BKT recency decay | SM-2 → Bayesian temporal decay |

---

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-12-08 | 3.0 | Multi-Course Architecture - added Course, Enrollment models; added course_id to Concept, Question, ReadingChunk; added enrollment_id to QuizSession, ReadingQueue; dynamic KnowledgeArea (no more enum) | Winston (Architect) |
| 2025-12-03 | 2.0 | Aligned with BKT Architecture - added Concept, BeliefState, ConceptStatus, CoverageReport; deprecated Competency | Winston (Architect) |
| 2025-11-01 | 1.0 | Initial data models | Original |
