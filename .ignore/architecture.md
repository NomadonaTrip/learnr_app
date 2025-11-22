# LearnR Fullstack Architecture Document

**Author:** Winston (Architect Agent)
**Date:** November 21, 2025
**Version:** 1.0

---

## Introduction

This document outlines the complete fullstack architecture for **LearnR**, including backend systems, frontend implementation, and their integration. It serves as the single source of truth for AI-driven development, ensuring consistency across the entire technology stack.

This unified approach combines what would traditionally be separate backend and frontend architecture documents, streamlining the development process for modern fullstack applications where these concerns are increasingly intertwined.

**LearnR** is an AI-powered adaptive learning platform that transforms professional certification exam preparation from passive memorization to active, adaptive mastery. The platform targets working professionals (ages 30-45) preparing for CBAP certification through:

- **Adaptive Learning Engine:** Real-time competency tracking using simplified IRT across 6 knowledge areas
- **Complete Learning Loop:** Diagnostic → Adaptive Quiz → Explanations → Post-Session Review → Asynchronous Reading Library → Spaced Repetition
- **AI-Powered Content:** GPT-4 + Llama 3.1 for content generation, semantic search via Qdrant vector database
- **Data-Driven Personalization:** 7-question onboarding, 12-question diagnostic, continuous competency estimation
- **Key Innovation:** "Test Fast, Read Later" - zero-interruption quiz flow with asynchronous BABOK reading recommendations

**Target Outcome:** 80%+ first-time pass rate (vs 60% industry average) with 30% reduction in study time through intelligent content targeting.

**MVP Timeline:** 30-day development → 30-day case study validation (exam Dec 21, 2025) → Go/No-Go decision → Beta launch Q1 2026.

---

### Starter Template or Existing Project

**N/A - Greenfield project**

This is a pure greenfield architecture with no existing starter template or codebase. The PRD specifies a custom technical stack (React + FastAPI + PostgreSQL + Qdrant) with no mentions of starter templates or existing frameworks.

**Decision:** Custom greenfield setup provides complete control and aligns perfectly with the PRD's specified technology stack and 30-day MVP timeline.

---

### Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-11-21 | 1.0 | Initial fullstack architecture document created | Winston (Architect Agent) |

---

## High Level Architecture

### Technical Summary

LearnR employs a **modern three-tier architecture** with clear separation between presentation (React SPA), business logic (FastAPI REST API), and data persistence (PostgreSQL + Qdrant). The system is designed as a **monolithic backend with microservice-ready boundaries**, allowing future decomposition if needed.

The architecture centers on an **adaptive learning engine** that continuously updates user competency models based on quiz responses, then uses these models to intelligently select questions and reading materials. A **dual-database strategy** leverages PostgreSQL for transactional data (users, responses, sessions) and Qdrant for semantic search (question retrieval, BABOK content matching).

**Frontend** (React SPA) handles all UI/UX concerns including dark mode, responsive design, and real-time progress visualization, communicating exclusively via RESTful API. **Backend** (FastAPI) orchestrates all business logic: adaptive question selection (simplified IRT), competency tracking, spaced repetition scheduling (SM-2), semantic search, and asynchronous reading queue management.

The platform is **cloud-native** with containerized deployment (Docker), designed for initial deployment on cost-effective platforms (Vercel frontend + Railway/Render backend) with clear migration path to AWS/GCP for scale. **PostHog** provides product analytics and session replay for MVP validation.

This architecture achieves PRD goals by: (1) enabling rapid 30-day MVP development through proven tech stack, (2) supporting real-time adaptive learning via efficient competency calculations, (3) providing foundation for multi-certification expansion through modular design, (4) ensuring 80%+ exam pass rates through intelligent content targeting backed by semantic search.

---

### Platform and Infrastructure Choice

**Platform:** Vercel (frontend) + Railway (backend) + Supabase (PostgreSQL) + Qdrant Cloud

**Key Services:**
- Vercel (React SPA hosting with edge CDN)
- Railway (FastAPI backend container with auto-scaling)
- Supabase PostgreSQL (relational data with pgvector fallback option)
- Qdrant Cloud (vector search for questions + reading content)
- PostHog Cloud (analytics, session replay, feature flags)
- GitHub Actions (CI/CD pipeline)

**Deployment Host and Regions:**
- Frontend: Vercel Edge Network (global CDN, primary US)
- Backend: Railway US-West region (low latency to Qdrant Cloud)
- Database: Supabase US-East (PostgreSQL primary + Qdrant Cloud US region)

**Rationale:** Cost-optimized MVP stack ($0-50/month) enables rapid validation with clear migration path to AWS/GCP if business metrics justify investment post-beta.

---

### Repository Structure

**Structure:** Monorepo (single repository, multiple packages)

**Monorepo Tool:** npm workspaces (lightweight, native to Node.js ecosystem)

**Package Organization:**

```
learnr/
├── apps/
│   ├── web/              # React SPA (frontend)
│   └── api/              # FastAPI backend
├── packages/
│   ├── shared-types/     # TypeScript interfaces shared between frontend/backend
│   └── config/           # Shared ESLint, Prettier, TypeScript configs
├── infrastructure/       # Docker, deployment configs, IaC (future)
└── docs/                 # PRD, architecture, API docs
```

---

### High Level Architecture Diagram

```mermaid
graph TB
    subgraph "User Devices"
        Browser[Web Browser - Desktop/Mobile]
    end

    subgraph "Frontend - Vercel Edge"
        SPA[React SPA<br/>- Quiz UI<br/>- Dashboard<br/>- Reading Library<br/>- Dark Mode]
    end

    subgraph "Backend - Railway"
        API[FastAPI REST API<br/>- Authentication<br/>- Adaptive Engine<br/>- Spaced Repetition<br/>- Reading Queue Mgmt]
    end

    subgraph "Data Layer"
        PG[(PostgreSQL - Supabase<br/>Users, Responses,<br/>Sessions, Progress)]
        Qdrant[(Qdrant Vector DB<br/>Questions, Reading Content<br/>Semantic Search)]
    end

    subgraph "External Services"
        OpenAI[OpenAI API<br/>GPT-4 Content Gen<br/>Embeddings]
        PostHog[PostHog Analytics<br/>Events, Session Replay]
    end

    Browser --> SPA
    SPA --> API
    API --> PG
    API --> Qdrant
    API --> OpenAI
    SPA --> PostHog
    API --> PostHog

    style SPA fill:#0066CC,color:#fff
    style API fill:#10B981,color:#fff
    style PG fill:#F59E0B,color:#fff
    style Qdrant fill:#EF4444,color:#fff
```

---

### Architectural Patterns

- **Single Page Application (SPA):** React SPA with client-side routing - *Rationale:* Fast, app-like UX for quiz sessions; no page reloads during learning flow

- **RESTful API Gateway:** FastAPI as single entry point for all backend operations - *Rationale:* Clear API contract, enables future mobile apps, centralizes auth/logging

- **Repository Pattern (Backend):** Abstract data access layer for PostgreSQL and Qdrant - *Rationale:* Enables testing with mock repositories, future database migration flexibility

- **Component-Based UI (Frontend):** Reusable React components with TypeScript - *Rationale:* Maintainability, type safety, design system consistency (22px/14px border radius hierarchy)

- **Service Layer Pattern (Backend):** Business logic separated from API routes (e.g., AdaptiveEngine, SpacedRepetition services) - *Rationale:* Testability, reusability, clear separation of concerns

- **Event-Driven Background Jobs:** Asynchronous reading queue population via task queue (Celery or FastAPI BackgroundTasks) - *Rationale:* Zero-interruption quiz flow, offload semantic search to background

- **Adapter Pattern (AI Services):** Abstraction layer for OpenAI API (LLMService) - *Rationale:* Enables switching between GPT-4 and Llama 3.1, rate limiting, cost tracking

- **State Management with Context + Hooks (Frontend):** React Context for global state (auth, competency) + local state for UI - *Rationale:* Lightweight for MVP, avoids Redux complexity, sufficient for medium-scale SPA

- **JWT Authentication with Refresh Tokens:** Stateless auth with 7-day expiration - *Rationale:* Scalable, works across devices, secure session management

- **Semantic Search Pattern:** Qdrant for approximate nearest neighbor (ANN) search on question/reading embeddings - *Rationale:* Enables "find similar questions" and "match reading to gaps" features critical to adaptive learning

---

## Tech Stack

**⚠️ CRITICAL: This is the DEFINITIVE technology selection for LearnR. All development MUST use these exact versions.**

### Technology Stack Table

| Category | Technology | Version | Purpose | Rationale |
|----------|-----------|---------|---------|-----------|
| **Frontend Language** | TypeScript | 5.3.x | Type-safe frontend development | Prevents runtime errors, enables IntelliSense, enforces API contracts with backend |
| **Frontend Framework** | React | 18.2.x | UI component framework | Industry standard SPA framework, excellent TypeScript support, massive ecosystem |
| **UI Component Library** | Tailwind CSS + Headless UI | Tailwind 3.4.x, Headless UI 1.7.x | Utility-first styling + accessible components | Rapid UI development, design system consistency (22px/14px radius), WCAG AA accessible |
| **State Management** | React Context + Zustand | Zustand 4.5.x | Global state (auth, competency) + local state | Lightweight vs Redux, sufficient for medium SPA, TypeScript-first API |
| **Backend Language** | Python | 3.11.x | Backend API development | AI/ML ecosystem (OpenAI SDK, NumPy for IRT), async support, PRD requirement |
| **Backend Framework** | FastAPI | 0.109.x | RESTful API server | Automatic OpenAPI docs, async/await, type hints (Pydantic), high performance |
| **API Style** | REST | OpenAPI 3.0 | Frontend-backend communication | Standard HTTP verbs, cacheable, automatic docs via FastAPI, simpler than GraphQL for MVP |
| **Database** | PostgreSQL | 15.x | Relational data (users, responses, sessions) | ACID compliance, JSON support, proven reliability, Supabase managed option |
| **Cache** | Redis | 7.2.x | Session cache, rate limiting, background job queue | In-memory performance for JWT blacklist, API rate limits, Celery broker |
| **File Storage** | AWS S3 | N/A (API v3) | BABOK PDFs, user data exports, backups | Industry standard, 99.99% durability, CDN integration, cost-effective |
| **Authentication** | JWT + bcrypt | PyJWT 2.8.x, bcrypt 4.1.x | Stateless auth with secure password hashing | Scalable across instances, 7-day expiration per PRD, industry-standard security |
| **Frontend Testing** | Vitest + React Testing Library | Vitest 1.2.x, RTL 14.x | Component unit tests, integration tests | Faster than Jest, native ESM support, excellent React integration |
| **Backend Testing** | pytest + httpx | pytest 7.4.x, httpx 0.26.x | API tests, unit tests, integration tests | Python standard, async test support for FastAPI, fixtures for test data |
| **E2E Testing** | Playwright | 1.41.x | Full user journey tests (onboarding → quiz → review) | Cross-browser, automatic waiting, screenshot/video on fail, better than Cypress for modern apps |
| **Build Tool** | Vite | 5.0.x | Frontend bundler and dev server | 10x faster than Webpack, native ESM, optimized for React + TypeScript |
| **Bundler** | esbuild (via Vite) | 0.19.x (bundled) | JavaScript/TypeScript compilation | Fastest bundler (Go-based), used internally by Vite |
| **IaC Tool** | Docker + Docker Compose | Docker 24.x, Compose 2.x | Local dev environment, containerized deployment | Platform-agnostic, Railway/AWS ECS compatible, reproducible environments |
| **CI/CD** | GitHub Actions | N/A | Automated testing, deployment | Native GitHub integration, free for public repos, Docker build support |
| **Monitoring** | Sentry | Latest SDK | Error tracking, performance monitoring | Real-time error alerts, stack traces, release tracking, 5k events/month free |
| **Logging** | Structlog + CloudWatch | structlog 24.x | Structured JSON logs for debugging | Machine-readable logs, context propagation, CloudWatch integration for production |
| **CSS Framework** | Tailwind CSS | 3.4.x | Utility-first styling system | Design system consistency, dark mode support, purges unused CSS (small bundles) |
| **Vector Database** | Qdrant | 1.7.x | Semantic search (questions, reading content) | Purpose-built vector DB, 10x faster than pgvector, HNSW indexing, filtering support |
| **AI/ML - LLM** | OpenAI GPT-4 + Llama 3.1 | gpt-4-turbo-preview (API), Llama 3.1-70B (local) | Content generation, explanation refinement | GPT-4 for quality, Llama 3.1 for cost-effective variations |
| **AI/ML - Embeddings** | OpenAI text-embedding-3-large | text-embedding-3-large (3072-dim) | Semantic search embeddings for questions/reading | State-of-the-art retrieval quality, 3072 dimensions for nuanced matching |
| **Analytics** | PostHog | Latest SDK (3.x) | Product analytics, session replay, feature flags | Self-hosted option, privacy-friendly, MVP validation metrics tracking |
| **ORM/Query Builder** | SQLAlchemy + Alembic | SQLAlchemy 2.0.x, Alembic 1.13.x | Database ORM and migrations | Python standard, async support, type-safe queries, automatic migration generation |
| **API Documentation** | FastAPI auto-docs + Redoc | Built-in | Interactive API documentation | Auto-generated from Pydantic models, live testing, always in sync with code |
| **Frontend Router** | React Router | 6.21.x | Client-side routing | Industry standard, nested routes, protected routes, TypeScript support |
| **Form Validation** | React Hook Form + Zod | RHF 7.49.x, Zod 3.22.x | Type-safe form handling | Performance (uncontrolled inputs), TypeScript schemas shared with backend |
| **HTTP Client (Frontend)** | Axios | 1.6.x | API communication with interceptors | Request/response interceptors for auth, error handling, request cancellation |
| **Background Jobs** | Celery + Redis | Celery 5.3.x | Asynchronous reading queue population | Reliable task queue for semantic search (offload from request cycle), Redis broker |
| **Code Quality** | ESLint + Prettier + Ruff | ESLint 8.x, Prettier 3.x, Ruff 0.1.x | Linting and formatting | ESLint+Prettier (frontend), Ruff (Python - 10x faster than Pylint) |
| **Package Manager** | npm | 10.x | JavaScript dependency management | Standard for Node.js, workspaces support for monorepo |

