# Epic 3: Diagnostic Assessment & Competency Baseline

**Epic Goal:** Enable first-time users to complete the anonymous 7-question onboarding flow (starting with first question inline on landing page), create an account, take the 12-question diagnostic assessment, and receive accurate baseline competency scores across all 6 CBAP knowledge areas with gap analysis and recommendations.

## Story 3.1: Landing Page with Inline First Onboarding Question

As a **first-time visitor**,
I want to see the value proposition and immediately engage with the first onboarding question on the landing page,
so that I can start my learning journey with minimal friction.

**Acceptance Criteria:**
1. Landing page displays LearnR value proposition (headline, subheadline, key benefits - trust, adaptive learning, reading content, spaced repetition)
2. First onboarding question displayed **inline immediately below value prop** (no "Sign Up" button friction): "How did you hear about LearnR?" with options (Search, Referral, Social Media, Other)
3. User selects answer → automatically progresses to Question 2 in same container (no separate "Submit" button, no page reload - smooth fade-in/slide transition 300ms)
4. Question 1 answer stored in browser sessionStorage (no server call yet, user not authenticated)
5. Visual design: Framer-inspired aesthetic, Inter font, pill-rounded answer buttons (border-radius: 9999px), primary information card styling (22px border radius)
6. Progress indicator: "Question 1 of 7" displayed
7. Page is mobile-responsive (works on 375px width minimum)
8. Loading state: Page renders in <3 seconds on 3G connection
9. Accessibility: Keyboard navigation works (tab to options, enter to select), screen reader announces question and options
10. Unit tests: Question renders, selection progresses to next question, sessionStorage updated

## Story 3.2: Onboarding Questions 2-7 (Progressive Disclosure)

As a **user progressing through onboarding**,
I want to answer questions 2-7 sequentially in the same container,
so that the platform learns my context and can personalize my learning experience.

**Acceptance Criteria:**
1. **Questions 2-7 appear sequentially in same container as Q1** (progressive disclosure, not separate pages)
   - Smooth fade-in/slide animation (300ms) between questions
   - No page reload, all client-side transitions
   - Previous answers stored in sessionStorage immediately
2. Question 2: "Which certification are you preparing for?" → Options: CBAP (default for MVP), [Other certifications grayed out/disabled]
3. Question 3: "What's your primary motivation?" → Options: Career advancement, Salary increase, Credibility, Personal growth, Other
4. Question 4: "When is your exam scheduled?" → Date picker (minimum: today + 30 days, maximum: today + 365 days), displays "X days until exam" after selection
5. Question 5: "What's your current knowledge level?" → Options: Beginner (new to BA), Intermediate (some experience), Advanced (experienced BA, need exam prep)
6. Question 6: "What's your target competency score?" → Options: 70% (pass threshold), 80% (confident pass), 90% (mastery)
7. Question 7: "How much time can you commit daily?" → Options: 30-60 minutes, 1-2 hours, 2+ hours
8. Each answer stored in sessionStorage immediately upon selection
9. **SessionStorage schema:** See `/docs/front-end-spec.md` Lines 391-407 for exact data structure:
   ```javascript
   {
     "onboarding_answers": {
       "referral_source": "search",
       "exam_type": "CBAP",
       "motivation": "career_advancement",
       "exam_date": "2025-12-21",
       "knowledge_level": "intermediate",
       "target_score": "pass",
       "daily_commitment": "1hr"
     },
     "started_at": "ISO8601 timestamp",
     "current_question": 7
   }
   ```
10. Progress indicator updates: "Question 2 of 7", "Question 3 of 7", etc. (thin progress bar at top of screen)
11. Optional "← Back" button allows returning to previous question (except from Q1 to landing page)
12. After Question 7 answered → automatically transition to Account Creation screen (same container, slide transition)

## Story 3.3: Account Creation After Onboarding

As a **user who completed 7 onboarding questions**,
I want to create an account to save my progress,
so that I can proceed to the diagnostic assessment and access my personalized learning.

**Acceptance Criteria:**
1. Account creation screen displays message: "Create your account to save your progress and start your diagnostic assessment"
2. Form fields: Email (required, validated), Password (required, 8+ chars, letter + number), Confirm Password (must match)
3. Visual summary of onboarding data displayed above form (exam date: "X days until exam", target: Y%, daily time: Z hours) - builds trust that data is captured
4. "Create Account" button (pill-rounded, primary color)
5. On submit: POST to `/api/auth/register` with email + password
6. On successful registration: Receive JWT token, store in localStorage or HttpOnly cookie
7. Immediately POST onboarding data to `/api/user/onboarding` (7 answers persisted to user profile)
8. Clear sessionStorage after successful account creation (data now in database)
9. Redirect to Diagnostic Assessment screen
10. Error handling: Display validation errors inline (email already exists → "Email already registered, please login"), weak password → "Password must be at least 8 characters with letter and number"
11. "Already have an account? Login" link navigates to login page (edge case: returning user who started onboarding)

## Story 3.4: Diagnostic Assessment Question Selection

