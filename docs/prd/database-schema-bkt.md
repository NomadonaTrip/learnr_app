# Database Schema - BKT-First Architecture

This document defines the database schema for the Bayesian Knowledge Tracing (BKT) architecture. It replaces the competency_tracking approach with concept-level belief states.

**Key Changes from Original Schema (v2.0):**
- Added `concepts` table (500-1500 concepts from BABOK)
- Added `concept_prerequisites` table (DAG for learning paths)
- Added `question_concepts` junction table (questions test concepts)
- Added `belief_states` table (replaces competency_tracking)
- Modified `questions` table (added IRT parameters)
- Modified `quiz_sessions` table (added info_gain tracking)
- Added `chunk_concepts` junction table (reading linked to concepts)

**Key Changes for Epic 11 & Story 4.11 (v3.0):**
- Modified `users` table (added `timezone` field for streak calculations)
- Added `notification_preferences` table (user notification settings)
- Added `study_streaks` table (streak state and freeze tracking)
- Added `daily_activity` table (daily activity log)
- Added `study_goals` table (user-defined goals)
- Added `achievements` table (badge definitions with 16 seeds)
- Added `user_achievements` table (earned badges)
- Added `notifications` table (in-app notifications)
- Added `concept_unlock_events` table (mastery gate unlock tracking)
- Added `concept_lock_status` table (cached lock status)

---

## Core Tables

### Table: `users`

*Modified: Added timezone field for gamification (Epic 11)*

```sql
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    theme_preference VARCHAR(10) DEFAULT 'auto',
    timezone VARCHAR(50) DEFAULT 'UTC',  -- IANA timezone (e.g., 'America/New_York') for streak calculations
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_admin ON users(is_admin) WHERE is_admin = TRUE;
```

### Table: `knowledge_areas`

*Unchanged - Used for aggregation and backward compatibility*

