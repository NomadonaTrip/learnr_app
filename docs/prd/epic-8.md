# Epic 8: Polish, Testing & Launch Readiness

**Epic Goal:** Complete platform polish with user settings, profile management, accessibility compliance (WCAG 2.1 AA), comprehensive error handling, production deployment configuration, and alpha test readiness. This epic ensures the platform is stable, accessible, and ready for the Day 30 case study user launch.

## Story 8.1: User Profile and Account Management

As a **user**,
I want to view and update my profile information and preferences,
so that I can keep my account details current and adjust my learning goals.

**Acceptance Criteria:**
1. GET `/api/user/profile` returns user profile data:
   - `email`, `created_at`, `onboarding_data` (7 questions answered), `exam_date`, `target_score`, `daily_time_commitment`
2. Settings page displays:
   - **Account section:** Email (editable), Password (change password option)
   - **Preferences section:** Exam date (date picker), Target score (70/80/90%), Daily time commitment (30-60 min / 1-2 hrs / 2+ hrs)
   - **Display Preferences:** Dark mode toggle (Light / Dark / Auto) - NEW MVP FEATURE
   - **Data & Privacy:** View privacy policy, Export my data, Delete account
3. PUT `/api/user/profile` updates editable fields (email, exam_date, target_score, daily_time_commitment)
4. Email change validation: Must be valid email, unique in database (409 Conflict if duplicate)
5. Password change: POST `/api/user/change-password` accepts `current_password`, `new_password`
   - Verify current password correct (401 if wrong)
   - Validate new password (8+ chars, letter + number)
   - Update hashed password in database
6. Exam date change: Recalculates "days until exam" on dashboard immediately
7. **Dark Mode Toggle:** Segmented control or dropdown with 3 options: Light / Dark / Auto (system preference)
   - Default: Auto mode (follows system preference via `prefers-color-scheme` media query)
   - Saved to user profile: `PUT /api/user/profile` with `theme_preference` field ('light' | 'dark' | 'auto')
   - Theme persists across devices and sessions (retrieved from user profile on login)
   - Root HTML class toggle: `<html class="light">` or `<html class="dark">`
   - 200ms color transition when toggling (prevents jarring flash)
   - **Complete dark mode specifications:** See `/docs/front-end-spec.md` Lines 2193-2227
8. Settings page styled consistent with dashboard (Framer-inspired, Inter font, form cards 22px radius, pill-rounded buttons)
9. Success messages: "Profile updated successfully", "Password changed successfully", "Theme preference updated"
10. Unit tests: Profile retrieval, profile update, password change, dark mode toggle, validation errors
11. Integration test: User can update preferences and changes persist across sessions, dark mode syncs across devices

## Story 8.2: Data Export and Account Deletion

As a **user concerned about data privacy**,
I want to export my data and have the option to delete my account completely,
so that I maintain control over my personal information (GDPR readiness).

**Acceptance Criteria:**
1. GET `/api/user/export` endpoint generates JSON export of all user data:
   - User profile (email, created_at, onboarding_data)
   - Competency scores (all 6 KAs, historical snapshots)
   - Quiz responses (all questions answered, timestamps, correctness)
   - Reading history (chunks read, engagement data)
   - Concept mastery state (spaced repetition data)
2. Export downloaded as `learnr_data_{user_id}_{date}.json` file (client-side download trigger)
3. DELETE `/api/user/account` endpoint deletes user account and all associated data:
   - Soft delete or hard delete (hard delete for MVP to truly remove data)
   - Cascade delete: Remove from `users`, `onboarding_data`, `competency_tracking`, `quiz_responses`, `concept_mastery`, `reading_history`, etc.
   - Confirmation step: Frontend shows modal "Are you sure? This cannot be undone. Type DELETE to confirm"
4. After deletion: User logged out, JWT invalidated, redirect to landing page with message "Account deleted successfully"
5. Settings page: "Export My Data" button (downloads JSON), "Delete Account" button (opens confirmation modal)
6. Privacy policy link: Links to `/privacy` page (static page with LearnR privacy policy)
7. Terms of service link: Links to `/terms` page (static page with terms)
8. Unit tests: Data export includes all user data, account deletion removes all records
9. Integration test: Full export → delete → verify user cannot log in and data removed from database
10. Compliance: GDPR right to be forgotten satisfied (user can delete all data)

## Story 8.3: WCAG 2.1 Level AA Accessibility Compliance

As a **user with disabilities**,
I want the platform to be fully accessible via keyboard and screen reader,
so that I can use LearnR regardless of visual or motor impairments.

