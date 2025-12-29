# Database Schema

## Status

**ALIGNED** with BKT Architecture (bkt-architecture.md) and Multi-Course Architecture (multi-course-architecture.md)

---

### PostgreSQL Schema

**Tables:**

#### Multi-Course Foundation Tables
- `courses` - Certification courses with dynamic knowledge area configuration
- `enrollments` - User enrollments in courses (exam_date, target_score per enrollment)

#### Core User Tables
- `users` - User accounts with authentication and global preferences

#### BKT Knowledge Graph Tables (Course-Scoped)
- `concepts` - Discrete knowledge units per course (500-1500 per course)
- `concept_prerequisites` - DAG edges defining prerequisite relationships
- `belief_states` - User mastery beliefs per concept (Beta distribution parameters)

#### Question Bank Tables (Course-Scoped)
- `questions` - Exam questions with BKT parameters (course_id FK)
- `question_concepts` - Junction table linking questions to concepts tested

#### Quiz Session Tables (Enrollment-Scoped)
- `quiz_sessions` - Quiz session tracking with enrollment_id
- `responses` - User answers with belief update snapshots

#### Reading Library Tables (Course-Scoped)
- `reading_chunks` - Corpus content chunks per course (vectors in Qdrant)
- `reading_queue` - Asynchronous reading recommendations per enrollment

#### Admin Tables
- `admin_audit_log` - Admin operations audit trail

---

### Table Definitions

#### courses
```sql
CREATE TABLE courses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    corpus_name VARCHAR(100),
    knowledge_areas JSONB NOT NULL,
    default_diagnostic_count INTEGER DEFAULT 12,
    mastery_threshold FLOAT DEFAULT 0.8,
    gap_threshold FLOAT DEFAULT 0.5,
    confidence_threshold FLOAT DEFAULT 0.7,
    icon_url VARCHAR(500),
    color_hex VARCHAR(7),
    is_active BOOLEAN DEFAULT TRUE,
    is_public BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_courses_slug ON courses(slug);
CREATE INDEX idx_courses_active ON courses(is_active) WHERE is_active = TRUE;

-- Seed CBAP as initial course
INSERT INTO courses (slug, name, corpus_name, knowledge_areas)
VALUES (
    'cbap',
    'CBAP Certification Prep',
    'BABOK v3',
    '[
        {"id": "ba-planning", "name": "Business Analysis Planning and Monitoring", "short_name": "BA Planning", "display_order": 1, "color": "#3B82F6"},
        {"id": "elicitation", "name": "Elicitation and Collaboration", "short_name": "Elicitation", "display_order": 2, "color": "#10B981"},
        {"id": "rlcm", "name": "Requirements Life Cycle Management", "short_name": "RLCM", "display_order": 3, "color": "#F59E0B"},
        {"id": "strategy", "name": "Strategy Analysis", "short_name": "Strategy", "display_order": 4, "color": "#EF4444"},
        {"id": "radd", "name": "Requirements Analysis and Design Definition", "short_name": "RADD", "display_order": 5, "color": "#8B5CF6"},
        {"id": "solution-eval", "name": "Solution Evaluation", "short_name": "Solution Eval", "display_order": 6, "color": "#EC4899"}
    ]'::JSONB
);
```

#### enrollments
```sql
CREATE TABLE enrollments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    exam_date DATE,
    target_score INTEGER,
    daily_study_time INTEGER,
    enrolled_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_activity_at TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    completion_percentage FLOAT NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, course_id),
    CHECK (status IN ('active', 'paused', 'completed', 'archived'))
);

CREATE INDEX idx_enrollments_user ON enrollments(user_id);
CREATE INDEX idx_enrollments_course ON enrollments(course_id);
CREATE INDEX idx_enrollments_user_active ON enrollments(user_id, status) WHERE status = 'active';
```

#### users
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    exam_date DATE,
    target_score INTEGER,
    daily_study_time INTEGER,
    knowledge_level VARCHAR(50),
    motivation TEXT,
    referral_source VARCHAR(50),
    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    dark_mode VARCHAR(10) NOT NULL DEFAULT 'auto',
    -- GDPR Account Deletion Support
    account_status VARCHAR(20) NOT NULL DEFAULT 'active',
    deletion_requested_at TIMESTAMP,
    deletion_scheduled_at TIMESTAMP,
    deletion_reason TEXT,
    deletion_cancellation_token VARCHAR(255),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CHECK (account_status IN ('active', 'pending_deletion', 'deleted'))
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_pending_deletion ON users(deletion_scheduled_at)
    WHERE account_status = 'pending_deletion';