```sql
CREATE TABLE knowledge_areas (
    ka_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ka_name VARCHAR(255) NOT NULL UNIQUE,
    ka_abbreviation VARCHAR(10),
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

---

## Knowledge Graph Tables (NEW)

### Table: `concepts`

The fundamental unit of knowledge in the BKT system.

```sql
CREATE TABLE concepts (
    concept_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    babok_section_ref VARCHAR(50),  -- e.g., "3.2.1"
    ka_id UUID NOT NULL REFERENCES knowledge_areas(ka_id),
    difficulty_estimate DECIMAL(3,2) DEFAULT 0.50 CHECK (difficulty_estimate >= 0 AND difficulty_estimate <= 1),
    prerequisite_depth INT DEFAULT 0,  -- Distance from root concepts (0 = foundational)
    parent_concept_id UUID REFERENCES concepts(concept_id),  -- For hierarchical organization

    -- Extraction metadata (populated during concept extraction - Story 2.2)
    keywords JSONB,  -- Array of related terms for search/matching
    source_sections JSONB,  -- Array of section refs if concept merged from multiple sources
    extraction_confidence DECIMAL(3,2) CHECK (extraction_confidence >= 0 AND extraction_confidence <= 1),  -- GPT-4 confidence score
    review_status VARCHAR(20) DEFAULT 'pending' CHECK (review_status IN ('pending', 'approved', 'rejected', 'needs_review')),

    is_active BOOLEAN DEFAULT TRUE,  -- For soft delete
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_concepts_ka ON concepts(ka_id);
CREATE INDEX idx_concepts_section ON concepts(babok_section_ref);
CREATE INDEX idx_concepts_depth ON concepts(prerequisite_depth);
CREATE INDEX idx_concepts_parent ON concepts(parent_concept_id);
CREATE INDEX idx_concepts_active ON concepts(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_concepts_review ON concepts(review_status);  -- For filtering by review status

-- Full-text search on concept name and description
CREATE INDEX idx_concepts_name_fts ON concepts USING gin(to_tsvector('english', name || ' ' || COALESCE(description, '')));
```

### Table: `concept_prerequisites`

Directed acyclic graph (DAG) of concept dependencies.

```sql
CREATE TABLE concept_prerequisites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    concept_id UUID NOT NULL REFERENCES concepts(concept_id) ON DELETE CASCADE,
    prerequisite_concept_id UUID NOT NULL REFERENCES concepts(concept_id) ON DELETE CASCADE,
    strength DECIMAL(3,2) DEFAULT 1.00 CHECK (strength >= 0 AND strength <= 1),
    relationship_type VARCHAR(20) DEFAULT 'required' CHECK (relationship_type IN ('required', 'helpful', 'related')),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT unique_concept_prereq UNIQUE (concept_id, prerequisite_concept_id),
    CONSTRAINT no_self_reference CHECK (concept_id != prerequisite_concept_id)
);

CREATE INDEX idx_prereq_concept ON concept_prerequisites(concept_id);
CREATE INDEX idx_prereq_prereq ON concept_prerequisites(prerequisite_concept_id);
CREATE INDEX idx_prereq_strength ON concept_prerequisites(strength);
```

---

## Question Tables (MODIFIED)

### Table: `questions`

Extended with IRT parameters and removed concept_tags (replaced by junction table).

```sql
CREATE TABLE questions (
    question_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_text TEXT NOT NULL,
    option_a TEXT NOT NULL,
    option_b TEXT NOT NULL,
    option_c TEXT NOT NULL,
    option_d TEXT NOT NULL,
    correct_answer CHAR(1) NOT NULL CHECK (correct_answer IN ('A', 'B', 'C', 'D')),
    explanation TEXT NOT NULL,

    -- Legacy: Keep for backward compatibility and display
    ka_id UUID NOT NULL REFERENCES knowledge_areas(ka_id),

    -- IRT Parameters (Story 10.1: Updated to IRT b-parameter scale)
    difficulty DECIMAL(4,2) NOT NULL DEFAULT 0.00 CHECK (difficulty >= -3.0 AND difficulty <= 3.0),  -- IRT b-parameter
    difficulty_label VARCHAR(10),  -- Human-readable: Easy/Medium/Hard
    discrimination DECIMAL(3,2) NOT NULL DEFAULT 1.00 CHECK (discrimination >= 0 AND discrimination <= 3),
    guess_rate DECIMAL(3,2) NOT NULL DEFAULT 0.25 CHECK (guess_rate >= 0 AND guess_rate <= 1),
    slip_rate DECIMAL(3,2) NOT NULL DEFAULT 0.10 CHECK (slip_rate >= 0 AND slip_rate <= 1),

    -- Calibration tracking
    times_asked INT DEFAULT 0,
    times_correct INT DEFAULT 0,

    -- Metadata
    source VARCHAR(50),  -- 'vendor' | 'llm_generated'
    babok_section VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_questions_ka ON questions(ka_id);
CREATE INDEX idx_questions_difficulty ON questions(difficulty);
CREATE INDEX idx_questions_active ON questions(is_active) WHERE is_active = TRUE;
```

### Table: `question_concepts`

Junction table linking questions to concepts they test.

```sql
CREATE TABLE question_concepts (
    question_id UUID NOT NULL REFERENCES questions(question_id) ON DELETE CASCADE,
    concept_id UUID NOT NULL REFERENCES concepts(concept_id) ON DELETE CASCADE,
    relevance DECIMAL(3,2) NOT NULL DEFAULT 1.00 CHECK (relevance >= 0 AND relevance <= 1),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    PRIMARY KEY (question_id, concept_id)
);

CREATE INDEX idx_qc_question ON question_concepts(question_id);
CREATE INDEX idx_qc_concept ON question_concepts(concept_id);
CREATE INDEX idx_qc_relevance ON question_concepts(relevance);
```

---

## Belief State Tables (NEW - Core of BKT)

### Table: `belief_states`

Replaces `competency_tracking`. Stores Beta distribution parameters per user per concept.

```sql
CREATE TABLE belief_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    concept_id UUID NOT NULL REFERENCES concepts(concept_id) ON DELETE CASCADE,

    -- Beta distribution parameters
    alpha DECIMAL(10,4) NOT NULL DEFAULT 1.0000,  -- Successes + prior
    beta DECIMAL(10,4) NOT NULL DEFAULT 1.0000,   -- Failures + prior

    -- Tracking
    response_count INT NOT NULL DEFAULT 0,  -- Questions answered for this concept
    last_response_at TIMESTAMP,  -- For recency/decay calculations

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT unique_user_concept UNIQUE (user_id, concept_id)
);

-- Primary query pattern: Get all beliefs for a user
CREATE INDEX idx_beliefs_user ON belief_states(user_id);

-- For concept-based queries
CREATE INDEX idx_beliefs_concept ON belief_states(concept_id);

-- For finding high-uncertainty concepts (where alpha + beta is low)
CREATE INDEX idx_beliefs_uncertainty ON belief_states(user_id, (alpha + beta));

-- For finding mastered concepts (where alpha / (alpha + beta) is high)
CREATE INDEX idx_beliefs_mastery ON belief_states(user_id, (alpha / (alpha + beta)));
```

**Notes:**
- `alpha = 1, beta = 1` is the uninformative prior (Beta(1,1) = Uniform[0,1])
- Mean mastery = `alpha / (alpha + beta)`
- Confidence = `(alpha + beta) / (alpha + beta + 2)` (approaches 1 with more data)
- Variance = `alpha * beta / ((alpha + beta)^2 * (alpha + beta + 1))`

### View: `belief_states_computed`

Materialized view for common computed properties.

```sql
CREATE MATERIALIZED VIEW belief_states_computed AS
SELECT
    id,
    user_id,
    concept_id,
    alpha,
    beta,
    response_count,
    last_response_at,

    -- Computed properties
    (alpha / (alpha + beta)) AS mastery_probability,
    ((alpha + beta) / (alpha + beta + 2)) AS confidence,

    -- Classification
    CASE
        WHEN (alpha + beta) < 3 THEN 'uncertain'
        WHEN (alpha / (alpha + beta)) >= 0.8 AND ((alpha + beta) / (alpha + beta + 2)) >= 0.7 THEN 'mastered'
        WHEN (alpha / (alpha + beta)) <= 0.5 AND ((alpha + beta) / (alpha + beta + 2)) >= 0.7 THEN 'gap'
        ELSE 'uncertain'
    END AS status,

    updated_at
FROM belief_states;

CREATE UNIQUE INDEX idx_bsc_id ON belief_states_computed(id);
CREATE INDEX idx_bsc_user ON belief_states_computed(user_id);
CREATE INDEX idx_bsc_status ON belief_states_computed(user_id, status);
CREATE INDEX idx_bsc_mastery ON belief_states_computed(user_id, mastery_probability DESC);

-- Refresh strategy: After each quiz session ends
-- REFRESH MATERIALIZED VIEW CONCURRENTLY belief_states_computed;
```

---

## Quiz Session Tables (MODIFIED)

### Table: `quiz_sessions`

Extended with BKT-specific tracking.

```sql
CREATE TABLE quiz_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,

    -- Session type
    session_type VARCHAR(20) NOT NULL DEFAULT 'adaptive'
        CHECK (session_type IN ('diagnostic', 'adaptive', 'focused_ka', 'focused_concept', 'review')),

    -- Focus targets (for focused sessions)
    target_ka_id UUID REFERENCES knowledge_areas(ka_id),
    target_concept_ids JSONB,  -- Array of concept UUIDs for focused_concept sessions

    -- Progress tracking
    questions_answered INT DEFAULT 0,
    correct_count INT DEFAULT 0,

    -- BKT-specific tracking (NEW)
    total_info_gain DECIMAL(10,4) DEFAULT 0,  -- Cumulative information gain
    concepts_updated INT DEFAULT 0,  -- Count of concepts with belief updates

    -- Status
    session_status VARCHAR(20) DEFAULT 'active'
        CHECK (session_status IN ('active', 'paused', 'completed', 'expired')),

    -- Timestamps
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    paused_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_sessions_user ON quiz_sessions(user_id);
CREATE INDEX idx_sessions_status ON quiz_sessions(session_status);
CREATE INDEX idx_sessions_user_active ON quiz_sessions(user_id, session_status) WHERE session_status = 'active';
```

### Table: `quiz_responses`

Extended with belief update tracking.

```sql
CREATE TABLE quiz_responses (
    response_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES quiz_sessions(session_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    question_id UUID NOT NULL REFERENCES questions(question_id),

    -- Response data
    selected_answer CHAR(1) NOT NULL CHECK (selected_answer IN ('A', 'B', 'C', 'D')),
    is_correct BOOLEAN NOT NULL,
    time_spent_ms INT,  -- Changed from seconds to milliseconds for precision

    -- BKT-specific tracking (NEW)
    info_gain_expected DECIMAL(8,4),  -- Expected info gain when question was selected
    info_gain_actual DECIMAL(8,4),    -- Actual info gain after response
    belief_updates JSONB,             -- Snapshot of concept updates: [{concept_id, old_alpha, old_beta, new_alpha, new_beta}]

    -- Timestamps
    answered_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_responses_session ON quiz_responses(session_id);
CREATE INDEX idx_responses_user ON quiz_responses(user_id);
CREATE INDEX idx_responses_question ON quiz_responses(question_id);
CREATE INDEX idx_responses_user_recent ON quiz_responses(user_id, answered_at DESC);
```

---

## Diagnostic Session Tables

### Table: `diagnostic_sessions`

Tracks diagnostic assessment state.

```sql
CREATE TABLE diagnostic_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,

    -- Selected questions for this diagnostic
    question_ids JSONB NOT NULL,  -- Array of question UUIDs in order
    current_index INT DEFAULT 0,

    -- Status
    status VARCHAR(20) DEFAULT 'in_progress'
        CHECK (status IN ('in_progress', 'completed', 'expired', 'reset')),

    -- Coverage tracking
    concepts_covered INT DEFAULT 0,
    total_concepts INT NOT NULL,

    -- Timestamps
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT unique_user_active_diagnostic UNIQUE (user_id, status)
);

CREATE INDEX idx_diagnostic_user ON diagnostic_sessions(user_id);
CREATE INDEX idx_diagnostic_status ON diagnostic_sessions(status);
```

---

## Content Tables (MODIFIED)

### Table: `content_chunks`

Extended with concept links.

```sql
CREATE TABLE content_chunks (
    chunk_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ka_id UUID NOT NULL REFERENCES knowledge_areas(ka_id),
    section_ref VARCHAR(50),
    title VARCHAR(255),
    text_content TEXT NOT NULL,
    word_count INT NOT NULL,
    difficulty VARCHAR(20) CHECK (difficulty IN ('easy', 'medium', 'hard')),
    embedding VECTOR(1536),
    page_reference INT,
    chunk_index INT,  -- Order within section
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_chunks_ka ON content_chunks(ka_id);
CREATE INDEX idx_chunks_section ON content_chunks(section_ref);
CREATE INDEX idx_chunks_embedding ON content_chunks USING ivfflat(embedding vector_cosine_ops);
```

### Table: `chunk_concepts`

Junction table linking chunks to concepts.

```sql
CREATE TABLE chunk_concepts (
    chunk_id UUID NOT NULL REFERENCES content_chunks(chunk_id) ON DELETE CASCADE,
    concept_id UUID NOT NULL REFERENCES concepts(concept_id) ON DELETE CASCADE,
    relevance DECIMAL(3,2) NOT NULL DEFAULT 1.00 CHECK (relevance >= 0 AND relevance <= 1),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    PRIMARY KEY (chunk_id, concept_id)
);

CREATE INDEX idx_cc_chunk ON chunk_concepts(chunk_id);
CREATE INDEX idx_cc_concept ON chunk_concepts(concept_id);
```

---

## User Preferences Tables (NEW - Epic 11)

### Table: `notification_preferences`

User notification settings for streak reminders and other notifications.

```sql
CREATE TABLE notification_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,

    -- Channel preferences
    email_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    push_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    in_app_enabled BOOLEAN NOT NULL DEFAULT TRUE,

    -- Notification type preferences
    streak_reminders_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    milestone_notifications_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    weekly_summary_enabled BOOLEAN NOT NULL DEFAULT TRUE,

    -- Timing preferences
    reminder_time TIME NOT NULL DEFAULT '20:00',  -- 8 PM default in user's timezone

    -- Mute settings (vacation mode)
    muted_until TIMESTAMP,  -- Null = not muted

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    UNIQUE(user_id)
);

CREATE INDEX idx_notification_prefs_user ON notification_preferences(user_id);
CREATE INDEX idx_notification_prefs_muted ON notification_preferences(muted_until)
    WHERE muted_until IS NOT NULL;
```

---

## Gamification Tables (NEW - Epic 11)

### Table: `study_streaks`

Tracks user study streak state.

```sql
CREATE TABLE study_streaks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,

    -- Streak state
    current_streak INT NOT NULL DEFAULT 0,
    longest_streak INT NOT NULL DEFAULT 0,
    last_activity_date DATE,

    -- Freeze state
    streak_frozen_until DATE,  -- Null if not frozen
    freeze_count_used INT NOT NULL DEFAULT 0,  -- Used this month
    freeze_count_available INT NOT NULL DEFAULT 2,  -- Monthly allowance
    freeze_last_reset DATE,  -- Last monthly reset date

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    UNIQUE(user_id)
);

CREATE INDEX idx_study_streaks_user ON study_streaks(user_id);
CREATE INDEX idx_study_streaks_activity ON study_streaks(last_activity_date);
CREATE INDEX idx_study_streaks_frozen ON study_streaks(streak_frozen_until)
    WHERE streak_frozen_until IS NOT NULL;
```

### Table: `daily_activity`

Daily activity log for streak calculation and goal tracking.

```sql
CREATE TABLE daily_activity (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    activity_date DATE NOT NULL,

    -- Activity metrics
    questions_answered INT NOT NULL DEFAULT 0,
    questions_correct INT NOT NULL DEFAULT 0,
    reading_completed INT NOT NULL DEFAULT 0,
    study_time_seconds INT NOT NULL DEFAULT 0,
    concepts_mastered INT NOT NULL DEFAULT 0,  -- Newly mastered this day

    -- Streak qualification
    qualifies_for_streak BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    UNIQUE(user_id, activity_date)
);

CREATE INDEX idx_daily_activity_user_date ON daily_activity(user_id, activity_date DESC);
CREATE INDEX idx_daily_activity_qualifies ON daily_activity(user_id, qualifies_for_streak)
    WHERE qualifies_for_streak = TRUE;
```

### Table: `study_goals`

User-defined study goals (daily and weekly).

```sql
CREATE TABLE study_goals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,

    -- Daily goals
    daily_questions_goal INT NOT NULL DEFAULT 10,
    daily_study_minutes_goal INT NOT NULL DEFAULT 15,
    daily_readings_goal INT NOT NULL DEFAULT 3,

    -- Weekly goals
    weekly_questions_goal INT NOT NULL DEFAULT 50,
    weekly_mastery_goal INT NOT NULL DEFAULT 5,  -- Concepts to master

    -- Display preferences
    show_goal_on_dashboard BOOLEAN NOT NULL DEFAULT TRUE,
    goal_completion_celebration BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    UNIQUE(user_id)
);

