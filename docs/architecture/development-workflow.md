# Development Workflow

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
