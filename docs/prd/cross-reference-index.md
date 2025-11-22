# Cross-Reference Index

**🎉 This PRD is now FULLY SELF-CONTAINED for critical specifications.**

All essential implementation details are included directly in this document:
- ✅ **Complete database schemas** (SQL DDL with all tables, indexes, constraints)
- ✅ **Complete algorithm pseudocode** (6 core algorithms with detailed logic)
- ✅ **Complete design system tokens** (colors, typography, spacing, CSS variables)
- ✅ **API versioning strategy** (v1 prefix, deprecation protocol)
- ✅ **Success metrics with baselines** (v2.0 → v2.1 improvement targets)

Supporting documents provide **supplementary details** for specific areas. Use this index to find additional context where needed.

### What's Self-Contained in This PRD

| Specification | PRD Section | Status |
|---------------|-------------|--------|
| **Database Schemas** | Database Schema Summary (15 tables with SQL) | ✅ Complete |
| **Core Algorithms** | Algorithm Specifications (6 algorithms with pseudocode) | ✅ Complete |
| **Design Tokens** | UI Design Goals → Design System Tokens | ✅ Complete |
| **Color Palettes** | Light mode (17 colors) + Dark mode (12 colors) with hex codes | ✅ Complete |
| **Typography Scale** | 8-level system (H1 → Caption) with weights and line heights | ✅ Complete |
| **Spacing System** | 7-level system (xs → 3xl) with rem values | ✅ Complete |
| **API Versioning** | Technical Assumptions → API Versioning Strategy | ✅ Complete |
| **Success Metrics** | Success Criteria → v2.1 Feature Validation table | ✅ Complete |

### Supplementary Documentation (Optional Reference)

These documents provide additional context but are NOT required for implementation:

| Supplementary Detail | Document | Purpose |
|----------------------|----------|---------|
| **Component Library** | `docs/front-end-spec.md` Lines 1273-2074 | 13 pre-designed component specifications with variants |
| **Screen Wireframes** | `docs/front-end-spec.md` Lines 328-1076 | ASCII wireframes for 10+ screens |
| **User Flow Diagrams** | `docs/user-flows.md` Flows 4, 4b, 9 | Mermaid diagrams of user journeys |
| **Accessibility Details** | `docs/front-end-spec.md` Lines 2349-2440 | WCAG 2.1 AA implementation checklist |
| **Animation Details** | `docs/front-end-spec.md` Lines 2541-2643 | 8 animation patterns with timing/easing |
| **Loading & Error States** | `docs/front-end-spec.md` Lines 1077-1174 | 8 loading patterns, 8 error scenarios |
| **Filter UI Designs** | `docs/front-end-spec.md` Lines 787-872 | Reading Library filter layouts (desktop/tablet/mobile) |
| **Post-Session Review Flowcharts** | `docs/Learning_Loop_Refinement.md` | Phase-by-phase specification with detailed diagrams |
| **ERD Diagrams** | `docs/TDDoc_DatabaseSchema.md` | Entity relationship diagrams (visual representation of schemas already in PRD) |

### Key API Endpoint References

All API endpoints use `/v1/` prefix. Complete specifications in Epic story acceptance criteria.

| Endpoint Category | Example Endpoints | PRD Location |
|-------------------|-------------------|--------------|
| **Authentication** | POST /v1/auth/login, /v1/auth/register | Epic 1 Stories 1.1-1.3 |
| **Quiz** | POST /v1/quiz/answer, GET /v1/quiz/session/{id} | Epic 4 Stories 4.1-4.5 |
| **Reading Queue** | GET /v1/reading/queue, POST /v1/reading/queue/batch-dismiss | Epic 5 Stories 5.7-5.8 |
| **Reading Stats** | GET /v1/reading/stats | Epic 5 Story 5.9 |
| **User Profile** | GET /v1/user/profile, PUT /v1/user/profile | Epic 8 Story 8.1 |
| **Admin** | GET /v1/admin/users/search, POST /v1/admin/impersonate/{id} | Epic 8 Story 8.7 |

### Development Workflow (Self-Contained PRD)

**For Software Architects:**
1. **This PRD is sufficient** - All critical specifications (schemas, algorithms, design tokens) included
2. Read PRD sections:
   - Database Schema Summary → Complete SQL DDL for all 15 tables
   - Algorithm Specifications → 6 core algorithms with full pseudocode
   - Technical Assumptions → Architecture, API versioning, deployment
3. **Optional:** Reference `docs/front-end-spec.md` for screen wireframes and component library details

**For Backend Developers:**
1. **This PRD is sufficient** - No external documents required
2. Read PRD sections:
   - Database Schema Summary → All tables, indexes, constraints
   - Algorithm Specifications → Implementation-ready pseudocode
   - Epic Stories → Feature requirements and API endpoints
   - Technical Assumptions → Architecture decisions
3. **Optional:** Reference `docs/Learning_Loop_Refinement.md` for post-session review flowcharts

**For Frontend Developers:**
1. **This PRD is sufficient for core implementation**
2. Read PRD sections:
   - UI Design Goals → Design System Tokens (complete color/typography/spacing specs)
   - Epic Stories → Feature requirements and acceptance criteria
   - Dark Mode Typography Specifications → Enhanced readability guidelines
3. **Optional:** Reference `docs/front-end-spec.md` for:
   - Pre-designed component library (13 components)
   - Screen wireframes (10+ ASCII layouts)
   - Detailed accessibility checklist

### Document Versioning

| Document | Version | Last Updated | Status |
|----------|---------|--------------|--------|
| `docs/prd.md` | 2.2 | 2025-11-19 | **Authoritative** - Single source of truth |
| `docs/Asynchronous_Reading_Model.md` | 2.1.0 | 2025-11-19 | Specification - Referenced by PRD |
| `docs/front-end-spec.md` | 1.0 | 2025-11-19 | Specification - Referenced by PRD |
| `docs/Implementation_Summary.md` | - | 2025-11-19 | Master guide - Referenced by PRD |
| `docs/Learning_Loop_Refinement.md` | - | 2025-11-19 | Specification - Referenced by PRD |

**Maintenance Protocol:**
- **PRD is the single source of truth** - All critical implementation specifications included directly
- Supporting documents provide supplementary context (wireframes, flowcharts, ERDs)
- When conflicts arise: **PRD takes precedence** - supporting docs are supplementary only
- Updates: Modify PRD first, then optionally update supporting docs for consistency

---
