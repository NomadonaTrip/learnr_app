# Scrum Master Instructions: Story 11.2 - Streak Visualization on Dashboard

**Document Purpose:** Provide the Scrum Master agent with all necessary context to draft the complete story file for Story 11.2.

---

## Quick Reference

| Attribute | Value |
|-----------|-------|
| Story ID | 11.2 |
| Story Title | Streak Visualization on Dashboard |
| Epic | Epic 11: Gamification & Motivation System |
| Functional Requirements | FR19.9-FR19.12 (Streak Display) |
| Dependencies | Story 11.1 (Streak Tracking), Story 6.1 (Dashboard) |
| Priority | HIGH (Core user-facing feature) |
| Estimated Complexity | Medium (Frontend components, animations) |

---

## Source Documents

The Scrum Master should reference these documents when drafting the story:

### Primary Sources

1. **Epic Definition:** `docs/prd/epic-11-gamification-motivation.md`
   - Lines 191-226: Full Story 11.2 specification with acceptance criteria
   - Lines 469-484: UI/UX specifications with ASCII wireframe
   - Lines 514-530: Rollout strategy (Phase 1)

2. **Dashboard Story:** `docs/prd/epic-6.md`
   - Story 6.1: Dashboard infrastructure for widget placement

3. **Design Tokens:** `docs/prd/prd.md`
   - UI Design Goals section: Color palettes, typography, spacing

---

## Story Structure Template

Based on the existing story format in `docs/stories/`, the SM should create:

```
docs/stories/11.2-streak-visualization.story.md
```

### Required Sections

1. **Status** - Set to "Ready for Development"

2. **Story** - User story format
   ```
   As a user viewing my dashboard,
   I want to see my current streak prominently displayed,
   So that I'm motivated to maintain and extend it.
   ```

3. **Acceptance Criteria** - Extract from epic-11-gamification-motivation.md Story 11.2 (8 criteria)

4. **Tasks / Subtasks** - Break down into implementable tasks:
   - Task 1: Create StreakWidget component
   - Task 2: Create StreakCalendar component (7-14 day history)
   - Task 3: Create StreakMilestone component (next badge progress)
   - Task 4: Implement flame icon with tier-based colors
   - Task 5: Add flame animation for 7+ day streaks
   - Task 6: Implement streak data hook (useStreak)
   - Task 7: Add loading state
   - Task 8: Add accessibility attributes
   - Task 9: Mobile responsive styling
   - Task 10: Unit tests (component rendering)
   - Task 11: Visual regression tests

5. **Dev Notes** - Include:
   - Dependencies and sequencing
   - Component hierarchy
   - Animation specifications
   - Color coding rules
   - File locations

6. **Testing** - Required test cases from acceptance criteria

7. **Change Log** - Initial entry

---

## Key Implementation Details

### Frontend Components

**Location:** `apps/web/src/components/dashboard/`

```
StreakWidget.tsx          - Main dashboard widget
├── StreakFlame.tsx       - Animated flame icon
├── StreakCalendar.tsx    - 7-14 day history view
└── StreakMilestone.tsx   - Next milestone progress
```

### Component Specifications

#### StreakWidget
```tsx
interface StreakWidgetProps {
  currentStreak: number;
  longestStreak: number;
  todayQualifies: boolean;
  freezeAvailable: number;
  history: DailyActivity[];
  nextMilestone: MilestoneProgress;
}
```

#### StreakCalendar
```tsx
interface StreakCalendarProps {
  history: DailyActivity[];  // Last 7-14 days
  today: Date;
}

// Visual representation:
// ○ = non-qualifying day (gray)
// ● = qualifying day (green)
// ◐ = today (highlighted, pending)
```

#### StreakMilestone
```tsx
interface MilestoneProgress {
  currentStreak: number;
  nextMilestone: number;  // 3, 7, 14, 30, 60
  milestoneName: string;  // "Week Warrior"
  daysRemaining: number;
  progressPercent: number;
}
```

### Color Coding Rules

