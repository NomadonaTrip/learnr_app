# Epic 5: Targeted Reading Content Integration

**🚨 CRITICAL IMPLEMENTATION NOTE - v2.1 Update:**

**Stories 5.1-5.4 are DEPRECATED.** They describe the v2.0 synchronous reading model (inline reading after explanations) which was found to interrupt learning flow and reduce engagement. These stories are preserved **for historical reference only**.

**Stories 5.5-5.9 are the AUTHORITATIVE implementation.** LearnR v2.1 implements the **Asynchronous Reading Library** model which provides superior UX through:
- Zero interruption to learning flow ("test fast, read later")
- User control over when to engage with reading materials
- Prioritized reading queue with smart filtering
- 2x improvement in reading engagement (25% → 50%+ expected)

**For software architects:** Implement Stories 5.5-5.9 (Async Reading Library). Do NOT implement Stories 5.1-5.4 unless explicitly directed for a specific integration scenario.

**Detailed Specifications:** See `/docs/Asynchronous_Reading_Model.md` for complete technical architecture of the v2.1 async reading system.

**User Flow Reference:** See `docs/user-flows.md` Flow #9 (Reading Library Flow) for visual representation of the asynchronous reading queue system introduced in v2.1. This flow shows how users access curated reading materials on-demand without interrupting their quiz experience.

**Epic Goal:** Complete the learning loop by adding semantic retrieval of BABOK v3 reading content that addresses user-specific knowledge gaps. This is the **critical differentiator** for LearnR - transforming it from "just another quiz app" to a complete learning system. This epic delivers vector search, reading content display after explanations, and engagement tracking to validate the differentiation value during Day 24 alpha test.

## Story 5.1: Gap-Based Reading Content Retrieval

As a **system**,
I want to automatically retrieve relevant BABOK reading chunks after a user answers a question incorrectly,
so that users can read targeted content addressing their specific knowledge gaps.

**Acceptance Criteria:**
1. After answer submission (Story 4.3), if answer is **incorrect** → trigger reading content retrieval
2. Generate query for semantic search:
   - Primary: Question's `concept_tags` (e.g., ["stakeholder analysis", "requirements elicitation"])
   - Secondary: Question text itself (if concept_tags not comprehensive)
