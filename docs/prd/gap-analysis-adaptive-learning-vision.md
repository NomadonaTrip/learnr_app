# Gap Analysis: Adaptive Learning Vision vs. PRD Coverage

**Date:** 2025-12-21
**Prepared by:** PM (John)
**Purpose:** Identify gaps between the stated vision and current PRD documentation

---

## Executive Summary

The PRD has **complete coverage** for all adaptive learning features. All 11 categories are now at 90%+ coverage. The BKT, IRT, knowledge graph, mastery gates, spaced repetition, gamification, advanced analytics, curriculum progress, and stuck-student intervention systems are fully specified.

| Category | Coverage | Status |
|----------|----------|--------|
| BKT (mastery tracking) | 95% | ✅ Well-specified |
| IRT (question selection) | 95% | ✅ Recently added (Epic 10) |
| Knowledge graphs | 90% | ✅ Complete (Story 2.3) |
| Adaptive traversal | 95% | ✅ Complete (Story 4.11) |
| Spaced repetition | 95% | ✅ Complete (Epic 7) |
| Progress dashboards | 95% | ✅ Complete (Epic 6, Story 6.6) |
| Streak gamification | 95% | ✅ Complete (Epic 11, FR19) |
| Performance analytics | 95% | ✅ Complete (Story 4.13) |
| 100% coverage requirement | 95% | ✅ Complete (FR5C, Story 4.12) |
| Dependency enforcement | 95% | ✅ Complete (Story 4.11) |
| Stuck-student intervention | 95% | ✅ Complete (Story 5.11) |

---

## Detailed Analysis

### 1. BKT (Mastery Tracking) ✅

**Status:** COMPLETE

**Coverage:**
- Algorithm 3: Bayesian Belief Update (algorithm-specifications.md)
- Algorithm 4: Information Gain Calculation (algorithm-specifications.md)
- Story 3.4: Belief State Initialization
- Story 4.4: Bayesian Belief Update Engine
- Beta-Bernoulli model with slip/guess parameters
- Prerequisite propagation (Story 2.3)

**Locations:**
- `docs/prd/algorithm-specifications.md` (Algorithms 3, 4)
- `docs/stories/4.4-bayesian-belief-update-engine.story.md`
- `docs/prd/epic-4-bkt.md`

**No gaps identified.**

---

### 2. IRT (Question Selection) ✅

**Status:** COMPLETE (Recently added)

**Coverage:**
- Algorithm 7: User Ability Classification per Concept
- Algorithm 8: IRT Difficulty Distribution Selection
- Algorithm 9: Combined BKT-IRT Question Selection
- IRT scale migration (-3.0 to +3.0)
- Difficulty distribution by ability level

**Locations:**
- `docs/prd/algorithm-specifications.md` (Algorithms 7, 8, 9)
- `docs/prd/epic-10-irt-difficulty-distribution.md`
- `docs/architecture/adr-002-irt-difficulty-scale.md`
- `docs/prd/traceability-matrix-irt.md`

**No gaps identified.**

---

### 3. Knowledge Graphs (Curriculum Structure) ✅

**Status:** COMPLETE

**Coverage:**
- Concept prerequisite table (`concept_prerequisites`)
- DAG validation (no cycles)
- Hierarchical, semantic, and GPT-4 inference
- Prerequisite depth calculation
- In-memory graph cache for O(1) lookups
- API: GET /v1/concepts/{id}/prerequisites

**Locations:**
- `docs/stories/2.3.concept-prerequisite-graph.md` (720 lines, comprehensive)
- `docs/prd/database-schema-bkt.md`

**No gaps identified.**

---

### 4. Adaptive Traversal (Navigation) ✅

**Status:** COMPLETE (Recently added)

**Coverage:**
- BKT-based question selection (max information gain)
- IRT-based difficulty distribution
- Focused practice mode (KA or concept targeting)
- Prerequisite weighting in selection
- **Story 4.11: Prerequisite-Based Curriculum Navigation** (mastery gates)

**Specifications Delivered:**
1. **Mastery gates:** P(mastery) > 0.7 threshold for prerequisites
2. **Soft/hard enforcement:** Configurable gate enforcement mode
3. **Unlock conditions:** Prerequisite mastery triggers unlock events
4. **Visual indicators:** Lock icons on concepts, progress toward unlock
5. **Override capability:** Advanced users can attempt locked concepts
6. **Dashboard integration:** Locked/unlocked concept counts

**Locations:**
- `docs/prd/epic-4-bkt.md` (Story 4.11)
- `docs/stories/2.3.concept-prerequisite-graph.md` (prerequisite graph)

**No gaps remaining.**

---

### 5. Spaced Repetition (Retention) ✅

**Status:** COMPLETE

