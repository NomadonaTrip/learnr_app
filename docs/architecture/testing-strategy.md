# Testing Strategy

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

### Test Environment Setup

**Backend Tests (Python):**

The LearnR backend uses pytest for testing. Test dependencies are separate from production dependencies.

**Install test dependencies:**

```bash
# From project root
cd apps/api
pip install -r requirements.txt         # Production dependencies
pip install -r requirements-test.txt    # Test dependencies
```

**Test dependencies include:**
- `pytest` - Testing framework
- `pytest-asyncio` - Async test support
- `pytest-cov` - Coverage reporting
- `pytest-mock` - Mocking utilities
- `httpx` - Async HTTP client for API tests
- `faker` - Test data generation

**Run backend tests:**

```bash
# Run all backend tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_auth_service.py

# Run with verbose output
pytest -v
```

**Root-level tests (scripts and utilities):**

Some tests are located in the root `tests/` directory (e.g., `tests/unit/test_chunk_embedding.py`). These test standalone scripts and utilities.

**Install dependencies for root-level tests:**

```bash
# From project root
pip install -r apps/api/requirements.txt       # Core dependencies
pip install -r apps/api/requirements-test.txt  # Test framework
```

**Run root-level tests:**

```bash
# From project root
python -m pytest tests/unit/test_chunk_embedding.py

# Or run all root tests
python -m pytest tests/
```

**Frontend Tests (TypeScript):**

The frontend uses Vitest for unit/integration tests and Playwright for E2E tests.

**Install test dependencies:**

```bash
# From project root
cd apps/web
npm install  # Installs both production and dev dependencies
```

**Run frontend tests:**

```bash
# Run unit/integration tests
npm test

# Run with coverage
npm run test:coverage

# Run E2E tests
npm run test:e2e

# Type checking
npm run type-check
```

**CI/CD Testing:**

All tests are automatically run in GitHub Actions on PR creation and merge to main. See `.github/workflows/ci.yml` for the full test suite execution.

**Test Best Practices:**

1. **Run tests locally before committing** - Use `pytest` for backend, `npm test` for frontend
2. **Maintain test coverage** - Aim for 80%+ coverage on critical paths
3. **Use appropriate test types** - Unit tests for logic, integration for APIs, E2E for user flows
4. **Mock external dependencies** - Don't call real OpenAI API or external services in tests
5. **Clean up test data** - Use fixtures and teardown to avoid test pollution

---
