# LearnR Architecture Pivot: Bayesian Knowledge Tracing

**Presentation Date:** _TBD_
**Prepared By:** Sarah (Product Owner)
**Status:** For Stakeholder Review & Approval

---

## Executive Summary

We propose pivoting LearnR from a traditional quiz application to a **Bayesian Knowledge Tracing (BKT)** system. This architectural change makes our adaptive engine dramatically smarter while keeping the user experience simple and familiar.

### The Opportunity

**What users see (unchanged):**
> "You're 72% ready for CBAP. Strategy Analysis needs focus."
>
> *6 Knowledge Area bars, clear next action, familiar interface*

**What the system knows (new):**
> Tracking 1,203 concepts with probabilistic confidence. Selecting optimal questions. Detecting specific gaps. Never wasting user time on mastered material.

**The result:**
> **50-75% fewer questions** to identify knowledge gaps compared to traditional quiz apps.

### Key Insight

**BKT is system intelligence, not user-facing complexity.**

Users don't need to know we track 1,203 concepts. They just experience:
- Smarter questions that feel relevant
- Faster progress toward exam readiness
- Confidence that the app knows what they need

### Key Decision Required

**Approve the BKT architecture pivot**, which requires:
- Restructuring Epic 2 (Content Foundation) from 7 to 12 stories
- Adding concept extraction as the critical foundation
- Revising the database schema for probabilistic belief tracking

---

## The User Experience: Simple and Familiar

### What Users See

```
┌─────────────────────────────────────────────────────────────────┐
│  DASHBOARD (Unchanged from Original Design)                     │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Exam Readiness: 72%                                    │   │
│  │  ████████████████████░░░░░░░░                           │   │
│  │                                                         │   │
│  │  "Focus on Strategy Analysis to improve your score"     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Knowledge Areas:                                               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                        │
│  │ BAPM     │ │ EC       │ │ RLCM     │                        │
│  │ ████████ │ │ ██████░░ │ │ ████░░░░ │                        │
│  │ 85%      │ │ 72%      │ │ 58%      │                        │
│  └──────────┘ └──────────┘ └──────────┘                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                        │
│  │ SA       │ │ RADD     │ │ SE       │                        │
│  │ ███░░░░░ │ │ ██████░░ │ │ █████░░░ │                        │
│  │ 45%      │ │ 78%      │ │ 65%      │                        │
│  └──────────┘ └──────────┘ └──────────┘                        │
│                                                                 │
│  [Continue Learning]  [Review Weak Areas]                       │
└─────────────────────────────────────────────────────────────────┘
```

**This is the same UI we planned.** Users see 6 Knowledge Areas, a readiness score, and clear next actions. No concept-level complexity exposed.

### What Changes for Users

| Before BKT | After BKT | User Perception |
|------------|-----------|-----------------|
| Random questions from weak KA | Optimal questions targeting specific gaps | "These questions feel really relevant" |
| 50-100 questions to assess | 15-25 questions to assess | "That was fast!" |
| "Study Strategy Analysis" | "Study Strategy Analysis" (same) | No change in messaging |
| Progress feels random | Progress feels consistent | "I can see myself improving" |

**Users don't see the difference. They feel it.**

---

## The System Intelligence: Powerful and Hidden

### What the System Knows

```
┌─────────────────────────────────────────────────────────────────┐
│  SYSTEM VIEW (Hidden from Users)                                │
│                                                                 │
│  User: jane.doe@email.com                                       │
│  Concepts tracked: 1,203                                        │
│                                                                 │
│  Belief State Summary:                                          │
│  ├── Mastered (>80% confidence): 487 concepts                   │
│  ├── Gaps (<50% confidence): 156 concepts                       │
│  └── Uncertain (need more data): 560 concepts                   │
│                                                                 │
│  Strategy Analysis Breakdown (internal):                        │
│  ├── "Stakeholder Identification": 92% mastery, HIGH confidence │
│  ├── "RACI Matrix Construction": 34% mastery, HIGH confidence   │  ← Gap
│  ├── "Business Case Development": 51% mastery, LOW confidence   │  ← Ask next
│  └── ... 184 more concepts                                      │
│                                                                 │
│  Next Question Selection:                                       │
│  → Question #247 (tests "Business Case Development")            │
│  → Expected information gain: 0.73 bits                         │
│  → Why: Highest uncertainty reduction among available questions │
└─────────────────────────────────────────────────────────────────┘
```

