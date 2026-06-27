# Scrum Master Instructions: Story 11.4 - Streak Protection (Freeze Feature)

**Document Purpose:** Provide the Scrum Master agent with all necessary context to draft the complete story file for Story 11.4.

---

## Quick Reference

| Attribute | Value |
|-----------|-------|
| Story ID | 11.4 |
| Story Title | Streak Protection (Freeze Feature) |
| Epic | Epic 11: Gamification & Motivation System |
| Functional Requirements | FR19.19-FR19.23 (Streak Freeze) |
| Dependencies | Story 11.1 (Streak Tracking) |
| Priority | MEDIUM (Retention feature) |
| Estimated Complexity | Medium (Backend logic, grace period handling) |

---

## Source Documents

The Scrum Master should reference these documents when drafting the story:

### Primary Sources

1. **Epic Definition:** `docs/prd/epic-11-gamification-motivation.md`
   - Lines 275-311: Full Story 11.4 specification with acceptance criteria
   - Lines 29-37: Database schema (study_streaks freeze columns)
   - Lines 546-548: Configuration parameters for freeze

2. **Functional Requirements:** `docs/prd/functional-requirements.md`
   - FR19.19-FR19.23: Streak freeze requirements

---

## Story Structure Template

Based on the existing story format in `docs/stories/`, the SM should create:

```
docs/stories/11.4-streak-protection.story.md
```

### Required Sections

1. **Status** - Set to "Ready for Development"

2. **Story** - User story format
   ```
   As a user who may miss a day occasionally,
   I want the option to freeze my streak,
   So that life events don't destroy my progress.
   ```

3. **Acceptance Criteria** - Extract from epic-11-gamification-motivation.md Story 11.4 (6 criteria)

4. **Tasks / Subtasks** - Break down into implementable tasks:
   - Task 1: Extend StreakService with freeze methods
   - Task 2: Implement proactive freeze logic
   - Task 3: Implement retroactive freeze (grace period)
   - Task 4: Add monthly freeze reset logic
   - Task 5: Create freeze schemas
   - Task 6: Implement POST `/api/v1/streaks/freeze` endpoint
   - Task 7: Implement GET `/api/v1/streaks/freezes` endpoint
   - Task 8: Create freeze confirmation dialog (frontend)
   - Task 9: Add freeze indicator to streak calendar
   - Task 10: Implement streak-at-risk prompt
   - Task 11: Unit tests
   - Task 12: Integration tests

5. **Dev Notes** - Include:
   - Business rules
   - Grace period logic
   - Monthly reset timing
   - File locations

6. **Testing** - Required test cases from acceptance criteria

7. **Change Log** - Initial entry

---

## Key Implementation Details

### Extended StreakService Methods

**Location:** `apps/api/src/services/streak_service.py` (extend existing)

```python
class StreakService:
    # ... existing methods from 11.1 ...

    async def freeze_streak(
        self,
        user_id: UUID,
        freeze_date: date  # today or yesterday
    ) -> FreezeResult:
        """
        Freeze streak for specified date.

        Rules:
        - Can freeze today (proactive) or yesterday (retroactive)
        - Cannot freeze if already studied that day
        - Cannot freeze future dates
        - Requires available freeze (max 2/month)
        """

    async def get_freeze_status(self, user_id: UUID) -> FreezeStatus:
        """
        Get current freeze availability.

        Returns:
        - freezes_available: int (0-2)
        - freezes_used_this_month: int
        - next_refill_date: date (1st of next month)
        - can_freeze_today: bool
        - can_freeze_yesterday: bool (grace period)
        """

    async def check_grace_period(self, user_id: UUID) -> GracePeriodStatus:
        """
        Check if user is in grace period (missed yesterday, streak at risk).

        Returns:
        - in_grace_period: bool
        - streak_at_risk: int (current streak that would break)
        - hours_remaining: int (time left to freeze)
        """

    async def reset_monthly_freezes(self) -> int:
        """
        Called by monthly cron job on 1st of month.
        Resets freeze_count_used to 0 for all users.
        Returns count of users reset.
        """
```

### Business Rules

1. **Monthly allowance:** 2 freezes per calendar month
2. **Reset timing:** 1st of each month at midnight UTC
3. **Proactive freeze:** Can freeze today before studying
4. **Retroactive freeze:** Can freeze yesterday within 24 hours
5. **Frozen day:** Doesn't count toward streak but doesn't break it
6. **Cannot freeze if:**
   - Already studied that day (qualifies for streak)
   - No freezes remaining
   - Date is in the future
   - Date is more than 1 day ago

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/streaks/freeze` | POST | Activate freeze for today/yesterday |
| `/api/v1/streaks/freezes` | GET | Get freeze availability status |

### API Request/Response

**POST /api/v1/streaks/freeze**
```json
// Request
{
  "freeze_date": "2025-12-21"  // today or yesterday only
}

