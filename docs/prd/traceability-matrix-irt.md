# Traceability Matrix: IRT Difficulty Distribution (Epic 10)

This document provides full traceability from business requirements through implementation for the IRT Difficulty Distribution feature.

---

## 1. Requirements to Epic/Story Mapping

| Requirement ID | Requirement Description | Epic | Story | Status |
|----------------|------------------------|------|-------|--------|
| FR5B.1 | Two-layer adaptive selection (BKT + IRT) | Epic 10 | 10.5 | Planned |
| FR5B.2 | User ability classification (novice/intermediate/expert) | Epic 10 | 10.3 | Planned |
| FR5B.3 | Classification based on mastery + tier performance | Epic 10 | 10.3 | Planned |
| FR5B.4 | Probabilistic difficulty distribution by ability | Epic 10 | 10.4 | Planned |
| FR5B.5 | IRT b-parameter scale (-3.0 to +3.0) | Epic 10 | 10.1 | Planned |
| FR5B.6 | Difficulty tier definitions | Epic 10 | 10.1, 10.4 | Planned |
| FR5B.7 | Fallback to adjacent tier | Epic 10 | 10.4 | Planned |
| FR5B.8 | Logging of ability/tier selection | Epic 10 | 10.5 | Planned |
| FR5B.9 | <10ms additional latency | Epic 10 | 10.4, 10.5 | Planned |
| FR5B.10 | Feature flag for A/B testing | Epic 10 | 10.5 | Planned |

---

## 2. Story to Algorithm Mapping

| Story | Algorithm | Algorithm Description | Specification Location |
|-------|-----------|----------------------|------------------------|
| 10.3 | Algorithm 7 | User Ability Classification per Concept | `algorithm-specifications.md` lines 418-599 |
| 10.4 | Algorithm 8 | IRT Difficulty Distribution Selection | `algorithm-specifications.md` lines 601-895 |
| 10.5 | Algorithm 9 | Combined BKT-IRT Question Selection | `algorithm-specifications.md` lines 908-950+ |

---

## 3. Story to Database Schema Mapping

| Story | Table | Column(s) | Change Type |
|-------|-------|-----------|-------------|
| 10.1 | `questions` | `difficulty` | Constraint change: 0.0-1.0 → -3.0-3.0 |
| 10.1 | `questions` | `difficulty_label` | New column (VARCHAR(10)) |
| 10.1 | `questions` | `difficulty` default | Change: 0.5 → 0.0 |
| 10.1 | N/A | N/A | Update `database-schema-bkt.md` documentation |

**Migration File:** `q7l8m9n0o1p2_migrate_difficulty_to_irt_scale.py`

---

## 4. Story to API Schema Mapping

| Story | Schema | Field(s) | Change |
|-------|--------|----------|--------|
| 10.6 | `QuestionBase` | `difficulty` | ge=-3.0, le=3.0 |
| 10.6 | `QuestionBase` | `difficulty_label` | New field (optional) |
| 10.6 | `QuestionUpdate` | `difficulty` | ge=-3.0, le=3.0 |
| 10.6 | `QuestionUpdate` | `difficulty_label` | New field (optional) |
| 10.6 | `QuestionResponse` | `difficulty_label` | New field |
| 10.6 | `QuestionListParams` | `difficulty_min/max` | Range: -3.0 to 3.0 |
| 10.6 | `QuestionListParams` | `difficulty_tier` | New field (easy/medium/hard) |
| 10.6 | `QuestionImport` | `get_difficulty_float()` | Returns IRT scale |
| 10.6 | `QuestionImport` | `get_difficulty_label()` | New method |

**File:** `apps/api/src/schemas/question.py`

---

## 5. Story to Service/Code Mapping

| Story | Service/File | Function/Class | Description |
|-------|--------------|----------------|-------------|
| 10.3 | `question_selector.py` | `get_difficulty_performance()` | Query tier performance |
| 10.3 | `question_selector.py` | `classify_user_ability()` | Classify as novice/intermediate/expert |
| 10.3 | `question_selector.py` | `DifficultyPerformance` | Dataclass for tier stats |
| 10.4 | `question_selector.py` | `select_difficulty_tier()` | Probabilistic tier selection |
| 10.4 | `question_selector.py` | `get_questions_in_tier()` | Filter by IRT tier |
| 10.4 | `question_selector.py` | `_fallback_tier_selection()` | Handle empty tier |
| 10.4 | `question_selector.py` | `select_question_by_irt()` | Full IRT selection |
| 10.5 | `question_selector.py` | `select_next_question_adaptive()` | Combined BKT-IRT |
| 10.2 | `import_vendor_questions.py` | `DIFFICULTY_MAP` | Updated to IRT values |
| 10.2 | `import_vendor_questions.py` | `QuestionData` | Added IRT fields |

---

## 6. Story to Test Mapping

| Story | Test Type | Test File | Test Coverage |
|-------|-----------|-----------|---------------|
| 10.1 | Migration | `alembic/test_migrations.py` | Verify data conversion |
| 10.3 | Unit | `test_question_selector.py` | `test_classify_user_ability_*` |
| 10.3 | Unit | `test_question_selector.py` | `test_get_difficulty_performance_*` |
| 10.4 | Unit | `test_question_selector.py` | `test_select_difficulty_tier_*` |
| 10.4 | Unit | `test_question_selector.py` | `test_get_questions_in_tier_*` |
| 10.4 | Unit | `test_question_selector.py` | `test_fallback_tier_selection_*` |
| 10.5 | Integration | `test_question_selection.py` | `test_adaptive_selection_with_irt` |
| 10.5 | Integration | `test_question_selection.py` | `test_irt_disabled_fallback` |
| 10.2 | Unit | `test_import_questions.py` | `test_irt_column_import` |
| 10.6 | Unit | `test_schemas.py` | `test_question_irt_validation` |

