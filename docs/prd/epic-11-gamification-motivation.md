# Epic 11: Gamification & Motivation System

**Epic Goal:** Implement a comprehensive gamification system featuring daily study streaks, achievement badges, milestone rewards, and motivational notifications to drive consistent user engagement and long-term retention through the exam preparation journey.

**Key Capabilities:**
- **Daily Streaks:** Track consecutive study days with visual progress
- **Achievement Badges:** Reward milestones and accomplishments
- **Streak Protection:** Grace periods and freeze options to maintain momentum
- **Motivational Notifications:** Timely reminders to protect streaks
- **Study Goals:** Daily/weekly targets with progress tracking

**Business Context:**
- Gamification drives 2-3x engagement in learning apps (Duolingo, Khan Academy)
- Streaks create powerful habit loops (commitment + reward)
- Loss aversion (protecting streaks) is a stronger motivator than gain seeking
- Social proof via achievements increases perceived value

---

## Database Schema

### New Tables

```sql
-- Daily study activity tracking
CREATE TABLE study_streaks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    current_streak INT NOT NULL DEFAULT 0,
    longest_streak INT NOT NULL DEFAULT 0,
    last_activity_date DATE,
    streak_frozen_until DATE,  -- Null if not frozen
    freeze_count_used INT NOT NULL DEFAULT 0,
    freeze_count_available INT NOT NULL DEFAULT 2,  -- Monthly allowance
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(user_id)
);

CREATE INDEX idx_study_streaks_user ON study_streaks(user_id);
CREATE INDEX idx_study_streaks_activity ON study_streaks(last_activity_date);

-- Daily activity log (for streak calculation)
CREATE TABLE daily_activity (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    activity_date DATE NOT NULL,
    questions_answered INT NOT NULL DEFAULT 0,
    reading_completed INT NOT NULL DEFAULT 0,
    study_time_seconds INT NOT NULL DEFAULT 0,
    qualifies_for_streak BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, activity_date)
);

CREATE INDEX idx_daily_activity_user_date ON daily_activity(user_id, activity_date);

-- Achievement definitions
CREATE TABLE achievements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(50) NOT NULL,  -- 'streak', 'mastery', 'volume', 'special'
    icon VARCHAR(50) NOT NULL,  -- Icon identifier for frontend
    tier VARCHAR(20) NOT NULL DEFAULT 'bronze',  -- 'bronze', 'silver', 'gold', 'platinum'
    requirement_type VARCHAR(50) NOT NULL,  -- 'streak_days', 'questions_answered', 'concepts_mastered', etc.
    requirement_value INT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_achievements_category ON achievements(category);
CREATE INDEX idx_achievements_active ON achievements(is_active);

-- User achievements (earned badges)
CREATE TABLE user_achievements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    achievement_id UUID NOT NULL REFERENCES achievements(id) ON DELETE CASCADE,
    earned_at TIMESTAMP NOT NULL DEFAULT NOW(),
    notified BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE(user_id, achievement_id)
);

CREATE INDEX idx_user_achievements_user ON user_achievements(user_id);
CREATE INDEX idx_user_achievements_earned ON user_achievements(earned_at);

-- Streak notifications (for scheduled reminders)
CREATE TABLE streak_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    notification_type VARCHAR(50) NOT NULL,  -- 'streak_risk', 'streak_lost', 'milestone', 'achievement'
    scheduled_for TIMESTAMP NOT NULL,
    sent_at TIMESTAMP,
    dismissed_at TIMESTAMP,
    payload JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_streak_notifications_pending ON streak_notifications(user_id, scheduled_for)
    WHERE sent_at IS NULL;
```

### Schema for Achievements (Seed Data)

