# Scrum Master Instructions: Story 6.6 - Curriculum Progress & Concept Unlock Display

**Document Purpose:** Provide the Scrum Master agent with all necessary context to draft the complete story file for Story 6.6.

---

## Quick Reference

| Attribute | Value |
|-----------|-------|
| Story ID | 6.6 |
| Story Title | Curriculum Progress & Concept Unlock Display |
| Epic | Epic 6: Progress Dashboard & Transparency |
| Functional Requirements | Extends FR11 (Progress Dashboard) |
| Dependencies | Story 4.11 (Mastery Gates), Story 4.5 (Coverage Tracking), Story 6.1 (Dashboard Overview) |
| Priority | LOW (Enhancement) |
| Estimated Complexity | Medium (API extension, frontend component) |

---

## Source Documents

The Scrum Master should reference these documents when drafting the story:

### Primary Sources

1. **Epic Definition:** `docs/prd/epic-6.md`
   - Lines 129-251: Full Story 6.6 specification with acceptance criteria
   - Lines 254-271: Dependencies
   - Lines 275-286: Success metrics

2. **Mastery Gates Story:** `docs/stories/4.11-prerequisite-based-curriculum-navigation.story.md` (or SM instructions)
   - Story 6.6 displays data from the `concept_unlock_events` table created by 4.11

3. **Gap Analysis:** `docs/prd/gap-analysis-adaptive-learning-vision.md`
   - Lines 140-164: Progress dashboards enhancement rationale

---

## Story Structure Template

Based on the existing story format in `docs/stories/`, the SM should create:

```
docs/stories/6.6-curriculum-progress-display.story.md
```

### Required Sections

1. **Status** - Set to "Ready for Development"

2. **Story** - User story format
   ```
   As a user tracking my learning journey,
   I want to see my curriculum progress showing how many concepts I've unlocked and mastered,
   So that I understand my progression through the knowledge structure and feel a sense of accomplishment.
   ```

3. **Acceptance Criteria** - Extract from epic-6.md Story 6.6 (10 criteria)

4. **Tasks / Subtasks** - Break down into implementable tasks:
   - Task 1: Extend dashboard API with curriculum_progress object
   - Task 2: Create CurriculumProgressService
   - Task 3: Implement recently_unlocked query
   - Task 4: Create curriculum progress schemas
   - Task 5: Implement per-KA breakdown endpoint
   - Task 6: Implement next-to-unlock calculation
   - Task 7: Create curriculum progress card component (frontend)
   - Task 8: Implement unlock celebration animation
   - Task 9: Add accessibility attributes
   - Task 10: Unit tests
   - Task 11: Integration tests

5. **Dev Notes** - Include:
   - Dependencies and sequencing
   - Data models (uses concept_unlock_events from 4.11)
   - Existing code assets (MasteryGateService from 4.11)
   - Frontend component location
   - File locations

6. **Testing** - Required test cases from acceptance criteria

7. **Change Log** - Initial entry

---

## Key Implementation Details

### New Service

**CurriculumProgressService** - `apps/api/src/services/curriculum_progress.py`
```python
class CurriculumProgressService:
    def __init__(self, mastery_gate_service, coverage_analyzer):
        self.mastery_gate = mastery_gate_service
        self.coverage = coverage_analyzer

    async def get_curriculum_progress(self, user_id: UUID) -> CurriculumProgress:
        """
        Get curriculum progress summary.

        Returns:
            CurriculumProgress:
                - total_concepts: int
                - unlocked: int
                - locked: int
                - mastered: int
                - in_progress: int
                - unlock_percentage: float
                - mastery_percentage: float
                - recently_unlocked: List[UnlockedConcept]
        """

    async def get_progress_by_ka(self, user_id: UUID) -> List[KAProgress]:
        """Get curriculum progress broken down by KA."""

    async def get_next_to_unlock(self, user_id: UUID) -> List[NearUnlock]:
        """Get concepts closest to being unlocked."""
```

### API Endpoints

| Endpoint | Description |
|----------|-------------|
| GET `/api/dashboard` | Extended with `curriculum_progress` object |
| GET `/api/dashboard/curriculum/by-ka` | Per-KA breakdown |

### Dashboard API Extension

```json
{
  "ka_scores": [...],
  "exam_readiness_score": 0.72,
  "curriculum_progress": {
    "total_concepts": 1203,
    "unlocked": 892,
    "locked": 311,
    "mastered": 487,
    "in_progress": 405,
    "untouched": 311,
    "unlock_percentage": 74.1,
    "mastery_percentage": 40.5,
    "recently_unlocked": [
      {"concept_id": "uuid", "name": "Requirements Prioritization", "unlocked_at": "2025-12-20T14:30:00Z"}
    ],
    "next_to_unlock": [
      {"concept_id": "uuid", "name": "Advanced Stakeholder Mapping", "prereq_mastery": 0.65, "questions_to_unlock": 2}
    ]
  }
}
```