As a **backend developer**,
I want to select 12 balanced diagnostic questions (3 per KA) with varied difficulty,
so that the diagnostic provides accurate baseline competency assessment.

**Acceptance Criteria:**
1. GET `/api/diagnostic/questions` endpoint (requires authentication)
2. Select exactly 12 questions: 3 from each of 6 KAs
3. Difficulty distribution per KA: 1 Easy, 1 Medium, 1 Hard (balanced assessment)
4. Questions selected randomly from available pool (different diagnostic each time, prevents memorization if retaken)
5. Question order randomized (not clustered by KA - intermix to reduce pattern recognition)
6. Response: JSON array of 12 question objects (id, question_text, options [A, B, C, D], ka, difficulty) - NO correct_answer or explanation yet
7. Mark diagnostic session as "in_progress" in database (track user's diagnostic state)
8. Unit tests: 12 questions returned, 3 per KA, varied difficulty, randomized order
9. Integration test: API returns valid diagnostic questions for authenticated user
10. Performance: Question selection in <500ms

## Story 3.5: Diagnostic Assessment UI and Answer Recording

As a **user taking the diagnostic**,
I want to answer 12 questions in a focused, distraction-free interface,
so that I can provide accurate responses reflecting my true knowledge level.

**Acceptance Criteria:**
1. Diagnostic screen displays one question at a time (full-screen or centered, minimal chrome)
2. Question display: Question text, 4 options (A/B/C/D as pill-rounded buttons), progress "Question X of 12"
3. User selects one option → "Submit Answer" button enabled (or auto-advance on selection, UX decision TBD)
4. On submit: POST `/api/diagnostic/answer` with `question_id` and `selected_answer`
5. No immediate feedback (correct/incorrect not shown during diagnostic - per requirements)
6. Auto-advance to next question after answer recorded
7. Answers stored in `diagnostic_responses` table (user_id, question_id, selected_answer, timestamp)
8. After 12th question submitted → automatically calculate competency scores (Story 3.6)
9. Visual design: Focused mode, Inter font, pill buttons, secondary card styling for question container (14px radius)
10. No "Back" button during diagnostic (prevents changing answers after seeing later questions)
11. Session timeout warning at 30 minutes (if user pauses mid-diagnostic)

## Story 3.6: Baseline Competency Calculation (Simplified IRT)

As a **system**,
I want to calculate baseline competency scores for each KA using simplified Item Response Theory,
so that users receive accurate assessment of their current knowledge level.

**Acceptance Criteria:**
1. After 12th diagnostic answer submitted, trigger competency calculation
2. For each KA, calculate competency score based on 3 questions answered:
   - Simplified IRT: Correct answer on Hard question → higher competency increase than Easy
   - Scoring formula (simplified): Base score 50%, +15% per correct Easy, +20% per correct Medium, +25% per correct Hard
   - Example: 1 correct Easy + 1 correct Medium + 0 correct Hard = 50% + 15% + 20% = 85% competency
3. Store competency scores in `competency_tracking` table (user_id, ka, competency_score, last_updated)
4. Calculate overall exam readiness score (average of 6 KA scores or weighted by CBAP exam distribution if data available)
5. Identify gap areas: KAs with competency < 70% flagged as "needs focus"
6. Unit tests: Various answer combinations produce expected competency scores, all 6 KAs have scores calculated
7. Integration test: Full diagnostic flow calculates and stores competency scores
8. Performance: Calculation executes in <1 second
9. Algorithm documented in `/docs/algorithms.md` for future refinement
10. Initial calibration: Expert review validates that competency scores feel accurate (e.g., 3/3 correct Hard questions → ~95-100% competency)

## Story 3.7: Diagnostic Results Screen with Gap Analysis

As a **user who completed the diagnostic**,
I want to see my baseline competency scores and understand which areas need focus,
so that I can start studying effectively with clear direction.

**Acceptance Criteria:**
1. Results screen displays after diagnostic completion (GET `/api/diagnostic/results`)
2. Hero metric: Exam Readiness Score (0-100%, large display, color-coded: Red <70%, Orange 70-85%, Green >85%)
3. Six KA competency bars visualized (horizontal bars or radial chart, showing score 0-100% for each KA)
4. Each KA bar color-coded: Red (<70%), Orange (70-85%), Green (>85%)
5. Gap analysis section: "Focus Areas" listing KAs with <70% competency, sorted by lowest score first
6. Recommendations: "Start with [Lowest KA Name] where you scored X%"
7. Days until exam displayed: "X days to prepare"
8. Primary CTA: "Start Learning" button (pill-rounded, primary color) → navigates to first adaptive quiz session
9. Secondary CTA: "Retake Diagnostic" (if user wants to reset baseline - confirmation modal warns this will reset all competency tracking)
10. Visual design: Main screen container (35px radius), competency cards (22px radius), Framer-inspired layout, Inter font
11. Accessibility: Screen reader announces competency scores, color-coding supplemented with text labels (not color-only)
12. Post-diagnostic survey: "How accurately did this assessment reflect your knowledge?" (5-point scale: Very Inaccurate to Very Accurate) → target 80%+ "Accurate" or "Very Accurate"