---

## Data Models

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

## API Specification

### REST API Specification

The LearnR API follows RESTful conventions with JSON payloads. All endpoints require JWT authentication except `/auth/*` routes.

**Base URL:** `https://api.learnr.com/v1` (production) | `http://localhost:8000/v1` (development)

**Authentication:** Bearer token in `Authorization` header: `Authorization: Bearer <jwt_token>`

**Error Format:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid email format",
    "details": { "field": "email" },
    "timestamp": "2025-11-21T10:30:00Z",
    "request_id": "req_abc123"
  }
}
```

**Key Endpoints:**

- `POST /auth/register` - Register new user account
- `POST /auth/login` - Authenticate user
- `POST /auth/refresh` - Refresh access token
- `GET /users/me` - Get current user profile
- `PUT /users/me` - Update user profile
- `POST /diagnostic/start` - Start diagnostic assessment
- `GET /diagnostic/{session_id}/questions` - Get next diagnostic question
- `POST /diagnostic/{session_id}/submit` - Submit diagnostic answer
- `GET /diagnostic/{session_id}/results` - Get diagnostic results
- `POST /sessions` - Start new quiz session
- `GET /sessions/{session_id}` - Get session details
- `POST /sessions/{session_id}/end` - End session
- `GET /questions/next` - Get next adaptive question
- `POST /questions/{question_id}/answer` - Submit answer to question
- `GET /competency` - Get all competency scores
- `GET /reading-queue` - Get reading queue
- `GET /reading-queue/{item_id}` - Get reading item details
- `PUT /reading-queue/{item_id}` - Update reading item
- `GET /reviews/due` - Get reviews due count
- `POST /sessions/{id}/review/start` - Start post-session review
- `POST /sessions/{id}/review/answer` - Submit review answer
- `GET /analytics/dashboard` - Get dashboard data

### Admin API Endpoints

**Authentication:** All admin endpoints require `is_admin: true` flag in JWT token. Protected by `@require_admin` middleware (extends `@require_auth`).

**Rate Limiting:** Admin endpoints have dedicated rate limits:
- User search: 100 requests/hour per admin
- Impersonation: 10 requests/hour per admin (security-sensitive)
- General admin operations: 500 requests/hour per admin

**Endpoints:**

#### User Management

- `GET /admin/users/search?q={query}` - Search users by email, user_id, or name
  - **Query Parameters:**
    - `q` (string, required): Search query (minimum 3 characters)
    - `limit` (integer, optional): Results limit (default: 20, max: 100)
    - `offset` (integer, optional): Pagination offset (default: 0)
  - **Response:**
    ```json
    {
      "total": 42,
      "results": [
        {
          "user_id": "uuid",
          "email": "user@example.com",
          "created_at": "2025-11-20T10:30:00Z",
          "onboarding_completed": true,
          "exam_date": "2025-12-21",
          "last_login": "2025-11-21T08:15:00Z",
          "exam_readiness": 73
        }
      ]
    }
    ```
  - **Error Codes:** 400 (query too short), 403 (not admin), 429 (rate limit)

- `GET /admin/users/{user_id}` - Get detailed user profile (admin view)
  - **Response:** Full user object + analytics summary + PostHog deep link
    ```json
    {
      "user": { /* Full User object */ },
      "analytics": {
        "total_sessions": 24,
        "total_questions_answered": 312,
        "avg_session_duration_minutes": 18,
        "competency_progression": [ /* 7-day history */ ]
      },
      "posthog_url": "https://app.posthog.com/person/{user_id}"
    }
    ```

#### Impersonation

- `POST /admin/impersonate/{user_id}` - Impersonate user (generates special JWT)
  - **Request Body:** None
  - **Response:**
    ```json
    {
      "impersonation_token": "jwt_token_here",
      "user": { /* User object being impersonated */ },
      "expires_at": "2025-11-21T11:00:00Z",
      "impersonated_by": "admin_user_id"
    }
    ```
  - **Token Claims:**
    ```json
    {
      "sub": "impersonated_user_id",
      "impersonated_by": "admin_user_id",
      "is_impersonation": true,
      "exp": 1732186800  // 30 minutes from issue
    }
    ```
  - **Restrictions:**
    - Cannot impersonate other admins (403 error)
    - Token expires in 30 minutes (non-refreshable)
    - Only one active impersonation session per admin at a time
    - All actions logged to `admin_audit_log` table
  - **Error Codes:** 403 (target is admin / permission denied), 404 (user not found), 429 (rate limit)

- `POST /admin/exit-impersonation` - Exit impersonation session (returns to admin session)
  - **Request:** Must provide impersonation token
  - **Response:**
    ```json
    {
      "message": "Impersonation ended",
      "admin_token": "original_admin_jwt",
      "duration_seconds": 1245
    }
    ```
  - **Side Effect:** Audit log updated with session duration

#### Audit Log

- `GET /admin/audit-log` - Get admin action audit trail
  - **Query Parameters:**
    - `admin_id` (uuid, optional): Filter by admin user
    - `action_type` (string, optional): Filter by action (e.g., "impersonate", "user_search")
    - `start_date` (ISO 8601, optional): Filter from date
    - `end_date` (ISO 8601, optional): Filter to date
    - `limit` (integer, optional): Results limit (default: 50, max: 500)
  - **Response:**
    ```json
    {
      "total": 128,
      "logs": [
        {
          "id": "uuid",
          "admin_id": "admin_uuid",
          "admin_email": "admin@learnr.com",
          "action_type": "impersonate",
          "target_user_id": "user_uuid",
          "target_email": "user@example.com",
          "timestamp": "2025-11-21T10:00:00Z",
          "duration_seconds": 1245,
          "ip_address": "192.168.1.1",
          "user_agent": "Mozilla/5.0..."
        }
      ]
    }
    ```

#### Content Management

- `POST /admin/questions/flag` - Flag question for review
- `PUT /admin/questions/{question_id}` - Update question (admin edit)
- `DELETE /admin/questions/{question_id}` - Delete question (soft delete)
- `POST /admin/reading-chunks/update` - Update BABOK chunk content

**PostHog Integration:**

All admin user detail views (`GET /admin/users/{user_id}`) return a `posthog_url` field with deep link to PostHog user profile:
```
https://app.posthog.com/person/{user_id}
```

Frontend should render this as a clickable link: **"View in PostHog →"**

**Security Features:**

1. **Admin Flag Protection:** `is_admin` flag can only be set via direct database update (no API endpoint for promotion)
2. **Impersonation Banner:** Frontend must show persistent banner when in impersonation mode:
   ```
   ⚠️ Viewing as user@example.com | Exit Impersonation
   ```
3. **Audit Trail:** All admin actions automatically logged with IP, timestamp, user agent
4. **Rate Limiting:** Aggressive rate limits on sensitive operations (impersonation: 10/hour)
5. **Session Isolation:** Impersonation tokens cannot be refreshed; 30-minute hard limit

**Full OpenAPI 3.0 specification available at `/docs` (Swagger UI) and `/redoc` (ReDoc) when API is running.**

---

## Components

### Frontend Components

1. **Authentication Module** - User auth state, login/logout, JWT refresh, protected routes
2. **Quiz Session Manager** - Session lifecycle, question navigation, answer submission
3. **Reading Library Manager** - Async reading queue, filters, engagement tracking
4. **Dashboard & Analytics Viewer** - Progress visualization, competency bars, trends
5. **Competency Visualizer** - Chart rendering, progress animations
6. **Reading Badge Component** - Navigation badge with unread count and priority indicator

### Reading Badge UI Pattern

**Purpose:** Display unread reading queue count in navigation with silent updates (zero-interruption learning flow).

**Component Location:** `apps/web/src/components/layout/Navigation.tsx` or `ReadingBadge.tsx`

**Visual Design:**

```
┌─────────────────────────────┐
│  Navigation                  │
│  [Dashboard] [Quiz] [Reading│ 7] [Settings]
│                         └─┬─┘
│                   Badge: count + priority
└─────────────────────────────┘
```

**Badge States:**

| State | Count | Priority | Visual | Example |
|-------|-------|----------|--------|---------|
| **Empty** | 0 | N/A | No badge shown | `Reading Library` |
| **Low/Medium** | 1-10 | None high | Blue badge, white text | `Reading Library [3]` |
| **High Priority** | 1-10 | ≥1 high | Red/orange badge, white text | `Reading Library [7]` |
| **Many Items** | 10+ | Any | Badge with "10+" | `Reading Library [10+]` |

**TypeScript Interface:**

```typescript
interface ReadingBadgeProps {
  count: number;
  hasHighPriority: boolean;
  className?: string;
}

interface ReadingBadgeState {
  count: number;
  hasHighPriority: boolean;
  previousCount: number; // For animation
}
```

**Implementation Example:**

```tsx
// apps/web/src/components/layout/ReadingBadge.tsx
import { useReadingQueue } from '@/hooks/useReadingQueue';
import { useEffect, useState } from 'react';

export function ReadingBadge() {
  const { unreadCount, hasHighPriority } = useReadingQueue();
  const [shouldPulse, setShouldPulse] = useState(false);

  // Pulse animation when count increases (silent notification)
  useEffect(() => {
    if (unreadCount > 0) {
      setShouldPulse(true);
      const timer = setTimeout(() => setShouldPulse(false), 1000);
      return () => clearTimeout(timer);
    }
  }, [unreadCount]);

  if (unreadCount === 0) return null;

  const displayCount = unreadCount > 10 ? '10+' : unreadCount.toString();
  const badgeColor = hasHighPriority
    ? 'bg-error-500 text-white' // High priority: red/orange
    : 'bg-primary-500 text-white'; // Normal: blue

  return (
    <span
      className={`
        inline-flex items-center justify-center
        min-w-[24px] h-[24px] px-2
        text-xs font-semibold
        rounded-full
        ${badgeColor}
        ${shouldPulse ? 'animate-pulse-subtle' : ''}
        transition-all duration-200
      `}
      aria-label={`${unreadCount} unread reading items${hasHighPriority ? ', including high priority' : ''}`}
      role="status"
    >
      {displayCount}
    </span>
  );
}
```

**Navigation Integration:**

```tsx
// apps/web/src/components/layout/Navigation.tsx
import { ReadingBadge } from './ReadingBadge';

export function Navigation() {
  return (
    <nav className="navigation">
      <NavLink to="/dashboard">Dashboard</NavLink>
      <NavLink to="/quiz">Quiz</NavLink>
      <NavLink to="/reading" className="flex items-center gap-2">
        Reading Library
        <ReadingBadge />
      </NavLink>
      <NavLink to="/settings">Settings</NavLink>
    </nav>
  );
}
```

**State Management (Zustand Store):**

```typescript
// apps/web/src/stores/readingStore.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface ReadingState {
  unreadCount: number;
  hasHighPriority: boolean;
  updateBadge: (count: number, hasHigh: boolean) => void;
}

export const useReadingStore = create<ReadingState>()(
  persist(
    (set) => ({
      unreadCount: 0,
      hasHighPriority: false,
      updateBadge: (count, hasHigh) => set({ unreadCount: count, hasHighPriority: hasHigh }),
    }),
    {
      name: 'reading-badge-storage',
    }
  )
);
```

**Silent Badge Updates (Background Service):**

```typescript
// apps/web/src/services/readingQueueService.ts
import { useReadingStore } from '@/stores/readingStore';

export async function syncReadingBadge() {
  // Called after answer submission (background)
  const response = await fetch('/api/v1/reading-queue/summary');
  const data = await response.json();

  // Update badge silently (no toast, no modal, no interruption)
  useReadingStore.getState().updateBadge(
    data.unread_count,
    data.has_high_priority
  );
}

// Hook into answer submission workflow
export async function submitAnswer(questionId: string, answer: string) {
  const response = await fetch(`/api/v1/questions/${questionId}/answer`, {
    method: 'POST',
    body: JSON.stringify({ answer }),
  });

  // Background sync (non-blocking)
  syncReadingBadge();

  return response.json();
}
```

**API Endpoint for Badge Data:**

```
GET /api/v1/reading-queue/summary
```

**Response:**
```json
{
  "unread_count": 7,
  "has_high_priority": true,
  "priority_breakdown": {
    "high": 2,
    "medium": 3,
    "low": 2
  }
}
```

**Accessibility:**

- Badge has `aria-label` with full description
- `role="status"` announces updates to screen readers
- Color is supplemental; count is primary indicator (colorblind-friendly)
- High priority communicated via text in `aria-label`, not just color

**Animation (Tailwind Config):**

```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      keyframes: {
        'pulse-subtle': {
          '0%, 100%': { transform: 'scale(1)', opacity: '1' },
          '50%': { transform: 'scale(1.1)', opacity: '0.9' },
        },
      },
      animation: {
        'pulse-subtle': 'pulse-subtle 1s ease-in-out',
      },
    },
  },
};
```

**Dashboard Widget (Optional):**

Display top 3 high-priority reading items on dashboard:

```tsx
// apps/web/src/components/dashboard/ReadingWidget.tsx
export function ReadingWidget() {
  const { topPriorityItems } = useReadingQueue();

  if (topPriorityItems.length === 0) return null;

  return (
    <div className="reading-widget card">
      <h3>Recommended Reading</h3>
      <ul className="space-y-2">
        {topPriorityItems.slice(0, 3).map((item) => (
          <li key={item.id} className="flex items-center gap-3">
            <Badge priority={item.priority} />
            <div>
              <p className="font-medium">{item.title}</p>
              <p className="text-sm text-gray-600">
                {item.knowledge_area} · {item.estimated_read_time_minutes} min
              </p>
            </div>
          </li>
        ))}
      </ul>
      <Button as={Link} to="/reading" variant="secondary" size="sm">
        View All Reading →
      </Button>
    </div>
  );
}
```

**Key Benefits:**

1. **Zero Interruption:** Badge updates silently in background (no popups/toasts during quiz)
2. **Priority Awareness:** Visual indicator (color) for high-priority items
3. **Engagement Signal:** Subtle pulse animation draws attention without disrupting flow
4. **Accessibility:** Screen reader friendly with descriptive labels

### Knowledge Area Detail View

**Purpose:** Provide deep-dive analytics into user's performance on a specific knowledge area (KA) when they click a competency bar on dashboard.

**Trigger:** User clicks/taps any of the 6 KA competency bars on dashboard

**Implementation:** Modal dialog or dedicated page (`/knowledge-area/{ka-slug}`)

**Data Requirements:**

```typescript
interface KADetailView {
  knowledge_area: KnowledgeArea;
  current_competency: number; // 0-100
  target_competency: number; // From user onboarding
  gap: number; // target - current
  confidence: number; // 0-1 (IRT uncertainty)

