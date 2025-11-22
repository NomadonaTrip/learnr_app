# Monitoring and Observability

### Service Level Objectives (SLOs)

**Purpose:** Define uptime and performance targets with clear escalation procedures.

#### Uptime SLAs by Environment

| Environment | Uptime Target | Downtime Budget (monthly) | Rationale |
|-------------|---------------|---------------------------|-----------|
| **MVP** (Days 1-30) | 95% | 36 hours | Development in progress, rapid iteration |
| **Beta** (Months 2-3) | 98% | 14.4 hours | Limited user base, tolerance for issues |
| **GA** (Month 4+) | 99% | 7.2 hours | Production-quality service, paying users |
| **Enterprise** (Future) | 99.9% | 43 minutes | SLA-backed service for enterprise customers |

**Planned Maintenance Windows:**
- Scheduled during low-traffic periods (Tuesday/Wednesday 2-4am UTC)
- Advance notice: 48 hours via in-app banner + email
- Max duration: 2 hours
- Excluded from SLA calculations

#### Performance SLOs

| Metric | Target | Measurement | Escalation Threshold |
|--------|--------|-------------|----------------------|
| **API Response Time (p95)** | <200ms | All API endpoints | Alert if >500ms for 5 min |
| **API Response Time (p99)** | <500ms | All API endpoints | Alert if >1000ms for 5 min |
| **Frontend Page Load (p95)** | <3 seconds | Lighthouse CI | Alert if >5s for 10 min |
| **Quiz Question Delivery** | <500ms | `/questions/next` endpoint | Alert if >1s for 5 min |
| **Adaptive Engine Latency** | <1 second | Competency update + next question | Alert if >2s for 5 min |
| **Vector Search (Qdrant)** | <50ms | Semantic search queries | Alert if >100ms for 5 min |

#### Error Rate SLOs

| Error Type | Target | Measurement | Escalation |
|------------|--------|-------------|------------|
| **API Error Rate (5xx)** | <1% | All API responses | Page on-call if >5% for 5 min |
| **Frontend JS Errors** | <1% | Sentry error rate vs sessions | Investigate if >2% for 15 min |
| **Database Query Errors** | <0.1% | PostgreSQL error logs | Page on-call if >1% for 5 min |
| **Authentication Failures** | <2% | Login/register endpoint failures | Alert if >10% for 5 min |

### Monitoring Stack

- **Frontend Monitoring:** Sentry (error tracking, performance monitoring)
- **Backend Monitoring:** Sentry (error tracking), Railway metrics (CPU, memory)
- **Error Tracking:** Sentry for both frontend and backend (unified dashboard)
- **Performance Monitoring:** Sentry Performance, PostHog session replay
- **Logs:** Structlog (backend), Railway logs, Vercel logs (frontend)

### Key Metrics

**Frontend Metrics:**
- **Core Web Vitals:** LCP < 2.5s, FID < 100ms, CLS < 0.1
- **JavaScript Errors:** Track via Sentry, alert on > 1% error rate
- **API Response Times:** Track p50, p95, p99 for all API calls
- **User Interactions:** PostHog events for quiz sessions, reading library usage

**Backend Metrics:**
- **Request Rate:** Requests per second (track normal baseline, alert on spikes)
- **Error Rate:** % of 5xx responses (alert if > 1%)
- **Response Time:** p50 < 100ms, p95 < 200ms, p99 < 500ms
- **Database Query Performance:** Track slow queries (> 100ms), optimize via indexes
- **Celery Task Metrics:** Task completion rate, queue length, failure rate

**Business Metrics (PostHog):**
- Daily active users (DAU)
- Quiz sessions completed per user
- Post-session review adoption rate (% of sessions with review)
- Reading library engagement (% of users opening reading items)
- Competency progression over time

---
