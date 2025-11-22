# Epic Details

This section provides detailed user stories and acceptance criteria for each epic, following the sequence established in the Epic List. Each story is designed to deliver complete, testable functionality that can be implemented by a single developer in a focused 2-4 hour session.

---

### Epic 1: Foundation & User Authentication

**Epic Goal:** Establish the technical foundation for LearnR by setting up the monorepo structure, development environment, databases (PostgreSQL and Qdrant), and implementing secure user authentication. This epic delivers a working full-stack application with user registration, login, password management, and a health-check endpoint demonstrating end-to-end integration.

#### Story 1.1: Monorepo Setup and Project Scaffolding

As a **developer**,
I want to set up a monorepo with frontend and backend scaffolding,
so that the team has a consistent development environment and can begin building features immediately.

**Acceptance Criteria:**
1. Monorepo structure created with `/frontend`, `/backend`, `/shared`, `/scripts`, `/docs` directories
2. Frontend: React 18+ with TypeScript, Vite build tool, basic folder structure (`/src/components`, `/src/pages`, `/src/hooks`, `/src/utils`)
3. Backend: Python 3.11+ with FastAPI, basic folder structure (`/app/api`, `/app/models`, `/app/services`, `/app/utils`)
4. Package managers configured: npm/yarn for frontend, poetry/pip for backend
5. Environment variable management: `.env.example` files in both frontend and backend with required variables documented
6. README.md files in root and each directory explaining setup and development commands
7. Git repository initialized with `.gitignore` for Node, Python, environment files
8. Both frontend and backend can start locally (frontend on localhost:3000, backend on localhost:8000)

#### Story 1.2: PostgreSQL Database Setup and Schema Initialization

As a **backend developer**,
I want to set up PostgreSQL with initial schema and migrations,
so that user data and application state can be persisted reliably.

**Acceptance Criteria:**
1. PostgreSQL database created locally (development) with connection configuration
2. Alembic migrations configured for schema version control
3. Initial schema migration created with core tables:
   - `users` table (id, email, hashed_password, created_at, updated_at)
   - `onboarding_data` table (user_id FK, referral_source, certification, motivation, exam_date, knowledge_level, target_score, daily_study_time)
4. SQLAlchemy models created for `User` and `OnboardingData` with Pydantic schemas
5. Database connection pooling configured in FastAPI
6. Migration commands documented in README (`alembic upgrade head`, `alembic downgrade`, etc.)
7. Test database setup for running tests in isolation
8. All tables have appropriate indexes on foreign keys and frequently queried columns

#### Story 1.3: User Registration API

As a **user**,
I want to create an account with my email and password,
so that I can save my progress and access personalized learning features.

**Acceptance Criteria:**
1. POST `/api/auth/register` endpoint accepts `email` and `password` in request body
2. Email validation: Must be valid email format, unique in database (return 409 Conflict if duplicate)
3. Password validation: Minimum 8 characters, must contain at least one letter and one number
4. Password hashed using bcrypt or Argon2 before storage (never store plaintext)
5. User record created in `users` table with hashed password
6. Response returns user object (id, email, created_at) and JWT token with 7-day expiration
7. JWT token includes user_id in payload for authentication
8. Error responses: 400 Bad Request for validation errors, 409 Conflict for duplicate email, 500 Internal Server Error for database issues
9. Unit tests: Valid registration, duplicate email, weak password, invalid email format
10. Integration test: Full registration flow creates user in database and returns valid JWT

#### Story 1.4: User Login API

As a **registered user**,
I want to log in with my email and password,
so that I can access my personalized learning dashboard and progress.

**Acceptance Criteria:**
1. POST `/api/auth/login` endpoint accepts `email` and `password` in request body
2. User lookup by email (case-insensitive)
3. Password verification using bcrypt/Argon2 compare function
4. On successful authentication: Return JWT token (7-day expiration) and user object
5. On failed authentication: Return 401 Unauthorized with generic message "Invalid email or password" (no distinction to prevent enumeration)
6. JWT token structure same as registration (user_id in payload)
7. Rate limiting: Maximum 5 login attempts per email per 15 minutes (prevent brute force)
8. Unit tests: Valid login, invalid password, non-existent email, rate limiting
9. Integration test: Login returns valid JWT that can be used for authenticated endpoints
10. Security: No sensitive information in error messages, timing-safe password comparison

#### Story 1.5: Password Reset Flow

As a **user who forgot my password**,
I want to reset my password via email verification,
so that I can regain access to my account securely.

**Acceptance Criteria:**
1. POST `/api/auth/forgot-password` endpoint accepts `email`
2. Generate secure password reset token (UUID or similar, 1-hour expiration)
3. Store reset token in database with expiration timestamp (new `password_reset_tokens` table or add to `users`)
4. Send password reset email with reset link: `https://app.learnr.com/reset-password?token={token}`
5. Email sent even if email not found (prevent email enumeration, but no token created)
6. POST `/api/auth/reset-password` endpoint accepts `token` and `new_password`
7. Token validation: Exists, not expired, not already used
8. Password validation: Same rules as registration (8+ chars, letter + number)
9. Update user password (hash new password), invalidate reset token
10. Return success message (no JWT - user must log in with new password)
11. Unit tests: Valid reset, expired token, invalid token, weak new password
12. Integration test: Full password reset flow from forgot to login with new password

#### Story 1.6: JWT Authentication Middleware

As a **backend developer**,
I want JWT authentication middleware protecting authenticated endpoints,
so that only logged-in users can access protected resources.

**Acceptance Criteria:**
1. Middleware function `verify_jwt_token` that extracts JWT from `Authorization: Bearer {token}` header
2. Token validation: Signature valid, not expired, contains required `user_id` claim
3. On valid token: Attach `current_user` to request context (user_id, email)
4. On invalid/missing token: Return 401 Unauthorized with message "Authentication required"
5. Decorator `@require_auth` to protect routes (e.g., `@require_auth` above route handler)
6. Protected route example: GET `/api/user/profile` returns current user's profile
7. Unit tests: Valid token grants access, expired token denied, missing token denied, invalid signature denied
8. Integration test: Protected endpoint accessible with valid JWT, denied without JWT
9. Token refresh not implemented in MVP (7-day expiration sufficient)
10. Security: Token stored securely in frontend (HttpOnly cookie or secure localStorage, TBD by frontend)

#### Story 1.7: Health Check and API Documentation

As a **developer or DevOps engineer**,
I want a health check endpoint and auto-generated API documentation,
so that I can verify the backend is running and understand available endpoints.

**Acceptance Criteria:**
1. GET `/health` endpoint returns `200 OK` with JSON `{"status": "healthy", "timestamp": "ISO8601"}`
2. Health check verifies database connectivity (PostgreSQL ping)
3. FastAPI auto-generated OpenAPI documentation available at `/docs` (Swagger UI)
4. `/docs` shows all implemented endpoints with request/response schemas
5. `/redoc` alternative documentation format available
6. Health check does not require authentication (publicly accessible for monitoring)
7. API documentation shows authentication requirements (lock icon) for protected endpoints
8. Response examples included in API docs for each endpoint
9. Health check returns 503 Service Unavailable if database connection fails
10. README documents how to access API docs and health check endpoint

---

### Epic 2: Content Foundation & Question Bank

**Epic Goal:** Build the content processing pipeline to load, parse, embed, and serve all CBAP questions and BABOK v3 reading content. This epic delivers 600-1,000 questions with metadata, BABOK chunks with embeddings, Qdrant vector database setup, and functional content retrieval APIs that can be tested independently before integrating with user-facing features.

#### Story 2.1: Qdrant Vector Database Setup

As a **backend developer**,
I want to set up Qdrant locally via Docker and create collections for questions and reading content,
so that semantic search and content retrieval can function.

**Acceptance Criteria:**
1. Qdrant Docker container running locally (docker-compose.yml or standalone docker run command)
2. Qdrant accessible at `localhost:6333` with REST API and gRPC
3. Two collections created:
   - `cbap_questions`: Vector size 1536 (text-embedding-3-large), distance metric: Cosine
   - `babok_chunks`: Vector size 1536, distance metric: Cosine
4. Collection schemas include metadata fields (payload):
   - Questions: `question_id`, `ka`, `difficulty`, `concept_tags`, `question_text`, `options`, `correct_answer`
   - BABOK chunks: `chunk_id`, `ka`, `section_ref`, `difficulty`, `concept_tags`, `text_content`
5. Qdrant Python client installed and configured in backend
6. Connection test: Backend can create, read, update, delete (CRUD) vectors in both collections
7. Environment variable `QDRANT_URL` configurable (default: `http://localhost:6333`)
8. README documents Qdrant setup commands and how to verify collections exist
9. Qdrant data persisted to local volume (survives container restart)
10. Health check extended to verify Qdrant connectivity

#### Story 2.2: Vendor Question Import and Metadata Enrichment

As a **content manager**,
I want to import 500 vendor CBAP questions with metadata into PostgreSQL and Qdrant,
so that the platform has a high-quality question foundation.

**Acceptance Criteria:**
1. Questions table schema in PostgreSQL:
   - `questions` (id, question_text, option_a, option_b, option_c, option_d, correct_answer, explanation, ka, difficulty, concept_tags JSONB, source VARCHAR, created_at)
2. Python script `/scripts/import_vendor_questions.py` reads vendor questions from CSV/JSON
3. Script validates each question: Required fields present, exactly 4 options, correct_answer is A/B/C/D, KA is one of 6 valid KAs
4. Difficulty labels assigned by expert or default to "Medium" if not provided
5. Concept tags extracted or manually assigned (JSONB array in PostgreSQL)
6. Questions inserted into PostgreSQL `questions` table (500 total)
7. Distribution validation: Each KA has at least 50 questions, balanced across difficulty levels
8. Script logs summary: Total questions imported, breakdown by KA and difficulty
9. Rollback mechanism if import fails mid-process (transaction-based insert or idempotent script)
10. README documents how to run import script and expected CSV/JSON format

#### Story 2.3: Question Embedding Generation and Qdrant Upload

As a **backend developer**,
I want to generate embeddings for all questions and upload to Qdrant,
so that semantic search can retrieve relevant questions.

**Acceptance Criteria:**
1. Python script `/scripts/generate_question_embeddings.py` reads all questions from PostgreSQL
2. For each question, create embedding text: `"{question_text} {option_a} {option_b} {option_c} {option_d}"`
3. Call OpenAI API `text-embedding-3-large` to generate 1536-dimension embedding vector
4. Batch API calls (up to 100 questions per request for efficiency)
5. Upload each question embedding to Qdrant `cbap_questions` collection with payload (question_id, ka, difficulty, concept_tags, question_text, options, correct_answer)
6. Script tracks progress (log every 50 questions embedded and uploaded)
7. Handle API rate limits: Retry with exponential backoff on 429 errors
8. Total embeddings: 500 vendor questions embedded
9. Verification: Query Qdrant collection, confirm 500 vectors exist
10. Script is idempotent (can re-run without duplicating embeddings, check if question_id already exists)

#### Story 2.4: BABOK v3 Parsing and Chunking

As a **content processor**,
I want to parse BABOK v3 PDF and chunk it into semantic segments,
so that targeted reading content can be retrieved for user gaps.

