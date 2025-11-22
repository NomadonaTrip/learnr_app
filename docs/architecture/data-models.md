# Data Models

These core data models form the conceptual foundation of LearnR, defining entities shared between frontend and backend. All models use TypeScript interfaces for type safety across the stack.

---

### User

**Purpose:** Represents a learner preparing for CBAP certification, including authentication, onboarding preferences, and exam context.

**Key Attributes:**
- `id`: UUID - Primary key, used in all relationships
- `email`: string - Authentication identifier, unique
- `password_hash`: string - Bcrypt-hashed password (never exposed to frontend)
- `created_at`: timestamp - Account creation date
- `exam_date`: date | null - Target exam date from onboarding
- `target_score`: number | null - Target competency goal (0-100 scale)
- `daily_study_time`: number | null - Commitment in minutes
- `knowledge_level`: string | null - Self-reported baseline
- `motivation`: string | null - Why taking CBAP
- `referral_source`: string | null - How they found LearnR
- `is_admin`: boolean - Admin access flag for support tools
- `dark_mode`: string - Theme preference ("light" | "dark" | "auto")

**TypeScript Interface:**

```typescript
interface User {
  id: string; // UUID
  email: string;
  created_at: string; // ISO 8601
  exam_date: string | null;
  target_score: number | null;
  daily_study_time: number | null;
  knowledge_level: 'Beginner' | 'Intermediate' | 'Advanced' | null;
  motivation: string | null;
  referral_source: 'Search' | 'Friend' | 'Social' | 'Other' | null;
  is_admin: boolean;
  dark_mode: 'light' | 'dark' | 'auto';
}
```

**Relationships:**
- 1:N with QuizSession, Response, Competency, ReadingQueue, SpacedRepetition

---

### Question

**Purpose:** Represents a CBAP exam question with metadata for adaptive selection and semantic search.

**Key Attributes:**
- `id`: UUID
- `text`: string - Question text
- `option_a/b/c/d`: string - Answer choices
- `correct_answer`: string - Correct option ("A" | "B" | "C" | "D")
- `explanation`: string - Detailed explanation
- `knowledge_area`: KnowledgeArea - One of 6 CBAP KAs
- `difficulty`: number - 1-5 scale
- `concept_tags`: string[] - Specific BABOK concepts tested
- `source`: string - "vendor" | "llm_generated"
- `babok_reference`: string | null
- `embedding_vector`: number[] - 3072-dim (stored in Qdrant)
- `times_seen`: number
- `avg_correct_rate`: number

**TypeScript Interface:**

```typescript
type KnowledgeArea =
  | 'Business Analysis Planning and Monitoring'
  | 'Elicitation and Collaboration'
  | 'Requirements Life Cycle Management'
  | 'Strategy Analysis'
  | 'Requirements Analysis and Design Definition'
  | 'Solution Evaluation';

interface Question {
  id: string;
  text: string;
  option_a: string;
  option_b: string;
  option_c: string;
  option_d: string;
  correct_answer: 'A' | 'B' | 'C' | 'D';
  explanation: string;
  knowledge_area: KnowledgeArea;
  difficulty: 1 | 2 | 3 | 4 | 5;
  concept_tags: string[];
  source: 'vendor' | 'llm_generated';
  babok_reference: string | null;
  times_seen: number;
  avg_correct_rate: number;
}
```

---

### QuizSession

**Purpose:** Tracks a single quiz session, grouping responses together for analytics and post-session review.

**TypeScript Interface:**

```typescript
interface QuizSession {
  id: string;
  user_id: string;
  started_at: string;
  ended_at: string | null;
  session_type: 'diagnostic' | 'mixed' | 'new_content' | 'review_only';
  total_questions: number;
  correct_count: number;
  is_paused: boolean;
}
```

---

### Response

**Purpose:** Records a single user answer to a question, used for competency tracking and spaced repetition.

**TypeScript Interface:**

```typescript
interface Response {
  id: string;
  user_id: string;
  session_id: string;
  question_id: string;
  selected_answer: 'A' | 'B' | 'C' | 'D';
  is_correct: boolean;
  time_taken_seconds: number;
  answered_at: string;
  is_review: boolean;
}
```

---

### Competency

**Purpose:** Tracks user's competency score for each of the 6 CBAP knowledge areas using simplified IRT.

**TypeScript Interface:**

```typescript
interface Competency {
  id: string;
  user_id: string;
  knowledge_area: KnowledgeArea;
  score: number; // 0-100
  confidence: number; // 0-1
  last_updated: string;
  questions_answered: number;
  recent_accuracy: number; // 0-1
}
```

---

### ReadingQueue

**Purpose:** Manages asynchronous reading library - BABOK chunks recommended to user based on gaps and incorrect answers.

**TypeScript Interface:**

```typescript
interface ReadingQueueItem {
  id: string;
  user_id: string;
  chunk_id: string;
  triggered_by_question_id: string | null;
  priority: 'High' | 'Medium' | 'Low';
  status: 'unread' | 'reading' | 'completed' | 'dismissed';
  added_at: string;
  times_opened: number;
  total_reading_time_seconds: number;
  completed_at: string | null;
  chunk?: ReadingChunk;
}
```

---

### ReadingChunk

**Purpose:** BABOK v3 content pre-chunked and embedded for semantic search and reading recommendations.

**TypeScript Interface:**

```typescript
interface ReadingChunk {
  id: string;
  title: string;
  content: string; // Markdown
  babok_section: string;
  knowledge_area: KnowledgeArea;
  concept_tags: string[];
  estimated_read_time_minutes: number;
}
```

---

### SpacedRepetition

**Purpose:** Tracks spaced repetition schedule for concept mastery using SM-2 algorithm.

**TypeScript Interface:**

```typescript
interface SpacedRepetition {
  id: string;
  user_id: string;
  concept_tag: string;
  knowledge_area: KnowledgeArea;
  easiness_factor: number; // 1.3-2.5
  interval_days: number;
  next_review_date: string;
  repetitions: number;
  last_reviewed: string | null;
}
```

---

### SessionReview

**Purpose:** Tracks post-session review metadata - immediate reinforcement of incorrect answers.

**TypeScript Interface:**

```typescript
interface SessionReview {
  id: string;
  session_id: string;
  user_id: string;
  started_at: string;
  completed_at: string | null;
  original_correct_count: number;
  original_total: number;
  review_total: number;
  reinforcement_count: number;
}
```

---

### ReviewAttempt

**Purpose:** Records user's re-answer during post-session review for each incorrect question.

**TypeScript Interface:**

```typescript
interface ReviewAttempt {
  id: string;
  session_review_id: string;
  question_id: string;
  original_response_id: string;
  review_answer: 'A' | 'B' | 'C' | 'D';
  is_correct_on_review: boolean;
  reviewed_at: string;
}
```

---