```

#### concepts
```sql
CREATE TABLE concepts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    corpus_section_ref VARCHAR(50),          -- Was babok_section_ref
    knowledge_area_id VARCHAR(50) NOT NULL,  -- References course.knowledge_areas[].id
    difficulty_estimate FLOAT NOT NULL DEFAULT 0.5,
    prerequisite_depth INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_concepts_course ON concepts(course_id);
CREATE INDEX idx_concepts_knowledge_area ON concepts(course_id, knowledge_area_id);
CREATE INDEX idx_concepts_section ON concepts(corpus_section_ref);
```

#### concept_prerequisites
```sql
CREATE TABLE concept_prerequisites (
    concept_id UUID NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
    prerequisite_concept_id UUID NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
    strength FLOAT NOT NULL DEFAULT 1.0,
    relationship_type VARCHAR(20) NOT NULL DEFAULT 'required',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (concept_id, prerequisite_concept_id),
    CHECK (concept_id != prerequisite_concept_id),
    CHECK (strength >= 0.0 AND strength <= 1.0),
    CHECK (relationship_type IN ('required', 'helpful', 'related'))
);

CREATE INDEX idx_concept_prereqs_concept ON concept_prerequisites(concept_id);
CREATE INDEX idx_concept_prereqs_prereq ON concept_prerequisites(prerequisite_concept_id);
```

**Relationship Types:**
- `required`: Must understand prerequisite before learning this concept
- `helpful`: Understanding prerequisite improves learning but not strictly required
- `related`: Concepts are related but no strict ordering required

#### belief_states
```sql
CREATE TABLE belief_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    concept_id UUID NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
    alpha FLOAT NOT NULL DEFAULT 1.0,
    beta FLOAT NOT NULL DEFAULT 1.0,
    last_response_at TIMESTAMP,
    response_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, concept_id),
    CHECK (alpha > 0),
    CHECK (beta > 0)
);

CREATE INDEX idx_belief_states_user ON belief_states(user_id);
CREATE INDEX idx_belief_states_user_concept ON belief_states(user_id, concept_id);
CREATE INDEX idx_belief_states_updated ON belief_states(updated_at);
```

#### questions
```sql
CREATE TABLE questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    options JSONB NOT NULL,
    correct_answer CHAR(1) NOT NULL,
    explanation TEXT NOT NULL,
    knowledge_area_id VARCHAR(50) NOT NULL,  -- References course.knowledge_areas[].id
    difficulty FLOAT NOT NULL DEFAULT 0.5,
    discrimination FLOAT NOT NULL DEFAULT 1.0,
    guess_rate FLOAT NOT NULL DEFAULT 0.25,
    slip_rate FLOAT NOT NULL DEFAULT 0.10,
    times_asked INTEGER NOT NULL DEFAULT 0,
    times_correct INTEGER NOT NULL DEFAULT 0,
    source VARCHAR(50) NOT NULL DEFAULT 'vendor',
    corpus_reference VARCHAR(100),            -- Was babok_reference
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CHECK (correct_answer IN ('A', 'B', 'C', 'D')),
    CHECK (difficulty >= 0.0 AND difficulty <= 1.0),
    CHECK (guess_rate >= 0.0 AND guess_rate <= 1.0),
    CHECK (slip_rate >= 0.0 AND slip_rate <= 1.0)
);

CREATE INDEX idx_questions_course ON questions(course_id);
CREATE INDEX idx_questions_knowledge_area ON questions(course_id, knowledge_area_id);
CREATE INDEX idx_questions_difficulty ON questions(difficulty);
CREATE INDEX idx_questions_active ON questions(is_active) WHERE is_active = TRUE;
```

#### question_concepts
```sql
CREATE TABLE question_concepts (
    question_id UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    concept_id UUID NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
    relevance FLOAT NOT NULL DEFAULT 1.0,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (question_id, concept_id),
    CHECK (relevance >= 0.0 AND relevance <= 1.0)
);