**Acceptance Criteria:**
1. Python script `/scripts/parse_babok.py` reads BABOK v3 PDF (path from environment variable or argument)
2. Extract text using PyMuPDF or pdfplumber (preserve structure: headings, paragraphs)
3. Identify 6 KA sections in BABOK (Business Analysis Planning, Elicitation, Requirements, Solution Evaluation, etc.)
4. Chunk text using hybrid strategy:
   - Structural chunking: Respect section/subsection boundaries (don't break mid-concept)
   - Semantic chunking: Target 200-500 tokens per chunk using LangChain RecursiveCharacterTextSplitter
5. Each chunk assigned metadata: KA, section_ref (e.g., "3.2.1 Stakeholder Analysis"), difficulty (Easy/Medium/Hard based on section complexity or default Medium), concept_tags (extracted keywords or manually assigned)
6. Chunks saved to PostgreSQL `babok_chunks` table (chunk_id, ka, section_ref, difficulty, concept_tags JSONB, text_content TEXT)
7. Validation: Total chunks approximately 200-500 (depends on BABOK length, aim for comprehensive coverage)
8. Distribution: Each KA has at least 20 chunks
9. Script logs summary: Total chunks created, breakdown by KA
10. README documents BABOK parsing script usage and expected output

#### Story 2.5: BABOK Chunk Embedding Generation and Qdrant Upload

As a **backend developer**,
I want to generate embeddings for all BABOK chunks and upload to Qdrant,
so that semantic retrieval can find relevant reading content for user gaps.

**Acceptance Criteria:**
1. Python script `/scripts/generate_babok_embeddings.py` reads all chunks from PostgreSQL `babok_chunks` table
2. For each chunk, use `text_content` as embedding input
3. Call OpenAI API `text-embedding-3-large` to generate 1536-dimension embedding
4. Batch API calls (up to 100 chunks per request)
5. Upload each chunk embedding to Qdrant `babok_chunks` collection with payload (chunk_id, ka, section_ref, difficulty, concept_tags, text_content)
6. Script tracks progress (log every 50 chunks embedded and uploaded)
7. Handle API rate limits: Retry with exponential backoff on 429 errors
8. Total embeddings: All BABOK chunks embedded (200-500 vectors)
9. Verification: Query Qdrant collection, confirm all chunks exist
10. Script is idempotent (check if chunk_id already exists before uploading)

#### Story 2.6: Content Retrieval API - Questions

As a **backend developer**,
I want an API endpoint to retrieve questions by filters (KA, difficulty, concept),
so that the quiz engine can select appropriate questions.

**Acceptance Criteria:**
1. GET `/api/content/questions` endpoint accepts query parameters: `ka`, `difficulty`, `concept_tags`, `limit` (default 10)
2. Query PostgreSQL `questions` table filtered by provided parameters
3. If `concept_tags` provided: Filter using JSONB containment (`concept_tags @> '{tag}'`)
4. Return JSON array of question objects (id, question_text, options, ka, difficulty, concept_tags, but NOT correct_answer or explanation - those come after answer submission)
5. Response includes pagination metadata: `total_count`, `page`, `limit`
6. Endpoint requires authentication (`@require_auth` middleware)
7. Unit tests: Filter by KA, filter by difficulty, filter by concept_tags, no filters (returns all up to limit)
8. Integration test: API returns questions matching filters
9. Performance: Query executes in <100ms for up to 1000 questions
10. API documentation updated in `/docs` with parameter descriptions and example responses

#### Story 2.7: Content Retrieval API - BABOK Chunks

As a **backend developer**,
I want an API endpoint to retrieve BABOK chunks via semantic search,
so that targeted reading content can be presented to users.

**Acceptance Criteria:**
1. POST `/api/content/reading` endpoint accepts JSON body: `query_text` (user's knowledge gap description), `ka` (optional filter), `limit` (default 3)
2. Generate embedding for `query_text` using OpenAI `text-embedding-3-large`
3. Query Qdrant `babok_chunks` collection with vector search (cosine similarity)
4. Apply filters: If `ka` provided, filter results to that KA only
5. Return top `limit` chunks ranked by similarity score
6. Response: JSON array of chunk objects (chunk_id, ka, section_ref, text_content, similarity_score)
7. Endpoint requires authentication
8. Unit tests: Search returns relevant chunks, KA filter works, limit parameter works
9. Integration test: Semantic search finds BABOK content related to query (e.g., "stakeholder analysis" retrieves relevant section)
10. Performance: Vector search executes in <500ms including embedding generation

---

### Epic 3: Diagnostic Assessment & Competency Baseline

**Epic Goal:** Enable first-time users to complete the anonymous 7-question onboarding flow (starting with first question inline on landing page), create an account, take the 12-question diagnostic assessment, and receive accurate baseline competency scores across all 6 CBAP knowledge areas with gap analysis and recommendations.

#### Story 3.1: Landing Page with Inline First Onboarding Question

As a **first-time visitor**,
I want to see the value proposition and immediately engage with the first onboarding question on the landing page,
so that I can start my learning journey with minimal friction.

**Acceptance Criteria:**
1. Landing page displays LearnR value proposition (headline, subheadline, key benefits - trust, adaptive learning, reading content, spaced repetition)
2. First onboarding question displayed **inline immediately below value prop** (no "Sign Up" button friction): "How did you hear about LearnR?" with options (Search, Referral, Social Media, Other)
3. User selects answer → automatically progresses to Question 2 in same container (no separate "Submit" button, no page reload - smooth fade-in/slide transition 300ms)
4. Question 1 answer stored in browser sessionStorage (no server call yet, user not authenticated)
5. Visual design: Framer-inspired aesthetic, Inter font, pill-rounded answer buttons (border-radius: 9999px), primary information card styling (22px border radius)
6. Progress indicator: "Question 1 of 7" displayed
7. Page is mobile-responsive (works on 375px width minimum)
8. Loading state: Page renders in <3 seconds on 3G connection
9. Accessibility: Keyboard navigation works (tab to options, enter to select), screen reader announces question and options
10. Unit tests: Question renders, selection progresses to next question, sessionStorage updated

#### Story 3.2: Onboarding Questions 2-7 (Progressive Disclosure)

As a **user progressing through onboarding**,
I want to answer questions 2-7 sequentially in the same container,
so that the platform learns my context and can personalize my learning experience.

**Acceptance Criteria:**
1. **Questions 2-7 appear sequentially in same container as Q1** (progressive disclosure, not separate pages)
   - Smooth fade-in/slide animation (300ms) between questions
   - No page reload, all client-side transitions
   - Previous answers stored in sessionStorage immediately
2. Question 2: "Which certification are you preparing for?" → Options: CBAP (default for MVP), [Other certifications grayed out/disabled]
3. Question 3: "What's your primary motivation?" → Options: Career advancement, Salary increase, Credibility, Personal growth, Other
4. Question 4: "When is your exam scheduled?" → Date picker (minimum: today + 30 days, maximum: today + 365 days), displays "X days until exam" after selection
5. Question 5: "What's your current knowledge level?" → Options: Beginner (new to BA), Intermediate (some experience), Advanced (experienced BA, need exam prep)
6. Question 6: "What's your target competency score?" → Options: 70% (pass threshold), 80% (confident pass), 90% (mastery)
7. Question 7: "How much time can you commit daily?" → Options: 30-60 minutes, 1-2 hours, 2+ hours
8. Each answer stored in sessionStorage immediately upon selection
9. **SessionStorage schema:** See `/docs/front-end-spec.md` Lines 391-407 for exact data structure:
   ```javascript
   {
     "onboarding_answers": {
       "referral_source": "search",
       "exam_type": "CBAP",
       "motivation": "career_advancement",
       "exam_date": "2025-12-21",
       "knowledge_level": "intermediate",
       "target_score": "pass",
       "daily_commitment": "1hr"
     },
     "started_at": "ISO8601 timestamp",
     "current_question": 7
   }
   ```
10. Progress indicator updates: "Question 2 of 7", "Question 3 of 7", etc. (thin progress bar at top of screen)
11. Optional "← Back" button allows returning to previous question (except from Q1 to landing page)
12. After Question 7 answered → automatically transition to Account Creation screen (same container, slide transition)

#### Story 3.3: Account Creation After Onboarding

As a **user who completed 7 onboarding questions**,
I want to create an account to save my progress,
so that I can proceed to the diagnostic assessment and access my personalized learning.

**Acceptance Criteria:**
1. Account creation screen displays message: "Create your account to save your progress and start your diagnostic assessment"
2. Form fields: Email (required, validated), Password (required, 8+ chars, letter + number), Confirm Password (must match)
3. Visual summary of onboarding data displayed above form (exam date: "X days until exam", target: Y%, daily time: Z hours) - builds trust that data is captured
4. "Create Account" button (pill-rounded, primary color)
5. On submit: POST to `/api/auth/register` with email + password
6. On successful registration: Receive JWT token, store in localStorage or HttpOnly cookie
7. Immediately POST onboarding data to `/api/user/onboarding` (7 answers persisted to user profile)
8. Clear sessionStorage after successful account creation (data now in database)
9. Redirect to Diagnostic Assessment screen
10. Error handling: Display validation errors inline (email already exists → "Email already registered, please login"), weak password → "Password must be at least 8 characters with letter and number"
11. "Already have an account? Login" link navigates to login page (edge case: returning user who started onboarding)

#### Story 3.4: Diagnostic Assessment Question Selection

As a **backend developer**,
I want to select 12 balanced diagnostic questions (3 per KA) with varied difficulty,
so that the diagnostic provides accurate baseline competency assessment.

**Acceptance Criteria:**
1. GET `/api/diagnostic/questions` endpoint (requires authentication)
2. Select exactly 12 questions: 3 from each of 6 KAs
3. Difficulty distribution per KA: 1 Easy, 1 Medium, 1 Hard (balanced assessment)
4. Questions selected randomly from available pool (different diagnostic each time, prevents memorization if retaken)
5. Question order randomized (not clustered by KA - intermix to reduce pattern recognition)
6. Response: JSON array of 12 question objects (id, question_text, options [A, B, C, D], ka, difficulty) - NO correct_answer or explanation yet
7. Mark diagnostic session as "in_progress" in database (track user's diagnostic state)
8. Unit tests: 12 questions returned, 3 per KA, varied difficulty, randomized order
9. Integration test: API returns valid diagnostic questions for authenticated user
10. Performance: Question selection in <500ms

#### Story 3.5: Diagnostic Assessment UI and Answer Recording

As a **user taking the diagnostic**,
I want to answer 12 questions in a focused, distraction-free interface,
so that I can provide accurate responses reflecting my true knowledge level.

**Acceptance Criteria:**
1. Diagnostic screen displays one question at a time (full-screen or centered, minimal chrome)
2. Question display: Question text, 4 options (A/B/C/D as pill-rounded buttons), progress "Question X of 12"
3. User selects one option → "Submit Answer" button enabled (or auto-advance on selection, UX decision TBD)
4. On submit: POST `/api/diagnostic/answer` with `question_id` and `selected_answer`
5. No immediate feedback (correct/incorrect not shown during diagnostic - per requirements)
6. Auto-advance to next question after answer recorded
7. Answers stored in `diagnostic_responses` table (user_id, question_id, selected_answer, timestamp)
8. After 12th question submitted → automatically calculate competency scores (Story 3.6)
9. Visual design: Focused mode, Inter font, pill buttons, secondary card styling for question container (14px radius)
10. No "Back" button during diagnostic (prevents changing answers after seeing later questions)
11. Session timeout warning at 30 minutes (if user pauses mid-diagnostic)

#### Story 3.6: Baseline Competency Calculation (Simplified IRT)

As a **system**,
I want to calculate baseline competency scores for each KA using simplified Item Response Theory,
so that users receive accurate assessment of their current knowledge level.

**Acceptance Criteria:**
1. After 12th diagnostic answer submitted, trigger competency calculation
2. For each KA, calculate competency score based on 3 questions answered:
   - Simplified IRT: Correct answer on Hard question → higher competency increase than Easy
   - Scoring formula (simplified): Base score 50%, +15% per correct Easy, +20% per correct Medium, +25% per correct Hard
   - Example: 1 correct Easy + 1 correct Medium + 0 correct Hard = 50% + 15% + 20% = 85% competency
3. Store competency scores in `competency_tracking` table (user_id, ka, competency_score, last_updated)
4. Calculate overall exam readiness score (average of 6 KA scores or weighted by CBAP exam distribution if data available)
5. Identify gap areas: KAs with competency < 70% flagged as "needs focus"
6. Unit tests: Various answer combinations produce expected competency scores, all 6 KAs have scores calculated
7. Integration test: Full diagnostic flow calculates and stores competency scores
8. Performance: Calculation executes in <1 second
9. Algorithm documented in `/docs/algorithms.md` for future refinement
10. Initial calibration: Expert review validates that competency scores feel accurate (e.g., 3/3 correct Hard questions → ~95-100% competency)

#### Story 3.7: Diagnostic Results Screen with Gap Analysis

As a **user who completed the diagnostic**,
I want to see my baseline competency scores and understand which areas need focus,
so that I can start studying effectively with clear direction.

**Acceptance Criteria:**
1. Results screen displays after diagnostic completion (GET `/api/diagnostic/results`)
2. Hero metric: Exam Readiness Score (0-100%, large display, color-coded: Red <70%, Orange 70-85%, Green >85%)
3. Six KA competency bars visualized (horizontal bars or radial chart, showing score 0-100% for each KA)
4. Each KA bar color-coded: Red (<70%), Orange (70-85%), Green (>85%)
5. Gap analysis section: "Focus Areas" listing KAs with <70% competency, sorted by lowest score first
6. Recommendations: "Start with [Lowest KA Name] where you scored X%"
7. Days until exam displayed: "X days to prepare"
8. Primary CTA: "Start Learning" button (pill-rounded, primary color) → navigates to first adaptive quiz session
9. Secondary CTA: "Retake Diagnostic" (if user wants to reset baseline - confirmation modal warns this will reset all competency tracking)
10. Visual design: Main screen container (35px radius), competency cards (22px radius), Framer-inspired layout, Inter font
11. Accessibility: Screen reader announces competency scores, color-coding supplemented with text labels (not color-only)
12. Post-diagnostic survey: "How accurately did this assessment reflect your knowledge?" (5-point scale: Very Inaccurate to Very Accurate) → target 80%+ "Accurate" or "Very Accurate"

---

### Epic 4: Adaptive Quiz Engine & Explanations

**Epic Goal:** Implement the core adaptive learning loop where users answer questions selected intelligently based on their competency gaps and difficulty matching, receive immediate feedback, and read detailed explanations for every question. This epic delivers quiz session management, real-time competency updates, and user feedback mechanisms.

**User Flow Reference:** See `docs/user-flows.md` Flow #4 (Learning Loop) and Flow #4b (Post-Session Review Flow) for visual representation of the complete learning experience including the post-session review phase introduced in v2.1.

#### Story 4.1: Quiz Session Creation and Management

As a **user ready to study**,
I want to start an adaptive quiz session,
so that I can practice questions matched to my competency level and knowledge gaps.

**Acceptance Criteria:**
1. POST `/api/quiz/session/start` endpoint creates new quiz session (requires authentication)
2. Session metadata stored: session_id, user_id, start_time, session_type ("new_content" for now, "mixed" added in Epic 7)
3. Session state tracked: questions_answered_count, current_question_id, is_paused, is_completed
4. Response: session_id and first adaptive question selected (Story 4.2 logic)
5. User can have only one active session at a time (if existing session incomplete → return existing session_id)
6. GET `/api/quiz/session/{session_id}` retrieves session state (questions answered so far, current question)
7. POST `/api/quiz/session/{session_id}/pause` pauses session (save state, can resume later)
8. POST `/api/quiz/session/{session_id}/end` ends session (mark completed, save end_time, calculate session stats)
9. Sessions auto-expire after 2 hours of inactivity (background cleanup job)
10. Unit tests: Session creation, pause, resume, end, retrieve state

#### Story 4.2: Adaptive Question Selection Logic

As a **quiz engine**,
I want to select the next question adaptively based on user's competency, knowledge gaps, and difficulty matching,
so that every question maximizes learning efficiency.

**Acceptance Criteria:**
1. Algorithm (`/app/services/adaptive_selection.py`):
   - **Step 1:** Identify weakest 2-3 KAs (lowest competency scores)
   - **Step 2:** Prioritize questions from weakest KAs (60% probability) vs. all KAs for breadth (40% probability)
   - **Step 3:** Match difficulty to user's current competency in that KA: <70% → Easy/Medium, 70-85% → Medium/Hard, >85% → Hard
   - **Step 4:** Filter out recently seen questions (exclude questions answered in last 7 days)
   - **Step 5:** Randomly select one question from filtered pool
2. Within-session difficulty adjustment (per Epic template requirements):
   - Track consecutive correct/incorrect answers in same KA within current session
   - If 3+ consecutive correct in KA → increase difficulty for next question in that KA (e.g., Medium → Hard)
   - If 3+ consecutive incorrect in KA → decrease difficulty for next question in that KA (e.g., Hard → Medium)
   - Adjustment resets between sessions (competency tracking persists, but within-session streaks don't)
3. Question returned includes: question_id, question_text, options, ka, difficulty (NO correct_answer or explanation yet)
4. Log selection rationale (for debugging): KA chosen, difficulty rationale, streak adjustment applied (if any)
5. Unit tests: Weakest KA prioritized, difficulty matched to competency, recently seen questions excluded, consecutive performance adjusts difficulty
6. Integration test: Adaptive selection returns appropriate questions across multiple quiz sessions
7. Performance: Selection logic executes in <200ms
8. Algorithm refinement: Monitor user feedback ("too easy" / "too hard") for future calibration

#### Story 4.3: Answer Submission and Immediate Feedback

As a **user answering a quiz question**,
I want to submit my answer and immediately see if I was correct or incorrect,
so that I receive instant feedback on my understanding.

**Acceptance Criteria:**
1. POST `/api/quiz/answer` endpoint accepts: session_id, question_id, selected_answer (A/B/C/D)
2. Record response in `quiz_responses` table (user_id, session_id, question_id, selected_answer, is_correct, time_taken, timestamp)
3. Determine correctness: Compare `selected_answer` to question's `correct_answer`
4. Response JSON:
   - `is_correct`: true/false
   - `correct_answer`: The right answer (e.g., "B")
   - `explanation`: Detailed explanation text
   - `competency_update`: New competency score for this KA (see Story 4.4)
5. Frontend displays immediate visual feedback:
   - Correct answer: Green checkmark icon, "Correct!" message
   - Incorrect answer: Orange/red X icon, "Incorrect. The correct answer is B."
6. No auto-advance yet (user must click "Next" after reading explanation - Story 4.5)
7. Track time_taken (client-side or server-side timestamp diff from question displayed to answer submitted)
8. Unit tests: Correct answer recorded, incorrect answer recorded, response includes explanation
9. Integration test: Full answer submission flow updates database and returns feedback
10. Error handling: Invalid session_id or question_id → 400 Bad Request

#### Story 4.4: Real-Time Competency Score Updates

As a **system**,
I want to update the user's competency score for the relevant KA after every quiz answer,
so that competency tracking reflects current knowledge level in real-time.

**Acceptance Criteria:**
1. After answer submission (Story 4.3), trigger competency update for the question's KA
2. Simplified IRT update logic:
   - Correct answer on Hard question: +5% competency (or more sophisticated IRT calculation)
   - Correct answer on Medium: +3% competency
   - Correct answer on Easy: +2% competency
   - Incorrect answer: -1% competency (small penalty to reflect gap)
   - Competency score capped at 0-100%
3. Update `competency_tracking` table: Set new `competency_score`, update `last_updated` timestamp
4. Include updated competency score in answer submission response (Story 4.3)
5. Exam readiness score recalculated as average (or weighted average) of all 6 KA scores
6. Unit tests: Various answer/difficulty combinations produce expected competency changes, score stays within 0-100%
7. Integration test: Multiple answers update competency progressively
8. Performance: Competency update executes in <100ms (included in answer submission response time)
9. Algorithm documented in `/docs/algorithms.md` for future refinement (full IRT in Phase 2)
10. Historical competency tracking: Store snapshots weekly for progress trends (see Epic 6)

#### Story 4.5: Explanation Display with User Feedback

As a **user who answered a question**,
I want to read a detailed explanation of why the correct answer is right and why other options are wrong,
so that I learn the concept rather than just memorizing answers.

**Acceptance Criteria:**
1. After answer submission and immediate feedback (Story 4.3), display explanation section below result
2. Explanation text retrieved from question's `explanation` field (loaded during question import, Story 2.2)
3. Explanation formatting:
   - **Maximum 200 characters total** (enforced during content creation) - concise, focused explanations
   - **"Why [Correct Answer] is correct:"** section explaining the right answer (2-3 sentences maximum)
   - **"Why other options are incorrect:"** brief explanation for each wrong option
   - **BABOK reference:** "See BABOK v3 Section X.Y.Z for more details" (included within 200-char limit if applicable)
   - **Rationale:** 200-char limit ensures explanations fit on screen without scrolling, reducing cognitive load
4. Explanation card styled with secondary card border radius (14px), readable typography (Inter font, adequate line spacing)
5. User feedback mechanism: Thumbs up / thumbs down icons below explanation
   - Click thumbs up → POST `/api/feedback/explanation` with `question_id`, `helpful: true`
   - Click thumbs down → POST `/api/feedback/explanation` with `question_id`, `helpful: false`
   - Feedback stored in `explanation_feedback` table (user_id, question_id, helpful, timestamp)
   - Visual feedback: Icon highlights after click, "Thanks for your feedback!" message
6. "Report Issue" link allows flagging incorrect questions (POST `/api/feedback/report` with `question_id`, `issue_description`)
7. "Next Question" button (pill-rounded, primary color) below explanation → advances to next adaptive question (Story 4.2 selects next)
8. Accessibility: Explanation text is screen-reader friendly, thumbs icons have alt text
9. Unit tests: Explanation renders, feedback submission works
10. Integration test: User can read explanation and provide feedback after answering question

#### Story 4.6: Post-Session Review Initiation (v2.1 NEW)

As a **user who completed a quiz session with incorrect answers**,
I want to immediately review all questions I got wrong,
so that I can reinforce correct understanding and improve retention.

**Acceptance Criteria:**
1. When quiz session ends (user clicks "End Session"), backend checks for incorrect answers in this session
2. If incorrect answers exist → redirect to Post-Session Review Transition Screen instead of dashboard
3. If all answers correct (perfect score) → show congratulatory message, skip review, return to dashboard
4. Transition screen displays:
   - Header: "Great work! Let's review X questions you got wrong"
   - Subtext: "Immediate review improves retention 2-3x"
   - Primary CTA: "Start Review" (pill-rounded button)
   - Secondary CTA: "Skip Review" (text link, less prominent)
5. POST `/api/v1/sessions/{session_id}/review/start` creates `session_reviews` record with status `not_started`
6. Response includes review_id, total_questions_to_review, and array of incorrect question IDs
7. If user clicks "Skip Review" → show confirmation modal: "Are you sure? Reviewing now will strengthen retention"
8. If user confirms skip → POST `/api/v1/sessions/{session_id}/review/skip`, update review status to `skipped`, return to dashboard
9. Track review skip rate for analytics (target: <30% skip rate)
10. Unit tests: Review initiation triggered only when incorrect answers exist
11. Integration test: User completing session with incorrect answers sees review transition screen

#### Story 4.7: Re-Present Incorrect Questions for Review

As a **user in review mode**,
I want to re-answer each question I got wrong,
so that I can test my understanding and reinforce the correct answer.

**Acceptance Criteria:**
1. Review screen displays first incorrect question with "REVIEW" badge (distinct visual indicator)
2. Progress indicator: "Review Question 1 of X" (shows current position in review)
3. Question display identical to quiz session (same format, same 4 options)
4. User cannot see their original incorrect answer (clean slate for re-attempt)
5. User selects answer and clicks "Submit Answer"
6. POST `/api/v1/sessions/{session_id}/review/answer` with:
   - `original_attempt_id` (FK to original incorrect attempt)
   - `selected_choice_id` (user's new answer)
   - `time_spent_seconds`
7. Backend creates `review_attempts` record linking to `session_reviews` and `question_attempts`
8. Backend calculates `is_correct` (boolean) and `is_reinforced` (true if incorrect → correct)
9. Response returns: `is_correct`, `is_reinforced`, `correct_answer`, `explanation`
10. Frontend displays immediate feedback:
    - If reinforced (incorrect → correct): Green checkmark + "Great improvement! 🎉"
    - If still incorrect: Orange X + "Still incorrect. Correct answer is: B"
11. Update competency score based on review performance (reinforced = +2% boost, still incorrect = neutral)
12. Automatically advance to next review question or review summary if complete
13. Unit tests: Review attempt recorded correctly, reinforcement logic works
14. Integration test: User can re-answer all incorrect questions and see appropriate feedback

#### Story 4.8: Review Performance Tracking and Summary

As a **user who completed post-session review**,
I want to see a summary of my review performance,
so that I can understand my improvement and identify concepts needing more practice.

**Acceptance Criteria:**
1. After last review question answered → display Review Summary Screen
2. Summary displays:
   - Total questions reviewed: X
   - Reinforced correctly (incorrect → correct): Y (green)
   - Still incorrect: Z (orange)
   - Improvement calculation: "Original: 80% → Final: 93% (+13%)"
3. "Original" score = session accuracy BEFORE review (e.g., 12/15 = 80%)
4. "Final" score = session accuracy AFTER review (e.g., 14/15 = 93%, assuming 2 reinforced)
5. Display list of still-incorrect questions with:
   - Question preview (first 50 chars)
   - Knowledge Area tag
   - "These will appear in spaced repetition reviews"
6. POST `/api/v1/sessions/{session_id}/review/complete` updates `session_reviews`:
   - `review_status` = `completed`
   - `questions_reinforced_correctly` = count
   - `questions_still_incorrect` = count
   - `review_completed_at` = timestamp
7. Primary CTA: "Return to Dashboard" → updates dashboard with new competency scores
8. Track review completion rate (target: 70%+ of users complete review when prompted)
9. Track reinforcement success rate (target: 60%+ of review attempts are reinforced)
10. Unit tests: Summary calculations accurate, metrics tracked correctly
11. Integration test: Completed review updates session_reviews table and returns user to dashboard

#### Story 4.9: Review Analytics and Dashboard Integration

As a **system**,
I want to track post-session review engagement and performance metrics,
so that we can validate the 2-3x retention improvement hypothesis and measure feature adoption.

**Acceptance Criteria:**
1. Dashboard displays review completion metrics:
   - Total reviews completed
   - Average reinforcement success rate (% of incorrect → correct)
   - Review adoption rate (% of sessions with reviews that user completed)
2. Analytics track per-user:
   - `total_reviews_offered` (sessions with incorrect answers)
   - `total_reviews_completed`
   - `total_reviews_skipped`
   - `total_questions_reinforced`
3. GET `/api/dashboard` response includes:
   - `review_stats.adoption_rate` (float, 0.0-1.0)
   - `review_stats.reinforcement_success_rate` (float, 0.0-1.0)
   - `review_stats.total_reinforced` (int)
4. Admin endpoint GET `/api/admin/alpha-metrics` includes:
   - Platform-wide review adoption rate
   - Platform-wide reinforcement success rate
   - User cohort comparison (reviewers vs. non-reviewers retention rates)
5. Spaced repetition algorithm prioritizes still-incorrect questions from reviews (schedule for +1 day review)
6. Correctly reinforced questions get standard spaced repetition interval (+3 days)
7. Track reading time during review phase (if user expands explanations or reading materials)
8. **Analytics Event Logging:** All review interactions must emit standardized events for tracking:
   - **Event: `post_session_review_started`** - Emitted when user begins review
     - Fields: `session_id`, `user_id`, `total_questions_to_review`, `original_session_accuracy`, `timestamp`
   - **Event: `review_question_answered`** - Emitted after each review answer submitted
     - Fields: `review_id`, `question_id`, `original_answer`, `review_answer`, `is_reinforced`, `time_spent_seconds`, `timestamp`
   - **Event: `review_reading_expanded`** - Emitted when user expands reading material during review
     - Fields: `review_id`, `chunk_id`, `question_id`, `babok_section`, `time_spent_seconds`, `timestamp`
   - **Event: `post_session_review_completed`** - Emitted when review phase finishes
     - Fields: `review_id`, `session_id`, `total_reviewed`, `reinforced_correctly`, `still_incorrect`, `reading_chunks_viewed`, `total_reading_time_seconds`, `final_accuracy`, `accuracy_improvement`, `timestamp`
   - **Event: `post_session_review_skipped`** - Emitted when user skips review
     - Fields: `session_id`, `questions_to_review`, `original_accuracy`, `timestamp`
9. Unit tests: Analytics calculations accurate, all events logged correctly with proper schemas
10. Integration test: Review completion updates user analytics and dashboard metrics, events are emitted
11. Performance: Dashboard analytics queries optimized with database indexes on `session_reviews(user_id, review_status)`

---

### Epic 5: Targeted Reading Content Integration

**🚨 CRITICAL IMPLEMENTATION NOTE - v2.1 Update:**

**Stories 5.1-5.4 are DEPRECATED.** They describe the v2.0 synchronous reading model (inline reading after explanations) which was found to interrupt learning flow and reduce engagement. These stories are preserved **for historical reference only**.

**Stories 5.5-5.9 are the AUTHORITATIVE implementation.** LearnR v2.1 implements the **Asynchronous Reading Library** model which provides superior UX through:
- Zero interruption to learning flow ("test fast, read later")
- User control over when to engage with reading materials
- Prioritized reading queue with smart filtering
- 2x improvement in reading engagement (25% → 50%+ expected)

**For software architects:** Implement Stories 5.5-5.9 (Async Reading Library). Do NOT implement Stories 5.1-5.4 unless explicitly directed for a specific integration scenario.

**Detailed Specifications:** See `/docs/Asynchronous_Reading_Model.md` for complete technical architecture of the v2.1 async reading system.

**User Flow Reference:** See `docs/user-flows.md` Flow #9 (Reading Library Flow) for visual representation of the asynchronous reading queue system introduced in v2.1. This flow shows how users access curated reading materials on-demand without interrupting their quiz experience.

**Epic Goal:** Complete the learning loop by adding semantic retrieval of BABOK v3 reading content that addresses user-specific knowledge gaps. This is the **critical differentiator** for LearnR - transforming it from "just another quiz app" to a complete learning system. This epic delivers vector search, reading content display after explanations, and engagement tracking to validate the differentiation value during Day 24 alpha test.

#### Story 5.1: Gap-Based Reading Content Retrieval

As a **system**,
I want to automatically retrieve relevant BABOK reading chunks after a user answers a question incorrectly,
so that users can read targeted content addressing their specific knowledge gaps.

**Acceptance Criteria:**
1. After answer submission (Story 4.3), if answer is **incorrect** → trigger reading content retrieval
2. Generate query for semantic search:
   - Primary: Question's `concept_tags` (e.g., ["stakeholder analysis", "requirements elicitation"])
   - Secondary: Question text itself (if concept_tags not comprehensive)
3. Call `/api/content/reading` (Story 2.7) with query_text and KA filter (same KA as question)
4. Retrieve top 2-3 BABOK chunks ranked by semantic similarity
5. Filter chunks by difficulty: Match to user's competency level in this KA (e.g., if user at 60% competency, retrieve Easy/Medium chunks, not Hard)
6. Return chunks in response to answer submission (Story 4.3 response expanded to include `reading_content` array)
7. If answer is **correct** on Easy/Medium question → no reading content (user already knows this, don't overwhelm)
8. If answer is **correct** on Hard question → optionally show 1 chunk for reinforcement (configurable)
9. Unit tests: Incorrect answer triggers retrieval, correct Easy answer does not, KA filtering works
10. Integration test: Semantic search returns BABOK content relevant to missed question concept

#### Story 5.2: Reading Content Display in Quiz Flow

As a **user who answered incorrectly**,
I want to read relevant BABOK content immediately after seeing the explanation,
so that I can understand the concept more deeply and fill my knowledge gap.

**Acceptance Criteria:**
1. Reading content section displays after explanation (Story 4.5), before "Next Question" button
2. Section header: "Learn More: Targeted Reading from BABOK v3" (clarifies source and purpose)
3. Display 2-3 reading chunks as expandable cards (14px border radius, secondary styling)
4. Each chunk card shows:
   - **BABOK Section Reference:** "Section 3.2.1: Stakeholder Analysis"
   - **Preview:** First 100 characters of `text_content` + "... Read more"
   - **Expand/Collapse:** Click to show full text_content (200-500 tokens)
5. Expanded state: Full text displayed with readable formatting (line spacing, paragraph breaks preserved)
6. "Mark as Read" checkbox for each chunk (tracks engagement)
7. If user clicks "Mark as Read" → POST `/api/reading/track` with `chunk_id`, stores in `reading_history` table (user_id, chunk_id, marked_read: true, timestamp)
8. "Skip Reading" button allows advancing to next question without reading (optional, not forced)
9. Visual design: Reading section visually separated from explanation (subtle border or background color), Inter font, adequate spacing
10. Accessibility: Expandable sections keyboard-accessible (Enter to expand/collapse), screen reader announces expanded state

#### Story 5.3: Reading Engagement Tracking and Analytics

As a **product manager**,
I want to track which reading chunks users engage with and how long they spend reading,
so that I can validate the reading feature's value during alpha test (Day 24 Go/No-Go decision).

**Acceptance Criteria:**
1. Track reading engagement events in `reading_engagement` table (user_id, chunk_id, session_id, displayed_at, expanded_at, time_spent_seconds, marked_read)
2. Frontend JavaScript tracks:
   - **Displayed:** Chunk shown to user (logged immediately)
   - **Expanded:** User clicked to read full content (logged on expand)
   - **Time Spent:** Seconds from expand to next action (collapse, next question, etc.) - measure reading duration
   - **Marked Read:** User clicked "Mark as Read" checkbox
3. POST `/api/reading/engagement` endpoint accepts engagement events from frontend
4. Engagement metrics calculated per user:
   - **Reading Engagement Rate:** % of displayed chunks that were expanded (target 60%+ per requirements)
   - **Average Time Spent:** Seconds per chunk (target 2-4 minutes for 200-500 token chunks per Brief)
   - **Marked Read Rate:** % of expanded chunks marked as read
5. Dashboard for product team (not user-facing): Aggregate reading metrics across all users
   - Total chunks displayed vs. expanded vs. marked read
   - Average engagement rate and time spent
   - Breakdown by KA (which KAs have highest reading engagement)
6. Alpha test validation (Day 24): Check if engagement rate >60% and user feedback positive (Story 5.4)
7. Unit tests: Engagement events logged correctly, metrics calculated accurately
8. Integration test: Full quiz flow logs reading engagement from display to mark-as-read
9. Performance: Engagement logging does not slow down quiz flow (<100ms latency)
10. Privacy: Engagement data anonymized for aggregate analytics

#### Story 5.4: Reading Content Feedback and Relevance Validation

As a **user reading BABOK content**,
I want to provide feedback on whether the content was relevant to my knowledge gap,
so that the platform can improve content retrieval accuracy.

**Acceptance Criteria:**
1. Below each reading chunk, display feedback prompt: "Was this content relevant to your gap?" with Thumbs Up / Thumbs Down icons
2. Click thumbs up → POST `/api/feedback/reading` with `chunk_id`, `relevant: true`
3. Click thumbs down → POST `/api/feedback/reading` with `chunk_id`, `relevant: false`, optional `reason` text field (e.g., "Too basic", "Not related to question", "Too advanced")
4. Feedback stored in `reading_feedback` table (user_id, chunk_id, relevant, reason, timestamp)
5. Visual feedback: Icon highlights after click, "Thanks for your feedback!" message
6. Relevance metrics calculated:
   - **Relevance Rate:** % of chunks rated thumbs up (target 80%+ per Brief requirements)
   - Breakdown by KA and difficulty level
7. Product team dashboard shows relevance metrics to validate semantic search quality
8. Alpha test validation (Day 24): Check if relevance rate >70% (acceptable) or >80% (excellent) to determine Go/No-Go for reading feature
9. Unit tests: Feedback submission works, relevance metrics calculated
10. Integration test: User can rate reading content relevance, data persists

#### Story 5.5: Background Reading Queue Population (v2.1 NEW - ASYNC MODEL)

As a **system**,
I want to automatically add relevant reading materials to the user's reading queue as they answer questions,
so that users have curated study materials available without interrupting their quiz flow.

**Acceptance Criteria:**
1. After user answers ANY question (correct or incorrect), trigger async background process to add reading materials
2. For incorrect answers: Add 2-3 high-priority BABOK chunks (semantic search on question concepts + KA)
3. For correct answers on Hard questions: Add 1 medium-priority chunk for reinforcement (optional, configurable)
4. For correct answers on Easy/Medium: Skip reading recommendation (user already understands)
5. Semantic search query composition:
   - Primary: Question `concept_tags` (e.g., ["stakeholder analysis", "requirements elicitation"])
   - Secondary: Question text if concept_tags insufficient
   - Filter: Same KA as question
6. POST `/api/v1/reading/queue` (internal/background call) with:
   - `user_id`, `chunk_id`, `question_id`, `session_id`
   - `was_incorrect` (boolean), `relevance_score` (from semantic search), `ka_id`
   - `priority` calculated based on: competency gap in KA (larger gap = higher priority), question difficulty
7. Priority calculation logic:
   - High: User competency in KA <60% AND incorrect answer
   - Medium: User competency 60-80% OR correct on hard question
   - Low: User competency >80% AND correct answer (rare, for completeness)
8. Database: Insert into `reading_queue` table with `reading_status = 'unread'`
9. Duplicate prevention: If chunk already in user's queue → update `relevance_score` if higher, don't duplicate
10. Performance: Background process <200ms, doesn't block answer submission response
11. Unit tests: Reading queue population triggered correctly, priority calculation accurate
12. Integration test: Answering questions adds appropriate reading materials to queue

#### Story 5.6: Silent Badge Updates in Navigation

As a **system**,
I want to update the reading library badge count silently as new materials are added,
so that users are aware of new content without interrupting their quiz flow.

**Acceptance Criteria:**
1. Navigation bar includes "Reading Library" link with badge count (e.g., "Reading [7]")
2. Badge displays count of `reading_queue` items with `reading_status = 'unread'`
3. Badge updates automatically via WebSocket OR polling (every 5-10 seconds during quiz session)
4. WebSocket implementation (RECOMMENDED):
   - Backend emits `reading_queue_updated` event with new `unread_count` when items added
   - Frontend listens and updates badge count reactively
   - No popup, toast, or notification shown (completely silent)
5. Polling fallback (if WebSocket not implemented in MVP):
   - Frontend polls GET `/api/v1/reading/stats` every 10 seconds during active quiz session
   - Response: `{unread_count: 7, high_priority_count: 3}`
   - Update badge silently
6. Badge styling: Small circular badge (8px border radius), orange/blue color, white text, positioned top-right of "Reading" text
7. Badge appears only when count >0, hidden when count = 0
8. Clicking badge/link navigates to Reading Library page (Story 5.7)
9. Unit tests: Badge count updates correctly when queue items added
10. Integration test: User answering questions sees badge count increment silently

#### Story 5.7: Reading Library Page with Queue Display

As a **user**,
I want to browse my reading queue in a dedicated library page,
so that I can read study materials when I'm ready, not when forced during quizzes.

**Acceptance Criteria:**
1. Dedicated page/route: `/reading-library` accessible from main navigation
2. GET `/api/v1/reading/queue?status=unread&sort_by=priority` retrieves user's reading queue
3. Query parameters supported:
   - `status=unread|reading|completed|dismissed|all` (default: unread)
   - `ka_id=uuid` (filter by Knowledge Area)
   - `priority=high|medium|low` (filter by priority)
   - `sort_by=priority|date|relevance` (default: priority)
4. Response includes array of queue items with:
   - `queue_id`, `chunk_id`, `title` (BABOK section name), `preview` (first 100 chars)
   - `babok_section` (e.g., "3.2.1"), `ka_name`, `relevance_score`, `priority`, `reading_status`
   - `word_count`, `estimated_read_minutes` (word_count / 200)
   - Context: `question_preview`, `was_incorrect`, `added_at`
5. Library page displays queue items as cards (14px border radius):
   - Priority badge (High = red, Medium = orange, Low = blue)
   - BABOK section title + preview
   - Knowledge Area tag
   - Context: "Added after incorrect answer on: [Question preview]" (shows why recommended)
   - Estimated read time (e.g., "2 min read")
   - "Read Now" button (primary CTA)
6. Tabs or filter bar: Unread (default) | Reading | Completed
7. Sort dropdown: Priority (default) | Date Added | Relevance Score
8. Filter by KA: Dropdown with 6 KA options + "All KAs"
9. Empty state: "Your reading library is empty. Complete quiz sessions to get personalized recommendations!"
10. Visual design: Framer-inspired, Inter font, cards (14px radius), main container (35px radius)
11. Accessibility: Cards keyboard navigable, screen reader announces priority and context
12. Unit tests: Library page renders, filters work
13. Integration test: User can browse queue and see all reading items

#### Story 5.8: Reading Item Detail View and Engagement Tracking

As a **user**,
I want to read individual BABOK chunks in detail and mark them as complete,
so that I can learn the material and track my reading progress.

**Acceptance Criteria:**
1. Clicking "Read Now" on queue item → navigate to detail view OR expand in-place (modal or dedicated page)
2. GET `/api/v1/reading/queue/{queue_id}` retrieves full chunk content
3. Response includes:
   - Full `text_content` (200-500 tokens, formatted markdown or plain text)
   - BABOK section reference, title, KA name
   - Context: Question that prompted recommendation
   - Previous reading history: `times_opened`, `total_reading_time_seconds`
4. Detail view displays:
   - Full reading content (readable formatting, proper line spacing, paragraph breaks)
   - BABOK section reference at top (e.g., "BABOK v3 - Section 3.2.1: Stakeholder Analysis")
   - Context card: "This was recommended because you answered [Question preview] incorrectly"
   - Actions: "Mark as Complete", "Dismiss", "Back to Library"
5. Track engagement automatically:
   - On view load → increment `times_opened`, set `first_opened_at` if first time
   - On view close/navigate away → calculate `time_spent_seconds` (time between load and close)
   - PUT `/api/v1/reading/queue/{queue_id}/engagement` with `time_spent_seconds`
   - Update `total_reading_time_seconds += time_spent_seconds`
6. "Mark as Complete" action:
   - PUT `/api/v1/reading/queue/{queue_id}/status` with `reading_status = 'completed'`
   - Set `completed_at` timestamp
   - Decrement unread badge count
   - Show success message: "Great! Added to your completed reading"
7. "Dismiss" action:
   - PUT `/api/v1/reading/queue/{queue_id}/status` with `reading_status = 'dismissed'`
   - Set `dismissed_at` timestamp
   - Remove from unread count
   - Show confirmation: "Dismissed. You can find this in Dismissed tab if needed."
8. **Bulk dismiss action:** POST `/api/v1/reading/queue/batch-dismiss` endpoint
   - Request body: `{"queue_ids": ["uuid1", "uuid2", "uuid3"]}`
   - Response: `{"dismissed_count": 3, "remaining_unread_count": 4}`
   - Use case: "Dismiss All Low Priority" button on library page
   - All specified queue_ids set to `reading_status = 'dismissed'` with single API call
9. Unit tests: Engagement tracking works, status updates correctly, batch dismiss works
10. Integration test: User can read content, mark complete, batch dismiss, and see badge count update

#### Story 5.9: Reading Queue Analytics and Completion Rates

As a **product team**,
I want to track reading queue engagement metrics,
so that we can validate the async reading model improves completion rates vs. inline reading.

**Acceptance Criteria:**
1. GET `/api/v1/reading/stats` endpoint returns complete user-level reading analytics
   - **Response schema** (see `docs/Asynchronous_Reading_Model.md` Lines 398-436 for complete spec):
   ```json
   {
     "reading_stats": {
       "total_items_added": 45,
       "total_completed": 28,
       "total_dismissed": 10,
       "current_unread": 7,
       "completion_rate": 0.62,
       "this_week": {
         "items_added": 7,
         "items_completed": 5,
         "total_reading_time_minutes": 25
       },
       "by_ka": [
         {
           "ka_name": "Business Analysis Planning and Monitoring",
           "unread": 3,
           "completed": 8,
           "completion_rate": 0.73
         }
       ],
       "average_reading_time_minutes": 2.5,
       "total_reading_time_hours": 1.2
     }
   }
   ```
   - Target: `completion_rate` >0.50 (50%+ per PRD v2.1 success criteria)
2. Dashboard integration: Display reading stats on main dashboard
   - "Reading Progress: X completed (Y% completion rate)"
   - "Total Reading Time: Z minutes"
3. Admin analytics endpoint GET `/api/admin/alpha-metrics/reading`:
   - Platform-wide reading completion rate
   - Comparison: Async model (v2.1) vs. Inline model (v2.0 baseline, if A/B tested)
   - Average reading time per chunk
   - Most frequently added BABOK sections (helps identify high-value content)
4. Track reading engagement by priority:
   - High priority items: Completion rate (expect highest)
   - Medium priority: Completion rate
   - Low priority: Completion rate (expect lowest)
5. Hypothesis validation metrics (Day 24 alpha test):
   - Async reading completion rate >50% (vs. 25% inline baseline per PRD)
   - User satisfaction with "read when ready" model (survey question)
6. Spaced repetition integration: Items marked "completed" should not re-appear in queue (unique constraint enforced)
7. Retention analysis: Users who complete reading have better long-term retention (tracked via spaced repetition accuracy)
8. Unit tests: Analytics calculations accurate
9. Integration test: Reading completion updates all analytics metrics
10. Performance: Analytics queries optimized with indexes on `reading_queue(user_id, reading_status)`

#### Story 5.10: Manual Reading Bookmarks for Post-Session Review (v2.1 NEW)

As a **user reviewing incorrect answers**,
I want to manually bookmark specific reading materials during post-session review for later study,
so that I can save high-priority content separately from the automatic reading queue.

**Context:** This story complements the automatic reading queue (Stories 5.5-5.9) by allowing users to explicitly bookmark materials they find particularly valuable during the post-session review phase. While the reading queue is auto-populated, bookmarks are user-initiated and signify higher intent to study specific content.

**Acceptance Criteria:**
1. **Database Schema:** Create `reading_bookmarks` table with the following structure:
   ```sql
   CREATE TABLE reading_bookmarks (
       bookmark_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
       user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
       chunk_id UUID NOT NULL REFERENCES content_chunks(chunk_id) ON DELETE CASCADE,

       -- Context: What prompted this bookmark
       question_id UUID REFERENCES questions(question_id) ON DELETE SET NULL,
       session_id UUID REFERENCES sessions(session_id) ON DELETE SET NULL,
       review_id UUID REFERENCES session_reviews(review_id) ON DELETE SET NULL,

       -- State tracking
       is_read BOOLEAN DEFAULT FALSE,
       read_at TIMESTAMP,

       -- Timestamps
       bookmarked_at TIMESTAMP NOT NULL DEFAULT NOW(),

       CONSTRAINT fk_bookmark_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
       CONSTRAINT fk_bookmark_chunk FOREIGN KEY (chunk_id) REFERENCES content_chunks(chunk_id) ON DELETE CASCADE,
       CONSTRAINT unique_user_chunk_bookmark UNIQUE (user_id, chunk_id)
   );

   CREATE INDEX idx_reading_bookmarks_user ON reading_bookmarks(user_id);
   CREATE INDEX idx_reading_bookmarks_unread ON reading_bookmarks(user_id, is_read) WHERE is_read = FALSE;
   ```

2. **POST `/api/v1/reading/bookmarks` endpoint** - Create new bookmark
   - Request body: `{"chunk_id": "uuid", "question_id": "uuid", "session_id": "uuid", "review_id": "uuid"}`
   - Response: `201 Created` with `{"bookmark_id": "uuid", "chunk_id": "uuid", "bookmarked_at": "ISO8601"}`
   - Validation: Duplicate bookmarks return existing bookmark (idempotent), not 409 error
   - Business logic: If chunk already in user's reading_queue, mark it as bookmarked (add flag to reading_queue or separate tracking)

3. **GET `/api/v1/reading/bookmarks` endpoint** - Retrieve user's bookmarks
   - Query parameters:
     - `unread_only=true|false` (default: false) - Filter to unread bookmarks only
     - `ka_id=uuid` (optional) - Filter by Knowledge Area
     - `page=1` and `per_page=20` (pagination)
   - Response: Array of bookmark objects including:
     - `bookmark_id`, `chunk_id`, `title` (BABOK section name), `preview` (first 100 chars)
     - `babok_section` (e.g., "3.2.1"), `ka_name`, `word_count`, `estimated_read_minutes`
     - Context: `question_preview`, `session_id`, `review_id`, `bookmarked_at`
     - `is_read`, `read_at`
   - Pagination metadata: `total_items`, `total_pages`, `current_page`

4. **PUT `/api/v1/reading/bookmarks/{bookmark_id}/mark-read` endpoint** - Mark bookmark as read
   - Request: No body required
   - Response: `200 OK` with `{"bookmark_id": "uuid", "is_read": true, "read_at": "ISO8601"}`
   - Business logic: Set `is_read = TRUE`, `read_at = NOW()`

5. **DELETE `/api/v1/reading/bookmarks/{bookmark_id}` endpoint** - Remove bookmark
   - Response: `204 No Content`
   - Business logic: Soft delete or hard delete (decision: hard delete for MVP simplicity)

6. **Frontend Integration in Post-Session Review:**
   - When displaying reading material during review (Story 4.7), add "Save for Later" button next to each chunk
   - Clicking "Save for Later" → POST to `/api/v1/reading/bookmarks` → Visual confirmation ("Bookmarked!")
   - If chunk already bookmarked → show "Bookmarked ✓" (disabled state)

7. **Bookmarks Page/Section in Navigation:**
   - Add "Bookmarks" link in navigation (separate from "Reading Library")
   - Bookmarks page displays user's saved materials using GET `/api/v1/reading/bookmarks`
   - Tabs: "Unread Bookmarks" (default) | "All Bookmarks"
   - Each bookmark card shows same design as reading queue but with bookmark icon
   - Actions: "Read Now", "Mark as Read", "Remove Bookmark"

8. **Distinction from Reading Queue:**
   - Reading Queue (`reading_queue` table): Auto-populated, system-driven recommendations based on incorrect answers
   - Reading Bookmarks (`reading_bookmarks` table): User-initiated, manually saved high-value materials
   - Both can coexist: A chunk can be in both queue AND bookmarks (separate tables, separate tracking)
   - User benefit: Bookmarks provide a "favorites" layer on top of the queue for items requiring extra attention

9. **Analytics Tracking:**
   - Track bookmark creation rate: % of displayed reading chunks that get bookmarked (expect 10-20%)
   - Track bookmark read rate: % of bookmarks that get marked as read (target: 70%+, higher than queue)
   - Compare engagement: Bookmarked items should have higher completion rate than queue items (validates manual curation)

10. **Unit Tests:**
    - Create bookmark, retrieve bookmarks, mark as read, remove bookmark
    - Idempotent bookmark creation (duplicate returns existing)
    - Pagination works correctly
    - Filtering by unread_only and ka_id works

11. **Integration Tests:**
    - Full bookmark flow: Create → Retrieve → Mark Read → Delete
    - Bookmark during review session updates bookmarks list
    - Bookmarks persist across sessions

12. **Performance:**
    - Bookmark queries optimized with indexes on `user_id` and `is_read`
    - GET `/api/v1/reading/bookmarks` returns in <200ms for up to 100 bookmarks per user

**Success Metrics (30-day post-launch):**
- Bookmark adoption: 30%+ of users create at least 1 bookmark
- Bookmark read rate: 70%+ of bookmarks are marked as read (vs. 50% for queue items)
- Average bookmarks per active user: 5-10
- Bookmark-to-queue ratio: ~1:5 (users are selective about bookmarking)

**Relationship to Reading Queue:**
- Reading Queue (Stories 5.5-5.9): Broad net, auto-populated, may have false positives
- Reading Bookmarks (Story 5.10): Curated collection, user-verified relevance, higher intent
- Together: Queue provides discovery, Bookmarks provide focus

---

### Epic 6: Progress Dashboard & Transparency

**Epic Goal:** Provide users with comprehensive progress visibility through a real-time dashboard showing competency scores for all 6 KAs, exam readiness scoring, weekly progress trends, reviews due count, days until exam, and actionable recommendations. This epic delivers the transparency that builds user trust and engagement.

#### Story 6.1: Dashboard Overview with 6 KA Competency Bars

As a **user**,
I want to see my current competency scores for all 6 CBAP knowledge areas at a glance,
so that I understand exactly where I stand and which areas need focus.

**Acceptance Criteria:**
1. GET `/api/dashboard` endpoint returns user's current competency data (requires authentication)
2. Response includes:
   - `ka_scores`: Array of 6 objects with `ka_name`, `competency_score` (0-100%), `target_score`, `gap` (target - current)
   - `exam_readiness_score`: Overall readiness (0-100%, average or weighted average of 6 KAs)
   - `days_until_exam`: Calculated from onboarding `exam_date`
   - `reviews_due_count`: Number of concepts needing spaced repetition review (Epic 7 integration)
   - `total_questions_answered`: Lifetime count
   - `total_reading_consumed`: Number of chunks read
3. Dashboard UI displays 6 competency bars (horizontal bars or radial/circular charts):
   - Each bar shows KA name, current score (e.g., "Strategy Analysis: 75%"), target score (e.g., "Target: 85%")
   - Bar color-coded: Red (<70%), Orange (70-85%), Green (>85%)
   - Visual fill indicates progress toward target (e.g., bar filled 75% if score is 75%)
4. Hero metric: Exam Readiness Score displayed prominently (large text, color-coded, main screen container 35px radius)
5. Recommended focus areas: "Focus on [Lowest KA]" callout or section highlighting weakest 2-3 KAs
6. Visual design: Framer-inspired layout, Inter font, primary cards for KA bars (22px radius), main container (35px radius)
7. Accessibility: Bar charts have text labels (not color-only), screen reader announces competency scores
8. Unit tests: Dashboard data retrieval, competency scores displayed correctly
9. Integration test: Dashboard reflects competency updates from quiz sessions
10. Performance: Dashboard renders in <2 seconds with all data

#### Story 6.2: Weekly Progress Trends Chart

As a **user tracking my improvement**,
I want to see how my competency scores have changed week-over-week,
so that I stay motivated by visible progress.

**Acceptance Criteria:**
1. Backend calculates weekly competency snapshots:
   - Every 7 days (or weekly cron job), store snapshot of all 6 KA scores in `competency_history` table (user_id, snapshot_date, ka, competency_score)
   - Alternative: Calculate on-the-fly from `competency_tracking.last_updated` timestamps (if real-time snapshots not stored)
2. GET `/api/dashboard/trends` endpoint returns weekly progress data for last 4-8 weeks
3. Response: Array of weekly snapshots with date and 6 KA scores per week
4. Dashboard displays line chart or bar chart showing competency trends over time:
   - X-axis: Weeks (Week 1, Week 2, ...)
   - Y-axis: Competency score (0-100%)
   - Multiple lines/bars for each KA (6 lines or 6 grouped bars)
5. Chart highlights improvement: Positive deltas shown in green (e.g., "+5% this week"), negative in orange (rare, indicates need for review)
6. If user has <2 weeks of data, show message: "Complete more quiz sessions to unlock weekly progress trends"
7. Chart library: Recharts or Chart.js (as specified in Technical Assumptions)
8. Visual design: Chart card (22px radius), Inter font for labels, color scheme consistent with overall design
9. Accessibility: Chart data available in table format for screen readers (toggle view or aria-label with values)
10. Performance: Trends chart renders in <1 second (included in dashboard <2 second total)

#### Story 6.3: Exam Countdown and Readiness Indicators

As a **user preparing for a specific exam date**,
I want to see how many days I have until my exam and whether I'm on track to be ready,
so that I can adjust my study intensity if needed.

**Acceptance Criteria:**
1. Dashboard displays "Days Until Exam: X days" prominently (from onboarding `exam_date`)
2. If exam date is <30 days away: Display urgency indicator (orange/red color, "Less than 1 month!")
3. If exam date is <7 days away: Display critical urgency (red, "Exam in X days - final review!")
4. Exam readiness threshold: 75% average competency or all 6 KAs >70% (configurable)
5. Readiness status indicator:
   - **Ready:** Green checkmark, "You're exam-ready!" (all KAs >70% or average >75%)
   - **Almost Ready:** Orange icon, "Focus on [KA Names] to reach readiness" (1-2 KAs <70%)
   - **Not Ready:** Red icon, "Continue studying - X KAs below target" (3+ KAs <70%)
6. Pacing recommendations (future enhancement noted, not fully implemented in MVP):
   - If exam in 30 days and user <60% avg competency: "Consider increasing daily study time or adjusting exam date"
   - If user on track: "Great progress! Keep up daily sessions to maintain retention"
7. User can update exam date from settings (Story 8.2) if timeline changes
8. Visual design: Countdown and readiness status in hero section (main container 35px radius), clear color-coding
9. Accessibility: Color-coded status supplemented with text and icons (not color-only)
10. Unit tests: Countdown calculated correctly, readiness status accurate based on competency scores

#### Story 6.4: Knowledge Area Detail Drill-Down

As a **user wanting to understand my gaps in a specific KA**,
I want to drill down into a KA's detail view to see concept-level gaps and recent performance,
so that I can focus my studying on specific weaknesses within that KA.

**Acceptance Criteria:**
1. Dashboard KA bars are clickable (or have "View Details" button) → navigates to KA detail page
2. GET `/api/dashboard/ka/{ka_name}` endpoint returns detailed data for one KA:
   - `ka_name`, `competency_score`, `target_score`, `gap`
   - `concept_gaps`: Array of concepts within this KA with low performance (e.g., ["Stakeholder Analysis: 50%", "RACI Matrix: 60%"])
   - `recent_questions`: Last 10 questions answered in this KA with correctness (correct/incorrect)
   - `time_spent`: Total minutes spent studying this KA
   - `questions_answered`: Count of questions answered in this KA
3. KA detail view displays:
   - **Header:** KA name, current score, target, gap (primary card 22px radius)
   - **Concept Gaps:** List of weak concepts (if trackable, else generic "Review questions you missed")
   - **Recent Performance:** Visual timeline or list showing last 10 questions (green checkmark = correct, red X = incorrect)
   - **Time Spent:** "You've spent X minutes on this KA"
   - **Recommended Action:** "Focus on [specific concept]" or "Continue practicing [KA] questions"
4. Primary CTA: "Study [KA Name]" button → starts KA-focused quiz session (filter adaptive selection to this KA only)
5. Secondary CTA: "Back to Dashboard" link
6. Visual design: Detail page consistent with dashboard (Framer-inspired, Inter font, card styling)
7. Accessibility: Navigation breadcrumb (Dashboard > [KA Name]), keyboard-accessible back button
8. Unit tests: KA detail data retrieval, concept gaps calculated
9. Integration test: Clicking KA bar navigates to detail view, detail view reflects KA-specific data
10. Performance: KA detail view loads in <1 second

#### Story 6.5: Actionable Recommendations and CTAs

As a **user viewing my dashboard**,
I want clear recommendations on what to study next,
so that I don't waste time deciding and can immediately take action.

**Acceptance Criteria:**
1. Dashboard calculates actionable recommendations based on current state:
   - **If reviews due:** Primary CTA = "Start Reviews (X concepts due)" (Epic 7 integration)
   - **If no reviews due:** Primary CTA = "Continue Learning" → starts adaptive quiz session (Epic 4)
   - **If specific KA very weak (<60%):** Recommendation callout = "Priority: Focus on [KA Name] (scored X%)"
2. Recommendations section (card, 22px radius) displays:
   - **Top recommendation:** "Your next best step: [Action]"
   - **Secondary recommendations:** List of 2-3 suggested actions (e.g., "Review Strategy Analysis concepts", "Complete 10 more questions to unlock trends")
3. CTAs are pill-rounded buttons (primary color, high contrast)
4. If user completes primary recommendation (e.g., finishes reviews), dashboard updates CTA dynamically on next load
5. Recommendation logic documented: Based on reviews due > weakest KA > general quiz (priority hierarchy)
6. Visual design: Recommendations prominent but not overwhelming (balanced with competency visualizations)
7. Accessibility: CTA buttons have clear aria-labels ("Start 5 review questions now")
8. Unit tests: Recommendation logic selects appropriate CTA based on user state
9. Integration test: Dashboard shows correct CTA after completing quiz session or reviews
10. A/B testing placeholder (Phase 2): Track which recommendations drive most engagement

---

### Epic 7: Spaced Repetition & Long-Term Retention

**Epic Goal:** Implement the SM-2 spaced repetition algorithm to schedule concept reviews at optimal intervals (1, 3, 7, 14 days), ensuring users retain learned concepts through exam day. This epic delivers concept mastery tracking, review scheduling, mixed quiz sessions (reviews + new content), and reviews-due indicators on the dashboard.

#### Story 7.1: Concept Mastery Tracking for Spaced Repetition

As a **system**,
I want to track concept-level mastery state for each user,
so that spaced repetition can schedule reviews based on forgetting curve.

**Acceptance Criteria:**
1. Define concept mapping: Each question tagged with 1-3 `concept_tags` (e.g., ["stakeholder analysis", "RACI matrix"])
2. Create `concept_mastery` table: user_id, concept_tag, ka, ease_factor (default 2.5), interval_days (1/3/7/14), repetition_count, last_reviewed, next_review_due
3. After user answers question correctly for **first time**:
   - Create `concept_mastery` record for each concept_tag in that question
   - Set `interval_days = 1` (review in 1 day), `next_review_due = today + 1 day`
4. After user answers question incorrectly:
   - If concept_mastery exists: Reset `interval_days = 1`, `repetition_count = 0` (start over)
   - If concept_mastery doesn't exist: Do not create (only correct answers establish mastery)
5. SM-2 algorithm parameters: ease_factor adjusts based on performance (2.5 default, range 1.3-2.5)
6. Unit tests: Concept mastery created on first correct answer, reset on incorrect, not created on first incorrect
7. Integration test: Answering questions populates concept_mastery table correctly
8. Performance: Mastery tracking adds <50ms to answer submission (Story 4.3)
9. Concept tags reviewed: Ensure all questions have meaningful concept_tags (not generic "CBAP")
10. Algorithm documented in `/docs/algorithms.md` (SM-2 adaptation for 60-day timeline)

#### Story 7.2: SM-2 Review Scheduling

As a **system**,
I want to schedule concept reviews at increasing intervals based on SM-2 algorithm,
so that users review concepts just before they're likely to forget them.

**Acceptance Criteria:**
1. When user answers **review question correctly**:
   - Calculate new interval: `new_interval = previous_interval * ease_factor`
   - Progression: 1 day → 3 days → 7 days → 14 days (approximately, SM-2 formula may vary slightly)
   - Update `concept_mastery`: `interval_days = new_interval`, `next_review_due = today + new_interval`, increment `repetition_count`
2. When user answers **review question incorrectly**:
   - Reset to start: `interval_days = 1`, `next_review_due = today + 1`, `repetition_count = 0`
   - Optionally decrease `ease_factor` (make future intervals shorter if concept is difficult)
3. Ease factor adjustment (SM-2 quality rating simplified for MVP):
   - Correct answer: ease_factor stays same or increases slightly (+0.1, max 2.5)
   - Incorrect answer: ease_factor decreases (-0.2, min 1.3)
4. Maximum interval capped at 14 days (per Brief requirements for 60-day exam timeline)
5. Reviews due identification: Query `concept_mastery` where `next_review_due <= today`
6. Overdue prioritization: Reviews past due date prioritized over newly due reviews
7. Unit tests: Correct answer increases interval, incorrect resets interval, intervals follow ~1/3/7/14 progression
8. Integration test: Multiple review cycles produce expected interval progression
9. Performance: Review scheduling calculation <100ms (part of answer submission)
10. Monitor review accuracy: Target 70%+ correct on reviews (per Brief) - if lower, intervals may be too aggressive

#### Story 7.3: Mixed Quiz Sessions (Reviews + New Content)

As a **user with reviews due**,
I want quiz sessions to automatically mix review questions with new content,
so that I reinforce retention while continuing to learn new material.

**Acceptance Criteria:**
1. When user starts quiz session (Story 4.1), check if reviews are due:
   - Query `concept_mastery` where `next_review_due <= today` → count of concepts needing review
   - If reviews due: Create **mixed session** (40% reviews + 60% new content per Brief requirements)
   - If no reviews due: Create **new content session** (100% new questions)
2. Mixed session composition example: If user plans to answer 10 questions → 4 reviews + 6 new
3. Review question selection:
   - Select questions tagged with concepts due for review (from `concept_mastery.concept_tag`)
   - Prioritize overdue reviews (past `next_review_due` by most days)
   - If multiple questions match same concept, select one randomly
4. New question selection: Use adaptive logic from Story 4.2 (weakest KAs, difficulty matching)
5. Question order: Intermix reviews and new questions (not clustered - e.g., R, N, N, R, N, R, N, N, R, N)
6. Review questions labeled: "Review" badge or icon displayed on question card (visual distinction from new content)
7. Session type stored in `quiz_sessions` table: `session_type` = "mixed" or "new_content"
8. Unit tests: Mixed session has correct ratio (40/60), review questions selected from due concepts
9. Integration test: User with reviews due receives mixed session, user without reviews receives new content session
10. Performance: Mixed session creation in <500ms (review lookup + adaptive selection)

#### Story 7.4: Review Performance Tracking and Accuracy Metrics

As a **user completing review questions**,
I want my review accuracy tracked so I can see if I'm retaining concepts long-term,
so that I have confidence my retention is improving.

**Acceptance Criteria:**
1. After user answers **review question** (identified by "Review" label in session):
   - Update `concept_mastery` per SM-2 logic (Story 7.2)
   - Record in `quiz_responses` with `is_review = true` flag
2. Calculate review accuracy metrics:
   - **Overall Review Accuracy:** % of all review questions answered correctly (target 70%+ per Brief)
   - **Accuracy by Interval:** % correct on 1-day reviews, 3-day reviews, 7-day reviews, 14-day reviews
   - **Accuracy by KA:** % correct reviews per KA
3. GET `/api/progress/reviews` endpoint returns review metrics:
   - `overall_review_accuracy`, `accuracy_by_interval`, `accuracy_by_ka`
   - `reviews_completed_count`, `reviews_due_count`
4. Dashboard (Epic 6) displays review accuracy in a card (22px radius):
   - "Review Accuracy: X%" (color-coded: Green >70%, Orange 60-70%, Red <60%)
   - Breakdown by interval if user wants to drill down
5. If review accuracy <60%: Recommendation to slow down learning (more time per concept before advancing)
6. Unit tests: Review accuracy calculated correctly, breakdown by interval accurate
7. Integration test: Completing review questions updates accuracy metrics
8. Performance: Metrics calculation <200ms (part of dashboard load)
9. Alpha/Beta test validation: Monitor if users maintain >70% review accuracy (validates SM-2 intervals)
10. Adjustment mechanism (Phase 2): If accuracy consistently low, suggest adjusting intervals or adding extra review cycles

#### Story 7.5: Reviews Due Indicator on Dashboard

As a **user**,
I want to see how many review concepts are due on my dashboard,
so that I'm reminded to complete reviews and maintain retention.

**Acceptance Criteria:**
1. Dashboard (Story 6.1) displays "Reviews Due" count:
   - Query `concept_mastery` where `next_review_due <= today` → count
   - Display as badge or prominent metric (e.g., "5 Reviews Due")
2. Visual treatment:
   - If reviews due: Orange/yellow color (attention, not alarming), icon (refresh/repeat symbol)
   - If no reviews due: Green checkmark, "No reviews due - great job!"
3. Clicking "Reviews Due" badge → starts mixed quiz session (Story 7.3) prioritizing reviews
4. Primary CTA on dashboard adapts (Story 6.5):
   - If reviews due: "Start Reviews (X concepts)" becomes primary action
   - If no reviews: "Continue Learning" is primary
5. Reviews due count updates in real-time after completing mixed session
6. If reviews overdue (past due by >2 days): Escalate visual treatment (red color, "X overdue reviews")
7. Unit tests: Reviews due count accurate, dashboard CTA adapts correctly
8. Integration test: Completing reviews reduces reviews due count on dashboard
9. Visual design: Reviews due indicator styled as secondary card (14px radius) or inline badge
10. Email reminders (Phase 2, not MVP): Daily email if reviews due >3 and user hasn't logged in

---

### Epic 8: Polish, Testing & Launch Readiness

**Epic Goal:** Complete platform polish with user settings, profile management, accessibility compliance (WCAG 2.1 AA), comprehensive error handling, production deployment configuration, and alpha test readiness. This epic ensures the platform is stable, accessible, and ready for the Day 30 case study user launch.

#### Story 8.1: User Profile and Account Management

As a **user**,
I want to view and update my profile information and preferences,
so that I can keep my account details current and adjust my learning goals.

**Acceptance Criteria:**
1. GET `/api/user/profile` returns user profile data:
   - `email`, `created_at`, `onboarding_data` (7 questions answered), `exam_date`, `target_score`, `daily_time_commitment`
2. Settings page displays:
   - **Account section:** Email (editable), Password (change password option)
   - **Preferences section:** Exam date (date picker), Target score (70/80/90%), Daily time commitment (30-60 min / 1-2 hrs / 2+ hrs)
   - **Display Preferences:** Dark mode toggle (Light / Dark / Auto) - NEW MVP FEATURE
   - **Data & Privacy:** View privacy policy, Export my data, Delete account
3. PUT `/api/user/profile` updates editable fields (email, exam_date, target_score, daily_time_commitment)
4. Email change validation: Must be valid email, unique in database (409 Conflict if duplicate)
5. Password change: POST `/api/user/change-password` accepts `current_password`, `new_password`
   - Verify current password correct (401 if wrong)
   - Validate new password (8+ chars, letter + number)
   - Update hashed password in database
6. Exam date change: Recalculates "days until exam" on dashboard immediately
7. **Dark Mode Toggle:** Segmented control or dropdown with 3 options: Light / Dark / Auto (system preference)
   - Default: Auto mode (follows system preference via `prefers-color-scheme` media query)
   - Saved to user profile: `PUT /api/user/profile` with `theme_preference` field ('light' | 'dark' | 'auto')
   - Theme persists across devices and sessions (retrieved from user profile on login)
   - Root HTML class toggle: `<html class="light">` or `<html class="dark">`
   - 200ms color transition when toggling (prevents jarring flash)
   - **Complete dark mode specifications:** See `/docs/front-end-spec.md` Lines 2193-2227
8. Settings page styled consistent with dashboard (Framer-inspired, Inter font, form cards 22px radius, pill-rounded buttons)
9. Success messages: "Profile updated successfully", "Password changed successfully", "Theme preference updated"
10. Unit tests: Profile retrieval, profile update, password change, dark mode toggle, validation errors
11. Integration test: User can update preferences and changes persist across sessions, dark mode syncs across devices

#### Story 8.2: Data Export and Account Deletion

As a **user concerned about data privacy**,
I want to export my data and have the option to delete my account completely,
so that I maintain control over my personal information (GDPR readiness).

**Acceptance Criteria:**
1. GET `/api/user/export` endpoint generates JSON export of all user data:
   - User profile (email, created_at, onboarding_data)
   - Competency scores (all 6 KAs, historical snapshots)
   - Quiz responses (all questions answered, timestamps, correctness)
   - Reading history (chunks read, engagement data)
   - Concept mastery state (spaced repetition data)
2. Export downloaded as `learnr_data_{user_id}_{date}.json` file (client-side download trigger)
3. DELETE `/api/user/account` endpoint deletes user account and all associated data:
   - Soft delete or hard delete (hard delete for MVP to truly remove data)
   - Cascade delete: Remove from `users`, `onboarding_data`, `competency_tracking`, `quiz_responses`, `concept_mastery`, `reading_history`, etc.
   - Confirmation step: Frontend shows modal "Are you sure? This cannot be undone. Type DELETE to confirm"
4. After deletion: User logged out, JWT invalidated, redirect to landing page with message "Account deleted successfully"
5. Settings page: "Export My Data" button (downloads JSON), "Delete Account" button (opens confirmation modal)
6. Privacy policy link: Links to `/privacy` page (static page with LearnR privacy policy)
7. Terms of service link: Links to `/terms` page (static page with terms)
8. Unit tests: Data export includes all user data, account deletion removes all records
9. Integration test: Full export → delete → verify user cannot log in and data removed from database
10. Compliance: GDPR right to be forgotten satisfied (user can delete all data)

#### Story 8.3: WCAG 2.1 Level AA Accessibility Compliance

As a **user with disabilities**,
I want the platform to be fully accessible via keyboard and screen reader,
so that I can use LearnR regardless of visual or motor impairments.

**Acceptance Criteria:**
1. **Keyboard Navigation:**
   - All interactive elements (buttons, links, form inputs, cards) accessible via Tab key
   - Tab order is logical (follows visual flow: top to bottom, left to right)
   - Focus indicators visible on all focusable elements (2px outline, high contrast color)
   - Enter/Space keys activate buttons and links
   - Escape key closes modals and dropdowns
2. **Screen Reader Compatibility:**
   - Semantic HTML: Use `<button>`, `<nav>`, `<main>`, `<section>`, `<article>` appropriately
   - ARIA labels on interactive elements: `aria-label` for icon buttons, `aria-describedby` for form field hints
   - Alt text on all images/icons (or `aria-hidden="true"` for decorative elements)
   - Form labels properly associated with inputs (`<label for="email">`)
   - Screen reader announcements for dynamic content (e.g., "Correct answer" announced after quiz submission)
3. **Color Contrast:**
   - Text contrast ratio: 4.5:1 for normal text (Inter font), 3:1 for large text (18pt+)
   - Button contrast: Primary buttons have 3:1 contrast with background
   - Visual indicators not color-only: Use icons + text (e.g., green checkmark + "Correct", not just green)
4. **Text Resizing:**
   - Page remains functional when text resized to 200% (browser zoom or font size increase)
   - No horizontal scrolling required, content reflows responsively
5. **No Flashing Content:** No animations or transitions flash >3 times per second (seizure risk)
6. **Descriptive Links:** Link text is descriptive (not "click here"), e.g., "View Knowledge Area details"
7. **Accessibility Audit Tools:**
   - Run axe DevTools or WAVE on all key pages (landing, dashboard, quiz, settings)
   - Fix all Critical and Serious issues flagged
   - Document any Minor issues deferred to Phase 2
8. Manual testing: Navigate entire quiz flow using only keyboard (no mouse)
9. Screen reader testing: Use NVDA (Windows) or VoiceOver (Mac) to navigate dashboard and quiz
10. README documents accessibility commitment and how to report issues

#### Story 8.4: Error Handling and User-Friendly Messages

As a **user encountering errors**,
I want clear, helpful error messages that guide me to resolution,
so that I'm not frustrated or confused when something goes wrong.

**Acceptance Criteria:**
1. **API Error Responses:** Standardized JSON format:
   ```json
   {
     "error": "ValidationError",
     "message": "Password must be at least 8 characters with letter and number",
     "field": "password"
   }
   ```
2. **Frontend Error Display:**
   - Inline validation errors on forms (red text below field, e.g., "Email already exists")
   - Toast/snackbar notifications for global errors (e.g., "Network error, please try again")
   - Modal dialogs for critical errors (e.g., "Session expired, please log in again")
3. **Error Categories:**
   - **400 Bad Request:** Validation errors → show specific field error
   - **401 Unauthorized:** Session expired → redirect to login with message
   - **403 Forbidden:** Access denied → "You don't have permission to access this"
   - **404 Not Found:** Resource not found → "Question not found" or "Page not found"
   - **409 Conflict:** Duplicate resource → "Email already registered"
   - **500 Internal Server Error:** Server error → "Something went wrong. Please try again or contact support."
4. **Network Errors:** Offline or timeout → "Connection lost. Check your internet and try again."
5. **Retry Logic:** Transient errors (500, network timeout) automatically retry 1-2 times before showing error to user
6. **Error Logging:** All errors logged server-side with context (user_id, endpoint, request payload, stack trace) for debugging
7. **User Support Link:** All error messages include "Contact Support" link (opens email or help page)
8. **Loading States:** Spinners or skeleton screens during API calls (prevent user thinking app is frozen)
9. Unit tests: Error responses formatted correctly, frontend displays appropriate messages
10. Integration test: Simulate various errors (validation, auth, network) and verify user sees helpful messages

#### Story 8.5: Production Deployment and Environment Configuration

As a **DevOps engineer**,
I want the application deployed to production with proper environment configuration and monitoring,
so that the platform is stable and accessible for the case study user launch.

**Acceptance Criteria:**
1. **Frontend Deployment:**
   - Deploy React app to Vercel or Netlify (per Technical Assumptions)
   - Environment variables: `VITE_API_URL` (backend URL), `VITE_ENV` (production)
   - Custom domain configured (e.g., `app.learnr.com`)
   - HTTPS enforced (SSL certificate auto-provisioned)
   - Build optimized: Code splitting, minification, gzip compression
2. **Backend Deployment:**
   - Deploy FastAPI to Railway or Render (containerized deployment)
   - Environment variables: `DATABASE_URL` (PostgreSQL), `QDRANT_URL`, `OPENAI_API_KEY`, `JWT_SECRET_KEY`, `ENV=production`
   - Health check endpoint `/health` monitored by platform
   - Auto-scaling configured (start with 1 instance, scale up if load >80% CPU)
3. **Database:**
   - PostgreSQL managed service (Railway/Render Postgres or similar)
   - Daily automated backups with 7-day retention
   - Connection pooling configured (max 10 connections for MVP)
4. **Qdrant:**
   - Self-hosted Qdrant via Docker on backend server (cost $0)
   - Alternative: Migrate to Qdrant Cloud if performance issues (budget $50-100/month approved)
   - Qdrant data persisted to volume (survives container restart)
5. **CI/CD Pipeline:**
   - GitHub Actions workflow triggers on push to `main` branch
   - Run tests (unit + integration) → if pass, deploy to production
   - Deployment rollback capability (revert to previous version if issues detected)
6. **Monitoring:**
   - Error tracking: Sentry or similar integrated (capture all 500 errors, unhandled exceptions)
   - Uptime monitoring: UptimeRobot or similar pings `/health` every 5 minutes
   - Alerts: Email/Slack notification if health check fails or error rate >5%
7. **Performance:**
   - Frontend initial load <3 seconds (verified with Lighthouse)
   - Backend API response times <500ms for quiz questions, <1 second for reading content
8. README documents deployment process, environment variables, and rollback procedure
9. Smoke tests: After deployment, manually verify key flows (register, login, quiz, dashboard)
10. Case study user access: Provide login credentials, confirm user can access production app

#### Story 8.6: Alpha Test Readiness and Day 24 Go/No-Go Preparation

As a **product manager**,
I want all alpha test instrumentation and success criteria tracking in place,
so that we can make a data-driven Go/No-Go decision on Day 24.

**Acceptance Criteria:**
1. **Alpha Test Instrumentation:**
   - Reading engagement tracking (Story 5.3) fully functional
   - Reading relevance feedback (Story 5.4) fully functional
   - Explanation helpfulness feedback (Story 4.5) fully functional
   - Review accuracy tracking (Story 7.4) fully functional
2. **Success Metrics Dashboard (Internal, not user-facing):**
   - GET `/api/admin/alpha-metrics` endpoint returns:
     - Reading engagement rate (% chunks expanded vs. displayed) - target 60%+
     - Reading relevance rate (% thumbs up) - target 80%+
     - Explanation helpfulness (% thumbs up) - target 85%+
     - Review accuracy (% correct) - target 70%+
     - Daily active usage (% of days user logged in) - target 80%+
3. **Case Study User Onboarding:**
   - User account created, onboarding completed, diagnostic taken (baseline established)
   - User provided with clear instructions: "Complete daily sessions for next 30 days, exam Dec 21"
   - Feedback mechanism: User can send feedback anytime (email, in-app form, or scheduled check-ins)
4. **Day 24 Alpha Test:**
   - Schedule user interview/survey on Day 24 (November 14, 2025 if launch Nov 21)
   - Survey questions:
     - "How relevant was the BABOK reading content to your gaps?" (1-5 scale)
     - "Did the reading content help you understand concepts better?" (Yes/Somewhat/No)
     - "Would you recommend LearnR over static quiz apps?" (Yes/No, why?)
     - "Do you plan to continue using LearnR for the remaining 30 days?" (Yes/No)
   - Go criteria (from Brief):
     - ✓ User finds BABOK reading content valuable (80%+ helpful rating)
     - ✓ User commits to daily usage for remaining 30 days
     - ✓ User can articulate differentiation vs. static quiz apps
5. **No-Go Plan:**
   - If reading content not valued: Iterate UX (make more prominent, improve relevance) OR pivot strategy (focus on adaptive quiz only)
   - If user not committing to continued usage: Diagnose blockers (UX issues, time commitment, feature gaps)
6. **Alpha Test Documentation:**
   - `/docs/alpha_test_plan.md` outlines schedule, metrics, Go/No-Go criteria
   - Daily progress log: Track user engagement, issues reported, feedback collected
7. Unit tests: Admin metrics endpoint returns accurate alpha test data
8. Integration test: Full alpha test flow simulated (onboarding → diagnostic → quiz → reading → reviews)
9. Stakeholder readiness: Product team briefed on Day 24 decision process
10. Contingency time: Days 25-30 available for iteration if No-Go (adjust features, re-test)

#### Story 8.7: Admin Support Tools for Alpha Test

As a **platform administrator**,
I want to search for users, impersonate their sessions, and view their analytics in PostHog,
so that I can provide support during alpha test and debug user-reported issues.

**Acceptance Criteria:**

1. **Admin Role Management:**
   - `users` table includes `is_admin` boolean column (default: false)
   - Admin users designated via direct database flag (no self-service promotion)
   - Only users with `is_admin = true` can access admin endpoints

2. **Admin Middleware:**
   - Implement `@require_admin` decorator/middleware extending JWT auth
   - Check `is_admin` claim in decoded JWT
   - Return 403 Forbidden if user not admin
   - All `/api/admin/*` endpoints protected by this middleware

3. **User Search:**
   - GET `/api/admin/users/search?q={query}` endpoint
   - Searches across: email (partial match), user_id (exact), name (if stored)
   - Response: Array of user objects with:
     - `user_id`, `email`, `created_at`, `onboarding_completed`, `exam_date`, `last_login_at`
   - Pagination: `?limit=20&offset=0` (default 20 results)
   - Sorting: `?sort_by=created_at&order=desc`

4. **User Impersonation:**
   - POST `/api/admin/impersonate/{user_id}` endpoint
   - Validates: user_id exists, requester is admin
   - Generates new JWT with:
     - `user_id`: target user's ID (not admin's)
     - `impersonated_by`: admin's user_id
     - `exp`: 30 minutes from now (short-lived token)
   - Response: `{access_token, user_email, expires_in_seconds}`
   - Frontend stores impersonation token separately from admin token

5. **Impersonation Session UI:**
   - Frontend detects impersonation token (checks for `impersonated_by` claim)
   - Displays persistent banner at top of ALL pages:
     - Background: Orange/yellow (high visibility)
     - Text: "🔍 Viewing as user@email.com"
     - Button: "Exit Impersonation" (pill-rounded, secondary)
   - Banner not dismissible (always visible during impersonation)
   - All API calls use impersonation token (user sees their actual data)

6. **Exit Impersonation:**
   - POST `/api/admin/impersonate/exit` endpoint
   - Invalidates impersonation token
   - Frontend switches back to admin's original token
   - Redirect to admin dashboard or user search

7. **Impersonation Audit Trail:**
   - Create `admin_audit_log` table:
     - `id`, `admin_user_id`, `action_type`, `target_user_id`, `metadata` (JSONB), `timestamp`
   - Log events: "impersonation_started", "impersonation_ended"
   - Metadata includes: `duration_seconds`, `ip_address`, `user_agent`
   - GET `/api/admin/audit-log` returns recent admin actions (for compliance)

8. **PostHog Integration:**
   - PostHog SDK configured in backend and frontend
   - User events tracked with `user_id` as distinct_id (PostHog identifier)
   - Admin user search results include "View in PostHog" link:
     - URL format: `https://app.posthog.com/person/{user_id}` (or PostHog-specific URL)
     - Opens in new tab
   - Link styled as tertiary action (icon: analytics)

9. **Security Safeguards:**
   - Impersonation tokens cannot impersonate other admins (403 if target user is admin)
   - Rate limiting on impersonation: Max 10 impersonations per admin per hour
   - Email notification to user if impersonated (optional, configurable)
   - Admin cannot modify user data during impersonation (read-only mode recommended, or log all changes)

10. **Testing:**
    - Unit tests: Admin middleware blocks non-admin, allows admin
    - Unit tests: Impersonation token generation includes correct claims
    - Integration test: Admin can search user, impersonate, view dashboard as user, exit
    - Integration test: PostHog link renders correctly on user search results
    - Security test: Non-admin cannot access `/api/admin/*` endpoints

**Admin UI Specifications:**

This story defines admin functional requirements. Detailed admin UI specifications should be documented in `/docs/front-end-spec.md` including:

- **Admin User Search Screen:** Layout, search bar, results table, action buttons
- **Impersonation Banner Component:** Persistent orange banner design, exit button placement
- **Admin Dashboard:** (if separate from main dashboard) user list, metrics, audit log access
- **PostHog Link Integration:** Icon, tooltip, visual styling

**Recommended Frontend Spec Addition:**
Add "Screen 9: Admin Support Interface" section with ASCII wireframes for:
1. User search page layout
2. Impersonation banner (shown across all pages during impersonation)
3. Admin dashboard (if needed)

See Story 8.7 Acceptance Criteria above for complete functional requirements.

---
