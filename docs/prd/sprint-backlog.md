# Sprint Backlog: Adaptive Learning Platform

**Last Updated:** 2025-12-23
**Current Sprint:** Sprint 8 - Adaptive Core Completion
**Branch:** `feature/coverage-progress-tracking`

---

## Executive Summary

This document provides the **execution-ordered backlog** for the LearnR adaptive learning platform. Story numbers (e.g., 4.5, 10.3) remain stable identifiers tied to their domain epics. This backlog defines **implementation sequence**.

**Total Outstanding Stories:** ~45 stories across Epics 4, 5, 6, 7, 8, 10, and 11

---

## Completed Sprints (Reference)

### Sprints 1-3: Foundation & Authentication (Epic 1)
| Story | Title | Status |
|-------|-------|--------|
| 1.1 | Monorepo Setup | ✅ Complete |
| 1.2 | PostgreSQL Setup | ✅ Complete |
| 1.3 | User Registration | ✅ Complete |
| 1.4 | User Login | ✅ Complete |
| 1.5 | Password Reset | ✅ Complete |
| 1.6 | JWT Auth Middleware | ✅ Complete |
| 1.7 | Health Check & API Docs | ✅ Complete |

### Sprints 3-4: Content Foundation (Epic 2)
| Story | Title | Status |
|-------|-------|--------|
| 2.0 | Courses Table Setup | ✅ Complete |
| 2.1 | Qdrant Vector Database Setup | ✅ Complete |
| 2.1.1 | Qdrant Multi-Course Support | ✅ Complete |
| 2.2 | BABOK Concept Extraction | ✅ Complete |
| 2.3 | Concept Prerequisite Graph | ✅ Complete |
| 2.4 | Vendor Question Import | ✅ Complete |
| 2.5 | Question Embedding Generation | ✅ Complete |
| 2.6 | BABOK Parsing and Chunking | ✅ Complete |
| 2.7 | BABOK Chunk Embedding | ✅ Complete |
| 2.8 | Question Retrieval API | ✅ Complete |
| 2.9 | Reading Retrieval API | ✅ Complete |
| 2.10 | Concept API Endpoints | ✅ Complete |
| 2.13 | Pre-Tagged Concept Import | ✅ Complete |
| 2.14 | Belief State Sync for New Concepts | ✅ Complete |
| 2.15 | Secondary Tagging (Perspectives/Competencies) | ✅ Complete |
| 2.16 | Non-Conventional KA Mapping | ✅ Complete |

### Sprints 5-6: Onboarding & Diagnostic (Epic 3)
| Story | Title | Status |
|-------|-------|--------|
| 3.1 | Marketing Landing Page | ✅ Complete |
| 3.2 | Onboarding Questions | ✅ Complete |
| 3.3 | Account Creation | ✅ Complete |
| 3.4 | Belief State Initialization | ✅ Complete |
| 3.4.1 | Familiarity Belief Prior Integration | ✅ Complete |
| 3.5 | Optimal Diagnostic Question Selection | ✅ Complete |
| 3.6 | Diagnostic Assessment UI | ✅ Complete |
| 3.7 | Diagnostic Belief Updates | ✅ Complete |
| 3.8 | Diagnostic Results with Concept Coverage | ✅ Complete |
| 3.8.1 | Collapsible Results Layout | ✅ Complete |
| 3.9 | Diagnostic Session Management | ✅ Complete |
| 3.10 | User Login Page | ✅ Complete |

### Sprint 7: Core Quiz Engine (Epic 4 - Partial)
| Story | Title | Status |
|-------|-------|--------|
| 4.1 | Quiz Session Creation | ✅ Complete |
| 4.1.1 | Quiz Session Frontend | ✅ Complete |
| 4.2 | Bayesian Question Selection Engine | ✅ Complete |
| 4.3 | Answer Submission and Immediate Feedback | ✅ Complete |
| 4.4 | Bayesian Belief Update Engine | ✅ Complete |
| 4.6 | Explanation Display and Concept Context | ✅ Complete |
| 4.7 | Fixed-Length Session Auto-Completion | ✅ Complete |
| 4.8 | Focused Practice Mode | ✅ Complete |
| 4.9 | Post-Session Review Mode | ✅ Complete |

---

## Current Sprint

### Sprint 8: Adaptive Core Completion
**Goal:** Complete coverage tracking and IRT difficulty selection to enhance the adaptive engine.

**Sprint Duration:** 2 weeks
**Start Date:** 2025-12-23