// Response
{
  "success": true,
  "streak_preserved": 12,
  "freezes_remaining": 1,
  "frozen_until": "2025-12-21"
}
```

**GET /api/v1/streaks/freezes**
```json
{
  "freezes_available": 2,
  "freezes_used_this_month": 0,
  "next_refill_date": "2026-01-01",
  "can_freeze_today": true,
  "can_freeze_yesterday": false,
  "grace_period": {
    "active": false,
    "streak_at_risk": null,
    "hours_remaining": null
  }
}
```

### Key Schemas

**Location:** `apps/api/src/schemas/streak.py` (extend existing)

```python
class FreezeRequest(BaseModel):
    freeze_date: date

class FreezeResult(BaseModel):
    success: bool
    streak_preserved: int
    freezes_remaining: int
    frozen_until: date
    error: Optional[str]

class FreezeStatus(BaseModel):
    freezes_available: int
    freezes_used_this_month: int
    next_refill_date: date
    can_freeze_today: bool
    can_freeze_yesterday: bool

class GracePeriodStatus(BaseModel):
    active: bool
    streak_at_risk: Optional[int]
    hours_remaining: Optional[int]
```

### Frontend Components

**Location:** `apps/web/src/components/dashboard/`

```
StreakFreezeButton.tsx    - "Freeze Streak" button in widget
FreezeConfirmDialog.tsx   - Confirmation modal
GracePeriodPrompt.tsx     - "Save your streak!" prompt
```

### Grace Period Prompt (Retroactive Freeze)

When user logs in after missing a day:
```
┌─────────────────────────────────────────────┐
│  ⚠️ Your 12-day streak is at risk!          │
│                                             │
│  You missed yesterday. Use a streak freeze  │
│  to save your progress.                     │
│                                             │
│  ❄️ Freezes available: 2                    │
│  ⏰ Time remaining: 18 hours                │
│                                             │
│  [Use Freeze]  [Let Streak Break]           │
└─────────────────────────────────────────────┘
```

---

## Dependencies

### Requires (Must Complete First)

| Story | Reason |
|-------|--------|
| 11.1 | Streak tracking infrastructure |

### Integrates With

| Story | Integration Point |
|-------|-------------------|
| 11.2 | Freeze indicator in streak widget |
| 11.5 | Freeze refill notification |

---

## Testing Requirements

### Unit Tests (`test_streak_freeze.py`)

1. `test_freeze_today_success` - Proactive freeze works
2. `test_freeze_yesterday_success` - Retroactive freeze works
3. `test_freeze_already_studied_fails` - Cannot freeze qualifying day
4. `test_freeze_no_remaining_fails` - Cannot freeze with 0 remaining
5. `test_freeze_future_date_fails` - Cannot freeze future
6. `test_freeze_old_date_fails` - Cannot freeze 2+ days ago
7. `test_monthly_reset` - Freezes reset on 1st
8. `test_streak_preserved_after_freeze` - Streak intact after frozen day
9. `test_grace_period_detection` - Grace period detected correctly
10. `test_grace_period_expires` - 24h limit enforced

### Integration Tests (`test_streak_freeze_api.py`)

1. `test_freeze_endpoint_success` - POST returns correct response
2. `test_freeze_status_endpoint` - GET returns availability
3. `test_freeze_updates_streak_record` - Database updated
4. `test_consecutive_freezes_blocked` - Cannot freeze 2 days in a row (optional rule)

---

## File Locations Summary

| Component | File Path |
|-----------|-----------|
| StreakService (extend) | `apps/api/src/services/streak_service.py` |
| Freeze Schemas | `apps/api/src/schemas/streak.py` |
| Streak Routes (extend) | `apps/api/src/routes/streaks.py` |
| FreezeConfirmDialog | `apps/web/src/components/dashboard/FreezeConfirmDialog.tsx` |
| GracePeriodPrompt | `apps/web/src/components/dashboard/GracePeriodPrompt.tsx` |
| Unit Tests | `apps/api/tests/unit/services/test_streak_freeze.py` |
| Integration Tests | `apps/api/tests/integration/test_streak_freeze_api.py` |

---

## Configuration Options

| Parameter | Default | Description |
|-----------|---------|-------------|
| `monthly_freeze_allowance` | 2 | Freezes per month |
| `retroactive_freeze_window_hours` | 24 | Grace period duration |

---

## Notes for SM

1. **Extends Story 11.1** - Adds freeze methods to existing StreakService
2. **Grace period UX critical** - Prompt must be prominent but not annoying
3. **Timezone handling** - Use user's timezone for day boundaries
4. **Monthly cron job** - Need scheduled task for freeze reset
5. **Premium consideration (Phase 2)** - Additional freezes could be premium feature

---

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-12-21 | 1.0 | Initial SM instructions document | PM (John) |
