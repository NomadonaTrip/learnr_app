# Components

### Frontend Components

1. **Authentication Module** - User auth state, login/logout, JWT refresh, protected routes
2. **Quiz Session Manager** - Session lifecycle, question navigation, answer submission
3. **Reading Library Manager** - Async reading queue, filters, engagement tracking
4. **Dashboard & Analytics Viewer** - Progress visualization, competency bars, trends
5. **Competency Visualizer** - Chart rendering, progress animations
6. **Reading Badge Component** - Navigation badge with unread count and priority indicator

### Reading Badge UI Pattern

**Purpose:** Display unread reading queue count in navigation with silent updates (zero-interruption learning flow).

**Component Location:** `apps/web/src/components/layout/Navigation.tsx` or `ReadingBadge.tsx`

**Visual Design:**

```
┌─────────────────────────────┐
│  Navigation                  │
│  [Dashboard] [Quiz] [Reading│ 7] [Settings]
│                         └─┬─┘
│                   Badge: count + priority
└─────────────────────────────┘
```

**Badge States:**

| State | Count | Priority | Visual | Example |
|-------|-------|----------|--------|---------|
| **Empty** | 0 | N/A | No badge shown | `Reading Library` |
| **Low/Medium** | 1-10 | None high | Blue badge, white text | `Reading Library [3]` |
| **High Priority** | 1-10 | ≥1 high | Red/orange badge, white text | `Reading Library [7]` |
| **Many Items** | 10+ | Any | Badge with "10+" | `Reading Library [10+]` |

**TypeScript Interface:**

```typescript
interface ReadingBadgeProps {
  count: number;
  hasHighPriority: boolean;
  className?: string;
}

interface ReadingBadgeState {
  count: number;
  hasHighPriority: boolean;
  previousCount: number; // For animation
}
```

**Implementation Example:**

```tsx
// apps/web/src/components/layout/ReadingBadge.tsx
import { useReadingQueue } from '@/hooks/useReadingQueue';
import { useEffect, useState } from 'react';

export function ReadingBadge() {
  const { unreadCount, hasHighPriority } = useReadingQueue();
  const [shouldPulse, setShouldPulse] = useState(false);

  // Pulse animation when count increases (silent notification)
  useEffect(() => {
    if (unreadCount > 0) {
      setShouldPulse(true);
      const timer = setTimeout(() => setShouldPulse(false), 1000);
      return () => clearTimeout(timer);
    }
  }, [unreadCount]);

  if (unreadCount === 0) return null;

  const displayCount = unreadCount > 10 ? '10+' : unreadCount.toString();
  const badgeColor = hasHighPriority
    ? 'bg-error-500 text-white' // High priority: red/orange
    : 'bg-primary-500 text-white'; // Normal: blue

  return (
    <span
      className={`
        inline-flex items-center justify-center
        min-w-[24px] h-[24px] px-2
        text-xs font-semibold
        rounded-full
        ${badgeColor}
        ${shouldPulse ? 'animate-pulse-subtle' : ''}
        transition-all duration-200
      `}
      aria-label={`${unreadCount} unread reading items${hasHighPriority ? ', including high priority' : ''}`}
      role="status"
    >
      {displayCount}
    </span>
  );
}
```

**Navigation Integration:**

```tsx
// apps/web/src/components/layout/Navigation.tsx
import { ReadingBadge } from './ReadingBadge';

export function Navigation() {
  return (
    <nav className="navigation">
      <NavLink to="/dashboard">Dashboard</NavLink>
      <NavLink to="/quiz">Quiz</NavLink>
      <NavLink to="/reading" className="flex items-center gap-2">
        Reading Library
        <ReadingBadge />
      </NavLink>
      <NavLink to="/settings">Settings</NavLink>
    </nav>
  );
}
```

**State Management (Zustand Store):**

```typescript
// apps/web/src/stores/readingStore.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface ReadingState {
  unreadCount: number;
  hasHighPriority: boolean;
  updateBadge: (count: number, hasHigh: boolean) => void;
}

export const useReadingStore = create<ReadingState>()(
  persist(
    (set) => ({
      unreadCount: 0,
      hasHighPriority: false,
      updateBadge: (count, hasHigh) => set({ unreadCount: count, hasHighPriority: hasHigh }),
    }),
    {
      name: 'reading-badge-storage',
    }
  )
);
```