  // Performance breakdown
  total_questions_answered: number;
  correct_count: number;
  recent_accuracy: number; // Last 10 questions

  // Concept-level gaps
  concept_gaps: Array<{
    concept_tag: string;
    competency: number;
    questions_answered: number;
    last_correct: boolean;
  }>;

  // Recent performance
  recent_questions: Array<{
    question_id: string;
    text: string; // Truncated
    is_correct: boolean;
    answered_at: string;
    difficulty: number;
  }>;

  // Time tracking
  total_time_spent_minutes: number;
  avg_time_per_question_seconds: number;

  // Recommendations
  recommended_difficulty: number; // Next questions should be difficulty X
  recommended_reading_chunks: Array<ReadingChunk>;
}
```

**API Endpoint:**

```
GET /api/v1/knowledge-areas/{ka_slug}/detail
```

**Response Example:**
```json
{
  "knowledge_area": "Business Analysis Planning and Monitoring",
  "current_competency": 68,
  "target_competency": 80,
  "gap": 12,
  "confidence": 0.75,
  "total_questions_answered": 42,
  "correct_count": 28,
  "recent_accuracy": 0.70,
  "concept_gaps": [
    {
      "concept_tag": "Stakeholder Analysis",
      "competency": 55,
      "questions_answered": 8,
      "last_correct": false
    },
    {
      "concept_tag": "Business Analysis Planning",
      "competency": 72,
      "questions_answered": 12,
      "last_correct": true
    }
  ],
  "recent_questions": [ /* Last 10 questions */ ],
  "total_time_spent_minutes": 78,
  "avg_time_per_question_seconds": 65,
  "recommended_difficulty": 3
}
```

**UI Layout:**

```
┌────────────────────────────────────────────────────────┐
│  Business Analysis Planning and Monitoring          [X]│
├────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────────────────────────────────────┐  │
│  │  Current Competency:  68%  ▓▓▓▓▓▓▓▓░░░░ (75% confidence) │
│  │  Target Competency:   80%  ▓▓▓▓▓▓▓▓▓▓▓░              │
│  │  Gap:                 12 points                     │
│  └─────────────────────────────────────────────────┘  │
│                                                         │
│  Performance Summary                                   │
│  • 42 questions answered (28 correct, 67%)            │
│  • Recent accuracy: 70% (last 10 questions)           │
│  • 78 minutes spent on this knowledge area            │
│                                                         │
│  Concept-Level Gaps                                    │
│  ┌─────────────────────────────────────────────────┐  │
│  │ Stakeholder Analysis            55%  [Weak]     │  │
│  │   └─ 8 questions answered, last: incorrect      │  │
│  │ Business Analysis Planning      72%  [Good]     │  │
│  │   └─ 12 questions answered, last: correct       │  │
│  │ ...                                              │  │
│  └─────────────────────────────────────────────────┘  │
│                                                         │
│  Recent Performance (Last 10 Questions)                │
│  ┌─────────────────────────────────────────────────┐  │
│  │ ✓ Nov 21, 2:30pm - Medium difficulty             │  │
│  │ ✗ Nov 21, 2:28pm - Hard difficulty               │  │
│  │ ✓ Nov 21, 2:25pm - Easy difficulty               │  │
│  │ ...                                              │  │
│  └─────────────────────────────────────────────────┘  │
│                                                         │
│  Recommended Reading                                   │
│  [Reading chunk cards with "Add to Queue" button]     │
│                                                         │
│  ┌─────────────────────────────────────────────────┐  │
│  │  [Study This Knowledge Area]  [Close]            │  │
│  └─────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────┘
```

**Component Implementation:**

```tsx
// apps/web/src/pages/KnowledgeAreaDetailPage.tsx
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { CompetencyBar } from '@/components/dashboard/CompetencyBar';
import { ConceptGapList } from '@/components/ka-detail/ConceptGapList';
import { RecentPerformance } from '@/components/ka-detail/RecentPerformance';
import { RecommendedReading } from '@/components/ka-detail/RecommendedReading';

export function KnowledgeAreaDetailPage() {
  const { kaSlug } = useParams<{ kaSlug: string }>();
  const { data, isLoading } = useQuery({
    queryKey: ['ka-detail', kaSlug],
    queryFn: () => fetch(`/api/v1/knowledge-areas/${kaSlug}/detail`).then(r => r.json()),
  });

  if (isLoading) return <Loading />;

  const {
    knowledge_area,
    current_competency,
    target_competency,
    gap,
    confidence,
    concept_gaps,
    recent_questions,
    total_questions_answered,
    correct_count,
    recent_accuracy,
  } = data;

  return (
    <div className="ka-detail-page">
      <header>
        <h1>{knowledge_area}</h1>
        <button aria-label="Close" onClick={() => navigate(-1)}>×</button>
      </header>

      <section className="competency-summary">
        <CompetencyBar
          label="Current Competency"
          value={current_competency}
          max={100}
          confidence={confidence}
        />
        <CompetencyBar
          label="Target Competency"
          value={target_competency}
          max={100}
          variant="target"
        />
        <div className="gap-indicator">
          Gap: <strong>{gap} points</strong>
        </div>
      </section>

      <section className="performance-summary">
        <h2>Performance Summary</h2>
        <ul>
          <li>{total_questions_answered} questions answered ({correct_count} correct, {Math.round((correct_count / total_questions_answered) * 100)}%)</li>
          <li>Recent accuracy: {Math.round(recent_accuracy * 100)}% (last 10 questions)</li>
        </ul>
      </section>

      <section className="concept-gaps">
        <h2>Concept-Level Gaps</h2>
        <ConceptGapList gaps={concept_gaps} />
      </section>

      <section className="recent-performance">
        <h2>Recent Performance (Last 10 Questions)</h2>
        <RecentPerformance questions={recent_questions} />
      </section>

      <section className="recommended-reading">
        <h2>Recommended Reading</h2>
        <RecommendedReading knowledgeArea={kaSlug} />
      </section>

      <footer className="actions">
        <Button onClick={() => startFocusedSession(kaSlug)}>
          Study This Knowledge Area
        </Button>
        <Button variant="secondary" onClick={() => navigate(-1)}>
          Close
        </Button>
      </footer>
    </div>
  );
}
```

**Focused Session Logic:**

When user clicks "Study This Knowledge Area", start a quiz session filtered to only that KA:

```typescript
// apps/web/src/services/quizService.ts
export async function startFocusedSession(knowledgeArea: string) {
  const response = await fetch('/api/v1/sessions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_type: 'focused',
      knowledge_area_filter: knowledgeArea,
    }),
  });

  const session = await response.json();
  return session;
}
```

**Backend Endpoint:**

```python
# apps/api/src/routes/knowledge_areas.py
from fastapi import APIRouter, Depends
from src.services.analytics_service import AnalyticsService
from src.dependencies import get_current_user

router = APIRouter(prefix="/knowledge-areas", tags=["knowledge_areas"])

@router.get("/{ka_slug}/detail")
async def get_ka_detail(
    ka_slug: str,
    user = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(),
):
    """
    Get detailed analytics for a specific knowledge area.

    Returns:
    - Current competency
    - Target competency
    - Concept-level breakdown
    - Recent performance
    - Recommended reading
    """
    ka_name = slug_to_ka_name(ka_slug)

    return await analytics_service.get_ka_detail(user.id, ka_name)
```

**Accessibility:**

- Competency bars use `role="progressbar"` with `aria-valuenow`, `aria-valuemin`, `aria-valuemax`
- Recent performance list uses semantic `<ul>` with checkmark/X icons that have `aria-label`
- "Study This Knowledge Area" button has clear focus indicator
- Modal is keyboard accessible (Esc to close, Tab navigation)

**Mobile Optimization:**

- Modal becomes full-screen on mobile (< 768px)
- Collapsible sections for concept gaps and recent performance
- Swipeable recent performance timeline (optional enhancement)

---

### Backend Components

6. **API Gateway (FastAPI)** - Request routing, auth middleware, rate limiting, CORS
7. **Authentication Service** - Password hashing, JWT generation/validation, token refresh
8. **Adaptive Engine** - Question selection (IRT), competency updates, gap analysis
9. **Spaced Repetition Engine** - SM-2 algorithm, review scheduling
10. **Reading Queue Service** - Semantic search, priority calculation, async population
11. **Session Management Service** - Session CRUD, response tracking, review orchestration
12. **Data Access Layer** - Repository pattern for PostgreSQL and Qdrant
13. **Vector Search Service** - Qdrant integration, embedding generation
14. **LLM Service** - OpenAI API integration, rate limiting, cost tracking
15. **Background Job Worker** - Celery tasks for async operations

---

## Core Workflows

### Workflow 1: User Registration & Onboarding

User completes 7-question onboarding flow (anonymous), then creates account with onboarding data persisted to profile.

### Workflow 2: Initial Diagnostic Assessment

User takes 12-question diagnostic (3 per KA) with no feedback during assessment, competency calculated at end.

### Workflow 3: Adaptive Quiz Session with Answer Submission

User answers question, receives immediate feedback + explanation, reading queue populated asynchronously (zero-interruption).

### Workflow 4: Post-Session Review

User completes session with incorrect answers, immediately re-answers them for reinforcement (2-3x better retention).

### Workflow 5: Accessing Asynchronous Reading Library

User navigates to Reading Library, views prioritized queue, reads content with engagement tracking.

---

## Database Schema

### PostgreSQL Schema

**Tables:**
- `users` - User accounts with authentication and onboarding data
- `questions` - CBAP exam questions (vectors in Qdrant)
- `quiz_sessions` - Quiz session tracking
- `responses` - User answers to questions
- `competencies` - Competency scores per KA (IRT-based)
- `reading_chunks` - BABOK content chunks (vectors in Qdrant)
- `reading_queue` - Asynchronous reading recommendations
- `spaced_repetition` - SM-2 spaced repetition schedules
- `session_reviews` - Post-session review tracking
- `review_attempts` - Individual review answers
- `admin_audit_log` - Admin operations audit trail

**Key Design Decisions:**
- UUID primary keys (security, distributed systems)
- Dual database strategy: PostgreSQL (structured data) + Qdrant (vector search)
- 3NF normalization with selective denormalization for performance
- Comprehensive indexing strategy for adaptive queries
- Triggers for automatic timestamp updates
- Views for optimized dashboard queries

### Qdrant Collections

- `questions` collection - 3072-dim vectors, filtered by KA and difficulty
- `reading_chunks` collection - 3072-dim vectors, filtered by KA and BABOK section

---

## Frontend Architecture

### Component Organization

```
apps/web/src/
├── components/           # Reusable UI components
├── pages/               # Page-level components (routes)
├── hooks/               # Custom React hooks
├── services/            # API client services
├── stores/              # Zustand state stores
├── utils/               # Utility functions
├── types/               # Frontend-specific types
└── styles/              # Global styles
```

### State Management

- **Zustand** for global state (auth, session, reading queue)
- **React Context** for theme and UI preferences
- **Local state** for forms, modals, timers

**Key Stores:**
- `authStore` - User, tokens, authentication state (persisted)
- `sessionStore` - Current quiz session, question, competency updates
- `readingStore` - Reading queue items, unread badge count

### Routing

- **React Router v6** with protected routes pattern
- Nested routes with Outlet for layout composition
- Auth guard redirects to login with return URL preservation

### API Client

- **Axios** with request/response interceptors
- Automatic JWT token attachment
- Token refresh on 401 responses
- Service layer abstracts API calls

### Browser Support Matrix

**Supported Browsers (Latest 2 Versions):**

| Browser | Versions | Platform | Priority | Notes |
|---------|----------|----------|----------|-------|
| **Chrome** | Latest 2 major versions | Windows, macOS, Linux | Primary | Development primary target |
| **Edge** | Latest 2 major versions | Windows, macOS | Primary | Chromium-based, same engine as Chrome |
| **Firefox** | Latest 2 major versions | Windows, macOS, Linux | Secondary | Gecko engine, test separately |
| **Safari** | Latest 2 major versions | macOS, iOS | Primary | WebKit engine, critical for iOS users |

**Mobile Browser Support:**

| Browser | Versions | Platform | Priority | Notes |
|---------|----------|----------|----------|-------|
| **Safari Mobile** | iOS 14+ | iPhone, iPad | Primary | Largest mobile user base for professionals |
| **Chrome Mobile** | Latest 2 versions | Android | Primary | Default Android browser |
| **Samsung Internet** | Latest version | Android Samsung devices | Tertiary | Chromium-based, usually works |

**Minimum Screen Resolutions:**

| Device Category | Minimum Width | Minimum Height | Breakpoint | Notes |
|-----------------|---------------|----------------|------------|-------|
| **Mobile** | 375px | 667px | 0-767px | iPhone SE and up |
| **Tablet** | 768px | 1024px | 768-1279px | iPad standard |
| **Desktop** | 1280px | 720px | 1280px+ | Minimum usable desktop |

**Responsive Breakpoints:**
```css
/* Mobile-first approach */
/* Base styles: Mobile (375px+) */