CREATE INDEX idx_study_goals_user ON study_goals(user_id);
```

### Table: `achievements`

Achievement/badge definitions (seed data).

```sql
CREATE TABLE achievements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(50) NOT NULL CHECK (category IN ('streak', 'mastery', 'volume', 'special')),
    icon VARCHAR(50) NOT NULL,  -- Icon identifier for frontend
    tier VARCHAR(20) NOT NULL DEFAULT 'bronze' CHECK (tier IN ('bronze', 'silver', 'gold', 'platinum')),
    requirement_type VARCHAR(50) NOT NULL,  -- 'streak_days', 'questions_answered', 'concepts_mastered', etc.
    requirement_value INT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    display_order INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_achievements_category ON achievements(category);
CREATE INDEX idx_achievements_active ON achievements(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_achievements_tier ON achievements(tier);

-- Seed data for achievements
INSERT INTO achievements (slug, name, description, category, icon, tier, requirement_type, requirement_value, display_order) VALUES
-- Streak achievements
('streak_3', 'Getting Started', 'Study 3 days in a row', 'streak', 'flame', 'bronze', 'streak_days', 3, 1),
('streak_7', 'Week Warrior', 'Study 7 days in a row', 'streak', 'flame', 'bronze', 'streak_days', 7, 2),
('streak_14', 'Fortnight Focus', 'Study 14 days in a row', 'streak', 'flame', 'silver', 'streak_days', 14, 3),
('streak_30', 'Monthly Master', 'Study 30 days in a row', 'streak', 'flame', 'gold', 'streak_days', 30, 4),
('streak_60', 'Exam Ready', 'Study 60 days in a row', 'streak', 'flame', 'platinum', 'streak_days', 60, 5),
-- Volume achievements
('questions_50', 'First Fifty', 'Answer 50 questions', 'volume', 'target', 'bronze', 'questions_answered', 50, 10),
('questions_250', 'Question Hunter', 'Answer 250 questions', 'volume', 'target', 'silver', 'questions_answered', 250, 11),
('questions_500', 'Quiz Champion', 'Answer 500 questions', 'volume', 'target', 'gold', 'questions_answered', 500, 12),
('questions_1000', 'Knowledge Seeker', 'Answer 1000 questions', 'volume', 'target', 'platinum', 'questions_answered', 1000, 13),
-- Mastery achievements
('mastery_10', 'First Concepts', 'Master 10 concepts', 'mastery', 'brain', 'bronze', 'concepts_mastered', 10, 20),
('mastery_50', 'Building Expertise', 'Master 50 concepts', 'mastery', 'brain', 'silver', 'concepts_mastered', 50, 21),
('mastery_100', 'Domain Expert', 'Master 100 concepts', 'mastery', 'brain', 'gold', 'concepts_mastered', 100, 22),
('mastery_all_ka', 'Well-Rounded', 'Reach 70%+ in all 6 KAs', 'mastery', 'star', 'gold', 'all_ka_threshold', 70, 23),
-- Special achievements
('perfect_session', 'Perfect Session', 'Answer 10+ questions with 100% accuracy', 'special', 'trophy', 'gold', 'perfect_session', 10, 30),
('comeback', 'Comeback Kid', 'Return after 7+ days and complete a session', 'special', 'refresh', 'silver', 'comeback_days', 7, 31),
('night_owl', 'Night Owl', 'Complete a session after 10pm', 'special', 'moon', 'bronze', 'time_based', 22, 32),
('early_bird', 'Early Bird', 'Complete a session before 7am', 'special', 'sun', 'bronze', 'time_based', 7, 33);
```

### Table: `user_achievements`

User's earned achievements.

```sql
CREATE TABLE user_achievements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    achievement_id UUID NOT NULL REFERENCES achievements(id) ON DELETE CASCADE,
    earned_at TIMESTAMP NOT NULL DEFAULT NOW(),
    notified BOOLEAN NOT NULL DEFAULT FALSE,  -- Has user been shown celebration?

    UNIQUE(user_id, achievement_id)
);