**Silent Badge Updates (Background Service):**

```typescript
// apps/web/src/services/readingQueueService.ts
import { useReadingStore } from '@/stores/readingStore';

export async function syncReadingBadge() {
  // Called after answer submission (background)
  const response = await fetch('/api/v1/reading-queue/summary');
  const data = await response.json();

  // Update badge silently (no toast, no modal, no interruption)
  useReadingStore.getState().updateBadge(
    data.unread_count,
    data.has_high_priority
  );
}

// Hook into answer submission workflow
export async function submitAnswer(questionId: string, answer: string) {
  const response = await fetch(`/api/v1/questions/${questionId}/answer`, {
    method: 'POST',
    body: JSON.stringify({ answer }),
  });

  // Background sync (non-blocking)
  syncReadingBadge();

  return response.json();
}
```

**API Endpoint for Badge Data:**

```
GET /api/v1/reading-queue/summary
```

**Response:**
```json
{
  "unread_count": 7,
  "has_high_priority": true,
  "priority_breakdown": {
    "high": 2,
    "medium": 3,
    "low": 2
  }
}
```

**Accessibility:**

- Badge has `aria-label` with full description
- `role="status"` announces updates to screen readers
- Color is supplemental; count is primary indicator (colorblind-friendly)
- High priority communicated via text in `aria-label`, not just color

**Animation (Tailwind Config):**

```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      keyframes: {
        'pulse-subtle': {
          '0%, 100%': { transform: 'scale(1)', opacity: '1' },
          '50%': { transform: 'scale(1.1)', opacity: '0.9' },
        },
      },
      animation: {
        'pulse-subtle': 'pulse-subtle 1s ease-in-out',
      },
    },
  },
};
```

**Dashboard Widget (Optional):**

Display top 3 high-priority reading items on dashboard:

```tsx
// apps/web/src/components/dashboard/ReadingWidget.tsx
export function ReadingWidget() {
  const { topPriorityItems } = useReadingQueue();

  if (topPriorityItems.length === 0) return null;

  return (
    <div className="reading-widget card">
      <h3>Recommended Reading</h3>
      <ul className="space-y-2">
        {topPriorityItems.slice(0, 3).map((item) => (
          <li key={item.id} className="flex items-center gap-3">
            <Badge priority={item.priority} />
            <div>
              <p className="font-medium">{item.title}</p>
              <p className="text-sm text-gray-600">
                {item.knowledge_area} · {item.estimated_read_time_minutes} min
              </p>
            </div>
          </li>
        ))}
      </ul>
      <Button as={Link} to="/reading" variant="secondary" size="sm">
        View All Reading →
      </Button>
    </div>
  );
}
```

**Key Benefits:**

1. **Zero Interruption:** Badge updates silently in background (no popups/toasts during quiz)
2. **Priority Awareness:** Visual indicator (color) for high-priority items
3. **Engagement Signal:** Subtle pulse animation draws attention without disrupting flow
4. **Accessibility:** Screen reader friendly with descriptive labels

### Knowledge Area Detail View

**Purpose:** Provide deep-dive analytics into user's performance on a specific knowledge area (KA) when they click a competency bar on dashboard.

**Trigger:** User clicks/taps any of the 6 KA competency bars on dashboard

**Implementation:** Modal dialog or dedicated page (`/knowledge-area/{ka-slug}`)

**Data Requirements:**

```typescript
interface KADetailView {
  knowledge_area: KnowledgeArea;
  current_competency: number; // 0-100
  target_competency: number; // From user onboarding
  gap: number; // target - current
  confidence: number; // 0-1 (IRT uncertainty)

  // Performance breakdown
  total_questions_answered: number;
  correct_count: number;
  recent_accuracy: number; // Last 10 questions

  // Concept-level gaps
  concept_gaps: Array<{
    concept_tag: string;
    competency: number;
    questions_answered: number;
    last_correct: boolean;
  }>;

  // Recent performance
  recent_questions: Array<{
    question_id: string;
    text: string; // Truncated
    is_correct: boolean;
    answered_at: string;
    difficulty: number;
  }>;

  // Time tracking
  total_time_spent_minutes: number;
  avg_time_per_question_seconds: number;

  // Recommendations
  recommended_difficulty: number; // Next questions should be difficulty X
  recommended_reading_chunks: Array<ReadingChunk>;
}
```

