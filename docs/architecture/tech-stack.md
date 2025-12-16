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

## Dependency File Specifications

> **Purpose:** Exact package specifications for AI agents to generate correct dependency files.

### Backend: requirements.txt

**Location:** `apps/api/requirements.txt`

```txt
# Core Framework
fastapi==0.109.2
uvicorn[standard]==0.27.1
pydantic==2.6.1
pydantic-settings==2.1.0

# Database
sqlalchemy==2.0.25
alembic==1.13.1
asyncpg==0.29.0
psycopg2-binary==2.9.9

# Authentication
pyjwt==2.8.0
bcrypt==4.1.2
python-multipart==0.0.9

# Redis & Background Jobs
redis==5.0.1
celery==5.3.6

# Vector Database
qdrant-client==1.7.3

# AI/ML
openai==1.12.0
numpy==1.26.4
scipy==1.12.0

# HTTP Client
httpx==0.26.0

# Email
sendgrid==6.11.0

# Monitoring & Logging
sentry-sdk[fastapi]==1.40.0
structlog==24.1.0

# Testing (dev dependencies)
pytest==7.4.4
pytest-asyncio==0.23.4
pytest-cov==4.1.0
httpx==0.26.0
factory-boy==3.3.0

# Code Quality (dev dependencies)
ruff==0.2.1
black==24.2.0
mypy==1.8.0

# Utilities
python-dotenv==1.0.1
tenacity==8.2.3
```

### Backend: pyproject.toml (alternative)

**Location:** `apps/api/pyproject.toml`

```toml
[project]
name = "learnr-api"
version = "1.0.0"
description = "LearnR Adaptive Learning API"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.109.0,<0.110.0",
    "uvicorn[standard]>=0.27.0,<0.28.0",
    "pydantic>=2.6.0,<2.7.0",
    "pydantic-settings>=2.1.0,<2.2.0",
    "sqlalchemy>=2.0.25,<2.1.0",
    "alembic>=1.13.0,<1.14.0",
    "asyncpg>=0.29.0,<0.30.0",
    "pyjwt>=2.8.0,<2.9.0",
    "bcrypt>=4.1.0,<4.2.0",
    "redis>=5.0.0,<5.1.0",
    "celery>=5.3.0,<5.4.0",
    "qdrant-client>=1.7.0,<1.8.0",
    "openai>=1.12.0,<2.0.0",
    "numpy>=1.26.0,<1.27.0",
    "scipy>=1.12.0,<1.13.0",
    "httpx>=0.26.0,<0.27.0",
    "sendgrid>=6.11.0,<7.0.0",
    "sentry-sdk[fastapi]>=1.40.0,<2.0.0",
    "structlog>=24.1.0,<25.0.0",
    "python-dotenv>=1.0.0,<2.0.0",
    "tenacity>=8.2.0,<9.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0,<8.0.0",
    "pytest-asyncio>=0.23.0,<0.24.0",
    "pytest-cov>=4.1.0,<5.0.0",
    "factory-boy>=3.3.0,<4.0.0",
    "ruff>=0.2.0,<0.3.0",
    "black>=24.2.0,<25.0.0",
    "mypy>=1.8.0,<2.0.0",
]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.black]
line-length = 100
target-version = ["py311"]

[tool.mypy]
python_version = "3.11"
strict = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

### Frontend: package.json

**Location:** `apps/web/package.json`

```json
{
  "name": "learnr-web",
  "version": "1.0.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "lint:fix": "eslint . --ext ts,tsx --fix",
    "format": "prettier --write \"src/**/*.{ts,tsx,css}\"",
    "test": "vitest",
    "test:coverage": "vitest --coverage",
    "test:e2e": "playwright test",
    "type-check": "tsc --noEmit"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.21.3",
    "@tanstack/react-query": "^5.17.19",
    "zustand": "^4.5.0",
    "axios": "^1.6.7",
    "react-hook-form": "^7.49.3",
    "zod": "^3.22.4",
    "@hookform/resolvers": "^3.3.4",
    "@headlessui/react": "^1.7.18",
    "@heroicons/react": "^2.1.1",
    "clsx": "^2.1.0",
    "date-fns": "^3.3.1"
  },
  "devDependencies": {
    "@types/react": "^18.2.48",
    "@types/react-dom": "^18.2.18",
    "@typescript-eslint/eslint-plugin": "^6.20.0",
    "@typescript-eslint/parser": "^6.20.0",
    "@vitejs/plugin-react": "^4.2.1",
    "autoprefixer": "^10.4.17",
    "eslint": "^8.56.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.5",
    "postcss": "^8.4.35",
    "prettier": "^3.2.4",
    "tailwindcss": "^3.4.1",
    "typescript": "^5.3.3",
    "vite": "^5.0.12",
    "vitest": "^1.2.2",
    "@vitest/coverage-v8": "^1.2.2",
    "@testing-library/react": "^14.2.1",
    "@testing-library/jest-dom": "^6.4.0",
    "@testing-library/user-event": "^14.5.2",
    "jsdom": "^24.0.0",
    "@playwright/test": "^1.41.2",
    "msw": "^2.1.5"
  },
  "engines": {
    "node": ">=18.0.0",
    "npm": ">=10.0.0"
  }
}
```

### Frontend: tsconfig.json

**Location:** `apps/web/tsconfig.json`

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,

    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",

    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,

    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"],
      "@/components/*": ["src/components/*"],
      "@/hooks/*": ["src/hooks/*"],
      "@/services/*": ["src/services/*"],
      "@/stores/*": ["src/stores/*"],
      "@/types/*": ["src/types/*"],
      "@/utils/*": ["src/utils/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

### Frontend: vite.config.ts

**Location:** `apps/web/vite.config.ts`

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom', 'react-router-dom'],
          query: ['@tanstack/react-query'],
          ui: ['@headlessui/react', '@heroicons/react'],
        },
      },
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
    },
  },
})
```

