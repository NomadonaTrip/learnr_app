# Scrum Master Instructions: Story 11.6 - Study Goals and Progress Tracking

**Document Purpose:** Provide the Scrum Master agent with all necessary context to draft the complete story file for Story 11.6.

---

## Quick Reference

| Attribute | Value |
|-----------|-------|
| Story ID | 11.6 |
| Story Title | Study Goals and Progress Tracking |
| Epic | Epic 11: Gamification & Motivation System |
| Functional Requirements | FR19.30-FR19.35 (Study Goals) |
| Dependencies | Story 11.1 (Activity tracking), Epic 4 (Quiz data), Epic 5 (Reading data) |
| Priority | MEDIUM (Engagement feature) |
| Estimated Complexity | Medium (Goal setting, progress calculation, weekly summary) |

---

## Source Documents

The Scrum Master should reference these documents when drafting the story:

### Primary Sources

1. **Epic Definition:** `docs/prd/epic-11-gamification-motivation.md`
   - Lines 352-388: Full Story 11.6 specification with acceptance criteria
   - Lines 503-510: Goal progress ring wireframe
   - Lines 552-555: Configuration parameters for goals

2. **Functional Requirements:** `docs/prd/functional-requirements.md`
   - FR19.30-FR19.35: Study goal requirements

---

## Story Structure Template

Based on the existing story format in `docs/stories/`, the SM should create:

```
docs/stories/11.6-study-goals.story.md
```

### Required Sections

1. **Status** - Set to "Ready for Development"

2. **Story** - User story format
   ```
   As a user setting personal targets,
   I want to set daily and weekly study goals,
   So that I can pace my preparation appropriately.
   ```

3. **Acceptance Criteria** - Extract from epic-11-gamification-motivation.md Story 11.6 (7 criteria)

4. **Tasks / Subtasks** - Break down into implementable tasks:
   - Task 1: Create study_goals table migration
   - Task 2: Create GoalService
   - Task 3: Implement goal progress calculation
   - Task 4: Create goal recommendation logic
   - Task 5: Create goal schemas
   - Task 6: Implement GET `/api/v1/goals` endpoint
   - Task 7: Implement PUT `/api/v1/goals` endpoint
   - Task 8: Implement GET `/api/v1/goals/history` endpoint
   - Task 9: Create goal setting UI in settings
   - Task 10: Create goal progress ring on dashboard
   - Task 11: Implement weekly summary notification/email
   - Task 12: Add goal completion celebration
   - Task 13: Implement adaptive goal suggestions
   - Task 14: Unit tests
   - Task 15: Integration tests

5. **Dev Notes** - Include:
   - Goal types and defaults
   - Progress calculation logic
   - Adaptive suggestions algorithm
   - File locations

6. **Testing** - Required test cases from acceptance criteria

7. **Change Log** - Initial entry

---

## Key Implementation Details

### Database Schema

**Table:** `study_goals`

```sql
CREATE TABLE study_goals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Daily goals
    daily_questions_goal INT NOT NULL DEFAULT 10,
    daily_study_minutes_goal INT NOT NULL DEFAULT 15,

    -- Weekly goals
    weekly_questions_goal INT NOT NULL DEFAULT 50,
    weekly_mastery_goal INT NOT NULL DEFAULT 5,  -- concepts to master

    -- Goal preferences
    show_goal_on_dashboard BOOLEAN NOT NULL DEFAULT TRUE,
    goal_completion_celebration BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    UNIQUE(user_id)
);

CREATE INDEX idx_study_goals_user ON study_goals(user_id);
```

### New Service

**GoalService** - `apps/api/src/services/goal_service.py`

```python
class GoalService:
    async def get_goals(self, user_id: UUID) -> UserGoals:
        """Get user's goal settings."""

    async def update_goals(self, user_id: UUID, goals: GoalUpdate) -> UserGoals:
        """Update user's goal settings."""

    async def get_goal_progress(self, user_id: UUID) -> GoalProgress:
        """
        Get current progress toward daily and weekly goals.

        Returns:
            - daily_questions: current/goal
            - daily_study_time: current/goal (minutes)
            - weekly_questions: current/goal
            - weekly_mastery: current/goal
            - daily_complete: bool
            - weekly_complete: bool
        """

    async def get_goal_history(
        self,
        user_id: UUID,
        weeks: int = 4
    ) -> List[WeeklyGoalSummary]:
        """Get historical goal completion data."""

    async def get_suggested_goals(self, user_id: UUID) -> SuggestedGoals:
        """
        Get adaptive goal suggestions based on:
        - Days until exam
        - Current performance
        - Recent goal completion rate
        """

    async def check_goal_completion(self, user_id: UUID) -> Optional[GoalCompletion]:
        """
        Check if user just completed a goal (for celebration trigger).
        Called after quiz answer or reading completion.
        """
```

### Goal Types