**API Endpoint:**

```
GET /api/v1/knowledge-areas/{ka_slug}/detail
```

**Response Example:**
```json
{
  "knowledge_area": "Business Analysis Planning and Monitoring",
  "current_competency": 68,
  "target_competency": 80,
  "gap": 12,
  "confidence": 0.75,
  "total_questions_answered": 42,
  "correct_count": 28,
  "recent_accuracy": 0.70,
  "concept_gaps": [
    {
      "concept_tag": "Stakeholder Analysis",
      "competency": 55,
      "questions_answered": 8,
      "last_correct": false
    },
    {
      "concept_tag": "Business Analysis Planning",
      "competency": 72,
      "questions_answered": 12,
      "last_correct": true
    }
  ],
  "recent_questions": [ /* Last 10 questions */ ],
  "total_time_spent_minutes": 78,
  "avg_time_per_question_seconds": 65,
  "recommended_difficulty": 3
}
```

**UI Layout:**

```
┌────────────────────────────────────────────────────────┐
│  Business Analysis Planning and Monitoring          [X]│
├────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────────────────────────────────────┐  │
│  │  Current Competency:  68%  ▓▓▓▓▓▓▓▓░░░░ (75% confidence) │
│  │  Target Competency:   80%  ▓▓▓▓▓▓▓▓▓▓▓░              │
│  │  Gap:                 12 points                     │
│  └─────────────────────────────────────────────────┘  │
│                                                         │
│  Performance Summary                                   │
│  • 42 questions answered (28 correct, 67%)            │
│  • Recent accuracy: 70% (last 10 questions)           │
│  • 78 minutes spent on this knowledge area            │
│                                                         │
│  Concept-Level Gaps                                    │
│  ┌─────────────────────────────────────────────────┐  │
│  │ Stakeholder Analysis            55%  [Weak]     │  │
│  │   └─ 8 questions answered, last: incorrect      │  │
│  │ Business Analysis Planning      72%  [Good]     │  │
│  │   └─ 12 questions answered, last: correct       │  │
│  │ ...                                              │  │
│  └─────────────────────────────────────────────────┘  │
│                                                         │
│  Recent Performance (Last 10 Questions)                │
│  ┌─────────────────────────────────────────────────┐  │
│  │ ✓ Nov 21, 2:30pm - Medium difficulty             │  │
│  │ ✗ Nov 21, 2:28pm - Hard difficulty               │  │
│  │ ✓ Nov 21, 2:25pm - Easy difficulty               │  │
│  │ ...                                              │  │
│  └─────────────────────────────────────────────────┘  │
│                                                         │
│  Recommended Reading                                   │
│  [Reading chunk cards with "Add to Queue" button]     │
│                                                         │
│  ┌─────────────────────────────────────────────────┐  │
│  │  [Study This Knowledge Area]  [Close]            │  │
│  └─────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────┘
```

**Component Implementation:**