CREATE INDEX idx_user_achievements_user ON user_achievements(user_id);
CREATE INDEX idx_user_achievements_earned ON user_achievements(earned_at DESC);
CREATE INDEX idx_user_achievements_unnotified ON user_achievements(user_id, notified)
    WHERE notified = FALSE;
```

### Table: `notifications`

In-app notification storage.

```sql
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,

    -- Notification content
    notification_type VARCHAR(50) NOT NULL,  -- 'streak_risk', 'streak_lost', 'milestone', 'achievement', 'freeze_refill'
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    payload JSONB,  -- Additional data (achievement_id, streak_count, etc.)

    -- Delivery tracking
    scheduled_for TIMESTAMP NOT NULL DEFAULT NOW(),
    sent_at TIMESTAMP,
    read_at TIMESTAMP,
    dismissed_at TIMESTAMP,

    -- Channels sent
    sent_in_app BOOLEAN DEFAULT FALSE,
    sent_email BOOLEAN DEFAULT FALSE,
    sent_push BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_notifications_user ON notifications(user_id);
CREATE INDEX idx_notifications_pending ON notifications(user_id, scheduled_for)
    WHERE sent_at IS NULL;
CREATE INDEX idx_notifications_unread ON notifications(user_id, read_at)
    WHERE read_at IS NULL AND sent_at IS NOT NULL;
