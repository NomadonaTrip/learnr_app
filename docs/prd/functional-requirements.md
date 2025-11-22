# Functional Requirements

### FR1: Anonymous Onboarding & Personalization (Pre-Registration)

**FR1.1:** Landing page displays value proposition with first onboarding question inline (immediate engagement, no separate CTA button)
**FR1.2:** Users progress through 7 questions sequentially without authentication
**FR1.3:** System collects: (1) referral source, (2) certification choice, (3) motivation, (4) exam date, (5) current knowledge level, (6) target score, (7) daily study time
**FR1.4:** System stores onboarding responses temporarily in browser session/localStorage (no server storage yet)
**FR1.5:** After question 7, system prompts: "Create your account to save your progress and start your diagnostic assessment"
**FR1.6:** System persists all 7 onboarding answers to user profile upon account creation
**FR1.7:** Users can update onboarding preferences anytime from settings after registration

### FR2: User Account & Authentication (Post-Onboarding)

**FR2.1:** Users create accounts with email and password after completing 7-question onboarding flow
**FR2.2:** Account creation form pre-fills with onboarding context (e.g., exam date already collected)
**FR2.3:** Users can log in securely with email and password on return visits
**FR2.4:** Users can reset forgotten passwords via email verification
**FR2.5:** Users can update email address and password from settings
**FR2.6:** Users can delete their account and all associated data
**FR2.7:** System maintains user sessions across browser sessions (7-day JWT expiration)
**FR2.8:** System logs users out after 7 days of inactivity for security

### FR3: Personalization & Preference Management

**FR3.1:** System uses exam date to calculate days remaining (displayed on dashboard)
**FR3.2:** System uses knowledge level and target score to set initial recommendations
**FR3.3:** System stores all onboarding preferences in user profile for adaptive algorithm
**FR3.4:** Users can update preferences anytime from settings (exam date, target score, daily study time)
**FR3.5:** Preference changes immediately affect recommendations and pacing suggestions

### FR4: Initial Diagnostic Assessment

**FR4.1:** Users take a 12-question diagnostic assessment immediately after account creation (3 questions per KA, 6 KAs total)
**FR4.2:** System presents diagnostic questions in balanced order (not clustered by KA)
**FR4.3:** System provides no feedback during diagnostic (answers only recorded)
**FR4.4:** System calculates baseline competency scores for all 6 KAs after completion
**FR4.5:** System presents diagnostic results with competency bars and gap analysis
**FR4.6:** System recommends which KAs to focus on based on diagnostic results
**FR4.7:** Users can retake diagnostic at any time from settings (resets competency baseline)

### FR5: Competency Tracking & Estimation

**FR5.1:** System maintains real-time competency scores for each of 6 CBAP knowledge areas
**FR5.2:** System updates competency scores after every quiz response using IRT model
**FR5.3:** System calculates exam readiness score based on all 6 KA competencies
**FR5.4:** System tracks user performance history (all responses, timestamps, questions)
**FR5.5:** System calculates weekly progress deltas (improvement tracking)
**FR5.6:** System identifies specific concept gaps within each KA
**FR5.7:** System provides competency predictions (projected readiness by exam date)

### FR5A: Adaptive Question Selection

**FR5A.1:** System selects questions adaptively based on user competency profile
**FR5A.2:** System prioritizes questions from weakest knowledge areas
**FR5A.3:** System matches question difficulty to user's current competency level (+/- 1 level)
**FR5A.4:** System prevents recently seen questions from reappearing (minimum 7 days between repeats)
**FR5A.5:** System mixes question sources (gold standard + LLM variations) transparently
**FR5A.6:** System tracks which questions user has seen and answered
**FR5A.7:** System adjusts difficulty up after consecutive correct answers (3+)
**FR5A.8:** System adjusts difficulty down after consecutive incorrect answers (3+)

### FR6: Quiz Session Management

**FR6.1:** Users can start a quiz session from dashboard
**FR6.2:** System creates a mixed session (reviews + new content) when reviews are due
**FR6.3:** System creates a new content session when no reviews are due
**FR6.4:** Users answer questions one at a time (single question focus)
**FR6.5:** Users can pause/exit quiz session anytime (progress saved)
**FR6.6:** Users can resume paused sessions from where they left off
**FR6.7:** System tracks session metadata (start time, duration, questions answered)
**FR6.8:** Users can end session early or continue indefinitely (user-controlled length)

### FR7: Question Presentation & Answer Submission

**FR7.1:** System displays question text with 4 multiple-choice options (A, B, C, D)
**FR7.2:** System displays question metadata: Knowledge Area, Progress indicator (X of Y in session)
**FR7.3:** Users select one answer option (radio button or card selection)
**FR7.4:** Users submit answer with clear "Submit Answer" action
**FR7.5:** System provides immediate visual feedback (correct = green, incorrect = red/orange)
**FR7.6:** System prevents answer changes after submission (committed answer)
**FR7.7:** System records response, timestamp, time taken, and correctness

