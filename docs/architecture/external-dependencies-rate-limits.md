# External Dependencies & Rate Limits

**Purpose:** Document all external service dependencies, API rate limits, quotas, and mitigation strategies to prevent production outages and control costs.

---

## Table of Contents
1. [OpenAI API](#openai-api)
2. [Qdrant Cloud](#qdrant-cloud)
3. [PostHog Analytics](#posthog-analytics)
4. [Sentry Error Tracking](#sentry-error-tracking)
5. [SendGrid Email Service](#sendgrid-email-service)
6. [Supabase PostgreSQL](#supabase-postgresql)
7. [Railway Redis](#railway-redis)
8. [Rate Limit Monitoring](#rate-limit-monitoring)
9. [Error Handling Patterns](#error-handling-patterns)

---

## OpenAI API

### Service Details
- **Purpose:** LLM content generation + embeddings for semantic search
- **Tier:** Pay-as-you-go (no free tier)
- **Pricing:** https://openai.com/pricing

### Rate Limits

| Tier | RPM (Requests/Min) | TPM (Tokens/Min) | RPD (Requests/Day) | Notes |
|------|-------------------|------------------|-------------------|-------|
| **Tier 1** (New accounts) | 60 | 200,000 | Unlimited | First $100 spent |
| **Tier 2** | 500 | 2,000,000 | Unlimited | After $100 spent |
| **Tier 3** | 5,000 | 10,000,000 | Unlimited | After $1,000 spent |

**API-Specific Limits:**
- **Embeddings API:** `text-embedding-3-large` (~500 tokens per request)
- **Chat API:** `gpt-4-turbo-preview` (~1000 tokens per explanation)

### MVP Usage Estimate

**One-Time Setup:**
```
Questions:      1,000 questions × 500 tokens = 500K tokens
BABOK chunks:   5,000 chunks × 500 tokens   = 2.5M tokens
Total:          3M tokens (one-time)
Cost:           ~$4 (@ $0.13 per 1M tokens for embeddings)
```

**Ongoing Usage (10 users):**
```
Explanations:   50 questions/day × 1K tokens = 50K tokens/day
Cost:           ~$1/day (@ $0.02 per 1K tokens for GPT-4)
Monthly:        ~$30/month for 10 users
```

### Rate Limit Mitigation

#### 1. Caching Strategy
```python
# apps/api/src/services/llm_service.py
from functools import lru_cache

@lru_cache(maxsize=10000)
def get_embedding(text: str) -> List[float]:
    """
    Cache embeddings to avoid regeneration.
    Embeddings for the same text are always identical.
    """
    response = openai.embeddings.create(
        model="text-embedding-3-large",
        input=text
    )
    return response.data[0].embedding
```

#### 2. Exponential Backoff
```python
import time
from openai import RateLimitError

def call_openai_with_retry(func, max_retries=3):
    """
    Retry OpenAI API calls with exponential backoff.
    """
    for attempt in range(max_retries):
        try:
            return func()
        except RateLimitError as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # 1s, 2s, 4s
                logger.warning(f"Rate limit hit, waiting {wait_time}s...")
                time.sleep(wait_time)
            else:
                logger.error(f"Max retries exceeded: {e}")
                # Send to Sentry
                sentry_sdk.capture_exception(e)
                raise
```

#### 3. Request Throttling
```python
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/questions/next")
@limiter.limit("10/minute")  # Max 10 questions per minute per user
async def get_next_question():
    """Prevent users from spamming question requests."""
    pass
```

#### 4. Batch Processing
```python
# Generate embeddings in batches during setup
def batch_generate_embeddings(texts: List[str], batch_size=100):
    """
    Generate embeddings in batches to optimize API usage.
    OpenAI allows up to 100 inputs per request.
    """
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        response = openai.embeddings.create(
            model="text-embedding-3-large",
            input=batch
        )
        yield response.data
```

### Monitoring & Alerts

**Dashboard Metrics:**
- Daily token usage (embeddings vs chat)
- Cost per day/week/month
- Rate limit errors (429 responses)
- Average response time

**Alert Thresholds:**
- ⚠️ Warning: $10/day (3x expected)
- 🔴 Critical: $25/day (10x expected)
- ⚠️ Rate limit errors > 5/hour

**Implementation:**
```python
# apps/api/src/middleware/openai_monitoring.py
import structlog

logger = structlog.get_logger()

def track_openai_usage(endpoint: str, tokens: int, cost: float):
    """Log OpenAI usage for monitoring."""
    logger.info(
        "openai_api_call",
        endpoint=endpoint,
        tokens=tokens,
        cost_usd=cost,
        tier=get_current_tier()
    )

    # Also send to PostHog for dashboard
    posthog.capture(
        event="openai_api_usage",
        properties={
            "endpoint": endpoint,
            "tokens": tokens,
            "cost_usd": cost
        }
    )
```

---

## Qdrant Cloud

### Service Details
- **Purpose:** Vector database for semantic search
- **Tier:** Free (1M vectors, 1GB storage)
- **Pricing:** https://qdrant.io/pricing/

### Limits

| Tier | Vectors | Storage | Requests | Cost |
|------|---------|---------|----------|------|
| **Free** | 1M | 1GB | Unlimited | $0 |
| **Startup** | 10M | 4GB | Unlimited | $25/month |
| **Production** | 100M | 16GB | Unlimited | $95/month |

### MVP Usage

```
Questions:      1,000 × 3KB  = 3MB
BABOK chunks:   5,000 × 5KB  = 25MB
Total:          6,000 vectors, 28MB

Free tier capacity: 1M vectors, 1GB storage
Headroom:          166x vectors, 35x storage
```

✅ **Free tier is sufficient for MVP and beyond.**

### Monitoring

**Metrics to Track:**
- Total vectors stored
- Storage used (MB)
- Query latency (p95)
- Collection count

**Alert Thresholds:**
- ⚠️ Warning: 800K vectors (80% of limit)
- ⚠️ Storage: 800MB (80% of limit)

---

## PostHog Analytics

### Service Details
- **Purpose:** Product analytics, session replay, feature flags
- **Tier:** Free (1M events/month)
- **Pricing:** https://posthog.com/pricing

### Limits

| Tier | Events/Month | Features | Cost |
|------|-------------|----------|------|
| **Free** | 1M | All features | $0 |
| **Growth** | Custom | All features | Usage-based |

### MVP Usage Estimate

```
10 users × 2 sessions/day × 50 events/session = 1,000 events/day
Monthly: 30K events/month

Free tier: 1M events/month
Headroom: 33x
```

✅ **Free tier is more than sufficient for MVP.**

### Event Sampling Strategy

For production scale (100+ users):
```javascript
// apps/web/src/services/analyticsService.ts
export function trackEvent(event: string, properties: object) {
  // Sample 10% of events in production
  const sampleRate = import.meta.env.PROD ? 0.1 : 1.0;

  if (Math.random() < sampleRate) {
    posthog.capture(event, properties);
  }
}
```

### Best Practices

**DO Track:**
- User actions (button clicks, page views)
- Feature usage (quiz started, reading opened)
- Business metrics (questions answered, sessions completed)

**DON'T Track:**
- Every API call (too noisy)
- System-level events (use logs instead)
- PII without anonymization

---

## Sentry Error Tracking

### Service Details
- **Purpose:** Error tracking and performance monitoring
- **Tier:** Free (5K errors/month)
- **Pricing:** https://sentry.io/pricing/

### Limits

| Tier | Errors/Month | Features | Cost |
|------|-------------|----------|------|
| **Developer** | 5K | Basic | $0 |
| **Team** | 50K | Full | $26/month |
| **Business** | 500K | Full + SSO | $80/month |

### MVP Usage

```
10 users × 1 error/day = 10 errors/day
Monthly: 300 errors/month

Free tier: 5K errors/month
Headroom: 16x
```

✅ **Free tier is sufficient for MVP.**

### Rate Limiting Strategy

```python
# apps/api/src/config.py
import sentry_sdk

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    environment=os.getenv("ENVIRONMENT"),

    # Sample error events
    sample_rate=1.0 if os.getenv("ENVIRONMENT") == "development" else 0.5,

    # Sample performance traces
    traces_sample_rate=0.1,

    # Filter sensitive data
    before_send=filter_sensitive_data
)

def filter_sensitive_data(event, hint):
    """Remove PII before sending to Sentry."""
    if "request" in event:
        # Remove auth headers
        event["request"]["headers"].pop("Authorization", None)
        # Remove sensitive query params
        event["request"]["query_string"] = "[FILTERED]"
    return event
```

---

## SendGrid Email Service

### Service Details
- **Purpose:** Transactional emails (password reset, welcome)
- **Tier:** Free (100 emails/day)
- **Pricing:** https://sendgrid.com/pricing/

### Limits

| Tier | Emails/Day | Features | Cost |
|------|-----------|----------|------|
| **Free** | 100 | Basic | $0 |
| **Essentials** | 100K | Full | $20/month |

### MVP Usage

```
Password resets: ~5/day
Welcome emails:  ~1/day
Total:           ~6/day

Free tier: 100/day
Headroom: 16x
```

✅ **Free tier is more than sufficient for MVP.**

### Rate Limiting

**Backend Implementation:**
```python
from slowapi import Limiter

@app.post("/api/auth/reset-password")
@limiter.limit("5/hour")  # Max 5 password resets per hour per IP
async def reset_password(email: str):
    """Prevent password reset abuse."""
    await email_service.send_password_reset_email(email)
```

### Monitoring

**Alert on:**
- Daily email count > 80 (approaching limit)
- Failed sends > 10% (deliverability issue)
- Bounce rate > 5%

---

## Supabase PostgreSQL

### Service Details
- **Purpose:** PostgreSQL database (user data, responses, sessions)
- **Tier:** Free (500MB database, 2GB bandwidth)
- **Pricing:** https://supabase.com/pricing

### Limits

| Tier | Database | Bandwidth | Cost |
|------|---------|----------|------|
| **Free** | 500MB | 2GB/month | $0 |
| **Pro** | 8GB | 50GB/month | $25/month |

### MVP Usage

```
10 users × 5,000 responses × 500 bytes = 25MB
Free tier: 500MB
Headroom: 20x
```

✅ **Free tier is sufficient for MVP.**

### Connection Limits

**Free Tier:**
- Max connections: 50 (use connection pooling)
- Max query time: 2 seconds

**Mitigation:**
```python
# apps/api/src/db/session.py
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,          # Max 5 connections per worker
    max_overflow=10,      # Allow 10 additional connections during peak
    pool_timeout=30,      # Wait 30s for connection
    pool_recycle=3600     # Recycle connections every hour
)
```

---

## Railway Redis

### Service Details
- **Purpose:** Session cache, rate limiting, background job queue
- **Cost:** $5 credit/month free

### Limits

Free tier includes:
- Memory: 100MB
- CPU: Shared
- Bandwidth: Unlimited

### MVP Usage

```
Session cache: ~1MB (10 users)
Rate limiting: ~100KB
Background jobs: ~500KB
Total: ~2MB

Free tier: 100MB
Headroom: 50x
```

✅ **Free tier is sufficient for MVP.**

---

## Rate Limit Monitoring

### Centralized Monitoring Dashboard

**Tools:**
- PostHog for business metrics
- Sentry for error tracking
- CloudWatch for infrastructure metrics (future)

**Key Metrics:**
1. OpenAI API: Tokens/day, Cost/day, Rate limit errors
2. SendGrid: Emails/day, Bounce rate, Failed sends
3. Database: Connections used, Query time p95
4. Redis: Memory usage, Cache hit rate

### Implementation

```python
# apps/api/src/middleware/rate_limit_monitoring.py
import structlog

logger = structlog.get_logger()

async def monitor_rate_limits():
    """
    Periodic task to check rate limit usage.
    Run every hour via Celery beat.
    """
    metrics = {
        "openai_tokens_today": get_openai_usage(),
        "sendgrid_emails_today": get_sendgrid_usage(),
        "db_connections": get_db_connections(),
        "redis_memory_mb": get_redis_memory()
    }

    logger.info("rate_limit_check", **metrics)

    # Alert if approaching limits
    if metrics["openai_tokens_today"] > 150000:  # 75% of 200K
        send_alert("OpenAI approaching daily limit")

    if metrics["sendgrid_emails_today"] > 80:  # 80% of 100
        send_alert("SendGrid approaching daily limit")
```

---

## Error Handling Patterns

### 1. Retry with Exponential Backoff

```python
import asyncio
from typing import TypeVar, Callable

T = TypeVar('T')

async def retry_with_backoff(
    func: Callable[[], T],
    max_retries: int = 3,
    base_delay: float = 1.0
) -> T:
    """
    Retry function with exponential backoff.

    Args:
        func: Async function to retry
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds (doubles each retry)

    Returns:
        Result of func()

    Raises:
        Last exception if all retries fail
    """
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise

            delay = base_delay * (2 ** attempt)
            logger.warning(
                f"Attempt {attempt + 1} failed, retrying in {delay}s",
                error=str(e)
            )
            await asyncio.sleep(delay)
```

### 2. Circuit Breaker Pattern

```python
from datetime import datetime, timedelta

class CircuitBreaker:
    """
    Circuit breaker to prevent cascading failures.

    States:
    - CLOSED: Normal operation
    - OPEN: Fast-fail after threshold errors
    - HALF_OPEN: Test if service recovered
    """
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures = 0
        self.last_failure_time = None
        self.state = "CLOSED"

    async def call(self, func):
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = await func()
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        self.failures = 0
        self.state = "CLOSED"

    def _on_failure(self):
        self.failures += 1
        self.last_failure_time = datetime.now()

        if self.failures >= self.failure_threshold:
            self.state = "OPEN"
            logger.error("Circuit breaker opened")

    def _should_attempt_reset(self):
        return (
            datetime.now() - self.last_failure_time
            > timedelta(seconds=self.timeout)
        )
```

### 3. Graceful Degradation

```python
async def get_question_explanation(question_id: str) -> str:
    """
    Get explanation with graceful degradation.

    Priority:
    1. LLM-generated (best quality, costs API calls)
    2. Pre-written explanation from database (good quality, free)
    3. Generic fallback (basic quality, always available)
    """
    try:
        # Try LLM generation first
        explanation = await llm_service.generate_explanation(question_id)
        return explanation
    except RateLimitError:
        logger.warning("OpenAI rate limit, falling back to pre-written")

        # Fall back to pre-written explanation
        explanation = await db.get_pre_written_explanation(question_id)
        if explanation:
            return explanation

        # Final fallback
        return "Please review the BABOK section for this topic."
```

---

## Summary & Recommendations

### ✅ MVP is Well Within Free Tiers

| Service | Free Tier | MVP Usage | Headroom | Risk |
|---------|-----------|-----------|----------|------|
| OpenAI | Pay-as-you-go | $30/month | N/A | Low (monitored) |
| Qdrant | 1M vectors | 6K vectors | 166x | None |
| PostHog | 1M events/month | 30K/month | 33x | None |
| Sentry | 5K errors/month | 300/month | 16x | None |
| SendGrid | 100 emails/day | 6/day | 16x | None |
| Supabase | 500MB | 25MB | 20x | None |
| Railway | 100MB Redis | 2MB | 50x | None |

### 🔴 Critical Actions

1. **Implement rate limit error handling** (exponential backoff)
2. **Set up monitoring dashboard** (PostHog + logs)
3. **Configure alerts** (approaching limits, errors)
4. **Cache aggressively** (embeddings, explanations)

### 📊 When to Upgrade

**Qdrant:** Upgrade to Startup ($25/month) when:
- Approaching 800K vectors (unlikely in MVP)

**PostHog:** Upgrade to Growth when:
- Approaching 1M events/month (>30 active users)

**Sentry:** Upgrade to Team ($26/month) when:
- Approaching 5K errors/month (indicates quality issues)

**SendGrid:** Upgrade to Essentials ($20/month) when:
- Approaching 100 emails/day (>50 daily active users)

---

*Last Updated: 2025-11-21*