CREATE INDEX idx_notifications_type ON notifications(notification_type);
```

---

## Mastery Gates Tables (NEW - Story 4.11)

### Table: `concept_unlock_events`

Tracks when concepts become unlocked (prerequisites mastered).

```sql
CREATE TABLE concept_unlock_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    concept_id UUID NOT NULL REFERENCES concepts(concept_id) ON DELETE CASCADE,

    -- Unlock details
    unlocked_at TIMESTAMP NOT NULL DEFAULT NOW(),
    unlock_trigger VARCHAR(50) NOT NULL DEFAULT 'prereq_mastery',  -- 'prereq_mastery', 'manual_override', 'initial_seed'

    -- Snapshot of state at unlock
    prereq_mastery_snapshot JSONB,  -- [{concept_id, mastery_probability, confidence}]

    -- For curriculum progress tracking
    notified BOOLEAN NOT NULL DEFAULT FALSE,

    UNIQUE(user_id, concept_id)
);

CREATE INDEX idx_unlock_events_user ON concept_unlock_events(user_id);
CREATE INDEX idx_unlock_events_concept ON concept_unlock_events(concept_id);
CREATE INDEX idx_unlock_events_recent ON concept_unlock_events(user_id, unlocked_at DESC);
CREATE INDEX idx_unlock_events_unnotified ON concept_unlock_events(user_id, notified)
    WHERE notified = FALSE;