| Priority | Story | Title | Status | Pipeline | Assignee | Notes |
|----------|-------|-------|--------|----------|----------|-------|
| P1 | **4.5** | Coverage Progress Tracking | 🔄 In Progress | 💻 `implementing` | - | Current branch work |
| P2 | **10.1** | IRT Scale Database Migration | ✅ Complete | ✅ `complete` | - | QA: PASS, committed |
| P3 | **10.6** | Pydantic Schema Updates for IRT | ✅ Complete | ✅ `complete` | - | QA: PASS (98/100) |
| P4 | **10.2** | Question Import IRT Support | ✅ Complete | ✅ `complete` | - | QA: PASS (95/100) |
| P5 | **10.3** | User Ability Classification (Alg 7) | ✅ Complete | ✅ `complete` | - | QA: PASS (96/100) |
| P6 | **10.4** | IRT Difficulty Distribution (Alg 8) | ✅ Complete | ✅ `complete` | - | QA: PASS (97/100) |
| P7 | **10.5** | Combined BKT-IRT Selection (Alg 9) | ✅ Complete | ✅ `complete` | - | QA: PASS (98/100) |
| P8 | **10.7** | Algorithm Specification Documentation | ✅ Complete | ✅ `complete` | - | QA: PASS (99/100) |

**Sprint 8 Definition of Done:**
- [ ] Coverage API returns mastered/gap/uncertain counts
- [ ] Questions have IRT scale difficulty (-3.0 to +3.0)
- [ ] Question selection uses ability-based difficulty distribution
- [ ] Unit tests for all new services
- [ ] Integration tests for API endpoints

---

## Upcoming Sprints

### Sprint 9: Mastery Gates & Exam Readiness
**Goal:** Implement prerequisite-based progression and exam readiness scoring.

| Priority | Story | Title | Dependencies | Status |
|----------|-------|-------|--------------|--------|
| P1 | **4.11** | Prerequisite-Based Curriculum Navigation | 2.3, 4.4 | 📋 Backlog |
| P2 | **4.12** | Exam Readiness Assessment & Coverage Gates | 4.5 | 📋 Backlog |
| P3 | **6.6** | Curriculum Progress & Concept Unlock Display | 4.11, 4.5 | 📋 Backlog |

---

### Sprint 10: Reading Library (Async Model v2.1)
**Goal:** Implement the asynchronous reading library for gap-based content delivery.

| Priority | Story | Title | Dependencies | Status |
|----------|-------|-------|--------------|--------|
| P1 | **5.5** | Background Reading Queue Population | 4.3 | 📋 Backlog |
| P2 | **5.6** | Silent Badge Updates in Navigation | 5.5 | 📋 Backlog |
| P3 | **5.7** | Reading Library Page with Queue Display | 5.5 | 📋 Backlog |
| P4 | **5.8** | Reading Item Detail View & Engagement | 5.7 | 📋 Backlog |
| P5 | **5.9** | Reading Queue Analytics | 5.8 | 📋 Backlog |
| P6 | **5.10** | Manual Reading Bookmarks | 5.7 | 📋 Backlog |
| P7 | **5.11** | Concept-Linked Reading Intervention | 5.5, 4.4 | 📋 Backlog |

---

### Sprint 11: Spaced Repetition System
**Goal:** Implement SM-2 algorithm for long-term retention.

| Priority | Story | Title | Dependencies | Status |
|----------|-------|-------|--------------|--------|
| P1 | **7.1** | Concept Mastery Tracking | 4.3 | 📋 Backlog |
| P2 | **7.2** | SM-2 Review Scheduling | 7.1 | 📋 Backlog |
| P3 | **7.3** | Mixed Quiz Sessions (40% reviews) | 7.1, 7.2 | 📋 Backlog |
| P4 | **7.4** | Review Performance Tracking | 7.3 | 📋 Backlog |
| P5 | **7.5** | Reviews Due Indicator on Dashboard | 7.1, 6.1 | 📋 Backlog |

---

### Sprint 12: Progress Dashboard
**Goal:** Complete the user-facing dashboard with all progress visualizations.

| Priority | Story | Title | Dependencies | Status |
|----------|-------|-------|--------------|--------|
| P1 | **6.1** | Dashboard Overview with 6 KA Bars | 4.5 | 📋 Backlog |
| P2 | **6.2** | Weekly Progress Trends Chart | 6.1 | 📋 Backlog |
| P3 | **6.3** | Exam Countdown and Readiness | 6.1, 4.12 | 📋 Backlog |
| P4 | **6.4** | Knowledge Area Detail Drill-Down | 6.1 | 📋 Backlog |
| P5 | **6.5** | Actionable Recommendations and CTAs | 6.1-6.4, 7.5 | 📋 Backlog |
| P6 | **4.10** | Quiz Analytics and Dashboard Data | 4.4, 4.5 | 📋 Backlog |

---

