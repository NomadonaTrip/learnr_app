# Epic 4: Adaptive Quiz Engine & Explanations

**Epic Goal:** Implement the core adaptive learning loop where users answer questions selected intelligently based on their competency gaps and difficulty matching, receive immediate feedback, and read detailed explanations for every question. This epic delivers quiz session management, real-time competency updates, and user feedback mechanisms.

**User Flow Reference:** See `docs/user-flows.md` Flow #4 (Learning Loop) and Flow #4b (Post-Session Review Flow) for visual representation of the complete learning experience including the post-session review phase introduced in v2.1.

## Story 4.1: Quiz Session Creation and Management

As a **user ready to study**,
I want to start an adaptive quiz session,
so that I can practice questions matched to my competency level and knowledge gaps.

**Acceptance Criteria:**
1. POST `/api/quiz/session/start` endpoint creates new quiz session (requires authentication)
2. Session metadata stored: session_id, user_id, start_time, session_type ("new_content" for now, "mixed" added in Epic 7)
3. Session state tracked: questions_answered_count, current_question_id, is_paused, is_completed
4. Response: session_id and first adaptive question selected (Story 4.2 logic)
5. User can have only one active session at a time (if existing session incomplete → return existing session_id)
6. GET `/api/quiz/session/{session_id}` retrieves session state (questions answered so far, current question)
7. POST `/api/quiz/session/{session_id}/pause` pauses session (save state, can resume later)
8. POST `/api/quiz/session/{session_id}/end` ends session (mark completed, save end_time, calculate session stats)
9. Sessions auto-expire after 2 hours of inactivity (background cleanup job)
10. Unit tests: Session creation, pause, resume, end, retrieve state

## Story 4.2: Adaptive Question Selection Logic

As a **quiz engine**,
I want to select the next question adaptively based on user's competency, knowledge gaps, and difficulty matching,
so that every question maximizes learning efficiency.

**Acceptance Criteria:**
1. Algorithm (`/app/services/adaptive_selection.py`):
   - **Step 1:** Identify weakest 2-3 KAs (lowest competency scores)
   - **Step 2:** Prioritize questions from weakest KAs (60% probability) vs. all KAs for breadth (40% probability)
   - **Step 3:** Match difficulty to user's current competency in that KA: <70% → Easy/Medium, 70-85% → Medium/Hard, >85% → Hard
   - **Step 4:** Filter out recently seen questions (exclude questions answered in last 7 days)
   - **Step 5:** Randomly select one question from filtered pool
