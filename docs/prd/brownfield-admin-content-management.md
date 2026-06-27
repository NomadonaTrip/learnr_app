# Admin Content Management - Brownfield Enhancement PRD

**Document Version:** 1.0
**Status:** Draft
**Created:** 2025-12-17
**Author:** John (PM Agent)

---

## Table of Contents

1. [Intro Project Analysis and Context](#1-intro-project-analysis-and-context)
2. [Requirements](#2-requirements)
3. [User Interface Enhancement Goals](#3-user-interface-enhancement-goals)
4. [Technical Constraints and Integration Requirements](#4-technical-constraints-and-integration-requirements)
5. [Epic and Story Structure](#5-epic-and-story-structure)
6. [Epic 10: Admin Content Management Infrastructure](#6-epic-10-admin-content-management-infrastructure)
7. [Epic 11: Content Moderation & Quality](#7-epic-11-content-moderation--quality)
8. [Change Log](#8-change-log)

---

## 1. Intro Project Analysis and Context

### 1.1 Scope Assessment

This enhancement **qualifies for a full Brownfield PRD** because:
- Introduces a new user persona (Content Manager/SME)
- Requires multiple coordinated stories across backend, frontend, and database
- Involves architectural decisions (workflow design, role granularity, API structure)
- Spawns 2 epics worth of implementation work

### 1.2 Existing Project Overview

#### Analysis Source
- **IDE-based analysis** combined with existing documentation
- **Document-project output available:** `docs/architecture/`, `docs/prd/`
- **Prior analysis:** Gap analysis of Epic 9 vs. admin content management needs

#### Current Project State

LearnR is an adaptive learning platform for certification exam preparation, currently focused on CBAP (Certified Business Analysis Professional). The system uses Bayesian Knowledge Tracing (BKT) to model learner mastery and deliver personalized quiz experiences.

**Key capabilities:**
- Diagnostic assessments with belief state initialization
- Adaptive quiz sessions with BKT-driven question selection
- Reading recommendations based on knowledge gaps
- Coverage reporting by knowledge area

**Current architecture:**
- FastAPI backend with PostgreSQL database
- React/TypeScript frontend
- Multi-course schema foundation (Epic 9 in progress)

### 1.3 Available Documentation Analysis

| Documentation | Status | Location |
|---------------|--------|----------|
| Tech Stack Documentation | Available | `docs/architecture/tech-stack.md` |
| Source Tree/Architecture | Available | `docs/architecture/` (sharded) |
| Coding Standards | Available | `docs/architecture/coding-standards.md` |
| API Documentation | Available | Route files + schemas |
| PRD Documentation | Available | `docs/prd/` (sharded, v4) |
| UX/UI Guidelines | Partial | Embedded in stories |
| Technical Debt Documentation | Limited | Not formalized |

### 1.4 Enhancement Scope Definition

#### Enhancement Type
- [x] **New Feature Addition** - Admin content management capabilities
- [x] **Integration with New Systems** - Admin UI, moderation workflows

#### Enhancement Description

Add comprehensive admin content management capabilities to LearnR, enabling Content Managers and SMEs to create, review, approve, and maintain quiz content (questions, concepts, reading materials) through web-based interfaces rather than CLI scripts. This includes content lifecycle management, user report triage, and content health monitoring.

#### Impact Assessment
- [x] **Significant Impact** (substantial existing code changes)

**Rationale:** Requires new database tables (admin_audit_log, question_reports), new API namespace (`/api/admin/*`), new middleware (`@require_admin`), and frontend admin routes. However, core BKT engine and learner-facing features remain unchanged.

### 1.5 Goals

- Enable Content Managers to add/edit/retire questions without developer intervention
- Provide SME review workflows for content quality assurance
- Allow users to report problematic questions with triage capabilities
- Surface content health metrics for proactive quality management
- Support multi-course content management (aligned with Epic 9)
- Maintain audit trail of all content changes

### 1.6 Background Context

The current LearnR implementation relies entirely on CLI scripts for content management (`extract_babok_concepts.py`, `import_vendor_questions.py`). While effective for initial CBAP content setup, this approach creates operational bottlenecks:

1. **Developer dependency** - Every content change requires developer time
2. **No real-time moderation** - User-reported issues cannot be triaged efficiently
3. **No content lifecycle** - Questions cannot be drafted, reviewed, then published
4. **Scaling barrier** - Adding new courses (PSM1, PMP) requires repeating manual processes

Epic 9 establishes the multi-course data model but explicitly defers admin editing capabilities ("No course editing in MVP - use scripts for content changes"). This brownfield PRD addresses that gap, enabling the platform to scale content operations alongside course expansion.

---

## 2. Requirements

### 2.1 Functional Requirements

#### Admin Authentication & Authorization

| ID | Requirement |
|----|-------------|
| **FR1** | The system shall implement `@require_admin` middleware that validates `users.is_admin=true` before allowing access to admin endpoints |
| **FR2** | Admin endpoints shall be namespaced under `/api/v1/admin/*` and return 403 Forbidden for non-admin users |
| **FR3** | Admin users shall be able to impersonate regular users for debugging purposes, with a 30-minute time-limited JWT and full audit logging |

#### Question Management

| ID | Requirement |
|----|-------------|
| **FR4** | Admins shall be able to create new questions with: question_text, options (JSONB), correct_answer, explanation, difficulty, course_id, and concept mappings |
| **FR5** | Admins shall be able to update existing questions, with changes tracked in an audit log |
| **FR6** | Admins shall be able to retire questions (soft delete) rather than hard delete, preserving historical data integrity |
| **FR7** | Admins shall be able to view a list of questions with filtering by: course, status, source (vendor/llm_generated), concept, and date range |
| **FR8** | The system shall support question status lifecycle: `draft` → `pending_review` → `approved` → `published` → `retired` |

#### Concept Management

| ID | Requirement |
|----|-------------|
| **FR9** | Admins shall be able to create, update, and archive concepts within a course scope |
| **FR10** | When a concept is archived, the system shall flag associated questions for review |
| **FR11** | Admins shall be able to view concept coverage metrics (questions per concept, min/max thresholds) |

#### Reading Content Management

| ID | Requirement |
|----|-------------|
| **FR12** | Admins shall be able to create, update, and archive reading chunks with markdown content |
| **FR13** | Reading chunks shall support concept linking with relevance scores |
| **FR14** | The system shall auto-generate embeddings when reading content is created or updated |

#### Content Moderation & Quality

| ID | Requirement |
|----|-------------|
| **FR15** | Users shall be able to report questions as incorrect, confusing, or inappropriate via a report form |
| **FR16** | The system shall create `question_reports` records with: user_id, question_id, issue_type, description, status, created_at |
| **FR17** | Admins shall be able to view a triage queue of reported questions, sorted by report count and recency |
| **FR18** | Questions with 5+ reports in 24 hours shall be auto-flagged for emergency review |
| **FR19** | Questions with 2+ reports in 7 days shall be escalated to the SME review queue |
| **FR20** | Admins shall be able to resolve reports with actions: dismiss, edit question, retire question |

#### Content Health Dashboard

| ID | Requirement |
|----|-------------|
| **FR21** | Admins shall have access to a content health dashboard showing: question count by status, concept coverage gaps, report backlog, and anomalous metrics |
| **FR22** | The system shall flag questions with anomalous performance metrics: >90% correct (too easy), <30% correct (needs review) |
| **FR23** | The dashboard shall display content health KPIs per course |

#### Audit Logging

| ID | Requirement |
|----|-------------|
| **FR24** | All admin content operations shall be logged to `admin_audit_log` with: admin_id, action, resource_type, resource_id, changes (JSONB), timestamp |
| **FR25** | Admins shall be able to view audit history filtered by resource, action type, admin user, and date range |

#### Bulk Operations

| ID | Requirement |
|----|-------------|
| **FR26** | Admins shall be able to bulk import questions via CSV/JSON upload with validation preview |
| **FR27** | Admins shall be able to bulk export questions for external review or backup |
| **FR28** | Import operations shall support dry-run mode showing validation results before committing |

### 2.2 Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| **NFR1** | Admin endpoints shall respond within 500ms for single-resource operations and 2s for list/dashboard operations |
| **NFR2** | Bulk import shall handle up to 1000 questions per operation without timeout |
| **NFR3** | The admin UI shall be responsive and functional on desktop browsers (mobile not required for MVP) |
| **NFR4** | Audit log queries shall perform efficiently with up to 1M records (indexed by resource_type, created_at) |
| **NFR5** | Admin operations shall not impact learner-facing API performance (separate query patterns) |
| **NFR6** | Content changes shall be eventually consistent - learners may see cached content for up to 5 minutes after admin changes |

### 2.3 Compatibility Requirements

| ID | Requirement |
|----|-------------|
| **CR1** | **Existing API Compatibility**: All existing learner-facing endpoints (`/api/v1/quiz/*`, `/api/v1/beliefs/*`, etc.) shall continue to function without modification |
| **CR2** | **Database Schema Compatibility**: New tables and columns shall be additive - no breaking changes to existing tables except adding nullable `status` column to `questions` table |
| **CR3** | **UI/UX Consistency**: Admin UI shall use the same design system (component library, color palette, typography) as the learner-facing application |
| **CR4** | **Epic 9 Integration**: Admin content management shall be fully course-scoped, integrating with the multi-course architecture from Epic 9 |
| **CR5** | **Existing Content Compatibility**: All existing CBAP questions, concepts, and reading chunks shall be backfilled with `status='published'` to maintain current behavior |

---

## 3. User Interface Enhancement Goals

### 3.1 Integration with Existing UI

The admin interface will be a **separate route namespace** (`/admin/*`) within the existing React application, sharing the same design system but with a distinct navigation context.

| Aspect | Approach |
|--------|----------|
| **Entry point** | Admin users see an "Admin" link in the main navigation header (conditionally rendered based on `is_admin` flag) |
| **Layout** | Admin pages use the same shell layout (header, sidebar pattern) but with admin-specific navigation |
| **Components** | Reuse existing component library (buttons, forms, tables, modals) for visual consistency |
| **State management** | Admin state is isolated from learner state - switching to admin view doesn't affect active enrollment context |
| **Routing** | Protected routes under `/admin/*` redirect non-admins to dashboard with error toast |

### 3.2 Modified/New Screens and Views

#### New Admin Screens

| Screen | Purpose | Key Components |
|--------|---------|----------------|
| **Admin Dashboard** (`/admin`) | Content health overview, quick stats, action items | KPI cards, charts, alert list |
| **Question Manager** (`/admin/questions`) | List, filter, create, edit questions | Data table, filters, bulk actions |
| **Question Editor** (`/admin/questions/new`, `/admin/questions/:id`) | Create/edit question form | Rich form, concept selector, preview |
| **Concept Manager** (`/admin/concepts`) | List, filter, manage concepts | Data table, coverage metrics |
| **Reading Manager** (`/admin/reading`) | List, manage reading chunks | Data table, markdown editor |
| **Report Triage** (`/admin/reports`) | View and resolve user reports | Queue list, resolution actions |
| **Audit Log** (`/admin/audit`) | View admin activity history | Filterable log table |
| **Bulk Import** (`/admin/import`) | Upload and validate content files | File upload, validation preview, progress |

#### Modified Existing Screens

| Screen | Modification |
|--------|--------------|
| **Main Header** | Add conditional "Admin" navigation link for admin users |
| **Quiz Answer View** | Add "Report Question" button (learner-facing, feeds into FR15) |

### 3.3 UI Consistency Requirements

| Requirement | Specification |
|-------------|---------------|
| **Color coding** | Use existing semantic colors: success (green), warning (amber), error (red), info (blue) for status indicators |
| **Table patterns** | Follow existing table component patterns: sortable columns, pagination, row actions dropdown |
| **Form patterns** | Use existing form components: input fields, select dropdowns, validation messages |
| **Modal patterns** | Confirmation modals for destructive actions (retire, bulk delete), form modals for quick edits |
| **Empty states** | Consistent empty state illustrations and messaging |
| **Loading states** | Skeleton loaders for tables, spinner for actions |
| **Error handling** | Toast notifications for operation results, inline validation for forms |
| **Responsive behavior** | Admin UI optimized for desktop (1024px+), functional but not optimized for tablet/mobile |

### 3.4 Admin Navigation Structure

```
/admin
├── Dashboard (default)
├── Content
│   ├── Questions
│   ├── Concepts
│   └── Reading
├── Moderation
│   └── Reports
├── Analytics
│   └── Content Health
├── System
│   ├── Audit Log
│   └── Bulk Import
└── (Course selector in header - scopes all views)
```

---

## 4. Technical Constraints and Integration Requirements

### 4.1 Existing Technology Stack

| Layer | Technology | Version/Notes |
|-------|------------|---------------|
| **Backend Language** | Python | 3.11+ |
| **Backend Framework** | FastAPI | Async-first, Pydantic v2 |
| **Database** | PostgreSQL | 14+, with JSONB support |
| **ORM** | SQLAlchemy | 2.0 async with Alembic migrations |
| **Frontend Language** | TypeScript | Strict mode |
| **Frontend Framework** | React | 18+ with hooks |
| **Styling** | Tailwind CSS | Utility-first |
| **Authentication** | JWT | Access + refresh tokens |
| **Testing** | pytest (backend), Vitest (frontend) | |

### 4.2 Integration Approach

#### Database Integration Strategy

| Aspect | Approach |
|--------|----------|
| **New tables** | `admin_audit_log`, `question_reports` - additive, no FK changes to existing tables |
| **Schema changes** | Add `status` column to `questions` table (nullable, default 'published' for backfill) |
| **Migrations** | Alembic migrations with `upgrade()` and `downgrade()` functions |
| **Backfill** | Migration script to set existing content to `status='published'` |

**New table schemas:**

```sql
-- admin_audit_log
CREATE TABLE admin_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    admin_id UUID NOT NULL REFERENCES users(id),
    action VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id UUID NOT NULL,
    changes JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- question_reports
CREATE TABLE question_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    question_id UUID NOT NULL REFERENCES questions(id),
    issue_type VARCHAR(50) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    resolution_notes TEXT,
    resolved_by UUID REFERENCES users(id),
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### API Integration Strategy

| Aspect | Approach |
|--------|----------|
| **Namespace** | All admin endpoints under `/api/v1/admin/` |
| **Router** | New `routes/admin/` directory with sub-routers |
| **Middleware** | `require_admin` dependency injection, extending existing `require_auth` |
| **Schemas** | New Pydantic schemas in `schemas/admin/` directory |
| **Services** | New service layer in `services/admin/` for business logic |

#### Frontend Integration Strategy

| Aspect | Approach |
|--------|----------|
| **Routing** | Add `/admin/*` routes with admin guard |
| **Layout** | Create `AdminLayout` component wrapping admin pages |
| **State** | Separate admin store/context from learner state |
| **API client** | Extend existing API client with admin endpoints |

### 4.3 Risk Assessment and Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Admin endpoint security vulnerabilities** | Medium | High | Thorough auth testing, security review |
| **Bulk import performance issues** | Medium | Medium | Implement chunked processing, async jobs |
| **Breaking existing question queries** | Medium | High | Add `status` column as nullable, backfill before enforcing |
| **Epic 9 dependency conflicts** | Medium | Medium | Coordinate with Epic 9 implementation |

---

## 5. Epic and Story Structure

### Epic Structure Decision

This enhancement is structured as **two focused epics**:

| Epic | Focus | Stories | Deliverable Value |
|------|-------|---------|-------------------|
| **Epic 10** | Admin Infrastructure | 16 stories | Content team can manage questions/concepts without developer intervention |
| **Epic 11** | Content Moderation | 12 stories | Proactive content quality management, user feedback loop |

### Dependency Analysis

```
Epic 9 (Multi-Course)
    │
    ├── 9.1-9.4: Schema foundation
    │
    ▼
Epic 10 (Admin Infrastructure)     [Can start after 9.1-9.2]
    │
    ├── Admin auth/middleware
    ├── Question/Concept/Reading CRUD
    ├── Audit logging
    └── Admin UI foundation
          │
          ▼
Epic 11 (Content Moderation)       [Depends on Epic 10]
    │
    ├── User reporting
    ├── Triage workflows
    └── Health dashboard
```

---

## 6. Epic 10: Admin Content Management Infrastructure

### Epic Goal

Enable Content Managers and Admins to create, edit, and manage quiz content (questions, concepts, reading chunks) through web-based interfaces, with full audit logging and multi-course support.

### Integration Requirements

- Must integrate with Epic 9 multi-course schema (course_id scoping)
- Must not disrupt existing learner-facing APIs
- Must use existing authentication system (extend with admin check)
- Must follow existing code patterns (routes, services, repositories)

---

### Story 10.1: Admin Authorization Middleware

As a **backend developer**,
I want to implement admin authorization middleware,
so that admin endpoints are protected from unauthorized access.

**Acceptance Criteria:**

1. Create `require_admin` dependency that extends `require_auth`
2. Verify `user.is_admin == True` before allowing access
3. Return 403 Forbidden with message "Admin access required" for non-admins
4. Log failed admin access attempts (user_id, endpoint, timestamp)
5. Create reusable dependency injection pattern for all admin routes
6. Unit tests: admin user passes, non-admin rejected, unauthenticated rejected

**Integration Verification:**

- IV1: Existing `require_auth` middleware unchanged and functioning
- IV2: Non-admin users accessing admin endpoints receive 403 (not 401)
- IV3: Admin check adds <5ms latency to request

---

### Story 10.2: Admin Audit Log Infrastructure

As a **backend developer**,
I want to create audit logging infrastructure,
so that all admin content operations are tracked for accountability.

**Acceptance Criteria:**

1. Create `admin_audit_log` table via Alembic migration
2. Create `AuditLog` SQLAlchemy model
3. Create `AuditLogRepository` with `create()` and `list()` methods
4. Create `AuditLogService` with `log_action()` helper method
5. Add indexes on `(resource_type, created_at)` and `(admin_id, created_at)`
6. Unit tests: create log entry, query by resource, query by admin

**Integration Verification:**

- IV1: Migration runs without affecting existing tables
- IV2: Audit log queries perform <50ms with 10k records
- IV3: Rollback migration successfully removes table

---

### Story 10.3: Question Status Lifecycle

As a **backend developer**,
I want to add status lifecycle to questions,
so that content can progress through draft, review, and publication states.

**Acceptance Criteria:**

1. Add `status` column to `questions` table (VARCHAR, nullable)
2. Define status enum: `draft`, `pending_review`, `approved`, `published`, `retired`
3. Backfill existing questions with `status = 'published'`
4. Add index on `questions.status`
5. Update existing question queries to filter `status = 'published'` for learner-facing APIs
6. Create status transition validation
7. Unit tests: status transitions, invalid transition rejected, backfill verification

**Integration Verification:**

- IV1: Existing quiz endpoints return same questions (published filter applied)
- IV2: BKT question selection unchanged (only published questions)
- IV3: Diagnostic test uses only published questions

---

### Story 10.4: Question Management API

As a **backend developer**,
I want to create admin endpoints for question CRUD operations,
so that admins can manage questions through the API.

**Acceptance Criteria:**

1. Create admin router at `/api/v1/admin/questions`
2. Implement endpoints:
   - `GET /` - List questions with filters (course_id, status, concept_id, search, pagination)
   - `GET /{id}` - Get question details with concept mappings
   - `POST /` - Create question (draft status by default)
   - `PUT /{id}` - Update question (logs changes to audit)
   - `DELETE /{id}` - Retire question (soft delete)
3. Create Pydantic schemas: `QuestionCreate`, `QuestionUpdate`, `QuestionResponse`, `QuestionListResponse`
4. Validate concept_ids belong to same course as question
5. Log all mutations to audit log
6. Unit tests: full CRUD, authorization, validation, audit logging

**Integration Verification:**

- IV1: Learner-facing `/api/v1/questions` endpoint unchanged
- IV2: Creating question does not affect existing question counts for learners
- IV3: Retiring question removes it from learner quiz pool

---

### Story 10.5: Question Status Transition API

As a **backend developer**,
I want endpoints to transition question status,
so that content can move through the review workflow.

**Acceptance Criteria:**

1. Implement `POST /api/v1/admin/questions/{id}/submit` - draft → pending_review
2. Implement `POST /api/v1/admin/questions/{id}/approve` - pending_review → approved
3. Implement `POST /api/v1/admin/questions/{id}/publish` - approved → published
4. Implement `POST /api/v1/admin/questions/{id}/retire` - any → retired
5. Implement `POST /api/v1/admin/questions/{id}/revert` - retired → draft
6. Each transition logs to audit with previous/new status
7. Invalid transitions return 400 with allowed transitions list
8. Unit tests: valid transitions, invalid transitions, audit logging

**Integration Verification:**

- IV1: Publishing question makes it available to learners
- IV2: Retiring question removes it from active pool immediately
- IV3: Status changes reflected in admin question list

---

### Story 10.6: Concept Management API

As a **backend developer**,
I want admin endpoints for concept management,
so that admins can maintain the concept taxonomy.

**Acceptance Criteria:**

1. Create admin router at `/api/v1/admin/concepts`
2. Implement endpoints:
   - `GET /` - List concepts with filters (course_id, knowledge_area, search, pagination)
   - `GET /{id}` - Get concept with question count, coverage metrics
   - `POST /` - Create concept within course scope
   - `PUT /{id}` - Update concept (name, description, prerequisites)
   - `DELETE /{id}` - Archive concept (soft delete)
3. Include coverage metrics: question_count, published_question_count, min_threshold_met
4. Log all mutations to audit log
5. Unit tests: CRUD, course scoping, coverage calculation

**Integration Verification:**

- IV1: Learner belief states unaffected by concept metadata changes
- IV2: Archived concepts excluded from new question creation
- IV3: Existing concept-question mappings preserved

---

### Story 10.7: Reading Chunk Management API

As a **backend developer**,
I want admin endpoints for reading content management,
so that admins can maintain supplementary learning materials.

**Acceptance Criteria:**

1. Create admin router at `/api/v1/admin/reading`
2. Implement endpoints:
   - `GET /` - List chunks with filters (course_id, knowledge_area, concept_id, pagination)
   - `GET /{id}` - Get chunk with full content and concept mappings
   - `POST /` - Create chunk with markdown content
   - `PUT /{id}` - Update chunk content
   - `DELETE /{id}` - Archive chunk (soft delete)
3. Trigger embedding regeneration on create/update (async background task)
4. Log all mutations to audit log
5. Unit tests: CRUD, embedding trigger, concept validation

**Integration Verification:**

- IV1: Existing reading recommendations continue to work
- IV2: New chunks appear in reading library after embedding generation
- IV3: Archived chunks excluded from recommendations

---

### Story 10.8: Admin Dashboard API

As a **backend developer**,
I want an admin dashboard endpoint,
so that the admin UI can display content health metrics and platform analytics.

**Acceptance Criteria:**

1. Create `GET /api/v1/admin/dashboard` endpoint
2. Return metrics per course:
   - Question counts by status
   - Concept count and coverage summary
   - Reading chunk count
   - Questions below minimum concept threshold
   - Recent admin activity (last 10 audit entries)
3. **Quiz Session Analytics** (system-wide, from Story 4.7):
   - Total quizzes completed (system-wide count)
   - Average session duration (seconds)
   - Average questions per session (should cluster around 10)
   - Quiz completion rate (completed / total started)
   - Total active quiz users (users with at least 1 completed quiz)
4. Accept `course_id` query parameter (required for content metrics, optional for quiz metrics)
5. Cache response for 5 minutes
6. Performance: <500ms response time
7. Unit tests: metrics calculation, caching, course scoping, quiz analytics

**Integration Verification:**

- IV1: Dashboard data consistent with individual list endpoints
- IV2: Metrics update after content changes (within cache TTL)
- IV3: Multi-course switching shows correct per-course data

---

### Story 10.9: Bulk Import API

As a **backend developer**,
I want bulk import endpoints,
so that admins can upload multiple questions at once.

**Acceptance Criteria:**

1. Create `POST /api/v1/admin/import/questions` endpoint
2. Accept CSV or JSON file upload
3. Implement dry-run mode (`?dry_run=true`) returning validation results
4. Validate each row: required fields, concept existence, course match
5. Return detailed validation report
6. On commit: insert questions with status=draft, log bulk import to audit
7. Limit: 1000 questions per import
8. Unit tests: valid import, validation errors, dry-run mode

**Integration Verification:**

- IV1: Imported questions appear in admin question list
- IV2: Imported questions not visible to learners until published
- IV3: Bulk import does not affect existing questions

---

### Story 10.10: Bulk Export API

As a **backend developer**,
I want bulk export endpoints,
so that admins can download content for backup or external review.

**Acceptance Criteria:**

1. Create `GET /api/v1/admin/export/questions` endpoint
2. Accept filters: course_id (required), status, concept_id
3. Return CSV or JSON format based on Accept header
4. Include all question fields plus concept names
5. Limit: 5000 questions per export
6. Log export action to audit
7. Unit tests: export formats, filtering, audit logging

**Integration Verification:**

- IV1: Exported data can be re-imported (round-trip compatibility)
- IV2: Export does not affect database state
- IV3: Large exports complete within 30s

---

### Story 10.11: Audit Log API

As a **backend developer**,
I want an audit log query endpoint,
so that admins can review content change history.

**Acceptance Criteria:**

1. Create `GET /api/v1/admin/audit` endpoint
2. Support filters: resource_type, resource_id, admin_id, action, date_range
3. Return paginated results with admin user details
4. Include change diff (old/new values) in response
5. Performance: <200ms for typical queries
6. Unit tests: filtering, pagination, date range queries

**Integration Verification:**

- IV1: All previous story mutations appear in audit log
- IV2: Audit entries include correct admin attribution
- IV3: Pagination works correctly with large datasets

---

### Story 10.12: Admin UI Layout and Navigation

As a **frontend developer**,
I want to create the admin UI shell,
so that admin pages have consistent layout and navigation.

**Acceptance Criteria:**

1. Create `/admin` route namespace with admin guard (redirect non-admins)
2. Create `AdminLayout` component with:
   - Header with logo, course selector, user menu, "Exit Admin" link
   - Sidebar navigation
   - Main content area
3. Implement course selector dropdown
4. Store selected course in admin state
5. Add "Admin" link to main app header (visible only to admin users)
6. Unit tests: admin guard, navigation rendering, course selection

**Integration Verification:**

- IV1: Non-admin users cannot access /admin routes
- IV2: Course selector shows only enrolled courses
- IV3: Existing learner navigation unchanged

---

### Story 10.13: Admin Dashboard UI

As a **frontend developer**,
I want to build the admin dashboard page,
so that admins can see content health at a glance.

**Acceptance Criteria:**

1. Create `/admin/dashboard` page (default admin landing)
2. Display KPI cards: question count, concept count, reading count, coverage %
3. Display content status breakdown chart
4. Display alerts list
5. Display recent activity feed
6. Loading states and error handling
7. Unit tests: data display, loading states, error states

**Integration Verification:**

- IV1: Dashboard loads within 2s
- IV2: Metrics match data from list pages
- IV3: Course switching updates all dashboard data

---

### Story 10.14: Question Manager UI

As a **frontend developer**,
I want to build the question management interface,
so that admins can browse, create, and edit questions.

**Acceptance Criteria:**

1. Create `/admin/questions` page with filterable data table
2. Create `/admin/questions/new` page with question form
3. Create `/admin/questions/:id` edit page
4. Status transition buttons based on current status
5. Form validation with error messages
6. Unit tests: table interactions, form validation, status transitions

**Integration Verification:**

- IV1: Created questions appear in list after save
- IV2: Status changes reflected immediately in UI
- IV3: Concept selector shows only course-scoped concepts

---

### Story 10.15: Concept and Reading Manager UI

As a **frontend developer**,
I want to build concept and reading management interfaces,
so that admins can maintain all content types.

**Acceptance Criteria:**

1. Create `/admin/concepts` page with data table and coverage metrics
2. Create `/admin/reading` page with markdown editor
3. Both pages: filtering, pagination, search
4. Archive action with confirmation
5. Unit tests: CRUD operations, form validation

**Integration Verification:**

- IV1: Concept coverage updates after question changes
- IV2: Reading chunks show linked concepts
- IV3: Archived items hidden from default view

---

### Story 10.16: Bulk Import UI

As a **frontend developer**,
I want a bulk import interface,
so that admins can upload content files with preview.

**Acceptance Criteria:**

1. Create `/admin/import` page with file upload dropzone
2. Two-step process: Upload → Validate → Confirm Import
3. Validation preview table with inline errors
4. Import progress indicator
5. Cancel/retry capability
6. Unit tests: file handling, validation display, import flow

**Integration Verification:**

- IV1: Imported questions appear in question manager
- IV2: Validation errors prevent import
- IV3: Large files handled without browser freeze

---

### Epic 10 Story Dependencies

```
10.1 (Middleware) ──┬──→ 10.4, 10.5, 10.6, 10.7, 10.8, 10.9, 10.10, 10.11
                    │
10.2 (Audit Log) ───┤
                    │
10.3 (Status) ──────┘

10.12 (UI Layout) ──→ 10.13, 10.14, 10.15, 10.16

Backend (10.1-10.11) can proceed in parallel with Frontend (10.12-10.16)
```

---

## 7. Epic 11: Content Moderation & Quality

### Epic Goal

Enable proactive content quality management through user feedback collection, SME review workflows, automated anomaly detection, and content health monitoring.

### Integration Requirements

- Depends on Epic 10 admin infrastructure
- Adds learner-facing report functionality
- Uses Epic 10's question status lifecycle for resolution actions

---

### Story 11.1: Question Report Database Schema

As a **backend developer**,
I want to create the question reports table,
so that user feedback can be stored and tracked.

**Acceptance Criteria:**

1. Create `question_reports` table via Alembic migration
2. Create indexes on `(question_id)`, `(status, created_at)`, `(user_id)`
3. Create `QuestionReport` SQLAlchemy model
4. Create `QuestionReportRepository` with CRUD methods
5. Add unique constraint: one pending report per user per question
6. Unit tests: create report, query by status, unique constraint

**Integration Verification:**

- IV1: Migration runs without affecting existing tables
- IV2: Foreign keys properly cascade on user/question deletion
- IV3: Rollback migration successfully removes table

---

### Story 11.2: Question Report Submission API

As a **backend developer**,
I want a learner-facing endpoint to report questions,
so that users can flag problematic content.

**Acceptance Criteria:**

1. Create `POST /api/v1/questions/{id}/report` endpoint (learner-facing)
2. Accept body: `{ "issue_type": string, "description": string? }`
3. Validate issue_type is one of allowed values
4. Prevent duplicate pending reports (return 409 if exists)
5. Create report with status='pending'
6. Unit tests: create report, duplicate prevention, validation

**Integration Verification:**

- IV1: Endpoint accessible to non-admin authenticated users
- IV2: Report creation does not affect question visibility
- IV3: Rate limiting prevents spam (max 10 reports/hour per user)

---

### Story 11.3: Report Triage API

As a **backend developer**,
I want admin endpoints for report triage,
so that admins can review and resolve user reports.

**Acceptance Criteria:**

1. Create admin router at `/api/v1/admin/reports`
2. Implement endpoints:
   - `GET /` - List reports with filters
   - `GET /{id}` - Get report details
   - `GET /summary` - Get report counts by status
   - `PUT /{id}/review` - Set status to 'under_review'
   - `PUT /{id}/resolve` - Resolve report with action
   - `PUT /{id}/dismiss` - Dismiss report with reason
3. Log resolution actions to audit log
4. Unit tests: CRUD, status transitions, audit logging

**Integration Verification:**

- IV1: Reports visible in admin UI after creation
- IV2: Resolved reports excluded from pending queue
- IV3: Audit log captures resolution details

---

### Story 11.4: Auto-Flagging Rules Engine

As a **backend developer**,
I want automated flagging rules,
so that problematic questions are surfaced without manual monitoring.

**Acceptance Criteria:**

1. Create `ContentHealthService` with rule evaluation methods
2. Implement rules:
   - **Emergency flag**: 5+ reports in 24 hours → auto-set question to 'pending_review'
   - **Escalation flag**: 2+ reports in 7 days → add to SME review queue
   - **Too easy flag**: >90% correct rate → flag for difficulty review
   - **Too hard flag**: <30% correct rate → flag for content review
3. Create `content_flags` table to track active flags
4. Create background task to evaluate rules daily
5. Unit tests: each rule, flag creation, threshold calculations

**Integration Verification:**

- IV1: Emergency flag immediately affects question visibility
- IV2: Flags appear in admin dashboard
- IV3: Rules only evaluate published questions

---

### Story 11.5: Content Health Metrics API

As a **backend developer**,
I want content health metrics endpoints,
so that the admin dashboard can display quality KPIs.

**Acceptance Criteria:**

1. Create `GET /api/v1/admin/content-health` endpoint
2. Return metrics per course:
   - Pending reports count and age distribution
   - Active flags by type
   - Questions with anomalous performance
   - Concepts with insufficient questions
   - Average resolution time
   - Report volume trend
3. Cache response for 15 minutes
4. Performance: <1s response time
5. Unit tests: metrics calculation, edge cases

**Integration Verification:**

- IV1: Metrics consistent with report list data
- IV2: Flag counts match active flags in database
- IV3: Performance trend accurate against historical data

---

### Story 11.6: Question Performance Tracking

As a **backend developer**,
I want to track question performance metrics,
so that anomaly detection has accurate data.

**Acceptance Criteria:**

1. Create `question_performance` table or add columns to questions
2. Create background task to calculate metrics daily
3. Calculate metrics from `quiz_responses` table
4. Store 7-day and 30-day rolling metrics
5. Unit tests: metric calculation, rolling window accuracy

**Integration Verification:**

- IV1: Metrics update after quiz responses
- IV2: Anomaly detection uses fresh metrics
- IV3: Calculation does not impact quiz performance

---

### Story 11.7: Report Resolution Workflows

As a **backend developer**,
I want resolution actions to update question status,
so that report resolution has immediate effect.

**Acceptance Criteria:**

1. When resolving with action='edited': clear all pending reports, log to audit
2. When resolving with action='retired': set question status to 'retired', clear reports
3. When resolving with action='no_action': mark only this report resolved
4. When resolving with action='duplicate': link to original report
5. Unit tests: each resolution path, cascading effects

**Integration Verification:**

- IV1: Retired question removed from learner quiz pool
- IV2: Edited question remains available (if published)
- IV3: Bulk resolution clears report backlog

---

### Story 11.8: Report Notification System

As a **backend developer**,
I want notifications for urgent reports,
so that admins are alerted to critical issues.

**Acceptance Criteria:**

1. Create notification when emergency flag triggered
2. Create daily digest of new reports
3. Store notifications in `admin_notifications` table
4. Create `GET /api/v1/admin/notifications` endpoint
5. Create `PUT /api/v1/admin/notifications/{id}/read` endpoint
6. Unit tests: notification creation, read marking, queries

**Integration Verification:**

- IV1: Emergency notifications created within 1 minute of trigger
- IV2: Daily digest sent at configured time
- IV3: Notifications visible in admin UI

---

### Story 11.9: Content Health Dashboard UI

As a **frontend developer**,
I want a content health dashboard,
so that admins can monitor quality metrics visually.

**Acceptance Criteria:**

1. Create `/admin/content-health` page or extend dashboard
2. Display KPI cards: pending reports, active flags, questions needing review
3. Display charts: report volume trend, resolution time trend
4. Display alert list with action buttons
5. Click-through to filtered report/question lists
6. Auto-refresh every 5 minutes
7. Unit tests: chart rendering, data display, navigation

**Integration Verification:**

- IV1: Metrics match API response data
- IV2: Click-through navigates to correct filtered view
- IV3: Real-time feel with auto-refresh

---

### Story 11.10: Report Triage UI

As a **frontend developer**,
I want a report triage interface,
so that admins can efficiently review and resolve reports.

**Acceptance Criteria:**

1. Create `/admin/reports` page with queue view
2. Report card showing: question preview, issue type, reporter count
3. Resolution form: action select, notes field
4. Bulk actions: dismiss multiple, assign to self
5. Keyboard shortcuts for power users
6. Unit tests: queue display, resolution flow, bulk actions

**Integration Verification:**

- IV1: Resolved reports disappear from queue
- IV2: Resolution updates question status where applicable
- IV3: Bulk dismiss works for 50+ reports

---

### Story 11.11: Question Report UI (Learner-Facing)

As a **frontend developer**,
I want a report button in the quiz interface,
so that learners can easily flag problematic questions.

**Acceptance Criteria:**

1. Add "Report Question" button to quiz answer/explanation view
2. Open report modal with issue type selector and description
3. Show success confirmation after submission
4. Disable report button if user already has pending report
5. Minimal disruption to quiz flow
6. Unit tests: modal interactions, submission, duplicate prevention

**Integration Verification:**

- IV1: Report appears in admin triage queue
- IV2: Quiz flow continues normally after report
- IV3: Button disabled after successful report

---

### Story 11.12: Notification Center UI

As a **frontend developer**,
I want a notification center in the admin UI,
so that admins see alerts without leaving their workflow.

**Acceptance Criteria:**

1. Add notification bell icon to admin header
2. Show unread count badge
3. Dropdown panel with recent notifications
4. Click to navigate to relevant page
5. "Mark all read" action
6. Unit tests: badge count, dropdown interactions, mark read

**Integration Verification:**

- IV1: Emergency notifications prominently displayed
- IV2: Read state persists across page navigation
- IV3: Notification links navigate to correct context

---

### Epic 11 Story Dependencies

```
11.1 (Schema) ──┬──→ 11.2 (Submit API)
                │
                ├──→ 11.3 (Triage API) ──→ 11.7 (Resolution)
                │
                └──→ 11.4 (Auto-Flag) ──→ 11.5 (Health API)
                                              │
11.6 (Performance) ──────────────────────────┘

11.8 (Notifications) independent after 11.1

Frontend:
Epic 10 UI ─→ 11.9 (Health Dashboard)
           ─→ 11.10 (Triage UI)
           ─→ 11.12 (Notifications)

Existing Quiz UI ──→ 11.11 (Report Button)
```

### Epic 11 Success Metrics

| Metric | Target |
|--------|--------|
| Report submission to resolution | <72 hours average |
| Emergency flag response time | <4 hours |
| Auto-flag accuracy | >80% (flags lead to action) |
| Report backlog | <50 pending at any time |
| User report adoption | >1% of active users report at least once |

---

## 8. Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-12-17 | 1.0 | Initial brownfield PRD for Admin Content Management | John (PM Agent) |
| 2025-12-24 | 1.1 | Added Quiz Session Analytics to Story 10.8 (AC 3) - migrated from Story 4.7 AC 9 | Sarah (Product Owner) |
| 2025-12-24 | 1.2 | Updated expected session length from 10-15 to 10 questions (habit-forming change) | Bob (Scrum Master) |