### Sprint 13: Gamification Core
**Goal:** Implement streaks, achievements, and study goals for engagement.

| Priority | Story | Title | Dependencies | Status |
|----------|-------|-------|--------------|--------|
| P1 | **11.1** | Daily Streak Tracking | 4.3 | 📋 Backlog |
| P2 | **11.2** | Streak Visualization on Dashboard | 11.1, 6.1 | 📋 Backlog |
| P3 | **11.3** | Achievement Badges and Milestones | 11.1 | 📋 Backlog |
| P4 | **11.6** | Study Goals and Progress Tracking | 11.1 | 📋 Backlog |

---

### Sprint 14: Gamification Polish
**Goal:** Add streak protection, notifications, and admin analytics.

| Priority | Story | Title | Dependencies | Status |
|----------|-------|-------|--------------|--------|
| P1 | **11.4** | Streak Protection (Freeze Feature) | 11.1 | 📋 Backlog |
| P2 | **11.5** | Streak Risk Notifications | 11.1 | 📋 Backlog |
| P3 | **11.7** | Gamification Analytics (Admin) | 11.1-11.6 | 📋 Backlog |

---

### Sprint 15: Advanced Analytics
**Goal:** Implement deep analytics for power users.

| Priority | Story | Title | Dependencies | Status |
|----------|-------|-------|--------------|--------|
| P1 | **4.13** | Advanced Performance Analytics | 4.10, 4.5 | 📋 Backlog |

**4.13 Capabilities:**
- Time-based analytics (best study hour/day)
- Question-level analytics (hardest/easiest)
- Improvement velocity tracking
- Comparison analytics (vs. cohort)
- Export reports (PDF/CSV)

---

### Sprint 16: Polish & Launch Readiness (Epic 8)
**Goal:** Final polish, accessibility, and production deployment.

| Priority | Story | Title | Dependencies | Status |
|----------|-------|-------|--------------|--------|
| P1 | **8.1** | Settings/Profile Management | - | 📋 Backlog |
| P2 | **8.2** | Exam Date Management | - | 📋 Backlog |
| P3 | **8.3** | Accessibility Compliance (WCAG 2.1 AA) | All UI | 📋 Backlog |
| P4 | **8.4** | Error Handling & Edge Cases | All | 📋 Backlog |
| P5 | **8.5** | Performance Optimization | All | 📋 Backlog |
| P6 | **8.6** | Production Deployment | All | 📋 Backlog |
| P7 | **8.7** | Admin Tooling | - | 📋 Backlog |

---

## Backlog (Unprioritized / Post-MVP)

| Story | Title | Epic | Notes |
|-------|-------|------|-------|
| 2.11 | Knowledge Graph Visualization Data | 2 | Power-user feature |
| 2.12 | Concept Coverage Validation Script | 2 | CI/CD integration |

---

## Dependency Graph

```
Epic 2 (Content) ─────────────────────────────────────────────────────┐
    │                                                                 │
    ├─ 2.3 Prerequisite Graph ──────────────────┐                     │
    │                                           │                     │
Epic 3 (Diagnostic) ────────────────────────────┼─────────────────────┤
    │                                           │                     │
    ├─ 3.4 Belief Init ─────────────────────────┤                     │
    │                                           │                     │
Epic 4 (Quiz Engine) ───────────────────────────┼─────────────────────┤
    │                                           │                     │
    ├─ 4.4 Belief Update ───────────────────────┤                     │
    │       │                                   │                     │
    │       ├─ 4.5 Coverage Tracking ───────────┼── 4.12 Readiness    │
    │       │       │                           │       │             │
    │       │       └── 6.6 Curriculum Progress─┘       │             │
    │       │                                           │             │
    │       └─ 4.11 Mastery Gates ──────────────────────┘             │
    │               │                                                 │
    │               └── Requires 2.3 ─────────────────────────────────┘
    │
Epic 10 (IRT) ──────────────────────────────────────────────────────────
    │
    ├─ 10.1 DB Migration
    │       │
    │       ├─ 10.2 Import Support
    │       ├─ 10.3 Ability Classification
    │       │       │
    │       │       ├─ 10.4 Difficulty Distribution
    │       │       │       │
    │       │       │       └─ 10.5 Combined BKT-IRT
    │       │       │
    │       └─ 10.6 Schema Updates
    │
Epic 5 (Reading) ───────────────────────────────────────────────────────
    │
    ├─ 5.5 Queue Population (requires 4.3)
    │       │
    │       ├─ 5.6 Badge Updates
    │       ├─ 5.7 Library Page
    │       │       │
    │       │       ├─ 5.8 Detail View
    │       │       │       │
    │       │       │       └─ 5.9 Analytics
    │       │       │
    │       │       └─ 5.10 Bookmarks
    │       │
    │       └─ 5.11 Intervention (requires 4.4)
    │
Epic 7 (Spaced Repetition) ─────────────────────────────────────────────
    │
    ├─ 7.1 Mastery Tracking (requires 4.3)
    │       │
    │       └─ 7.2 SM-2 Scheduling
    │               │
    │               └─ 7.3 Mixed Sessions
    │                       │
    │                       └─ 7.4 Review Tracking
    │                               │
    │                               └─ 7.5 Reviews Due
    │
Epic 6 (Dashboard) ─────────────────────────────────────────────────────
    │
    ├─ 6.1 Overview (requires 4.5)
    │       │
    │       ├─ 6.2 Trends
    │       ├─ 6.3 Countdown (requires 4.12)
    │       ├─ 6.4 KA Detail
    │       └─ 6.5 Recommendations (requires 7.5)
    │
Epic 11 (Gamification) ─────────────────────────────────────────────────
    │
    ├─ 11.1 Streak Tracking (requires 4.3)
    │       │
    │       ├─ 11.2 Visualization (requires 6.1)
    │       ├─ 11.3 Achievements
    │       ├─ 11.4 Freeze
    │       ├─ 11.5 Notifications
    │       └─ 11.6 Goals
    │               │
    │               └─ 11.7 Analytics (requires all)
```