CREATE INDEX idx_question_concepts_question ON question_concepts(question_id);
CREATE INDEX idx_question_concepts_concept ON question_concepts(concept_id);
```

#### quiz_sessions
```sql
CREATE TABLE quiz_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    enrollment_id UUID NOT NULL REFERENCES enrollments(id) ON DELETE CASCADE,
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMP,
    session_type VARCHAR(50) NOT NULL DEFAULT 'adaptive',
    question_strategy VARCHAR(50) NOT NULL DEFAULT 'max_info_gain',
    knowledge_area_filter VARCHAR(50),       -- References course.knowledge_areas[].id
    total_questions INTEGER NOT NULL DEFAULT 0,
    correct_count INTEGER NOT NULL DEFAULT 0,
    is_paused BOOLEAN NOT NULL DEFAULT FALSE,
    version INTEGER NOT NULL DEFAULT 1,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CHECK (session_type IN ('diagnostic', 'adaptive', 'focused', 'review')),
    CHECK (question_strategy IN ('max_info_gain', 'max_uncertainty', 'prerequisite_first', 'balanced'))
);

CREATE INDEX idx_quiz_sessions_user ON quiz_sessions(user_id);
CREATE INDEX idx_quiz_sessions_enrollment ON quiz_sessions(enrollment_id);
CREATE INDEX idx_quiz_sessions_user_active ON quiz_sessions(user_id, ended_at) WHERE ended_at IS NULL;

-- Optimistic locking trigger
CREATE OR REPLACE FUNCTION update_session_version()
RETURNS TRIGGER AS $$
BEGIN
    NEW.version = OLD.version + 1;
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER quiz_sessions_version_trigger
BEFORE UPDATE ON quiz_sessions
FOR EACH ROW
EXECUTE FUNCTION update_session_version();
```

#### responses
```sql
CREATE TABLE responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID NOT NULL REFERENCES quiz_sessions(id) ON DELETE CASCADE,
    question_id UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    selected_answer CHAR(1) NOT NULL,
    is_correct BOOLEAN NOT NULL,
    time_taken_ms INTEGER,
    request_id UUID UNIQUE,
    info_gain_actual FLOAT,  -- Actual entropy reduction; populated by belief update (Story 4.4)
    belief_updates JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CHECK (selected_answer IN ('A', 'B', 'C', 'D'))
);

CREATE INDEX idx_responses_user ON responses(user_id);
CREATE INDEX idx_responses_session ON responses(session_id);
CREATE INDEX idx_responses_question ON responses(question_id);
CREATE INDEX idx_responses_request_id ON responses(request_id);
CREATE INDEX idx_responses_user_recent ON responses(user_id, created_at DESC);
```

#### reading_chunks
```sql
CREATE TABLE reading_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    corpus_section VARCHAR(50) NOT NULL,     -- Was babok_section
    knowledge_area_id VARCHAR(50) NOT NULL,  -- References course.knowledge_areas[].id
    concept_ids UUID[] NOT NULL DEFAULT '{}',
    estimated_read_time_minutes INTEGER NOT NULL DEFAULT 5,
    chunk_index INTEGER NOT NULL DEFAULT 0,  -- Order within section (for multi-chunk sections)
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_reading_chunks_course ON reading_chunks(course_id);
CREATE INDEX idx_reading_chunks_knowledge_area ON reading_chunks(course_id, knowledge_area_id);
CREATE INDEX idx_reading_chunks_section ON reading_chunks(corpus_section);
CREATE INDEX idx_reading_chunks_concepts ON reading_chunks USING GIN(concept_ids);
```

#### reading_queue
```sql
CREATE TABLE reading_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    enrollment_id UUID NOT NULL REFERENCES enrollments(id) ON DELETE CASCADE,
    chunk_id UUID NOT NULL REFERENCES reading_chunks(id) ON DELETE CASCADE,
    triggered_by_question_id UUID REFERENCES questions(id) ON DELETE SET NULL,
    triggered_by_concept_id UUID REFERENCES concepts(id) ON DELETE SET NULL,
    priority VARCHAR(10) NOT NULL DEFAULT 'Medium',
    status VARCHAR(20) NOT NULL DEFAULT 'unread',
    added_at TIMESTAMP NOT NULL DEFAULT NOW(),
    times_opened INTEGER NOT NULL DEFAULT 0,
    total_reading_time_seconds INTEGER NOT NULL DEFAULT 0,
    completed_at TIMESTAMP,
    first_opened_at TIMESTAMP,      -- Set on first view of queue item (Story 5.8)
    dismissed_at TIMESTAMP,         -- Set when user dismisses item (Story 5.8)
    UNIQUE (enrollment_id, chunk_id),  -- Changed from (user_id, chunk_id)
    CHECK (priority IN ('High', 'Medium', 'Low')),
    CHECK (status IN ('unread', 'reading', 'completed', 'dismissed'))
);

