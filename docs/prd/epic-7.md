# Epic 7: Spaced Repetition & Long-Term Retention

**Epic Goal:** Implement the SM-2 spaced repetition algorithm to schedule concept reviews at optimal intervals (1, 3, 7, 14 days), ensuring users retain learned concepts through exam day. This epic delivers concept mastery tracking, review scheduling, mixed quiz sessions (reviews + new content), and reviews-due indicators on the dashboard.

## Story 7.1: Concept Mastery Tracking for Spaced Repetition

As a **system**,
I want to track concept-level mastery state for each user,
so that spaced repetition can schedule reviews based on forgetting curve.

**Acceptance Criteria:**
1. Define concept mapping: Each question tagged with 1-3 `concept_tags` (e.g., ["stakeholder analysis", "RACI matrix"])
2. Create `concept_mastery` table: user_id, concept_tag, ka, ease_factor (default 2.5), interval_days (1/3/7/14), repetition_count, last_reviewed, next_review_due
3. After user answers question correctly for **first time**:
   - Create `concept_mastery` record for each concept_tag in that question
   - Set `interval_days = 1` (review in 1 day), `next_review_due = today + 1 day`
4. After user answers question incorrectly:
   - If concept_mastery exists: Reset `interval_days = 1`, `repetition_count = 0` (start over)
   - If concept_mastery doesn't exist: Do not create (only correct answers establish mastery)
5. SM-2 algorithm parameters: ease_factor adjusts based on performance (2.5 default, range 1.3-2.5)
6. Unit tests: Concept mastery created on first correct answer, reset on incorrect, not created on first incorrect
7. Integration test: Answering questions populates concept_mastery table correctly
8. Performance: Mastery tracking adds <50ms to answer submission (Story 4.3)
9. Concept tags reviewed: Ensure all questions have meaningful concept_tags (not generic "CBAP")
10. Algorithm documented in `/docs/algorithms.md` (SM-2 adaptation for 60-day timeline)

## Story 7.2: SM-2 Review Scheduling

As a **system**,
I want to schedule concept reviews at increasing intervals based on SM-2 algorithm,
so that users review concepts just before they're likely to forget them.

**Acceptance Criteria:**
1. When user answers **review question correctly**:
   - Calculate new interval: `new_interval = previous_interval * ease_factor`
   - Progression: 1 day → 3 days → 7 days → 14 days (approximately, SM-2 formula may vary slightly)
   - Update `concept_mastery`: `interval_days = new_interval`, `next_review_due = today + new_interval`, increment `repetition_count`
2. When user answers **review question incorrectly**:
   - Reset to start: `interval_days = 1`, `next_review_due = today + 1`, `repetition_count = 0`
   - Optionally decrease `ease_factor` (make future intervals shorter if concept is difficult)
3. Ease factor adjustment (SM-2 quality rating simplified for MVP):
   - Correct answer: ease_factor stays same or increases slightly (+0.1, max 2.5)
   - Incorrect answer: ease_factor decreases (-0.2, min 1.3)
4. Maximum interval capped at 14 days (per Brief requirements for 60-day exam timeline)
5. Reviews due identification: Query `concept_mastery` where `next_review_due <= today`
6. Overdue prioritization: Reviews past due date prioritized over newly due reviews
7. Unit tests: Correct answer increases interval, incorrect resets interval, intervals follow ~1/3/7/14 progression
8. Integration test: Multiple review cycles produce expected interval progression
9. Performance: Review scheduling calculation <100ms (part of answer submission)
10. Monitor review accuracy: Target 70%+ correct on reviews (per Brief) - if lower, intervals may be too aggressive

## Story 7.3: Mixed Quiz Sessions (Reviews + New Content)

As a **user with reviews due**,
I want quiz sessions to automatically mix review questions with new content,
so that I reinforce retention while continuing to learn new material.

**Acceptance Criteria:**
1. When user starts quiz session (Story 4.1), check if reviews are due:
   - Query `concept_mastery` where `next_review_due <= today` → count of concepts needing review
   - If reviews due: Create **mixed session** (40% reviews + 60% new content per Brief requirements)
   - If no reviews due: Create **new content session** (100% new questions)
