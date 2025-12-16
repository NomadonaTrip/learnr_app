# Components

## Status

**ALIGNED** with BKT Architecture (bkt-architecture.md)

---

### Frontend Components

1. **Authentication Module** - User auth state, login/logout, JWT refresh, protected routes
2. **Quiz Session Manager** - Session lifecycle, BKT question navigation, answer submission with belief updates
3. **Reading Library Manager** - Async reading queue linked to gap concepts, filters, engagement tracking
4. **Dashboard & Analytics Viewer** - KA-level progress bars (aggregated from beliefs), coverage summary
5. **Coverage Visualizer** - Heatmap, gap analysis panel, concept-level belief display
6. **Belief Update Indicator** - Shows users how answers affect their knowledge (simplified view)
7. **Reading Badge Component** - Navigation badge with unread count and priority indicator

---

### BKT Coverage Components

#### Coverage Heatmap

**Purpose:** Visual representation of concept mastery across the corpus (optional advanced view).

**Component Location:** `apps/web/src/components/coverage/CoverageHeatmap.tsx`

```tsx
interface CoverageHeatmapProps {
  beliefs: BeliefState[];
  onConceptClick: (conceptId: string) => void;
}

export function CoverageHeatmap({ beliefs, onConceptClick }: CoverageHeatmapProps) {
  const getColor = (belief: BeliefState) => {
    const mean = belief.alpha / (belief.alpha + belief.beta);
    const confidence = (belief.alpha + belief.beta) / (belief.alpha + belief.beta + 10);

    if (confidence < 0.7) return 'gray';      // Uncertain
    if (mean >= 0.8) return 'green';          // Mastered
    if (mean <= 0.5) return 'red';            // Gap
    return 'yellow';                          // Borderline
  };

  return (
    <div className="heatmap-grid">
      {beliefs.map((belief) => (
        <div
          key={belief.concept_id}
          className="concept-cell"
          style={{ backgroundColor: getColor(belief) }}
          onClick={() => onConceptClick(belief.concept_id)}
          aria-label={`${belief.concept_name}: ${Math.round(belief.mean * 100)}% mastery`}
        />
      ))}
    </div>
  );
}
```

**Color Legend:**
| Color | Status | Criteria |
|-------|--------|----------|
| Green | Mastered | mean ≥ 0.8, confidence ≥ 0.7 |
| Red | Gap | mean ≤ 0.5, confidence ≥ 0.7 |
| Yellow | Borderline | 0.5 < mean < 0.8, confidence ≥ 0.7 |
| Gray | Uncertain | confidence < 0.7 |

---

#### Gap Analysis Panel

**Purpose:** Display identified knowledge gaps sorted by priority for focused study.

**Component Location:** `apps/web/src/components/coverage/GapAnalysis.tsx`

```tsx
interface GapAnalysisProps {
  gaps: ConceptStatus[];
  onFocusGap: (conceptId: string) => void;
}

export function GapAnalysis({ gaps, onFocusGap }: GapAnalysisProps) {
  // Sort gaps by priority (lowest mastery × highest confidence)
  const sortedGaps = [...gaps].sort((a, b) => {
    const priorityA = (1 - a.probability) * a.confidence;
    const priorityB = (1 - b.probability) * b.confidence;
    return priorityB - priorityA;
  });

  return (
    <div className="gap-analysis">
      <h2>Focus Areas ({gaps.length} gaps identified)</h2>
      <p className="description">
        These concepts need attention. We're confident you haven't mastered them yet.
      </p>
      <ul className="gap-list">
        {sortedGaps.map((gap) => (
          <li key={gap.concept_id} className="gap-item">
            <ConceptCard
              concept={gap}
              onAction={() => onFocusGap(gap.concept_id)}
              actionLabel="Practice This"
            />
          </li>
        ))}
      </ul>
    </div>
  );
}
```

---

#### Belief Update Indicator

**Purpose:** Show users (in simplified terms) how their answer affected their knowledge.

**Component Location:** `apps/web/src/components/quiz/BeliefUpdateIndicator.tsx`

```tsx
interface BeliefUpdateIndicatorProps {
  updates: BeliefUpdate[];
  isCorrect: boolean;
}

export function BeliefUpdateIndicator({ updates, isCorrect }: BeliefUpdateIndicatorProps) {
  const conceptsAffected = updates.length;

  return (
    <div className={`belief-indicator ${isCorrect ? 'positive' : 'negative'}`}>
      {isCorrect ? (
        <span>
          <CheckIcon /> Strengthened understanding of {conceptsAffected} concept{conceptsAffected !== 1 ? 's' : ''}
        </span>
      ) : (
        <span>
          <InfoIcon /> Identified area for review: {updates[0]?.concept_name}
        </span>
      )}
    </div>
  );
}
```

