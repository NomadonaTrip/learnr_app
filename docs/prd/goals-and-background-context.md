# Goals and Background Context

### Goals

The LearnR PRD aims to deliver the following desired outcomes:

- **Proven Learning Effectiveness**: Achieve 80%+ first-time pass rate for CBAP certification (vs. 60% industry average) through adaptive learning
- **Time Efficiency**: Reduce total study time by 30% (60-85 hours vs. 90-120 hours traditional methods) via intelligent content targeting
- **Complete Learning System**: Deliver integrated diagnostic → adaptive quiz → explanations → targeted reading → spaced repetition loop
- **Validated Differentiation**: Prove reading content feature provides measurable value (alpha test Day 24 validation)
- **Scalable Platform Foundation**: Establish architecture supporting multi-certification expansion (PSM1, CFA Level 1) within 6 months
- **User Confidence & Retention**: Maintain 80%+ daily engagement and 70%+ completion rates through exam day
- **Trainer Visibility & Institutional Adoption**: Provide trainers with multi-level analytics (organization, class, individual) to identify at-risk students and target interventions, enabling B2B/institutional sales
- **Business Sustainability**: Create validated MVP ready for beta launch (Q1 2026) with clear path to profitability through both B2C (individual learners) and B2B (institutional licensing) channels

### Background Context

Working professionals preparing for high-stakes certifications like CBAP face three compounding challenges: they don't know where to focus limited study time, existing tools (static quiz banks) don't adapt to individual gaps, and forgetting curves erode early learning without systematic review.

**Customer discovery (March 2026) revealed a critical insight:** while individual learners benefit from LearnR's adaptive engine, the stronger market pull comes from **trainers and instructors** who lack visibility into student performance. Training organizations, boot camps, and corporate L&D teams need to see which students are struggling and where — at the school, class, and individual level — so they can intervene before students fall behind. This shifts the go-to-market from pure B2C to a **B2B2C model** where trainers are the buying decision-makers and students are the end users.

LearnR addresses both sides by combining AI-powered competency assessment, adaptive difficulty matching, immediate explanations, targeted BABOK v3 reading content, and spaced repetition into a complete learning system for students, **plus** a multi-level analytics dashboard for trainers. Unlike competitors (Pocket Prep, Quizlet, expensive bootcamps), LearnR provides both testing AND teaching in one intelligent, personalized experience — with institutional-grade visibility for the people responsible for student outcomes.

This PRD builds upon comprehensive project planning documented in the Project Brief (docs/brief.md) and 200+ strategic decisions (docs/note.md), including critical decisions to include reading content (Decision #23) and spaced repetition (Decision #31) in MVP scope. The platform targets career-advancing professionals (ages 30-45) who need efficient, self-paced preparation with transparent progress tracking, **and training organizations who need actionable student performance analytics**.

Validation approach: 30-day MVP development → 30-day case study validation (exam Dec 21, 2025) → Go/No-Go decision (Day 24 alpha test validates reading content value) → Beta launch Q1 2026 → Trainer pilot Q2 2026.

### Target User Personas

#### Persona 1: The Learner (Existing)
- **Profile:** Working professional, ages 30-45, preparing for certification exam
- **Pain:** Limited study time, doesn't know where to focus, forgets what they studied
- **Need:** Efficient, adaptive study tool that targets their specific gaps
- **Success:** Passes certification exam on first attempt

#### Persona 2: The Trainer (NEW - v3.0)
- **Profile:** Instructor, training coordinator, or L&D manager responsible for student outcomes
- **Pain:** No visibility into which students are struggling or which concepts need classroom reinforcement
- **Need:** Multi-level dashboard showing student performance at organization, class, and individual levels
- **Success:** Can identify at-risk students within 1 week of enrollment and intervene effectively
- **Key Workflows:**
  - Morning check: Review class dashboard for overnight study activity and at-risk alerts
  - Class prep: Identify weakest concepts across the class to inform lesson planning
  - Student intervention: Drill into individual student profiles to understand specific gaps
  - Reporting: Generate progress reports for stakeholders, parents, or institutional compliance

### Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-11-17 | 1.0 | Initial PRD created with comprehensive functional and non-functional requirements | Developer |
| 2025-11-19 | 2.0 | Enhanced with Goals/Background, UI Design Goals, Technical Assumptions restructure, Epic List, User Stories with Acceptance Criteria, PM Checklist validation, and Next Steps prompts per B-MAD template | Developer |
| 2025-11-19 | 2.1 | **MAJOR UPDATE:** Added Post-Session Review feature for immediate reinforcement and Asynchronous Reading Library for zero-interruption learning flow. Approved design decisions #84-87. Complete technical specifications in Implementation_Summary.md | Developer |
| 2025-11-19 | 2.2 | Added MVP admin support tools: FR18 (Admin Operations and Support Tools), Story 8.7 (User Impersonation, User Search, PostHog Integration, Admin Audit Trail), PostHog analytics integration, admin-specific security requirements, admin_audit_log table, and users.is_admin column | Analyst Agent |

---
