# Scrum Master Instructions: Story 11.7 - Gamification Analytics Dashboard (Admin)

**Document Purpose:** Provide the Scrum Master agent with all necessary context to draft the complete story file for Story 11.7.

---

## Quick Reference

| Attribute | Value |
|-----------|-------|
| Story ID | 11.7 |
| Story Title | Gamification Analytics Dashboard (Admin) |
| Epic | Epic 11: Gamification & Motivation System |
| Functional Requirements | FR19.36-FR19.40 (Admin Analytics) |
| Dependencies | Stories 11.1-11.6 (All gamification data), Epic 8 (Admin infrastructure) |
| Priority | LOW (Admin feature, Phase 4) |
| Estimated Complexity | Medium (Analytics aggregation, visualization) |

---

## Source Documents

The Scrum Master should reference these documents when drafting the story:

### Primary Sources

1. **Epic Definition:** `docs/prd/epic-11-gamification-motivation.md`
   - Lines 390-419: Full Story 11.7 specification with acceptance criteria
   - Lines 451-465: Success metrics for gamification
   - Lines 514-530: Rollout strategy (Phase 4)

2. **Admin Stories:** `docs/prd/epic-8.md`
   - Story 8.7: Admin dashboard infrastructure

3. **Functional Requirements:** `docs/prd/functional-requirements.md`
   - FR19.36-FR19.40: Admin analytics requirements

---

## Story Structure Template

Based on the existing story format in `docs/stories/`, the SM should create:

```
docs/stories/11.7-gamification-analytics.story.md
```

### Required Sections

1. **Status** - Set to "Ready for Development"

2. **Story** - User story format
   ```
   As an administrator,
   I want analytics on gamification engagement,
   So that I can tune the system for maximum motivation.
   ```

3. **Acceptance Criteria** - Extract from epic-11-gamification-motivation.md Story 11.7 (7 criteria)

4. **Tasks / Subtasks** - Break down into implementable tasks:
   - Task 1: Create GamificationAnalyticsService
   - Task 2: Implement streak analytics aggregation
   - Task 3: Implement achievement analytics aggregation
   - Task 4: Implement goal analytics aggregation
   - Task 5: Implement engagement correlation calculations
   - Task 6: Create analytics schemas
   - Task 7: Implement admin API endpoints
   - Task 8: Create admin gamification dashboard page
   - Task 9: Implement streak distribution histogram
   - Task 10: Implement achievement unlock charts
   - Task 11: Add time-range filtering
   - Task 12: Add CSV export functionality
   - Task 13: Unit tests
   - Task 14: Integration tests

5. **Dev Notes** - Include:
   - Analytics categories
   - Aggregation strategies
   - Correlation calculations
   - File locations

6. **Testing** - Required test cases from acceptance criteria

7. **Change Log** - Initial entry

---

## Key Implementation Details

### New Service

**GamificationAnalyticsService** - `apps/api/src/services/gamification_analytics.py`

```python
class GamificationAnalyticsService:
    async def get_streak_analytics(
        self,
        date_range: DateRange
    ) -> StreakAnalytics:
        """
        Aggregate streak statistics.

        Returns:
            - streak_distribution: histogram of current streak lengths
            - average_streak: mean streak length
            - median_streak: median streak length
            - streak_survival_rate: % maintaining streak week-over-week
            - freeze_usage_rate: % of available freezes used
            - longest_streaks: top 10 longest current streaks
        """

    async def get_achievement_analytics(
        self,
        date_range: DateRange
    ) -> AchievementAnalytics:
        """
        Aggregate achievement statistics.

        Returns:
            - most_earned: top 5 achievements by earn count
            - least_earned: bottom 5 achievements by earn count
            - time_to_earn: median days to earn each achievement
            - unlock_rate_by_tier: % of users with bronze/silver/gold/platinum
            - recent_unlocks: achievements earned in date range
        """

    async def get_goal_analytics(
        self,
        date_range: DateRange
    ) -> GoalAnalytics:
        """
        Aggregate goal statistics.

        Returns:
            - daily_completion_rate: % of daily goals met
            - weekly_completion_rate: % of weekly goals met
            - common_goal_settings: distribution of goal values
            - goal_vs_actual: average performance relative to goals
        """

    async def get_engagement_correlations(
        self,
        date_range: DateRange
    ) -> EngagementCorrelations:
        """
        Calculate engagement correlations.

        Returns:
            - streak_vs_session_frequency: correlation coefficient
            - achievements_vs_exam_readiness: correlation coefficient
            - goal_setters_retention: retention rate for goal-setters
            - non_goal_setters_retention: retention rate for non-goal-setters
        """

    async def export_analytics_csv(
        self,
        date_range: DateRange,
        analytics_type: str
    ) -> str:
        """Export analytics data as CSV string."""
```