### Frontend: tailwind.config.js

**Location:** `apps/web/tailwind.config.js`

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      colors: {
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        },
        // Knowledge Area colors
        'ka-planning': '#3B82F6',
        'ka-elicitation': '#10B981',
        'ka-rlcm': '#F59E0B',
        'ka-strategy': '#EF4444',
        'ka-radd': '#8B5CF6',
        'ka-solution': '#EC4899',
      },
      borderRadius: {
        'card': '14px',  // Design system standard
      },
      spacing: {
        '22': '5.5rem',  // 88px - design system
      },
    },
  },
  plugins: [],
}
```

### Docker: Dockerfile (Backend)

**Location:** `infrastructure/docker/Dockerfile.api`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY apps/api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY apps/api/src ./src

# Set environment variables
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker: docker-compose.dev.yml

**Location:** `infrastructure/docker/docker-compose.dev.yml`

```yaml
version: '3.8'

services:
  api:
    build:
      context: ../..
      dockerfile: infrastructure/docker/Dockerfile.api
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/learnr
      - REDIS_URL=redis://redis:6379/0
      - QDRANT_URL=http://qdrant:6333
      - JWT_SECRET=dev-secret-change-in-production
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - db
      - redis
      - qdrant
    volumes:
      - ../../apps/api/src:/app/src

  db:
    image: postgres:15-alpine
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=learnr
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7.2-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  qdrant:
    image: qdrant/qdrant:v1.7.3
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_data:/qdrant/storage

  celery:
    build:
      context: ../..
      dockerfile: infrastructure/docker/Dockerfile.api
    command: celery -A src.tasks worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/learnr
      - REDIS_URL=redis://redis:6379/0
      - QDRANT_URL=http://qdrant:6333
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - db
      - redis
      - qdrant

volumes:
  postgres_data:
  redis_data:
  qdrant_data:
