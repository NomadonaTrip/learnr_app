# Database Schema Summary

This section provides complete SQL DDL statements for all LearnR database tables. All tables use PostgreSQL 15+.

**Schema Design Principles:**
- UUIDs for all primary keys (distributed-system ready, avoid sequential ID leakage)
- Timestamps: `created_at`, `updated_at` on all tables (audit trail)
- Foreign key constraints with CASCADE deletes where appropriate (user deletion cleanup)
- Indexes on frequently queried fields (user_id, session_id, KA filters, reading_status)
- JSONB columns for flexible metadata (PostHog properties, admin action details)

### Core Tables (v2.0 Foundation)

#### Table: `users`
```sql
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE, -- v2.2: Admin role flag
    theme_preference VARCHAR(10) DEFAULT 'auto', -- v2.2: 'light' | 'dark' | 'auto'
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_admin ON users(is_admin) WHERE is_admin = TRUE;
```

#### Table: `onboarding_data`
```sql
CREATE TABLE onboarding_data (
    onboarding_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    referral_source VARCHAR(50), -- 'search' | 'referral' | 'social' | 'other'
    certification VARCHAR(50) NOT NULL, -- 'CBAP' for MVP
    motivation VARCHAR(100), -- 'career_advancement' | 'salary' | 'credibility' | etc
    exam_date DATE NOT NULL,
    knowledge_level VARCHAR(20), -- 'beginner' | 'intermediate' | 'advanced'
    target_score VARCHAR(10), -- 'pass' | 'high_pass' (70% | 80% | 90%)
    daily_commitment VARCHAR(20), -- '30-60min' | '1-2hrs' | '2+hrs'
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_onboarding_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX idx_onboarding_user ON onboarding_data(user_id);
```

#### Table: `questions`
```sql
CREATE TABLE questions (
    question_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_text TEXT NOT NULL,
    option_a TEXT NOT NULL,
    option_b TEXT NOT NULL,
    option_c TEXT NOT NULL,
    option_d TEXT NOT NULL,
    correct_answer CHAR(1) NOT NULL CHECK (correct_answer IN ('A', 'B', 'C', 'D')),
    explanation TEXT NOT NULL, -- Max 200 characters (enforced in application)
    ka_id UUID NOT NULL REFERENCES knowledge_areas(ka_id),
    difficulty DECIMAL(3,2) NOT NULL CHECK (difficulty >= 0 AND difficulty <= 1),
    concept_tags JSONB, -- Array of concept tags for semantic search
    source VARCHAR(50), -- 'vendor' | 'llm_generated'
    babok_section VARCHAR(20), -- e.g., "3.2.1"
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_questions_ka ON questions(ka_id);
CREATE INDEX idx_questions_difficulty ON questions(difficulty);
CREATE INDEX idx_questions_concept_tags ON questions USING GIN(concept_tags);
```

#### Table: `content_chunks`
```sql
CREATE TABLE content_chunks (
    chunk_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ka_id UUID NOT NULL REFERENCES knowledge_areas(ka_id),
    section_ref VARCHAR(20), -- BABOK section reference (e.g., "3.2.1")
    title VARCHAR(255),
    text_content TEXT NOT NULL, -- 200-500 tokens per chunk
    word_count INT NOT NULL,
    difficulty VARCHAR(20), -- 'easy' | 'medium' | 'hard'
    concept_tags JSONB, -- Array of concept tags
    embedding VECTOR(1536), -- OpenAI text-embedding-3-large dimensions
    page_reference INT, -- Page number in BABOK v3
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_chunks_ka ON content_chunks(ka_id);
CREATE INDEX idx_chunks_embedding ON content_chunks USING ivfflat(embedding vector_cosine_ops);
```

#### Table: `knowledge_areas`
```sql
CREATE TABLE knowledge_areas (
    ka_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ka_name VARCHAR(255) NOT NULL UNIQUE,
    ka_abbreviation VARCHAR(10), -- e.g., "BAPM"
    description TEXT,
    display_order INT NOT NULL
);

-- Pre-populate with 6 CBAP Knowledge Areas
INSERT INTO knowledge_areas (ka_name, ka_abbreviation, display_order) VALUES
('Business Analysis Planning and Monitoring', 'BAPM', 1),
('Elicitation and Collaboration', 'EC', 2),
('Requirements Life Cycle Management', 'RLCM', 3),
('Strategy Analysis', 'SA', 4),
('Requirements Analysis and Design Definition', 'RADD', 5),
('Solution Evaluation', 'SE', 6);
```

