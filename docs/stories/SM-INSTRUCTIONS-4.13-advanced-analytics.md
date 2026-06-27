# Scrum Master Instructions: Story 4.13 - Advanced Performance Analytics

**Document Purpose:** Provide the Scrum Master agent with all necessary context to draft the complete story file for Story 4.13.

---

## Quick Reference

| Attribute | Value |
|-----------|-------|
| Story ID | 4.13 |
| Story Title | Advanced Performance Analytics |
| Epic | Epic 4: Bayesian Adaptive Quiz Engine |
| Functional Requirements | Extends FR5 (Competency Tracking & Estimation) |
| Dependencies | Story 4.10 (Quiz Analytics), Story 4.5 (Coverage Tracking) |
| Priority | LOW (Enhancement) |
| Estimated Complexity | Medium-High (multiple analytics services, export functionality) |

---

## Source Documents

The Scrum Master should reference these documents when drafting the story:

### Primary Sources

1. **Epic Definition:** `docs/prd/epic-4-bkt.md`
   - Lines 963-1228: Full Story 4.13 specification with acceptance criteria
   - Lines 1253: Dependency chain
   - Lines 1284-1288: Success metrics

2. **Existing Analytics Story:** `docs/stories/4.10-quiz-analytics.story.md` (if exists)
   - Story 4.13 extends the base analytics infrastructure

3. **Gap Analysis:** `docs/prd/gap-analysis-adaptive-learning-vision.md`
   - Lines 195-216: Performance analytics rationale

---

## Story Structure Template

Based on the existing story format in `docs/stories/`, the SM should create:

```
docs/stories/4.13-advanced-performance-analytics.story.md
```

### Required Sections

1. **Status** - Set to "Ready for Development"

2. **Story** - User story format
   ```
   As a user wanting deeper insights into my learning patterns,
   I want to see detailed analytics about my study habits, question performance, and improvement velocity,
   So that I can optimize my study approach and understand what's working.
   ```

3. **Acceptance Criteria** - Extract from epic-4-bkt.md Story 4.13 (10 criteria)

4. **Tasks / Subtasks** - Break down into implementable tasks:
   - Task 1: Create TimeAnalyticsService
   - Task 2: Implement optimal study time calculation
   - Task 3: Implement session fatigue analysis
   - Task 4: Create question-level analytics methods
   - Task 5: Implement improvement velocity tracking
   - Task 6: Create comparison analytics (with privacy safeguards)
   - Task 7: Create analytics schemas
   - Task 8: Implement API endpoints (4 new endpoints)
   - Task 9: Create ReportGenerator for PDF/CSV export
   - Task 10: Dashboard integration (analytics summary card)
   - Task 11: Unit tests
   - Task 12: Integration tests

5. **Dev Notes** - Include:
   - Dependencies and sequencing
   - Data models (uses quiz_responses, belief_states)
   - Existing code assets (QuizAnalytics from 4.10)
   - Privacy considerations for comparison analytics
   - File locations

6. **Testing** - Required test cases from acceptance criteria

7. **Change Log** - Initial entry

---

## Key Implementation Details

### New Services

**TimeAnalyticsService** - `apps/api/src/services/time_analytics.py`
```python
class TimeAnalyticsService:
    async def get_optimal_study_times(user_id) -> OptimalStudyTimes
    async def get_session_fatigue_analysis(user_id) -> FatigueAnalysis
```

**QuestionAnalyticsService** - `apps/api/src/services/question_analytics.py`
```python
class QuestionAnalyticsService:
    async def get_question_analytics(user_id) -> QuestionAnalytics
    async def get_frequently_missed_concepts(user_id) -> List[ConceptStat]
```

**VelocityTracker** - `apps/api/src/services/velocity_tracker.py`
```python
class VelocityTracker:
    async def get_improvement_velocity(user_id) -> ImprovementVelocity
```

**ComparisonAnalytics** - `apps/api/src/services/comparison_analytics.py`
```python
class ComparisonAnalytics:
    async def get_comparison_analytics(user_id) -> ComparisonAnalytics
    # Privacy: Uses pre-computed cohort aggregates, minimum 50 users
```

**ReportGenerator** - `apps/api/src/services/report_generator.py`
```python
class ReportGenerator:
    async def generate_pdf_report(user_id, date_range) -> bytes
    async def generate_csv_export(user_id, date_range) -> str
```