```

---

## Dependency Management

### Update Strategy

**Cadence:**
- **Security patches:** Immediate (within 24 hours of disclosure)
- **Minor versions:** Monthly review, apply if tests pass
- **Major versions:** Quarterly assessment, staged rollout via staging environment

**Automation:**
- Dependabot configured for automated PR creation
- GitHub Actions runs full test suite on dependency update PRs
- Auto-merge enabled for patch versions with passing tests

### Dependabot Configuration

```yaml
# .github/dependabot.yml
version: 2
updates:
  # Frontend dependencies (npm)
  - package-ecosystem: "npm"
    directory: "/apps/web"
    schedule:
      interval: "weekly"
      day: "monday"
    open-pull-requests-limit: 10
    groups:
      react-ecosystem:
        patterns:
          - "react*"
          - "@types/react*"
      testing:
        patterns:
          - "vitest*"
          - "@testing-library/*"
          - "playwright*"
    ignore:
      # Ignore major version updates for core framework (manual review)
      - dependency-name: "react"
        update-types: ["version-update:semver-major"]
      - dependency-name: "react-router-dom"
        update-types: ["version-update:semver-major"]

  # Backend dependencies (pip)
  - package-ecosystem: "pip"
    directory: "/apps/api"
    schedule:
      interval: "weekly"
      day: "monday"
    open-pull-requests-limit: 10
    groups:
      fastapi-ecosystem:
        patterns:
          - "fastapi*"
          - "pydantic*"
          - "uvicorn*"
      testing:
        patterns:
          - "pytest*"
          - "httpx*"
    ignore:
      - dependency-name: "sqlalchemy"
        update-types: ["version-update:semver-major"]

  # GitHub Actions
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"

  # Docker base images
  - package-ecosystem: "docker"
    directory: "/infrastructure/docker"
    schedule:
      interval: "monthly"
```

### License Compliance

**Approved Licenses:**
- MIT License ✅
- Apache License 2.0 ✅
- BSD (2-clause, 3-clause) ✅
- ISC License ✅
- Python Software Foundation License ✅

**Requires Review:**
- GPL (any version) - Copyleft concerns
- LGPL - Review for linking requirements
- AGPL - Network copyleft concerns

**Prohibited:**
- Proprietary/Commercial without license
- CC-BY-NC (Non-commercial restriction)

**License Audit Tool:**
```bash
# Frontend license audit
npx license-checker --summary --production

# Backend license audit
pip-licenses --format=markdown --with-urls
```

**Current Audit Status:**

| Package | License | Status |
|---------|---------|--------|
| React | MIT | ✅ Approved |
| FastAPI | MIT | ✅ Approved |
| SQLAlchemy | MIT | ✅ Approved |
| Pydantic | MIT | ✅ Approved |
| Qdrant Client | Apache 2.0 | ✅ Approved |
| OpenAI SDK | MIT | ✅ Approved |
| TailwindCSS | MIT | ✅ Approved |
| Celery | BSD-3-Clause | ✅ Approved |
| Redis (py) | MIT | ✅ Approved |
| Axios | MIT | ✅ Approved |
| Zustand | MIT | ✅ Approved |

**Automated Enforcement:**
```yaml
# .github/workflows/license-check.yml
name: License Compliance Check
on: [push, pull_request]

jobs:
  check-licenses:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Check frontend licenses
        run: |
          cd apps/web
          npm ci
          npx license-checker --failOn "GPL;AGPL;LGPL;UNLICENSED"

      - name: Check backend licenses
        run: |
          cd apps/api
          pip install pip-licenses
          pip-licenses --fail-on="GPL;AGPL"
