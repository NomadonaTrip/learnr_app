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

### Rollback Procedures

This section documents rollback procedures for each deployment component.

#### Frontend Rollback (Vercel)

**Automatic Rollback:**
Vercel maintains deployment history with instant rollback capability.

**Procedure:**
```bash
# Option 1: Vercel Dashboard
# 1. Go to https://vercel.com/learnr/web/deployments
# 2. Find the last known good deployment
# 3. Click "..." menu → "Promote to Production"

# Option 2: Vercel CLI
vercel rollback                           # Rollback to previous deployment
vercel rollback <deployment-url>          # Rollback to specific deployment

# Option 3: Git revert (triggers new deployment)
git revert HEAD
git push origin main
```

**Rollback Time:** < 30 seconds (instant alias switch)

**Verification:**
1. Check https://learnr.com loads correctly
2. Verify bundle hash in Network tab matches previous deployment
3. Test critical user flows (login, quiz start)

---

#### Backend Rollback (Railway)

**Automatic Rollback:**
Railway maintains deployment history per service.

**Procedure:**
```bash
# Option 1: Railway Dashboard
# 1. Go to https://railway.app/project/learnr/service/api
# 2. Click "Deployments" tab
# 3. Find last known good deployment
# 4. Click "..." menu → "Redeploy"

# Option 2: Railway CLI
railway up --detach                       # Deploy specific commit
railway rollback                          # Rollback to previous deployment

# Option 3: Git revert (triggers new deployment)
git revert HEAD
git push origin main
```

**Rollback Time:** 2-5 minutes (container rebuild and health check)

**Verification:**
1. Check https://api.learnr.com/health returns 200
2. Verify `/docs` OpenAPI spec matches expected version
3. Test authentication flow
4. Monitor error rate in Sentry for 5 minutes

---

#### Database Rollback (Alembic Migrations)

**CRITICAL:** Database rollbacks are destructive. Only perform if migration caused data corruption or critical bugs.

**Pre-Rollback Checklist:**
- [ ] Confirm rollback is necessary (not just application bug)
- [ ] Verify backup exists (Supabase daily backup or manual)
- [ ] Notify team of impending rollback
- [ ] Schedule maintenance window if possible

**Procedure:**
```bash
# 1. SSH into Railway container or run locally with production DB connection
railway run bash

# 2. Check current migration state
alembic current

# 3. View migration history
alembic history

# 4. Rollback one migration
alembic downgrade -1

# 5. Rollback to specific revision
alembic downgrade <revision_id>

# 6. Verify rollback
alembic current
```

**Rollback Time:** 1-30 minutes (depends on migration complexity)

**Post-Rollback:**
1. Deploy matching application version
2. Verify application connects successfully
3. Test affected functionality
4. Monitor for data integrity issues

---

#### Qdrant Rollback (Vector Database)

**Scenario:** Corrupted embeddings or wrong vectors uploaded.

**Procedure:**
```bash
# Option 1: Delete and recreate collection
# 1. Export current collection (if partially valid)
python scripts/export_qdrant_collection.py --collection cbap_questions --output backup.json

# 2. Delete corrupted collection
curl -X DELETE "https://qdrant.learnr.com/collections/cbap_questions"

# 3. Recreate collection with correct schema
python scripts/create_qdrant_collections.py

# 4. Re-import from PostgreSQL source of truth
python scripts/generate_question_embeddings.py
python scripts/generate_babok_embeddings.py
```

**Rollback Time:** 30-60 minutes (full re-embedding)

**Note:** Qdrant data is derived from PostgreSQL. Full rebuild is always possible.

---

#### Redis Rollback (Cache)

**Scenario:** Corrupted cache causing application errors.

**Procedure:**
```bash
# Option 1: Flush specific key patterns
redis-cli KEYS "session:*" | xargs redis-cli DEL      # Clear sessions
redis-cli KEYS "coverage:*" | xargs redis-cli DEL    # Clear coverage cache
redis-cli KEYS "rate_limit:*" | xargs redis-cli DEL  # Clear rate limits

# Option 2: Full flush (nuclear option)
redis-cli FLUSHALL

# Option 3: Railway Redis addon - recreate
# Delete and recreate Redis addon in Railway dashboard
```

**Rollback Time:** < 1 minute

**Note:** Redis is cache-only. Full flush causes temporary performance degradation but no data loss.

---

#### Rollback Decision Matrix

| Symptom | Likely Cause | Rollback Action |
|---------|--------------|-----------------|
| Frontend blank page | Bad React build | Vercel rollback |
| API 500 errors on all routes | Bad backend deploy | Railway rollback |
| API 500 on specific route | Code bug in route | Railway rollback or hotfix |
| Login failures | Auth code bug | Railway rollback |
| Quiz not loading questions | Qdrant issue or code bug | Check Qdrant health, then Railway rollback |
| Slow response times | Missing index or bad query | Check slow query log, consider DB rollback |
| Data corruption visible | Bad migration | DB rollback (CRITICAL) |
| Rate limiting broken | Redis config issue | Flush Redis |

---

#### Emergency Contacts

| Role | Contact | Escalation Path |
|------|---------|-----------------|
| On-Call Engineer | PagerDuty rotation | First responder |
| Backend Lead | [email] | Escalate after 15 min |
| Infrastructure Lead | [email] | Database/infra issues |
| Product Lead | [email] | User communication decisions |

---

#### Post-Rollback Checklist

After any rollback:

- [ ] Verify system health (all health checks passing)
- [ ] Monitor error rates for 15 minutes
- [ ] Document incident in runbook
- [ ] Create post-mortem issue
- [ ] Notify affected users if data loss occurred
- [ ] Schedule root cause analysis meeting

---

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-12-08 | 1.1 | Added comprehensive Rollback Procedures section - frontend (Vercel), backend (Railway), database (Alembic), Qdrant, Redis; rollback decision matrix; emergency contacts; post-rollback checklist | Winston (Architect) |
| 2025-11-01 | 1.0 | Initial deployment architecture | Original |