CREATE INDEX idx_reading_queue_user ON reading_queue(user_id);
CREATE INDEX idx_reading_queue_enrollment ON reading_queue(enrollment_id);
CREATE INDEX idx_reading_queue_enrollment_status ON reading_queue(enrollment_id, status);
CREATE INDEX idx_reading_queue_priority ON reading_queue(enrollment_id, priority DESC, added_at);
```

#### admin_audit_log
```sql
CREATE TABLE admin_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    admin_id UUID NOT NULL REFERENCES users(id),
    admin_email VARCHAR(255) NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    target_user_id UUID REFERENCES users(id),
    target_email VARCHAR(255),
    details JSONB,
    duration_seconds INTEGER,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_log_admin ON admin_audit_log(admin_id);
CREATE INDEX idx_audit_log_action ON admin_audit_log(action_type);
CREATE INDEX idx_audit_log_created ON admin_audit_log(created_at);
```

---

### Key Design Decisions

1. **UUID primary keys** - Security (non-guessable), distributed systems ready
2. **Dual database strategy** - PostgreSQL (structured/transactional) + Qdrant (vector search)
3. **Beta distribution storage** - Store α and β directly; compute mean/confidence in application
4. **Belief state per concept** - ~1,500 concepts × N users = millions of rows; indexed appropriately
5. **JSONB for belief_updates** - Snapshot of updates stored with each response for auditability
6. **Optimistic locking** - Version column on quiz_sessions prevents concurrent modification conflicts
7. **Idempotency via request_id** - Unique constraint prevents duplicate response processing
8. **Soft deletes for questions** - `is_active` flag preserves historical data integrity

---

### Qdrant Collections

#### questions collection
- **Vector dimension:** 3072 (OpenAI text-embedding-3-large)
- **Distance metric:** Cosine
- **Payload fields:** knowledge_area, difficulty, concept_ids, is_active
- **Use case:** Semantic search for similar questions, concept-based retrieval

#### reading_chunks collection
- **Vector dimension:** 3072 (OpenAI text-embedding-3-large)
- **Distance metric:** Cosine
- **Payload fields:** knowledge_area, babok_section, concept_ids
- **Use case:** Match reading content to gap concepts, semantic search

---

### Materialized Views (Performance Optimization)

#### coverage_by_ka (User Coverage per Knowledge Area)
```sql
CREATE MATERIALIZED VIEW coverage_by_ka AS
SELECT
    bs.user_id,
    c.knowledge_area,
    COUNT(*) AS total_concepts,
    COUNT(*) FILTER (WHERE bs.alpha / (bs.alpha + bs.beta) >= 0.8
                     AND (bs.alpha + bs.beta) / (bs.alpha + bs.beta + 10) >= 0.7) AS mastered_count,
    COUNT(*) FILTER (WHERE bs.alpha / (bs.alpha + bs.beta) < 0.5
                     AND (bs.alpha + bs.beta) / (bs.alpha + bs.beta + 10) >= 0.7) AS gap_count,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE bs.alpha / (bs.alpha + bs.beta) >= 0.8
                                  AND (bs.alpha + bs.beta) / (bs.alpha + bs.beta + 10) >= 0.7)
        / COUNT(*)
    ) AS readiness_score
FROM belief_states bs
JOIN concepts c ON bs.concept_id = c.id
GROUP BY bs.user_id, c.knowledge_area;

CREATE UNIQUE INDEX idx_coverage_by_ka ON coverage_by_ka(user_id, knowledge_area);

-- Refresh periodically or after significant updates
-- REFRESH MATERIALIZED VIEW CONCURRENTLY coverage_by_ka;
```

---

### Database Functions

#### initialize_beliefs
Initialize belief states for a new user (all concepts start with Beta(1,1) uninformative prior):

```sql
CREATE OR REPLACE FUNCTION initialize_beliefs(p_user_id UUID)
RETURNS INTEGER AS $$
DECLARE
    inserted_count INTEGER;