#### Table: `competency_tracking`
```sql
CREATE TABLE competency_tracking (
    competency_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    ka_id UUID NOT NULL REFERENCES knowledge_areas(ka_id),
    competency_score DECIMAL(4,2) NOT NULL CHECK (competency_score >= 0 AND competency_score <= 100),
    last_updated TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_user_ka UNIQUE (user_id, ka_id)
);

CREATE INDEX idx_competency_user ON competency_tracking(user_id);
CREATE INDEX idx_competency_ka ON competency_tracking(ka_id);
```

#### Table: `quiz_sessions`
```sql
CREATE TABLE quiz_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    session_type VARCHAR(20) NOT NULL, -- 'diagnostic' | 'adaptive' | 'review' | 'mixed'
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMP,
    total_questions INT DEFAULT 0,
    correct_count INT DEFAULT 0,
    session_status VARCHAR(20) DEFAULT 'active' -- 'active' | 'completed' | 'abandoned'
);

CREATE INDEX idx_sessions_user ON quiz_sessions(user_id);
CREATE INDEX idx_sessions_status ON quiz_sessions(session_status);
```

#### Table: `quiz_responses`
```sql
CREATE TABLE quiz_responses (
    response_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES quiz_sessions(session_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    question_id UUID NOT NULL REFERENCES questions(question_id),
    selected_answer CHAR(1) NOT NULL CHECK (selected_answer IN ('A', 'B', 'C', 'D')),
    is_correct BOOLEAN NOT NULL,
    time_spent_seconds INT,
    answered_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_responses_session ON quiz_responses(session_id);
CREATE INDEX idx_responses_user ON quiz_responses(user_id);
CREATE INDEX idx_responses_question ON quiz_responses(question_id);
```

### v2.1 New Tables (Reading Library & Post-Session Review)

#### Table: `reading_queue` (Epic 5)
```sql
CREATE TABLE reading_queue (
    queue_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    chunk_id UUID NOT NULL REFERENCES content_chunks(chunk_id) ON DELETE CASCADE,

    -- Context: Why was this recommended?
    question_id UUID REFERENCES questions(question_id) ON DELETE SET NULL,
    session_id UUID REFERENCES quiz_sessions(session_id) ON DELETE SET NULL,
    was_incorrect BOOLEAN DEFAULT TRUE,

    -- Priority & Relevance
    relevance_score DECIMAL(3,2) NOT NULL CHECK (relevance_score >= 0 AND relevance_score <= 1),
    priority VARCHAR(20) DEFAULT 'medium' CHECK (priority IN ('high', 'medium', 'low')),
    ka_id UUID REFERENCES knowledge_areas(ka_id) ON DELETE SET NULL,

    -- Reading State
    reading_status VARCHAR(20) DEFAULT 'unread' CHECK (reading_status IN ('unread', 'reading', 'completed', 'dismissed')),

    -- Engagement Tracking
    times_opened INT DEFAULT 0,
    total_reading_time_seconds INT DEFAULT 0,
    first_opened_at TIMESTAMP,
    completed_at TIMESTAMP,
    dismissed_at TIMESTAMP,

    -- Timestamps
    added_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_reading_queue_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT fk_reading_queue_chunk FOREIGN KEY (chunk_id) REFERENCES content_chunks(chunk_id) ON DELETE CASCADE,
    CONSTRAINT unique_user_chunk_queue UNIQUE (user_id, chunk_id)
);

CREATE INDEX idx_reading_queue_user_status ON reading_queue(user_id, reading_status);
CREATE INDEX idx_reading_queue_user_unread ON reading_queue(user_id, reading_status) WHERE reading_status = 'unread';
CREATE INDEX idx_reading_queue_ka ON reading_queue(ka_id);
CREATE INDEX idx_reading_queue_priority ON reading_queue(user_id, priority, reading_status);
```

**Field Explanations:**
- `relevance_score`: Semantic similarity between question and chunk (0.00-1.00)
- `priority`: Calculated based on user competency gap, mistake frequency, and recency
- `reading_status`: User interaction state (unread → reading → completed/dismissed)
- `times_opened`: Tracks if user revisits material (engagement metric)