```

### Table: `concept_lock_status`

Cached lock status for performance (derived from belief_states and concept_prerequisites).

```sql
CREATE TABLE concept_lock_status (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    concept_id UUID NOT NULL REFERENCES concepts(concept_id) ON DELETE CASCADE,

    -- Lock state
    is_locked BOOLEAN NOT NULL DEFAULT TRUE,
    lock_reason VARCHAR(100),  -- 'prereq_not_mastered: Stakeholder Analysis' or null if unlocked

    -- Progress toward unlock
    blocking_prereq_id UUID REFERENCES concepts(concept_id),
    blocking_prereq_mastery DECIMAL(5,4),  -- Current mastery of blocking prereq
    required_mastery DECIMAL(5,4) DEFAULT 0.7000,  -- Threshold needed
    estimated_questions_to_unlock INT,  -- Rough estimate

    -- Cache management
    last_calculated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    UNIQUE(user_id, concept_id)
);

CREATE INDEX idx_lock_status_user ON concept_lock_status(user_id);
CREATE INDEX idx_lock_status_locked ON concept_lock_status(user_id, is_locked) WHERE is_locked = TRUE;
CREATE INDEX idx_lock_status_unlocked ON concept_lock_status(user_id, is_locked) WHERE is_locked = FALSE;
```

---

## REMOVED Tables

The following tables from the original schema are **removed** in BKT architecture:

### `competency_tracking` (REMOVED)

Replaced by `belief_states`. Competency scores are now derived from Beta distribution parameters, not stored directly.

**Migration:** Existing competency data can be converted to belief states:
```sql
-- Example migration (conceptual)
INSERT INTO belief_states (user_id, concept_id, alpha, beta)
SELECT
    ct.user_id,
    c.concept_id,
    (ct.competency_score / 100) * 10 + 1,  -- Convert score to alpha
    ((100 - ct.competency_score) / 100) * 10 + 1  -- Convert to beta