**Design Principle:** BKT complexity is hidden from users. They see friendly messages like "Strengthened 3 concepts" instead of "Updated α from 3.2 to 4.1".

---

#### Knowledge Area Progress Bar

**Purpose:** Display user-facing progress for each of the 6 Knowledge Areas (aggregated from beliefs).

**Component Location:** `apps/web/src/components/coverage/KnowledgeAreaProgress.tsx`

```tsx
interface KnowledgeAreaProgressProps {
  knowledgeArea: string;
  masteredCount: number;
  totalConcepts: number;
  readinessScore: number; // 0-100
}

export function KnowledgeAreaProgress({
  knowledgeArea,
  masteredCount,
  totalConcepts,
  readinessScore,
}: KnowledgeAreaProgressProps) {
  return (
    <div className="ka-progress">
      <div className="ka-header">
        <h3>{knowledgeArea}</h3>
        <span className="readiness">{readinessScore}% Ready</span>
      </div>
      <div
        className="progress-bar"
        role="progressbar"
        aria-valuenow={readinessScore}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`${knowledgeArea}: ${readinessScore}% ready`}
      >
        <div
          className="progress-fill"
          style={{ width: `${readinessScore}%` }}
        />
      </div>
      <p className="concept-count">
        {masteredCount} of {totalConcepts} concepts mastered
      </p>
    </div>
  );
}
```

---

### Reading Badge UI Pattern

**Purpose:** Display unread reading queue count in navigation with silent updates (zero-interruption learning flow).

**Component Location:** `apps/web/src/components/layout/ReadingBadge.tsx`

**Visual Design:**

```
┌─────────────────────────────────┐
│  Navigation                      │
│  [Dashboard] [Quiz] [Reading│ 7] [Settings]
│                           └─┬─┘
│                     Badge: count + priority
└─────────────────────────────────┘
```

**Badge States:**

| State | Count | Priority | Visual | Example |
|-------|-------|----------|--------|---------|
| **Empty** | 0 | N/A | No badge shown | `Reading Library` |
| **Low/Medium** | 1-10 | None high | Blue badge, white text | `Reading Library [3]` |
| **High Priority** | 1-10 | ≥1 high | Red/orange badge, white text | `Reading Library [7]` |
| **Many Items** | 10+ | Any | Badge with "10+" | `Reading Library [10+]` |

**Implementation:**

```tsx
export function ReadingBadge() {
  const { unreadCount, hasHighPriority } = useReadingQueue();
  const [shouldPulse, setShouldPulse] = useState(false);

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
    ? 'bg-error-500 text-white'
    : 'bg-primary-500 text-white';

  return (
    <span
      className={`badge ${badgeColor} ${shouldPulse ? 'animate-pulse-subtle' : ''}`}
      aria-label={`${unreadCount} unread reading items${hasHighPriority ? ', including high priority' : ''}`}
      role="status"
    >
      {displayCount}
    </span>
  );
}
```

---

### Knowledge Area Detail View

**Purpose:** Provide deep-dive analytics into user's performance on a specific knowledge area when they click a progress bar on dashboard.

**Trigger:** User clicks/taps any of the 6 KA progress bars on dashboard

**Component Location:** `apps/web/src/pages/KnowledgeAreaDetailPage.tsx`

**Data Requirements:**

```typescript
interface KADetailView {
  knowledge_area: KnowledgeArea;
  readiness_score: number; // 0-100 (aggregated from beliefs)
  total_concepts: number;
  mastered_count: number;
  gap_count: number;
  uncertain_count: number;

  // Concept-level breakdown
  concept_beliefs: Array<{
    concept_id: string;
    concept_name: string;
    probability: number; // mean
    confidence: number;
    status: 'mastered' | 'gap' | 'borderline' | 'uncertain';
    response_count: number;
  }>;

  // Recent performance
  recent_questions: Array<{
    question_id: string;
    text: string;
    is_correct: boolean;
    answered_at: string;
    concepts_tested: string[];
  }>;

  // Recommendations
  top_gaps: ConceptStatus[];
  recommended_reading: ReadingChunk[];
}
```

**API Endpoint:**

```
GET /api/v1/coverage/by-knowledge-area/{ka_slug}
```

**UI Layout:**