@media (min-width: 768px) {
  /* Tablet styles */
}

@media (min-width: 1280px) {
  /* Desktop styles */
}

@media (min-width: 1920px) {
  /* Large desktop (optional) */
}
```

**Polyfill Strategy:**

LearnR uses modern JavaScript (ES2020+) and relies on Vite's built-in browser target configuration. No polyfills required for supported browsers.

**Browser Target (vite.config.ts):**
```typescript
export default {
  build: {
    target: ['es2020', 'edge88', 'firefox78', 'chrome87', 'safari14'],
  },
};
```

**Unsupported Browsers:**
- Internet Explorer (all versions) - End of life, no support
- Browsers older than 2 major versions - Security and performance concerns
- Opera Mini - Limited JavaScript support

**Testing Matrix:**

| Browser | Device | Frequency | Tools |
|---------|--------|-----------|-------|
| Chrome (latest) | Desktop | Every build | Playwright E2E |
| Safari (latest) | macOS, iOS | Every release | Manual + BrowserStack |
| Firefox (latest) | Desktop | Every release | Playwright E2E |
| Edge (latest) | Desktop | Weekly | Playwright E2E |
| Chrome Mobile | Android | Pre-release | BrowserStack |
| Safari Mobile | iPhone | Pre-release | Manual testing |

**Browser-Specific Considerations:**

**Safari:**
- Date input handling (use custom date picker if needed)
- Flexbox gap property (supported in Safari 14.1+)
- Service worker limitations (iOS PWA restrictions)

**Firefox:**
- Scrollbar styling (limited compared to Chrome)
- CSS backdrop-filter (supported in Firefox 103+)

**Mobile Safari:**
- 100vh viewport height issues (use `-webkit-fill-available`)
- Scroll momentum (`-webkit-overflow-scrolling: touch`)
- Fixed position elements during scroll

### Progressive Web App (PWA) Implementation

LearnR implements Progressive Web App capabilities to enhance mobile experience, enable offline error handling, and prepare for future offline features.

#### MVP PWA Features (30-Day Sprint)

**1. Web App Manifest**

Location: `apps/web/public/manifest.json`

```json
{
  "name": "LearnR - CBAP Exam Preparation",
  "short_name": "LearnR",
  "description": "AI-powered adaptive learning for CBAP certification",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#FFFFFF",
  "theme_color": "#0066CC",
  "orientation": "portrait-primary",
  "icons": [
    {
      "src": "/icons/icon-72x72.png",
      "sizes": "72x72",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/icons/icon-96x96.png",
      "sizes": "96x96",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-128x128.png",
      "sizes": "128x128",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-144x144.png",
      "sizes": "144x144",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-152x152.png",
      "sizes": "152x152",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-192x192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-384x384.png",
      "sizes": "384x384",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-512x512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ],
  "categories": ["education", "productivity"],
  "screenshots": [
    {
      "src": "/screenshots/desktop-dashboard.png",
      "sizes": "1280x720",
      "type": "image/png",
      "form_factor": "wide"
    },
    {
      "src": "/screenshots/mobile-quiz.png",
      "sizes": "750x1334",
      "type": "image/png",
      "form_factor": "narrow"
    }
  ]
}
```

**Manifest Configuration in index.html:**
```html
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#0066CC">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="LearnR">
<link rel="apple-touch-icon" href="/icons/icon-152x152.png">
```

**2. Service Worker for Offline Error Handling**

Location: `apps/web/public/service-worker.js`

**Strategy:** Network-first with graceful offline error page

```javascript
const CACHE_NAME = 'learnr-v1';
const OFFLINE_PAGE = '/offline.html';

// Install event - cache offline page
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll([
        OFFLINE_PAGE,
        '/icons/icon-192x192.png',
        '/styles/offline.css'
      ]);
    })
  );
  self.skipWaiting();
});

// Fetch event - network-first, fallback to offline page
self.addEventListener('fetch', (event) => {
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request).catch(() => {
        return caches.match(OFFLINE_PAGE);
      })
    );
  }
});

// Activate event - cleanup old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name !== CACHE_NAME)
          .map((name) => caches.delete(name))
      );
    })
  );
  self.clients.claim();
});
```

**Service Worker Registration (main.tsx):**
```typescript
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker
      .register('/service-worker.js')
      .then((registration) => {
        console.log('SW registered:', registration);
      })
      .catch((error) => {
        console.error('SW registration failed:', error);
      });
  });
}
```

**Offline Page (`apps/web/public/offline.html`):**
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Offline - LearnR</title>
  <link rel="stylesheet" href="/styles/offline.css">
</head>
<body>
  <div class="offline-container">
    <img src="/icons/icon-192x192.png" alt="LearnR Logo" width="96" height="96">
    <h1>You're Offline</h1>
    <p>LearnR requires an internet connection to load quiz questions and track your progress.</p>
    <p>Please check your connection and try again.</p>
    <button onclick="window.location.reload()">Retry</button>
  </div>
</body>
</html>
```

**3. Add to Home Screen (A2HS) Prompt**

**User Prompt Strategy:**
- Show A2HS prompt after user completes first quiz session (engagement signal)
- Defer prompt using `beforeinstallprompt` event
- User can dismiss permanently (localStorage flag)

**Implementation:**
```typescript
// src/hooks/useInstallPrompt.ts
import { useState, useEffect } from 'react';

export function useInstallPrompt() {
  const [deferredPrompt, setDeferredPrompt] = useState<any>(null);
  const [showPrompt, setShowPrompt] = useState(false);

  useEffect(() => {
    const handler = (e: Event) => {
      e.preventDefault();
      setDeferredPrompt(e);

      // Show prompt if user hasn't dismissed it
      const dismissed = localStorage.getItem('a2hs-dismissed');
      const firstSessionCompleted = localStorage.getItem('first-session-completed');

      if (!dismissed && firstSessionCompleted) {
        setShowPrompt(true);
      }
    };

    window.addEventListener('beforeinstallprompt', handler);
    return () => window.removeEventListener('beforeinstallprompt', handler);
  }, []);

  const promptInstall = async () => {
    if (!deferredPrompt) return;

    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;

    console.log(`User ${outcome === 'accepted' ? 'accepted' : 'dismissed'} A2HS`);
    setDeferredPrompt(null);
    setShowPrompt(false);
  };

  const dismissPrompt = () => {
    localStorage.setItem('a2hs-dismissed', 'true');
    setShowPrompt(false);
  };

  return { showPrompt, promptInstall, dismissPrompt };
}
```

#### Post-MVP PWA Features (Future Roadmap)

**1. Offline Quiz Mode (Q1 2026)**
- Cache last 50 questions in IndexedDB
- Allow offline quiz sessions with local state
- Sync responses when connection restored
- Background Sync API for reliable upload

**2. Background Sync for Progress Tracking**
- Queue competency updates during offline usage
- Sync when connection restored
- Prevent data loss on flaky connections

**3. Push Notifications for Spaced Repetition**
- Remind users when reviews are due
- Daily study streak notifications
- Exam countdown reminders
- Requires user opt-in and notification permission

**4. Offline Reading Library**
- Cache reading content chunks for offline access
- Smart pre-caching based on user's weak areas
- Download BABOK sections for offline study

#### iOS-Specific Considerations

**Safari PWA Limitations:**
- No push notifications support (as of iOS 17)
- Service worker limitations (cleared after 7 days of inactivity)
- No background sync API
- Limited IndexedDB quota (50MB)

**iOS Workarounds:**
- Use Web Share API for sharing progress (instead of push)
- Show in-app reminders (instead of push notifications)
- Aggressive caching strategy for frequently accessed content
- Clear user expectations about offline capabilities

#### PWA Build Configuration

**Vite PWA Plugin (vite.config.ts):**
```typescript
import { VitePWA } from 'vite-plugin-pwa';

export default {
  plugins: [
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['icons/*.png', 'offline.html'],
      manifest: {
        // ... manifest config from above
      },
      workbox: {
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/api\.learnr\.com\/v1\/.*/,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'api-cache',
              expiration: {
                maxEntries: 100,
                maxAgeSeconds: 60 * 60, // 1 hour
              },
            },
          },
        ],
      },
    }),
  ],
};
```

#### Testing PWA Features

**Lighthouse PWA Audit:**
- Target score: 90+ (MVP)
- Required criteria:
  - ✓ Installable (manifest + service worker)
  - ✓ Registers a service worker
  - ✓ Responds with 200 when offline
  - ✓ Provides a valid manifest
  - ✓ Uses HTTPS
  - ✓ Redirects HTTP to HTTPS

**Manual Testing:**
- Test A2HS on Android Chrome, iOS Safari
- Test offline page display (disable network)
- Verify manifest icons at all sizes
- Test app in standalone mode (after install)

---

## Accessibility Architecture

### WCAG 2.1 Level AA Compliance

LearnR is committed to **WCAG 2.1 Level AA accessibility** to ensure the platform is usable by all learners, including those with disabilities. This is both a legal requirement and a core product value.

### Semantic HTML Strategy

**Foundation:**
- Use semantic HTML5 elements (`<nav>`, `<main>`, `<article>`, `<section>`, `<button>`, `<header>`) instead of generic `<div>` elements
- All form inputs have associated `<label>` elements with proper `for` attribute
- Headings follow logical hierarchy (single `<h1>` per page, no skipped levels)
- Lists use proper `<ul>`, `<ol>`, `<li>` structure

**Implementation Pattern:**
```tsx
// Good - Semantic
<nav aria-label="Main navigation">
  <button aria-label="Start quiz session">Continue Learning</button>
</nav>

// Bad - Non-semantic
<div className="nav">
  <div onClick={handleClick}>Continue Learning</div>
</div>
```

### ARIA Implementation Patterns

**When to Use ARIA:**
- Only when semantic HTML is insufficient
- For dynamic content updates (live regions)
- For custom interactive widgets (modals, tabs, tooltips)

**Key ARIA Patterns:**

| Component | ARIA Pattern | Example |
|-----------|-------------|---------|
| **Quiz Question** | `role="region"`, `aria-live="polite"` | Announce answer feedback to screen readers |
| **Competency Bars** | `role="progressbar"`, `aria-valuenow`, `aria-valuemin`, `aria-valuemax` | Progress visualization |
| **Modal Dialogs** | `role="dialog"`, `aria-modal="true"`, `aria-labelledby` | Reading content modal, settings |
| **Navigation Badge** | `aria-label="7 unread reading items"` | Reading queue count |
| **Loading States** | `aria-busy="true"`, `aria-live="assertive"` | Question loading |
| **Error Messages** | `role="alert"`, `aria-live="assertive"` | Form validation errors |

**Live Region Example:**
```tsx
// Answer feedback announces to screen readers
<div
  role="status"
  aria-live="polite"
  aria-atomic="true"
  className="answer-feedback"
>
  {isCorrect ? "Correct! Well done." : "Incorrect. Review the explanation below."}
</div>
```

### Keyboard Navigation Flow

**Tab Order Requirements:**
- All interactive elements accessible via `Tab` key
- Logical tab order follows visual layout (top-to-bottom, left-to-right)
- Focus trap implemented in modals (tab cycles within modal)
- Skip to main content link for screen reader users

**Keyboard Shortcuts:**
| Action | Shortcut | Context |
|--------|----------|---------|
| **Submit Answer** | `Enter` | When answer option focused |
| **Next Question** | `Enter` or `Space` | After reviewing explanation |
| **Close Modal** | `Esc` | Reading content, settings |
| **Navigate Quiz Options** | Arrow keys (optional enhancement) | Answer selection |

**Focus Management:**
```tsx
// After submitting answer, focus moves to explanation
useEffect(() => {
  if (answerSubmitted) {
    explanationRef.current?.focus();
  }
}, [answerSubmitted]);
```

### Screen Reader Support

**Testing Requirements:**
- Test with NVDA (Windows), JAWS (Windows), VoiceOver (macOS/iOS)
- All interactive elements have descriptive labels
- Dynamic content changes announced via ARIA live regions
- Images have meaningful `alt` text (or `alt=""` for decorative images)

**Screen Reader Optimizations:**
- Competency scores announced as percentages: "Business Analysis Planning and Monitoring: 73 percent"
- Question progress: "Question 5 of 12"
- Review status: "This is a review question from 3 days ago"
- Reading priority: "High priority reading item"

### Color Contrast Requirements

**WCAG AA Standards:**
- **Normal text (< 18px):** Minimum 4.5:1 contrast ratio
- **Large text (≥ 18px or 14px bold):** Minimum 3:1 contrast ratio
- **Interactive elements:** Minimum 3:1 contrast for borders/icons

**Validation Process:**
- All color combinations validated using WebAIM Contrast Checker
- Design tokens include contrast ratios in documentation
- Automated contrast testing in CI pipeline (axe-core)

**Dark Mode Considerations:**
- Dark mode palette independently validated for contrast
- Enhanced contrast in dark mode (ratios often exceed WCAG AA)
- Text size increased in dark mode (17px vs 16px) for better readability

### Focus Indicators

**Visibility Requirements:**
- All interactive elements have visible focus indicator
- Focus outline: 2px solid, high contrast color
- Minimum 3:1 contrast ratio against background
- Focus indicators never removed (`outline: none` prohibited without replacement)