```sql
-- Streak achievements
INSERT INTO achievements (slug, name, description, category, icon, tier, requirement_type, requirement_value) VALUES
('streak_3', 'Getting Started', 'Study 3 days in a row', 'streak', 'flame', 'bronze', 'streak_days', 3),
('streak_7', 'Week Warrior', 'Study 7 days in a row', 'streak', 'flame', 'bronze', 'streak_days', 7),
('streak_14', 'Fortnight Focus', 'Study 14 days in a row', 'streak', 'flame', 'silver', 'streak_days', 14),
('streak_30', 'Monthly Master', 'Study 30 days in a row', 'streak', 'flame', 'gold', 'streak_days', 30),
('streak_60', 'Exam Ready', 'Study 60 days in a row', 'streak', 'flame', 'platinum', 'streak_days', 60),

-- Volume achievements
('questions_50', 'First Fifty', 'Answer 50 questions', 'volume', 'target', 'bronze', 'questions_answered', 50),
('questions_250', 'Question Hunter', 'Answer 250 questions', 'volume', 'target', 'silver', 'questions_answered', 250),
('questions_500', 'Quiz Champion', 'Answer 500 questions', 'volume', 'target', 'gold', 'questions_answered', 500),
('questions_1000', 'Knowledge Seeker', 'Answer 1000 questions', 'volume', 'target', 'platinum', 'questions_answered', 1000),

-- Mastery achievements
('mastery_10', 'First Concepts', 'Master 10 concepts', 'mastery', 'brain', 'bronze', 'concepts_mastered', 10),
('mastery_50', 'Building Expertise', 'Master 50 concepts', 'mastery', 'brain', 'silver', 'concepts_mastered', 50),
('mastery_100', 'Domain Expert', 'Master 100 concepts', 'mastery', 'brain', 'gold', 'concepts_mastered', 100),
('mastery_all_ka', 'Well-Rounded', 'Reach 70%+ in all 6 KAs', 'mastery', 'star', 'gold', 'all_ka_threshold', 70),

-- Special achievements
('perfect_session', 'Perfect Session', 'Answer 10+ questions with 100% accuracy', 'special', 'trophy', 'gold', 'perfect_session', 10),
('comeback', 'Comeback Kid', 'Return after 7+ days and complete a session', 'special', 'refresh', 'silver', 'comeback_days', 7),
('night_owl', 'Night Owl', 'Complete a session after 10pm', 'special', 'moon', 'bronze', 'time_based', 22),
('early_bird', 'Early Bird', 'Complete a session before 7am', 'special', 'sun', 'bronze', 'time_based', 7);
```

---

## Stories

### Story 11.1: Daily Streak Tracking and Calculation

**As a** user studying consistently,
**I want** my daily study streaks tracked automatically,
**So that** I can see my commitment and stay motivated.

**Acceptance Criteria:**

1. Create `StreakService` in `apps/api/src/services/streak_service.py`
2. **Streak qualification rules:**
   ```python
   def qualifies_for_streak(activity: DailyActivity) -> bool:
       """
       A day qualifies for streak if user completes ANY of:
       - 5+ quiz questions answered
       - 10+ minutes of study time
       - 3+ reading materials completed
       """
       return (
           activity.questions_answered >= 5 or
           activity.study_time_seconds >= 600 or  # 10 minutes
           activity.reading_completed >= 3
       )
   ```
3. **Streak calculation logic:**
   ```python
   def update_streak(user_id: UUID, activity_date: date) -> StreakUpdate:
       """
       Called after each qualifying activity.

       Rules:
       - Same day activity: No change to streak count
       - Next consecutive day: Increment streak
       - Gap of 1 day (yesterday missed): Streak breaks (unless frozen)
       - Gap of 2+ days: Streak resets to 1
       """
   ```
4. Streak updates in real-time after quiz answer or reading completion
5. `last_activity_date` updated on each qualifying activity
6. `longest_streak` updated when `current_streak` exceeds it
7. Timezone handling: Use user's configured timezone (default UTC)
8. API endpoint: GET `/api/v1/streaks` returns current streak data
9. API endpoint: GET `/api/v1/streaks/history` returns last 30 days
10. Performance: Streak calculation in <50ms

