# Goals and Background Context

### Goals

The LearnR PRD aims to deliver the following desired outcomes:

- **Proven Learning Effectiveness**: Achieve 80%+ first-time pass rate for CBAP certification (vs. 60% industry average) through adaptive learning
- **Time Efficiency**: Reduce total study time by 30% (60-85 hours vs. 90-120 hours traditional methods) via intelligent content targeting
- **Complete Learning System**: Deliver integrated diagnostic → adaptive quiz → explanations → targeted reading → spaced repetition loop
- **Validated Differentiation**: Prove reading content feature provides measurable value (alpha test Day 24 validation)
- **Scalable Platform Foundation**: Establish architecture supporting multi-certification expansion (PSM1, CFA Level 1) within 6 months
- **User Confidence & Retention**: Maintain 80%+ daily engagement and 70%+ completion rates through exam day
- **Business Sustainability**: Create validated MVP ready for beta launch (Q1 2026) with clear path to profitability

### Background Context

Working professionals preparing for high-stakes certifications like CBAP face three compounding challenges: they don't know where to focus limited study time, existing tools (static quiz banks) don't adapt to individual gaps, and forgetting curves erode early learning without systematic review.

LearnR addresses this gap by combining AI-powered competency assessment, adaptive difficulty matching, immediate explanations, targeted BABOK v3 reading content, and spaced repetition into a complete learning system. Unlike competitors (Pocket Prep, Quizlet, expensive bootcamps), LearnR provides both testing AND teaching in one intelligent, personalized experience.

This PRD builds upon comprehensive project planning documented in the Project Brief (docs/brief.md) and 200+ strategic decisions (docs/note.md), including critical decisions to include reading content (Decision #23) and spaced repetition (Decision #31) in MVP scope. The platform targets career-advancing professionals (ages 30-45) who need efficient, self-paced preparation with transparent progress tracking.

Validation approach: 30-day MVP development → 30-day case study validation (exam Dec 21, 2025) → Go/No-Go decision (Day 24 alpha test validates reading content value) → Beta launch Q1 2026.

### Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-11-17 | 1.0 | Initial PRD created with comprehensive functional and non-functional requirements | Developer |
| 2025-11-19 | 2.0 | Enhanced with Goals/Background, UI Design Goals, Technical Assumptions restructure, Epic List, User Stories with Acceptance Criteria, PM Checklist validation, and Next Steps prompts per B-MAD template | Developer |
| 2025-11-19 | 2.1 | **MAJOR UPDATE:** Added Post-Session Review feature for immediate reinforcement and Asynchronous Reading Library for zero-interruption learning flow. Approved design decisions #84-87. Complete technical specifications in Implementation_Summary.md | Developer |
| 2025-11-19 | 2.2 | Added MVP admin support tools: FR18 (Admin Operations and Support Tools), Story 8.7 (User Impersonation, User Search, PostHog Integration, Admin Audit Trail), PostHog analytics integration, admin-specific security requirements, admin_audit_log table, and users.is_admin column | Analyst Agent |

---