FROM competency_tracking ct
CROSS JOIN concepts c
WHERE c.ka_id = ct.ka_id;
```

### `concept_mastery` (REMOVED)

Functionality absorbed by `belief_states`. The Beta distribution provides more nuanced mastery tracking than the 0-5 scale.

---

## Summary of Tables

### Core Tables

| Table | Status | Purpose |
|-------|--------|---------|
| `users` | Modified | User accounts (added `timezone` field) |
| `knowledge_areas` | Unchanged | 6 CBAP KAs for aggregation |

### Knowledge Graph Tables

| Table | Status | Purpose |
|-------|--------|---------|
| `concepts` | **NEW** | Corpus of testable concepts (includes extraction metadata) |
| `concept_prerequisites` | **NEW** | Prerequisite DAG for learning paths |

### Question Tables

| Table | Status | Purpose |
|-------|--------|---------|
| `questions` | Modified | Added IRT params (b-parameter -3.0 to +3.0), difficulty_label column |
| `question_concepts` | **NEW** | Question-concept mapping |

### Belief State Tables

| Table | Status | Purpose |
|-------|--------|---------|
| `belief_states` | **NEW** | User knowledge state (replaces competency_tracking) |
| `belief_states_computed` | **NEW** | Materialized view for computed properties |

### Quiz Session Tables

| Table | Status | Purpose |
|-------|--------|---------|
| `quiz_sessions` | Modified | Added info_gain tracking |
| `quiz_responses` | Modified | Added belief update tracking |
| `diagnostic_sessions` | **NEW** | Diagnostic state management |

### Content Tables

| Table | Status | Purpose |
|-------|--------|---------|
| `content_chunks` | Modified | Added chunk_index |
| `chunk_concepts` | **NEW** | Chunk-concept mapping |

### User Preferences Tables (Epic 11)

| Table | Status | Purpose |
|-------|--------|---------|
| `notification_preferences` | **NEW** | User notification channel and timing settings |

### Gamification Tables (Epic 11)

| Table | Status | Purpose |
|-------|--------|---------|
| `study_streaks` | **NEW** | User streak state and freeze tracking |
| `daily_activity` | **NEW** | Daily activity log for streak calculation |
| `study_goals` | **NEW** | User-defined daily/weekly study goals |
| `achievements` | **NEW** | Achievement/badge definitions (16 seeded) |
| `user_achievements` | **NEW** | User's earned achievements |
| `notifications` | **NEW** | In-app notification storage and delivery tracking |

### Mastery Gates Tables (Story 4.11)

| Table | Status | Purpose |
|-------|--------|---------|
| `concept_unlock_events` | **NEW** | Tracks when concepts become unlocked |
| `concept_lock_status` | **NEW** | Cached lock status for performance |

### Removed Tables

| Table | Status | Purpose |
|-------|--------|---------|
| `competency_tracking` | **REMOVED** | Replaced by belief_states |
| `concept_mastery` | **REMOVED** | Replaced by belief_states |

---

## Migration Strategy

### Phase 1: Add New Tables
```sql
-- Run after creating tables above
-- Populate concepts from BABOK extraction (Epic 2.2)
-- Populate concept_prerequisites (Epic 2.3)
-- Populate question_concepts (Epic 2.4)
```

### Phase 2: Initialize Belief States for Existing Users
```sql
-- For each existing user, create belief states for all concepts
INSERT INTO belief_states (user_id, concept_id, alpha, beta, response_count)
SELECT
    u.user_id,
    c.concept_id,
    1.0,  -- Uninformative prior
    1.0,  -- Uninformative prior
    0
