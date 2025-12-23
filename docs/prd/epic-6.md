# Epic 6: Progress Dashboard & Transparency

**Epic Goal:** Provide users with comprehensive progress visibility through a real-time dashboard showing competency scores for all 6 KAs, exam readiness scoring, weekly progress trends, reviews due count, days until exam, and actionable recommendations. This epic delivers the transparency that builds user trust and engagement.

## Story 6.1: Dashboard Overview with 6 KA Competency Bars

As a **user**,
I want to see my current competency scores for all 6 CBAP knowledge areas at a glance,
so that I understand exactly where I stand and which areas need focus.

**Acceptance Criteria:**
1. GET `/api/dashboard` endpoint returns user's current competency data (requires authentication)
2. Response includes:
   - `ka_scores`: Array of 6 objects with `ka_name`, `competency_score` (0-100%), `target_score`, `gap` (target - current)
   - `exam_readiness_score`: Overall readiness (0-100%, average or weighted average of 6 KAs)
   - `days_until_exam`: Calculated from onboarding `exam_date`
   - `reviews_due_count`: Number of concepts needing spaced repetition review (Epic 7 integration)
   - `quizzes_completed`: Total completed quiz sessions (lifetime count)
   - `quizzes_this_week`: Quiz sessions completed in current week (optional display)
   - `total_questions_answered`: Lifetime count
   - `total_time_spent_minutes`: Cumulative study time across all sessions
   - `total_reading_consumed`: Number of chunks read
3. Dashboard UI displays 6 competency bars (horizontal bars or radial/circular charts):
   - Each bar shows KA name, current score (e.g., "Strategy Analysis: 75%"), target score (e.g., "Target: 85%")
   - Bar color-coded: Red (<70%), Orange (70-85%), Green (>85%)
   - Visual fill indicates progress toward target (e.g., bar filled 75% if score is 75%)
4. Hero metric: Exam Readiness Score displayed prominently (large text, color-coded, main screen container 35px radius)
5. Recommended focus areas: "Focus on [Lowest KA]" callout or section highlighting weakest 2-3 KAs
6. Visual design: Framer-inspired layout, Inter font, primary cards for KA bars (22px radius), main container (35px radius)
7. Accessibility: Bar charts have text labels (not color-only), screen reader announces competency scores
8. Unit tests: Dashboard data retrieval, competency scores displayed correctly
9. Integration test: Dashboard reflects competency updates from quiz sessions
10. Performance: Dashboard renders in <2 seconds with all data

## Story 6.2: Weekly Progress Trends Chart

As a **user tracking my improvement**,
I want to see how my competency scores have changed week-over-week,
so that I stay motivated by visible progress.

**Acceptance Criteria:**
1. Backend calculates weekly competency snapshots:
   - Every 7 days (or weekly cron job), store snapshot of all 6 KA scores in `competency_history` table (user_id, snapshot_date, ka, competency_score)
   - Alternative: Calculate on-the-fly from `competency_tracking.last_updated` timestamps (if real-time snapshots not stored)
2. GET `/api/dashboard/trends` endpoint returns weekly progress data for last 4-8 weeks
3. Response: Array of weekly snapshots with date and 6 KA scores per week
4. Dashboard displays line chart or bar chart showing competency trends over time:
   - X-axis: Weeks (Week 1, Week 2, ...)
   - Y-axis: Competency score (0-100%)
   - Multiple lines/bars for each KA (6 lines or 6 grouped bars)
5. Chart highlights improvement: Positive deltas shown in green (e.g., "+5% this week"), negative in orange (rare, indicates need for review)
6. If user has <2 weeks of data, show message: "Complete more quiz sessions to unlock weekly progress trends"
7. Chart library: Recharts or Chart.js (as specified in Technical Assumptions)
8. Visual design: Chart card (22px radius), Inter font for labels, color scheme consistent with overall design
9. Accessibility: Chart data available in table format for screen readers (toggle view or aria-label with values)
10. Performance: Trends chart renders in <1 second (included in dashboard <2 second total)

## Story 6.3: Exam Countdown and Readiness Indicators

As a **user preparing for a specific exam date**,
I want to see how many days I have until my exam and whether I'm on track to be ready,
so that I can adjust my study intensity if needed.

**Acceptance Criteria:**
1. Dashboard displays "Days Until Exam: X days" prominently (from onboarding `exam_date`)
2. If exam date is <30 days away: Display urgency indicator (orange/red color, "Less than 1 month!")
3. If exam date is <7 days away: Display critical urgency (red, "Exam in X days - final review!")
4. Exam readiness threshold: 75% average competency or all 6 KAs >70% (configurable)
5. Readiness status indicator:
   - **Ready:** Green checkmark, "You're exam-ready!" (all KAs >70% or average >75%)
   - **Almost Ready:** Orange icon, "Focus on [KA Names] to reach readiness" (1-2 KAs <70%)
   - **Not Ready:** Red icon, "Continue studying - X KAs below target" (3+ KAs <70%)
