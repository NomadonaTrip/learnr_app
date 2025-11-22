# LearnR

AI-Powered Adaptive Learning Platform for Professional Certification Exam Preparation

## Overview

LearnR is a comprehensive adaptive learning platform that transforms professional certification exam preparation from passive memorization to active, adaptive mastery. The platform uses AI-driven competency assessment, personalized content delivery, and scientifically-proven retention techniques to help working professionals prepare for high-stakes certifications.

**Initial Target:** CBAP (Certified Business Analysis Professional) certification

**Key Innovation:** "Test Fast, Read Later" - Separating momentum-driven testing from thoughtful reading study for optimal learning flow.

---

## Quick Start

### For Developers

📖 **[Complete Developer Setup Guide](./docs/DEVELOPER_SETUP.md)** ← **START HERE**

**TL;DR:**
```bash
# 1. Clone repository
git clone https://github.com/your-org/learnr.git
cd learnr

# 2. Set up environment (see DEVELOPER_SETUP.md for API keys)
cp apps/api/.env.example apps/api/.env
cp apps/web/.env.example apps/web/.env
# Edit .env files with your API keys

# 3. Start local services
docker-compose -f infrastructure/docker/docker-compose.dev.yml up -d

# 4. Install dependencies
cd apps/api && pip install -r requirements.txt
cd ../web && npm install

# 5. Run migrations
cd apps/api && alembic upgrade head

# 6. Start development servers
# Terminal 1 (Backend):
cd apps/api && uvicorn src.main:app --reload

# Terminal 2 (Frontend):
cd apps/web && npm run dev

# Open http://localhost:5173
```

**Estimated Setup Time:** 1-2 hours (first time)

---

## Key Features (MVP)

✅ **Adaptive Learning Engine**
- Real-time competency tracking across 6 CBAP knowledge areas
- Intelligent question selection based on user gaps
- Simplified Item Response Theory (IRT) for difficulty matching

✅ **Post-Session Review** (Retention Booster)
- Immediate re-presentation of incorrect answers
- 2-3x better retention vs spaced repetition alone
- Track reinforcement success (incorrect → correct)

✅ **Asynchronous Reading Library** (Critical Differentiator)
- BABOK v3 content delivered without interrupting learning flow
- Priority-sorted reading queue (High/Medium/Low)
- Zero popups, toasts, or interruptions during quiz sessions

✅ **Spaced Repetition System**
- SM-2 algorithm adapted for 60-day exam timeline
- Review intervals: 1 → 3 → 7 → 14 days
- Mixed sessions: 40% reviews + 60% new content

✅ **Progress Transparency**
- Dashboard with competency bars per knowledge area
- Exam readiness score
- Weekly progress trends
- Days until exam countdown

✅ **Modern UX**
- Dark mode support (light/dark/auto)
- Mobile-responsive (PWA-ready)
- WCAG 2.1 AA accessible

---

## Architecture

**Tech Stack:**
- **Frontend:** React 18.2 + TypeScript + Tailwind CSS + Vite
- **Backend:** Python 3.11 + FastAPI + PostgreSQL + Redis
- **Vector DB:** Qdrant (semantic search for questions + reading content)
- **AI/ML:** OpenAI GPT-4 (content generation) + text-embedding-3-large (embeddings)
- **Analytics:** PostHog (product analytics, session replay)
- **Email:** SendGrid (password reset, transactional emails)
- **Deployment:** Vercel (frontend) + Railway (backend) + Supabase (database)

**Project Structure:**
```
learnr/
├── apps/
│   ├── web/          # React frontend (SPA)
│   └── api/          # FastAPI backend
├── docs/
│   ├── prd/          # Product requirements (sharded)
│   ├── architecture/ # System architecture (sharded)
│   └── DEVELOPER_SETUP.md  # 👈 Complete setup guide
├── infrastructure/
│   └── docker/       # Docker Compose for local dev
└── scripts/          # Seed data, migrations, utilities
```

---

## Documentation

### 📚 Essential Reading

1. **[Developer Setup Guide](./docs/DEVELOPER_SETUP.md)** - Start here for environment setup
2. **[PRD (Product Requirements)](./docs/prd/)** - Detailed product requirements (sharded by section)
3. **[Architecture](./docs/architecture/)** - System architecture (sharded by component)
4. **[API Rate Limits](./docs/architecture/external-dependencies-rate-limits.md)** - External service limits & mitigation

### 📖 Quick Links

- [Tech Stack](./docs/architecture/tech-stack.md) - Complete technology selections with versions
- [Coding Standards](./docs/architecture/coding-standards.md) - Code quality guidelines
- [Database Schema](./docs/architecture/database-schema.md) - Data model overview
- [Deployment Architecture](./docs/architecture/deployment-architecture.md) - Deployment strategy & scaling
- [Frontend Architecture](./docs/architecture/frontend-architecture.md) - UI/UX architecture & PWA

---

## Development Workflow

### Branching Strategy

```
main          # Production-ready code
  ├── develop # Integration branch
  │   ├── feature/epic-1-authentication
  │   ├── feature/epic-2-content-foundation
  │   └── feature/epic-3-diagnostic
```

### Testing

```bash
# Frontend tests (Vitest + React Testing Library)
cd apps/web && npm run test

# Backend tests (pytest)
cd apps/api && pytest

# E2E tests (Playwright)
npm run test:e2e

# With coverage
pytest --cov=src --cov-report=html
```

### Linting & Formatting