**Coverage:**
- SM-2 algorithm adaptation (Epic 7)
- Concept mastery tracking (Story 7.1)
- Review scheduling: 1→3→7→14 day intervals (Story 7.2)
- Mixed sessions: 40% reviews + 60% new (Story 7.3)
- Review accuracy metrics (Story 7.4)
- Reviews due indicator (Story 7.5)

**Locations:**
- `docs/prd/epic-7.md`
- `docs/stories/7.1-7.5` (if exist as separate files)

**No gaps identified.**

---

### 6. Progress Dashboards (Visibility) ✅

**Status:** COMPLETE (Recently enhanced)

**Coverage:**
- 6 KA competency bars (Story 6.1)
- Exam readiness score (Story 6.1)
- Weekly progress trends (Story 6.2)
- Days until exam countdown (Story 6.3)
- KA detail drill-down (Story 6.4)
- Actionable recommendations (Story 6.5)
- Reviews due indicator (Story 7.5)
- **Story 6.6: Curriculum Progress & Concept Unlock Display** (recently added)

**Specifications Delivered (Story 6.6):**
1. **Curriculum progress card:** Total/unlocked/locked/mastered concept counts
2. **Unlock percentage:** Visual progress bar with segmented display
3. **Recently unlocked:** Last 3 concepts with celebration animation
4. **Per-KA breakdown:** Unlock progress by knowledge area
5. **Next unlock preview:** Concepts closest to being unlocked

**Locations:**
- `docs/prd/epic-6.md` (Stories 6.1-6.6)

**No gaps remaining.**

---

### 7. Streak Gamification (Motivation) ✅

**Status:** COMPLETE (Recently added)

**Coverage:**
- Epic 11: Gamification & Motivation System (7 stories)
- FR19: Gamification functional requirements (29 requirements)
- Database schema: `study_streaks`, `daily_activity`, `achievements`, `user_achievements`, `streak_notifications`

**Specifications Delivered:**
1. **Streak calculation rules:** 5 questions OR 10 min OR 3 readings qualifies a day
2. **Streak milestones:** Badges at 3, 7, 14, 30, 60 days
3. **Streak visualization:** Flame icon, calendar view, milestone celebrations
4. **Streak recovery:** 2 freezes/month, 24h retroactive grace period
5. **Achievement system:** 16+ badges across 4 categories (streak, volume, mastery, special)
6. **Study goals:** Daily/weekly targets with progress tracking
7. **Notifications:** Evening reminder, late warning, milestone celebrations

**Locations:**
- `docs/prd/epic-11-gamification-motivation.md`
- `docs/prd/functional-requirements.md` (FR19)
- `docs/prd/epic-list.md` (Epic 11 entry)

**No gaps remaining.**

---

### 8. Performance Analytics (Insights) ✅

**Status:** COMPLETE (Recently added)

**Coverage:**
- Story 4.10: Quiz Analytics and Dashboard Data
- Accuracy trends, study time, coverage progress
- Review accuracy by interval (Story 7.4)
- Admin analytics endpoints
- **Story 4.13: Advanced Performance Analytics** (recently added)

**Specifications Delivered (Story 4.13):**
1. **Time-based analytics:** Best study hour/day, accuracy by time, fatigue analysis
2. **Question-level analytics:** Hardest/easiest questions, frequently missed concepts
3. **Improvement velocity:** Weekly changes, velocity trend, projected ready date
4. **Comparison analytics:** Percentile rank vs anonymized cohort
5. **Export/reports:** PDF and CSV export with configurable date ranges

**Locations:**
- `docs/prd/epic-4-bkt.md` (Story 4.13)

**No gaps remaining.**

---

### 9. 100% Coverage Requirement ✅

**Status:** COMPLETE (Recently added)

**Coverage:**
- Story 4.5: Coverage Progress Tracking (comprehensive)
- **FR5C: Coverage Completion & Exam Readiness Requirements** (15 requirements)
- **Story 4.12: Exam Readiness Assessment & Coverage Gates**

**Specifications Delivered:**
1. **Explicit requirement:** Exam Ready = 80%+ coverage AND 70%+ confidence AND all KAs >= 60%
2. **Coverage targets:** Configurable thresholds per course (CBAP vs CFA)
3. **Readiness score:** Weighted formula (coverage × 0.4 + confidence × 0.3 + ka_balance × 0.3)
4. **KA balance:** Minimum 60% per KA, max 20% variance between KAs
5. **Status levels:** NOT_READY, ALMOST_READY, READY, WELL_PREPARED
6. **Recommendations:** Actionable guidance for reaching readiness
7. **API endpoint:** GET `/api/v1/readiness`

**Locations:**
- `docs/prd/functional-requirements.md` (FR5C)
- `docs/prd/epic-4-bkt.md` (Story 4.12)

**No gaps remaining.**

---

### 10. Dependency Enforcement ✅

**Status:** COMPLETE (Recently added)

