# Security and Performance

### Security Requirements

**Frontend Security:**
- **CSP Headers:** `default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.posthog.com; connect-src 'self' https://api.learnr.com https://app.posthog.com`
- **XSS Prevention:** React automatic escaping, DOMPurify for markdown rendering, Content-Security-Policy headers
- **Secure Storage:** JWT tokens in localStorage (XSS risk acknowledged), HttpOnly cookies for refresh tokens (future enhancement)

**Backend Security:**
- **Input Validation:** Pydantic models for all API inputs, SQL injection prevention via SQLAlchemy ORM, no raw SQL queries
- **Rate Limiting:** 100 req/min for adaptive endpoints, 1000 req/min for read endpoints (Redis-backed)
- **CORS Policy:** Whitelist only production domains (`https://learnr.com`), localhost for development

**Authentication Security:**
- **Token Storage:** Access tokens in memory (15 min expiry), refresh tokens in localStorage (7 day expiry)
- **Session Management:** Stateless JWT tokens, Redis blacklist for logout
- **Password Policy:** Minimum 8 characters, bcrypt hashing (cost factor 12), no complexity requirements for MVP

**Data Security:**
- **Encryption at rest:** PostgreSQL encryption via Supabase, S3 server-side encryption (AES-256)
- **Encryption in transit:** HTTPS/TLS 1.3 for all API communication, WSS for future WebSocket features
- **PII Protection:** User email, password hashes, study data never logged, GDPR-ready data export/deletion

### Admin Security Controls

**Purpose:** Secure admin operations (user impersonation, content management, user search) while maintaining audit trail for compliance.

#### Admin Role Management

**Admin Flag Protection:**
- `is_admin` boolean flag stored in `users` table
- **No API endpoint** for admin promotion (security-by-design)
- Admin promotion requires direct database update:
  ```sql
  UPDATE users SET is_admin = TRUE WHERE email = 'admin@learnr.com';
  ```
- Production database access restricted to infrastructure team only
- All admin user emails documented in secure runbook

**Middleware Protection:**
```python
# apps/api/src/middleware/auth_middleware.py
from fastapi import Depends, HTTPException, status
from src.dependencies import get_current_user

def require_admin(user = Depends(get_current_user)):
    """
    Middleware decorator for admin-only endpoints.

    Raises 403 Forbidden if user.is_admin is False.
    """
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user

# Usage in routes
@router.get("/admin/users/search")
async def search_users(
    q: str,
    admin_user = Depends(require_admin)  # Enforces admin access
):
    ...
```

#### Impersonation Security

**Token Structure:**
- Standard JWT with additional claims
- 30-minute hard expiration (non-refreshable)
- Cannot be used to impersonate other admins

**Token Claims:**
```json
{
  "sub": "impersonated_user_id",
  "is_impersonation": true,
  "impersonated_by": "admin_user_id",
  "exp": 1732186800,  // 30 minutes from issue
  "iat": 1732185000,
  "original_admin_token": "jwt_token_hash"  // For exit impersonation
}
```

**Restrictions Enforced:**

1. **Cannot Impersonate Admins:**
```python
async def impersonate_user(target_user_id: UUID, admin = Depends(require_admin)):
    target_user = await user_repo.get_by_id(target_user_id)

    if target_user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Cannot impersonate other admins"
        )

    # ... generate impersonation token
```

2. **One Active Impersonation Per Admin:**
```python
# Check Redis for active impersonation
active_key = f"impersonation:admin:{admin.id}"
if await redis.exists(active_key):
    raise HTTPException(
        status_code=409,
        detail="You have an active impersonation session. Exit it first."
    )

# Store active impersonation in Redis (30-min TTL)
await redis.setex(
    active_key,
    1800,  // 30 minutes
    target_user_id
)
```

3. **Automatic Audit Logging:**
```python
# Log impersonation start
await audit_log_repo.create(
    admin_id=admin.id,
    action_type="impersonate",
    target_user_id=target_user_id,
    ip_address=request.client.host,
    user_agent=request.headers.get("user-agent"),
    timestamp=datetime.utcnow(),
)
```

**Frontend Impersonation Banner:**

Mandatory persistent banner shown during all impersonation sessions:

```tsx
// apps/web/src/components/admin/ImpersonationBanner.tsx
export function ImpersonationBanner() {
  const { isImpersonating, impersonatedUser, exitImpersonation } = useAuth();

  if (!isImpersonating) return null;

  return (
    <div
      className="impersonation-banner"
      role="alert"
      aria-live="polite"
      style={{
        position: 'sticky',
        top: 0,
        zIndex: 9999,
        background: '#F59E0B', // Warning orange
        color: '#000',
        padding: '12px 24px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
      }}
    >
      <div className="flex items-center gap-3">
        <span className="font-bold">⚠️ IMPERSONATION MODE</span>
        <span>Viewing as: {impersonatedUser.email}</span>
      </div>
      <button
        onClick={exitImpersonation}
        className="btn-exit-impersonation"
        style={{
          background: '#000',
          color: '#fff',
          padding: '8px 16px',
          borderRadius: '4px',
          fontWeight: 600,
        }}
      >
        Exit Impersonation
      </button>
    </div>
  );
}
```

**Banner Requirements:**
- Always visible (sticky position, highest z-index)
- High-contrast colors (WCAG AAA for warning)
- Cannot be dismissed (only exit impersonation button)
- Screen reader announcement via `role="alert"`

#### Rate Limiting for Admin Endpoints

**Aggressive Rate Limits:**

