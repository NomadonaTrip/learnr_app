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

---