BEGIN
    INSERT INTO belief_states (user_id, concept_id, alpha, beta)
    SELECT p_user_id, id, 1.0, 1.0
    FROM concepts
    ON CONFLICT (user_id, concept_id) DO NOTHING;

    GET DIAGNOSTICS inserted_count = ROW_COUNT;
    RETURN inserted_count;
END;
$$ LANGUAGE plpgsql;
```

#### get_recent_questions
Get questions asked to user in recent window (for recency filtering):

```sql
CREATE OR REPLACE FUNCTION get_recent_questions(
    p_user_id UUID,
    p_days INTEGER DEFAULT 7
)
RETURNS TABLE(question_id UUID) AS $$
BEGIN
    RETURN QUERY
    SELECT DISTINCT r.question_id
    FROM responses r
    WHERE r.user_id = p_user_id
      AND r.created_at > NOW() - (p_days || ' days')::INTERVAL;
END;
$$ LANGUAGE plpgsql;
```

---

### Triggers

#### Auto-update timestamps
```sql
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to all tables with updated_at
CREATE TRIGGER users_updated_at BEFORE UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER concepts_updated_at BEFORE UPDATE ON concepts
FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER belief_states_updated_at BEFORE UPDATE ON belief_states
FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER questions_updated_at BEFORE UPDATE ON questions
FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER reading_chunks_updated_at BEFORE UPDATE ON reading_chunks
FOR EACH ROW EXECUTE FUNCTION update_updated_at();
```

#### Update question statistics
```sql
CREATE OR REPLACE FUNCTION update_question_stats()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE questions
    SET times_asked = times_asked + 1,
        times_correct = times_correct + CASE WHEN NEW.is_correct THEN 1 ELSE 0 END
    WHERE id = NEW.question_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER responses_update_question_stats
AFTER INSERT ON responses
FOR EACH ROW EXECUTE FUNCTION update_question_stats();
```

---

### GDPR Data Management Functions

#### schedule_user_deletion
Schedule user account for deletion with grace period:

```sql
CREATE OR REPLACE FUNCTION schedule_user_deletion(
    p_user_id UUID,
    p_reason TEXT DEFAULT NULL,
    p_grace_period_days INTEGER DEFAULT 7
)
RETURNS TABLE(
    deletion_scheduled_at TIMESTAMP,
    deletion_effective_at TIMESTAMP,
    cancellation_token VARCHAR
) AS $$
DECLARE
    v_cancellation_token VARCHAR(255);
    v_scheduled_at TIMESTAMP;
    v_effective_at TIMESTAMP;
BEGIN
    -- Generate secure cancellation token
    v_cancellation_token := encode(gen_random_bytes(32), 'hex');
    v_scheduled_at := NOW();
    v_effective_at := NOW() + (p_grace_period_days || ' days')::INTERVAL;

    -- Update user record
    UPDATE users
    SET account_status = 'pending_deletion',
        deletion_requested_at = v_scheduled_at,
        deletion_scheduled_at = v_effective_at,
        deletion_reason = p_reason,
        deletion_cancellation_token = v_cancellation_token,
        updated_at = NOW()
    WHERE id = p_user_id
      AND account_status = 'active';

    IF NOT FOUND THEN
        RAISE EXCEPTION 'User not found or not in active status';
    END IF;

    RETURN QUERY SELECT v_scheduled_at, v_effective_at, v_cancellation_token;
END;
$$ LANGUAGE plpgsql;
```

#### cancel_user_deletion
Cancel pending deletion during grace period:

```sql
CREATE OR REPLACE FUNCTION cancel_user_deletion(
    p_user_id UUID,
    p_cancellation_token VARCHAR
)
RETURNS BOOLEAN AS $$
DECLARE
    v_success BOOLEAN := FALSE;
BEGIN
    UPDATE users
    SET account_status = 'active',
        deletion_requested_at = NULL,
        deletion_scheduled_at = NULL,
        deletion_reason = NULL,
        deletion_cancellation_token = NULL,
        updated_at = NOW()
    WHERE id = p_user_id
      AND account_status = 'pending_deletion'
      AND deletion_cancellation_token = p_cancellation_token
      AND deletion_scheduled_at > NOW();

    GET DIAGNOSTICS v_success = ROW_COUNT > 0;
    RETURN v_success;
