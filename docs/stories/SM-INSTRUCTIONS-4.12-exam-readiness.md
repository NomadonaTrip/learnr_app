# Scrum Master Instructions: Story 4.12 - Exam Readiness Assessment

**Document Purpose:** Provide the Scrum Master agent with all necessary context to draft the complete story file for Story 4.12.

---

## Quick Reference

| Attribute | Value |
|-----------|-------|
| Story ID | 4.12 |
| Story Title | Exam Readiness Assessment & Coverage Gates |
| Epic | Epic 4: Bayesian Adaptive Quiz Engine |
| Functional Requirements | FR5C (Coverage Completion & Exam Readiness) |
| Dependencies | Story 4.5 (Coverage Progress Tracking) |
| Priority | MEDIUM |
| Estimated Complexity | Medium (extends existing coverage system) |

---

## Source Documents

The Scrum Master should reference these documents when drafting the story:

### Primary Sources

1. **Epic Definition:** `docs/prd/epic-4-bkt.md`
   - Lines 688-960: Full Story 4.12 specification with acceptance criteria
   - Lines 983-984: Dependency chain
   - Lines 1012-1014: Success metrics

2. **Functional Requirements:** `docs/prd/functional-requirements.md`
   - Lines 79-111: FR5C complete requirements (15 items)
   - Key thresholds and configuration options

3. **Existing Story Template:** `docs/stories/4.5-coverage-progress-tracking.story.md`
   - Story 4.12 extends this story's CoverageAnalyzer service
   - Follow same task breakdown structure

### Supporting Sources

4. **Gap Analysis:** `docs/prd/gap-analysis-adaptive-learning-vision.md`
   - Lines 208-230: Coverage requirement rationale

5. **Cross-Reference Index:** `docs/prd/cross-reference-index.md`
   - Line 23: FR5C and Story 4.12 entry

---

## Story Structure Template

Based on the existing story format in `docs/stories/`, the SM should create:

```
docs/stories/4.12-exam-readiness-assessment.story.md
```

### Required Sections

1. **Status** - Set to "Ready for Development"

2. **Story** - User story format (As a... I want... So that...)
   ```
   As a user preparing for certification,
   I want to see a clear exam readiness assessment based on my coverage and confidence levels,
   So that I know when I'm adequately prepared and can focus on specific weak areas.
   ```

3. **Acceptance Criteria** - Extract from epic-4-bkt.md Story 4.12 (10 criteria)

4. **Tasks / Subtasks** - Break down into implementable tasks:
   - Task 1: Create ReadinessCalculator service
   - Task 2: Implement readiness score calculation
   - Task 3: Implement KA balance validation
   - Task 4: Create readiness schemas
   - Task 5: Implement recommendation generator
   - Task 6: Create readiness API endpoint
   - Task 7: Add caching layer
   - Task 8: Dashboard integration preparation
   - Task 9: Unit tests
   - Task 10: Integration tests

5. **Dev Notes** - Include:
   - Dependencies and sequencing (requires Story 4.5)
   - Data models (uses CoverageReport from 4.5)
   - Existing code assets (CoverageAnalyzer)
   - Configuration parameters
   - File locations

6. **Testing** - Required test cases from acceptance criteria

7. **Change Log** - Initial entry

---

## Key Implementation Details

### New Service: ReadinessCalculator

**Location:** `apps/api/src/services/readiness_calculator.py`

**Constructor:**
```python
def __init__(self, coverage_analyzer: CoverageAnalyzer):
    self.coverage_analyzer = coverage_analyzer
    self.config = ReadinessConfig.from_course(course_id)
```

**Primary Method:**
```python
async def calculate_readiness(self, user_id: UUID) -> ReadinessAssessment
```

### Readiness Score Formula

```python
readiness_score = (coverage_score * 0.4) + (confidence_score * 0.3) + (ka_balance_score * 0.3)
```