### Analytics Categories

#### Streak Analytics
| Metric | Description | Query |
|--------|-------------|-------|
| Streak Distribution | Histogram: 0, 1-3, 4-7, 8-14, 15-30, 30+ | GROUP BY bucket |
| Average Streak | Mean of current_streak | AVG(current_streak) |
| Survival Rate | % who had streak last week and still have it | Week-over-week comparison |
| Freeze Usage | Used freezes / Total available | SUM(used) / SUM(available) |

#### Achievement Analytics
| Metric | Description | Query |
|--------|-------------|-------|
| Most Earned | Top 5 by count | COUNT GROUP BY achievement_id |
| Time to Earn | Days from signup to earn | earned_at - user.created_at |
| Tier Distribution | % with each tier | COUNT DISTINCT user_id by tier |

#### Goal Analytics
| Metric | Description | Query |
|--------|-------------|-------|
| Completion Rate | Days goal met / Total days | COUNT(met) / COUNT(total) |
| Popular Settings | Distribution of goal values | COUNT GROUP BY goal value |
| Performance Ratio | Actual / Goal average | AVG(actual / goal) |

#### Engagement Correlations
| Correlation | X Axis | Y Axis |
|-------------|--------|--------|
| Streak vs Frequency | Current streak length | Sessions per week |
| Achievements vs Readiness | Achievement count | Exam readiness score |
| Goals vs Retention | Has goals set | D30 retention |

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/admin/gamification/streaks` | GET | Streak analytics |
| `/api/v1/admin/gamification/achievements` | GET | Achievement analytics |
| `/api/v1/admin/gamification/goals` | GET | Goal analytics |
| `/api/v1/admin/gamification/correlations` | GET | Engagement correlations |
| `/api/v1/admin/gamification/export` | GET | CSV export |

### Query Parameters

All endpoints support:
- `range`: `7d`, `30d`, `90d`, `all` (default: `30d`)
- `format`: `json`, `csv` (default: `json`)

### API Response Schema

**GET /api/v1/admin/gamification/streaks**
```json
{
  "date_range": {"start": "2025-11-21", "end": "2025-12-21"},
  "streak_distribution": {
    "0": 150,
    "1-3": 320,
    "4-7": 280,
    "8-14": 120,
    "15-30": 45,
    "30+": 12
  },
  "average_streak": 5.4,
  "median_streak": 4,
  "streak_survival_rate": 0.72,
  "freeze_usage_rate": 0.34,
  "longest_streaks": [
    {"user_id": "uuid", "streak": 67, "started": "2025-10-15"}
  ],
  "total_active_users": 927
}
```

### Key Schemas

**Location:** `apps/api/src/schemas/gamification_analytics.py`

```python
class DateRange(BaseModel):
    start: date
    end: date

class StreakDistribution(BaseModel):
    bucket_0: int
    bucket_1_3: int
    bucket_4_7: int
    bucket_8_14: int
    bucket_15_30: int
    bucket_30_plus: int

class StreakAnalytics(BaseModel):
    date_range: DateRange
    streak_distribution: StreakDistribution
    average_streak: float
    median_streak: int
    streak_survival_rate: float
    freeze_usage_rate: float
    longest_streaks: List[TopStreak]
    total_active_users: int

class AchievementStats(BaseModel):
    achievement_slug: str
    achievement_name: str
    earn_count: int
    median_days_to_earn: float

class AchievementAnalytics(BaseModel):
    date_range: DateRange
    most_earned: List[AchievementStats]
    least_earned: List[AchievementStats]
    tier_distribution: Dict[str, float]  # bronze: 0.65, silver: 0.40, etc.
    total_achievements_earned: int

class GoalAnalytics(BaseModel):
    date_range: DateRange
    daily_completion_rate: float
    weekly_completion_rate: float
    common_daily_questions_goal: int
    common_daily_time_goal: int
    goal_setters_count: int
    non_goal_setters_count: int

class EngagementCorrelations(BaseModel):
    streak_session_correlation: float  # -1 to 1
    achievement_readiness_correlation: float
    goal_setter_retention_d7: float
    non_goal_setter_retention_d7: float
    goal_setter_retention_d30: float
    non_goal_setter_retention_d30: float
