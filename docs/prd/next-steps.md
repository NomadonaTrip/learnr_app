# Next Steps

This PRD is now complete and ready for the next phases. The recommended sequence is **UX Design** (parallel track) and **Architecture** (parallel track), followed by **Development**.

---

### Prompt for UX Expert

**Context:** You are the UX Expert agent responsible for designing the user experience and visual design for LearnR, an adaptive learning platform for CBAP exam preparation.

**Your Task:**
Create a comprehensive UX Design Document based on the LearnR PRD (docs/prd.md). Your design should bring the requirements to life with user flows, wireframes, high-fidelity mockups, and a complete design system.

**IMPORTANT - Existing Documentation:**
A detailed Frontend Specification already exists at **`docs/front-end-spec.md`** (1,801 lines). Additionally, comprehensive user flows are documented in **`docs/user-flows.md`** (747 lines). Your task is to:
1. Review these existing specifications for completeness and quality
2. Validate alignment with PRD requirements (especially v2.1 features: Post-Session Review, Async Reading Library)
3. Enhance and refine where needed
4. Create visual mockups and design system assets (Figma files)
5. **DO NOT recreate specifications from scratch** - build upon the extensive work already documented

**Key Inputs from PRD:**
1. **UI Design Goals** (Section: User Interface Design Goals)
   - Overall UX Vision: "Personal learning coach" feel
   - Key Interaction Paradigms: Progressive disclosure (onboarding), focused assessment mode (quiz), data dashboard (progress), contextual content (reading)
   - Core Screens: 9 critical screens identified
   - Design Specs:
     - Font: Inter (primary typeface, weights 400/500/600/700)
     - Icons: Vector icons ONLY (no emojis anywhere)
     - Design Inspiration: Framer website templates
     - Border Radius Hierarchy: Main containers (35px), primary cards (22px), secondary cards (14px), icons (8-12px)
     - Buttons: Pill-rounded (border-radius: 9999px or 50%)
     - Layout: 8px grid system for consistent spacing
   - Color Psychology: Professional blue (primary), green (success), warm orange (attention), clean grays/whites
   - Accessibility: WCAG 2.1 Level AA compliance (keyboard nav, screen reader, 4.5:1 contrast, text resizing 200%)
   - Platforms: Web responsive (desktop 1280x720+, tablet 768x1024, mobile 375x667+)

2. **User Journeys** (Section: User Experience Principles → Critical User Flows)
   - First-Time User Journey: Landing + inline Q1 → Q2-7 → Account creation → Diagnostic (12 questions) → Results + dashboard → First quiz + reading → Return to dashboard
   - Daily Active User Journey: Login → Dashboard (reviews due?) → Start reviews OR new quiz → Quiz loop (question → answer → explanation → reading → next) → Return to dashboard

3. **Core Screens to Design** (from UI Design Goals):
   - Landing Screen with Inline First Question
   - Onboarding Flow (Questions 2-7)
   - Account Creation Screen
   - Diagnostic Assessment Screen (12 questions, focused mode)
   - Diagnostic Results Screen (6 KA bars, gap analysis, exam readiness)
   - Progress Dashboard (home screen with 6 KA bars, exam readiness, reviews due, trends)
   - Knowledge Area Detail View (drill-down for specific KA)
   - Quiz Session Screen (question display, answer selection)
   - Explanation & Reading Screen (feedback, detailed explanation, BABOK chunks)
   - Settings/Profile Screen (account, preferences, privacy)

**Your Deliverables:**
1. **User Flow Diagrams** (visual flowcharts for key journeys using tools like Figma, Miro, or Whimsical)
2. **Wireframes** (low-fidelity layouts for all 9 core screens)
3. **High-Fidelity Mockups** (polished designs for key screens: Landing, Dashboard, Quiz, Results) following Framer-inspired aesthetic
4. **Design System / Style Guide**:
   - Color palette (hex codes for primary blue, success green, attention orange, neutrals)
   - Typography scale (Inter font sizes, weights, line heights)
   - Component library (buttons, cards, form inputs, progress bars, charts, icons)
   - Spacing system (8px grid multiples)
   - Accessibility guidelines (contrast ratios, focus states, aria-labels)
5. **Interaction Patterns Document** (animations, transitions, hover states, loading states, error states)