**Implementation:**
```css
/* Default focus style */
:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
  border-radius: 4px;
}

/* Custom focus for buttons */
.button:focus-visible {
  box-shadow: 0 0 0 3px rgba(0, 102, 204, 0.4);
}
```

### Form Accessibility

**Input Requirements:**
- Every input has associated `<label>` (explicit association via `for`/`id`)
- Required fields marked with `aria-required="true"` and visual indicator
- Error messages associated with inputs via `aria-describedby`
- Validation errors announced to screen readers via `role="alert"`

**Error Handling Example:**
```tsx
<div>
  <label htmlFor="email">Email Address *</label>
  <input
    id="email"
    type="email"
    aria-required="true"
    aria-invalid={hasError}
    aria-describedby={hasError ? "email-error" : undefined}
  />
  {hasError && (
    <div id="email-error" role="alert" className="error-message">
      Please enter a valid email address
    </div>
  )}
</div>
```

### Responsive & Mobile Accessibility

**Touch Target Size:**
- Minimum 44x44px touch targets (WCAG AAA guideline, adopted for quality)
- Adequate spacing between interactive elements (minimum 8px)
- Mobile buttons use pill-rounded design for larger touch area

**Zoom & Scaling:**
- Support 200% text zoom without loss of functionality
- No horizontal scrolling at 320px width (mobile)
- Responsive layout adapts to portrait and landscape orientations

### Motion & Animation Accessibility

**Respect User Preferences:**
```css
/* Disable animations for users who prefer reduced motion */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

**Animation Guidelines:**
- No flashing content (avoid seizure triggers)
- Animations are decorative, not required for understanding content
- Provide alternative feedback for users with reduced motion (e.g., instant state change instead of fade)

### Testing & Validation

**Automated Testing:**
- **axe-core** integrated into Playwright E2E tests (runs on every build)
- **eslint-plugin-jsx-a11y** for React accessibility linting
- Lighthouse accessibility audits (target score: 95+)

**Manual Testing:**
- Keyboard-only navigation testing (unplug mouse)
- Screen reader testing (NVDA, VoiceOver)
- Color contrast validation (WebAIM tool)
- Zoom testing (200% browser zoom)

**Accessibility Checklist (Pre-Release):**
- [ ] All interactive elements keyboard accessible
- [ ] Screen reader announces all dynamic content changes
- [ ] Color contrast meets WCAG AA for all text and icons
- [ ] Focus indicators visible on all interactive elements
- [ ] Forms have proper labels, error messages, and validation
- [ ] No keyboard traps (except intentional modal focus traps)
- [ ] Images have appropriate alt text
- [ ] Headings follow logical hierarchy
- [ ] ARIA used appropriately (not overused)
- [ ] Automated axe-core tests pass with 0 violations

### Accessibility Statement

**User-Facing Commitment:**
- Accessibility statement published at `/accessibility`
- Contact information for reporting accessibility issues
- Commitment to WCAG 2.1 Level AA compliance
- Known limitations documented (if any)
- Roadmap for accessibility improvements

---

## Backend Architecture

### Service Architecture

**Traditional Server (FastAPI on Railway)**

Layered architecture: API Routes → Services → Repositories → Database

```
apps/api/src/
├── main.py              # FastAPI app entry
├── routes/              # API route handlers
├── services/            # Business logic layer
├── repositories/        # Data access layer
├── models/              # SQLAlchemy ORM models
├── schemas/             # Pydantic schemas
├── middleware/          # Auth, CORS, rate limiting
├── tasks/               # Celery background tasks
└── utils/               # Utilities (IRT, SM-2)
```

### Repository Pattern

All database access abstracted through repositories:
- `UserRepository`, `QuestionRepository`, `ResponseRepository`, etc.
- Async methods for non-blocking I/O
- Enables testing with mock repositories

### Authentication

**JWT-based authentication:**
- Access tokens (15 min expiry)
- Refresh tokens (7 day expiry)
- Redis blacklist for logout support
- bcrypt password hashing (cost factor 12)
- Dependency injection for current user in routes

### Concurrent Session Handling

**Challenge:** Users may access LearnR from multiple devices simultaneously (e.g., desktop at home, laptop at work, mobile during commute). The system must handle concurrent quiz sessions, competency updates, and reading queue modifications without data corruption.

**Strategy: Optimistic Locking with Conflict Detection**

#### Database-Level Concurrency Control

**Optimistic Locking Pattern:**
All tables with concurrent write risk include `updated_at` timestamp column with automatic trigger updates.

```sql
-- Example: quiz_sessions table
CREATE TABLE quiz_sessions (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMP,
    version INTEGER NOT NULL DEFAULT 1,  -- Optimistic lock version
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Trigger: auto-update version on modification
CREATE OR REPLACE FUNCTION update_version_and_timestamp()
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
EXECUTE FUNCTION update_version_and_timestamp();
```

**Update Pattern (SQLAlchemy):**
```python
# apps/api/src/repositories/session_repository.py
from sqlalchemy import and_
from sqlalchemy.exc import StaleDataError

async def end_session(session_id: UUID, expected_version: int) -> QuizSession:
    """
    End a quiz session with optimistic locking.

    Raises:
        ConcurrentModificationError: If session was modified by another device
    """
    result = await db.execute(
        update(QuizSession)
        .where(and_(
            QuizSession.id == session_id,
            QuizSession.version == expected_version  # Optimistic lock check
        ))
        .values(ended_at=datetime.utcnow())
        .returning(QuizSession)
    )

    session = result.scalar_one_or_none()

    if session is None:
        raise ConcurrentModificationError(
            "Session was modified by another device. Please refresh and try again."
        )

    return session
```

#### Quiz Session Conflict Resolution

**Rule: Last-Write-Wins for Session Metadata, Merge for Responses**

| Scenario | Resolution Strategy | Example |
|----------|---------------------|---------|
| **User starts quiz on Device A, then Device B** | Allow both sessions (separate session IDs) | Two distinct quiz sessions created |
| **User ends session on Device A, Device B tries to submit answer** | Return 409 Conflict, prompt user to refresh | Frontend shows: "This session ended on another device" |
| **Same answer submitted twice (network retry)** | Idempotency: use `response_id` (client-generated UUID) | Duplicate response ignored, return existing |
| **Competency updated concurrently** | Row-level locking on `competencies` table | Serialized updates via PostgreSQL row lock |

#### Response Idempotency

**Challenge:** Network retries may cause duplicate answer submissions.

**Solution: Client-Generated Request IDs**

**Frontend:**
```typescript
// apps/web/src/services/quizService.ts
import { v4 as uuidv4 } from 'uuid';

export async function submitAnswer(questionId: string, answer: string) {
  const requestId = uuidv4(); // Client-generated idempotency key

  const response = await fetch(`/api/v1/questions/${questionId}/answer`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Request-ID': requestId,
    },
    body: JSON.stringify({ answer, request_id: requestId }),
  });

  return response.json();
}
```

**Backend:**
```python
# apps/api/src/routes/questions.py
from fastapi import Header

@router.post("/{question_id}/answer")
async def submit_answer(
    question_id: UUID,
    answer_data: AnswerSubmission,
    x_request_id: str = Header(..., alias="X-Request-ID"),
    user = Depends(get_current_user),
):
    """
    Submit answer with idempotency via request_id.

    If request_id already exists in responses table, return existing response.
    """
    # Check for existing response with same request_id
    existing = await response_repo.get_by_request_id(x_request_id)
    if existing:
        return existing  # Idempotent: return cached response

    # Create new response
    response = await response_repo.create(
        user_id=user.id,
        question_id=question_id,
        selected_answer=answer_data.answer,
        request_id=x_request_id,  # Store for idempotency
    )

    return response
```

**Database Schema Addition:**
```sql
ALTER TABLE responses ADD COLUMN request_id UUID UNIQUE;
CREATE INDEX idx_responses_request_id ON responses(request_id);
```

#### Competency Update Locking

**Challenge:** Competency scores updated concurrently from multiple sessions may produce incorrect results.

**Solution: Row-Level Locking**

```python
# apps/api/src/services/adaptive_engine.py
from sqlalchemy import select

async def update_competency(user_id: UUID, knowledge_area: str, delta: float):
    """
    Update competency with row-level locking to prevent concurrent modification.
    """
    async with db.begin():  # Transaction
        # Acquire row lock (SELECT ... FOR UPDATE)
        result = await db.execute(
            select(Competency)
            .where(and_(
                Competency.user_id == user_id,
                Competency.knowledge_area == knowledge_area
            ))
            .with_for_update()  # Row-level lock
        )

        competency = result.scalar_one()

        # Update competency score
        competency.score = min(100, max(0, competency.score + delta))
        competency.last_updated = datetime.utcnow()

        await db.flush()

    return competency
```

**Performance:** Row locks are released at transaction commit, minimal contention for single-user updates.

#### Reading Queue Deduplication

**Challenge:** Multiple quiz sessions may trigger duplicate reading queue items.

**Solution: Unique Constraint + INSERT ... ON CONFLICT**

```sql
ALTER TABLE reading_queue
ADD CONSTRAINT unique_user_chunk UNIQUE (user_id, chunk_id);
```

```python
# apps/api/src/repositories/reading_repository.py
async def add_to_queue(user_id: UUID, chunk_id: UUID, priority: str):
    """
    Add reading item to queue with deduplication.

    If (user_id, chunk_id) already exists, update priority if higher.
    """
    query = insert(ReadingQueue).values(
        user_id=user_id,
        chunk_id=chunk_id,
        priority=priority,
        added_at=datetime.utcnow(),
    ).on_conflict_do_update(
        constraint='unique_user_chunk',
        set_={
            'priority': func.greatest(ReadingQueue.priority, priority),
            'added_at': datetime.utcnow(),  # Refresh timestamp
        }
    )

    await db.execute(query)
