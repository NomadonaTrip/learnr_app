# Scrum Master Instructions: Story 11.1 - Daily Streak Tracking and Calculation

**Document Purpose:** Provide the Scrum Master agent with all necessary context to draft the complete story file for Story 11.1.

---

## Quick Reference

| Attribute | Value |
|-----------|-------|
| Story ID | 11.1 |
| Story Title | Daily Streak Tracking and Calculation |
| Epic | Epic 11: Gamification & Motivation System |
| Functional Requirements | FR19.1-FR19.8 (Streak Tracking) |
| Dependencies | Epic 4 (Quiz sessions), Epic 5 (Reading completion) |
| Priority | HIGH (Foundation for all gamification) |
| Estimated Complexity | Medium (Service, database, real-time updates) |

---

## Source Documents

The Scrum Master should reference these documents when drafting the story:

### Primary Sources

1. **Epic Definition:** `docs/prd/epic-11-gamification-motivation.md`
   - Lines 139-188: Full Story 11.1 specification with acceptance criteria
   - Lines 24-103: Database schema (study_streaks, daily_activity tables)
   - Lines 537-558: Configuration parameters

2. **Functional Requirements:** `docs/prd/functional-requirements.md`
   - FR19.1: Consecutive study days tracking
   - FR19.2: Streak qualification rules (5+ questions OR 10+ min OR 3+ readings)
   - FR19.3-FR19.8: Streak calculation and update rules

---

## Story Structure Template

Based on the existing story format in `docs/stories/`, the SM should create:

```
docs/stories/11.1-daily-streak-tracking.story.md
```

### Required Sections

1. **Status** - Set to "Ready for Development"

2. **Story** - User story format
   ```
   As a user studying consistently,
   I want my daily study streaks tracked automatically,
   So that I can see my commitment and stay motivated.
   ```

3. **Acceptance Criteria** - Extract from epic-11-gamification-motivation.md Story 11.1 (10 criteria)

4. **Tasks / Subtasks** - Break down into implementable tasks:
   - Task 1: Create database migration for `study_streaks` table
   - Task 2: Create database migration for `daily_activity` table
   - Task 3: Create StreakService with qualification logic
   - Task 4: Implement streak calculation algorithm
   - Task 5: Create streak update triggers (quiz answer, reading completion)
   - Task 6: Create streak schemas (Pydantic models)
   - Task 7: Implement GET `/api/v1/streaks` endpoint
   - Task 8: Implement GET `/api/v1/streaks/history` endpoint
   - Task 9: Add timezone handling
   - Task 10: Unit tests
   - Task 11: Integration tests

5. **Dev Notes** - Include:
   - Dependencies and sequencing
   - Data models (study_streaks, daily_activity)
   - Integration points (quiz_responses, reading_queue)
   - Race condition considerations
   - File locations

6. **Testing** - Required test cases from acceptance criteria

7. **Change Log** - Initial entry

---

## Key Implementation Details

### New Service

**StreakService** - `apps/api/src/services/streak_service.py`
```python
class StreakService:
    async def qualifies_for_streak(self, activity: DailyActivity) -> bool:
        """
        A day qualifies for streak if user completes ANY of:
        - 5+ quiz questions answered
        - 10+ minutes of study time (600 seconds)
        - 3+ reading materials completed
        """
        return (
            activity.questions_answered >= 5 or
            activity.study_time_seconds >= 600 or
            activity.reading_completed >= 3
        )

    async def update_streak(self, user_id: UUID, activity_date: date) -> StreakUpdate:
        """
        Called after each qualifying activity.

        Rules:
        - Same day activity: No change to streak count
        - Next consecutive day: Increment streak
        - Gap of 1 day (yesterday missed): Streak breaks (unless frozen)
        - Gap of 2+ days: Streak resets to 1
        """

    async def get_streak(self, user_id: UUID) -> StreakData:
        """Get current streak data for user."""

    async def get_streak_history(self, user_id: UUID, days: int = 30) -> List[DailyActivity]:
        """Get last N days of activity history."""

    async def record_activity(self, user_id: UUID, activity_type: str, value: int) -> None:
        """Record activity and check if streak qualifies."""
```

### API Endpoints

| Endpoint | Description |
|----------|-------------|
| GET `/api/v1/streaks` | Current streak data |
| GET `/api/v1/streaks/history` | Last 30 days activity |

### API Response Schema