END;
$$ LANGUAGE plpgsql;
```

#### execute_user_deletion
Permanently delete user data (called by background job after grace period):

```sql
CREATE OR REPLACE FUNCTION execute_user_deletion(p_user_id UUID)
RETURNS TABLE(
    deleted_reading_queue INTEGER,
    deleted_responses INTEGER,
    deleted_sessions INTEGER,
    deleted_beliefs INTEGER,
    deleted_enrollments INTEGER,
    user_deleted BOOLEAN
) AS $$
DECLARE
    v_reading_queue INTEGER;
    v_responses INTEGER;
    v_sessions INTEGER;
    v_beliefs INTEGER;
    v_enrollments INTEGER;
    v_email_hash VARCHAR(64);
BEGIN
    -- Verify user is in pending_deletion status and grace period expired
    IF NOT EXISTS (
        SELECT 1 FROM users
        WHERE id = p_user_id
          AND account_status = 'pending_deletion'
          AND deletion_scheduled_at <= NOW()
    ) THEN
        RAISE EXCEPTION 'User not eligible for deletion';
    END IF;

    -- Get email hash for anonymized audit log
    SELECT encode(sha256(email::bytea), 'hex') INTO v_email_hash
    FROM users WHERE id = p_user_id;

    -- Delete in cascade order (respecting foreign keys)
    -- 1. reading_queue (depends on enrollment, user)
    DELETE FROM reading_queue WHERE user_id = p_user_id;
    GET DIAGNOSTICS v_reading_queue = ROW_COUNT;

    -- 2. responses (depends on session, user)
    DELETE FROM responses WHERE user_id = p_user_id;
    GET DIAGNOSTICS v_responses = ROW_COUNT;

    -- 3. quiz_sessions (depends on enrollment, user)
    DELETE FROM quiz_sessions WHERE user_id = p_user_id;
    GET DIAGNOSTICS v_sessions = ROW_COUNT;

    -- 4. belief_states (depends on user, concept)
    DELETE FROM belief_states WHERE user_id = p_user_id;
    GET DIAGNOSTICS v_beliefs = ROW_COUNT;

    -- 5. enrollments (depends on user, course)
    DELETE FROM enrollments WHERE user_id = p_user_id;
    GET DIAGNOSTICS v_enrollments = ROW_COUNT;

    -- 6. Anonymize admin_audit_log entries (preserve for compliance)
    UPDATE admin_audit_log
    SET target_user_id = NULL,
        target_email = 'deleted_user_' || v_email_hash
    WHERE target_user_id = p_user_id;

    -- 7. Delete user record
    DELETE FROM users WHERE id = p_user_id;

    -- Log deletion in audit
    INSERT INTO admin_audit_log (
        admin_id, admin_email, action_type, details, created_at
    ) VALUES (
        p_user_id,
        'system',
        'user_data_deleted',
        jsonb_build_object(
            'user_hash', v_email_hash,
            'reading_queue_deleted', v_reading_queue,
            'responses_deleted', v_responses,
            'sessions_deleted', v_sessions,
            'beliefs_deleted', v_beliefs,
            'enrollments_deleted', v_enrollments
        ),
        NOW()
    );

    RETURN QUERY SELECT v_reading_queue, v_responses, v_sessions,
                        v_beliefs, v_enrollments, TRUE;
END;
$$ LANGUAGE plpgsql;
```

#### export_user_data
Export all user data in GDPR-compliant format:

```sql
CREATE OR REPLACE FUNCTION export_user_data(p_user_id UUID)
RETURNS JSONB AS $$
DECLARE
    v_result JSONB;
