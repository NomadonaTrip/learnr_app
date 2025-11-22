# Technical Assumptions

This section documents technical decisions that will guide the Architect. These choices are based on MVP constraints (30-day timeline, minimal budget), scalability requirements (multi-certification expansion), and alignment with project goals documented in the brief.

### Repository Structure: Monorepo

**Decision:** Use a **monorepo** structure for MVP to simplify coordination and enable shared types between frontend and backend.

**Repository Organization:**
- `/frontend` - React web application (TypeScript)
- `/backend` - FastAPI application (Python 3.11+)
- `/shared` - Shared types/interfaces (TypeScript type definitions, Pydantic models)
- `/scripts` - Content generation pipelines, embedding generation, BABOK parsing, admin utilities
- `/docs` - Architecture docs, API specs, deployment guides, decision logs

**Rationale:**
- Faster iteration during MVP (single git repo, coordinated releases)
- Shared types reduce bugs at API boundaries (TypeScript + Pydantic model sync)
- Simpler CI/CD setup (single pipeline for entire system)
- Team size (small MVP team) doesn't justify multi-repo overhead

**Alternative Considered:** Multi-repo (separate frontend and backend repositories) - Better for larger teams with independent release cycles, but adds coordination overhead unnecessary for MVP.

**Post-MVP Evolution:** Can split into multi-repo if team grows or independent release cadences needed.

### Service Architecture: Monolithic Backend

**Decision:** Build a **monolithic FastAPI backend** service containing all features for MVP, with optional microservices extraction post-validation.

**Monolithic Service Architecture:**
- Single FastAPI application handling:
  - Authentication & user management
  - Quiz engine (diagnostic, adaptive question selection, session management)
  - Competency tracking & IRT calculations
  - Reading content retrieval (vector search against Qdrant)
  - Spaced repetition scheduling
  - Progress tracking & analytics
- RESTful JSON API endpoints
- Async request handling (FastAPI async/await)
- SQLAlchemy ORM for PostgreSQL operations
- Qdrant client for vector database queries

**Rationale:**
- Faster development (no inter-service communication complexity)
- Simpler deployment (single container/process)
- Acceptable performance for MVP scale (10-100 concurrent users)
- Easier debugging and local development
- Can handle 1,000+ users before bottlenecks emerge

**When to Consider Microservices (Post-MVP):**
- Only if monolith becomes performance bottleneck (>1,000 concurrent users)
- Potential service boundaries:
  - **Auth Service:** User authentication, session management
  - **Quiz Service:** Question selection, competency tracking, adaptive algorithm
  - **Content Service:** Vector search, BABOK retrieval, question bank management
  - **Analytics Service:** Progress tracking, KPI calculation, reporting

**Current Decision:** Defer microservices until scale demands; premature optimization would slow MVP delivery.

### API Versioning Strategy: /v1/ Prefix for Future Compatibility

**Decision:** All API endpoints use `/v1/` prefix for version compatibility and future evolution (e.g., `POST /v1/quiz/answer` not `POST /api/quiz/answer`).

**API Path Format:**
- Authentication: `POST /v1/auth/login`, `POST /v1/auth/register`, `POST /v1/auth/logout`
- Quiz: `POST /v1/quiz/answer`, `GET /v1/quiz/session/{session_id}`
- Reading: `GET /v1/reading/queue`, `POST /v1/reading/queue/batch-dismiss`, `GET /v1/reading/stats`
- User: `GET /v1/user/profile`, `PUT /v1/user/profile`, `POST /v1/user/change-password`
- Content: `POST /v1/content/search`, `GET /v1/content/chunks/{chunk_id}`
- Admin: `GET /v1/admin/users/search`, `POST /v1/admin/impersonate/{user_id}`

**Rationale:**
- **Future-proofing:** Allows backward-compatible API evolution (v1 stays stable, v2 introduces breaking changes)
- **Client flexibility:** Clients can specify which version they support
- **Clear versioning contract:** Version in URL makes compatibility explicit
- **Industry standard:** REST API best practice for long-lived applications