**Acceptance Criteria:**
1. **Keyboard Navigation:**
   - All interactive elements (buttons, links, form inputs, cards) accessible via Tab key
   - Tab order is logical (follows visual flow: top to bottom, left to right)
   - Focus indicators visible on all focusable elements (2px outline, high contrast color)
   - Enter/Space keys activate buttons and links
   - Escape key closes modals and dropdowns
2. **Screen Reader Compatibility:**
   - Semantic HTML: Use `<button>`, `<nav>`, `<main>`, `<section>`, `<article>` appropriately
   - ARIA labels on interactive elements: `aria-label` for icon buttons, `aria-describedby` for form field hints
   - Alt text on all images/icons (or `aria-hidden="true"` for decorative elements)
   - Form labels properly associated with inputs (`<label for="email">`)
   - Screen reader announcements for dynamic content (e.g., "Correct answer" announced after quiz submission)
3. **Color Contrast:**
   - Text contrast ratio: 4.5:1 for normal text (Inter font), 3:1 for large text (18pt+)
   - Button contrast: Primary buttons have 3:1 contrast with background
   - Visual indicators not color-only: Use icons + text (e.g., green checkmark + "Correct", not just green)
4. **Text Resizing:**
   - Page remains functional when text resized to 200% (browser zoom or font size increase)
   - No horizontal scrolling required, content reflows responsively
5. **No Flashing Content:** No animations or transitions flash >3 times per second (seizure risk)
6. **Descriptive Links:** Link text is descriptive (not "click here"), e.g., "View Knowledge Area details"
7. **Accessibility Audit Tools:**
   - Run axe DevTools or WAVE on all key pages (landing, dashboard, quiz, settings)
   - Fix all Critical and Serious issues flagged
   - Document any Minor issues deferred to Phase 2
8. Manual testing: Navigate entire quiz flow using only keyboard (no mouse)
9. Screen reader testing: Use NVDA (Windows) or VoiceOver (Mac) to navigate dashboard and quiz
10. README documents accessibility commitment and how to report issues

## Story 8.4: Error Handling and User-Friendly Messages

As a **user encountering errors**,
I want clear, helpful error messages that guide me to resolution,
so that I'm not frustrated or confused when something goes wrong.

**Acceptance Criteria:**
1. **API Error Responses:** Standardized JSON format:
   ```json
   {
     "error": "ValidationError",
     "message": "Password must be at least 8 characters with letter and number",
     "field": "password"
   }
   ```
2. **Frontend Error Display:**
   - Inline validation errors on forms (red text below field, e.g., "Email already exists")
   - Toast/snackbar notifications for global errors (e.g., "Network error, please try again")
   - Modal dialogs for critical errors (e.g., "Session expired, please log in again")
3. **Error Categories:**
   - **400 Bad Request:** Validation errors → show specific field error
   - **401 Unauthorized:** Session expired → redirect to login with message
   - **403 Forbidden:** Access denied → "You don't have permission to access this"
   - **404 Not Found:** Resource not found → "Question not found" or "Page not found"
   - **409 Conflict:** Duplicate resource → "Email already registered"
   - **500 Internal Server Error:** Server error → "Something went wrong. Please try again or contact support."
4. **Network Errors:** Offline or timeout → "Connection lost. Check your internet and try again."
5. **Retry Logic:** Transient errors (500, network timeout) automatically retry 1-2 times before showing error to user
6. **Error Logging:** All errors logged server-side with context (user_id, endpoint, request payload, stack trace) for debugging
7. **User Support Link:** All error messages include "Contact Support" link (opens email or help page)
8. **Loading States:** Spinners or skeleton screens during API calls (prevent user thinking app is frozen)
9. Unit tests: Error responses formatted correctly, frontend displays appropriate messages
10. Integration test: Simulate various errors (validation, auth, network) and verify user sees helpful messages

## Story 8.5: Production Deployment and Environment Configuration

As a **DevOps engineer**,
I want the application deployed to production with proper environment configuration and monitoring,
so that the platform is stable and accessible for the case study user launch.

**Acceptance Criteria:**
1. **Frontend Deployment:**
   - Deploy React app to Vercel or Netlify (per Technical Assumptions)
   - Environment variables: `VITE_API_URL` (backend URL), `VITE_ENV` (production)
   - Custom domain configured (e.g., `app.learnr.com`)
   - HTTPS enforced (SSL certificate auto-provisioned)
   - Build optimized: Code splitting, minification, gzip compression