Where:
- `coverage_score` = mastered_count / total_concepts
- `confidence_score` = avg confidence across all beliefs
- `ka_balance_score` = 1.0 - (max_ka_coverage - min_ka_coverage)

### Status Thresholds

| Status | Score Range | Color |
|--------|-------------|-------|
| NOT_READY | < 0.60 | Red |
| ALMOST_READY | 0.60-0.79 | Yellow |
| READY | 0.80-0.89 | Green |
| WELL_PREPARED | >= 0.90 | Green + Star |

### Configuration Defaults

```python
READINESS_CONFIG = {
    'exam_ready_coverage_threshold': 0.80,
    'exam_ready_confidence_threshold': 0.70,
    'ka_minimum_coverage_threshold': 0.60,
    'ka_imbalance_variance_threshold': 0.20,
}
```

### New Schemas

**Location:** `apps/api/src/schemas/readiness.py`

- `ReadinessStatus` (enum)
- `ReadinessIssue` (blocking issue)
- `KAReadinessStatus` (per-KA status)
- `ReadinessAssessment` (full response)

### API Endpoint

```
GET /api/v1/readiness
```

**Performance:** <150ms (uses cached coverage data)

---

## Dependencies

### Requires (Must Complete First)

| Story | Reason |
|-------|--------|
| 4.5 | CoverageAnalyzer service and CoverageReport schema |

### Integrates With

| Story/Epic | Integration Point |
|------------|-------------------|
| Epic 6 | Dashboard displays readiness status |
| Story 4.10 | Quiz analytics includes readiness trends |

---

## Testing Requirements

### Unit Tests (`test_readiness_calculator.py`)

1. `test_readiness_score_calculation` - Verify weighted formula
2. `test_status_not_ready` - Score < 0.60 returns NOT_READY
3. `test_status_almost_ready` - Score 0.60-0.79 returns ALMOST_READY
4. `test_status_ready` - Score 0.80-0.89 returns READY
5. `test_status_well_prepared` - Score >= 0.90 returns WELL_PREPARED
6. `test_ka_balance_detection` - Identify KAs below 60%
7. `test_recommendations_priority` - Most critical issues first
8. `test_course_specific_thresholds` - CFA uses different thresholds

### Integration Tests (`test_readiness_api.py`)

1. `test_readiness_requires_auth` - 401 without token
2. `test_readiness_api_response_schema` - Correct structure
3. `test_readiness_reflects_coverage_changes` - Updates when beliefs change
4. `test_exam_date_warning` - Warning when date < 7 days and readiness < 60%

---

## File Locations Summary

| Component | File Path |
|-----------|-----------|
| ReadinessCalculator Service | `apps/api/src/services/readiness_calculator.py` |
| Readiness Schemas | `apps/api/src/schemas/readiness.py` |
| Readiness Route | `apps/api/src/routes/readiness.py` |
| CoverageAnalyzer (existing) | `apps/api/src/services/coverage_analyzer.py` |
| Unit Tests | `apps/api/tests/unit/services/test_readiness_calculator.py` |
| Integration Tests | `apps/api/tests/integration/test_readiness_api.py` |

---

## Success Metrics (from Epic 4)

| Metric | Target |
|--------|--------|
| Readiness calculation time | <150ms |
| Users reaching "Ready" status | >60% by exam |
| KA balance variance | <20% at readiness |

---

## Notes for SM

1. **Story 4.5 is prerequisite** - Ensure Story 4.5 is complete before this story starts
2. **Extends, doesn't replace** - ReadinessCalculator uses CoverageAnalyzer, doesn't duplicate
3. **Dashboard work is separate** - This story prepares the API; Epic 6 handles UI
4. **Caching reuses 4.5 pattern** - Use same Redis caching approach from CoverageAnalyzer
5. **Course-specific thresholds** - Design with multi-course support (Epic 9 compatibility)

---

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-12-21 | 1.0 | Initial SM instructions document | PM (John) |