**Design Constraints:**
- NO emojis - use vector icons instead (recommend library: Heroicons, Feather Icons, or Lucide)
- Pill-rounded buttons (border-radius: 9999px)
- Hierarchical border radius for cards (35px/22px/14px/8-12px)
- WCAG 2.1 AA compliance (test with axe DevTools or similar)
- Mobile-first responsive design (works from 375px width up)

**Output:**
Create a UX Design Document (docs/ux-design.md or Figma file) that developers can reference during implementation. Include links to Figma prototypes or image exports of mockups.

---

### Prompt for Architect

**Context:** You are the Architect agent responsible for creating the technical specification for LearnR, an adaptive learning platform for CBAP exam preparation.

**Your Task:**
Create a comprehensive Technical Specification Document based on the LearnR PRD (docs/prd.md). Your specification should define the system architecture, data models, API contracts, deployment strategy, and provide implementation guidance for the development team.

**IMPORTANT - Existing Technical Specifications:**
Detailed technical specifications for v2.1 features already exist. You MUST review these documents as foundational inputs:
- **`docs/Implementation_Summary.md`** (964 lines) - Master implementation guide covering database schemas, API contracts, and feature specifications for Post-Session Review and Asynchronous Reading Library
- **`docs/Asynchronous_Reading_Model.md`** (1,050 lines) - Complete technical architecture for the reading queue system
- **`docs/Learning_Loop_Refinement.md`** (1,488 lines) - Phase-by-phase specification of the post-session review feature with detailed flowcharts

Your task is to consolidate these specifications into a unified Technical Specification Document and add missing architectural elements (system diagrams, deployment architecture, algorithm specifications).

**Key Inputs from PRD:**
1. **Technical Assumptions** (Section: Technical Assumptions)
   - Repository Structure: Monorepo (`/frontend`, `/backend`, `/shared`, `/scripts`, `/docs`)
   - Service Architecture: Monolithic FastAPI backend (defer microservices until >1,000 concurrent users)
   - Technology Stack:
     - **Frontend:** React 18+, TypeScript, Vite, Context API (or Redux if needed)
     - **Backend:** Python 3.11+, FastAPI, SQLAlchemy 2.0+, Pydantic
     - **Databases:** PostgreSQL 15+ (relational), Qdrant (vector embeddings)
     - **External APIs:** OpenAI (GPT-4, text-embedding-3-large)
   - Testing Requirements: Unit + Integration testing (70%+ coverage for business-critical), manual E2E for MVP
   - Deployment: Frontend (Vercel/Netlify), Backend (Railway/Render), PostgreSQL (managed service), Qdrant (self-hosted Docker)
   - CI/CD: GitHub Actions (test → deploy on push to `main`)

2. **Data Model Requirements** (from Epic Stories):
   - **Users:** id, email, hashed_password, created_at, updated_at
   - **Onboarding Data:** user_id FK, referral_source, certification, motivation, exam_date, knowledge_level, target_score, daily_study_time
   - **Questions:** id, question_text, option_a/b/c/d, correct_answer, explanation, ka, difficulty, concept_tags JSONB, source, created_at
   - **BABOK Chunks:** chunk_id, ka, section_ref, difficulty, concept_tags JSONB, text_content TEXT
   - **Diagnostic Responses:** user_id FK, question_id FK, selected_answer, timestamp
   - **Quiz Responses:** user_id FK, session_id FK, question_id FK, selected_answer, is_correct, is_review BOOL, time_taken, timestamp
   - **Competency Tracking:** user_id FK, ka, competency_score FLOAT, last_updated
   - **Concept Mastery:** user_id FK, concept_tag, ka, ease_factor FLOAT, interval_days INT, repetition_count INT, last_reviewed, next_review_due
   - **Reading History:** user_id FK, chunk_id FK, marked_read BOOL, timestamp
   - **Reading Engagement:** user_id FK, chunk_id FK, session_id FK, displayed_at, expanded_at, time_spent_seconds, marked_read
   - **Quiz Sessions:** session_id, user_id FK, start_time, end_time, session_type (new_content | mixed), questions_answered_count, is_paused, is_completed

