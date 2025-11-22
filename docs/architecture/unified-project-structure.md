# Unified Project Structure

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
