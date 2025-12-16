# Epic List

This section presents the high-level epic structure for LearnR MVP implementation. Each epic delivers a significant, end-to-end increment of testable functionality following agile best practices. Epics are sequenced to enable incremental delivery while building toward the complete adaptive learning platform.

### Epic Overview

**Epic 1: Foundation & User Authentication**
**Goal:** Establish project infrastructure, development environment, and secure user authentication system with basic user management capabilities.

Delivers: Working monorepo with CI/CD, PostgreSQL database, user registration/login, password management, and project health-check endpoint demonstrating full-stack integration.

---

**Epic 2: Content Foundation & Question Bank**
**Goal:** Build the content processing pipeline and establish the question bank with embeddings, enabling the platform to serve CBAP questions.

Delivers: 600-1,000 questions loaded with metadata, BABOK v3 parsed and chunked, all content embedded in Qdrant, content retrieval APIs functional and testable.

---

**Epic 3: Diagnostic Assessment & Competency Baseline**
**Goal:** Enable users to complete the 12-question diagnostic assessment and receive accurate baseline competency scores across all 6 CBAP knowledge areas.

Delivers: Anonymous onboarding flow (7 questions), account creation, 12-question diagnostic quiz interface (3 per KA), simplified IRT competency calculation, diagnostic results screen with KA breakdown and gap analysis.

---

**Epic 4: Adaptive Quiz Engine & Explanations**
**Goal:** Implement the core adaptive learning loop with intelligent question selection, answer submission, and detailed explanations.

Delivers: Adaptive quiz sessions with real-time competency updates, difficulty matching, immediate feedback, comprehensive explanations with user feedback capability.

---

**Epic 5: Targeted Reading Content Integration**
**Goal:** Complete the learning loop by adding semantic BABOK content retrieval that addresses user-specific knowledge gaps (critical differentiator).

Delivers: Vector search retrieval of relevant BABOK chunks, reading content display after explanations, reading engagement tracking, validation of differentiation value.

---

**Epic 6: Progress Dashboard & Transparency**
**Goal:** Provide users with comprehensive progress visibility through real-time competency tracking, exam readiness scoring, and actionable recommendations.

Delivers: Dashboard with 6 KA competency bars, exam readiness score, weekly progress trends, KA detail views, days-until-exam countdown, recommended focus areas.

---

**Epic 7: Spaced Repetition & Long-Term Retention**
**Goal:** Implement SM-2 spaced repetition system to ensure users retain learned concepts through exam day.

Delivers: Concept mastery tracking, review scheduling (1/3/7/14 day intervals), mixed quiz sessions (reviews + new content), review performance tracking, reviews-due indicator on dashboard.

---

**Epic 8: Polish, Testing & Launch Readiness**
**Goal:** Complete platform polish, comprehensive testing, performance optimization, and deployment for case study user validation.

Delivers: Settings/profile management, accessibility compliance (WCAG 2.1 AA), error handling, production deployment, alpha test readiness, all acceptance criteria validated.

---

**Epic 9: Multi-Course Platform Architecture**
**Goal:** Transform LearnR from a single-course CBAP application into a multi-course platform capable of supporting multiple certifications (PSM1, CFA Level 1, etc.) while maintaining full backward compatibility.

Delivers: Course and enrollment data model, course-scoped content (concepts, questions, reading), enrollment management API, course catalog, dynamic knowledge areas, migration of existing CBAP users, content import pipeline for new courses.

---

### Epic Sequencing Rationale

**Why This Structure:**

1. **Epic 1** establishes technical foundation (monorepo, database, CI/CD) while delivering initial user capability (authentication) - demonstrates full-stack integration early

2. **Epic 2** loads all content (questions + BABOK) before building features that consume it - enables all subsequent epics to have real data

3. **Epic 3** builds diagnostic first because competency baseline is required for adaptive algorithm (Epic 4) to function

4. **Epic 4** creates core quiz experience before adding reading content (Epic 5) - validates basic adaptive loop works

5. **Epic 5** adds critical differentiator (reading content) mid-sprint to allow Day 24 alpha test validation

6. **Epic 6** provides progress visibility after core learning loop functional - users need quiz capability before progress makes sense

7. **Epic 7** adds spaced repetition after quiz working - review scheduling requires existing question history

8. **Epic 8** focuses on polish and deployment after all features functional - prepares for production launch

9. **Epic 9** adds multi-course capability post-launch - validates BKT engine is course-agnostic before Phase 2 (user-generated content)

**Incremental Value Delivery:**
- After Epic 1: Team can develop and deploy code
- After Epic 2: Content is loaded and queryable
- After Epic 3: Users can take diagnostic and see competency scores
- After Epic 4: Users can study adaptively with explanations
- After Epic 5: **CRITICAL - Alpha test can validate reading differentiation (Day 24 Go/No-Go)**
- After Epic 6: Users have full progress transparency
- After Epic 7: Retention system ensures long-term learning
- After Epic 8: Platform ready for production case study validation
- After Epic 9: **Platform supports multiple certifications - ready for PSM1/CFA expansion**

---