---

## Status Legend

| Icon | Status | Description |
|------|--------|-------------|
| ✅ | Complete | Story implemented and tested |
| 🔄 | In Progress | Currently being worked on |
| 📋 | Ready | Backlog, ready to start |
| 🚫 | Blocked | Waiting on dependency |
| ⏸️ | Paused | Started but paused |

### Pipeline State Icons

| Icon | Pipeline State | Description |
|------|----------------|-------------|
| 📋 | `backlog` | Not yet started |
| 📝 | `drafting` | SM Agent drafting story |
| 🔍 | `validating` | PO Agent validating/amending |
| ⏳ | `awaiting_po_approval` | HITL #1: Waiting for user |
| ✅ | `approved` | User approved, ready for dev |
| 💻 | `implementing` | Dev Agent writing code |
| 🧪 | `qa_review` | QA Agent reviewing |
| ⏳ | `awaiting_qa_approval` | HITL #2: Waiting for user |
| 🔧 | `fixing` | Dev Agent fixing QA issues |
| ⏳ | `awaiting_commit` | HITL #3: Waiting for commit approval |
| ✅ | `complete` | Done and committed |

---

## Pipeline Integration

This backlog integrates with the automated story lifecycle pipeline.

**Pipeline State File:** `.bmad-core/state/pipeline-state.json`
**Pipeline Schema:** `.bmad-core/state/pipeline-state-schema.md`
**Orchestrator Task:** `.bmad-core/tasks/workflow-story-pipeline.md`

### Running the Pipeline

```bash
# Start pipeline for next P1 story in current sprint
/workflow-story-pipeline

# Start pipeline for specific story
/workflow-story-pipeline 4.5

# Resume pipeline at checkpoint
/workflow-story-pipeline --resume

# Check pipeline status
/workflow-story-pipeline --status
```

### HITL Checkpoints

The pipeline pauses at three checkpoints for human approval:

1. **HITL #1 (PO Approval):** After SM drafts and PO validates/amends
2. **HITL #2 (QA Approval):** After QA Agent reviews implementation
3. **HITL #3 (Commit Approval):** Before committing changes

---

## Change Log

| Date | Sprint | Description | Author |
|------|--------|-------------|--------|
| 2025-12-23 | 8 | Added story lifecycle pipeline automation with HITL checkpoints | Winston (Architect) |
| 2025-12-23 | 8 | Initial sprint backlog creation; organized ~45 outstanding stories into 9 sprints | Winston (Architect) |

---

## References

| Document | Path | Purpose |
|----------|------|---------|
| Algorithm Specifications | `docs/prd/algorithm-specifications.md` | Algorithms 1-9 pseudocode |
| Database Schema (BKT) | `docs/prd/database-schema-bkt.md` | All table definitions |
| Epic 4 (Quiz Engine) | `docs/prd/epic-4-bkt.md` | Core adaptive loop stories |
| Epic 10 (IRT) | `docs/prd/epic-10-irt-difficulty-distribution.md` | IRT enhancement stories |
| Epic 11 (Gamification) | `docs/prd/epic-11-gamification-motivation.md` | Engagement system stories |
| Cross-Reference Index | `docs/prd/cross-reference-index.md` | PRD navigation guide |
| Gap Analysis | `docs/prd/gap-analysis-adaptive-learning-vision.md` | Coverage validation |