---

## 7. Story to Architecture Decision Mapping

| Story | ADR | Decision |
|-------|-----|----------|
| 10.1 | ADR-002 | IRT Difficulty Scale Migration |
| 10.4 | ADR-002 | Difficulty tier boundaries |
| 10.5 | ADR-002 | Combined BKT-IRT architecture |

**ADR Location:** `docs/architecture/adr-002-irt-difficulty-scale.md`

---

## 8. Cross-Epic Dependencies

### Epic 10 Depends On:

| Dependency | Epic | Story | Reason |
|------------|------|-------|--------|
| Questions with difficulty values | Epic 2 | 2.4 | Questions must exist |
| Belief states exist | Epic 3 | 3.4 | BKT mastery probability needed |
| Question selector service | Epic 4 | 4.2 | Extends existing selection |
| Quiz session infrastructure | Epic 4 | 4.1 | Session context for selection |
| User familiarity from onboarding | Epic 3 | 3.2 | Bootstraps initial ability |

### Stories Depending on Epic 10:

| Story | Epic | Dependency | Reason |
|-------|------|------------|--------|
| 5.11 | Epic 5 | 10.3 | Uses tier performance for stuck detection |

---

## 9. Configuration Parameters

| Parameter | Default | Location | Story |
|-----------|---------|----------|-------|
| `DIFFICULTY_DISTRIBUTION.novice` | {easy: 0.70, medium: 0.25, hard: 0.05} | `question_selector.py` | 10.4 |
| `DIFFICULTY_DISTRIBUTION.intermediate` | {easy: 0.40, medium: 0.40, hard: 0.20} | `question_selector.py` | 10.4 |
| `DIFFICULTY_DISTRIBUTION.expert` | {easy: 0.10, medium: 0.40, hard: 0.50} | `question_selector.py` | 10.4 |
| `DIFFICULTY_TIERS.easy` | (-3.0, -1.0) | `question_selector.py` | 10.4 |
| `DIFFICULTY_TIERS.medium` | (-1.0, 1.0) | `question_selector.py` | 10.4 |
| `DIFFICULTY_TIERS.hard` | (1.0, 3.0) | `question_selector.py` | 10.4 |
| `ABILITY_THRESHOLDS.mastery_novice_max` | 0.4 | `question_selector.py` | 10.3 |
| `ABILITY_THRESHOLDS.mastery_expert_min` | 0.7 | `question_selector.py` | 10.3 |
| `ABILITY_THRESHOLDS.medium_competence_min` | 3 | `question_selector.py` | 10.3 |
| `ABILITY_THRESHOLDS.hard_competence_min` | 3 | `question_selector.py` | 10.3 |
| `ABILITY_THRESHOLDS.medium_accuracy_min` | 0.6 | `question_selector.py` | 10.3 |
| `ABILITY_THRESHOLDS.hard_accuracy_min` | 0.5 | `question_selector.py` | 10.3 |
| `IRT_DIFFICULTY_ENABLED` | True | `config.py` | 10.5 |

---

## 10. Success Metrics Traceability

| Metric | Target | Story | Measurement Method |
|--------|--------|-------|-------------------|
| Difficulty-appropriate accuracy | 60-80% | 10.4 | Accuracy within expected range per tier |
| Ability classification accuracy | >85% | 10.3 | Expert review validation |
| Engagement (session length) | +15% | 10.5 | A/B test vs control |
| Frustration signal | <10% sessions | 10.4 | Consecutive failures count |
| Boredom signal (skip rate) | <5% | 10.4 | Skip action tracking |
| Selection latency | <200ms | 10.5 | P95 latency monitoring |
| IRT layer latency | <10ms | 10.4 | Isolated timing |
| Migration accuracy | 100% | 10.1 | Post-migration validation |

---

## 11. Documentation Artifacts

| Document | Location | Purpose | Stories |
|----------|----------|---------|---------|
| Epic 10 | `docs/prd/epic-10-irt-difficulty-distribution.md` | Epic definition | All |
| Algorithm Specs | `docs/prd/algorithm-specifications.md` | Algorithms 7, 8, 9 | 10.3, 10.4, 10.5 |
| ADR-002 | `docs/architecture/adr-002-irt-difficulty-scale.md` | Migration decision | 10.1 |
| CSV Template | `scripts/data/question_template_irt.csv` | Import format | 10.2 |
| Functional Requirements | `docs/prd/functional-requirements.md` (FR5B) | Requirements | All |
| Database Schema | `docs/prd/database-schema-bkt.md` | Schema updates (AC 9) | 10.1 |
| This Matrix | `docs/prd/traceability-matrix-irt.md` | Traceability | All |

---

## 12. BMAD Workflow Handoff

### For Architect Agent:
- Review ADR-002 for migration architecture
- Review Algorithm 7, 8, 9 specifications
- Validate database schema changes
- Assess performance implications

### For Scrum Master Agent:
- Create individual story files from Epic 10 story definitions
- Assign story points based on complexity
- Sequence stories per dependency graph
- Define sprint allocation

### For Product Owner Agent:
- Validate acceptance criteria completeness
- Verify success metrics are measurable
- Approve story prioritization
- Confirm business value alignment

### For Developer Agent:
- Implement per story acceptance criteria
- Follow algorithm specifications exactly
- Maintain backward compatibility
- Write comprehensive tests

### For QA Agent:
- Design test cases from acceptance criteria
- Validate migration data integrity
- Performance test selection latency
- A/B test metric validation

---

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-12-22 | 1.1 | Added AC 9 (schema doc update) to Story 10.1 traceability | PM (John) |
| 2025-12-21 | 1.0 | Initial traceability matrix | PM (John) |