3. Call `/api/content/reading` (Story 2.7) with query_text and KA filter (same KA as question)
4. Retrieve top 2-3 BABOK chunks ranked by semantic similarity
5. Filter chunks by difficulty: Match to user's competency level in this KA (e.g., if user at 60% competency, retrieve Easy/Medium chunks, not Hard)
6. Return chunks in response to answer submission (Story 4.3 response expanded to include `reading_content` array)
7. If answer is **correct** on Easy/Medium question → no reading content (user already knows this, don't overwhelm)
8. If answer is **correct** on Hard question → optionally show 1 chunk for reinforcement (configurable)
9. Unit tests: Incorrect answer triggers retrieval, correct Easy answer does not, KA filtering works
10. Integration test: Semantic search returns BABOK content relevant to missed question concept

## Story 5.2: Reading Content Display in Quiz Flow

As a **user who answered incorrectly**,
I want to read relevant BABOK content immediately after seeing the explanation,
so that I can understand the concept more deeply and fill my knowledge gap.

**Acceptance Criteria:**
1. Reading content section displays after explanation (Story 4.5), before "Next Question" button
2. Section header: "Learn More: Targeted Reading from BABOK v3" (clarifies source and purpose)
3. Display 2-3 reading chunks as expandable cards (14px border radius, secondary styling)
4. Each chunk card shows:
   - **BABOK Section Reference:** "Section 3.2.1: Stakeholder Analysis"
   - **Preview:** First 100 characters of `text_content` + "... Read more"
   - **Expand/Collapse:** Click to show full text_content (200-500 tokens)
5. Expanded state: Full text displayed with readable formatting (line spacing, paragraph breaks preserved)
6. "Mark as Read" checkbox for each chunk (tracks engagement)
7. If user clicks "Mark as Read" → POST `/api/reading/track` with `chunk_id`, stores in `reading_history` table (user_id, chunk_id, marked_read: true, timestamp)
8. "Skip Reading" button allows advancing to next question without reading (optional, not forced)
9. Visual design: Reading section visually separated from explanation (subtle border or background color), Inter font, adequate spacing
10. Accessibility: Expandable sections keyboard-accessible (Enter to expand/collapse), screen reader announces expanded state

## Story 5.3: Reading Engagement Tracking and Analytics

As a **product manager**,
I want to track which reading chunks users engage with and how long they spend reading,
so that I can validate the reading feature's value during alpha test (Day 24 Go/No-Go decision).

**Acceptance Criteria:**
1. Track reading engagement events in `reading_engagement` table (user_id, chunk_id, session_id, displayed_at, expanded_at, time_spent_seconds, marked_read)
2. Frontend JavaScript tracks:
   - **Displayed:** Chunk shown to user (logged immediately)
   - **Expanded:** User clicked to read full content (logged on expand)
   - **Time Spent:** Seconds from expand to next action (collapse, next question, etc.) - measure reading duration
   - **Marked Read:** User clicked "Mark as Read" checkbox
3. POST `/api/reading/engagement` endpoint accepts engagement events from frontend
4. Engagement metrics calculated per user:
   - **Reading Engagement Rate:** % of displayed chunks that were expanded (target 60%+ per requirements)
   - **Average Time Spent:** Seconds per chunk (target 2-4 minutes for 200-500 token chunks per Brief)
   - **Marked Read Rate:** % of expanded chunks marked as read
5. Dashboard for product team (not user-facing): Aggregate reading metrics across all users
   - Total chunks displayed vs. expanded vs. marked read
   - Average engagement rate and time spent
   - Breakdown by KA (which KAs have highest reading engagement)
6. Alpha test validation (Day 24): Check if engagement rate >60% and user feedback positive (Story 5.4)
7. Unit tests: Engagement events logged correctly, metrics calculated accurately
8. Integration test: Full quiz flow logs reading engagement from display to mark-as-read
9. Performance: Engagement logging does not slow down quiz flow (<100ms latency)
10. Privacy: Engagement data anonymized for aggregate analytics

## Story 5.4: Reading Content Feedback and Relevance Validation

As a **user reading BABOK content**,
I want to provide feedback on whether the content was relevant to my knowledge gap,
so that the platform can improve content retrieval accuracy.

**Acceptance Criteria:**
1. Below each reading chunk, display feedback prompt: "Was this content relevant to your gap?" with Thumbs Up / Thumbs Down icons
2. Click thumbs up → POST `/api/feedback/reading` with `chunk_id`, `relevant: true`
3. Click thumbs down → POST `/api/feedback/reading` with `chunk_id`, `relevant: false`, optional `reason` text field (e.g., "Too basic", "Not related to question", "Too advanced")
4. Feedback stored in `reading_feedback` table (user_id, chunk_id, relevant, reason, timestamp)
5. Visual feedback: Icon highlights after click, "Thanks for your feedback!" message
6. Relevance metrics calculated:
   - **Relevance Rate:** % of chunks rated thumbs up (target 80%+ per Brief requirements)
   - Breakdown by KA and difficulty level
7. Product team dashboard shows relevance metrics to validate semantic search quality
8. Alpha test validation (Day 24): Check if relevance rate >70% (acceptable) or >80% (excellent) to determine Go/No-Go for reading feature
9. Unit tests: Feedback submission works, relevance metrics calculated
10. Integration test: User can rate reading content relevance, data persists

## Story 5.5: Background Reading Queue Population (v2.1 NEW - ASYNC MODEL)

As a **system**,
I want to automatically add relevant reading materials to the user's reading queue as they answer questions,
so that users have curated study materials available without interrupting their quiz flow.

**Acceptance Criteria:**
1. After user answers ANY question (correct or incorrect), trigger async background process to add reading materials
2. For incorrect answers: Add 2-3 high-priority BABOK chunks (semantic search on question concepts + KA)
3. For correct answers on Hard questions: Add 1 medium-priority chunk for reinforcement (optional, configurable)
4. For correct answers on Easy/Medium: Skip reading recommendation (user already understands)
5. Semantic search query composition:
   - Primary: Question `concept_tags` (e.g., ["stakeholder analysis", "requirements elicitation"])
   - Secondary: Question text if concept_tags insufficient
   - Filter: Same KA as question
6. POST `/api/v1/reading/queue` (internal/background call) with:
   - `user_id`, `chunk_id`, `question_id`, `session_id`
   - `was_incorrect` (boolean), `relevance_score` (from semantic search), `ka_id`
   - `priority` calculated based on: competency gap in KA (larger gap = higher priority), question difficulty
7. Priority calculation logic:
   - High: User competency in KA <60% AND incorrect answer
   - Medium: User competency 60-80% OR correct on hard question
   - Low: User competency >80% AND correct answer (rare, for completeness)
8. Database: Insert into `reading_queue` table with `reading_status = 'unread'`
9. Duplicate prevention: If chunk already in user's queue → update `relevance_score` if higher, don't duplicate
10. Performance: Background process <200ms, doesn't block answer submission response
11. Unit tests: Reading queue population triggered correctly, priority calculation accurate
12. Integration test: Answering questions adds appropriate reading materials to queue

## Story 5.6: Silent Badge Updates in Navigation

As a **system**,
I want to update the reading library badge count silently as new materials are added,
so that users are aware of new content without interrupting their quiz flow.

**Acceptance Criteria:**
1. Navigation bar includes "Reading Library" link with badge count (e.g., "Reading [7]")
2. Badge displays count of `reading_queue` items with `reading_status = 'unread'`
3. Badge updates automatically via WebSocket OR polling (every 5-10 seconds during quiz session)
4. WebSocket implementation (RECOMMENDED):
   - Backend emits `reading_queue_updated` event with new `unread_count` when items added
   - Frontend listens and updates badge count reactively
   - No popup, toast, or notification shown (completely silent)
5. Polling fallback (if WebSocket not implemented in MVP):
   - Frontend polls GET `/api/v1/reading/stats` every 10 seconds during active quiz session
   - Response: `{unread_count: 7, high_priority_count: 3}`
   - Update badge silently
6. Badge styling: Small circular badge (8px border radius), orange/blue color, white text, positioned top-right of "Reading" text
7. Badge appears only when count >0, hidden when count = 0
8. Clicking badge/link navigates to Reading Library page (Story 5.7)
9. Unit tests: Badge count updates correctly when queue items added
10. Integration test: User answering questions sees badge count increment silently

## Story 5.7: Reading Library Page with Queue Display

As a **user**,
I want to browse my reading queue in a dedicated library page,
so that I can read study materials when I'm ready, not when forced during quizzes.

**Acceptance Criteria:**
1. Dedicated page/route: `/reading-library` accessible from main navigation
2. GET `/api/v1/reading/queue?status=unread&sort_by=priority` retrieves user's reading queue
3. Query parameters supported:
   - `status=unread|reading|completed|dismissed|all` (default: unread)
   - `ka_id=uuid` (filter by Knowledge Area)
   - `priority=high|medium|low` (filter by priority)
   - `sort_by=priority|date|relevance` (default: priority)
4. Response includes array of queue items with:
   - `queue_id`, `chunk_id`, `title` (BABOK section name), `preview` (first 100 chars)
   - `babok_section` (e.g., "3.2.1"), `ka_name`, `relevance_score`, `priority`, `reading_status`
   - `word_count`, `estimated_read_minutes` (word_count / 200)
   - Context: `question_preview`, `was_incorrect`, `added_at`
5. Library page displays queue items as cards (14px border radius):
   - Priority badge (High = red, Medium = orange, Low = blue)
   - BABOK section title + preview
   - Knowledge Area tag
   - Context: "Added after incorrect answer on: [Question preview]" (shows why recommended)
   - Estimated read time (e.g., "2 min read")
   - "Read Now" button (primary CTA)
6. Tabs or filter bar: Unread (default) | Reading | Completed
7. Sort dropdown: Priority (default) | Date Added | Relevance Score
8. Filter by KA: Dropdown with 6 KA options + "All KAs"
9. Empty state: "Your reading library is empty. Complete quiz sessions to get personalized recommendations!"
10. Visual design: Framer-inspired, Inter font, cards (14px radius), main container (35px radius)
11. Accessibility: Cards keyboard navigable, screen reader announces priority and context
12. Unit tests: Library page renders, filters work
13. Integration test: User can browse queue and see all reading items

## Story 5.8: Reading Item Detail View and Engagement Tracking

As a **user**,
I want to read individual BABOK chunks in detail and mark them as complete,
so that I can learn the material and track my reading progress.

**Acceptance Criteria:**
1. Clicking "Read Now" on queue item → navigate to detail view OR expand in-place (modal or dedicated page)
2. GET `/api/v1/reading/queue/{queue_id}` retrieves full chunk content
3. Response includes:
   - Full `text_content` (200-500 tokens, formatted markdown or plain text)
   - BABOK section reference, title, KA name
   - Context: Question that prompted recommendation
   - Previous reading history: `times_opened`, `total_reading_time_seconds`
4. Detail view displays:
   - Full reading content (readable formatting, proper line spacing, paragraph breaks)
   - BABOK section reference at top (e.g., "BABOK v3 - Section 3.2.1: Stakeholder Analysis")
   - Context card: "This was recommended because you answered [Question preview] incorrectly"
   - Actions: "Mark as Complete", "Dismiss", "Back to Library"
5. Track engagement automatically:
   - On view load → increment `times_opened`, set `first_opened_at` if first time
   - On view close/navigate away → calculate `time_spent_seconds` (time between load and close)
   - PUT `/api/v1/reading/queue/{queue_id}/engagement` with `time_spent_seconds`
   - Update `total_reading_time_seconds += time_spent_seconds`
6. "Mark as Complete" action:
   - PUT `/api/v1/reading/queue/{queue_id}/status` with `reading_status = 'completed'`
   - Set `completed_at` timestamp
   - Decrement unread badge count
   - Show success message: "Great! Added to your completed reading"
7. "Dismiss" action:
   - PUT `/api/v1/reading/queue/{queue_id}/status` with `reading_status = 'dismissed'`
   - Set `dismissed_at` timestamp
   - Remove from unread count
   - Show confirmation: "Dismissed. You can find this in Dismissed tab if needed."
8. **Bulk dismiss action:** POST `/api/v1/reading/queue/batch-dismiss` endpoint
   - Request body: `{"queue_ids": ["uuid1", "uuid2", "uuid3"]}`
   - Response: `{"dismissed_count": 3, "remaining_unread_count": 4}`
   - Use case: "Dismiss All Low Priority" button on library page
   - All specified queue_ids set to `reading_status = 'dismissed'` with single API call
9. Unit tests: Engagement tracking works, status updates correctly, batch dismiss works
10. Integration test: User can read content, mark complete, batch dismiss, and see badge count update

## Story 5.9: Reading Queue Analytics and Completion Rates

As a **product team**,
I want to track reading queue engagement metrics,
so that we can validate the async reading model improves completion rates vs. inline reading.

**Acceptance Criteria:**
1. GET `/api/v1/reading/stats` endpoint returns complete user-level reading analytics
   - **Response schema** (see `docs/Asynchronous_Reading_Model.md` Lines 398-436 for complete spec):
   ```json
   {
     "reading_stats": {
       "total_items_added": 45,
       "total_completed": 28,
       "total_dismissed": 10,
       "current_unread": 7,
       "completion_rate": 0.62,
       "this_week": {
         "items_added": 7,
         "items_completed": 5,
         "total_reading_time_minutes": 25
       },
       "by_ka": [
         {
           "ka_name": "Business Analysis Planning and Monitoring",
           "unread": 3,
           "completed": 8,
           "completion_rate": 0.73
         }
       ],
       "average_reading_time_minutes": 2.5,
       "total_reading_time_hours": 1.2
     }
   }
   ```
   - Target: `completion_rate` >0.50 (50%+ per PRD v2.1 success criteria)
2. Dashboard integration: Display reading stats on main dashboard
   - "Reading Progress: X completed (Y% completion rate)"
   - "Total Reading Time: Z minutes"
3. Admin analytics endpoint GET `/api/admin/alpha-metrics/reading`:
   - Platform-wide reading completion rate
   - Comparison: Async model (v2.1) vs. Inline model (v2.0 baseline, if A/B tested)
   - Average reading time per chunk
   - Most frequently added BABOK sections (helps identify high-value content)
4. Track reading engagement by priority:
   - High priority items: Completion rate (expect highest)
   - Medium priority: Completion rate
   - Low priority: Completion rate (expect lowest)
5. Hypothesis validation metrics (Day 24 alpha test):
   - Async reading completion rate >50% (vs. 25% inline baseline per PRD)
   - User satisfaction with "read when ready" model (survey question)
6. Spaced repetition integration: Items marked "completed" should not re-appear in queue (unique constraint enforced)
7. Retention analysis: Users who complete reading have better long-term retention (tracked via spaced repetition accuracy)
8. Unit tests: Analytics calculations accurate
9. Integration test: Reading completion updates all analytics metrics
10. Performance: Analytics queries optimized with indexes on `reading_queue(user_id, reading_status)`

## Story 5.10: Manual Reading Bookmarks for Post-Session Review (v2.1 NEW)

As a **user reviewing incorrect answers**,
I want to manually bookmark specific reading materials during post-session review for later study,
so that I can save high-priority content separately from the automatic reading queue.

**Context:** This story complements the automatic reading queue (Stories 5.5-5.9) by allowing users to explicitly bookmark materials they find particularly valuable during the post-session review phase. While the reading queue is auto-populated, bookmarks are user-initiated and signify higher intent to study specific content.

**Acceptance Criteria:**
1. **Database Schema:** Create `reading_bookmarks` table with the following structure:
   ```sql
   CREATE TABLE reading_bookmarks (
       bookmark_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
       user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
       chunk_id UUID NOT NULL REFERENCES content_chunks(chunk_id) ON DELETE CASCADE,

       -- Context: What prompted this bookmark
       question_id UUID REFERENCES questions(question_id) ON DELETE SET NULL,
       session_id UUID REFERENCES sessions(session_id) ON DELETE SET NULL,
       review_id UUID REFERENCES session_reviews(review_id) ON DELETE SET NULL,

       -- State tracking
       is_read BOOLEAN DEFAULT FALSE,
       read_at TIMESTAMP,

       -- Timestamps
       bookmarked_at TIMESTAMP NOT NULL DEFAULT NOW(),

       CONSTRAINT fk_bookmark_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
       CONSTRAINT fk_bookmark_chunk FOREIGN KEY (chunk_id) REFERENCES content_chunks(chunk_id) ON DELETE CASCADE,
       CONSTRAINT unique_user_chunk_bookmark UNIQUE (user_id, chunk_id)
   );

   CREATE INDEX idx_reading_bookmarks_user ON reading_bookmarks(user_id);
   CREATE INDEX idx_reading_bookmarks_unread ON reading_bookmarks(user_id, is_read) WHERE is_read = FALSE;
   ```

2. **POST `/api/v1/reading/bookmarks` endpoint** - Create new bookmark
   - Request body: `{"chunk_id": "uuid", "question_id": "uuid", "session_id": "uuid", "review_id": "uuid"}`
   - Response: `201 Created` with `{"bookmark_id": "uuid", "chunk_id": "uuid", "bookmarked_at": "ISO8601"}`
   - Validation: Duplicate bookmarks return existing bookmark (idempotent), not 409 error
   - Business logic: If chunk already in user's reading_queue, mark it as bookmarked (add flag to reading_queue or separate tracking)

3. **GET `/api/v1/reading/bookmarks` endpoint** - Retrieve user's bookmarks
   - Query parameters:
     - `unread_only=true|false` (default: false) - Filter to unread bookmarks only
     - `ka_id=uuid` (optional) - Filter by Knowledge Area
     - `page=1` and `per_page=20` (pagination)
   - Response: Array of bookmark objects including:
     - `bookmark_id`, `chunk_id`, `title` (BABOK section name), `preview` (first 100 chars)
     - `babok_section` (e.g., "3.2.1"), `ka_name`, `word_count`, `estimated_read_minutes`
     - Context: `question_preview`, `session_id`, `review_id`, `bookmarked_at`
     - `is_read`, `read_at`
   - Pagination metadata: `total_items`, `total_pages`, `current_page`

4. **PUT `/api/v1/reading/bookmarks/{bookmark_id}/mark-read` endpoint** - Mark bookmark as read
   - Request: No body required
   - Response: `200 OK` with `{"bookmark_id": "uuid", "is_read": true, "read_at": "ISO8601"}`
   - Business logic: Set `is_read = TRUE`, `read_at = NOW()`

5. **DELETE `/api/v1/reading/bookmarks/{bookmark_id}` endpoint** - Remove bookmark
   - Response: `204 No Content`
   - Business logic: Soft delete or hard delete (decision: hard delete for MVP simplicity)

6. **Frontend Integration in Post-Session Review:**
   - When displaying reading material during review (Story 4.7), add "Save for Later" button next to each chunk
   - Clicking "Save for Later" → POST to `/api/v1/reading/bookmarks` → Visual confirmation ("Bookmarked!")
   - If chunk already bookmarked → show "Bookmarked ✓" (disabled state)

7. **Bookmarks Page/Section in Navigation:**
   - Add "Bookmarks" link in navigation (separate from "Reading Library")
   - Bookmarks page displays user's saved materials using GET `/api/v1/reading/bookmarks`
   - Tabs: "Unread Bookmarks" (default) | "All Bookmarks"
   - Each bookmark card shows same design as reading queue but with bookmark icon
   - Actions: "Read Now", "Mark as Read", "Remove Bookmark"

8. **Distinction from Reading Queue:**
   - Reading Queue (`reading_queue` table): Auto-populated, system-driven recommendations based on incorrect answers
   - Reading Bookmarks (`reading_bookmarks` table): User-initiated, manually saved high-value materials
   - Both can coexist: A chunk can be in both queue AND bookmarks (separate tables, separate tracking)
   - User benefit: Bookmarks provide a "favorites" layer on top of the queue for items requiring extra attention

9. **Analytics Tracking:**
   - Track bookmark creation rate: % of displayed reading chunks that get bookmarked (expect 10-20%)
   - Track bookmark read rate: % of bookmarks that get marked as read (target: 70%+, higher than queue)
   - Compare engagement: Bookmarked items should have higher completion rate than queue items (validates manual curation)

10. **Unit Tests:**
    - Create bookmark, retrieve bookmarks, mark as read, remove bookmark
    - Idempotent bookmark creation (duplicate returns existing)
    - Pagination works correctly
    - Filtering by unread_only and ka_id works

11. **Integration Tests:**
    - Full bookmark flow: Create → Retrieve → Mark Read → Delete
    - Bookmark during review session updates bookmarks list
    - Bookmarks persist across sessions

12. **Performance:**
    - Bookmark queries optimized with indexes on `user_id` and `is_read`
    - GET `/api/v1/reading/bookmarks` returns in <200ms for up to 100 bookmarks per user

**Success Metrics (30-day post-launch):**
- Bookmark adoption: 30%+ of users create at least 1 bookmark
- Bookmark read rate: 70%+ of bookmarks are marked as read (vs. 50% for queue items)
- Average bookmarks per active user: 5-10
- Bookmark-to-queue ratio: ~1:5 (users are selective about bookmarking)

**Relationship to Reading Queue:**
- Reading Queue (Stories 5.5-5.9): Broad net, auto-populated, may have false positives
- Reading Bookmarks (Story 5.10): Curated collection, user-verified relevance, higher intent
- Together: Queue provides discovery, Bookmarks provide focus