2. Mixed session composition example: If user plans to answer 10 questions → 4 reviews + 6 new
3. Review question selection:
   - Select questions tagged with concepts due for review (from `concept_mastery.concept_tag`)
   - Prioritize overdue reviews (past `next_review_due` by most days)
   - If multiple questions match same concept, select one randomly
4. New question selection: Use adaptive logic from Story 4.2 (weakest KAs, difficulty matching)
5. Question order: Intermix reviews and new questions (not clustered - e.g., R, N, N, R, N, R, N, N, R, N)
6. Review questions labeled: "Review" badge or icon displayed on question card (visual distinction from new content)
7. Session type stored in `quiz_sessions` table: `session_type` = "mixed" or "new_content"
8. Unit tests: Mixed session has correct ratio (40/60), review questions selected from due concepts
9. Integration test: User with reviews due receives mixed session, user without reviews receives new content session
10. Performance: Mixed session creation in <500ms (review lookup + adaptive selection)

## Story 7.4: Review Performance Tracking and Accuracy Metrics

As a **user completing review questions**,
I want my review accuracy tracked so I can see if I'm retaining concepts long-term,
so that I have confidence my retention is improving.

**Acceptance Criteria:**
1. After user answers **review question** (identified by "Review" label in session):
   - Update `concept_mastery` per SM-2 logic (Story 7.2)
   - Record in `quiz_responses` with `is_review = true` flag
2. Calculate review accuracy metrics:
   - **Overall Review Accuracy:** % of all review questions answered correctly (target 70%+ per Brief)
   - **Accuracy by Interval:** % correct on 1-day reviews, 3-day reviews, 7-day reviews, 14-day reviews
   - **Accuracy by KA:** % correct reviews per KA
3. GET `/api/progress/reviews` endpoint returns review metrics:
   - `overall_review_accuracy`, `accuracy_by_interval`, `accuracy_by_ka`
   - `reviews_completed_count`, `reviews_due_count`
4. Dashboard (Epic 6) displays review accuracy in a card (22px radius):
   - "Review Accuracy: X%" (color-coded: Green >70%, Orange 60-70%, Red <60%)
   - Breakdown by interval if user wants to drill down
5. If review accuracy <60%: Recommendation to slow down learning (more time per concept before advancing)
6. Unit tests: Review accuracy calculated correctly, breakdown by interval accurate
7. Integration test: Completing review questions updates accuracy metrics
8. Performance: Metrics calculation <200ms (part of dashboard load)
9. Alpha/Beta test validation: Monitor if users maintain >70% review accuracy (validates SM-2 intervals)
10. Adjustment mechanism (Phase 2): If accuracy consistently low, suggest adjusting intervals or adding extra review cycles

## Story 7.5: Reviews Due Indicator on Dashboard

As a **user**,
I want to see how many review concepts are due on my dashboard,
so that I'm reminded to complete reviews and maintain retention.

**Acceptance Criteria:**
1. Dashboard (Story 6.1) displays "Reviews Due" count:
   - Query `concept_mastery` where `next_review_due <= today` → count
   - Display as badge or prominent metric (e.g., "5 Reviews Due")
2. Visual treatment:
   - If reviews due: Orange/yellow color (attention, not alarming), icon (refresh/repeat symbol)
   - If no reviews due: Green checkmark, "No reviews due - great job!"
3. Clicking "Reviews Due" badge → starts mixed quiz session (Story 7.3) prioritizing reviews
4. Primary CTA on dashboard adapts (Story 6.5):
   - If reviews due: "Start Reviews (X concepts)" becomes primary action
   - If no reviews: "Continue Learning" is primary
5. Reviews due count updates in real-time after completing mixed session
6. If reviews overdue (past due by >2 days): Escalate visual treatment (red color, "X overdue reviews")
7. Unit tests: Reviews due count accurate, dashboard CTA adapts correctly
8. Integration test: Completing reviews reduces reviews due count on dashboard
9. Visual design: Reviews due indicator styled as secondary card (14px radius) or inline badge
10. Email reminders (Phase 2, not MVP): Daily email if reviews due >3 and user hasn't logged in
