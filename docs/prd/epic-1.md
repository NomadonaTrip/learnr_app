# Epic 1: Foundation & User Authentication

**Epic Goal:** Establish the technical foundation for LearnR by setting up the monorepo structure, development environment, databases (PostgreSQL and Qdrant), and implementing secure user authentication. This epic delivers a working full-stack application with user registration, login, password management, and a health-check endpoint demonstrating end-to-end integration.

## Story 1.1: Monorepo Setup and Project Scaffolding

As a **developer**,
I want to set up a monorepo with frontend and backend scaffolding,
so that the team has a consistent development environment and can begin building features immediately.

**Acceptance Criteria:**
1. Monorepo structure created with `/frontend`, `/backend`, `/shared`, `/scripts`, `/docs` directories
2. Frontend: React 18+ with TypeScript, Vite build tool, basic folder structure (`/src/components`, `/src/pages`, `/src/hooks`, `/src/utils`)
3. Backend: Python 3.11+ with FastAPI, basic folder structure (`/app/api`, `/app/models`, `/app/services`, `/app/utils`)
4. Package managers configured: npm/yarn for frontend, poetry/pip for backend
5. Environment variable management: `.env.example` files in both frontend and backend with required variables documented
6. README.md files in root and each directory explaining setup and development commands
7. Git repository initialized with `.gitignore` for Node, Python, environment files
8. Both frontend and backend can start locally (frontend on localhost:3000, backend on localhost:8000)

## Story 1.2: PostgreSQL Database Setup and Schema Initialization

As a **backend developer**,
I want to set up PostgreSQL with initial schema and migrations,
so that user data and application state can be persisted reliably.

**Acceptance Criteria:**
1. PostgreSQL database created locally (development) with connection configuration
2. Alembic migrations configured for schema version control
3. Initial schema migration created with core tables:
   - `users` table (id, email, hashed_password, created_at, updated_at)
   - `onboarding_data` table (user_id FK, referral_source, certification, motivation, exam_date, knowledge_level, target_score, daily_study_time)
4. SQLAlchemy models created for `User` and `OnboardingData` with Pydantic schemas
5. Database connection pooling configured in FastAPI
6. Migration commands documented in README (`alembic upgrade head`, `alembic downgrade`, etc.)
7. Test database setup for running tests in isolation
8. All tables have appropriate indexes on foreign keys and frequently queried columns

## Story 1.3: User Registration API

As a **user**,
I want to create an account with my email and password,
so that I can save my progress and access personalized learning features.

**Acceptance Criteria:**
1. POST `/api/auth/register` endpoint accepts `email` and `password` in request body
2. Email validation: Must be valid email format, unique in database (return 409 Conflict if duplicate)
3. Password validation: Minimum 8 characters, must contain at least one letter and one number
4. Password hashed using bcrypt or Argon2 before storage (never store plaintext)
5. User record created in `users` table with hashed password
6. Response returns user object (id, email, created_at) and JWT token with 7-day expiration
7. JWT token includes user_id in payload for authentication
8. Error responses: 400 Bad Request for validation errors, 409 Conflict for duplicate email, 500 Internal Server Error for database issues
9. Unit tests: Valid registration, duplicate email, weak password, invalid email format
10. Integration test: Full registration flow creates user in database and returns valid JWT

## Story 1.4: User Login API

As a **registered user**,
I want to log in with my email and password,
so that I can access my personalized learning dashboard and progress.

**Acceptance Criteria:**
1. POST `/api/auth/login` endpoint accepts `email` and `password` in request body
2. User lookup by email (case-insensitive)
3. Password verification using bcrypt/Argon2 compare function
4. On successful authentication: Return JWT token (7-day expiration) and user object
5. On failed authentication: Return 401 Unauthorized with generic message "Invalid email or password" (no distinction to prevent enumeration)
6. JWT token structure same as registration (user_id in payload)
7. Rate limiting: Maximum 5 login attempts per email per 15 minutes (prevent brute force)
8. Unit tests: Valid login, invalid password, non-existent email, rate limiting
9. Integration test: Login returns valid JWT that can be used for authenticated endpoints
10. Security: No sensitive information in error messages, timing-safe password comparison

## Story 1.5: Password Reset Flow

As a **user who forgot my password**,
I want to reset my password via email verification,
so that I can regain access to my account securely.

**Acceptance Criteria:**
1. POST `/api/auth/forgot-password` endpoint accepts `email`
2. Generate secure password reset token (UUID or similar, 1-hour expiration)
3. Store reset token in database with expiration timestamp (new `password_reset_tokens` table or add to `users`)
4. Send password reset email with reset link: `https://app.learnr.com/reset-password?token={token}`
5. Email sent even if email not found (prevent email enumeration, but no token created)
6. POST `/api/auth/reset-password` endpoint accepts `token` and `new_password`
7. Token validation: Exists, not expired, not already used
8. Password validation: Same rules as registration (8+ chars, letter + number)
9. Update user password (hash new password), invalidate reset token
10. Return success message (no JWT - user must log in with new password)
11. Unit tests: Valid reset, expired token, invalid token, weak new password
12. Integration test: Full password reset flow from forgot to login with new password

## Story 1.6: JWT Authentication Middleware

As a **backend developer**,
I want JWT authentication middleware protecting authenticated endpoints,
so that only logged-in users can access protected resources.

**Acceptance Criteria:**
1. Middleware function `verify_jwt_token` that extracts JWT from `Authorization: Bearer {token}` header
2. Token validation: Signature valid, not expired, contains required `user_id` claim
3. On valid token: Attach `current_user` to request context (user_id, email)
4. On invalid/missing token: Return 401 Unauthorized with message "Authentication required"
5. Decorator `@require_auth` to protect routes (e.g., `@require_auth` above route handler)
6. Protected route example: GET `/api/user/profile` returns current user's profile
7. Unit tests: Valid token grants access, expired token denied, missing token denied, invalid signature denied
8. Integration test: Protected endpoint accessible with valid JWT, denied without JWT
9. Token refresh not implemented in MVP (7-day expiration sufficient)
10. Security: Token stored securely in frontend (HttpOnly cookie or secure localStorage, TBD by frontend)

## Story 1.7: Health Check and API Documentation

As a **developer or DevOps engineer**,
I want a health check endpoint and auto-generated API documentation,
so that I can verify the backend is running and understand available endpoints.

**Acceptance Criteria:**
1. GET `/health` endpoint returns `200 OK` with JSON `{"status": "healthy", "timestamp": "ISO8601"}`
2. Health check verifies database connectivity (PostgreSQL ping)
3. FastAPI auto-generated OpenAPI documentation available at `/docs` (Swagger UI)
4. `/docs` shows all implemented endpoints with request/response schemas
5. `/redoc` alternative documentation format available
6. Health check does not require authentication (publicly accessible for monitoring)
7. API documentation shows authentication requirements (lock icon) for protected endpoints
8. Response examples included in API docs for each endpoint
9. Health check returns 503 Service Unavailable if database connection fails
10. README documents how to access API docs and health check endpoint