**Version Deprecation Strategy (Post-MVP):**
- When introducing breaking changes: Launch `/v2/` endpoints alongside `/v1/`
- Support overlap period: Both versions active for 6 months
- Deprecation notice: Return `X-API-Deprecated: v1 will sunset on YYYY-MM-DD` header
- Final cutover: Disable v1 endpoints after transition period

**Current Version:** v1 (MVP launch)

**Note:** All API endpoint references in this PRD use `/v1/` prefix. Supporting documentation may use `/api/` as shorthand, but implementation must use versioned paths.

### Testing Requirements: Unit + Integration Testing for Business-Critical Code

**Decision:** Implement **Unit + Integration testing** focused on business-critical code paths, with manual E2E testing for MVP.

**Testing Pyramid for MVP:**

**1. Unit Tests (Foundation):**
- **Backend Business Logic:**
  - Competency estimation (IRT algorithm) - CRITICAL
  - Adaptive question selection logic - CRITICAL
  - Spaced repetition scheduling (SM-2 algorithm) - CRITICAL
  - User data validation (Pydantic models)
  - Content retrieval ranking logic
- **Frontend Components (Selective):**
  - Critical user flows (question answering, explanation display)
  - Data visualization components (competency bars, progress charts)
- **Coverage Target:** >70% for business-critical modules
- **Tool:** pytest (backend), Jest/React Testing Library (frontend)

**2. Integration Tests (API Level):**
- **Backend API Endpoints:**
  - POST /diagnostic - Diagnostic submission + competency calculation
  - POST /quiz/session - Start adaptive quiz session
  - POST /quiz/answer - Submit answer + update competency + retrieve reading
  - GET /progress - Dashboard data retrieval
  - POST /auth/login - Authentication flow
- **Database Integrations:**
  - PostgreSQL read/write operations (user data, responses, competency tracking)
  - Qdrant vector search (question retrieval, reading chunk retrieval)
- **Coverage Target:** All critical API endpoints tested
- **Tool:** pytest with test database, Qdrant test collection

**3. End-to-End Tests (Manual for MVP):**
- **Critical User Journeys (Manual Testing):**
  - Onboarding → Diagnostic → Results → Dashboard (first-time user flow)
  - Quiz session → Answer → Explanation → Reading → Next question (learning loop)
  - Spaced repetition: Review due → Mixed session → Review accuracy tracking
  - Settings: Update exam date, password reset, account deletion
- **Why Manual for MVP:** E2E automation (Playwright, Cypress) takes time; manual testing acceptable for 30-day sprint
- **Post-MVP:** Automate E2E tests for regression prevention during beta

**Testing Philosophy:**
- **Test behavior, not implementation** (black-box approach where possible)
- **Focus on business value** (competency accuracy > UI styling)
- **Fast feedback loops** (unit tests run in <5 seconds for rapid iteration)
- **CI Integration** (tests run on every commit; block merge if critical tests fail)

**Explicit Non-Testing for MVP:**
- Performance/load testing (defer until beta scale)
- Security penetration testing (basic security practices enforced, formal testing post-MVP)
- Accessibility automated testing (manual WCAG compliance verification, automated tools in Phase 2)

### Additional Technical Assumptions and Requests

Throughout the PRD development and brief analysis, these additional technical assumptions have been identified as critical for the Architect:

**1. Data Model Assumptions:**
- **Competency Tracking:** Per-user, per-KA competency scores stored with timestamp history (enables weekly progress trends)
- **Spaced Repetition State:** Per-user, per-concept tracking (last_seen, next_review_date, ease_factor, interval, repetition_count)
- **Response History:** All user answers persisted with metadata (question_id, answer_selected, correctness, time_taken, timestamp, session_id)
- **Session Management:** Quiz sessions track start/end times, questions answered, paused state (enable resume capability)

**2. API Design Assumptions:**
- **RESTful conventions:** Standard HTTP methods (GET, POST, PUT, DELETE), status codes (200, 201, 400, 401, 404, 500)
- **JSON request/response:** All API communication uses JSON (no XML, form-encoded)
- **Stateless API:** JWT tokens carry authentication; no server-side session state (enables horizontal scaling)
- **Pagination:** Not needed for MVP (small data sets per user), defer to Phase 2 if needed