2. **Backend Deployment:**
   - Deploy FastAPI to Railway or Render (containerized deployment)
   - Environment variables: `DATABASE_URL` (PostgreSQL), `QDRANT_URL`, `OPENAI_API_KEY`, `JWT_SECRET_KEY`, `ENV=production`
   - Health check endpoint `/health` monitored by platform
   - Auto-scaling configured (start with 1 instance, scale up if load >80% CPU)
3. **Database:**
   - PostgreSQL managed service (Railway/Render Postgres or similar)
   - Daily automated backups with 7-day retention
   - Connection pooling configured (max 10 connections for MVP)
4. **Qdrant:**
   - Self-hosted Qdrant via Docker on backend server (cost $0)
   - Alternative: Migrate to Qdrant Cloud if performance issues (budget $50-100/month approved)
   - Qdrant data persisted to volume (survives container restart)
5. **CI/CD Pipeline:**
   - GitHub Actions workflow triggers on push to `main` branch
   - Run tests (unit + integration) → if pass, deploy to production
   - Deployment rollback capability (revert to previous version if issues detected)
6. **Monitoring:**
   - Error tracking: Sentry or similar integrated (capture all 500 errors, unhandled exceptions)
   - Uptime monitoring: UptimeRobot or similar pings `/health` every 5 minutes
   - Alerts: Email/Slack notification if health check fails or error rate >5%
7. **Performance:**
   - Frontend initial load <3 seconds (verified with Lighthouse)
   - Backend API response times <500ms for quiz questions, <1 second for reading content
8. README documents deployment process, environment variables, and rollback procedure
9. Smoke tests: After deployment, manually verify key flows (register, login, quiz, dashboard)
10. Case study user access: Provide login credentials, confirm user can access production app

## Story 8.6: Alpha Test Readiness and Day 24 Go/No-Go Preparation

As a **product manager**,
I want all alpha test instrumentation and success criteria tracking in place,
so that we can make a data-driven Go/No-Go decision on Day 24.

**Acceptance Criteria:**
1. **Alpha Test Instrumentation:**
   - Reading engagement tracking (Story 5.3) fully functional
   - Reading relevance feedback (Story 5.4) fully functional
   - Explanation helpfulness feedback (Story 4.5) fully functional
   - Review accuracy tracking (Story 7.4) fully functional
2. **Success Metrics Dashboard (Internal, not user-facing):**
   - GET `/api/admin/alpha-metrics` endpoint returns:
     - Reading engagement rate (% chunks expanded vs. displayed) - target 60%+
     - Reading relevance rate (% thumbs up) - target 80%+
     - Explanation helpfulness (% thumbs up) - target 85%+
     - Review accuracy (% correct) - target 70%+
     - Daily active usage (% of days user logged in) - target 80%+
3. **Case Study User Onboarding:**
   - User account created, onboarding completed, diagnostic taken (baseline established)
   - User provided with clear instructions: "Complete daily sessions for next 30 days, exam Dec 21"
   - Feedback mechanism: User can send feedback anytime (email, in-app form, or scheduled check-ins)
4. **Day 24 Alpha Test:**
   - Schedule user interview/survey on Day 24 (November 14, 2025 if launch Nov 21)
   - Survey questions:
     - "How relevant was the BABOK reading content to your gaps?" (1-5 scale)
     - "Did the reading content help you understand concepts better?" (Yes/Somewhat/No)
     - "Would you recommend LearnR over static quiz apps?" (Yes/No, why?)
     - "Do you plan to continue using LearnR for the remaining 30 days?" (Yes/No)
   - Go criteria (from Brief):
     - ✓ User finds BABOK reading content valuable (80%+ helpful rating)
     - ✓ User commits to daily usage for remaining 30 days
     - ✓ User can articulate differentiation vs. static quiz apps
5. **No-Go Plan:**
   - If reading content not valued: Iterate UX (make more prominent, improve relevance) OR pivot strategy (focus on adaptive quiz only)
   - If user not committing to continued usage: Diagnose blockers (UX issues, time commitment, feature gaps)
6. **Alpha Test Documentation:**
   - `/docs/alpha_test_plan.md` outlines schedule, metrics, Go/No-Go criteria
   - Daily progress log: Track user engagement, issues reported, feedback collected
7. Unit tests: Admin metrics endpoint returns accurate alpha test data
8. Integration test: Full alpha test flow simulated (onboarding → diagnostic → quiz → reading → reviews)
9. Stakeholder readiness: Product team briefed on Day 24 decision process
10. Contingency time: Days 25-30 available for iteration if No-Go (adjust features, re-test)