```

---

## Vendor Lock-in Assessment

### Risk Matrix

| Service | Lock-in Risk | Data Portability | Migration Effort | Mitigation Strategy |
|---------|--------------|------------------|------------------|---------------------|
| **Vercel** | Low | N/A (static hosting) | 1-2 hours | Standard Next.js/Vite build, any CDN works |
| **Railway** | Low | Docker containers | 2-4 hours | Standard Docker, portable to any container host |
| **Supabase** | Medium | PostgreSQL export | 4-8 hours | Standard PostgreSQL, can migrate to RDS/Cloud SQL |
| **Qdrant Cloud** | Medium | Collection export API | 8-16 hours | Standard vectors, can migrate to Pinecone/Weaviate |
| **OpenAI** | High | N/A (API service) | 40-80 hours | Abstract via interface, swap to Azure OpenAI/Anthropic |
| **SendGrid** | Low | N/A (API service) | 2-4 hours | Standard SMTP, swap to SES/Mailgun |
| **PostHog** | Low | Event export | 4-8 hours | Self-hosted option, swap to Amplitude/Mixpanel |
| **Sentry** | Low | N/A (monitoring) | 2-4 hours | Swap to Datadog/New Relic |
| **Redis (Railway)** | Low | RDB dump | 1-2 hours | Standard Redis protocol, any Redis host |

### Portability Strategies

#### Database (Supabase → AWS RDS)

**Current State:** Supabase PostgreSQL with managed backups

**Migration Path:**
1. Export schema via `pg_dump --schema-only`
2. Export data via `pg_dump --data-only`
3. Create RDS PostgreSQL instance
4. Import schema and data
5. Update `DATABASE_URL` environment variable
6. Test all queries and migrations

**Abstraction Layer:** SQLAlchemy ORM ensures database-agnostic queries

#### Vector Database (Qdrant → Pinecone)

**Current State:** Qdrant Cloud with 2 collections (questions, reading_chunks)

**Migration Path:**
1. Export vectors via Qdrant scroll API
2. Transform payload format (minimal changes)
3. Create Pinecone index with same dimensions (3072)
4. Bulk upsert vectors
5. Update `VectorSearchService` to use Pinecone client

**Abstraction Recommendation:**
```python
# apps/api/src/services/vector_store.py
from abc import ABC, abstractmethod

class VectorStore(ABC):
    """Abstract vector store interface for portability."""

    @abstractmethod
    async def search(self, vector: List[float], limit: int) -> List[SearchResult]:
        pass

    @abstractmethod
    async def upsert(self, id: str, vector: List[float], payload: dict) -> None:
        pass

class QdrantVectorStore(VectorStore):
    """Qdrant implementation."""
    pass

class PineconeVectorStore(VectorStore):
    """Pinecone implementation (for migration)."""
    pass
```

#### LLM Provider (OpenAI → Azure OpenAI / Anthropic)

**Current State:** Direct OpenAI API calls for embeddings

**Migration Path:**
1. Azure OpenAI: Same API, change base URL and auth
2. Anthropic: Different API, requires code changes

**Abstraction Recommendation:**
```python
# apps/api/src/services/llm_provider.py
from abc import ABC, abstractmethod

class EmbeddingProvider(ABC):
    """Abstract embedding provider for portability."""

    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        pass

    @abstractmethod
    def get_dimension(self) -> int:
        pass

class OpenAIEmbedding(EmbeddingProvider):
    """OpenAI text-embedding-3-large (3072 dim)."""
    pass

class AzureOpenAIEmbedding(EmbeddingProvider):
    """Azure OpenAI (same API, different auth)."""
    pass

class CohereEmbedding(EmbeddingProvider):
    """Cohere embed-english-v3.0 (1024 dim) - requires re-indexing."""
    pass
```

#### Hosting (Railway → AWS ECS)

**Current State:** Railway Docker deployment with auto-scaling

**Migration Path:**
1. Dockerfiles already exist and are portable
2. Create ECS task definitions from Docker Compose
3. Set up ALB for load balancing
4. Configure RDS, ElastiCache, S3
5. Update CI/CD to deploy to ECS

**Timeline:** Documented in deployment-architecture.md as "Future AWS Migration"

### Lock-in Mitigation Checklist

- [x] Database access via ORM (SQLAlchemy) - no raw SQL vendor extensions
- [x] Docker containers for compute - portable to any container host
- [x] Standard PostgreSQL - no Supabase-specific features used
- [ ] Vector store abstraction interface - **Recommended**
- [ ] LLM provider abstraction interface - **Recommended**
- [x] Environment variables for all service URLs - easy endpoint swapping
- [x] No proprietary file formats - JSON, CSV, standard SQL

---

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-12-08 | 1.2 | Added Dependency File Specifications section with complete requirements.txt, package.json, tsconfig.json, vite.config.ts, tailwind.config.js, Dockerfile, docker-compose.dev.yml for AI agent implementation | Winston (Architect) |
| 2025-12-08 | 1.1 | Added Dependency Management section (update strategy, Dependabot config, license compliance, automated enforcement); Added Vendor Lock-in Assessment (risk matrix, portability strategies, abstraction recommendations) | Winston (Architect) |
| 2025-11-01 | 1.0 | Initial tech stack | Original |
