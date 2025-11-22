# Deployment Architecture

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