6. Pacing recommendations (future enhancement noted, not fully implemented in MVP):
   - If exam in 30 days and user <60% avg competency: "Consider increasing daily study time or adjusting exam date"
   - If user on track: "Great progress! Keep up daily sessions to maintain retention"
7. User can update exam date from settings (Story 8.2) if timeline changes
8. Visual design: Countdown and readiness status in hero section (main container 35px radius), clear color-coding
9. Accessibility: Color-coded status supplemented with text and icons (not color-only)
10. Unit tests: Countdown calculated correctly, readiness status accurate based on competency scores

## Story 6.4: Knowledge Area Detail Drill-Down

As a **user wanting to understand my gaps in a specific KA**,
I want to drill down into a KA's detail view to see concept-level gaps and recent performance,
so that I can focus my studying on specific weaknesses within that KA.

**Acceptance Criteria:**
1. Dashboard KA bars are clickable (or have "View Details" button) → navigates to KA detail page
2. GET `/api/dashboard/ka/{ka_name}` endpoint returns detailed data for one KA:
   - `ka_name`, `competency_score`, `target_score`, `gap`
   - `concept_gaps`: Array of concepts within this KA with low performance (e.g., ["Stakeholder Analysis: 50%", "RACI Matrix: 60%"])
   - `recent_questions`: Last 10 questions answered in this KA with correctness (correct/incorrect)
   - `time_spent`: Total minutes spent studying this KA
   - `questions_answered`: Count of questions answered in this KA
3. KA detail view displays:
   - **Header:** KA name, current score, target, gap (primary card 22px radius)
   - **Concept Gaps:** List of weak concepts (if trackable, else generic "Review questions you missed")
   - **Recent Performance:** Visual timeline or list showing last 10 questions (green checkmark = correct, red X = incorrect)
   - **Time Spent:** "You've spent X minutes on this KA"
   - **Recommended Action:** "Focus on [specific concept]" or "Continue practicing [KA] questions"
4. Primary CTA: "Study [KA Name]" button → starts KA-focused quiz session (filter adaptive selection to this KA only)
5. Secondary CTA: "Back to Dashboard" link
6. Visual design: Detail page consistent with dashboard (Framer-inspired, Inter font, card styling)
7. Accessibility: Navigation breadcrumb (Dashboard > [KA Name]), keyboard-accessible back button
8. Unit tests: KA detail data retrieval, concept gaps calculated
9. Integration test: Clicking KA bar navigates to detail view, detail view reflects KA-specific data
10. Performance: KA detail view loads in <1 second

## Story 6.5: Actionable Recommendations and CTAs

As a **user viewing my dashboard**,
I want clear recommendations on what to study next,
so that I don't waste time deciding and can immediately take action.

**Acceptance Criteria:**
1. Dashboard calculates actionable recommendations based on current state:
   - **If reviews due:** Primary CTA = "Start Reviews (X concepts due)" (Epic 7 integration)
   - **If no reviews due:** Primary CTA = "Continue Learning" → starts adaptive quiz session (Epic 4)
   - **If specific KA very weak (<60%):** Recommendation callout = "Priority: Focus on [KA Name] (scored X%)"
2. Recommendations section (card, 22px radius) displays:
   - **Top recommendation:** "Your next best step: [Action]"
   - **Secondary recommendations:** List of 2-3 suggested actions (e.g., "Review Strategy Analysis concepts", "Complete 10 more questions to unlock trends")
3. CTAs are pill-rounded buttons (primary color, high contrast)
4. If user completes primary recommendation (e.g., finishes reviews), dashboard updates CTA dynamically on next load
5. Recommendation logic documented: Based on reviews due > weakest KA > general quiz (priority hierarchy)
6. Visual design: Recommendations prominent but not overwhelming (balanced with competency visualizations)
7. Accessibility: CTA buttons have clear aria-labels ("Start 5 review questions now")
8. Unit tests: Recommendation logic selects appropriate CTA based on user state
9. Integration test: Dashboard shows correct CTA after completing quiz session or reviews
10. A/B testing placeholder (Phase 2): Track which recommendations drive most engagement

## Story 6.6: Curriculum Progress & Concept Unlock Display (NEW)

As a **user tracking my learning journey**,
I want to see my curriculum progress showing how many concepts I've unlocked and mastered,
so that I understand my progression through the knowledge structure and feel a sense of accomplishment.

**Background:**
Story 4.11 introduces mastery gates that lock/unlock concepts based on prerequisite mastery. This story adds the dashboard visualization of that progression, showing users their journey through the curriculum structure.

**Acceptance Criteria:**

1. **Curriculum Progress API Extension:**
   - Extend GET `/api/dashboard` to include:
     ```json
     {
       "curriculum_progress": {
         "total_concepts": 1203,
         "unlocked": 892,
         "locked": 311,
         "mastered": 487,
         "in_progress": 405,
         "untouched": 311,
         "unlock_percentage": 74.1,
         "mastery_percentage": 40.5,
         "recently_unlocked": [
           {"concept_id": "uuid", "name": "Requirements Prioritization", "unlocked_at": "2025-12-20T14:30:00Z"}
         ]
       }
     }
     ```