### The Two-Layer Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     USER LAYER                                  │
│         Simple • Familiar • 6 Knowledge Areas                   │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │  "You're 72% ready. Strategy Analysis needs work."      │   │
│   │  [6 KA bars] [Progress trends] [Next action button]     │   │
│   └─────────────────────────────────────────────────────────┘   │
│                            ▲                                    │
│                            │ Aggregated to KA level             │
│                            │                                    │
├─────────────────────────────────────────────────────────────────┤
│                   INTELLIGENCE LAYER                            │
│         Powerful • Hidden • 1,203 Concepts                      │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │  BKT Engine                                             │   │
│   │  ├── Track 1,203 concepts with Beta distributions       │   │
│   │  ├── Select questions for maximum information gain      │   │
│   │  ├── Detect gaps at concept level                       │   │
│   │  ├── Respect prerequisite relationships                 │   │
│   │  └── Stop when confident (not when count reached)       │   │
│   └─────────────────────────────────────────────────────────┘   │
│                            ▲                                    │
│                            │ Granular tracking                  │
│                            │                                    │
├─────────────────────────────────────────────────────────────────┤
│                    CONTENT LAYER                                │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │  Questions → Concepts → Knowledge Areas                 │   │
│   │  BABOK Chunks → Concepts → Knowledge Areas              │   │
│   │  Prerequisite Graph (Concepts → Concepts)               │   │
│   └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Why This Pivot?

### The Problem with Traditional Quiz Apps

| What They Do | Why It's Inefficient |
|--------------|---------------------|
| Ask random questions | Wastes time on mastered material |
| Track 6 categories | Can't identify specific gaps |
| Fixed question counts | Stops too early or too late |
| "You scored 72%" | Not actionable - what should I study? |

### What BKT Enables

| Capability | How It Works | User Benefit |
|------------|--------------|--------------|
| **Optimal question selection** | Pick questions that maximize learning per minute | Faster progress |
| **Specific gap detection** | Know "RACI Matrix" is weak, not just "Strategy Analysis" | Better content recommendations |
| **Confidence-based stopping** | Stop diagnostic when confident, not at fixed count | Respect user's time |
| **Prerequisite awareness** | Don't test advanced concepts before foundations | Less frustration |

### The Efficiency Gain

```
Traditional App:                    LearnR with BKT:

Question 1  → Random               Question 1  → Max uncertainty concept
Question 2  → Random               Question 2  → Max uncertainty concept
Question 3  → Random               Question 3  → Max uncertainty concept
...                                ...
Question 50 → Still uncertain      Question 18 → Confident on 90% of corpus
                                   STOP - diagnostic complete
```

**Result: 50-75% fewer questions to map knowledge state.**

---

## What is Bayesian Knowledge Tracing?

### The Core Idea (Technical Summary)

For each concept, we track a **probability distribution** (not a point score):

```
Traditional: "User knows 72% of Strategy Analysis"
     ↓
BKT: "User has P(mastery)=0.72 for 'Stakeholder ID' with confidence 0.85,
      P(mastery)=0.34 for 'RACI Matrix' with confidence 0.90,
      P(mastery)=0.51 for 'Business Case' with confidence 0.40..."
```

The confidence measure tells us **when to keep asking** vs **when we know enough**.

### Why It Matters

| Scenario | Traditional App | BKT |
|----------|-----------------|-----|
| User answers 2 questions correctly | "Good job!" (no state change) | Updates belief: likely mastered this concept |
| User answers 1 wrong after 5 correct | "Oops!" (score drops) | Updates belief: probably a slip, still likely mastered |
| User guesses correctly on hard question | Score increases (false positive) | Belief increases slightly (accounts for guessing) |

BKT handles **noise** (slips, guesses) mathematically, producing more accurate assessments.

---

## Architecture Changes

### Data Model

