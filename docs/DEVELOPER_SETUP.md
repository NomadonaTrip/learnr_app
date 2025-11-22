# Developer Setup Guide

Complete guide for setting up your LearnR development environment.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Obtain API Keys](#obtain-api-keys)
3. [Configure Environment Variables](#configure-environment-variables)
4. [Install Dependencies](#install-dependencies)
5. [Set Up Database](#set-up-database)
6. [Run Development Servers](#run-development-servers)
7. [Verify Setup](#verify-setup)
8. [Running Tests](#running-tests)
9. [Offline Development Mode](#offline-development-mode)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Ensure you have the following installed:

- **Node.js** 18.x or higher ([Download](https://nodejs.org/))
- **Python** 3.11.x ([Download](https://www.python.org/downloads/))
- **Docker Desktop** ([Download](https://www.docker.com/products/docker-desktop))
- **Git** ([Download](https://git-scm.com/downloads))

Verify installations:
```bash
node --version  # Should be v18.x or higher
python --version  # Should be 3.11.x
docker --version  # Should be 24.x or higher
git --version
```

---

## Obtain API Keys

### Required Services (Must Complete Before Development)

#### 1. OpenAI API Key

**Purpose:** LLM content generation + embeddings for semantic search
**Cost:** $1-5/month for development testing (pay-as-you-go)

**Steps:**
1. Sign up at https://platform.openai.com/signup
2. Add payment method (required, even for testing)
   - Navigate to **Billing** → **Add Payment Method**
   - Add at least $5 credit for testing
3. Navigate to https://platform.openai.com/api-keys
4. Click **"Create new secret key"**
5. Name: `LearnR Development - [Your Name]`
6. **Important:** Copy key immediately (starts with `sk-...`)
7. Save to your password manager (won't be shown again)

**Environment Variable:**
```bash
OPENAI_API_KEY=sk-proj-...your-key-here...
```

---

#### 2. Qdrant Cloud API Key

**Purpose:** Vector database for semantic search (questions + reading content)
**Cost:** Free (1M vectors, sufficient for MVP)

**Steps:**
1. Sign up at https://cloud.qdrant.io/
2. Create free cluster:
   - Cluster name: `learnr-dev-[yourname]`
   - Region: Choose closest (US/EU)
   - Tier: **Free** (1M vectors)
3. Wait for cluster provisioning (~2 minutes)
4. Navigate to cluster → **Settings** → **API Keys**
5. Copy:
   - **Cluster URL** (e.g., `https://abc123.us-east.aws.cloud.qdrant.io:6333`)
   - **API Key** (click "Show" to reveal)

**Environment Variables:**
```bash
QDRANT_URL=https://your-cluster.cloud.qdrant.io:6333
QDRANT_API_KEY=your-api-key-here
```

---

#### 3. PostHog Project API Key

**Purpose:** Product analytics, session replay, feature flags
**Cost:** Free (1M events/month)

**Steps:**
1. Sign up at https://posthog.com/signup
2. Create project:
   - Project name: `LearnR Development`
   - Select: **Cloud (US)** or **Cloud (EU)**
3. Navigate to **Project Settings** → **Project** → **API Keys**
4. Copy **Project API Key** (starts with `phc_...`)

**Environment Variable:**
```bash
POSTHOG_API_KEY=phc_...your-key-here...
```

**Optional:** For local development, you can disable PostHog:
```bash
POSTHOG_ENABLED=false
```

---

#### 4. Sentry DSN

**Purpose:** Error tracking and performance monitoring
**Cost:** Free (5K errors/month)

**Steps:**
1. Sign up at https://sentry.io/signup
2. Create project:
   - Platform: **Python / FastAPI**
   - Project name: `LearnR API`
3. Copy **DSN** from project settings (looks like `https://abc123@o123.ingest.sentry.io/123`)

**Environment Variable:**
```bash
SENTRY_DSN=https://abc123@o123.ingest.sentry.io/123
```

**Optional:** For local development, you can disable Sentry:
```bash
SENTRY_ENABLED=false
```

---

#### 5. SendGrid API Key

**Purpose:** Transactional emails (password reset, welcome emails)
**Cost:** Free (100 emails/day)

**Steps:**
1. Sign up at https://sendgrid.com/
2. **Complete sender verification:**
   - Navigate to **Settings** → **Sender Authentication**
   - Click **Verify a Single Sender**
   - Use: `noreply@learnr.com` (or your domain)
   - Verify via email confirmation
3. Navigate to **Settings** → **API Keys**
4. Click **Create API Key**
5. Name: `LearnR Development`
6. Permissions: **Full Access** (for development)
7. Copy API key (starts with `SG.`)

**Environment Variables:**
```bash
SENDGRID_API_KEY=SG.your-api-key-here
FROM_EMAIL=noreply@learnr.com
```

---

#### 6. Supabase Database Credentials

**Purpose:** PostgreSQL database (user data, responses, sessions)
**Cost:** Free (500MB database, 2GB bandwidth)

**Steps:**
1. Sign up at https://supabase.com/
2. Create new project:
   - Name: `learnr-dev-[yourname]`
   - Database password: Generate strong password (save it!)
   - Region: Choose closest
3. Wait for provisioning (~2 minutes)
4. Navigate to **Settings** → **Database**
5. Copy **Connection String** (URI format)
   - Replace `[YOUR-PASSWORD]` with your database password

**Environment Variable:**
```bash
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.xxx.supabase.co:5432/postgres
```

---

#### 7. Railway Redis (Optional for Local Dev)

**Purpose:** Session cache, rate limiting, background job queue
**Cost:** $5 credit/month free

**Options:**

**Option A: Use Local Redis via Docker (Recommended for Development)**
```bash
# Redis will run via docker-compose.dev.yml
# No API key needed
REDIS_URL=redis://localhost:6379
```

**Option B: Use Railway Hosted Redis**
1. Sign up at https://railway.app
2. Create new project → Add Redis
3. Copy connection URL from Redis service settings

```bash
REDIS_URL=redis://default:password@redis.railway.internal:6379
```

---

## Configure Environment Variables

### Backend Environment (.env)

1. Create backend `.env` file:
   ```bash
   cp apps/api/.env.example apps/api/.env
   ```

2. Edit `apps/api/.env` with your API keys:
   ```bash
   # OpenAI
   OPENAI_API_KEY=sk-proj-...

   # Qdrant
   QDRANT_URL=https://your-cluster.cloud.qdrant.io:6333
   QDRANT_API_KEY=...

   # Database
   DATABASE_URL=postgresql://postgres:...@db.xxx.supabase.co:5432/postgres

   # Redis (local or Railway)
   REDIS_URL=redis://localhost:6379

   # Email
   SENDGRID_API_KEY=SG....
   FROM_EMAIL=noreply@learnr.com

   # Analytics (optional for dev)
   POSTHOG_API_KEY=phc_...
   POSTHOG_ENABLED=false  # Disable for local dev

   # Error Tracking (optional for dev)
   SENTRY_DSN=https://...
   SENTRY_ENABLED=false  # Disable for local dev

   # App Config
   ENVIRONMENT=development
   DEBUG=true
   SECRET_KEY=your-secret-key-for-jwt-signing
   FRONTEND_URL=http://localhost:5173
   ```

### Frontend Environment (.env)

1. Create frontend `.env` file:
   ```bash
   cp apps/web/.env.example apps/web/.env
   ```

2. Edit `apps/web/.env`:
   ```bash
   VITE_API_URL=http://localhost:8000
   VITE_POSTHOG_KEY=phc_...  # Optional
   VITE_ENVIRONMENT=development
   ```

---

## Install Dependencies

### Backend Dependencies

```bash
cd apps/api

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "import fastapi; print(fastapi.__version__)"
```

### Frontend Dependencies

```bash
cd apps/web

# Install dependencies
npm install

# Verify installation
npm list react
```

---

## Set Up Database

### Run Database Migrations

```bash
cd apps/api

# Ensure virtual environment is activated
source venv/bin/activate

# Run migrations
alembic upgrade head

# Verify migrations
alembic current
```

### Seed Database (Optional)

Load sample questions and BABOK content:

```bash
# Seed questions (500-1000 CBAP questions)
python scripts/seed-questions.py

# Generate embeddings for questions
python scripts/generate-embeddings.py --type questions

# Seed BABOK reading chunks
python scripts/seed-reading-content.py

# Generate embeddings for reading chunks
python scripts/generate-embeddings.py --type reading
```

**Note:** Embedding generation may take 10-15 minutes and cost ~$3-4 in OpenAI API calls.

---

## Run Development Servers

### Start Local Services (Redis, PostgreSQL, Qdrant)

**Option 1: Use Docker Compose (Recommended)**

```bash
# From project root
docker-compose -f infrastructure/docker/docker-compose.dev.yml up -d

# Verify services are running
docker ps
```

**Option 2: Use Cloud Services**
- Use Supabase for PostgreSQL (already configured)
- Use Qdrant Cloud (already configured)
- Use Railway for Redis or local Redis

### Start Backend Server

```bash
cd apps/api
source venv/bin/activate

# Run FastAPI server with hot reload
uvicorn src.main:app --reload --port 8000

# Server will start at http://localhost:8000
# API docs available at http://localhost:8000/docs
```

### Start Frontend Server

```bash
cd apps/web

# Run Vite dev server
npm run dev

# Server will start at http://localhost:5173
```

### Access the Application

- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs
- **Redoc:** http://localhost:8000/redoc

---

## Verify Setup

### Health Check

Test backend health endpoint:
```bash
curl http://localhost:8000/health

# Expected response:
# {"status": "healthy", "timestamp": "..."}
```

Test frontend is accessible:
```bash
# Open in browser
open http://localhost:5173  # macOS
# or
start http://localhost:5173  # Windows
# or visit manually
```

---

## Running Tests

LearnR has comprehensive test coverage across frontend, backend, and E2E tests.

### Frontend Tests (Vitest + React Testing Library)

**Run all tests:**
```bash
cd apps/web
npm run test
```

**Watch mode (re-runs on file changes):**
```bash
npm run test:watch
```

**Interactive UI mode:**
```bash
npm run test:ui
# Opens browser-based test UI at http://localhost:51204
```

**CI mode (with coverage):**
```bash
npm run test:ci
# Generates coverage report in apps/web/coverage/
```

**View coverage report:**
```bash
# After running npm run test:ci
open coverage/index.html  # macOS
# or
start coverage/index.html  # Windows
```

**Coverage thresholds:** 80% minimum (lines, functions, branches, statements)

---

### Backend Tests (pytest + httpx)

**Run all tests:**
```bash
cd apps/api
pytest
```

**Run with coverage:**
```bash
pytest --cov=src --cov-report=html
# Generates coverage report in apps/api/htmlcov/
```

**Run with coverage (terminal output):**
```bash
pytest --cov=src --cov-report=term-missing
# Shows missing lines in terminal
```

**Run specific test file:**
```bash
pytest tests/test_health.py
```

**Run specific test function:**
```bash
pytest tests/test_health.py::test_health_check_returns_200
```

**Run tests by marker:**
```bash
pytest -m unit           # Only unit tests
pytest -m integration    # Only integration tests
pytest -m api            # Only API tests
pytest -m auth           # Only auth tests
pytest -m "not slow"     # Exclude slow tests
```

**Available markers:**
- `unit` - Unit tests (isolated, fast)
- `integration` - Integration tests (database, external services)
- `slow` - Slow tests (>1 second)
- `api` - API endpoint tests
- `database` - Database tests
- `auth` - Authentication tests
- `email` - Email service tests
- `openai` - OpenAI integration tests
- `qdrant` - Qdrant vector DB tests

**Run tests in parallel:**
```bash
pytest -n auto  # Uses all CPU cores
pytest -n 4     # Uses 4 workers
```

**Run verbose output:**
```bash
pytest -v  # Verbose
pytest -vv # Very verbose
```

**View coverage report:**
```bash
# After running pytest --cov=src --cov-report=html
open htmlcov/index.html  # macOS
# or
start htmlcov/index.html  # Windows
```

**Coverage threshold:** 80% minimum

---

### E2E Tests (Playwright)

**Run all E2E tests:**
```bash
# From project root
npm run test:e2e

# Or with Playwright directly
npx playwright test
```

**Run in UI mode (recommended for development):**
```bash
npm run playwright:ui
# Opens interactive Playwright UI for debugging
```

**Run specific test file:**
```bash
npx playwright test tests/e2e/homepage.spec.ts
```

**Run specific browser:**
```bash
npx playwright test --project=chromium
npx playwright test --project=firefox
npx playwright test --project=webkit
```

**Run in headed mode (see browser):**
```bash
npx playwright test --headed
```

**Debug mode (step through tests):**
```bash
npx playwright test --debug
```

**View test report:**
```bash
npm run playwright:report
# Opens HTML report in browser
```

**Update snapshots (if using visual regression):**
```bash
npx playwright test --update-snapshots
```

**Prerequisites for E2E tests:**
1. Backend must be running on `http://localhost:8000`
2. Frontend must be running on `http://localhost:5173`
3. Database must be seeded with test data

**Playwright configuration:** See `playwright.config.ts` for timeout, retries, and browser settings.

---

### Run All Tests (Full Test Suite)

**From project root:**
```bash
npm run test
# Runs: frontend tests → backend tests → E2E tests
```

**Run tests in CI mode:**
```bash
npm run test:ci
# Runs frontend and backend with coverage, skips E2E
```

**Individual test suites:**
```bash
npm run test:frontend     # Frontend only
npm run test:backend      # Backend only
npm run test:e2e          # E2E only
```

---

### CI/CD Test Requirements

**What runs on every PR:**
1. ✅ Frontend linting (`npm run lint`)
2. ✅ Frontend type checking (`npm run type-check`)
3. ✅ Frontend tests with coverage (`npm run test:ci`)
4. ✅ Backend linting (`ruff check src/`)
5. ✅ Backend type checking (`mypy src/`)
6. ✅ Backend tests with coverage (`pytest --cov=src`)
7. ✅ E2E tests (after unit tests pass)
8. ✅ Frontend build check (`npm run build`)

**Coverage requirements:**
- Frontend: 80% minimum
- Backend: 80% minimum
- Uploads to Codecov (if configured)

**Test services in CI:**
- PostgreSQL 15 (service container)
- Redis 7.2 (service container)
- Mock OpenAI (via `USE_MOCK_OPENAI=true`)
- Mock Email (via `USE_MOCK_EMAIL=true`)

**All tests must pass before merging to `main` or `develop`.**

---

### Test Best Practices

**1. Write tests for new features:**
```bash
# Feature: Add new user registration endpoint
# Tests required:
# - Unit tests for validation logic
# - Integration tests for API endpoint
# - E2E tests for user flow
```

**2. Run tests before committing:**
```bash
# Quick check (frontend + backend unit tests)
cd apps/web && npm run test && cd ../..
cd apps/api && pytest -m "not slow" && cd ../..
```

**3. Use watch mode during development:**
```bash
# Frontend (auto-runs on file changes)
cd apps/web && npm run test:watch

# Backend (using pytest-watch)
cd apps/api && ptw  # pip install pytest-watch
```

**4. Debug failing tests:**
```bash
# Frontend: Use Vitest UI
npm run test:ui

# Backend: Use pytest verbose mode
pytest -vv tests/path/to/failing_test.py

# E2E: Use Playwright debug mode
npx playwright test --debug tests/e2e/failing.spec.ts
```

**5. Check coverage gaps:**
```bash
# Frontend
npm run test:ci
open coverage/index.html

# Backend
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

**6. Mock external services:**
```bash
# In tests, always use mocks for:
# - OpenAI API (use mock_openai_service fixture)
# - Email service (use mock_email_service fixture)
# - Qdrant (use in-memory mock)
# - External APIs (use responses library)
```

**7. Test naming conventions:**
```python
# Backend (pytest)
def test_user_registration_with_valid_email():
    # Given: valid email
    # When: user registers
    # Then: user is created

# Frontend (Vitest)
it('should show error message for invalid email', () => {
    // Arrange
    // Act
    // Assert
})
```

---

## Offline Development Mode

Develop without internet access or to avoid external API costs.

### Enable Offline Mode

1. **Start local services:**
   ```bash
   docker-compose -f infrastructure/docker/docker-compose.dev.yml up -d
   ```

2. **Configure offline environment:**
   ```bash
   # In apps/api/.env
   USE_MOCK_OPENAI=true
   USE_MOCK_EMAIL=true
   OPENAI_API_BASE=http://localhost:8001  # Mock OpenAI service
   ```

3. **Start development servers as normal**

### What Works Offline?

✅ **Works:**
- Question selection (uses mock embeddings)
- Answer submission and feedback
- Competency calculation
- Reading content retrieval (local Qdrant)
- All UI development
- Database operations
- API development

❌ **Doesn't Work (Uses Mock Data):**
- LLM-generated explanations (returns canned responses)
- Email sending (logs to console instead)
- Analytics (no-op)
- Real embedding generation (uses deterministic mock vectors)

---

## Troubleshooting

### Q: "ModuleNotFoundError: No module named 'fastapi'"

**A:** Virtual environment not activated or dependencies not installed.

```bash
cd apps/api
source venv/bin/activate
pip install -r requirements.txt
```

---

### Q: OpenAI API key not working - 401 Unauthorized

**A:** Ensure you've added a payment method to your OpenAI account.

1. Go to https://platform.openai.com/account/billing
2. Add payment method
3. Add at least $5 credit
4. Wait 5 minutes for activation
5. Regenerate API key if still failing

---

### Q: Qdrant connection refused

**A:** Check cluster URL format.

- ✅ Correct: `https://abc123.us-east.aws.cloud.qdrant.io:6333`
- ❌ Wrong: `abc123.us-east.aws.cloud.qdrant.io` (missing https:// and port)

---

### Q: Database migration fails - "relation already exists"

**A:** Database has existing tables. Reset migrations:

```bash
# Drop all tables (⚠️ This will delete all data!)
alembic downgrade base

# Re-run migrations
alembic upgrade head
```

---

### Q: SendGrid emails not sending - 403 Forbidden

**A:** Sender identity not verified.

1. Go to https://sendgrid.com/settings/sender_auth
2. Complete single sender verification
3. Check your email for verification link
4. Wait 10 minutes after verification
5. Retry sending email

---

### Q: Port 8000 already in use

**A:** Another process is using port 8000.

```bash
# Find process using port 8000
# On macOS/Linux:
lsof -i :8000

# On Windows:
netstat -ano | findstr :8000

# Kill the process or use a different port:
uvicorn src.main:app --reload --port 8001
```

---

### Q: Docker services won't start

**A:** Check if Docker Desktop is running.

```bash
# Restart Docker Desktop
# Then:
docker-compose -f infrastructure/docker/docker-compose.dev.yml down
docker-compose -f infrastructure/docker/docker-compose.dev.yml up -d
```

---

### Q: Frontend can't connect to backend - CORS error

**A:** Check `FRONTEND_URL` in backend `.env`:

```bash
# In apps/api/.env
FRONTEND_URL=http://localhost:5173
```

Also verify CORS middleware in `apps/api/src/main.py` includes frontend URL.

---

## Security Notes

⚠️ **IMPORTANT SECURITY PRACTICES:**

1. **NEVER commit `.env` files to Git**
   - `.env` files are in `.gitignore`
   - Double-check before committing: `git status`

2. **Use separate API keys for each developer**
   - Don't share API keys via Slack/email
   - Each developer should obtain their own keys

3. **Use development-tier services for local dev**
   - Free tiers are sufficient for development
   - Production API keys stored in Railway/Vercel only

4. **Rotate API keys if compromised**
   - Immediately rotate if keys are accidentally committed
   - Use GitHub secret scanning alerts

5. **Never use production credentials locally**
   - Keep production and development completely separate
   - Production credentials only in deployment platforms

---

## Next Steps

Once setup is complete:

1. ✅ Read [Architecture Documentation](./architecture.md)
2. ✅ Review [Coding Standards](./architecture/coding-standards.md)
3. ✅ Check [API Specification](./architecture/api-specification.md)
4. ✅ Explore [Project Structure](./architecture/unified-project-structure.md)
5. ✅ Start with Epic 1 stories (when available)

---

## Getting Help

**Questions or Issues?**

- 📖 Check [Architecture Docs](./architecture/)
- 🐛 Search [GitHub Issues](https://github.com/your-org/learnr/issues)
- 💬 Ask in team Slack channel
- 📧 Email: dev@learnr.com

**Estimated Setup Time:** 1-2 hours (first time)

---

*Last Updated: 2025-11-21*
