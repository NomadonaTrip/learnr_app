# Phase 2 Backlog: User-Generated Content & Platform Expansion

This document captures features deferred from MVP to Phase 2, which focuses on enabling user-generated courses and advanced platform capabilities.

**Phase 2 Strategic Goal:** Transform LearnR from a curated content platform into a user-generated content platform where instructors and organizations can create custom certification courses.

---

## Deferred Features

### 1. Concept Knowledge Graph Visualization

**Original Request:** Make the concept knowledge graphs visible/accessible to users.

**Deferred From:** Epic 6 (Progress Dashboard & Transparency)

**Rationale for Deferral:**
- Story 6.4 (KA Detail Drill-Down) already provides concept gap visibility per Knowledge Area
- For learners, viewing the raw graph structure adds cognitive load without clear actionability
- 500-1500 concepts is overwhelming in a list view without strong use case
- The knowledge graph primarily powers internal question selection, not user-facing navigation

**Why Relevant in Phase 2:**
When users can create their own courses, they need to:
- Define concepts for their course
- Establish prerequisite relationships between concepts
- Visualize the concept graph structure they're building
- Validate graph integrity (no cycles, proper coverage)

**Phase 2 Implementation Scope:**

#### Story: Concept Graph Editor (Course Creator View)

**As a** course creator building a custom certification course,
**I want** to view and edit the concept knowledge graph for my course,
**so that** I can define learning prerequisites and ensure proper content sequencing.

**Acceptance Criteria:**
1. Course creator dashboard includes "Manage Concepts" section
2. List view of all concepts with:
   - Concept name, description, knowledge area assignment
   - Prerequisite count (inbound) and dependent count (outbound)
   - Difficulty estimate, linked question count
3. Add/Edit/Delete concept functionality
4. Prerequisite relationship editor:
   - Add/remove prerequisites for a concept
   - Set relationship strength (required/helpful/related)
   - Visual warning if creating cycles
5. Bulk import concepts from CSV/Excel
6. Graph validation: Check for cycles, orphan concepts, unreachable concepts
7. Optional: Visual graph view (interactive node-link diagram)

**Estimated Complexity:** High (new CRUD functionality, graph editing, validation)

**Dependencies:**
- Phase 2 course creation infrastructure
- User roles (course creator vs learner)
- Content management system

---

#### Story: Concept Progress View (Learner View - Optional)

**As a** learner studying a course,
**I want** to optionally view my mastery across all concepts,
**so that** I can see a holistic view of my learning progress.

**Acceptance Criteria:**
1. Optional "View All Concepts" link from KA detail pages
2. Read-only list view grouped by Knowledge Area
3. Mastery status badges (Mastered/Gap/Uncertain)
4. Filtering by status and KA
5. Search by concept name
6. Link back to KA detail for actionable next steps

**Estimated Complexity:** Medium (frontend-focused, API exists)

**Dependencies:**
- Story 6.4 complete (KA detail drill-down)
- User preference setting to enable/disable

**Note:** Only implement if alpha test feedback indicates demand. Story 6.4 may be sufficient for most learners.

---

### 2. Other Phase 2 Deferred Items

*Consolidated from epic documents:*

| Feature | Source | Notes |
|---------|--------|-------|
| Full 3-parameter IRT | Epic 3 | MVP uses simplified competency deltas |
| A/B testing framework | Epic 6.5 | Track recommendation engagement |
| Review interval auto-adjustment | Epic 7 | Adjust SM-2 based on accuracy patterns |
| Email reminders for reviews | Epic 7 | Daily email if reviews due >3 |
| Course marketplace | Epic 9 | Purchasing/licensing courses |
| Course sharing | Epic 9 | Users sharing custom courses |
| Course templates | Epic 9 | Creating courses from templates |
| Cross-course analytics | Epic 9 | Comparing progress across courses |
| Course recommendations | Epic 9 | Suggesting courses based on interests |

---

## Phase 2 Planning Notes

**Prerequisites for Phase 2:**
1. MVP launch and alpha validation complete
2. Multi-course architecture (Epic 9) validated with 2+ courses
3. User feedback collected on gap visibility needs
4. Course creator user role and permissions defined

**Open Questions:**
- Will course creators use LearnR's UI or import from external tools?
- What level of graph visualization is needed (list vs. interactive diagram)?
- Should learners ever see prerequisite relationships, or keep them internal?

---

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-12-14 | 1.0 | Initial Phase 2 backlog with concept graph visualization | Sarah (Product Owner) |
