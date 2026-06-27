# Scrum Master Instructions: Story 11.5 - Streak Risk Notifications

**Document Purpose:** Provide the Scrum Master agent with all necessary context to draft the complete story file for Story 11.5.

---

## Quick Reference

| Attribute | Value |
|-----------|-------|
| Story ID | 11.5 |
| Story Title | Streak Risk Notifications |
| Epic | Epic 11: Gamification & Motivation System |
| Functional Requirements | FR19.23-FR19.26 (Notifications) |
| Dependencies | Story 11.1 (Streak Tracking) |
| Priority | MEDIUM (Engagement feature) |
| Estimated Complexity | Medium (Email + In-App notifications only for MVP) |

---

## MVP Scope Decision

**For MVP, notifications are limited to two channels:**

| Channel | MVP Status | Rationale |
|---------|------------|-----------|
| **In-App** | ✅ Included | Zero external dependencies, notification center UI |
| **Email** | ✅ Included | SendGrid configured, proven delivery for reminders |
| **Push** | ❌ Deferred | Requires PWA/service worker complexity - Phase 2 |

This simplification reduces implementation complexity while preserving the core gamification loop:
- Email brings users back to the app
- In-app notifications provide details and celebrate achievements

---

## Source Documents

The Scrum Master should reference these documents when drafting the story:

### Primary Sources

1. **Epic Definition:** `docs/prd/epic-11-gamification-motivation.md`
   - Lines 313-350: Full Story 11.5 specification with acceptance criteria
   - Lines 89-102: Database schema (notifications table)
   - Lines 549-551: Configuration parameters for notifications

2. **Functional Requirements:** `docs/prd/functional-requirements.md`
   - FR19.23-FR19.26: Notification requirements

3. **Database Schema:** `docs/prd/database-schema-bkt.md`
   - `notifications` table (in Gamification Tables section)
   - `notification_preferences` table (in User Preferences section)

---

## Infrastructure Available

The following infrastructure is already specified and available:

| Component | Location | Status |
|-----------|----------|--------|
| SendGrid email service | `docs/architecture/tech-stack.md` | ✅ Configured |
| `notifications` table | `docs/prd/database-schema-bkt.md` | ✅ Defined |
| `notification_preferences` table | `docs/prd/database-schema-bkt.md` | ✅ Defined |
| `users.timezone` field | `docs/prd/database-schema-bkt.md` | ✅ Defined |
| Celery Beat scheduler | `infrastructure/docker/docker-compose.dev.yml` | ✅ Configured |
| Redis broker | `infrastructure/docker/docker-compose.dev.yml` | ✅ Configured |

**No new foundational stories required.**

---

## Story Structure Template

Based on the existing story format in `docs/stories/`, the SM should create:

```
docs/stories/11.5-streak-risk-notifications.story.md
```

### Required Sections

1. **Status** - Set to "Ready for Development"

2. **Story** - User story format
   ```
   As a user who might forget to study,
   I want timely reminders when my streak is at risk,
   So that I don't accidentally lose my progress.
   ```

3. **Acceptance Criteria** - Extract from epic-11-gamification-motivation.md Story 11.5 (7 criteria)

4. **Tasks / Subtasks** - Break down into implementable tasks:
   - Task 1: Create NotificationService
   - Task 2: Implement in-app notification creation and retrieval
   - Task 3: Implement email notification sender (SendGrid)
   - Task 4: Implement evening reminder logic (8pm local)
   - Task 5: Implement late warning logic (10pm local)
   - Task 6: Implement streak broken notification
   - Task 7: Implement milestone celebration notification
   - Task 8: Create notification preferences API endpoints
   - Task 9: Create Celery periodic task for notification scheduling
   - Task 10: Create notification center UI (bell icon, dropdown)
   - Task 11: Add notification preferences to settings page
   - Task 12: Add vacation mode (mute notifications)
   - Task 13: Unit tests
   - Task 14: Integration tests