```

#### Frontend Conflict UI

**User Experience for Conflicts:**

**Scenario 1: Session Ended on Another Device**
```tsx
// Frontend error handler
if (error.status === 409 && error.code === 'SESSION_ENDED') {
  showToast({
    type: 'warning',
    message: 'This session ended on another device. Redirecting to dashboard...',
    duration: 3000,
  });

  setTimeout(() => navigate('/dashboard'), 3000);
}
```

**Scenario 2: Optimistic Lock Failure**
```tsx
if (error.status === 409 && error.code === 'CONCURRENT_MODIFICATION') {
  showToast({
    type: 'error',
    message: 'Data changed on another device. Refreshing...',
    duration: 2000,
  });

  // Refetch latest data
  queryClient.invalidateQueries(['session', sessionId]);
}
```

#### Monitoring & Alerting

**Metrics to Track:**
- Concurrent session conflict rate (target: <1% of requests)
- Optimistic lock failures (alert if >5% over 5 minutes)
- Duplicate request_id occurrences (indicates network retry behavior)

**Logging:**
```python
logger.info(
    "Concurrent modification detected",
    extra={
        "user_id": user_id,
        "resource": "quiz_session",
        "expected_version": expected_version,
        "actual_version": actual_version,
    }
)
```

#### Edge Cases

| Edge Case | Handling |
|-----------|----------|
| **User starts session on Device A, loses network, continues on Device B** | Device A session times out after 30 min inactivity; Device B creates new session |
| **User submits same answer twice (double-click)** | Request ID deduplication prevents duplicate response |
| **User updates profile on Device A while quiz running on Device B** | Independent updates; no conflict (separate tables) |
| **Reading queue badge count stale on Device A** | Periodic polling (30s) + refresh on app focus ensures eventual consistency |

**Key Principle:** Prioritize user experience over perfect consistency. Eventual consistency is acceptable for analytics (e.g., badge counts), but critical data (responses, competency) uses strong consistency (locking).

---

## Unified Project Structure

```
learnr/
├── .github/
│   └── workflows/
│       ├── ci.yml                    # Test on PR, push to main
│       ├── deploy-frontend.yml       # Deploy to Vercel
│       └── deploy-backend.yml        # Deploy to Railway
├── apps/
│   ├── web/                          # React SPA Frontend
│   │   ├── src/
│   │   │   ├── components/
│   │   │   │   ├── common/          # Button, Card, Modal, Badge
│   │   │   │   ├── quiz/            # QuestionCard, AnswerOptions, Feedback
│   │   │   │   ├── dashboard/       # CompetencyBar, ProgressChart
│   │   │   │   ├── reading/         # ReadingLibrary, ReadingCard
│   │   │   │   └── layout/          # Navigation, Header, Footer
│   │   │   ├── pages/
│   │   │   │   ├── HomePage.tsx
│   │   │   │   ├── LoginPage.tsx
│   │   │   │   ├── OnboardingPage.tsx
│   │   │   │   ├── DiagnosticPage.tsx
│   │   │   │   ├── DashboardPage.tsx
│   │   │   │   ├── QuizSessionPage.tsx
│   │   │   │   ├── SessionReviewPage.tsx
│   │   │   │   ├── ReadingLibraryPage.tsx
│   │   │   │   └── SettingsPage.tsx
│   │   │   ├── hooks/
│   │   │   │   ├── useAuth.ts
│   │   │   │   ├── useQuizSession.ts
│   │   │   │   ├── useReadingQueue.ts
│   │   │   │   └── useTimer.ts
│   │   │   ├── services/
│   │   │   │   ├── api.ts           # Axios config
│   │   │   │   ├── authService.ts
│   │   │   │   ├── quizService.ts
│   │   │   │   ├── readingService.ts
│   │   │   │   └── analyticsService.ts
│   │   │   ├── stores/
│   │   │   │   ├── authStore.ts     # Zustand
│   │   │   │   ├── sessionStore.ts
│   │   │   │   └── readingStore.ts
│   │   │   ├── utils/
│   │   │   │   ├── formatters.ts
│   │   │   │   └── validators.ts
│   │   │   ├── types/
│   │   │   │   └── index.ts
│   │   │   ├── styles/
│   │   │   │   └── globals.css
│   │   │   ├── App.tsx
│   │   │   └── main.tsx
│   │   ├── public/
│   │   │   ├── favicon.ico
│   │   │   └── assets/
│   │   ├── index.html
│   │   ├── vite.config.ts
│   │   ├── tailwind.config.js
│   │   ├── tsconfig.json
│   │   ├── package.json
│   │   └── .env.example
│   └── api/                          # FastAPI Backend
│       ├── src/
│       │   ├── main.py              # App entry point
│       │   ├── config.py            # Settings
│       │   ├── dependencies.py      # DI
│       │   ├── routes/
│       │   │   ├── auth.py
│       │   │   ├── users.py
│       │   │   ├── diagnostic.py
│       │   │   ├── sessions.py
│       │   │   ├── questions.py
│       │   │   ├── competency.py
│       │   │   ├── reading.py
│       │   │   ├── reviews.py
│       │   │   ├── session_review.py
│       │   │   └── analytics.py
│       │   ├── services/
│       │   │   ├── auth_service.py
│       │   │   ├── adaptive_engine.py
│       │   │   ├── spaced_repetition.py
│       │   │   ├── reading_queue_service.py
│       │   │   ├── session_service.py
│       │   │   └── llm_service.py
│       │   ├── repositories/
│       │   │   ├── user_repository.py
│       │   │   ├── question_repository.py
│       │   │   ├── response_repository.py
│       │   │   ├── competency_repository.py
│       │   │   ├── session_repository.py
│       │   │   ├── reading_repository.py
│       │   │   └── spaced_repetition_repository.py
│       │   ├── models/
│       │   │   ├── user.py
│       │   │   ├── question.py
│       │   │   ├── session.py
│       │   │   ├── response.py
│       │   │   ├── competency.py
│       │   │   ├── reading.py
│       │   │   └── spaced_repetition.py
│       │   ├── schemas/
│       │   │   ├── user.py
│       │   │   ├── question.py
│       │   │   ├── session.py
│       │   │   ├── response.py
│       │   │   └── auth.py
│       │   ├── middleware/
│       │   │   ├── auth_middleware.py
│       │   │   ├── cors_middleware.py
│       │   │   └── rate_limit_middleware.py
│       │   ├── tasks/
│       │   │   ├── reading_queue_tasks.py
│       │   │   └── analytics_tasks.py
│       │   ├── utils/
│       │   │   ├── irt.py
│       │   │   ├── sm2.py
│       │   │   └── validators.py
│       │   └── db/
│       │       ├── session.py
│       │       ├── migrations/       # Alembic
│       │       └── qdrant_client.py
│       ├── tests/
│       │   ├── test_auth.py
│       │   ├── test_adaptive.py
│       │   └── test_api.py
│       ├── Dockerfile
│       ├── requirements.txt
│       ├── pyproject.toml
│       ├── pytest.ini
│       └── .env.example
├── packages/
│   ├── shared-types/                # Shared TypeScript interfaces
│   │   ├── src/
│   │   │   └── index.ts
│   │   ├── package.json
│   │   └── tsconfig.json
│   └── config/                      # Shared configs
│       ├── eslint-config/
│       ├── typescript-config/
│       └── prettier-config/
├── infrastructure/
│   ├── docker/
│   │   ├── docker-compose.yml       # Local dev environment
│   │   └── docker-compose.prod.yml
│   └── terraform/                   # Future IaC (AWS)
├── scripts/
│   ├── seed-questions.py            # Seed database
│   ├── generate-embeddings.py      # Populate Qdrant
│   └── backup-db.sh
├── docs/
│   ├── prd.md
│   ├── architecture.md
│   └── api/
│       └── openapi.json
├── .env.example
├── .gitignore
├── package.json                     # Root package.json (npm workspaces)
├── package-lock.json
└── README.md
```

---

## Development Workflow

### Local Development Setup

**Prerequisites:**

```bash
# Required software
node --version  # v18.x or higher
python --version  # 3.11.x
docker --version  # 24.x
docker-compose --version  # 2.x
```

**Initial Setup:**

```bash
# Clone repository
git clone https://github.com/your-org/learnr.git
cd learnr

# Install all dependencies (monorepo)
npm install

# Copy environment files
cp .env.example .env
cp apps/web/.env.example apps/web/.env.local
cp apps/api/.env.example apps/api/.env

# Start infrastructure (PostgreSQL, Redis, Qdrant)
docker-compose up -d

# Backend setup
cd apps/api
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Seed initial data (questions, reading chunks)
python scripts/seed-questions.py

# Start backend server
uvicorn src.main:app --reload --port 8000

# Frontend setup (new terminal)
cd apps/web
npm run dev  # Starts Vite dev server on port 5173
```

**Development Commands:**

```bash
# Start all services
npm run dev              # Root: Runs frontend + backend concurrently

# Start frontend only
cd apps/web
npm run dev              # Vite dev server (http://localhost:5173)

# Start backend only
cd apps/api
uvicorn src.main:app --reload  # FastAPI (http://localhost:8000)

# Start background worker
cd apps/api
celery -A src.tasks worker --loglevel=info

# Run tests
npm run test             # All tests (frontend + backend)
npm run test:frontend    # Frontend tests only (Vitest)
npm run test:backend     # Backend tests only (pytest)
npm run test:e2e         # E2E tests (Playwright)

# Linting & formatting
npm run lint             # ESLint + Ruff
npm run format           # Prettier + Ruff format

# Database migrations
cd apps/api
alembic revision --autogenerate -m "description"  # Create migration
alembic upgrade head     # Apply migrations
alembic downgrade -1     # Rollback one migration
```

### Environment Configuration

**Required Environment Variables:**

**Frontend (`.env.local`):**
```bash
VITE_API_BASE_URL=http://localhost:8000/v1
VITE_POSTHOG_KEY=your_posthog_key
VITE_POSTHOG_HOST=https://app.posthog.com
```

**Backend (`.env`):**
```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/learnr
REDIS_URL=redis://localhost:6379/0

# Qdrant
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your_qdrant_key

# OpenAI
OPENAI_API_KEY=sk-...

# JWT
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256

# PostHog
POSTHOG_API_KEY=your_posthog_key

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

**Shared (root `.env`):**
```bash
NODE_ENV=development
PYTHON_ENV=development
```

---

## Deployment Architecture

### Deployment Strategy

**Frontend Deployment:**
- **Platform:** Vercel
- **Build Command:** `cd apps/web && npm run build`
- **Output Directory:** `apps/web/dist`
- **CDN/Edge:** Vercel Edge Network (global, automatic)
- **Environment Variables:** Set in Vercel dashboard
- **Deployment Trigger:** Push to `main` branch (automatic)

**Backend Deployment:**
- **Platform:** Railway
- **Build Command:** `cd apps/api && pip install -r requirements.txt`
- **Start Command:** `cd apps/api && uvicorn src.main:app --host 0.0.0.0 --port $PORT`
- **Deployment Method:** Docker container (Dockerfile in apps/api)
- **Environment Variables:** Set in Railway dashboard
- **Scaling:** Auto-scaling based on CPU/memory (Railway)

**Database & Services:**
- **PostgreSQL:** Supabase (managed, US-East region)
- **Redis:** Railway Redis addon (same region as backend)
- **Qdrant:** Qdrant Cloud (managed, US region)
- **Celery Worker:** Separate Railway service (same image, different command)

### CI/CD Pipeline

**GitHub Actions Workflow (`.github/workflows/ci.yml`):**

```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: 18
      - run: npm ci
      - run: npm run test:frontend
      - run: npm run lint:frontend

  test-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r apps/api/requirements.txt
      - run: pytest apps/api/tests
      - run: ruff check apps/api/src

  e2e-tests:
    runs-on: ubuntu-latest
    needs: [test-frontend, test-backend]
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - run: npm ci
      - run: npx playwright install --with-deps
      - run: npm run test:e2e
```

**Deployment Workflows:**
- `deploy-frontend.yml` - Vercel deployment (automatic on Vercel)
- `deploy-backend.yml` - Railway deployment (automatic on Railway)

### Scalability Roadmap

**Purpose:** Define infrastructure scaling strategy from MVP (10 users) → Beta (100 users) → GA (1,000+ users).

#### Milestone 1: MVP - 10 Concurrent Users

**Timeline:** Days 1-30 (Initial Launch + Case Study)

**Infrastructure:**
| Component | Configuration | Capacity | Monthly Cost |
|-----------|--------------|----------|--------------|
| **Vercel** (Frontend) | Hobby plan | Unlimited bandwidth | $0 |
| **Railway** (Backend) | Hobby plan (512MB RAM, 0.5 vCPU) | ~10 concurrent requests | $5 |
| **Supabase** (PostgreSQL) | Free tier | 500MB database, 1GB bandwidth | $0 |
| **Qdrant Cloud** | Free tier | 1M vectors, 1GB storage | $0 |
| **Redis** | Railway addon (256MB) | Session cache, rate limiting | $3 |
| **PostHog** | Free tier | 1M events/month | $0 |
| **Sentry** | Developer plan | 5K errors/month | $0 |
| **Total** | | | **$8/month** |

**Expected Performance:**
- API response time: <200ms p95
- Quiz sessions: 5-10 concurrent
- Database size: <100MB (10 users × 500 responses avg)
- Vector DB: ~1,000 questions + 5,000 reading chunks

**Scaling Triggers:**
- Database > 400MB → Upgrade Supabase to Pro ($25/month)
- API errors > 1% → Investigate and optimize
- Response time > 500ms p95 → Profile and optimize queries

---

#### Milestone 2: Beta - 100 Concurrent Users

**Timeline:** Months 2-3 (Post-MVP Validation → Beta Launch)

**Infrastructure:**
| Component | Configuration | Capacity | Monthly Cost |
|-----------|--------------|----------|--------------|
| **Vercel** (Frontend) | Pro plan (team) | Unlimited, analytics | $20 |
| **Railway** (Backend) | Pro plan (2GB RAM, 2 vCPU) | ~100 concurrent requests | $20 |
| **Supabase** (PostgreSQL) | Pro plan | Unlimited database, 8GB bandwidth, daily backups | $25 |
| **Qdrant Cloud** | Startup plan | 10M vectors, 4GB storage | $25 |
| **Redis** | Railway addon (1GB) | Expanded cache | $10 |
| **PostHog** | Growth plan | 10M events/month | $0 (usage-based) |
| **Sentry** | Team plan | 50K errors/month | $26 |
| **OpenAI API** | Usage-based | ~1,000 content generations/month | $50 |
| **Total** | | | **$176/month** |

**Expected Performance:**
- API response time: <200ms p95
- Quiz sessions: 50-100 concurrent
- Database size: ~5GB (100 users × 2,000 responses avg)
- Vector DB: ~5,000 questions + 20,000 reading chunks

**Scaling Triggers:**
- Railway CPU > 70% sustained → Upgrade to 4GB RAM / 4 vCPU ($40/month)
- Database connections > 50 → Enable connection pooling (PgBouncer)
- Qdrant latency > 100ms p95 → Upgrade to Production plan

**Optimizations:**
- Enable PostgreSQL read replicas for analytics queries
- Implement Redis caching for competency scores (reduce DB load)
- Add CDN caching for reading content chunks (Cloudflare)

---

#### Milestone 3: GA - 1,000+ Concurrent Users

**Timeline:** Months 4-6 (General Availability)

**Infrastructure:**
| Component | Configuration | Capacity | Monthly Cost (est.) |
|-----------|--------------|----------|---------------------|
| **Vercel** (Frontend) | Pro plan | Unlimited | $20 |
| **Railway** (Backend) | 3× instances (4GB RAM, 4 vCPU each) | ~1,000 concurrent (load balanced) | $120 |
| **Supabase** (PostgreSQL) | Pro plan + read replica | Unlimited, high availability | $125 |
| **Qdrant Cloud** | Production plan | 100M vectors, 16GB storage | $95 |
| **Redis** | Railway addon (4GB) | Distributed cache | $30 |
| **PostHog** | Growth plan | 50M events/month | $150 (usage-based) |
| **Sentry** | Business plan | 500K errors/month | $80 |
| **OpenAI API** | Usage-based | ~10,000 generations/month | $500 |
| **CloudFlare CDN** | Pro plan | Global CDN for static assets | $20 |
| **Total** | | | **$1,140/month** |

**Expected Performance:**
- API response time: <200ms p95
- Quiz sessions: 500-1,000 concurrent
- Database size: ~50GB (1,000 users × 5,000 responses avg)
- Vector DB: ~10,000 questions + 50,000 reading chunks (multi-certification)

**Scaling Triggers:**
- Railway instances > 80% CPU → Add 4th instance (horizontal scaling)
- Database > 100GB → Migrate to AWS RDS PostgreSQL with auto-scaling storage
- Qdrant > 80% capacity → Upgrade to Enterprise plan or self-hosted cluster

**Optimizations:**
- Implement full-stack caching strategy (Redis + CDN + browser cache)
- Optimize database indexes based on slow query log analysis
- Enable Qdrant horizontal scaling (sharding by certification)
- Implement background job queue optimization (Celery autoscaling)

---

#### Migration Path to AWS (Post-GA, 10,000+ Users)

**When to Migrate:**
- Railway costs exceed AWS equivalent (>$500/month)
- Need advanced features (auto-scaling groups, RDS read replicas, CloudWatch)
- Enterprise customers require SLAs and compliance certifications