| Goal | Default | Unit | Reset |
|------|---------|------|-------|
| Daily Questions | 10 | questions | Daily (midnight) |
| Daily Study Time | 15 | minutes | Daily (midnight) |
| Weekly Questions | 50 | questions | Weekly (Monday) |
| Weekly Mastery | 5 | concepts | Weekly (Monday) |

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/goals` | GET | Current goals and progress |
| `/api/v1/goals` | PUT | Update goal settings |
| `/api/v1/goals/history` | GET | Weekly goal history |
| `/api/v1/goals/suggestions` | GET | Adaptive goal recommendations |

### API Response Schema

**GET /api/v1/goals**
```json
{
  "settings": {
    "daily_questions_goal": 10,
    "daily_study_minutes_goal": 15,
    "weekly_questions_goal": 50,
    "weekly_mastery_goal": 5
  },
  "progress": {
    "daily": {
      "questions": {"current": 8, "goal": 10, "percent": 80},
      "study_time": {"current": 12, "goal": 15, "percent": 80}
    },
    "weekly": {
      "questions": {"current": 42, "goal": 50, "percent": 84},
      "mastery": {"current": 3, "goal": 5, "percent": 60}
    },
    "daily_complete": false,
    "weekly_complete": false
  },
  "suggestions": {
    "message": "You've exceeded your goal 5 days in a row. Consider increasing to 15 questions?",
    "suggested_daily_questions": 15
  }
}
```

### Key Schemas

**Location:** `apps/api/src/schemas/goal.py`

```python
class GoalSettings(BaseModel):
    daily_questions_goal: int = Field(ge=1, le=100, default=10)
    daily_study_minutes_goal: int = Field(ge=5, le=180, default=15)
    weekly_questions_goal: int = Field(ge=10, le=500, default=50)
    weekly_mastery_goal: int = Field(ge=1, le=50, default=5)

class GoalProgress(BaseModel):
    current: int
    goal: int
    percent: float

class DailyProgress(BaseModel):
    questions: GoalProgress
    study_time: GoalProgress

class WeeklyProgress(BaseModel):
    questions: GoalProgress
    mastery: GoalProgress

class UserGoalProgress(BaseModel):
    settings: GoalSettings
    progress: dict  # daily + weekly progress
    daily_complete: bool
    weekly_complete: bool
    suggestions: Optional[GoalSuggestion]

class WeeklyGoalSummary(BaseModel):
    week_start: date
    week_end: date
    questions_completed: int
    questions_goal: int
    concepts_mastered: int
    mastery_goal: int
    goals_met: int  # 0-4
    comparison_to_previous: str  # 'better', 'same', 'worse'
```

### Adaptive Goal Suggestions

```python
def calculate_suggested_goals(
    user_id: UUID,
    days_until_exam: int,
    current_coverage: float,
    recent_completion_rate: float  # last 7 days
) -> SuggestedGoals:
    """
    Adaptive goal logic:

    1. If exceeded goal 5+ days in a row → suggest increase
    2. If missed goal 3+ days in a row → suggest decrease
    3. If behind schedule for exam → suggest increase with message
    4. If ahead of schedule → maintain current
    """
```

### Frontend Components

**Location:** `apps/web/src/components/`

```
dashboard/GoalProgressRing.tsx   - Circular progress on dashboard
settings/GoalSettings.tsx        - Goal configuration form
dashboard/GoalCelebration.tsx    - Completion animation
```

### Goal Progress Ring Wireframe (from Epic)

```
     ╭───────╮
    ╱    8    ╲
   │   ───    │
   │    10    │
    ╲ questions╱
     ╰───────╯
   80% complete
```

---

## Dependencies

### Requires (Must Complete First)

| Story | Reason |
|-------|--------|
| 11.1 | Daily activity data for progress calculation |
| Epic 4 | Questions answered count |
| Epic 5 | Reading completion data |

### Integrates With

| Story | Integration Point |
|-------|-------------------|
| 11.2 | Goal progress shown on dashboard |
| 11.5 | Weekly summary notification |

---

## Testing Requirements

### Unit Tests (`test_goal_service.py`)

1. `test_default_goals_created` - New user gets defaults
2. `test_update_goals` - Goal settings saved
3. `test_daily_progress_calculation` - Questions counted correctly
4. `test_weekly_progress_calculation` - Week aggregation correct
5. `test_goal_completion_detected` - Completion trigger fires
6. `test_suggestion_increase` - Suggests increase when exceeding
7. `test_suggestion_decrease` - Suggests decrease when missing
8. `test_weekly_reset` - Progress resets on Monday

### Integration Tests (`test_goal_api.py`)

1. `test_get_goals_endpoint` - Returns goals and progress
2. `test_update_goals_endpoint` - PUT updates settings
3. `test_goal_history_endpoint` - Returns weekly summaries
4. `test_suggestions_endpoint` - Returns adaptive suggestions

### Frontend Tests

1. `test_progress_ring_renders` - Ring displays correctly
2. `test_goal_settings_form` - Form saves correctly
3. `test_celebration_animation` - Animation triggers on completion

---

## File Locations Summary

| Component | File Path |
|-----------|-----------|
| GoalService | `apps/api/src/services/goal_service.py` |
| Goal Schemas | `apps/api/src/schemas/goal.py` |
| Goal Routes | `apps/api/src/routes/goals.py` |
| Database Migration | `apps/api/alembic/versions/xxxx_add_goal_tables.py` |
| GoalProgressRing | `apps/web/src/components/dashboard/GoalProgressRing.tsx` |
| GoalSettings | `apps/web/src/components/settings/GoalSettings.tsx` |
| Unit Tests | `apps/api/tests/unit/services/test_goal_service.py` |
| Integration Tests | `apps/api/tests/integration/test_goal_api.py` |

---

## Configuration Options

| Parameter | Default | Description |
|-----------|---------|-------------|
| `default_daily_questions` | 10 | Default daily question goal |
| `default_daily_study_minutes` | 15 | Default daily time goal |
| `default_weekly_questions` | 50 | Default weekly question goal |
| `suggest_increase_threshold` | 5 | Days exceeding to suggest increase |
| `suggest_decrease_threshold` | 3 | Days missing to suggest decrease |

---

## Notes for SM

1. **Uses activity data from 11.1** - Extends daily_activity tracking
2. **Weekly reset timing** - Consider user timezone for Monday reset
3. **Exam pacing** - Suggestions should consider days_until_exam
4. **Celebration UX** - Keep celebration brief, not blocking
5. **Weekly summary** - Could be email or in-app notification (integrate with 11.5)

---

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-12-21 | 1.0 | Initial SM instructions document | PM (John) |