**Technical Notes:**
- Use database transaction for streak + activity update
- Consider race condition if user has multiple devices
- Daily activity aggregated from `quiz_responses` and `reading_queue`

---

### Story 11.2: Streak Visualization on Dashboard

**As a** user viewing my dashboard,
**I want** to see my current streak prominently displayed,
**So that** I'm motivated to maintain and extend it.

**Acceptance Criteria:**

1. Dashboard displays streak widget with:
   - Current streak count (large, prominent number)
   - Flame icon (animated if streak > 7 days)
   - "day" / "days" label
   - Longest streak comparison: "Personal best: X days"
2. Streak calendar showing last 7-14 days:
   - Green checkmark for qualifying days
   - Gray circle for non-qualifying days
   - Today highlighted with special indicator
3. Color coding based on streak length:
   - 1-6 days: Orange flame
   - 7-13 days: Red flame
   - 14-29 days: Blue flame
   - 30+ days: Purple/gold flame
4. Streak milestone progress:
   - "3 more days to Week Warrior badge!"
   - Progress bar to next milestone
5. Mobile responsive (streak visible on all screen sizes)
6. Accessibility: Screen reader announces streak count
7. Animation: Flame flickers, number increments on new streak day
8. Loading state while fetching streak data

**UI Components:**
- `StreakWidget` - Main dashboard widget
- `StreakCalendar` - 7-14 day history view
- `StreakMilestone` - Next milestone progress

---

### Story 11.3: Achievement Badges and Milestones

**As a** user progressing through my studies,
**I want** to earn achievement badges for milestones,
**So that** I feel rewarded for my accomplishments.

**Acceptance Criteria:**

1. Create `AchievementService` in `apps/api/src/services/achievement_service.py`
2. Achievement checking triggered after:
   - Quiz session completion
   - Reading completion
   - Daily streak update
   - Coverage update
3. **Achievement categories:**
   - Streak: 3, 7, 14, 30, 60 day milestones
   - Volume: 50, 250, 500, 1000 questions
   - Mastery: 10, 50, 100 concepts mastered
   - Special: Perfect session, comeback, time-based
4. Achievement unlock flow:
   ```python
   async def check_and_award_achievements(user_id: UUID, trigger: str) -> List[Achievement]:
       """
       Check all relevant achievements and award any newly earned.
       Returns list of newly earned achievements for notification.
       """
   ```
5. Achievement toast notification on unlock:
   - Badge icon + name
   - Confetti animation
   - "View all achievements" link
6. Achievement gallery page: `/achievements`
   - Grid of all achievements (earned + locked)
   - Locked shown as grayscale with requirements
   - Filter by category
   - Sort by date earned or category
7. API endpoints:
   - GET `/api/v1/achievements` - All available achievements
   - GET `/api/v1/achievements/earned` - User's earned achievements
   - POST `/api/v1/achievements/{id}/notify` - Mark as notified
8. Achievement tier styling:
   - Bronze: Copper border
   - Silver: Silver border + shine
   - Gold: Gold border + glow
   - Platinum: Rainbow/iridescent effect

---

### Story 11.4: Streak Protection (Freeze Feature)

**As a** user who may miss a day occasionally,
**I want** the option to freeze my streak,
**So that** life events don't destroy my progress.

**Acceptance Criteria:**

1. **Streak freeze mechanics:**
   - Users get 2 streak freezes per month (reset on 1st)
   - Freeze can be activated proactively OR retroactively (within 24h)
   - Frozen day doesn't count toward streak but doesn't break it
   - Maximum freeze duration: 1 day per freeze
2. API endpoints:
   - POST `/api/v1/streaks/freeze` - Activate freeze for today/yesterday
   - GET `/api/v1/streaks/freezes` - Remaining freezes this month
3. Freeze UI:
   - "Freeze Streak" button in streak widget
   - Confirmation dialog explaining freeze
   - Visual indicator on frozen days (snowflake icon)
   - Remaining freezes count displayed