```

### Frontend Components

**Location:** `apps/web/src/pages/admin/`

```
GamificationAnalytics.tsx      - Main admin page
├── StreakDistributionChart.tsx   - Histogram
├── AchievementUnlockChart.tsx    - Bar chart
├── GoalCompletionChart.tsx       - Line chart
├── CorrelationCard.tsx           - Metric cards
└── AnalyticsExport.tsx           - Export button
```

### Admin Dashboard Section

```
┌─────────────────────────────────────────────────────────────────┐
│  Gamification Analytics                    [7d] [30d] [90d] [All]│
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  STREAK DISTRIBUTION              ACHIEVEMENT UNLOCK RATE       │
│  ┌─────────────────────┐          ┌─────────────────────┐      │
│  │    ▓▓▓              │          │ Bronze:  65%        │      │
│  │    ▓▓▓▓▓▓           │          │ Silver:  40%        │      │
│  │    ▓▓▓▓▓            │          │ Gold:    15%        │      │
│  │    ▓▓               │          │ Platinum: 3%        │      │
│  │    ▓                │          │                     │      │
│  └─────────────────────┘          └─────────────────────┘      │
│   0  1-3 4-7 8-14 15-30 30+                                     │
│                                                                 │
│  KEY METRICS                                                    │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │ Avg Streak   │ │ Survival %   │ │ Goal Complete│            │
│  │    5.4 days  │ │    72%       │ │    58%       │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
│                                                                 │
│  [Export CSV]                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Dependencies

### Requires (Must Complete First)

| Story | Reason |
|-------|--------|
| 11.1 | Streak data |
| 11.3 | Achievement data |
| 11.4 | Freeze data |
| 11.6 | Goal data |
| 8.7 | Admin dashboard infrastructure |

### Notes

This story is in **Phase 4** of the Epic 11 rollout. All other gamification stories should be complete before this one.

---

## Testing Requirements

### Unit Tests (`test_gamification_analytics.py`)

1. `test_streak_distribution_buckets` - Correct bucket counts
2. `test_average_streak_calculation` - Mean calculated correctly
3. `test_survival_rate_calculation` - Week-over-week comparison correct
4. `test_freeze_usage_rate` - Ratio calculated correctly
5. `test_achievement_ranking` - Most/least earned ordered correctly
6. `test_time_to_earn_calculation` - Median days correct
7. `test_goal_completion_rate` - Rate calculated correctly
8. `test_correlation_coefficient` - Pearson correlation correct
9. `test_date_range_filtering` - Respects date bounds

### Integration Tests (`test_gamification_analytics_api.py`)

1. `test_admin_streak_endpoint` - Returns correct schema
2. `test_admin_achievement_endpoint` - Returns correct schema
3. `test_admin_goals_endpoint` - Returns correct schema
4. `test_admin_correlations_endpoint` - Returns correct schema
5. `test_csv_export` - CSV generated correctly
6. `test_date_range_parameter` - Filtering works
7. `test_non_admin_forbidden` - Non-admins get 403

---

## File Locations Summary

| Component | File Path |
|-----------|-----------|
| GamificationAnalyticsService | `apps/api/src/services/gamification_analytics.py` |
| Analytics Schemas | `apps/api/src/schemas/gamification_analytics.py` |
| Admin Routes | `apps/api/src/routes/admin/gamification.py` |
| GamificationAnalytics Page | `apps/web/src/pages/admin/GamificationAnalytics.tsx` |
| Chart Components | `apps/web/src/components/admin/charts/` |
| Unit Tests | `apps/api/tests/unit/services/test_gamification_analytics.py` |
| Integration Tests | `apps/api/tests/integration/test_gamification_analytics_api.py` |

---

## Performance Considerations

| Query | Target | Strategy |
|-------|--------|----------|
| Streak distribution | <500ms | Index on current_streak |
| Achievement counts | <300ms | COUNT with index |
| Correlation calculation | <2s | Pre-aggregate or limit sample |
| CSV export | <5s | Stream generation |

---

## Notes for SM

1. **Phase 4 story** - Should be implemented after all other Epic 11 stories
2. **Admin-only** - Requires admin authentication
3. **Charting library** - Use Recharts (consistent with Epic 6)
4. **Correlation caveats** - Display correlation != causation disclaimer
5. **Export functionality** - CSV for Excel analysis
6. **Caching opportunity** - Analytics can be cached for 1 hour

---

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-12-21 | 1.0 | Initial SM instructions document | PM (John) |
