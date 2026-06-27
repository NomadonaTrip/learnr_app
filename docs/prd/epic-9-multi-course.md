# Epic 9: Multi-Course Platform Architecture

**Epic Goal:** Transform LearnR from a single-course CBAP application into a multi-course platform capable of supporting multiple certifications (PSM1, CFA Level 1, etc.) while maintaining full backward compatibility with existing CBAP functionality. This epic establishes the foundational data model and infrastructure for course extensibility.

**Strategic Context:** This is Phase 1 of the platform expansion strategy, validating multi-course architecture before Phase 2 (user-generated content). Success here proves the BKT engine is course-agnostic.

**Architecture Reference:** See `docs/architecture/bkt-architecture.md` for Bayesian Knowledge Tracing design (100% reusable across courses).

---

## Key Design Principles

1. **Course Isolation** - Content never leaks between courses; users see only enrolled course data
2. **Shared Infrastructure** - BKT engine, quiz delivery, reading library work identically across all courses
3. **Self-Describing Courses** - Each course defines its own knowledge areas, thresholds, and import rules
4. **Enrollment-Centric** - User progress is per-enrollment, not global (same user can take multiple courses)
5. **Backward Compatible** - Existing CBAP users experience zero disruption

---

## Story 9.1: Course and Enrollment Database Schema

As a **backend developer**,
I want to create database tables for courses and user enrollments,
so that the platform can support multiple certification courses.

**Acceptance Criteria:**

1. Create `courses` table:
   ```sql
   CREATE TABLE courses (
       id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
       slug VARCHAR(50) UNIQUE NOT NULL,  -- 'cbap', 'psm1', 'cfa-l1'
       name VARCHAR(255) NOT NULL,         -- 'CBAP Certification Prep'
       description TEXT,
       corpus_name VARCHAR(100),           -- 'BABOK v3', 'Scrum Guide 2020'
       knowledge_areas JSONB NOT NULL,     -- Dynamic KA definitions
       default_diagnostic_count INTEGER DEFAULT 12,
       mastery_threshold FLOAT DEFAULT 0.8,
       gap_threshold FLOAT DEFAULT 0.5,
       confidence_threshold FLOAT DEFAULT 0.7,
       is_active BOOLEAN DEFAULT TRUE,
       is_public BOOLEAN DEFAULT TRUE,     -- Visible in course catalog
       icon_url VARCHAR(500),
       color_hex VARCHAR(7),               -- Brand color for UI
       created_at TIMESTAMP DEFAULT NOW(),
       updated_at TIMESTAMP DEFAULT NOW()
   );
   ```
2. Create `enrollments` table:
   ```sql
   CREATE TABLE enrollments (
       id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
       user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
       course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
       exam_date DATE,
       target_score INTEGER,
       daily_study_time INTEGER,           -- Minutes per day commitment
       enrolled_at TIMESTAMP DEFAULT NOW(),
       last_activity_at TIMESTAMP,
       status VARCHAR(20) DEFAULT 'active', -- active, paused, completed, archived
       completion_percentage FLOAT DEFAULT 0,
       created_at TIMESTAMP DEFAULT NOW(),
       updated_at TIMESTAMP DEFAULT NOW(),
       UNIQUE (user_id, course_id)
   );
   ```
3. Seed CBAP course as first record with slug='cbap'
4. Knowledge areas stored as JSONB array:
   ```json
   [
     {"id": "ba-planning", "name": "Business Analysis Planning and Monitoring", "display_order": 1},
     {"id": "elicitation", "name": "Elicitation and Collaboration", "display_order": 2},
     ...
   ]
   ```
5. Alembic migration with rollback support
6. Indexes on: `courses(slug)`, `enrollments(user_id)`, `enrollments(course_id)`, `enrollments(user_id, course_id)`
7. Trigger to update `updated_at` on both tables
8. Unit tests: Create course, create enrollment, unique constraint validation

**Integration Verification:**
- IV1: Existing CBAP users can still log in and access their data
- IV2: Database migration runs without affecting existing tables
- IV3: Query performance for user enrollments <10ms

---

## Story 9.2: Add Course Foreign Keys to Content Tables

As a **backend developer**,
I want to add course_id references to concepts, questions, and reading_chunks tables,
so that content is properly scoped to courses.

**Acceptance Criteria:**

