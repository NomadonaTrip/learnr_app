# Tech Stack

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
| **Email Service** | SendGrid | Latest SDK (9.x) | Transactional emails (password reset, welcome) | Reliable delivery, 100 emails/day free tier, simple API, production-ready |
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