**3. Frontend State Management:**
- **Decision Deferred to Architect:** React Context API vs. Redux Toolkit
- **Recommendation:** Context API sufficient for MVP (simpler, less boilerplate)
- **When Redux Needed:** If state management becomes unwieldy or performance issues arise (complex cross-component state)

**4. Deployment & Infrastructure:**
- **MVP Hosting:**
  - Frontend: Vercel or Netlify (free tier, CDN included, simple deployment)
  - Backend: Railway or Render (container deployment, ~$20/month)
  - PostgreSQL: Managed service from Railway/Render ($10-15/month)
  - Qdrant: Self-hosted via Docker on backend server (cost $0)
- **CI/CD:** GitHub Actions (free for public repos, included in GitHub plan)
- **Environment Variables:** Secure storage for API keys (OpenAI, database URLs, JWT secrets)

**5. Content Processing Pipeline:**
- **BABOK Parsing:** PyMuPDF or pdfplumber for PDF text extraction
- **Chunking Strategy:** Hybrid structural + semantic chunking (200-500 tokens, respect section boundaries)
- **Embedding Generation:** Batch process (all questions + chunks upfront, minimal ongoing costs)
- **Question Generation:** GPT-4 for quality baseline, Llama 3.1 for volume variations (cost optimization)

**6. Security & Privacy:**
- **Password Hashing:** bcrypt or Argon2 (industry standard, salted hashes)
- **JWT Expiration:** 7-day token expiration, refresh token strategy for longer sessions
- **HTTPS Only:** All production traffic over TLS (no HTTP endpoints)
- **Input Validation:** Pydantic models validate all API inputs (prevent injection attacks)
- **Rate Limiting:** Implement on auth endpoints (prevent brute force), defer for other endpoints until abuse detected

**7. Performance Assumptions:**
- **Response Time Targets:**
  - Question display: <500ms after answer submission
  - Reading content retrieval: <1 second (vector search + PostgreSQL join)
  - Dashboard rendering: <2 seconds (aggregate all 6 KA scores + trends)
- **Database Queries:** Indexed on user_id, question_id, session_id for fast lookups
- **Caching:** Not implemented in MVP (premature optimization), consider Redis post-MVP if needed

**8. Monitoring & Observability (Minimal for MVP):**
- **Error Tracking:** Sentry or similar for backend exceptions
- **Logging:** Structured JSON logs (timestamp, user_id, endpoint, error details)
- **Analytics:** Minimal (user count, session count), no invasive tracking
- **Post-MVP:** Add performance monitoring (response times), user analytics (Plausible or similar)

**9. Known Technical Debt Accepted for MVP:**
- Simplified IRT (not full 3-parameter IRT with item calibration)
- Manual E2E testing (no automation)

### Supporting Technical Documentation (REQUIRED READING)

**CRITICAL:** This PRD is supported by detailed technical specifications that provide implementation-level guidance. Architects, UX designers, and developers MUST review these documents alongside the PRD for complete understanding:

**v2.1 Feature Specifications:**
- **`docs/Implementation_Summary.md`** (964 lines) - Master implementation guide for Post-Session Review and Asynchronous Reading Library features
- **`docs/Asynchronous_Reading_Model.md`** (1,050 lines) - Complete technical architecture for the reading queue system, including data models, API contracts, and UX specifications
- **`docs/Learning_Loop_Refinement.md`** (1,488 lines) - Detailed specification of the post-session review feature with flowcharts and phase-by-phase implementation guidance

**UX/UI Specifications:**
- **`docs/front-end-spec.md`** (1,801 lines) - Complete UI/UX specification including information architecture, design system, component specs, and accessibility requirements
- **`docs/user-flows.md`** (747 lines) - Detailed user flow diagrams (Mermaid format) covering onboarding, learning loops, review flows, and reading library interactions

**Cross-Reference Notes:**
- Epic 4 Stories 4.6-4.9 (Post-Session Review) → See `Learning_Loop_Refinement.md` Phase 2 specification
- Epic 5 Stories 5.5-5.9 (Async Reading Library) → See `Asynchronous_Reading_Model.md` for complete architecture
- All UI implementation → Reference `front-end-spec.md` for design system tokens, component specifications, and accessibility requirements
- All user flows → See `user-flows.md` Flows 4, 4b, and 9 for detailed interaction diagrams

---