### Key Schemas

**Location:** `apps/api/src/schemas/curriculum_progress.py`

```python
class UnlockedConcept(BaseModel):
    concept_id: UUID
    name: str
    unlocked_at: datetime

class NearUnlock(BaseModel):
    concept_id: UUID
    name: str
    blocking_prereq: str
    prereq_mastery: float
    required_mastery: float
    questions_to_unlock: int

class KAProgress(BaseModel):
    ka_id: str
    ka_name: str
    total_concepts: int
    unlocked: int
    locked: int
    mastered: int
    unlock_percentage: float

class CurriculumProgress(BaseModel):
    total_concepts: int
    unlocked: int
    locked: int
    mastered: int
    in_progress: int
    untouched: int
    unlock_percentage: float
    mastery_percentage: float
    recently_unlocked: list[UnlockedConcept]
    next_to_unlock: list[NearUnlock]
```

### Frontend Component

**Location:** `apps/web/src/components/dashboard/CurriculumProgressCard.tsx`

Features:
- Progress ring/bar showing unlock percentage
- Segmented bar (mastered/in-progress/locked)
- Recently unlocked list with "time ago" display
- "Almost unlocked" preview
- Unlock celebration animation (confetti/glow)

---

## Dependencies

### Requires (Must Complete First)

| Story | Reason |
|-------|--------|
| 4.11 | `concept_unlock_events` table and MasteryGateService |
| 4.5 | Mastery classification for concept states |
| 6.1 | Dashboard infrastructure to add curriculum card |

### Integrates With

| Story/Epic | Integration Point |
|------------|-------------------|
| Story 6.1 | Curriculum card placed on main dashboard |
| Story 4.11 | Real-time unlock notifications |

---

## Testing Requirements

### Unit Tests (`test_curriculum_progress.py`)

1. `test_progress_counts_correct` - Total/unlocked/locked/mastered accurate
2. `test_unlock_percentage_calculation` - Percentage math correct
3. `test_recently_unlocked_order` - Most recent first
4. `test_recently_unlocked_limit` - Limited to configured count
5. `test_next_to_unlock_calculation` - Correct prereq mastery gap
6. `test_questions_to_unlock_estimate` - Reasonable estimate

### Integration Tests (`test_curriculum_api.py`)

1. `test_dashboard_includes_curriculum` - curriculum_progress in response
2. `test_curriculum_by_ka_endpoint` - Per-KA data correct
3. `test_recently_unlocked_after_event` - New unlock appears
4. `test_progress_updates_on_mastery` - Counts update correctly

### Frontend Tests

1. `test_progress_card_renders` - Card displays correctly
2. `test_celebration_animation` - Animation triggers on new unlock
3. `test_accessibility_attributes` - Screen reader support

---

## File Locations Summary

| Component | File Path |
|-----------|-----------|
| CurriculumProgressService | `apps/api/src/services/curriculum_progress.py` |
| Curriculum Schemas | `apps/api/src/schemas/curriculum_progress.py` |
| Dashboard Route (extend) | `apps/api/src/routes/dashboard.py` |
| Progress Card Component | `apps/web/src/components/dashboard/CurriculumProgressCard.tsx` |
| Unit Tests | `apps/api/tests/unit/services/test_curriculum_progress.py` |
| Integration Tests | `apps/api/tests/integration/test_curriculum_api.py` |

---

## Configuration Options

| Parameter | Default | Description |
|-----------|---------|-------------|
| `recently_unlocked_count` | 3 | Number of recent unlocks to show |
| `next_to_unlock_count` | 3 | Number of "almost unlocked" to show |
| `unlock_celebration_enabled` | true | Show celebration animation |

---

## Visual Design Notes

1. **Progress Card:** 22px radius, consistent with other dashboard cards
2. **Progress Colors:**
   - Green: Mastered concepts
   - Yellow: In-progress concepts
   - Gray: Locked concepts
3. **Lock Icon:** Subtle, not alarming
4. **Celebration:** Brief confetti or glow animation on new unlock
5. **Accessibility:**
   - Progress announced by screen readers
   - Lock status via text, not just icons

---

## Notes for SM

1. **Story 4.11 is prerequisite** - Must have unlock events table
2. **Extends existing dashboard API** - Don't create separate endpoint for main progress
3. **Frontend component** - Include in story scope (or split into 6.6a backend / 6.6b frontend)
4. **Celebration animation** - Keep subtle, not distracting
5. **Performance** - Cache curriculum progress, invalidate on unlock event

---

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-12-21 | 1.0 | Initial SM instructions document | PM (John) |