| Streak Length | Flame Color | CSS Variable |
|---------------|-------------|--------------|
| 1-6 days | Orange | `--streak-orange` |
| 7-13 days | Red | `--streak-red` |
| 14-29 days | Blue | `--streak-blue` |
| 30+ days | Purple/Gold | `--streak-platinum` |

### Animation Specifications

| Animation | Trigger | Duration | Easing |
|-----------|---------|----------|--------|
| Flame flicker | Always (7+ days) | 2s loop | ease-in-out |
| Number increment | New streak day | 500ms | spring |
| Milestone celebration | Milestone reached | 1.5s | ease-out |

### Wireframe (from Epic)

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

### Custom Hook

**Location:** `apps/web/src/hooks/useStreak.ts`

```typescript
interface UseStreakReturn {
  streak: StreakData | null;
  history: DailyActivity[];
  nextMilestone: MilestoneProgress;
  isLoading: boolean;
  error: Error | null;
  refetch: () => void;
}

function useStreak(): UseStreakReturn {
  // Fetches from GET /api/v1/streaks and /api/v1/streaks/history
  // Calculates next milestone locally
  // Caches data with SWR or React Query
}
```

---

## Dependencies

### Requires (Must Complete First)

| Story | Reason |
|-------|--------|
| 11.1 | Streak API endpoints for data |
| 6.1 | Dashboard infrastructure |

### Integrates With

| Story | Integration Point |
|-------|-------------------|
| 11.3 | Milestone badges link to achievements |
| 11.4 | Freeze button triggers freeze modal |

---

## Testing Requirements

### Unit Tests (`StreakWidget.test.tsx`)

1. `test_streak_widget_renders` - Widget displays with data
2. `test_streak_count_displayed` - Current streak number visible
3. `test_longest_streak_displayed` - Personal best shown
4. `test_calendar_days_correct` - History dots match data
5. `test_today_highlighted` - Today indicator visible
6. `test_milestone_progress_shown` - Progress bar accurate
7. `test_freeze_count_displayed` - Freeze availability shown

### Visual Tests

1. `test_flame_orange_under_7` - Orange for 1-6 days
2. `test_flame_red_7_to_13` - Red for 7-13 days
3. `test_flame_blue_14_to_29` - Blue for 14-29 days
4. `test_flame_platinum_30_plus` - Purple/gold for 30+ days

### Accessibility Tests

1. `test_screen_reader_streak_count` - Streak announced
2. `test_keyboard_navigation` - Focusable elements
3. `test_color_contrast` - WCAG AA compliance

---

## File Locations Summary

| Component | File Path |
|-----------|-----------|
| StreakWidget | `apps/web/src/components/dashboard/StreakWidget.tsx` |
| StreakFlame | `apps/web/src/components/dashboard/StreakFlame.tsx` |
| StreakCalendar | `apps/web/src/components/dashboard/StreakCalendar.tsx` |
| StreakMilestone | `apps/web/src/components/dashboard/StreakMilestone.tsx` |
| useStreak Hook | `apps/web/src/hooks/useStreak.ts` |
| Streak Types | `apps/web/src/types/streak.ts` |
| Unit Tests | `apps/web/src/components/dashboard/__tests__/StreakWidget.test.tsx` |

---

## Accessibility Requirements

1. **Screen reader:** "Current streak: 12 days. Personal best: 18 days."
2. **Calendar:** Each day announced with date and status
3. **Progress bar:** Percentage announced
4. **Flame icon:** Decorative (aria-hidden)
5. **Freeze button:** Clear label "Use streak freeze"

---

## Mobile Responsive Design

| Breakpoint | Layout |
|------------|--------|
| Desktop (>1024px) | Full widget with calendar |
| Tablet (768-1024px) | Compact calendar (7 days) |
| Mobile (<768px) | Streak count + milestone only |

---

## Notes for SM

1. **Depends on Story 11.1** - Cannot start until streak API exists
2. **Animation library** - Use Framer Motion (already in stack)
3. **Data fetching** - Use existing SWR/React Query pattern
4. **Design consistency** - Follow Framer-inspired design from Epic 6
5. **Dashboard placement** - Coordinate with dashboard layout (Story 6.1)

---

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-12-21 | 1.0 | Initial SM instructions document | PM (John) |