```
┌────────────────────────────────────────────────────────┐
│  Business Analysis Planning and Monitoring          [X]│
├────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────────────────────────────────────┐  │
│  │  Readiness Score:  71%  ▓▓▓▓▓▓▓▓░░░░            │  │
│  │  145 of 203 concepts mastered                    │  │
│  │  28 gaps identified • 30 need more data          │  │
│  └─────────────────────────────────────────────────┘  │
│                                                         │
│  Top Gaps to Address                                   │
│  ┌─────────────────────────────────────────────────┐  │
│  │ Stakeholder Analysis        32%  [Practice]     │  │
│  │ BA Planning Approach        41%  [Practice]     │  │
│  │ Governance Planning         45%  [Practice]     │  │
│  └─────────────────────────────────────────────────┘  │
│                                                         │
│  Recent Performance (Last 10 Questions)                │
│  ┌─────────────────────────────────────────────────┐  │
│  │ ✓ Nov 21, 2:30pm - Stakeholder Mapping          │  │
│  │ ✗ Nov 21, 2:28pm - BA Planning                  │  │
│  │ ✓ Nov 21, 2:25pm - Requirements Management      │  │
│  └─────────────────────────────────────────────────┘  │
│                                                         │
│  Recommended Reading                                   │
│  [Reading chunk cards linked to gap concepts]         │
│                                                         │
│  ┌─────────────────────────────────────────────────┐  │
│  │  [Study This Knowledge Area]  [Close]            │  │
│  └─────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────┘
```

**Focused Session Logic:**

When user clicks "Study This Knowledge Area", start a quiz session filtered to only that KA with prerequisite-first strategy:

```typescript
export async function startFocusedSession(knowledgeArea: string) {
  const response = await fetch('/api/v1/sessions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_type: 'focused',
      question_strategy: 'prerequisite_first',
      knowledge_area_filter: knowledgeArea,
    }),
  });
  return response.json();
}
```

---

### Backend Components

1. **API Gateway (FastAPI)** - Request routing, auth middleware, rate limiting, CORS
2. **Authentication Service** - Password hashing, JWT generation/validation, token refresh
3. **BKT Engine Services:**
   - **BeliefUpdater** - Bayesian belief updates after each response
   - **QuestionSelector** - Optimal question selection (max info gain, prerequisite-first, etc.)
   - **CoverageAnalyzer** - Coverage reports, gap identification, mastery classification
4. **Reading Queue Service** - Semantic search, gap-based priority calculation, async population
5. **Session Management Service** - Session CRUD, response tracking, concurrency handling
6. **Data Access Layer:**
   - **BeliefRepository** - Belief state CRUD with row-level locking
   - **ConceptRepository** - Concept DAG traversal, prerequisite lookups
   - **QuestionRepository** - Question retrieval with concept mappings
   - **ResponseRepository** - Response storage with belief update snapshots
7. **Vector Search Service** - Qdrant integration, embedding generation, concept matching
8. **LLM Service** - OpenAI API integration, rate limiting, cost tracking
9. **Background Job Worker** - Celery tasks for async operations (prerequisite propagation, reading queue)

---

### Component Interactions

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                              │
├─────────────────────────────────────────────────────────────┤
│  Dashboard                                                   │
│  ├── KnowledgeAreaProgress (×6)  ←── useCoverageByKA()      │
│  └── ReadingWidget              ←── useReadingQueue()       │
│                                                              │
│  Quiz                                                        │
│  ├── QuestionCard               ←── useQuiz().getNext()     │
│  ├── AnswerFeedback             ←── useQuiz().submit()      │
│  └── BeliefUpdateIndicator      ←── response.belief_updates │
│                                                              │
│  Coverage                                                    │
│  ├── CoverageSummary            ←── useCoverageSummary()    │
│  ├── CoverageHeatmap            ←── useBeliefs()            │
│  └── GapAnalysis                ←── useGaps()               │
│                                                              │
│  Navigation                                                  │
│  └── ReadingBadge               ←── useReadingStore()       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        BACKEND                               │
├─────────────────────────────────────────────────────────────┤
│  Routes                                                      │
│  ├── /beliefs      → BeliefRepository                       │
│  ├── /coverage     → CoverageAnalyzer                       │
│  ├── /quiz         → QuestionSelector + BeliefUpdater       │
│  └── /reading      → ReadingQueueService                    │
│                                                              │
│  Services                                                    │
│  ├── BeliefUpdater     ─── Bayesian update logic            │
│  ├── QuestionSelector  ─── Info gain calculation            │
│  └── CoverageAnalyzer  ─── Classification logic             │
│                                                              │
│  Repositories                                                │
│  ├── BeliefRepository  → belief_states table                │
│  ├── ConceptRepository → concepts + prerequisites           │
│  └── QuestionRepository → questions + question_concepts     │
└─────────────────────────────────────────────────────────────┘
```

---

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-12-03 | 2.0 | Aligned with BKT Architecture - added coverage components, belief update indicator, BKT backend services | Winston (Architect) |
| 2025-11-01 | 1.0 | Initial components | Original |