3. **API Endpoints to Define** (from Epic Stories):
   - **Authentication:** POST /api/auth/register, POST /api/auth/login, POST /api/auth/forgot-password, POST /api/auth/reset-password
   - **User Profile:** GET /api/user/profile, PUT /api/user/profile, POST /api/user/change-password, POST /api/user/onboarding, GET /api/user/export, DELETE /api/user/account
   - **Diagnostic:** GET /api/diagnostic/questions, POST /api/diagnostic/answer, GET /api/diagnostic/results
   - **Quiz:** POST /api/quiz/session/start, GET /api/quiz/session/{id}, POST /api/quiz/session/{id}/pause, POST /api/quiz/session/{id}/end, POST /api/quiz/answer
   - **Content:** GET /api/content/questions, POST /api/content/reading
   - **Dashboard:** GET /api/dashboard, GET /api/dashboard/trends, GET /api/dashboard/ka/{ka_name}
   - **Progress:** GET /api/progress/reviews
   - **Reading:** POST /api/reading/track, POST /api/reading/engagement
   - **Feedback:** POST /api/feedback/explanation, POST /api/feedback/reading, POST /api/feedback/report
   - **Health:** GET /health
   - **Admin (Support Tools):** GET /api/admin/users/search, POST /api/admin/impersonate/{user_id}, POST /api/admin/impersonate/exit, GET /api/admin/audit-log, GET /api/admin/alpha-metrics

4. **Performance Requirements** (from Technical Assumptions):
   - Question display: <500ms after answer submission
   - Reading content retrieval: <1 second (vector search + PostgreSQL join)
   - Dashboard rendering: <2 seconds (aggregate all 6 KA scores + trends)
   - Database queries: Indexed on user_id, question_id, session_id for fast lookups

5. **Security Requirements**:
   - Password hashing: bcrypt or Argon2
   - JWT expiration: 7-day token expiration
   - HTTPS only (all production traffic over TLS)
   - Input validation: Pydantic models validate all API inputs
   - Rate limiting: Implement on auth endpoints (prevent brute force)

**Your Deliverables:**
1. **System Architecture Diagram** (components: Frontend → Backend API → PostgreSQL, Qdrant → External APIs: OpenAI)
2. **Data Model ERD** (Entity-Relationship Diagram showing all tables, relationships, foreign keys, indexes)
3. **API Contract Specification** (OpenAPI 3.0 spec or detailed endpoint documentation):
   - For each endpoint: Method, Path, Request Body Schema, Response Schema, Status Codes, Error Responses
4. **Deployment Architecture Diagram** (Frontend hosting, Backend hosting, Database services, CI/CD pipeline)
5. **Algorithm Specifications** (docs/TDDoc_Algorithms.md):
   - Simplified IRT competency calculation formula
   - Adaptive question selection algorithm (pseudocode)
   - SM-2 spaced repetition scheduling logic
6. **Testing Strategy Document**:
   - Unit test structure (what to test, coverage targets)
   - Integration test approach (API endpoint testing, database integration)
   - E2E test scenarios (manual for MVP)
7. **Technical Debt Register**:
   - Simplified IRT (full 3-parameter IRT deferred to Phase 2)
   - Manual E2E testing (automation deferred)
   - When to extract microservices (threshold: >1,000 concurrent users)

**Technical Decisions Deferred to You:**
1. **Frontend State Management:** Context API (recommended for simplicity) vs. Redux Toolkit (if complex state)
2. **UI Component Library:** Material-UI, Chakra UI, or custom components (recommend MUI or Chakra for speed)
3. **Chart Library:** Recharts or Chart.js (for progress dashboard visualization)
4. **Email Service:** SendGrid, AWS SES, or similar (for password reset, future notifications)

**Output:**
Create a Technical Specification Document (docs/tech-spec.md) that developers can reference during implementation. Include diagrams (export from Lucidchart, draw.io, or Mermaid markdown), data models, and API contracts.

---

**Recommended Next Workflow:**
Run both UX Design and Architecture phases in **parallel** (they have minimal dependencies), then proceed to Development Sprint Planning with outputs from both
- Purpose: Define technical architecture, system design, technology choices
- Note: Epic breakdown created after will have full technical context

### Recommended Path

**For LearnR:**
1. **UX Design** (critical for learning app experience)
2. **Architecture** (technical design for adaptive engine + AI integration)
3. **Epic Breakdown** (with full UX + Architecture context)
4. **Solutioning Gate Check** (validate cohesion before implementation)
5. **Sprint Planning** (begin implementation)

---