BEGIN
    SELECT jsonb_build_object(
        'export_metadata', jsonb_build_object(
            'exported_at', NOW(),
            'user_id', p_user_id,
            'format_version', '1.0'
        ),
        'user_profile', (
            SELECT jsonb_build_object(
                'id', id,
                'email', email,
                'created_at', created_at,
                'exam_date', exam_date,
                'target_score', target_score,
                'daily_study_time', daily_study_time,
                'knowledge_level', knowledge_level,
                'motivation', motivation,
                'referral_source', referral_source,
                'dark_mode', dark_mode
            )
            FROM users WHERE id = p_user_id
        ),
        'enrollments', (
            SELECT COALESCE(jsonb_agg(jsonb_build_object(
                'course_slug', c.slug,
                'course_name', c.name,
                'enrolled_at', e.enrolled_at,
                'exam_date', e.exam_date,
                'target_score', e.target_score,
                'status', e.status,
                'completion_percentage', e.completion_percentage
            )), '[]'::jsonb)
            FROM enrollments e
            JOIN courses c ON e.course_id = c.id
            WHERE e.user_id = p_user_id
        ),
        'quiz_sessions', (
            SELECT COALESCE(jsonb_agg(jsonb_build_object(
                'session_type', qs.session_type,
                'started_at', qs.started_at,
                'ended_at', qs.ended_at,
                'total_questions', qs.total_questions,
                'correct_count', qs.correct_count
            )), '[]'::jsonb)
            FROM quiz_sessions qs
            WHERE qs.user_id = p_user_id
        ),
        'responses_count', (
            SELECT COUNT(*) FROM responses WHERE user_id = p_user_id
        ),
        'belief_states_count', (
            SELECT COUNT(*) FROM belief_states WHERE user_id = p_user_id
        )
    ) INTO v_result;

    RETURN v_result;
END;
$$ LANGUAGE plpgsql;
```

---

### Cascade Deletion Behavior

All user-related tables use `ON DELETE CASCADE` to ensure complete data removal:

| Table | Foreign Key | Cascade Behavior |
|-------|-------------|------------------|
| `enrollments` | `user_id → users(id)` | `ON DELETE CASCADE` |
| `belief_states` | `user_id → users(id)` | `ON DELETE CASCADE` |
| `quiz_sessions` | `user_id → users(id)` | `ON DELETE CASCADE` |
| `responses` | `user_id → users(id)` | `ON DELETE CASCADE` |
| `reading_queue` | `user_id → users(id)` | `ON DELETE CASCADE` |
| `admin_audit_log` | `target_user_id → users(id)` | `ON DELETE SET NULL` (preserves audit trail) |

**Note:** The `execute_user_deletion` function performs explicit deletions in order to capture row counts for audit purposes. The `ON DELETE CASCADE` constraints serve as a safety net.

---

### Migration Notes

When migrating from the legacy schema:

1. **Create new tables** - concepts, concept_prerequisites, belief_states, question_concepts
2. **Migrate questions** - Add BKT parameters (guess_rate, slip_rate, discrimination)
3. **Initialize beliefs** - Run `initialize_beliefs()` for existing users
4. **Map questions to concepts** - Populate question_concepts junction table
5. **Deprecate competencies** - Stop using legacy competencies table
6. **Update reading_queue** - Add `triggered_by_concept_id` column

---

### Entity Relationship Diagram

```
                    ┌──────────────┐
                    │    users     │
                    └──────┬───────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
           ▼               ▼               ▼
    ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
    │belief_states│  │quiz_sessions│  │reading_queue│
    └──────┬──────┘  └──────┬──────┘  └─────────────┘
           │                │
           │                ▼
           │         ┌─────────────┐
           │         │  responses  │
           │         └──────┬──────┘
           │                │
           ▼                ▼
    ┌─────────────┐  ┌─────────────┐
    │   concepts  │◄─┤  questions  │
    └──────┬──────┘  └─────────────┘
           │                ▲
           │                │
           ▼                │
┌───────────────────┐       │
│concept_prerequisites│     │
└───────────────────┘       │
                            │
                   ┌────────┴────────┐
                   │question_concepts│
                   └─────────────────┘
```

---

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-12-08 | 3.1 | GDPR Compliance - added account_status, deletion_* columns to users table; added GDPR functions (schedule_user_deletion, cancel_user_deletion, execute_user_deletion, export_user_data); documented cascade deletion behavior | Winston (Architect) |
| 2025-12-08 | 3.0 | Multi-Course Architecture - added courses, enrollments tables; added course_id to concepts, questions, reading_chunks; added enrollment_id to quiz_sessions, reading_queue; dynamic knowledge_area_id | Winston (Architect) |
| 2025-12-03 | 2.0 | Aligned with BKT Architecture - added concepts, belief_states, question_concepts; deprecated competencies | Winston (Architect) |
| 2025-11-01 | 1.0 | Initial database schema | Original |