```bash
# Frontend (ESLint + Prettier)
cd apps/web
npm run lint
npm run format

# Backend (Ruff)
cd apps/api
ruff check src/
ruff format src/
```

---

## Epic Overview

**Timeline:** 30-day MVP sprint (8 epics)

1. **Epic 1:** Foundation & User Authentication (4 days)
2. **Epic 2:** Content Foundation & Question Bank (5 days)
3. **Epic 3:** Diagnostic Assessment & Competency Baseline (3 days)
4. **Epic 4:** Adaptive Quiz Engine & Explanations (5 days)
5. **Epic 5:** Targeted Reading Content Integration (4 days) - **Day 24 Alpha Test**
6. **Epic 6:** Progress Dashboard & Transparency (3 days)
7. **Epic 7:** Spaced Repetition & Long-Term Retention (3 days)
8. **Epic 8:** Polish, Testing & Launch Readiness (3 days)

See [Epic List](./docs/prd/epic-list.md) for detailed breakdown and sequencing rationale.

---

## Success Criteria

### MVP Validation (Case Study User - 60 Days)
- ✅ User confirms diagnostic accuracy reflects actual knowledge level
- ✅ User reports reading content was relevant and helpful (80%+ helpful rating)
- ✅ User can articulate differentiation vs. competitor quiz apps
- ✅ User passes CBAP exam on first attempt (December 21, 2025)

### Go/No-Go Decision (Day 24 of MVP)
- ✅ Complete learning loop functional (quiz → explanation → reading)
- ✅ User finds BABOK reading content valuable
- ✅ User commits to daily usage for remaining 30 days
- ✅ Differentiation from static quiz apps is clear

### Target Outcomes
- **80%+ first-time pass rate** (vs. 60% industry average)
- **30% reduction in study time** through adaptive targeting
- **90%+ users feel "exam-ready"** before taking the test

---

## Environment Setup Checklist

Before starting development, ensure you have:

- [ ] Node.js 18.x or higher
- [ ] Python 3.11.x
- [ ] Docker Desktop running
- [ ] Git installed
- [ ] API keys obtained (see [Developer Setup Guide](./docs/DEVELOPER_SETUP.md)):
  - [ ] OpenAI API key
  - [ ] Qdrant Cloud cluster + API key
  - [ ] PostHog project API key
  - [ ] Sentry DSN
  - [ ] SendGrid API key
  - [ ] Supabase database credentials
- [ ] Environment variables configured (`.env` files)
- [ ] Dependencies installed (backend + frontend)
- [ ] Database migrations run
- [ ] Tests passing

**See [DEVELOPER_SETUP.md](./docs/DEVELOPER_SETUP.md) for detailed instructions.**

---

## Offline Development Mode

Develop without internet or external API costs:

```bash
# Start local services (includes mock OpenAI)
docker-compose -f infrastructure/docker/docker-compose.dev.yml up -d

# Configure offline mode in apps/api/.env
USE_MOCK_OPENAI=true
USE_MOCK_EMAIL=true
OPENAI_API_BASE=http://localhost:8001

# Start development as usual
```

**What works offline:**
- ✅ Question selection (mock embeddings)
- ✅ Answer submission & feedback
- ✅ Competency calculation
- ✅ Reading content retrieval
- ✅ All UI development

**See [Developer Setup Guide - Offline Mode](./docs/DEVELOPER_SETUP.md#offline-development-mode) for details.**

---

## Contributing

### Before Starting Development

1. Read [Developer Setup Guide](./docs/DEVELOPER_SETUP.md)
2. Review [Coding Standards](./docs/architecture/coding-standards.md)
3. Check [Architecture Documentation](./docs/architecture/)
4. Understand [API Specification](./docs/architecture/api-specification.md)

### Pull Request Process

1. Create feature branch from `develop`
2. Write tests for new functionality
3. Ensure all tests pass (`npm run test`, `pytest`)
4. Run linters (`npm run lint`, `ruff check`)
5. Update documentation if needed
6. Submit PR to `develop` (not `main`)
7. Address code review feedback
8. Squash commits before merge

---

## Troubleshooting

### Common Issues

**Q: "OpenAI API key not working"**
→ Ensure payment method added at https://platform.openai.com/account/billing

**Q: "Database connection refused"**
→ Check if Docker containers are running: `docker ps`

**Q: "SendGrid emails not sending"**
→ Verify sender identity at https://sendgrid.com/settings/sender_auth

**Q: "Frontend can't connect to backend - CORS error"**
→ Check `FRONTEND_URL` in backend `.env` matches frontend dev server URL

**See [Developer Setup Guide - Troubleshooting](./docs/DEVELOPER_SETUP.md#troubleshooting) for more solutions.**

---

## Support & Contact

- 📖 **Documentation:** [docs/](./docs/)
- 🐛 **Issues:** [GitHub Issues](https://github.com/your-org/learnr/issues)
- 💬 **Discussions:** [GitHub Discussions](https://github.com/your-org/learnr/discussions)
- 📧 **Email:** dev@learnr.com

---

## License

*[Add license information here]*

---

## Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [React](https://react.dev/) - UI library
- [Qdrant](https://qdrant.tech/) - Vector database
- [OpenAI](https://openai.com/) - LLM & embeddings
- [PostHog](https://posthog.com/) - Product analytics
- [SendGrid](https://sendgrid.com/) - Email delivery
- [Tailwind CSS](https://tailwindcss.com/) - Utility-first CSS

---

**Version:** 1.0.0-MVP
**Last Updated:** 2025-11-21