FROM users u
CROSS JOIN concepts c
WHERE NOT EXISTS (
    SELECT 1 FROM belief_states bs
    WHERE bs.user_id = u.user_id AND bs.concept_id = c.concept_id
);
```

### Phase 3: Backfill Beliefs from History
```sql
-- Optional: Use historical quiz_responses to update beliefs
-- Run BKT update algorithm on historical responses
```

---

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-12-23 | 3.1 | **Story 10.1 IRT Scale Migration:** Updated `questions` table difficulty constraint from `0.0-1.0` to `-3.0 to +3.0` (IRT b-parameter scale); Added `difficulty_label` column (VARCHAR(10)) for human-readable labels (Easy/Medium/Hard); Updated default from 0.50 to 0.00 (medium difficulty center) | James (Dev) |
| 2025-12-22 | 3.0 | **Epic 11 & Story 4.11 Infrastructure:** Added `timezone` field to users table; Added User Preferences section (`notification_preferences`); Added Gamification section (`study_streaks`, `daily_activity`, `study_goals`, `achievements`, `user_achievements`, `notifications`); Added Mastery Gates section (`concept_unlock_events`, `concept_lock_status`); Reorganized summary table by category | Winston (Architect) |
| 2025-11-27 | 2.1 | Added extraction metadata fields to concepts table (keywords, source_sections, extraction_confidence, review_status) per Story 2.2 requirements | Sarah (Product Owner) |
| 2025-11-27 | 2.0 | BKT-first schema redesign; Added concepts, concept_prerequisites, question_concepts, belief_states, chunk_concepts; Modified questions, quiz_sessions, quiz_responses; Removed competency_tracking, concept_mastery | Sarah (Product Owner) |