**Coverage:**
- Prerequisite graph exists (Story 2.3)
- Prerequisite weighting in question selection (Algorithm 9)
- `prerequisite_depth` calculated for each concept
- **Story 4.11: Prerequisite-Based Curriculum Navigation** (mastery gates)

**Specifications Delivered:**
1. **Mastery gate thresholds:** P(mastery) > 0.7 AND confidence > 0.6
2. **Soft vs. hard enforcement:** Configurable mode (default: soft)
3. **Visual indication:** Lock icons, progress bars, tooltips
4. **Unlock notifications:** Events triggered when prerequisites mastered
5. **Override capability:** Advanced users can attempt locked concepts

**Locations:**
- `docs/prd/epic-4-bkt.md` (Story 4.11)
- `docs/stories/2.3.concept-prerequisite-graph.md` (prerequisite graph)

**No gaps remaining.**

---

### 11. Stuck-Student Intervention ✅

**Status:** COMPLETE

**Coverage:**
- Story 5.11: Concept-Linked Reading Intervention (comprehensive)
- `concept_ids` array on reading_queue items
- Consecutive failure tracking (`consecutive_failures`, `failures_since_reading`)
- Gentle nudge at 3 failures
- Strong modal at 5 failures
- Question deprioritization for stuck concepts
- Reading completion resets intervention

**Locations:**
- `docs/stories/5.11-concept-linked-reading-intervention.story.md`
- `docs/prd/algorithm-specifications.md` (Algorithm 9 references intervention)

**No gaps identified.**

---

## Summary of Gaps

### Critical Gaps (Need New Stories/Epics)

| Gap | Recommendation | Priority |
|-----|----------------|----------|
| ~~Streak Gamification~~ | ~~Create Epic 11: Gamification & Motivation System~~ | ✅ RESOLVED |
| ~~Mastery Gates~~ | ~~Create Story 4.11: Prerequisite-Based Curriculum Navigation~~ | ✅ RESOLVED |

### Minor Gaps (Enhancements to Existing Stories)

| Gap | Recommendation | Priority |
|-----|----------------|----------|
| ~~100% Coverage Requirement~~ | ~~Add FR5C requirements, clarify in Story 4.5~~ | ✅ RESOLVED |
| ~~Dashboard Curriculum Progress~~ | ~~Add to Story 6.1: % concepts unlocked~~ | ✅ RESOLVED (Story 6.6) |
| ~~Advanced Analytics~~ | ~~Extend Story 4.10 with time-based analysis~~ | ✅ RESOLVED (Story 4.13) |

---

## Recommended Actions

### Immediate (Before Next Sprint)

1. ~~**Create Epic 11: Gamification & Motivation System**~~ ✅ COMPLETE
   - ~~Defines streak rules, visualization, badges~~
   - ~~Critical for user engagement~~
   - **Delivered:** Epic 11 with 7 stories, FR19 with 29 requirements

2. ~~**Create Story 4.11: Prerequisite-Based Curriculum Navigation**~~ ✅ COMPLETE
   - ~~Defines mastery gates and progression logic~~
   - ~~Ensures systematic knowledge building~~
   - **Delivered:** Story 4.11 in Epic 4 with mastery gate service, API endpoints, dashboard integration

### Near-Term (Next 2 Sprints)

3. ~~**Add FR5C: Coverage Completion Requirements**~~ ✅ COMPLETE
   - ~~Explicit coverage targets for exam readiness~~
   - **Delivered:** FR5C with 15 requirements, Story 4.12 with readiness calculator

4. ~~**Enhance Story 4.10: Advanced Analytics**~~ ✅ COMPLETE
   - ~~Time-based insights, comparison analytics~~
   - **Delivered:** Story 4.13 with time analytics, question-level insights, velocity tracking, comparison analytics, export reports

5. ~~**Dashboard Curriculum Progress**~~ ✅ COMPLETE
   - ~~Visual curriculum map showing progress~~
   - **Delivered:** Story 6.6 with curriculum progress card, unlock tracking, per-KA breakdown

### Deferred (Phase 2)

6. **Learning Path Visualization** (Optional Enhancement)
   - Visual graph-based curriculum map (beyond basic progress display)
   - Interactive dependency tree exploration
   - Note: Story 6.6 provides core curriculum progress; this is a visual enhancement

---

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-12-21 | 1.0 | Initial gap analysis | PM (John) |
| 2025-12-21 | 1.1 | Marked Streak Gamification as COMPLETE (Epic 11, FR19 added) | PM (John) |
| 2025-12-21 | 1.2 | Marked Mastery Gates as COMPLETE (Story 4.11 added to Epic 4) | PM (John) |
| 2025-12-21 | 1.3 | Marked Coverage Requirement as COMPLETE (FR5C, Story 4.12 added) | PM (John) |
| 2025-12-21 | 1.4 | Marked ALL GAPS RESOLVED: Performance Analytics (Story 4.13), Dashboard Curriculum Progress (Story 6.6) | PM (John) |