| Endpoint | Rate Limit | Window | Rationale |
|----------|-----------|--------|-----------|
| `POST /admin/impersonate/{user_id}` | 10 requests | 1 hour | Security-sensitive, infrequent legitimate use |
| `GET /admin/users/search` | 100 requests | 1 hour | Prevent bulk scraping of user data |
| `GET /admin/audit-log` | 500 requests | 1 hour | Read-heavy, less sensitive |
| `PUT /admin/questions/{id}` | 50 requests | 1 hour | Content modification, moderate use |

**Implementation (Redis):**
```python
# apps/api/src/middleware/rate_limit_middleware.py
from fastapi import Request, HTTPException
import redis

async def rate_limit_admin(
    request: Request,
    limit: int,
    window_seconds: int,
    admin = Depends(require_admin)
):
    """
    Rate limit admin endpoint per admin user.
    """
    key = f"rate_limit:admin:{admin.id}:{request.url.path}"
    current = await redis.incr(key)

    if current == 1:
        await redis.expire(key, window_seconds)

    if current > limit:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Try again in {window_seconds}s."
        )

# Usage
@router.post("/admin/impersonate/{user_id}")
async def impersonate_user(
    user_id: UUID,
    admin = Depends(require_admin),
    _rate_limit = Depends(lambda req: rate_limit_admin(req, limit=10, window_seconds=3600))
):
    ...
```

#### Audit Trail

**Comprehensive Logging:**

All admin actions automatically logged to `admin_audit_log` table:

**Schema:**
```sql
CREATE TABLE admin_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    admin_id UUID NOT NULL REFERENCES users(id),
    action_type VARCHAR(50) NOT NULL,  -- 'impersonate', 'user_search', 'content_edit', etc.
    target_user_id UUID REFERENCES users(id),  -- For user-specific actions
    target_resource_id UUID,  -- For content modifications (question_id, chunk_id, etc.)
    metadata JSONB,  -- Action-specific metadata
    ip_address INET NOT NULL,
    user_agent TEXT,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    duration_seconds INTEGER,  -- For impersonation sessions

    INDEX idx_admin_audit_admin_id (admin_id),
    INDEX idx_admin_audit_action_type (action_type),
    INDEX idx_admin_audit_timestamp (timestamp DESC)
);
```

**Logged Actions:**
- `impersonate` - User impersonation start
- `impersonate_exit` - User impersonation end
- `user_search` - User search query (including search term)
- `user_view` - Viewing user detail page
- `content_edit` - Question/chunk modification
- `content_delete` - Question/chunk deletion (soft delete)

**Audit Log Access:**
- Accessible via `GET /admin/audit-log` (admin-only)
- Exportable to CSV for compliance review
- Retention: 2 years (compliance requirement)

**Security Monitoring:**
- Alert if single admin performs >20 impersonations in 24 hours (unusual activity)
- Alert if impersonation duration >25 minutes (approaching limit)
- Daily audit report emailed to security team

#### Admin Session Management

**Admin-Specific Token Handling:**
- Admin tokens have `is_admin: true` claim
- Shorter expiration for admin tokens: 60 minutes (vs 15 min for regular users)
- Admin refresh tokens: 24 hours (vs 7 days for regular users)
- Admin logout invalidates ALL admin sessions (including impersonations)

#### PostHog Integration Security

**Deep Links:**
- PostHog URLs include user_id only (no PII in URL)
- PostHog access restricted to admin team (SSO integration)
- URLs generated server-side (not exposed to client for non-admins)

```python
def generate_posthog_url(user_id: UUID) -> str:
    """Generate PostHog deep link for user profile."""
    base_url = settings.POSTHOG_URL  # From environment
    return f"{base_url}/person/{user_id}"

# Only included in admin API responses
```

#### Security Checklist (Pre-Release)

- [ ] Admin flag can only be set via direct database update (verified: no API endpoint)
- [ ] `require_admin` middleware enforced on all admin routes
- [ ] Impersonation cannot target other admins (unit test coverage)
- [ ] Impersonation tokens expire in 30 minutes (non-refreshable)
- [ ] Impersonation banner shown on all pages during active session
- [ ] Rate limiting active on all admin endpoints (verified in staging)
- [ ] Audit log captures all admin actions (integration test coverage)
- [ ] Audit log retention configured (2 years)
- [ ] Security monitoring alerts configured (impersonation anomalies)
- [ ] Admin access documented in secure runbook (Confluence/Notion)

---

### Performance Optimization

**Frontend Performance:**
- **Bundle Size Target:** < 300 KB gzipped (initial load)
- **Loading Strategy:** Code splitting via React.lazy(), route-based chunks, Vite tree-shaking
- **Caching Strategy:** Service worker for static assets (future), API response caching via SWR/React Query (future)
- **Image Optimization:** WebP format, lazy loading, responsive images

**Backend Performance:**
- **Response Time Target:** < 200ms p95 for API endpoints, < 500ms for adaptive question selection (includes Qdrant query)
- **Database Optimization:** Indexes on all foreign keys and query filters, connection pooling (SQLAlchemy async pool), prepared statements
- **Caching Strategy:** Redis for user sessions, competency scores cached in PostgreSQL, Qdrant vector cache

**Qdrant Performance:**
- **HNSW Index:** m=16, ef_construct=100 (balance speed/accuracy)
- **Search Performance:** < 50ms for semantic search (3072-dim vectors, 1000+ questions)
- **Payload Filtering:** Index on `knowledge_area`, `difficulty` for fast filtered search

---