1. Add nullable `course_id` column to:
   - `concepts` table (FK to courses)
   - `questions` table (FK to courses)
   - `reading_chunks` table (FK to courses)
2. Backfill existing records: Set course_id = CBAP course UUID for all existing data
3. Add indexes on course_id for each table
4. Update question_concepts and chunk_concepts junction tables (inherit course from parent)
5. Database constraints:
   - Question's concepts must belong to same course as question
   - Chunk's concepts must belong to same course as chunk
6. Migration is reversible (can drop columns if needed)
7. Validate: All existing CBAP content has course_id set
8. Performance: Queries with course_id filter use index

**Integration Verification:**
- IV1: Existing API endpoints return same results (filtered to CBAP implicitly)
- IV2: BKT engine continues to function with existing beliefs
- IV3: No orphaned content (all records have valid course_id)

---

## Story 9.3: Course-Scoped Belief States

As a **backend developer**,
I want belief states to be scoped to course enrollments,
so that a user's mastery in one course doesn't affect another.

**Acceptance Criteria:**

1. Belief states already scoped via concept_id → course relationship
2. Add validation: When creating belief state, verify concept belongs to user's enrolled course
3. Update `initialize_beliefs()` function:
   ```python
   async def initialize_beliefs(user_id: UUID, course_id: UUID) -> int:
       """Initialize belief states for all concepts in a course."""
       concepts = await get_concepts_for_course(course_id)
       # Create Beta(1,1) uninformative prior for each concept
   ```
4. Coverage report endpoint accepts `course_id` parameter
5. Belief queries always filter by course (via concept.course_id)
6. Add database function to initialize beliefs for new enrollment
7. Unit test: User enrolled in two courses has separate belief states
8. Validate: Belief updates only affect concepts in same course

**Integration Verification:**
- IV1: Existing CBAP belief states unchanged
- IV2: Coverage percentage calculated per-course
- IV3: BKT question selection filters to enrolled course

---

## Story 9.4: Course-Scoped Quiz Sessions

As a **backend developer**,
I want quiz sessions to be associated with a specific course enrollment,
so that session history and analytics are course-specific.

**Acceptance Criteria:**

1. Add `enrollment_id` column to `quiz_sessions` table (FK to enrollments)
2. Backfill: Create CBAP enrollments for existing users, link sessions
3. Quiz session creation requires enrollment_id
4. Responses inherit course context from session
5. Update session APIs:
   - POST `/api/v1/quiz/start` requires `course_id` (derives enrollment)
   - GET `/api/v1/quiz/sessions` filters by course
6. Question selection uses course_id to filter question pool
7. Session statistics aggregated per-course
8. Validate: Cannot start quiz for course user isn't enrolled in

**Integration Verification:**
- IV1: Existing quiz sessions associated with CBAP enrollment
- IV2: Quiz flow unchanged for single-course users
- IV3: Session history displays correctly per course

---

## Story 9.5: Course Catalog API

As a **frontend developer**,
I want API endpoints to browse available courses,
so that users can discover and enroll in courses.

**Acceptance Criteria:**

1. GET `/api/v1/courses` - List available courses
   - Query params: `is_active=true` (default), `search` (name search)
   - Returns: id, slug, name, description, icon_url, color_hex, knowledge_area_count
   - Public endpoint (no auth required for browsing)
   - Sorted by display_order or popularity
2. GET `/api/v1/courses/{slug}` - Get course details
   - Returns: Full course object with knowledge_areas array
   - Include: concept_count, question_count, enrolled_user_count
   - Public endpoint
3. GET `/api/v1/courses/{slug}/preview` - Course preview
   - Returns: Sample questions (3), sample reading content
   - Public endpoint (marketing/discovery)
4. Response caching: Course list cached 1 hour
5. Performance: <100ms for course list
6. Unit tests: List courses, filter active, get by slug

---

## Story 9.6: Enrollment Management API

As a **backend developer**,
I want API endpoints for users to enroll in and manage courses,
so that users can start learning new certifications.

**Acceptance Criteria:**

1. POST `/api/v1/enrollments` - Enroll in course
   - Body: `{ "course_id": UUID, "exam_date": date?, "target_score": int? }`
   - Creates enrollment record
   - Initializes belief states for all course concepts
   - Returns enrollment object with course details
   - Auth required