2. Within-session difficulty adjustment (per Epic template requirements):
   - Track consecutive correct/incorrect answers in same KA within current session
   - If 3+ consecutive correct in KA → increase difficulty for next question in that KA (e.g., Medium → Hard)
   - If 3+ consecutive incorrect in KA → decrease difficulty for next question in that KA (e.g., Hard → Medium)
   - Adjustment resets between sessions (competency tracking persists, but within-session streaks don't)
3. Question returned includes: question_id, question_text, options, ka, difficulty (NO correct_answer or explanation yet)
4. Log selection rationale (for debugging): KA chosen, difficulty rationale, streak adjustment applied (if any)
5. Unit tests: Weakest KA prioritized, difficulty matched to competency, recently seen questions excluded, consecutive performance adjusts difficulty
6. Integration test: Adaptive selection returns appropriate questions across multiple quiz sessions
7. Performance: Selection logic executes in <200ms
8. Algorithm refinement: Monitor user feedback ("too easy" / "too hard") for future calibration

## Story 4.3: Answer Submission and Immediate Feedback

As a **user answering a quiz question**,
I want to submit my answer and immediately see if I was correct or incorrect,
so that I receive instant feedback on my understanding.

**Acceptance Criteria:**
1. POST `/api/quiz/answer` endpoint accepts: session_id, question_id, selected_answer (A/B/C/D)
2. Record response in `quiz_responses` table (user_id, session_id, question_id, selected_answer, is_correct, time_taken, timestamp)
3. Determine correctness: Compare `selected_answer` to question's `correct_answer`
4. Response JSON:
   - `is_correct`: true/false
   - `correct_answer`: The right answer (e.g., "B")
   - `explanation`: Detailed explanation text
   - `competency_update`: New competency score for this KA (see Story 4.4)
5. Frontend displays immediate visual feedback:
   - Correct answer: Green checkmark icon, "Correct!" message
   - Incorrect answer: Orange/red X icon, "Incorrect. The correct answer is B."
6. No auto-advance yet (user must click "Next" after reading explanation - Story 4.5)
7. Track time_taken (client-side or server-side timestamp diff from question displayed to answer submitted)
8. Unit tests: Correct answer recorded, incorrect answer recorded, response includes explanation
9. Integration test: Full answer submission flow updates database and returns feedback
10. Error handling: Invalid session_id or question_id → 400 Bad Request

## Story 4.4: Real-Time Competency Score Updates

As a **system**,
I want to update the user's competency score for the relevant KA after every quiz answer,
so that competency tracking reflects current knowledge level in real-time.

**Acceptance Criteria:**
1. After answer submission (Story 4.3), trigger competency update for the question's KA
2. Simplified IRT update logic:
   - Correct answer on Hard question: +5% competency (or more sophisticated IRT calculation)
   - Correct answer on Medium: +3% competency
   - Correct answer on Easy: +2% competency
   - Incorrect answer: -1% competency (small penalty to reflect gap)
   - Competency score capped at 0-100%
3. Update `competency_tracking` table: Set new `competency_score`, update `last_updated` timestamp
4. Include updated competency score in answer submission response (Story 4.3)
5. Exam readiness score recalculated as average (or weighted average) of all 6 KA scores
6. Unit tests: Various answer/difficulty combinations produce expected competency changes, score stays within 0-100%
7. Integration test: Multiple answers update competency progressively
8. Performance: Competency update executes in <100ms (included in answer submission response time)
9. Algorithm documented in `/docs/algorithms.md` for future refinement (full IRT in Phase 2)
10. Historical competency tracking: Store snapshots weekly for progress trends (see Epic 6)

## Story 4.5: Explanation Display with User Feedback

As a **user who answered a question**,
I want to read a detailed explanation of why the correct answer is right and why other options are wrong,
so that I learn the concept rather than just memorizing answers.

**Acceptance Criteria:**
1. After answer submission and immediate feedback (Story 4.3), display explanation section below result
2. Explanation text retrieved from question's `explanation` field (loaded during question import, Story 2.2)
3. Explanation formatting:
   - **Maximum 200 characters total** (enforced during content creation) - concise, focused explanations
   - **"Why [Correct Answer] is correct:"** section explaining the right answer (2-3 sentences maximum)
   - **"Why other options are incorrect:"** brief explanation for each wrong option
   - **BABOK reference:** "See BABOK v3 Section X.Y.Z for more details" (included within 200-char limit if applicable)
   - **Rationale:** 200-char limit ensures explanations fit on screen without scrolling, reducing cognitive load
4. Explanation card styled with secondary card border radius (14px), readable typography (Inter font, adequate line spacing)
5. User feedback mechanism: Thumbs up / thumbs down icons below explanation
   - Click thumbs up → POST `/api/feedback/explanation` with `question_id`, `helpful: true`
   - Click thumbs down → POST `/api/feedback/explanation` with `question_id`, `helpful: false`
   - Feedback stored in `explanation_feedback` table (user_id, question_id, helpful, timestamp)
   - Visual feedback: Icon highlights after click, "Thanks for your feedback!" message
6. "Report Issue" link allows flagging incorrect questions (POST `/api/feedback/report` with `question_id`, `issue_description`)
7. "Next Question" button (pill-rounded, primary color) below explanation → advances to next adaptive question (Story 4.2 selects next)
8. Accessibility: Explanation text is screen-reader friendly, thumbs icons have alt text
9. Unit tests: Explanation renders, feedback submission works
10. Integration test: User can read explanation and provide feedback after answering question

## Story 4.6: Post-Session Review Initiation (v2.1 NEW)

As a **user who completed a quiz session with incorrect answers**,
I want to immediately review all questions I got wrong,
so that I can reinforce correct understanding and improve retention.

**Acceptance Criteria:**
1. When quiz session ends (user clicks "End Session"), backend checks for incorrect answers in this session
2. If incorrect answers exist → redirect to Post-Session Review Transition Screen instead of dashboard
3. If all answers correct (perfect score) → show congratulatory message, skip review, return to dashboard
4. Transition screen displays:
   - Header: "Great work! Let's review X questions you got wrong"
   - Subtext: "Immediate review improves retention 2-3x"
   - Primary CTA: "Start Review" (pill-rounded button)
   - Secondary CTA: "Skip Review" (text link, less prominent)
5. POST `/api/v1/sessions/{session_id}/review/start` creates `session_reviews` record with status `not_started`
6. Response includes review_id, total_questions_to_review, and array of incorrect question IDs
7. If user clicks "Skip Review" → show confirmation modal: "Are you sure? Reviewing now will strengthen retention"
8. If user confirms skip → POST `/api/v1/sessions/{session_id}/review/skip`, update review status to `skipped`, return to dashboard
9. Track review skip rate for analytics (target: <30% skip rate)
10. Unit tests: Review initiation triggered only when incorrect answers exist
11. Integration test: User completing session with incorrect answers sees review transition screen

## Story 4.7: Re-Present Incorrect Questions for Review

As a **user in review mode**,
I want to re-answer each question I got wrong,
so that I can test my understanding and reinforce the correct answer.

**Acceptance Criteria:**
1. Review screen displays first incorrect question with "REVIEW" badge (distinct visual indicator)
2. Progress indicator: "Review Question 1 of X" (shows current position in review)
3. Question display identical to quiz session (same format, same 4 options)
4. User cannot see their original incorrect answer (clean slate for re-attempt)
5. User selects answer and clicks "Submit Answer"
6. POST `/api/v1/sessions/{session_id}/review/answer` with:
   - `original_attempt_id` (FK to original incorrect attempt)
   - `selected_choice_id` (user's new answer)
   - `time_spent_seconds`
7. Backend creates `review_attempts` record linking to `session_reviews` and `question_attempts`
8. Backend calculates `is_correct` (boolean) and `is_reinforced` (true if incorrect → correct)
9. Response returns: `is_correct`, `is_reinforced`, `correct_answer`, `explanation`
10. Frontend displays immediate feedback:
    - If reinforced (incorrect → correct): Green checkmark + "Great improvement! 🎉"
    - If still incorrect: Orange X + "Still incorrect. Correct answer is: B"
11. Update competency score based on review performance (reinforced = +2% boost, still incorrect = neutral)
12. Automatically advance to next review question or review summary if complete
13. Unit tests: Review attempt recorded correctly, reinforcement logic works
14. Integration test: User can re-answer all incorrect questions and see appropriate feedback

## Story 4.8: Review Performance Tracking and Summary

As a **user who completed post-session review**,
I want to see a summary of my review performance,
so that I can understand my improvement and identify concepts needing more practice.

**Acceptance Criteria:**
1. After last review question answered → display Review Summary Screen
2. Summary displays:
   - Total questions reviewed: X
   - Reinforced correctly (incorrect → correct): Y (green)
   - Still incorrect: Z (orange)
   - Improvement calculation: "Original: 80% → Final: 93% (+13%)"
3. "Original" score = session accuracy BEFORE review (e.g., 12/15 = 80%)
4. "Final" score = session accuracy AFTER review (e.g., 14/15 = 93%, assuming 2 reinforced)
5. Display list of still-incorrect questions with:
   - Question preview (first 50 chars)
   - Knowledge Area tag
   - "These will appear in spaced repetition reviews"
6. POST `/api/v1/sessions/{session_id}/review/complete` updates `session_reviews`:
   - `review_status` = `completed`
   - `questions_reinforced_correctly` = count
   - `questions_still_incorrect` = count
   - `review_completed_at` = timestamp
7. Primary CTA: "Return to Dashboard" → updates dashboard with new competency scores
8. Track review completion rate (target: 70%+ of users complete review when prompted)
9. Track reinforcement success rate (target: 60%+ of review attempts are reinforced)
10. Unit tests: Summary calculations accurate, metrics tracked correctly
11. Integration test: Completed review updates session_reviews table and returns user to dashboard

## Story 4.9: Review Analytics and Dashboard Integration

As a **system**,
I want to track post-session review engagement and performance metrics,
so that we can validate the 2-3x retention improvement hypothesis and measure feature adoption.

**Acceptance Criteria:**
1. Dashboard displays review completion metrics:
   - Total reviews completed
   - Average reinforcement success rate (% of incorrect → correct)
   - Review adoption rate (% of sessions with reviews that user completed)
2. Analytics track per-user:
   - `total_reviews_offered` (sessions with incorrect answers)
   - `total_reviews_completed`
   - `total_reviews_skipped`
   - `total_questions_reinforced`
3. GET `/api/dashboard` response includes:
   - `review_stats.adoption_rate` (float, 0.0-1.0)
   - `review_stats.reinforcement_success_rate` (float, 0.0-1.0)
   - `review_stats.total_reinforced` (int)
4. Admin endpoint GET `/api/admin/alpha-metrics` includes:
   - Platform-wide review adoption rate
   - Platform-wide reinforcement success rate
   - User cohort comparison (reviewers vs. non-reviewers retention rates)
5. Spaced repetition algorithm prioritizes still-incorrect questions from reviews (schedule for +1 day review)
6. Correctly reinforced questions get standard spaced repetition interval (+3 days)
7. Track reading time during review phase (if user expands explanations or reading materials)
8. **Analytics Event Logging:** All review interactions must emit standardized events for tracking:
   - **Event: `post_session_review_started`** - Emitted when user begins review
     - Fields: `session_id`, `user_id`, `total_questions_to_review`, `original_session_accuracy`, `timestamp`
   - **Event: `review_question_answered`** - Emitted after each review answer submitted
     - Fields: `review_id`, `question_id`, `original_answer`, `review_answer`, `is_reinforced`, `time_spent_seconds`, `timestamp`
   - **Event: `review_reading_expanded`** - Emitted when user expands reading material during review
     - Fields: `review_id`, `chunk_id`, `question_id`, `babok_section`, `time_spent_seconds`, `timestamp`
   - **Event: `post_session_review_completed`** - Emitted when review phase finishes
     - Fields: `review_id`, `session_id`, `total_reviewed`, `reinforced_correctly`, `still_incorrect`, `reading_chunks_viewed`, `total_reading_time_seconds`, `final_accuracy`, `accuracy_improvement`, `timestamp`
   - **Event: `post_session_review_skipped`** - Emitted when user skips review
     - Fields: `session_id`, `questions_to_review`, `original_accuracy`, `timestamp`
9. Unit tests: Analytics calculations accurate, all events logged correctly with proper schemas
10. Integration test: Review completion updates user analytics and dashboard metrics, events are emitted
11. Performance: Dashboard analytics queries optimized with database indexes on `session_reviews(user_id, review_status)`