**AWS Architecture (Future):**
| Component | AWS Service | Rationale |
|-----------|-------------|-----------|
| **Frontend** | CloudFront + S3 | Global CDN, lower cost at scale |
| **Backend API** | ECS Fargate (containers) | Auto-scaling, familiar Docker deployment |
| **Database** | RDS PostgreSQL (Multi-AZ) | High availability, automated backups, read replicas |
| **Vector DB** | Self-hosted Qdrant on EC2 | Cost savings vs cloud at scale |
| **Cache** | ElastiCache Redis (cluster mode) | Distributed cache, high availability |
| **Analytics** | Self-hosted PostHog on ECS | Data sovereignty, cost savings |
| **Monitoring** | CloudWatch + Sentry | Native AWS integration |

**Estimated AWS Cost (10,000 users):** $3,000-5,000/month (vs $10,000+ on current stack)

---

#### Capacity Planning Guidelines

**Database Growth:**
- Average user: 5,000 responses over 60 days
- Response record: ~500 bytes
- Per-user storage: 2.5MB
- 10,000 users: 25GB database

**API Request Volume:**
- Average user: 50 API requests per quiz session
- 10,000 users, 2 sessions/week: 1M requests/week = 143K requests/day
- Peak load (evening hours): 3x average = 430K requests/day = 5 requests/second

**Vector DB Growth:**
- Questions: 10,000 (multi-certification) × 3KB per question = 30MB
- Reading chunks: 50,000 × 5KB per chunk = 250MB
- Total: 280MB vectors (well within cloud tiers)

---

### Environments

| Environment | Frontend URL | Backend URL | Purpose |
|-------------|--------------|-------------|---------|
| **Development** | http://localhost:5173 | http://localhost:8000 | Local development |
| **Staging** | https://staging.learnr.com | https://api-staging.learnr.com | Pre-production testing |
| **Production** | https://learnr.com | https://api.learnr.com | Live environment |

---

## Security and Performance

### Security Requirements

**Frontend Security:**
- **CSP Headers:** `default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.posthog.com; connect-src 'self' https://api.learnr.com https://app.posthog.com`
- **XSS Prevention:** React automatic escaping, DOMPurify for markdown rendering, Content-Security-Policy headers
- **Secure Storage:** JWT tokens in localStorage (XSS risk acknowledged), HttpOnly cookies for refresh tokens (future enhancement)

**Backend Security:**
- **Input Validation:** Pydantic models for all API inputs, SQL injection prevention via SQLAlchemy ORM, no raw SQL queries
- **Rate Limiting:** 100 req/min for adaptive endpoints, 1000 req/min for read endpoints (Redis-backed)
- **CORS Policy:** Whitelist only production domains (`https://learnr.com`), localhost for development

**Authentication Security:**
- **Token Storage:** Access tokens in memory (15 min expiry), refresh tokens in localStorage (7 day expiry)
- **Session Management:** Stateless JWT tokens, Redis blacklist for logout
- **Password Policy:** Minimum 8 characters, bcrypt hashing (cost factor 12), no complexity requirements for MVP

**Data Security:**
- **Encryption at rest:** PostgreSQL encryption via Supabase, S3 server-side encryption (AES-256)
- **Encryption in transit:** HTTPS/TLS 1.3 for all API communication, WSS for future WebSocket features
- **PII Protection:** User email, password hashes, study data never logged, GDPR-ready data export/deletion

### Admin Security Controls

**Purpose:** Secure admin operations (user impersonation, content management, user search) while maintaining audit trail for compliance.

#### Admin Role Management

**Admin Flag Protection:**
- `is_admin` boolean flag stored in `users` table
- **No API endpoint** for admin promotion (security-by-design)
- Admin promotion requires direct database update:
  ```sql
  UPDATE users SET is_admin = TRUE WHERE email = 'admin@learnr.com';
  ```
- Production database access restricted to infrastructure team only
- All admin user emails documented in secure runbook

**Middleware Protection:**
```python
# apps/api/src/middleware/auth_middleware.py
from fastapi import Depends, HTTPException, status
from src.dependencies import get_current_user

def require_admin(user = Depends(get_current_user)):
    """
    Middleware decorator for admin-only endpoints.

    Raises 403 Forbidden if user.is_admin is False.
    """
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user

# Usage in routes
@router.get("/admin/users/search")
async def search_users(
    q: str,
    admin_user = Depends(require_admin)  # Enforces admin access
):
    ...
```

#### Impersonation Security

**Token Structure:**
- Standard JWT with additional claims
- 30-minute hard expiration (non-refreshable)
- Cannot be used to impersonate other admins

**Token Claims:**
```json
{
  "sub": "impersonated_user_id",
  "is_impersonation": true,
  "impersonated_by": "admin_user_id",
  "exp": 1732186800,  // 30 minutes from issue
  "iat": 1732185000,
  "original_admin_token": "jwt_token_hash"  // For exit impersonation
}
```

**Restrictions Enforced:**

1. **Cannot Impersonate Admins:**
```python
async def impersonate_user(target_user_id: UUID, admin = Depends(require_admin)):
    target_user = await user_repo.get_by_id(target_user_id)

    if target_user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Cannot impersonate other admins"
        )

    # ... generate impersonation token
```

2. **One Active Impersonation Per Admin:**
```python
# Check Redis for active impersonation
active_key = f"impersonation:admin:{admin.id}"
if await redis.exists(active_key):
    raise HTTPException(
        status_code=409,
        detail="You have an active impersonation session. Exit it first."
    )

# Store active impersonation in Redis (30-min TTL)
await redis.setex(
    active_key,
    1800,  // 30 minutes
    target_user_id
)
```

3. **Automatic Audit Logging:**
```python
# Log impersonation start
await audit_log_repo.create(
    admin_id=admin.id,
    action_type="impersonate",
    target_user_id=target_user_id,
    ip_address=request.client.host,
    user_agent=request.headers.get("user-agent"),
    timestamp=datetime.utcnow(),
)
```

**Frontend Impersonation Banner:**

Mandatory persistent banner shown during all impersonation sessions:

```tsx
// apps/web/src/components/admin/ImpersonationBanner.tsx
export function ImpersonationBanner() {
  const { isImpersonating, impersonatedUser, exitImpersonation } = useAuth();

  if (!isImpersonating) return null;

  return (
    <div
      className="impersonation-banner"
      role="alert"
      aria-live="polite"
      style={{
        position: 'sticky',
        top: 0,
        zIndex: 9999,
        background: '#F59E0B', // Warning orange
        color: '#000',
        padding: '12px 24px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
      }}
    >
      <div className="flex items-center gap-3">
        <span className="font-bold">⚠️ IMPERSONATION MODE</span>
        <span>Viewing as: {impersonatedUser.email}</span>
      </div>
      <button
        onClick={exitImpersonation}
        className="btn-exit-impersonation"
        style={{
          background: '#000',
          color: '#fff',
          padding: '8px 16px',
          borderRadius: '4px',
          fontWeight: 600,
        }}
      >
        Exit Impersonation
      </button>
    </div>
  );
}
```

**Banner Requirements:**
- Always visible (sticky position, highest z-index)
- High-contrast colors (WCAG AAA for warning)
- Cannot be dismissed (only exit impersonation button)
- Screen reader announcement via `role="alert"`

#### Rate Limiting for Admin Endpoints

**Aggressive Rate Limits:**

| Endpoint | Rate Limit | Window | Rationale |
|----------|-----------|--------|-----------|
| `POST /admin/impersonate/{user_id}` | 10 requests | 1 hour | Security-sensitive, infrequent legitimate use |
| `GET /admin/users/search` | 100 requests | 1 hour | Prevent bulk scraping of user data |
| `GET /admin/audit-log` | 500 requests | 1 hour | Read-heavy, less sensitive |
| `PUT /admin/questions/{id}` | 50 requests | 1 hour | Content modification, moderate use |

**Implementation (Redis):**
```python
# apps/api/src/middleware/rate_limit_middleware.py
from fastapi import Request, HTTPException
import redis

async def rate_limit_admin(
    request: Request,
    limit: int,
    window_seconds: int,
    admin = Depends(require_admin)
):
    """
    Rate limit admin endpoint per admin user.
    """
    key = f"rate_limit:admin:{admin.id}:{request.url.path}"
    current = await redis.incr(key)

    if current == 1:
        await redis.expire(key, window_seconds)

    if current > limit:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Try again in {window_seconds}s."
        )

# Usage
@router.post("/admin/impersonate/{user_id}")
async def impersonate_user(
    user_id: UUID,
    admin = Depends(require_admin),
    _rate_limit = Depends(lambda req: rate_limit_admin(req, limit=10, window_seconds=3600))
):
    ...
```

#### Audit Trail

**Comprehensive Logging:**

All admin actions automatically logged to `admin_audit_log` table:

**Schema:**
```sql
CREATE TABLE admin_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    admin_id UUID NOT NULL REFERENCES users(id),
    action_type VARCHAR(50) NOT NULL,  -- 'impersonate', 'user_search', 'content_edit', etc.
    target_user_id UUID REFERENCES users(id),  -- For user-specific actions
    target_resource_id UUID,  -- For content modifications (question_id, chunk_id, etc.)
    metadata JSONB,  -- Action-specific metadata
    ip_address INET NOT NULL,
    user_agent TEXT,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    duration_seconds INTEGER,  -- For impersonation sessions

    INDEX idx_admin_audit_admin_id (admin_id),
    INDEX idx_admin_audit_action_type (action_type),
    INDEX idx_admin_audit_timestamp (timestamp DESC)
);
```

**Logged Actions:**
- `impersonate` - User impersonation start
- `impersonate_exit` - User impersonation end
- `user_search` - User search query (including search term)
- `user_view` - Viewing user detail page
- `content_edit` - Question/chunk modification
- `content_delete` - Question/chunk deletion (soft delete)

**Audit Log Access:**
- Accessible via `GET /admin/audit-log` (admin-only)
- Exportable to CSV for compliance review
- Retention: 2 years (compliance requirement)

**Security Monitoring:**
- Alert if single admin performs >20 impersonations in 24 hours (unusual activity)
- Alert if impersonation duration >25 minutes (approaching limit)
- Daily audit report emailed to security team

#### Admin Session Management

**Admin-Specific Token Handling:**
- Admin tokens have `is_admin: true` claim
- Shorter expiration for admin tokens: 60 minutes (vs 15 min for regular users)
- Admin refresh tokens: 24 hours (vs 7 days for regular users)
- Admin logout invalidates ALL admin sessions (including impersonations)

#### PostHog Integration Security

**Deep Links:**
- PostHog URLs include user_id only (no PII in URL)
- PostHog access restricted to admin team (SSO integration)
- URLs generated server-side (not exposed to client for non-admins)

```python
def generate_posthog_url(user_id: UUID) -> str:
    """Generate PostHog deep link for user profile."""
    base_url = settings.POSTHOG_URL  # From environment
    return f"{base_url}/person/{user_id}"

# Only included in admin API responses
```

#### Security Checklist (Pre-Release)

- [ ] Admin flag can only be set via direct database update (verified: no API endpoint)
- [ ] `require_admin` middleware enforced on all admin routes
- [ ] Impersonation cannot target other admins (unit test coverage)
- [ ] Impersonation tokens expire in 30 minutes (non-refreshable)
- [ ] Impersonation banner shown on all pages during active session
- [ ] Rate limiting active on all admin endpoints (verified in staging)
- [ ] Audit log captures all admin actions (integration test coverage)
- [ ] Audit log retention configured (2 years)
- [ ] Security monitoring alerts configured (impersonation anomalies)
- [ ] Admin access documented in secure runbook (Confluence/Notion)

---

### Performance Optimization

**Frontend Performance:**
- **Bundle Size Target:** < 300 KB gzipped (initial load)
- **Loading Strategy:** Code splitting via React.lazy(), route-based chunks, Vite tree-shaking
- **Caching Strategy:** Service worker for static assets (future), API response caching via SWR/React Query (future)
- **Image Optimization:** WebP format, lazy loading, responsive images

**Backend Performance:**
- **Response Time Target:** < 200ms p95 for API endpoints, < 500ms for adaptive question selection (includes Qdrant query)
- **Database Optimization:** Indexes on all foreign keys and query filters, connection pooling (SQLAlchemy async pool), prepared statements
- **Caching Strategy:** Redis for user sessions, competency scores cached in PostgreSQL, Qdrant vector cache

**Qdrant Performance:**
- **HNSW Index:** m=16, ef_construct=100 (balance speed/accuracy)
- **Search Performance:** < 50ms for semantic search (3072-dim vectors, 1000+ questions)
- **Payload Filtering:** Index on `knowledge_area`, `difficulty` for fast filtered search

---

## Testing Strategy

### Testing Pyramid

```
        E2E Tests (5%)
       /            \
    Integration Tests (15%)
   /                    \
Frontend Unit (40%)   Backend Unit (40%)
```

**Test Distribution:**
- **Unit Tests:** 80% (frontend components + backend services)
- **Integration Tests:** 15% (API endpoints, database operations)
- **E2E Tests:** 5% (critical user journeys)

### Test Organization

**Frontend Tests (`apps/web/tests/`):**

```
apps/web/tests/
├── unit/
│   ├── components/
│   │   ├── QuestionCard.test.tsx
│   │   ├── CompetencyBar.test.tsx
│   │   └── ReadingCard.test.tsx
│   ├── hooks/
│   │   ├── useAuth.test.ts
│   │   └── useQuizSession.test.ts
│   └── services/
│       ├── quizService.test.ts
│       └── authService.test.ts
└── integration/
    ├── quiz-flow.test.tsx
    └── reading-library.test.tsx
```

**Backend Tests (`apps/api/tests/`):**

```
apps/api/tests/
├── unit/
│   ├── services/
│   │   ├── test_adaptive_engine.py
│   │   ├── test_spaced_repetition.py
│   │   └── test_auth_service.py
│   ├── repositories/
│   │   └── test_question_repository.py
│   └── utils/
│       ├── test_irt.py
│       └── test_sm2.py
├── integration/
│   ├── test_api_auth.py
│   ├── test_api_quiz.py
│   └── test_api_reading.py
└── conftest.py  # Pytest fixtures
```