4. **Retroactive freeze (grace period):**
   - If user logs in after missing a day (streak would break)
   - Prompt: "You missed yesterday! Use a streak freeze to save your X-day streak?"
   - One-click freeze activation
   - 24-hour window to apply retroactive freeze
5. Freeze refill notification on 1st of month
6. Premium consideration (Phase 2): Additional freezes for premium users

**Business Rules:**
- Cannot freeze future days
- Cannot freeze if already studied that day
- Freeze doesn't contribute to streak count
- Longest streak excludes frozen days

---

### Story 11.5: Streak Risk Notifications

**As a** user who might forget to study,
**I want** timely reminders when my streak is at risk,
**So that** I don't accidentally lose my progress.

**Acceptance Criteria:**

1. **Notification triggers:**
   - Evening reminder (8pm local): "Don't forget to study today! 🔥"
   - Late night warning (10pm local): "Your X-day streak ends in 2 hours!"
   - Streak broken (next day): "Your streak ended. Start a new one today!"
   - Milestone approaching: "2 more days to your 7-day badge!"
2. **Notification channels:**
   - In-app notification (always)
   - Email (opt-in, daily digest option)
   - Push notification (PWA, if enabled)
3. **Notification preferences:**
   - User can enable/disable each notification type
   - User can set preferred reminder time
   - User can mute for X days (vacation mode)
4. API endpoints:
   - GET `/api/v1/notifications/preferences`
   - PUT `/api/v1/notifications/preferences`
   - POST `/api/v1/notifications/{id}/dismiss`