2. GET `/api/v1/enrollments` - List user's enrollments
   - Returns: Array of enrollments with course summary
   - Include: completion_percentage, last_activity_at, status
   - Auth required
3. GET `/api/v1/enrollments/{id}` - Get enrollment details
   - Returns: Full enrollment with course and progress summary
   - Auth required (must be owner)
4. PATCH `/api/v1/enrollments/{id}` - Update enrollment
   - Body: `{ "exam_date": date?, "target_score": int?, "status": string? }`
   - Auth required (must be owner)
5. DELETE `/api/v1/enrollments/{id}` - Archive enrollment
   - Soft delete (set status='archived')
   - Preserves data for potential reactivation
   - Auth required (must be owner)
6. Validation: Cannot enroll in same course twice
7. Side effect: First enrollment triggers welcome flow
8. Unit tests: Full CRUD operations, authorization checks

---

## Story 9.7: Dynamic Knowledge Area Handling

As a **backend developer**,
I want knowledge areas to be loaded dynamically from course configuration,
so that each course can define its own knowledge structure.

**Acceptance Criteria:**

1. Remove hardcoded `KnowledgeArea` enum from codebase
2. Create `CourseConfig` service that loads KAs from course.knowledge_areas JSONB
3. KA-related queries join through course:
   ```python
   # Before (hardcoded)
   concepts = query.filter(Concept.knowledge_area == 'Elicitation')

   # After (dynamic)
   concepts = query.filter(Concept.knowledge_area_id == ka_id)
   ```
4. Coverage report uses course's KA definitions
5. Dashboard KA bars generated from course.knowledge_areas
6. Frontend receives KA list as part of course data (not hardcoded)
7. TypeScript types generated from API response (not static enum)
8. Validate: CBAP displays same 6 KAs as before
9. Unit test: Course with different KA count displays correctly

**Integration Verification:**
- IV1: CBAP dashboard shows 6 knowledge areas
- IV2: Coverage by KA endpoint returns course-specific KAs
- IV3: No TypeScript type errors from KA changes

---

## Story 9.8: Course Context in Frontend State

As a **frontend developer**,
I want the frontend to track active course context,
so that all views display course-appropriate content.

**Acceptance Criteria:**

1. Add `activeEnrollment` to global state (Context or Zustand)
2. Course selector component in header/sidebar
3. Switching courses updates:
   - Dashboard data (coverage, progress)
   - Quiz question pool
   - Reading library content
   - Navigation breadcrumbs
4. URL structure: `/courses/{slug}/dashboard`, `/courses/{slug}/quiz`
5. Deep links work: User can bookmark course-specific pages
6. Persist last active course in localStorage
7. Auto-select: If user has one enrollment, auto-select it
8. Loading states during course switch
9. Error handling: Redirect if accessing unenrolled course

**Integration Verification:**
- IV1: Existing CBAP URLs redirect to `/courses/cbap/...`
- IV2: Single-course users see no course selector clutter
- IV3: Page refresh maintains course context

---

## Story 9.9: Course-Scoped Reading Queue

As a **backend developer**,
I want the reading queue to be scoped to course enrollment,
so that reading recommendations are course-specific.

**Acceptance Criteria:**

1. Add `enrollment_id` column to `reading_queue` table
2. Backfill: Link existing queue items to CBAP enrollment
3. Reading queue APIs filter by enrollment:
   - GET `/api/v1/reading-queue` requires active course context
   - POST `/api/v1/reading-queue` associates with enrollment
4. Reading recommendations use course's reading_chunks
5. Queue badge count is per-course
6. Validation: Cannot add reading from different course
7. Unit test: User with two enrollments has separate queues

**Integration Verification:**
- IV1: Existing reading queue items visible under CBAP
- IV2: Badge count unchanged for single-course users
- IV3: Queue filtering performs well (<50ms)

---

## Story 9.10: Course Content Import Pipeline

As a **content manager**,
I want a standardized process for importing content into new courses,
so that new certifications can be added efficiently.

**Acceptance Criteria:**

1. Create `/scripts/import_course_content.py` master script
2. Course content package structure:
   ```
   courses/
     psm1/
       course_config.yaml      # Course metadata, KA definitions
       concepts.csv            # Concept list with prerequisites
       questions.csv           # Question bank
       reading_chunks/         # Markdown files for reading content
       embeddings/             # Pre-computed embeddings (optional)
   ```