#### Table: `session_reviews` (Epic 4)
```sql
CREATE TABLE session_reviews (
    review_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES quiz_sessions(session_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    review_status VARCHAR(20) DEFAULT 'pending' CHECK (review_status IN ('pending', 'in_progress', 'completed', 'skipped')),
    items_to_review INT NOT NULL,
    items_reviewed INT DEFAULT 0,
    improvement_rate DECIMAL(4,2), -- % of incorrect → correct (0.00-1.00)
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_session_reviews_user ON session_reviews(user_id);
CREATE INDEX idx_session_reviews_session ON session_reviews(session_id);
CREATE INDEX idx_session_reviews_status ON session_reviews(review_status);
```

#### Table: `review_attempts` (Epic 4)
```sql
CREATE TABLE review_attempts (
    attempt_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    review_id UUID NOT NULL REFERENCES session_reviews(review_id) ON DELETE CASCADE,
    question_id UUID NOT NULL REFERENCES questions(question_id),
    original_answer CHAR(1) NOT NULL CHECK (original_answer IN ('A', 'B', 'C', 'D')),
    review_answer CHAR(1) NOT NULL CHECK (review_answer IN ('A', 'B', 'C', 'D')),
    now_correct BOOLEAN NOT NULL,
    attempt_number INT DEFAULT 1,
    time_spent_seconds INT,
    answered_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_review_attempts_review ON review_attempts(review_id);
CREATE INDEX idx_review_attempts_question ON review_attempts(question_id);
```

### v2.2 New Tables (Admin & Analytics)

#### Table: `admin_audit_log` (Epic 8)
```sql
CREATE TABLE admin_audit_log (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    admin_user_id UUID NOT NULL REFERENCES users(user_id),
    action_type VARCHAR(50) NOT NULL, -- 'impersonation_started' | 'impersonation_ended' | 'user_search' | etc
    target_user_id UUID REFERENCES users(user_id) ON DELETE SET NULL,
    metadata JSONB, -- {duration_seconds, ip_address, user_agent, etc}
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_admin ON admin_audit_log(admin_user_id);
CREATE INDEX idx_audit_target ON admin_audit_log(target_user_id);
CREATE INDEX idx_audit_action ON admin_audit_log(action_type);
CREATE INDEX idx_audit_timestamp ON admin_audit_log(created_at DESC);
```

### Spaced Repetition Tables (Epic 7)

#### Table: `concept_mastery`
```sql
CREATE TABLE concept_mastery (
    mastery_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    concept_tag VARCHAR(100) NOT NULL,
    ka_id UUID REFERENCES knowledge_areas(ka_id),
    mastery_level INT DEFAULT 0 CHECK (mastery_level >= 0 AND mastery_level <= 5),
    last_reviewed_at TIMESTAMP,
    next_review_at TIMESTAMP,
    review_count INT DEFAULT 0,
    correct_streak INT DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_user_concept UNIQUE (user_id, concept_tag)
);

CREATE INDEX idx_mastery_user ON concept_mastery(user_id);
CREATE INDEX idx_mastery_next_review ON concept_mastery(user_id, next_review_at);
CREATE INDEX idx_mastery_ka ON concept_mastery(ka_id);
```

#### Table: `spaced_repetition_schedule`
```sql
CREATE TABLE spaced_repetition_schedule (
    schedule_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    question_id UUID NOT NULL REFERENCES questions(question_id),
    concept_tag VARCHAR(100) NOT NULL,
    next_review_date DATE NOT NULL,
    review_interval_days INT NOT NULL, -- 1, 3, 7, 14 (SM-2 adapted)
    ease_factor DECIMAL(3,2) DEFAULT 2.50,
    consecutive_correct INT DEFAULT 0,
    last_reviewed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_user_question_srs UNIQUE (user_id, question_id)
);

CREATE INDEX idx_srs_user_date ON spaced_repetition_schedule(user_id, next_review_date);
CREATE INDEX idx_srs_concept ON spaced_repetition_schedule(concept_tag);
```

### Engagement & Feedback Tables

#### Table: `explanation_feedback`
```sql
CREATE TABLE explanation_feedback (
    feedback_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    question_id UUID NOT NULL REFERENCES questions(question_id),
    helpful BOOLEAN NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_explanation_feedback_question ON explanation_feedback(question_id);
```

#### Table: `question_reports`
```sql
CREATE TABLE question_reports (
    report_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    question_id UUID NOT NULL REFERENCES questions(question_id),
    issue_type VARCHAR(50) NOT NULL, -- 'incorrect_question' | 'unclear_explanation' | 'typo' | etc
    description TEXT,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'reviewing', 'resolved', 'dismissed')),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_reports_status ON question_reports(status);
CREATE INDEX idx_reports_question ON question_reports(question_id);
```

---