```tsx
// apps/web/src/pages/KnowledgeAreaDetailPage.tsx
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { CompetencyBar } from '@/components/dashboard/CompetencyBar';
import { ConceptGapList } from '@/components/ka-detail/ConceptGapList';
import { RecentPerformance } from '@/components/ka-detail/RecentPerformance';
import { RecommendedReading } from '@/components/ka-detail/RecommendedReading';

export function KnowledgeAreaDetailPage() {
  const { kaSlug } = useParams<{ kaSlug: string }>();
  const { data, isLoading } = useQuery({
    queryKey: ['ka-detail', kaSlug],
    queryFn: () => fetch(`/api/v1/knowledge-areas/${kaSlug}/detail`).then(r => r.json()),
  });

  if (isLoading) return <Loading />;

  const {
    knowledge_area,
    current_competency,
    target_competency,
    gap,
    confidence,
    concept_gaps,
    recent_questions,
    total_questions_answered,
    correct_count,
    recent_accuracy,
  } = data;

  return (
    <div className="ka-detail-page">
      <header>
        <h1>{knowledge_area}</h1>
        <button aria-label="Close" onClick={() => navigate(-1)}>×</button>
      </header>

      <section className="competency-summary">
        <CompetencyBar
          label="Current Competency"
          value={current_competency}
          max={100}
          confidence={confidence}
        />
        <CompetencyBar
          label="Target Competency"
          value={target_competency}
          max={100}
          variant="target"
        />
        <div className="gap-indicator">
          Gap: <strong>{gap} points</strong>
        </div>
      </section>

      <section className="performance-summary">
        <h2>Performance Summary</h2>
        <ul>
          <li>{total_questions_answered} questions answered ({correct_count} correct, {Math.round((correct_count / total_questions_answered) * 100)}%)</li>
          <li>Recent accuracy: {Math.round(recent_accuracy * 100)}% (last 10 questions)</li>
        </ul>
      </section>

      <section className="concept-gaps">
        <h2>Concept-Level Gaps</h2>
        <ConceptGapList gaps={concept_gaps} />
      </section>

      <section className="recent-performance">
        <h2>Recent Performance (Last 10 Questions)</h2>
        <RecentPerformance questions={recent_questions} />
      </section>

      <section className="recommended-reading">
        <h2>Recommended Reading</h2>
        <RecommendedReading knowledgeArea={kaSlug} />
      </section>

      <footer className="actions">
        <Button onClick={() => startFocusedSession(kaSlug)}>
          Study This Knowledge Area
        </Button>
        <Button variant="secondary" onClick={() => navigate(-1)}>
          Close
        </Button>
      </footer>
    </div>
  );
}
```

**Focused Session Logic:**

When user clicks "Study This Knowledge Area", start a quiz session filtered to only that KA:

```typescript
// apps/web/src/services/quizService.ts
export async function startFocusedSession(knowledgeArea: string) {
  const response = await fetch('/api/v1/sessions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_type: 'focused',
      knowledge_area_filter: knowledgeArea,
    }),
  });

  const session = await response.json();
  return session;
}
```

**Backend Endpoint:**

```python
# apps/api/src/routes/knowledge_areas.py
from fastapi import APIRouter, Depends
from src.services.analytics_service import AnalyticsService
from src.dependencies import get_current_user

router = APIRouter(prefix="/knowledge-areas", tags=["knowledge_areas"])

@router.get("/{ka_slug}/detail")
async def get_ka_detail(
    ka_slug: str,
    user = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(),
):
    """
    Get detailed analytics for a specific knowledge area.

    Returns:
    - Current competency
    - Target competency
    - Concept-level breakdown
    - Recent performance
    - Recommended reading
    """
    ka_name = slug_to_ka_name(ka_slug)

    return await analytics_service.get_ka_detail(user.id, ka_name)
```

**Accessibility:**

- Competency bars use `role="progressbar"` with `aria-valuenow`, `aria-valuemin`, `aria-valuemax`
- Recent performance list uses semantic `<ul>` with checkmark/X icons that have `aria-label`
- "Study This Knowledge Area" button has clear focus indicator
- Modal is keyboard accessible (Esc to close, Tab navigation)

**Mobile Optimization:**

- Modal becomes full-screen on mobile (< 768px)
- Collapsible sections for concept gaps and recent performance
- Swipeable recent performance timeline (optional enhancement)

---

### Backend Components

6. **API Gateway (FastAPI)** - Request routing, auth middleware, rate limiting, CORS
7. **Authentication Service** - Password hashing, JWT generation/validation, token refresh
8. **Adaptive Engine** - Question selection (IRT), competency updates, gap analysis
9. **Spaced Repetition Engine** - SM-2 algorithm, review scheduling
10. **Reading Queue Service** - Semantic search, priority calculation, async population
11. **Session Management Service** - Session CRUD, response tracking, review orchestration
12. **Data Access Layer** - Repository pattern for PostgreSQL and Qdrant
13. **Vector Search Service** - Qdrant integration, embedding generation
14. **LLM Service** - OpenAI API integration, rate limiting, cost tracking
15. **Background Job Worker** - Celery tasks for async operations

---