| Component | Original | BKT |
|-----------|----------|-----|
| **Knowledge tracking** | `competency_tracking` (6 rows/user) | `belief_states` (1,203 rows/user) |
| **Knowledge unit** | Knowledge Area | Concept (aggregated to KA for display) |
| **State representation** | `score` (0-100) | `alpha`, `beta` (Beta distribution) |
| **Question mapping** | Question → KA | Question → Concepts (1-5) → KA |

### New Database Tables

```sql
concepts (1,203 rows)           -- Extracted from BABOK
concept_prerequisites           -- Learning path DAG
belief_states                   -- Per-user, per-concept probability
question_concepts               -- Which concepts each question tests
```

### What Stays the Same

- User table structure
- Knowledge Areas table (used for aggregation/display)
- Quiz session flow
- Frontend dashboard design
- 6 KA progress bars

---

## Epic 2 Scope Impact

### Original Epic 2 (7 Stories)

| Story | Title | Status |
|-------|-------|--------|
| 2.1 | Qdrant Setup | Complete |
| 2.2 | Vendor Question Import | Complete |
| 2.3 | Question Embedding | In Progress |
| 2.4 | BABOK Parsing | Planned |
| 2.5 | BABOK Embedding | Planned |
| 2.6 | Questions API | Planned |
| 2.7 | Reading API | Planned |

### BKT Epic 2 (12 Stories)

| Story | Title | Change | Priority |
|-------|-------|--------|----------|
| 2.1 | Qdrant Setup | Unchanged | Complete |
| **2.2** | **BABOK Concept Extraction** | **NEW** | **Critical Path** |
| **2.3** | **Concept Prerequisite Graph** | **NEW** | **Critical Path** |
| 2.4 | Question Import + Concept Mapping | Revised | Critical Path |
| 2.5 | Question Embedding + Concepts | Revised | Required |
| 2.6 | BABOK Parsing + Concept Links | Revised | Required |
| 2.7 | BABOK Embedding + Concepts | Revised | Required |
| 2.8 | Questions API by Concept | Revised | Required |
| 2.9 | Reading API by Concept | New | Required |
| 2.10 | Concept API Endpoints | New | Internal tooling |
| 2.11 | Knowledge Graph Visualization | New | **Post-MVP** |
| 2.12 | Concept Coverage Validation | New | QA tooling |

### Priority Clarification: Story 2.11

**Knowledge Graph Visualization is NOT required for MVP.**

- Users see KA-level progress (6 bars) - no change
- Concept-level visualization is a power-user feature
- Move to post-MVP or make optional

**Revised effort with 2.11 deferred: ~12-15 days additional** (down from 15-21)

---

## Effort Estimate

### Critical Path (Must Have)

| Story | Effort | Notes |
|-------|--------|-------|
| 2.2 Concept Extraction | 3-5 days | GPT-4 + human review |
| 2.3 Prerequisite Graph | 2-3 days | Graph algorithms |
| 2.4 Question-Concept Mapping | 1-2 days | Extend existing |

**Critical path: ~6-10 days**

### Required Support

| Story | Effort |
|-------|--------|
| 2.5-2.8 revisions | 3-4 days |
| 2.9 Reading API | 1 day |
| 2.10 Concept API | 1 day |
| 2.12 Validation | 1 day |

**Support work: ~6-7 days**

### Rework

| Item | Effort |
|------|--------|
| Revise completed 2.2 | 1-2 days |
| Schema migration | 0.5 days |

**Rework: ~2-3 days**

### Total

**~14-20 additional development days** (with 2.11 deferred to post-MVP)

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Concept extraction quality | Medium | High | SME review checkpoint |
| Too many/few concepts | Medium | Medium | Target range (500-1500), validation |
| User confusion about progress | Low | Medium | **Keep UI unchanged - KA level only** |
| Timeline extension | High | Medium | Defer 2.11, phase approach |

---

## Benefits Summary

### For Users (What They Experience)

| Benefit | How It Feels |
|---------|--------------|
| Smarter questions | "This app knows exactly what I need to work on" |
| Faster assessments | "The diagnostic was quick but thorough" |
| Relevant content | "The reading suggestions are always spot-on" |
| Steady progress | "I can see myself improving every week" |

