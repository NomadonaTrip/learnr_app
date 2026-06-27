# Scrum Master Instructions: Story 11.3 - Achievement Badges and Milestones

**Document Purpose:** Provide the Scrum Master agent with all necessary context to draft the complete story file for Story 11.3.

---

## Quick Reference

| Attribute | Value |
|-----------|-------|
| Story ID | 11.3 |
| Story Title | Achievement Badges and Milestones |
| Epic | Epic 11: Gamification & Motivation System |
| Functional Requirements | FR19.13-FR19.18 (Achievements) |
| Dependencies | Story 11.1 (Streak data), Epic 4 (Quiz data), Epic 5 (Reading data) |
| Priority | MEDIUM (Engagement feature) |
| Estimated Complexity | Medium-High (Service, database, frontend gallery) |

---

## Source Documents

The Scrum Master should reference these documents when drafting the story:

### Primary Sources

1. **Epic Definition:** `docs/prd/epic-11-gamification-motivation.md`
   - Lines 228-273: Full Story 11.3 specification with acceptance criteria
   - Lines 59-75: Database schema (achievements, user_achievements tables)
   - Lines 105-133: Achievement seed data (16 achievements)
   - Lines 489-498: Achievement badge wireframe

2. **Functional Requirements:** `docs/prd/functional-requirements.md`
   - FR19.13-FR19.18: Achievement system requirements

---

## Story Structure Template

Based on the existing story format in `docs/stories/`, the SM should create:

```
docs/stories/11.3-achievement-badges.story.md
```

### Required Sections

1. **Status** - Set to "Ready for Development"

2. **Story** - User story format
   ```
   As a user progressing through my studies,
   I want to earn achievement badges for milestones,
   So that I feel rewarded for my accomplishments.
   ```

3. **Acceptance Criteria** - Extract from epic-11-gamification-motivation.md Story 11.3 (8 criteria)

4. **Tasks / Subtasks** - Break down into implementable tasks:
   - Task 1: Create database migration for `achievements` table
   - Task 2: Create database migration for `user_achievements` table
   - Task 3: Seed 16 achievement definitions
   - Task 4: Create AchievementService
   - Task 5: Implement achievement checking logic
   - Task 6: Create achievement unlock triggers
   - Task 7: Create achievement schemas
   - Task 8: Implement API endpoints (3 endpoints)
   - Task 9: Create achievement toast notification component
   - Task 10: Create achievement gallery page
   - Task 11: Implement tier-based styling (bronze/silver/gold/platinum)
   - Task 12: Unit tests
   - Task 13: Integration tests

5. **Dev Notes** - Include:
   - Dependencies and sequencing
   - Achievement categories and types
   - Trigger points for checking
   - Tier visual styling
   - File locations

6. **Testing** - Required test cases from acceptance criteria

7. **Change Log** - Initial entry

---

## Key Implementation Details

### New Service

**AchievementService** - `apps/api/src/services/achievement_service.py`
```python
class AchievementService:
    async def check_and_award_achievements(
        self,
        user_id: UUID,
        trigger: str
    ) -> List[Achievement]:
        """
        Check all relevant achievements and award any newly earned.

        Triggers:
        - 'quiz_complete': Check question count, perfect session
        - 'reading_complete': Check reading count
        - 'streak_update': Check streak milestones
        - 'coverage_update': Check mastery achievements

        Returns list of newly earned achievements for notification.
        """

    async def get_all_achievements(self) -> List[Achievement]:
        """Get all available achievements."""

    async def get_user_achievements(self, user_id: UUID) -> List[UserAchievement]:
        """Get user's earned achievements."""

    async def mark_notified(self, user_id: UUID, achievement_id: UUID) -> None:
        """Mark achievement as notified (toast shown)."""

    def _check_streak_achievements(self, streak: int) -> List[str]:
        """Check which streak achievements are earned."""

    def _check_volume_achievements(self, questions: int) -> List[str]:
        """Check which volume achievements are earned."""

    def _check_mastery_achievements(self, mastered: int, ka_scores: dict) -> List[str]:
        """Check which mastery achievements are earned."""

    def _check_special_achievements(self, session_data: dict) -> List[str]:
        """Check special achievements (perfect session, comeback, time-based)."""
```

### Achievement Categories

| Category | Achievements | Trigger |
|----------|--------------|---------|
| Streak | streak_3, streak_7, streak_14, streak_30, streak_60 | streak_update |
| Volume | questions_50, questions_250, questions_500, questions_1000 | quiz_complete |
| Mastery | mastery_10, mastery_50, mastery_100, mastery_all_ka | coverage_update |
| Special | perfect_session, comeback, night_owl, early_bird | various |

### Achievement Seed Data (from Epic)

```sql
-- Streak achievements
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
('early_bird', 'Early Bird', 'Complete a session before 7am', 'special', 'sun', 'bronze', 'time_based', 7)
```

### API Endpoints