```json
{
  "current_streak": 12,
  "longest_streak": 18,
  "last_activity_date": "2025-12-21",
  "today_qualifies": true,
  "freeze_available": 2,
  "streak_frozen_until": null
}
```

### Key Schemas

**Location:** `apps/api/src/schemas/streak.py`

```python
class DailyActivityCreate(BaseModel):
    activity_date: date
    questions_answered: int = 0
    reading_completed: int = 0
    study_time_seconds: int = 0

class DailyActivity(BaseModel):
    id: UUID
    user_id: UUID
    activity_date: date
    questions_answered: int
    reading_completed: int
    study_time_seconds: int
    qualifies_for_streak: bool
    created_at: datetime

class StreakData(BaseModel):
    current_streak: int
    longest_streak: int
    last_activity_date: Optional[date]
    today_qualifies: bool
    freeze_available: int
    streak_frozen_until: Optional[date]

class StreakUpdate(BaseModel):
    previous_streak: int
    new_streak: int
    streak_broken: bool
    milestone_reached: Optional[int]  # 3, 7, 14, 30, 60
```

### Performance Requirements

| Operation | Target |
|-----------|--------|
| Streak calculation | <50ms |
| Activity recording | <100ms |
| History retrieval | <200ms |

---

## Dependencies

### Requires (Must Complete First)

| Component | Reason |
|-----------|--------|
| Epic 4 | Quiz session completion events |
| Epic 5 | Reading completion events |
| User timezone | From user profile |

### Enables (Blocks These Stories)

| Story | Reason |
|-------|--------|
| 11.2 | Streak visualization needs streak data |
| 11.3 | Streak achievements need streak count |
| 11.4 | Freeze feature needs streak service |
| 11.5 | Notifications need streak state |

---

## Testing Requirements

### Unit Tests (`test_streak_service.py`)

1. `test_qualifies_for_streak_questions` - 5+ questions qualifies
2. `test_qualifies_for_streak_time` - 10+ minutes qualifies
3. `test_qualifies_for_streak_readings` - 3+ readings qualifies
4. `test_qualifies_for_streak_none` - Less than threshold doesn't qualify
5. `test_streak_increment_consecutive_day` - Next day increments streak
6. `test_streak_break_missed_day` - Gap breaks streak
7. `test_streak_reset_multiple_days` - 2+ day gap resets to 1
8. `test_longest_streak_updated` - Longest streak tracks max
9. `test_same_day_activity_no_change` - Multiple activities same day

### Integration Tests (`test_streak_api.py`)

1. `test_get_streak_endpoint` - Returns correct schema
2. `test_streak_history_endpoint` - Returns 30 days
3. `test_streak_updates_after_quiz` - Quiz answer updates activity
4. `test_streak_updates_after_reading` - Reading completion updates activity
5. `test_timezone_handling` - Respects user timezone

---

## File Locations Summary

| Component | File Path |
|-----------|-----------|
| StreakService | `apps/api/src/services/streak_service.py` |
| Streak Schemas | `apps/api/src/schemas/streak.py` |
| Streak Routes | `apps/api/src/routes/streaks.py` |
| Database Migration | `apps/api/alembic/versions/xxxx_add_streak_tables.py` |
| Unit Tests | `apps/api/tests/unit/services/test_streak_service.py` |
| Integration Tests | `apps/api/tests/integration/test_streak_api.py` |

---

## Configuration Options

| Parameter | Default | Description |
|-----------|---------|-------------|
| `streak_min_questions` | 5 | Minimum questions to qualify |
| `streak_min_study_seconds` | 600 | Minimum study time (10 min) |
| `streak_min_readings` | 3 | Minimum readings to qualify |
| `streak_history_days` | 30 | Days of history to return |

---

## Technical Considerations

1. **Race conditions:** Use database transaction for streak + activity update
2. **Multiple devices:** Last write wins, activity is additive within day
3. **Timezone handling:** Use user's configured timezone, default UTC
4. **Real-time updates:** Streak updates immediately after qualifying activity
5. **Activity aggregation:** Daily activity aggregated from `quiz_responses` and `reading_queue`

---

## Notes for SM

1. **This is the foundation story** - All other Epic 11 stories depend on this
2. **Two new tables required** - Include migration tasks
3. **Integration hooks needed** - Quiz and reading completion must trigger activity recording
4. **Performance critical** - Streak calculation must be <50ms
5. **Consider caching** - Streak data accessed frequently on dashboard

---

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-12-21 | 1.0 | Initial SM instructions document | PM (John) |