### For the Business (What We Gain)

| Benefit | Impact |
|---------|--------|
| Differentiation | "Our adaptive engine is smarter" - defensible advantage |
| Efficiency claims | "50-75% fewer questions" - marketing message |
| Foundation for advanced features | Prerequisite paths, personalized curricula |
| Data quality | Per-concept analytics for content improvement |

### What We Don't Expose

| Internal Capability | Why Not User-Facing |
|--------------------|---------------------|
| 1,203 concepts | Overwhelming - users think in 6 KAs |
| Beta distributions | Technical - users want simple percentages |
| Information gain | Confusing - users want "next question" |
| Prerequisite graph | Complex - just serve the right questions |

---

## Decision Points

### Decision 1: Architecture Approval

**Do we approve the BKT architecture pivot?**

| Option | Recommendation |
|--------|---------------|
| **Approve** | Proceed with concept-level tracking (hidden from users) |
| Reject | Continue with KA-level tracking only |

### Decision 2: Story Renumbering

**How do we handle the 2.2 conflict?**

| Option | Recommendation |
|--------|---------------|
| **Renumber original 2.2 → 2.4** | Aligns with BKT epic |

### Decision 3: Knowledge Graph Visualization (2.11)

**When do we build the concept visualization?**

| Option | Recommendation |
|--------|---------------|
| **Defer to post-MVP** | Users don't need it; focus on core BKT |
| Include in MVP | Nice-to-have, not essential |

### Decision 4: Timeline

**How do we handle the ~14-20 day extension?**

| Option | Recommendation |
|--------|---------------|
| **Phased approach** | Core BKT in MVP, visualization later |

---

## Recommended Approach

### MVP (Core BKT)

1. Concept extraction (2.2) - **Critical**
2. Prerequisite graph (2.3) - **Critical**
3. Question-concept mapping (2.4) - **Critical**
4. Revised content pipeline (2.5-2.8)
5. Concept APIs (2.9-2.10) - Internal use
6. Validation tooling (2.12) - QA

**User-facing: No change to dashboard. Same 6 KA bars.**

### Post-MVP (Enhanced)

1. Knowledge graph visualization (2.11) - Power users only
2. "Why this question?" explanations - Optional feature
3. Concept-level drill-down - Settings toggle

---

## Next Steps (If Approved)

| Step | Owner | Timeline |
|------|-------|----------|
| 1. Approve BKT architecture | Stakeholders | This meeting |
| 2. Renumber stories (2.2 → 2.4) | Scrum Master | Day 1 |
| 3. Defer Story 2.11 to post-MVP | Product Owner | Day 1 |
| 4. Begin 2.2 implementation | Dev Team | Day 2 |
| 5. SME review of concepts | Subject Matter Expert | Week 2 |

---

## Summary

**BKT makes LearnR smarter without making it more complex for users.**

| Aspect | What Changes | What Stays the Same |
|--------|--------------|---------------------|
| System | Tracks 1,203 concepts | - |
| System | Selects optimal questions | - |
| System | Detects specific gaps | - |
| User | - | Sees 6 Knowledge Areas |
| User | - | Sees simple percentages |
| User | - | Gets clear next actions |
| User | Experiences faster progress | - |
| User | Feels questions are more relevant | - |

**The intelligence is invisible. The benefits are obvious.**

---

## Appendix: Technical References

| Document | Location |
|----------|----------|
| BKT Architecture | `docs/architecture/bkt-architecture.md` |
| BKT Database Schema | `docs/prd/database-schema-bkt.md` |
| BKT Epic 2 | `docs/prd/epic-2-bkt.md` |
| Story 2.2 (Concepts) | `docs/stories/2.2.babok-concept-extraction.md` |

---

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-11-27 | 2.0 | Major revision: Reframed BKT as system intelligence (hidden from users); Clarified UI stays unchanged (6 KAs); Deferred Story 2.11 to post-MVP; Updated effort estimates; Added two-layer architecture diagram | Sarah (Product Owner) |
| 2025-11-27 | 1.0 | Initial stakeholder presentation | Sarah (Product Owner) |