5. Notification scheduling:
   - Background job checks at-risk streaks hourly
   - Respects user timezone
   - Deduplication (don't spam multiple reminders)
6. Smart notifications:
   - Don't remind if user already studied today
   - Increase urgency as deadline approaches
   - Celebrate milestones prominently
7. Notification center:
   - Bell icon in header with unread count
   - Dropdown showing recent notifications
   - Mark all as read functionality

---

### Story 11.6: Study Goals and Progress Tracking

**As a** user setting personal targets,
**I want** to set daily and weekly study goals,
**So that** I can pace my preparation appropriately.

**Acceptance Criteria:**

1. **Goal types:**
   - Daily questions goal (default: 10)
   - Daily study time goal (default: 15 minutes)
   - Weekly questions goal (default: 50)
   - Weekly mastery goal (default: 5 concepts)
2. Goal setting UI in settings:
   - Slider or input for each goal type
   - Suggested goals based on exam date
   - "Recommended for your timeline" indicator
3. Goal progress on dashboard:
   - Circular progress ring showing daily completion
   - "8/10 questions today" text
   - Color changes as goal approached (gray → orange → green)
4. Weekly summary:
   - End-of-week email/notification
   - Goals met vs. missed
   - Comparison to previous week
5. API endpoints:
   - GET `/api/v1/goals` - Current goals and progress
   - PUT `/api/v1/goals` - Update goal settings
   - GET `/api/v1/goals/history` - Weekly goal history
6. Goal completion celebration:
   - Confetti/animation when daily goal met
   - Bonus XP or badge for consistent goal completion
7. Adaptive goal suggestions:
   - "You've exceeded your goal 5 days in a row. Increase to 15?"
   - "You're behind schedule. Consider 20 questions/day to catch up"

---

### Story 11.7: Gamification Analytics Dashboard (Admin)

**As an** administrator,
**I want** analytics on gamification engagement,
**So that** I can tune the system for maximum motivation.

**Acceptance Criteria:**

1. Admin dashboard section: `/admin/gamification`
2. **Streak analytics:**
   - Distribution of current streaks (histogram)
   - Average streak length
   - Streak survival rate (% maintaining streak week-over-week)
   - Freeze usage rate
3. **Achievement analytics:**
   - Most/least earned achievements
   - Time to earn each achievement (median)
   - Achievement unlock rate by tier
4. **Goal analytics:**
   - Goal completion rates (daily/weekly)
   - Most common goal settings
   - Goal vs. actual performance
5. **Engagement correlations:**
   - Streak length vs. session frequency
   - Achievements earned vs. exam readiness
   - Goal-setters vs. non-goal-setters retention
6. Export capability for deeper analysis
7. Time-range filtering (7d, 30d, 90d, all-time)

---

## Dependencies

```
Epic 11 Story Dependencies:

11.1 (Streak Tracking) → 11.2 (Visualization), 11.4 (Freeze), 11.5 (Notifications)
11.1 → 11.3 (Achievements) - Streak achievements depend on streak data
11.3 (Achievements) → 11.2 (Visualization) - Show next badge milestone
11.6 (Goals) → 11.2 (Visualization) - Show goal progress on dashboard
All stories → 11.7 (Analytics)

External Dependencies:

From Epic 4:
- Quiz session completion events (trigger achievement check)
- Questions answered count

From Epic 5:
- Reading completion events

From Epic 6:
- Dashboard infrastructure

From Epic 1:
- User timezone preference
- Notification infrastructure
```

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| 7-day streak rate | >40% | % of active users with 7+ day streak |
| 30-day streak rate | >15% | % of active users with 30+ day streak |
| Streak freeze usage | 20-40% | % of freezes used (too low = not needed, too high = too easy) |
| Achievement unlock rate | >60% | % of users with 3+ achievements |
| Goal completion rate | >50% | % of daily goals met |
| DAU/MAU ratio | >0.3 | Daily active / monthly active (engagement) |
| Notification open rate | >25% | % of streak notifications acted upon |
| Retention (D7) | +20% | Improvement vs. pre-gamification |
| Retention (D30) | +30% | Improvement vs. pre-gamification |

---

## UI/UX Specifications

### Streak Widget (Dashboard)

```
┌─────────────────────────────────────────────┐
│  🔥  12                                     │
│      days                                   │
│                                             │
│  ○ ○ ● ● ● ● ● ● ● ● ● ● ● ◐              │
│  Personal best: 18 days                     │
│                                             │
│  ━━━━━━━━━━━━━━━━━░░░░░░  2 days to        │
│                          Fortnight Focus!   │
│                                             │
│  [❄️ Freeze Available: 2]                   │
└─────────────────────────────────────────────┘
```

### Achievement Badge

```
┌─────────────┐
│   🏆        │  ← Icon (tier-colored border)
│             │
│ Week Warrior│  ← Name
│ 7-day streak│  ← Description
│             │
│ Earned 12/15│  ← Date earned
└─────────────┘
```

### Goal Progress Ring

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

## Rollout Strategy

### Phase 1: Core Streaks (Stories 11.1, 11.2)
- Streak tracking backend
- Dashboard visualization
- Basic streak calculation

### Phase 2: Engagement (Stories 11.3, 11.5)
- Achievement system
- Notifications

### Phase 3: Retention (Stories 11.4, 11.6)
- Streak freeze feature
- Study goals

### Phase 4: Optimization (Story 11.7)
- Admin analytics
- A/B testing different thresholds

---

## Configuration Parameters

```python
GAMIFICATION_CONFIG = {
    # Streak qualification thresholds
    "streak_min_questions": 5,
    "streak_min_study_seconds": 600,  # 10 minutes
    "streak_min_readings": 3,

    # Streak freeze
    "monthly_freeze_allowance": 2,
    "retroactive_freeze_window_hours": 24,

    # Notifications
    "evening_reminder_hour": 20,  # 8pm local
    "late_warning_hour": 22,  # 10pm local

    # Goals (defaults)
    "default_daily_questions": 10,
    "default_daily_study_minutes": 15,
    "default_weekly_questions": 50,

    # Achievement thresholds (see seed data above)
}
```

---

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-12-21 | 1.0 | Initial epic creation with 7 stories | PM (John) |