| Endpoint | Description |
|----------|-------------|
| GET `/api/v1/achievements` | All available achievements |
| GET `/api/v1/achievements/earned` | User's earned achievements |
| POST `/api/v1/achievements/{id}/notify` | Mark achievement as notified |

### API Response Schema

```json
{
  "achievements": [
    {
      "id": "uuid",
      "slug": "streak_7",
      "name": "Week Warrior",
      "description": "Study 7 days in a row",
      "category": "streak",
      "icon": "flame",
      "tier": "bronze",
      "earned": true,
      "earned_at": "2025-12-15T10:30:00Z"
    }
  ],
  "total_earned": 5,
  "total_available": 16
}
```

### Key Schemas

**Location:** `apps/api/src/schemas/achievement.py`

```python
class Achievement(BaseModel):
    id: UUID
    slug: str
    name: str
    description: str
    category: str  # 'streak', 'volume', 'mastery', 'special'
    icon: str
    tier: str  # 'bronze', 'silver', 'gold', 'platinum'
    requirement_type: str
    requirement_value: int
    is_active: bool

class UserAchievement(BaseModel):
    achievement: Achievement
    earned_at: datetime
    notified: bool

class AchievementUnlock(BaseModel):
    achievement: Achievement
    is_new: bool  # For notification purposes
```

### Frontend Components

**Location:** `apps/web/src/components/achievements/`

```
AchievementToast.tsx      - Unlock notification
AchievementBadge.tsx      - Single badge display
AchievementGallery.tsx    - Full achievements page
AchievementFilter.tsx     - Category filter
```

### Tier Visual Styling

| Tier | Border | Effect |
|------|--------|--------|
| Bronze | Copper (#B87333) | None |
| Silver | Silver (#C0C0C0) | Subtle shine |
| Gold | Gold (#FFD700) | Glow effect |
| Platinum | Rainbow gradient | Iridescent shimmer |

### Achievement Badge Wireframe (from Epic)

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

---

## Dependencies

### Requires (Must Complete First)

| Story/Component | Reason |
|-----------------|--------|
| 11.1 | Streak data for streak achievements |
| Epic 4 | Question count for volume achievements |
| Epic 5 | Reading count data |
| Story 4.5 | Mastery data for mastery achievements |

### Integrates With

| Story | Integration Point |
|-------|-------------------|
| 11.2 | Next milestone shown in streak widget |
| 11.5 | Achievement unlock triggers notification |

---

## Testing Requirements

### Unit Tests (`test_achievement_service.py`)

1. `test_streak_achievement_awarded` - Streak milestone triggers award
2. `test_volume_achievement_awarded` - Question count triggers award
3. `test_mastery_achievement_awarded` - Concept mastery triggers award
4. `test_special_perfect_session` - 100% accuracy session triggers award
5. `test_no_duplicate_awards` - Same achievement not awarded twice
6. `test_multiple_achievements_at_once` - Batch awards work
7. `test_all_ka_threshold` - Well-Rounded achievement logic

### Integration Tests (`test_achievement_api.py`)

1. `test_get_all_achievements` - Returns 16 achievements
2. `test_get_earned_achievements` - Returns user's earned only
3. `test_mark_notified` - Updates notification status
4. `test_achievement_after_quiz` - Award triggered by quiz completion

### Frontend Tests

1. `test_achievement_toast_renders` - Toast shows on unlock
2. `test_gallery_displays_all` - Gallery shows earned + locked
3. `test_tier_styling_applied` - Correct colors per tier
4. `test_filter_by_category` - Category filter works

---

## File Locations Summary

| Component | File Path |
|-----------|-----------|
| AchievementService | `apps/api/src/services/achievement_service.py` |
| Achievement Schemas | `apps/api/src/schemas/achievement.py` |
| Achievement Routes | `apps/api/src/routes/achievements.py` |
| Database Migration | `apps/api/alembic/versions/xxxx_add_achievement_tables.py` |
| Seed Data | `apps/api/alembic/versions/xxxx_seed_achievements.py` |
| AchievementToast | `apps/web/src/components/achievements/AchievementToast.tsx` |
| AchievementGallery | `apps/web/src/pages/Achievements.tsx` |
| Unit Tests | `apps/api/tests/unit/services/test_achievement_service.py` |
| Integration Tests | `apps/api/tests/integration/test_achievement_api.py` |

---

## Configuration Options

| Parameter | Default | Description |
|-----------|---------|-------------|
| `achievement_toast_duration` | 5000 | Toast display time (ms) |
| `achievement_confetti_enabled` | true | Show confetti on unlock |

---

## Notes for SM

1. **Seed data required** - 16 achievements must be inserted
2. **Multiple trigger points** - Achievement check called from quiz, reading, streak
3. **Tier styling important** - Visual distinction for motivation
4. **Toast animation** - Use Framer Motion for celebration effect
5. **Consider caching** - Achievement definitions rarely change

---

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-12-21 | 1.0 | Initial SM instructions document | PM (John) |