## Story 8.7: Admin Support Tools for Alpha Test

As a **platform administrator**,
I want to search for users, impersonate their sessions, and view their analytics in PostHog,
so that I can provide support during alpha test and debug user-reported issues.

**Acceptance Criteria:**

1. **Admin Role Management:**
   - `users` table includes `is_admin` boolean column (default: false)
   - Admin users designated via direct database flag (no self-service promotion)
   - Only users with `is_admin = true` can access admin endpoints

2. **Admin Middleware:**
   - Implement `@require_admin` decorator/middleware extending JWT auth
   - Check `is_admin` claim in decoded JWT
   - Return 403 Forbidden if user not admin
   - All `/api/admin/*` endpoints protected by this middleware

3. **User Search:**
   - GET `/api/admin/users/search?q={query}` endpoint
   - Searches across: email (partial match), user_id (exact), name (if stored)
   - Response: Array of user objects with:
     - `user_id`, `email`, `created_at`, `onboarding_completed`, `exam_date`, `last_login_at`
   - Pagination: `?limit=20&offset=0` (default 20 results)
   - Sorting: `?sort_by=created_at&order=desc`

4. **User Impersonation:**
   - POST `/api/admin/impersonate/{user_id}` endpoint
   - Validates: user_id exists, requester is admin
   - Generates new JWT with:
     - `user_id`: target user's ID (not admin's)
     - `impersonated_by`: admin's user_id
     - `exp`: 30 minutes from now (short-lived token)
   - Response: `{access_token, user_email, expires_in_seconds}`
   - Frontend stores impersonation token separately from admin token

5. **Impersonation Session UI:**
   - Frontend detects impersonation token (checks for `impersonated_by` claim)
   - Displays persistent banner at top of ALL pages:
     - Background: Orange/yellow (high visibility)
     - Text: "🔍 Viewing as user@email.com"
     - Button: "Exit Impersonation" (pill-rounded, secondary)
   - Banner not dismissible (always visible during impersonation)
   - All API calls use impersonation token (user sees their actual data)

6. **Exit Impersonation:**
   - POST `/api/admin/impersonate/exit` endpoint
   - Invalidates impersonation token
   - Frontend switches back to admin's original token
   - Redirect to admin dashboard or user search

7. **Impersonation Audit Trail:**
   - Create `admin_audit_log` table:
     - `id`, `admin_user_id`, `action_type`, `target_user_id`, `metadata` (JSONB), `timestamp`
   - Log events: "impersonation_started", "impersonation_ended"
   - Metadata includes: `duration_seconds`, `ip_address`, `user_agent`
   - GET `/api/admin/audit-log` returns recent admin actions (for compliance)

8. **PostHog Integration:**
   - PostHog SDK configured in backend and frontend
   - User events tracked with `user_id` as distinct_id (PostHog identifier)
   - Admin user search results include "View in PostHog" link:
     - URL format: `https://app.posthog.com/person/{user_id}` (or PostHog-specific URL)
     - Opens in new tab
   - Link styled as tertiary action (icon: analytics)

9. **Security Safeguards:**
   - Impersonation tokens cannot impersonate other admins (403 if target user is admin)
   - Rate limiting on impersonation: Max 10 impersonations per admin per hour
   - Email notification to user if impersonated (optional, configurable)
   - Admin cannot modify user data during impersonation (read-only mode recommended, or log all changes)

10. **Testing:**
    - Unit tests: Admin middleware blocks non-admin, allows admin
    - Unit tests: Impersonation token generation includes correct claims
    - Integration test: Admin can search user, impersonate, view dashboard as user, exit
    - Integration test: PostHog link renders correctly on user search results
    - Security test: Non-admin cannot access `/api/admin/*` endpoints

**Admin UI Specifications:**

This story defines admin functional requirements. Detailed admin UI specifications should be documented in `/docs/front-end-spec.md` including:

- **Admin User Search Screen:** Layout, search bar, results table, action buttons
- **Impersonation Banner Component:** Persistent orange banner design, exit button placement
- **Admin Dashboard:** (if separate from main dashboard) user list, metrics, audit log access
- **PostHog Link Integration:** Icon, tooltip, visual styling

**Recommended Frontend Spec Addition:**
Add "Screen 9: Admin Support Interface" section with ASCII wireframes for:
1. User search page layout
2. Impersonation banner (shown across all pages during impersonation)
3. Admin dashboard (if needed)

See Story 8.7 Acceptance Criteria above for complete functional requirements.