### FR8: Answer Explanations

**FR8.1:** System displays detailed explanation immediately after answer submission
**FR8.2:** Explanation includes: why correct answer is correct, why incorrect options are wrong
**FR8.3:** Explanation references BABOK section when applicable
**FR8.4:** Users can rate explanation helpfulness (thumbs up/down)
**FR8.5:** Users can report incorrect questions or explanations (feedback mechanism)
**FR8.6:** System displays explanation before showing reading content (logical flow)

### FR8.5: Post-Session Review (NEW)

**FR8.5.1:** System detects incorrect answers during session and flags for review
**FR8.5.2:** After session ends, system displays transition screen if incorrect answers exist
**FR8.5.3:** Transition screen shows session summary (X/Y correct) and review prompt
**FR8.5.4:** Users can choose to start review immediately or skip (optional but encouraged)
**FR8.5.5:** If skipped, system adds questions to spaced repetition schedule
**FR8.5.6:** Review presents each incorrect question again with "REVIEW" badge
**FR8.5.7:** System shows original answer vs correct answer as context
**FR8.5.8:** User re-answers question; system provides immediate feedback
**FR8.5.9:** System tracks "reinforcement": incorrect → correct on review
**FR8.5.10:** System shows explanation after each review answer
**FR8.5.11:** System displays review summary: "X reinforced correctly, Y still incorrect"
**FR8.5.12:** Summary shows improvement: "Original: 80% → Final: 93%"
**FR8.5.13:** System stores review data in `session_reviews` and `review_attempts` tables
**FR8.5.14:** Review contributes to competency updates (weighted appropriately)

### FR9: Asynchronous Reading Library (UPDATED)

**FR9.1:** System retrieves 2-3 relevant BABOK chunks **asynchronously** (background task) after each answer
**FR9.2:** Reading materials added to user's reading queue with priority (High/Medium/Low)
**FR9.3:** Priority calculated based on: user competency, was_incorrect, question difficulty
**FR9.4:** System updates navigation badge count **silently** (no popups/toasts) - e.g., [6] → [7]
**FR9.5:** **Zero interruption** to learning flow during quiz sessions
**FR9.6:** Reading Library accessible from main navigation anytime
**FR9.7:** Reading Library displays queue items sorted by priority (default)
**FR9.8:** Each item shows: title, BABOK section, KA, relevance score, priority, estimated read time
**FR9.9:** Each item shows context: which question prompted it, when added
**FR9.10:** Users can filter by: KA, priority, reading status (unread/reading/completed)
**FR9.11:** Users can search reading queue by keyword
**FR9.12:** Users can click "Read Now" to view full content in modal/page
**FR9.13:** System tracks engagement: times_opened, total_reading_time_seconds
**FR9.14:** Users can mark items as "Completed" or "Dismissed"
**FR9.15:** System supports bulk actions (dismiss multiple items)
**FR9.16:** Reading content includes: full markdown text, BABOK section, related question link
**FR9.17:** Users can rate reading helpfulness (thumbs up/down)
**FR9.18:** System displays reading stats: completion rate, total time, by KA breakdown
**FR9.19:** System prevents duplicate items (unique: user_id + chunk_id)
**FR9.20:** Reading queue stored in `reading_queue` table with all engagement metadata

### FR10: Spaced Repetition System

**FR10.1:** System tracks concept mastery for spaced repetition scheduling
**FR10.2:** System schedules concept reviews based on SM-2 algorithm (1, 3, 7, 14 day intervals)
**FR10.3:** System identifies when review questions are due (past scheduled date)
**FR10.4:** System creates mixed sessions: 40% reviews + 60% new when reviews are due
**FR10.5:** System labels review questions clearly ("Review" badge or indicator)
**FR10.6:** System updates review schedule based on review performance (correct = longer interval, incorrect = reset)
**FR10.7:** System prioritizes overdue reviews (past due date) over newly due reviews
**FR10.8:** System shows "Reviews Due" count on dashboard (motivational indicator)

### FR11: Progress Dashboard

**FR11.1:** Dashboard displays 6 KA competency bars with current scores (0-100% or equivalent scale)
**FR11.2:** Dashboard shows exam readiness score (overall preparedness indicator)
**FR11.3:** Dashboard displays reviews due count (number of concepts needing review)
**FR11.4:** Dashboard shows days until exam (countdown from onboarding exam date)
**FR11.5:** Dashboard displays weekly progress chart (competency changes over time)
**FR11.6:** Dashboard provides recommended focus areas (weakest KAs to study)
**FR11.7:** Dashboard shows total questions answered and reading content consumed
**FR11.8:** Dashboard includes primary action: "Continue Learning" or "Start Review"
**FR11.9:** Navigation includes Reading Library link with unread badge count (e.g., [7])
**FR11.10:** Badge shows high-priority indicator (red) if high-priority items exist
**FR11.11:** (Optional) Dashboard widget shows top 3 priority reading items