3. Import process:
   - Validate course_config.yaml schema
   - Create course record
   - Import concepts with prerequisite graph
   - Import questions with concept mappings
   - Import reading chunks
   - Generate embeddings (if not pre-computed)
   - Run validation script
4. Dry-run mode: Validate without inserting
5. Incremental update mode: Add new content to existing course
6. Rollback on failure: Transaction-based import
7. Detailed logging: Progress, warnings, errors
8. Documentation: README for content package format

---

## Story 9.11: Course Administration UI (Internal)

As an **admin user**,
I want to view and manage courses through an admin interface,
so that I can monitor course health and user activity.

**Acceptance Criteria:**

1. Admin route: `/admin/courses` (requires is_admin=true)
2. Course list view:
   - Name, slug, status, enrollment count, question count
   - Quick actions: Activate/deactivate, view details
3. Course detail view:
   - Enrollment statistics (active, paused, completed)
   - Content statistics (concepts, questions, chunks)
   - Coverage distribution across users
   - Recent activity feed
4. No course editing in MVP (use scripts for content changes)
5. Export: Download enrollment list as CSV
6. Performance: Dashboard loads <2s with 10k enrollments

**Integration Verification:**
- IV1: Admin can view CBAP course statistics
- IV2: Non-admin users cannot access admin routes
- IV3: Large enrollment counts don't crash UI

---

## Story 9.12: Migration Script for Existing Users

As a **backend developer**,
I want a migration script that creates CBAP enrollments for existing users,
so that current users experience seamless transition.

**Acceptance Criteria:**

1. Create `/scripts/migrate_to_multi_course.py`
2. Migration steps:
   - Create CBAP course record (if not exists)
   - For each existing user:
     - Create enrollment with status='active'
     - Copy exam_date, target_score from users table
     - Link existing quiz_sessions to enrollment
     - Link existing reading_queue items to enrollment
3. Validation:
   - All users have exactly one CBAP enrollment
   - All quiz sessions linked
   - All reading queue items linked
   - Belief states accessible via enrollment
4. Idempotent: Safe to run multiple times
5. Dry-run mode with detailed report
6. Rollback script: Undo migration if needed
7. Performance: Handle 10k users in <5 minutes
8. Audit log: Record migration timestamp and counts

**Integration Verification:**
- IV1: Existing user logs in, sees same dashboard
- IV2: Quiz history preserved and accessible
- IV3: Reading queue unchanged

---

## Dependencies

```
Epic 9 Story Dependencies:

9.1 (Schema) → 9.2, 9.3, 9.4, 9.6 (All need courses/enrollments tables)
9.2 (Content FKs) → 9.3, 9.10 (Content scoping needed for beliefs and import)
9.3 (Belief Scoping) → 9.4 (Sessions need scoped beliefs)
9.5 (Catalog API) → 9.6 (Enrollment needs catalog)
9.6 (Enrollment API) → 9.8 (Frontend needs enrollment API)
9.7 (Dynamic KA) → 9.8 (Frontend needs dynamic KAs)
9.1, 9.2, 9.4 → 9.12 (Migration needs all schema changes)
9.12 (Migration) → 9.11 (Admin needs migrated data)

Critical Path: 9.1 → 9.2 → 9.3 → 9.4 → 9.12 → 9.6 → 9.8

Parallel Work:
- 9.5 (Catalog API) can start after 9.1
- 9.7 (Dynamic KA) can start after 9.1
- 9.10 (Import Pipeline) can start after 9.2
- 9.9 (Reading Queue) can start after 9.4
```

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Migration success rate | 100% of existing users |
| Course switch latency | <500ms |
| Enrollment creation time | <2s (includes belief init) |
| API backward compatibility | 100% (no breaking changes) |
| CBAP user experience change | Zero (transparent migration) |
| New course setup time | <4 hours (with content ready) |

---

## Future Considerations (Out of Scope)

- **Course marketplace** - Purchasing/licensing courses
- **Course sharing** - Users sharing custom courses
- **Course templates** - Creating courses from templates
- **Cross-course analytics** - Comparing progress across courses
- **Course recommendations** - Suggesting courses based on interests

These are deferred to Phase 2+ after validating multi-course demand.

---

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-12-08 | 1.0 | Initial multi-course architecture epic | Winston (Architect) |