5. **Dev Notes** - Include:
   - MVP scope (email + in-app only)
   - Scheduling logic
   - Timezone handling
   - Deduplication rules
   - File locations

6. **Testing** - Required test cases from acceptance criteria

7. **Change Log** - Initial entry

---

## Key Implementation Details

### New Service

**NotificationService** - `apps/api/src/services/notification_service.py`

```python
class NotificationService:
    """
    MVP Notification Service - Email + In-App only.
    Push notifications deferred to Phase 2.
    """

    def __init__(self, sendgrid_client, db_session):
        self.sendgrid = sendgrid_client
        self.db = db_session

    async def create_notification(
        self,
        user_id: UUID,
        notification_type: str,
        title: str,
        message: str,
        payload: Optional[dict] = None
    ) -> Notification:
        """
        Create in-app notification and optionally send email.

        MVP Channels:
        - in_app: Always created (stored in notifications table)
        - email: If user has email_enabled=True in preferences
        """

    async def send_email_notification(
        self,
        user_email: str,
        subject: str,
        body: str,
        template_id: Optional[str] = None
    ) -> bool:
        """Send email via SendGrid."""

    async def get_user_notifications(
        self,
        user_id: UUID,
        limit: int = 20,
        unread_only: bool = False
    ) -> List[Notification]:
        """Get user's recent notifications for notification center."""

    async def mark_as_read(self, user_id: UUID, notification_id: UUID) -> None:
        """Mark single notification as read."""

    async def mark_all_read(self, user_id: UUID) -> int:
        """Mark all notifications as read. Returns count updated."""

    async def dismiss_notification(self, user_id: UUID, notification_id: UUID) -> None:
        """Dismiss (hide) a notification."""

    async def get_unread_count(self, user_id: UUID) -> int:
        """Get count of unread notifications for badge."""
```

### Notification Types

| Type | Trigger | Channel | Message |
|------|---------|---------|---------|
| `streak_risk` | Scheduled (8pm) | Email + In-App | "Don't forget to study today! Your X-day streak is at risk." |
| `streak_warning` | Scheduled (10pm) | Email + In-App | "Your X-day streak ends in 2 hours!" |
| `streak_broken` | On login (next day) | In-App only | "Your streak ended. Start a new one today!" |
| `milestone_approaching` | On streak update | In-App only | "2 more days to your 7-day badge!" |
| `milestone_reached` | On streak update | In-App only | "You earned Week Warrior!" |
| `achievement_unlocked` | On achievement | In-App only | "You unlocked {achievement_name}!" |
| `freeze_refill` | Monthly cron | In-App only | "Your streak freezes have been refilled!" |

### Celery Periodic Tasks

**Location:** `apps/api/src/tasks/notification_tasks.py`

```python
from celery import shared_task
from celery.schedules import crontab

# Celery Beat schedule configuration
CELERYBEAT_SCHEDULE = {
    'check-streak-reminders': {
        'task': 'tasks.notification_tasks.check_and_send_streak_reminders',
        'schedule': crontab(minute='*/15'),  # Every 15 minutes
    },
    'monthly-freeze-refill-notification': {
        'task': 'tasks.notification_tasks.send_freeze_refill_notifications',
        'schedule': crontab(hour=9, minute=0, day_of_month=1),  # 1st of month, 9am UTC
    },
}

@shared_task
def check_and_send_streak_reminders():
    """
    Runs every 15 minutes.

    1. Query users with active streaks who haven't studied today
    2. Check each user's local time (using timezone from profile)
    3. If 8pm local and no reminder sent today → send evening reminder
    4. If 10pm local and no late warning sent today → send late warning
    5. Deduplicate to prevent multiple sends
    """

@shared_task
def send_freeze_refill_notifications():
    """
    Runs on 1st of each month.
    Notify users their streak freezes have been refilled.
    """
```

### Smart Notification Logic