### API Endpoints

| Endpoint | Description |
|----------|-------------|
| GET `/api/v1/analytics/time-patterns` | Best study times, fatigue analysis |
| GET `/api/v1/analytics/questions` | Question-level performance |
| GET `/api/v1/analytics/velocity` | Improvement velocity |
| GET `/api/v1/analytics/comparison` | Cohort comparison |
| GET `/api/v1/analytics/export` | PDF/CSV export |

### Key Schemas

**Location:** `apps/api/src/schemas/analytics.py`

- `OptimalStudyTimes`
- `FatigueAnalysis`
- `QuestionStat`
- `QuestionAnalytics`
- `ImprovementVelocity`
- `ComparisonAnalytics`

### Performance Requirements

| Operation | Target |
|-----------|--------|
| Time analytics | <300ms |
| Question analytics | <500ms |
| Velocity calculation | <200ms |
| Comparison analytics | <400ms |
| PDF export | <5s |
| CSV export | <2s |

---

## Dependencies

### Requires (Must Complete First)

| Story | Reason |
|-------|--------|
| 4.10 | Base quiz analytics infrastructure |
| 4.5 | Coverage data for velocity calculations |

### Integrates With

| Story/Epic | Integration Point |
|------------|-------------------|
| Epic 6 | Analytics summary card on dashboard |
| Story 6.6 | Curriculum progress analytics |

---

## Testing Requirements

### Unit Tests (`test_analytics_services.py`)

1. `test_optimal_study_time_calculation` - Correct hour/day identification
2. `test_fatigue_onset_detection` - Accuracy drop detection
3. `test_improvement_velocity_trend` - Accelerating/steady/slowing
4. `test_percentile_rank_calculation` - Correct ranking
5. `test_cohort_minimum_size` - Returns null if < 50 users
6. `test_csv_export_columns` - Expected columns present
7. `test_pdf_generation` - PDF creates without error

### Integration Tests (`test_analytics_api.py`)

1. `test_time_patterns_endpoint` - Returns correct schema
2. `test_questions_endpoint` - Hardest/easiest accurate
3. `test_velocity_endpoint` - Velocity data correct
4. `test_comparison_endpoint` - Privacy maintained
5. `test_export_csv_download` - File downloads correctly
6. `test_export_pdf_download` - File downloads correctly

---

## File Locations Summary

| Component | File Path |
|-----------|-----------|
| TimeAnalyticsService | `apps/api/src/services/time_analytics.py` |
| QuestionAnalyticsService | `apps/api/src/services/question_analytics.py` |
| VelocityTracker | `apps/api/src/services/velocity_tracker.py` |
| ComparisonAnalytics | `apps/api/src/services/comparison_analytics.py` |
| ReportGenerator | `apps/api/src/services/report_generator.py` |
| Analytics Schemas | `apps/api/src/schemas/analytics.py` |
| Analytics Routes | `apps/api/src/routes/analytics.py` |
| Unit Tests | `apps/api/tests/unit/services/test_analytics_services.py` |
| Integration Tests | `apps/api/tests/integration/test_analytics_api.py` |

---

## Configuration Options

| Parameter | Default | Description |
|-----------|---------|-------------|
| `cohort_minimum_size` | 50 | Minimum users for comparison |
| `fatigue_threshold` | 0.10 | Accuracy drop to detect fatigue |
| `velocity_window_days` | 7 | Days for velocity calculation |
| `export_date_range_max` | 365 | Maximum days for export |

---

## Privacy Considerations

1. **Comparison analytics** use only pre-computed cohort aggregates
2. **No individual user data** exposed in comparisons
3. **Export** includes only requesting user's own data
4. **Cohort minimum:** 50 users (below this, show "Insufficient data")

---

## Notes for SM

1. **Story 4.10 is prerequisite** - Base analytics infrastructure must exist
2. **Privacy is critical** - Comparison analytics must use aggregated data only
3. **PDF generation** - May require additional library (reportlab or weasyprint)
4. **Performance** - Use pre-computed stats where possible
5. **Dashboard integration** - Analytics summary card is separate from full analytics page

---

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-12-21 | 1.0 | Initial SM instructions document | PM (John) |