2. **Curriculum Progress Card on Dashboard:**
   - Display curriculum progress as visual card (22px radius)
   - **Primary metric:** "X% Curriculum Unlocked" with progress ring/bar
   - **Secondary metrics:**
     - "X concepts mastered" (green)
     - "X in progress" (yellow)
     - "X locked" (gray with lock icon)
   - **Visual:** Segmented progress bar showing mastered/in-progress/locked proportions

3. **Recently Unlocked Concepts:**
   - Show last 3 concepts unlocked (from `concept_unlock_events` table)
   - Each shows: concept name, time since unlock ("2 hours ago")
   - Celebration micro-animation when new unlock appears
   - "View All" link to full unlock history

4. **Unlock Progress by Knowledge Area:**
   - GET `/api/dashboard/curriculum/by-ka` returns per-KA breakdown:
     ```json
     {
       "by_knowledge_area": [
         {
           "ka_id": "business_analysis_planning",
           "ka_name": "Business Analysis Planning",
           "total_concepts": 187,
           "unlocked": 156,
           "locked": 31,
           "mastered": 89,
           "unlock_percentage": 83.4
         }
       ]
     }
     ```
   - Dashboard can show mini-progress bars per KA

5. **Next Unlock Preview:**
   - Show 1-3 concepts closest to being unlocked:
     ```json
     {
       "next_to_unlock": [
         {
           "concept_id": "uuid",
           "name": "Advanced Stakeholder Mapping",
           "blocking_prereq": "Stakeholder Analysis",
           "prereq_mastery": 0.65,
           "required_mastery": 0.70,
           "questions_to_unlock": 2
         }
       ]
     }
     ```
   - Display: "Almost unlocked: {concept} (2 more questions)"
   - Motivates continued study

6. **Visual Design:**
   - Curriculum card placed prominently on dashboard (after KA competency bars)
   - Progress ring uses brand colors: Green (mastered), Yellow (in-progress), Gray (locked)
   - Lock icons for locked concepts (subtle, not alarming)
   - Unlock celebration: Brief confetti or glow animation

7. **Accessibility:**
   - Progress percentages announced by screen readers
   - Lock status conveyed via text, not just icons
   - "X of Y concepts unlocked in {KA}" for AT users

8. **Integration with Story 4.11:**
   - Uses `concept_unlock_events` table from Story 4.11
   - Uses `check_prerequisites_mastered()` from MasteryGateService
   - Real-time unlock notification triggers dashboard refresh

9. **Performance Requirements:**
   - Curriculum progress calculation: <150ms
   - Uses cached data where possible
   - Incremental updates (not full recalculation)

10. **Testing Requirements:**
    - Unit tests: Progress calculation, unlock percentage
    - Integration tests: API returns correct counts, recently unlocked accurate
    - Visual regression: Progress bar renders correctly at various percentages

**Dependencies:**
- **Requires:** Story 4.11 (Prerequisite-Based Curriculum Navigation) - unlock events table
- **Requires:** Story 4.5 (Coverage Tracking) - mastery classification
- **Integrates with:** Story 6.1 (Dashboard Overview) - curriculum card placement

**Configuration Options:**

| Parameter | Default | Description |
|-----------|---------|-------------|
| `recently_unlocked_count` | 3 | Number of recent unlocks to show |
| `next_to_unlock_count` | 3 | Number of "almost unlocked" to show |
| `unlock_celebration_enabled` | true | Show celebration animation |

---

## Dependencies

```
Epic 6 Dependencies:

6.1 (Dashboard) → 6.2 (Trends) → 6.3 (Countdown)
6.1 → 6.4 (KA Detail)
6.1 → 6.5 (Recommendations)
6.1, 4.11 → 6.6 (Curriculum Progress) - requires unlock events from 4.11

Requires from Epic 4:
- Competency tracking (4.5)
- Quiz analytics (4.10)
- Mastery gates (4.11)

Requires from Epic 7:
- Reviews due count (7.5)
```

---

## Success Metrics

| Metric | Target | Story |
|--------|--------|-------|
| Dashboard load time | <2s | 6.1 |
| Trends chart render | <1s | 6.2 |
| KA detail load | <1s | 6.4 |
| User dashboard visits | >3x/week | 6.1 |
| KA drill-down usage | >50% of users | 6.4 |
| Curriculum progress views | >60% of users | 6.6 |
| Unlock celebration engagement | >30% interaction | 6.6 |

---

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-11-21 | 1.0 | Initial Epic 6 with Stories 6.1-6.5 | Sarah (Product Owner) |
| 2025-12-21 | 1.1 | Added Story 6.6: Curriculum Progress & Concept Unlock Display - integrates with Story 4.11 mastery gates | PM (John) |
| 2025-12-22 | 1.2 | Story 6.1: Added quiz completion metrics (quizzes_completed, quizzes_this_week, total_time_spent_minutes) to align with Story 4.7 dashboard integration requirements | PM (John) |
