# API Specification

### REST API Specification

The LearnR API follows RESTful conventions with JSON payloads. All endpoints require JWT authentication except `/auth/*` routes.

**Base URL:** `https://api.learnr.com/v1` (production) | `http://localhost:8000/v1` (development)

**Authentication:** Bearer token in `Authorization` header: `Authorization: Bearer <jwt_token>`

**Error Format:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid email format",
    "details": { "field": "email" },
    "timestamp": "2025-11-21T10:30:00Z",
    "request_id": "req_abc123"
  }
}
```

**Key Endpoints:**

- `POST /auth/register` - Register new user account
- `POST /auth/login` - Authenticate user
- `POST /auth/refresh` - Refresh access token
- `GET /users/me` - Get current user profile
- `PUT /users/me` - Update user profile
- `POST /diagnostic/start` - Start diagnostic assessment
- `GET /diagnostic/{session_id}/questions` - Get next diagnostic question
- `POST /diagnostic/{session_id}/submit` - Submit diagnostic answer
- `GET /diagnostic/{session_id}/results` - Get diagnostic results
- `POST /sessions` - Start new quiz session
- `GET /sessions/{session_id}` - Get session details
- `POST /sessions/{session_id}/end` - End session
- `GET /questions/next` - Get next adaptive question
- `POST /questions/{question_id}/answer` - Submit answer to question
- `GET /competency` - Get all competency scores
- `GET /reading-queue` - Get reading queue
- `GET /reading-queue/{item_id}` - Get reading item details
- `PUT /reading-queue/{item_id}` - Update reading item
- `GET /reviews/due` - Get reviews due count
- `POST /sessions/{id}/review/start` - Start post-session review
- `POST /sessions/{id}/review/answer` - Submit review answer
- `GET /analytics/dashboard` - Get dashboard data

### Admin API Endpoints

**Authentication:** All admin endpoints require `is_admin: true` flag in JWT token. Protected by `@require_admin` middleware (extends `@require_auth`).

**Rate Limiting:** Admin endpoints have dedicated rate limits:
- User search: 100 requests/hour per admin
- Impersonation: 10 requests/hour per admin (security-sensitive)
- General admin operations: 500 requests/hour per admin

**Endpoints:**

#### User Management

- `GET /admin/users/search?q={query}` - Search users by email, user_id, or name
  - **Query Parameters:**
    - `q` (string, required): Search query (minimum 3 characters)
    - `limit` (integer, optional): Results limit (default: 20, max: 100)
    - `offset` (integer, optional): Pagination offset (default: 0)
  - **Response:**
    ```json
    {
      "total": 42,
      "results": [
        {
          "user_id": "uuid",
          "email": "user@example.com",
          "created_at": "2025-11-20T10:30:00Z",
          "onboarding_completed": true,
          "exam_date": "2025-12-21",
          "last_login": "2025-11-21T08:15:00Z",
          "exam_readiness": 73
        }
      ]
    }
    ```
  - **Error Codes:** 400 (query too short), 403 (not admin), 429 (rate limit)

- `GET /admin/users/{user_id}` - Get detailed user profile (admin view)
  - **Response:** Full user object + analytics summary + PostHog deep link
    ```json
    {
      "user": { /* Full User object */ },
      "analytics": {
        "total_sessions": 24,
        "total_questions_answered": 312,
        "avg_session_duration_minutes": 18,
        "competency_progression": [ /* 7-day history */ ]
      },
      "posthog_url": "https://app.posthog.com/person/{user_id}"
    }
    ```

#### Impersonation

- `POST /admin/impersonate/{user_id}` - Impersonate user (generates special JWT)
  - **Request Body:** None
  - **Response:**
    ```json
    {
      "impersonation_token": "jwt_token_here",
      "user": { /* User object being impersonated */ },
      "expires_at": "2025-11-21T11:00:00Z",
      "impersonated_by": "admin_user_id"
    }
    ```
  - **Token Claims:**
    ```json
    {
      "sub": "impersonated_user_id",
      "impersonated_by": "admin_user_id",
      "is_impersonation": true,
      "exp": 1732186800  // 30 minutes from issue
    }
    ```
  - **Restrictions:**
    - Cannot impersonate other admins (403 error)
    - Token expires in 30 minutes (non-refreshable)
    - Only one active impersonation session per admin at a time
    - All actions logged to `admin_audit_log` table
  - **Error Codes:** 403 (target is admin / permission denied), 404 (user not found), 429 (rate limit)

- `POST /admin/exit-impersonation` - Exit impersonation session (returns to admin session)
  - **Request:** Must provide impersonation token
  - **Response:**
    ```json
    {
      "message": "Impersonation ended",
      "admin_token": "original_admin_jwt",
      "duration_seconds": 1245
    }
    ```
  - **Side Effect:** Audit log updated with session duration

#### Audit Log

- `GET /admin/audit-log` - Get admin action audit trail
  - **Query Parameters:**
    - `admin_id` (uuid, optional): Filter by admin user
    - `action_type` (string, optional): Filter by action (e.g., "impersonate", "user_search")
    - `start_date` (ISO 8601, optional): Filter from date
    - `end_date` (ISO 8601, optional): Filter to date
    - `limit` (integer, optional): Results limit (default: 50, max: 500)
  - **Response:**
    ```json
    {
      "total": 128,
      "logs": [
        {
          "id": "uuid",
          "admin_id": "admin_uuid",
          "admin_email": "admin@learnr.com",
          "action_type": "impersonate",
          "target_user_id": "user_uuid",
          "target_email": "user@example.com",
          "timestamp": "2025-11-21T10:00:00Z",
          "duration_seconds": 1245,
          "ip_address": "192.168.1.1",
          "user_agent": "Mozilla/5.0..."
        }
      ]
    }
    ```

#### Content Management

- `POST /admin/questions/flag` - Flag question for review
- `PUT /admin/questions/{question_id}` - Update question (admin edit)
- `DELETE /admin/questions/{question_id}` - Delete question (soft delete)
- `POST /admin/reading-chunks/update` - Update BABOK chunk content

**PostHog Integration:**

All admin user detail views (`GET /admin/users/{user_id}`) return a `posthog_url` field with deep link to PostHog user profile:
```
https://app.posthog.com/person/{user_id}
```

Frontend should render this as a clickable link: **"View in PostHog →"**

**Security Features:**

1. **Admin Flag Protection:** `is_admin` flag can only be set via direct database update (no API endpoint for promotion)
2. **Impersonation Banner:** Frontend must show persistent banner when in impersonation mode:
   ```
   ⚠️ Viewing as user@example.com | Exit Impersonation
   ```
3. **Audit Trail:** All admin actions automatically logged with IP, timestamp, user agent
4. **Rate Limiting:** Aggressive rate limits on sensitive operations (impersonation: 10/hour)
5. **Session Isolation:** Impersonation tokens cannot be refreshed; 30-minute hard limit

**Full OpenAPI 3.0 specification available at `/docs` (Swagger UI) and `/redoc` (ReDoc) when API is running.**

---