### FR12: Knowledge Area Detail View

**FR12.1:** Users can click/tap on a KA bar to view detailed competency breakdown
**FR12.2:** Detail view shows: current competency, target competency, gap, specific concept gaps
**FR12.3:** Detail view displays recent performance on this KA (last 10 questions)
**FR12.4:** Detail view shows time spent on this KA
**FR12.5:** Detail view provides action: "Study [KA Name]" to start focused session
**FR12.6:** System allows users to start KA-specific quiz sessions (focused learning)

### FR13: Settings & Preferences

**FR13.1:** Users can update profile information (name, email)
**FR13.2:** Users can update password
**FR13.3:** Users can update onboarding preferences (exam date, target score, study time)
**FR13.4:** Users can update notification preferences (if implemented)
**FR13.5:** Users can view privacy policy and terms of service
**FR13.6:** Users can export their data (responses, progress, study history)
**FR13.7:** Users can delete their account (with confirmation step)
**FR13.8:** Users can toggle between light mode, dark mode, or auto (system preference) - NEW MVP FEATURE
**FR13.9:** Dark mode preference persists across devices and sessions

### FR14: Question Bank Management (System)

**FR14.1:** System stores 500 gold standard vendor questions with metadata
**FR14.2:** System stores 500-1,000 LLM-generated question variations
**FR14.3:** All questions include: KA, difficulty level, concept tags, correct answer, explanations
**FR14.4:** System generates embeddings for all questions (semantic search capability)
**FR14.5:** System tracks question performance metrics (average correctness, user feedback)
**FR14.6:** System flags questions with poor metrics (< 50% or > 90% correctness, negative feedback)
**FR14.7:** System supports content updates (admin capability to add/edit/remove questions)

### FR15: Reading Content Management (System)

**FR15.1:** System stores BABOK v3 content parsed into chunks (200-500 tokens each)
**FR15.2:** All chunks include: KA, section reference, difficulty level, concept tags
**FR15.3:** System generates embeddings for all chunks (semantic similarity search)
**FR15.4:** System retrieves chunks via vector similarity based on question concepts and user gaps
**FR15.5:** System filters chunks by KA (only show relevant KA content)
**FR15.6:** System ranks chunks by relevance score (similarity + difficulty match)
**FR15.7:** System supports content updates (admin capability to re-chunk or update BABOK content)

### FR16: Data Persistence & Synchronization

**FR16.1:** System persists all user data in PostgreSQL database
**FR16.2:** System persists all question and reading embeddings in Qdrant vector database
**FR16.3:** System saves quiz progress in real-time (no data loss on browser close)
**FR16.4:** System synchronizes competency scores after every response
**FR16.5:** System maintains data consistency across user sessions
**FR16.6:** System handles concurrent sessions gracefully (same user, multiple devices)

### FR17: Error Handling & Recovery

**FR17.1:** System displays user-friendly error messages for failures
**FR17.2:** System logs errors for debugging without exposing technical details to user
**FR17.3:** System recovers from network errors gracefully (retry logic)
**FR17.4:** System prevents data loss during errors (save before operations)
**FR17.5:** System provides "Contact Support" option when errors occur
**FR17.6:** System shows loading indicators during operations (user feedback)

### FR18: Admin Operations and Support Tools

**FR18.1:** Admin users have elevated role flag (`is_admin: boolean`) stored in users table
**FR18.2:** Admin-only endpoints protected by `@require_admin` middleware (extends `@require_auth`)
**FR18.3:** Admin can search users by email, user_id, or name via GET `/api/admin/users/search?q={query}`
**FR18.4:** Search returns: user_id, email, created_at, onboarding_status, exam_date, last_login
**FR18.5:** Admin can impersonate any user via POST `/api/admin/impersonate/{user_id}`
**FR18.6:** Impersonation generates time-limited JWT (30 minutes) with `impersonated_by: admin_user_id` claim
**FR18.7:** Impersonated session shows banner: "Viewing as {user_email} | Exit Impersonation" (always visible)
**FR18.8:** Admin can exit impersonation anytime (returns to admin session)
**FR18.9:** All impersonation events logged to audit trail (admin_id, user_id, timestamp, duration)
**FR18.10:** User detail pages include PostHog deep link: "View in PostHog" → Opens PostHog profile for that user_id
**FR18.11:** PostHog integration configured with user_id as primary identifier (for linking)
**FR18.12:** Admin access restricted to designated admin users (cannot self-promote to admin)

---