```python
async def should_send_streak_reminder(user_id: UUID, reminder_type: str) -> bool:
    """
    Determine if reminder should be sent.

    Returns True if ALL conditions met:
    - User has streak_reminders_enabled = True
    - User hasn't studied today (not qualified for streak)
    - User isn't muted (muted_until is null or in the past)
    - User has an active streak > 0 (something to lose)
    - Haven't already sent this reminder type today
    """

def get_user_local_hour(user_timezone: str) -> int:
    """
    Get current hour in user's local timezone.
    Uses pytz or zoneinfo for conversion.
    """
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/notifications` | GET | User's recent notifications |
| `/api/v1/notifications/unread-count` | GET | Count for badge |
| `/api/v1/notifications/{id}/read` | POST | Mark as read |
| `/api/v1/notifications/{id}/dismiss` | POST | Dismiss notification |
| `/api/v1/notifications/mark-all-read` | POST | Mark all as read |
| `/api/v1/notifications/preferences` | GET | Get notification preferences |
| `/api/v1/notifications/preferences` | PUT | Update notification preferences |

### API Response Schemas

**GET /api/v1/notifications**
```json
{
  "notifications": [
    {
      "id": "uuid",
      "type": "streak_risk",
      "title": "Streak at risk!",
      "message": "Your 12-day streak is at risk. Study now to keep it going!",
      "created_at": "2025-12-21T20:00:00Z",
      "read_at": null,
      "payload": {"streak_count": 12}
    }
  ],
  "unread_count": 3,
  "total_count": 15
}
```

**GET /api/v1/notifications/preferences**
```json
{
  "email_enabled": true,
  "in_app_enabled": true,
  "streak_reminders_enabled": true,
  "milestone_notifications_enabled": true,
  "weekly_summary_enabled": false,
  "reminder_time": "20:00",
  "muted_until": null
}
```

### Frontend Components

**Location:** `apps/web/src/components/notifications/`

```
NotificationBell.tsx          - Header bell icon with unread count badge
NotificationDropdown.tsx      - Dropdown list of notifications
NotificationItem.tsx          - Single notification display
NotificationPreferences.tsx   - Settings page section for preferences
```

### Notification Center Wireframe

```
┌────────────────────────────────────────┐
│ 🔔 (3)                                 │  ← Bell with unread count
├────────────────────────────────────────┤
│ Notifications                          │
├────────────────────────────────────────┤
│ 🔥 Streak at risk!              2h ago │
│    Your 12-day streak is at risk       │
│    [●] unread indicator                │
│                                        │
│ 🎉 Milestone approaching!       1d ago │
│    2 more days to Fortnight Focus      │
│                                        │
│ ✅ Week Warrior earned!         3d ago │
│    You studied 7 days in a row         │
├────────────────────────────────────────┤
│ [Mark all as read]                     │
└────────────────────────────────────────┘
```

### Email Templates

**Location:** SendGrid Dynamic Templates (or inline HTML)

| Template | Subject | Use Case |
|----------|---------|----------|
| `streak_risk` | "Your {streak_count}-day streak is at risk!" | 8pm reminder |
| `streak_warning` | "2 hours left to save your streak!" | 10pm warning |
| `weekly_summary` | "Your LearnR week in review" | Optional weekly digest |

---

## Dependencies

### Requires (Must Complete First)

| Story | Reason |
|-------|--------|
| 11.1 | Streak data for risk detection |

### Integrates With

| Story | Integration Point |
|-------|-------------------|
| 11.3 | Achievement unlock triggers notification |
| 11.4 | Freeze refill triggers notification |
| 11.6 | Goal completion triggers notification |

---

## Testing Requirements

### Unit Tests (`test_notification_service.py`)