**E2E Tests (`tests/e2e/`):**

```
tests/e2e/
├── onboarding-to-quiz.spec.ts
├── diagnostic-flow.spec.ts
├── quiz-session.spec.ts
├── post-session-review.spec.ts
└── reading-library.spec.ts
```

---

## Coding Standards

### Critical Fullstack Rules

- **Type Sharing:** Always define types in `packages/shared-types` and import from there - never duplicate type definitions between frontend/backend
- **API Calls:** Never make direct HTTP calls with axios in components - use the service layer (`quizService`, `authService`, etc.)
- **Environment Variables:** Access only through config objects, never `process.env` directly in components/services
- **Error Handling:** All API routes must use the standard error handler middleware - return consistent error format
- **State Updates:** Never mutate state directly in Zustand stores - use immutable update patterns
- **Database Access:** Never write raw SQL - use SQLAlchemy ORM and repository pattern exclusively
- **Async/Await:** All database and API operations must use async/await - no callbacks or .then() chains
- **Component Props:** Keep prop drilling to max 2 levels - use context or global state for deeper nesting

### Naming Conventions

| Element | Frontend | Backend | Example |
|---------|----------|---------|---------|
| **Components** | PascalCase | - | `UserProfile.tsx` |
| **Hooks** | camelCase with 'use' | - | `useAuth.ts` |
| **API Routes** | - | kebab-case | `/api/user-profile` |
| **Database Tables** | - | snake_case | `user_profiles` |
| **TypeScript Interfaces** | PascalCase | - | `interface User` |
| **Python Classes** | PascalCase | PascalCase | `class UserRepository` |
| **Functions/Methods** | camelCase | snake_case | `getUserById()` (TS), `get_user_by_id()` (Python) |
| **Constants** | UPPER_SNAKE_CASE | UPPER_SNAKE_CASE | `MAX_QUESTIONS` |
| **Env Variables** | UPPER_SNAKE_CASE | UPPER_SNAKE_CASE | `VITE_API_BASE_URL` |

---

## Error Handling Strategy

### Error Response Format

```typescript
interface ApiError {
  error: {
    code: string;           // VALIDATION_ERROR, AUTH_ERROR, etc.
    message: string;        // User-friendly message
    details?: Record<string, any>;  // Field-specific errors
    timestamp: string;      // ISO 8601
    request_id: string;     // For tracing
  };
}
```

### Frontend Error Handling

Axios interceptors handle errors globally, displaying user-friendly toast messages and logging to Sentry for monitoring.

### Backend Error Handling

FastAPI global exception handlers return consistent error format with request IDs for tracing and structured logging for debugging.

---

## Content Quality & Moderation

**Purpose:** Ensure question and reading content accuracy, relevance, and quality through systematic review and user feedback loops.

### Content Lifecycle

```
[Creation] → [Review] → [Publication] → [Monitoring] → [Update/Retire]
```

### Question Content Management

#### 1. Vendor Questions (Gold Standard)

**Source:** 500 CBAP questions from certified exam prep vendors

**Validation Process:**
- [ ] Verified by CBAP-certified subject matter expert (SME)
- [ ] Mapped to specific BABOK v3 sections
- [ ] Difficulty level assigned (1-5) based on SME assessment
- [ ] Explanations reviewed for accuracy and clarity
- [ ] Distractors (incorrect options) validated as plausible but incorrect

**Quality Metrics:**
- Target correctness rate: 50-70% (questions too easy or too hard flagged for review)
- User feedback rating: >80% "helpful"
- Report rate: <2% of users flag as incorrect

#### 2. LLM-Generated Questions (Variations)

**Generation Process:**
```python
# Prompt template for GPT-4
generate_question_variation(
    base_question=vendor_question,
    knowledge_area=ka,
    difficulty=difficulty,
    variation_type="rephrasing" | "context_change" | "difficulty_adjust"
)
```

**Review Workflow:**

| Stage | Reviewer | Criteria | SLA |
|-------|----------|----------|-----|
| **1. Auto-Validation** | GPT-4 self-check | Grammatical correctness, answer key consistency | Instant |
| **2. Similarity Check** | Qdrant vector search | Ensure variation is unique (>0.3 distance from base) | <1s |
| **3. Human Review** | CBAP SME (contract) | Content accuracy, BABOK alignment | 48 hours |
| **4. Pilot Testing** | Alpha user cohort | Correctness rate, user feedback | 7 days |

**Approval Criteria:**
- [ ] Passes similarity threshold (not duplicate)
- [ ] SME approves content (accuracy verified)
- [ ] Pilot correctness rate: 40-80% (within acceptable range)
- [ ] Zero "report as incorrect" flags during pilot

**Post-Launch Monitoring:**
- Questions with >90% correctness → Flag as "too easy", consider difficulty increase
- Questions with <30% correctness → Flag for review (possibly ambiguous or incorrect)
- Questions with >5% report rate → Immediate SME review

#### 3. User Feedback Mechanism

**In-App Feedback:**

```tsx
// After answer submission
<div className="feedback-actions">
  <button onClick={() => rateExplanation('helpful')}>
    👍 Helpful Explanation
  </button>
  <button onClick={() => rateExplanation('unhelpful')}>
    👎 Needs Improvement
  </button>
  <button onClick={() => openReportModal()}>
    🚩 Report Incorrect Question
  </button>
</div>
```

**Report Modal:**
```tsx
interface QuestionReport {
  question_id: UUID;
  user_id: UUID;
  issue_type: 'incorrect_answer' | 'ambiguous_wording' | 'outdated_content' | 'typo' | 'other';
  description: string;
  suggested_fix?: string;
  submitted_at: timestamp;
}
```

**Report Triage:**
- Reports auto-tagged by issue type
- Questions with 2+ reports in 7 days → Escalated to SME review queue
- High-severity reports (incorrect answer) → Immediate notification to content team
- Question temporarily hidden if 5+ reports in 24 hours (emergency removal)

### Reading Content Management

#### BABOK v3 Content Chunking

**Chunking Strategy:**
- Chunk size: 200-500 tokens (1-2 paragraphs)
- Chunk boundaries: Respect heading structure, don't break mid-concept
- Overlap: 50-token overlap between adjacent chunks (context preservation)

**Metadata Tagging:**
```python
chunk = {
    "id": UUID,
    "title": "5.2.4 Define Solution Scope",
    "content": "Markdown text...",
    "babok_section": "5.2.4",
    "knowledge_area": "Requirements Analysis and Design Definition",
    "concept_tags": ["Solution Scope", "Requirements", "Stakeholders"],
    "difficulty": 3,  # 1-5 scale
    "estimated_read_time_minutes": 4,
    "source": "BABOK v3 (2015)",
}
```

**Quality Assurance:**
- [ ] All chunks reference valid BABOK sections
- [ ] Concept tags align with exam blueprint
- [ ] No chunks <100 tokens (too short, lacks context)
- [ ] No chunks >800 tokens (too long, overwhelming)
- [ ] Reading time estimate validated (200 words/minute baseline)

#### Content Updates (BABOK Version Changes)

**Update Workflow:**
- Monitor IIBA for BABOK version releases
- On new version: Identify changed sections via diff analysis
- Update affected chunks within 30 days
- Notify users of content updates via in-app banner
- Maintain version history (rollback capability)

### Content Moderation Workflows

#### Daily Content Health Check (Automated)

```python
# Scheduled task: Daily 2am UTC
async def daily_content_health_check():
    # Flag questions with anomalous metrics
    flagged_questions = await db.execute("""
        SELECT id, text, avg_correct_rate, report_count
        FROM questions
        WHERE (avg_correct_rate < 0.30 OR avg_correct_rate > 0.90)
           OR report_count >= 2
           AND created_at > NOW() - INTERVAL '7 days'
    """)

    # Send report to content team
    await send_email(
        to="content@learnr.com",
        subject=f"Content Health Report - {flagged_questions.count()} Issues",
        body=generate_report(flagged_questions)
    )
```

#### Weekly SME Review (Manual)

**Agenda:**
- Review flagged questions from automated checks
- Review user reports (triage by severity)
- Approve pending LLM-generated questions
- Plan content updates for next sprint

**Approval Process:**
- SME marks questions as: "Approve", "Edit Required", "Retire"
- Edits applied by content editor
- Retired questions soft-deleted (historical data preserved)

### Content Metrics Dashboard (Admin)

**Key Metrics:**
- Total questions: 1,000 (500 vendor + 500 LLM)
- Average correctness rate by KA
- Questions flagged for review (count + list)
- User feedback sentiment (% helpful)
- Report resolution time (target: <48 hours)
- Content freshness (last BABOK update date)

**Admin UI:**
```
┌────────────────────────────────────────────────┐
│ Content Quality Dashboard                      │
├────────────────────────────────────────────────┤
│ Total Questions: 1,000                         │
│ Flagged for Review: 12                         │
│ Pending User Reports: 8                        │
│                                                │
│ Questions by Status:                           │
│  ✓ Active: 980                                 │
│  ⚠ Under Review: 12                            │
│  🚫 Retired: 8                                 │
│                                                │
│ User Feedback:                                 │
│  👍 Helpful: 87%                               │
│  👎 Needs Improvement: 10%                     │
│  🚩 Reported: 3%                               │
└────────────────────────────────────────────────┘
```

---

## Monitoring and Observability

### Service Level Objectives (SLOs)

**Purpose:** Define uptime and performance targets with clear escalation procedures.

#### Uptime SLAs by Environment

| Environment | Uptime Target | Downtime Budget (monthly) | Rationale |
|-------------|---------------|---------------------------|-----------|
| **MVP** (Days 1-30) | 95% | 36 hours | Development in progress, rapid iteration |
| **Beta** (Months 2-3) | 98% | 14.4 hours | Limited user base, tolerance for issues |
| **GA** (Month 4+) | 99% | 7.2 hours | Production-quality service, paying users |
| **Enterprise** (Future) | 99.9% | 43 minutes | SLA-backed service for enterprise customers |

**Planned Maintenance Windows:**
- Scheduled during low-traffic periods (Tuesday/Wednesday 2-4am UTC)
- Advance notice: 48 hours via in-app banner + email
- Max duration: 2 hours
- Excluded from SLA calculations

#### Performance SLOs

| Metric | Target | Measurement | Escalation Threshold |
|--------|--------|-------------|----------------------|
| **API Response Time (p95)** | <200ms | All API endpoints | Alert if >500ms for 5 min |
| **API Response Time (p99)** | <500ms | All API endpoints | Alert if >1000ms for 5 min |
| **Frontend Page Load (p95)** | <3 seconds | Lighthouse CI | Alert if >5s for 10 min |
| **Quiz Question Delivery** | <500ms | `/questions/next` endpoint | Alert if >1s for 5 min |
| **Adaptive Engine Latency** | <1 second | Competency update + next question | Alert if >2s for 5 min |
| **Vector Search (Qdrant)** | <50ms | Semantic search queries | Alert if >100ms for 5 min |

#### Error Rate SLOs

| Error Type | Target | Measurement | Escalation |
|------------|--------|-------------|------------|
| **API Error Rate (5xx)** | <1% | All API responses | Page on-call if >5% for 5 min |
| **Frontend JS Errors** | <1% | Sentry error rate vs sessions | Investigate if >2% for 15 min |
| **Database Query Errors** | <0.1% | PostgreSQL error logs | Page on-call if >1% for 5 min |
| **Authentication Failures** | <2% | Login/register endpoint failures | Alert if >10% for 5 min |

### Monitoring Stack

- **Frontend Monitoring:** Sentry (error tracking, performance monitoring)
- **Backend Monitoring:** Sentry (error tracking), Railway metrics (CPU, memory)
- **Error Tracking:** Sentry for both frontend and backend (unified dashboard)
- **Performance Monitoring:** Sentry Performance, PostHog session replay
- **Logs:** Structlog (backend), Railway logs, Vercel logs (frontend)

### Key Metrics

**Frontend Metrics:**
- **Core Web Vitals:** LCP < 2.5s, FID < 100ms, CLS < 0.1
- **JavaScript Errors:** Track via Sentry, alert on > 1% error rate
- **API Response Times:** Track p50, p95, p99 for all API calls
- **User Interactions:** PostHog events for quiz sessions, reading library usage

**Backend Metrics:**
- **Request Rate:** Requests per second (track normal baseline, alert on spikes)
- **Error Rate:** % of 5xx responses (alert if > 1%)
- **Response Time:** p50 < 100ms, p95 < 200ms, p99 < 500ms
- **Database Query Performance:** Track slow queries (> 100ms), optimize via indexes
- **Celery Task Metrics:** Task completion rate, queue length, failure rate

**Business Metrics (PostHog):**
- Daily active users (DAU)
- Quiz sessions completed per user
- Post-session review adoption rate (% of sessions with review)
- Reading library engagement (% of users opening reading items)
- Competency progression over time

---

## Architecture Complete

**✅ All 18 sections completed:**

1. ✅ Introduction
2. ✅ High Level Architecture
3. ✅ Tech Stack
4. ✅ Data Models
5. ✅ API Specification
6. ✅ Components
7. ✅ Core Workflows
8. ✅ Database Schema
9. ✅ Frontend Architecture
10. ✅ Backend Architecture
11. ✅ Unified Project Structure
12. ✅ Development Workflow
13. ✅ Deployment Architecture
14. ✅ Security and Performance
15. ✅ Testing Strategy
16. ✅ Coding Standards
17. ✅ Error Handling Strategy
18. ✅ Monitoring and Observability

---

**Document Status:** Complete and ready for implementation

**Next Steps:**
1. Share with development team for review
2. Use as reference during 30-day MVP development sprint
3. Update as architecture evolves based on implementation learnings

---

*Architecture document completed by Winston (Architect Agent) on November 21, 2025*