1. `test_create_notification` - Notification created in database
2. `test_send_email_enabled` - Email sent when preference enabled
3. `test_send_email_disabled` - Email not sent when preference disabled
4. `test_skip_if_already_studied` - No reminder if studied today
5. `test_skip_if_muted` - No notification during vacation mode
6. `test_skip_if_no_streak` - No reminder if streak is 0
7. `test_deduplication` - Same notification not sent twice per day
8. `test_timezone_conversion` - Correct local time calculated
9. `test_get_user_notifications` - Returns correct notifications
10. `test_mark_as_read` - Updates read_at timestamp
11. `test_unread_count` - Returns correct count

### Integration Tests (`test_notification_api.py`)

1. `test_get_notifications_endpoint` - Returns user's notifications
2. `test_get_unread_count_endpoint` - Returns correct count
3. `test_mark_as_read_endpoint` - Updates notification
4. `test_dismiss_endpoint` - Marks as dismissed
5. `test_get_preferences_endpoint` - Returns correct preferences
6. `test_update_preferences_endpoint` - Preferences saved correctly
7. `test_mark_all_read_endpoint` - All notifications marked read

### Celery Task Tests

1. `test_streak_reminder_task_runs` - Task executes without error
2. `test_reminder_sent_at_correct_time` - 8pm/10pm logic works
3. `test_reminder_respects_timezone` - User timezone used correctly

---

## File Locations Summary

| Component | File Path |
|-----------|-----------|
| NotificationService | `apps/api/src/services/notification_service.py` |
| Notification Schemas | `apps/api/src/schemas/notification.py` |
| Notification Routes | `apps/api/src/routes/notifications.py` |
| Celery Tasks | `apps/api/src/tasks/notification_tasks.py` |
| Celery Config | `apps/api/src/celery_config.py` |
| NotificationBell | `apps/web/src/components/notifications/NotificationBell.tsx` |
| NotificationDropdown | `apps/web/src/components/notifications/NotificationDropdown.tsx` |
| NotificationPreferences | `apps/web/src/components/settings/NotificationPreferences.tsx` |
| Unit Tests | `apps/api/tests/unit/services/test_notification_service.py` |
| Integration Tests | `apps/api/tests/integration/test_notification_api.py` |

---

## Configuration Options

| Parameter | Default | Description |
|-----------|---------|-------------|
| `evening_reminder_hour` | 20 | Evening reminder time (8pm local) |
| `late_warning_hour` | 22 | Late warning time (10pm local) |
| `notification_job_interval_minutes` | 15 | Celery Beat check interval |
| `max_notifications_displayed` | 20 | Notifications in dropdown |
| `notification_retention_days` | 30 | Days to keep old notifications |

---

## Email Configuration

**SendGrid Setup Required:**

| Setting | Value |
|---------|-------|
| API Key | `SENDGRID_API_KEY` env var |
| From Email | `notifications@learnr.com` |
| From Name | `LearnR` |
| Unsubscribe Group | Create for streak reminders |

---

## Phase 2: Push Notifications (Deferred)

The following is deferred to Phase 2:

- PWA Service Worker implementation
- Web Push API integration
- Firebase Cloud Messaging (FCM) setup
- `push_enabled` preference handling
- Browser permission prompts

The `notification_preferences.push_enabled` field and `notifications.sent_push` field are already in the schema for future use.

---

## Notes for SM

1. **MVP Scope:** Email + In-App only - push notifications deferred to Phase 2
2. **Timezone handling critical** - All scheduled times based on user's local timezone
3. **SendGrid configured** - API key needed in environment variables
4. **Celery Beat required** - Ensure celery-beat service is running for scheduled tasks
5. **Deduplication important** - Track sent notifications to prevent spam
6. **Email templates** - Consider using SendGrid Dynamic Templates for better maintainability

---

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-12-22 | 1.1 | Updated for MVP scope: Email + In-App only, push notifications deferred to Phase 2. Simplified tasks, removed push infrastructure dependencies. Added Celery task specifications. | Winston (Architect) |
| 2025-12-21 | 1.0 | Initial SM instructions document | PM (John) |
