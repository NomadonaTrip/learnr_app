# Frontend Architecture

## Status

**ALIGNED** with BKT Architecture (bkt-architecture.md)

---

## Component Organization

```
apps/web/src/
├── components/           # Reusable UI components
│   ├── coverage/         # BKT coverage visualization components
│   │   ├── CoverageHeatmap.tsx
│   │   ├── GapAnalysis.tsx
│   │   ├── ConceptCard.tsx
│   │   └── KnowledgeAreaProgress.tsx
│   ├── quiz/             # Quiz flow components
│   │   ├── QuestionCard.tsx
│   │   ├── AnswerFeedback.tsx
│   │   └── BeliefUpdateIndicator.tsx
│   └── common/           # Shared UI primitives
├── pages/               # Page-level components (routes)
│   ├── Dashboard.tsx    # KA-level progress bars (aggregated beliefs)
│   ├── Coverage.tsx     # Detailed concept-level coverage view
│   ├── Quiz.tsx         # Adaptive quiz with BKT question selection
│   └── Gaps.tsx         # Gap analysis with concept details
├── hooks/               # Custom React hooks
│   ├── useBeliefs.ts    # Fetch/cache belief states
│   ├── useCoverage.ts   # Coverage report data
│   └── useQuiz.ts       # Quiz session state
├── services/            # API client services
│   ├── beliefService.ts # Belief state API calls
│   ├── coverageService.ts
│   └── quizService.ts
├── stores/              # Zustand state stores
│   ├── authStore.ts
│   ├── beliefStore.ts   # Local belief state cache
│   └── quizStore.ts
├── utils/               # Utility functions
│   ├── beliefMath.ts    # Frontend Beta distribution calculations
│   └── coverage.ts      # Coverage aggregation helpers
├── types/               # Frontend-specific types
│   ├── belief.ts        # BeliefState, ConceptStatus types
│   └── coverage.ts      # CoverageReport types
└── styles/              # Global styles
```

---

## BKT UI Components

### Coverage Visualization

**Design Principle:** BKT complexity is system-internal. Users see familiar KA-level progress (6 bars). The intelligence is invisible; the benefits (smarter questions, faster progress) are obvious.

#### Dashboard Progress (User-Facing)

Users see aggregated progress by Knowledge Area:

```tsx
// apps/web/src/components/coverage/KnowledgeAreaProgress.tsx
interface KnowledgeAreaProgressProps {
  knowledgeArea: string;
  masteredCount: number;
  totalConcepts: number;
  readinessScore: number; // 0-100, derived from beliefs
}

export function KnowledgeAreaProgress({
  knowledgeArea,
  masteredCount,
  totalConcepts,
  readinessScore,
}: KnowledgeAreaProgressProps) {
  return (
    <div className="ka-progress">
      <h3>{knowledgeArea}</h3>
      <ProgressBar value={readinessScore} max={100} />
      <span className="readiness">{readinessScore}% Ready</span>
      {/* Concept-level detail hidden from users */}
    </div>
  );
}
```

#### Coverage Heatmap (Advanced View)

For users who want deeper insight (optional advanced view):

```tsx
// apps/web/src/components/coverage/CoverageHeatmap.tsx
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
        />
      ))}
    </div>
  );
}
```

#### Gap Analysis Panel

```tsx
// apps/web/src/components/coverage/GapAnalysis.tsx
interface GapAnalysisProps {
  gaps: ConceptStatus[];
  onFocusGap: (conceptId: string) => void;
}

export function GapAnalysis({ gaps, onFocusGap }: GapAnalysisProps) {
  // Sort gaps by priority (lowest mastery first, highest confidence)
  const sortedGaps = [...gaps].sort((a, b) => {
    const priorityA = (1 - a.probability) * a.confidence;
    const priorityB = (1 - b.probability) * b.confidence;
    return priorityB - priorityA;
  });

  return (
    <div className="gap-analysis">
      <h2>Focus Areas ({gaps.length} gaps identified)</h2>
      <ul>
        {sortedGaps.map((gap) => (
          <li key={gap.concept_id}>
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

### Quiz Flow Components

#### Belief Update Indicator

Show users how their answer affected their knowledge map:

```tsx
// apps/web/src/components/quiz/BeliefUpdateIndicator.tsx
interface BeliefUpdateIndicatorProps {
  updates: BeliefUpdate[];
  isCorrect: boolean;
}

export function BeliefUpdateIndicator({ updates, isCorrect }: BeliefUpdateIndicatorProps) {
  // Simplified user-facing message
  const conceptsAffected = updates.length;

  return (
    <div className={`belief-indicator ${isCorrect ? 'positive' : 'negative'}`}>
      {isCorrect ? (
        <span>Strengthened understanding of {conceptsAffected} concept(s)</span>
      ) : (
        <span>Identified area for review: {updates[0]?.concept_name}</span>
      )}
    </div>
  );
}
```

---

## State Management

### Zustand Stores

**Key Stores:**
- `authStore` - User, tokens, authentication state (persisted)
- `beliefStore` - Cached belief states for quick access
- `quizStore` - Current quiz session, question, strategy

#### Belief Store

```typescript
// apps/web/src/stores/beliefStore.ts
import { create } from 'zustand';
import { BeliefState, CoverageReport } from '../types/belief';

interface BeliefStore {
  beliefs: Map<string, BeliefState>;
  coverage: CoverageReport | null;
  lastFetched: Date | null;

  // Actions
  setBeliefs: (beliefs: BeliefState[]) => void;
  updateBelief: (conceptId: string, alpha: number, beta: number) => void;
  setCoverage: (coverage: CoverageReport) => void;
  invalidate: () => void;
}

export const useBeliefStore = create<BeliefStore>((set) => ({
  beliefs: new Map(),
  coverage: null,
  lastFetched: null,

  setBeliefs: (beliefs) => set({
    beliefs: new Map(beliefs.map(b => [b.concept_id, b])),
    lastFetched: new Date(),
  }),

  updateBelief: (conceptId, alpha, beta) => set((state) => {
    const newBeliefs = new Map(state.beliefs);
    const existing = newBeliefs.get(conceptId);
    if (existing) {
      newBeliefs.set(conceptId, { ...existing, alpha, beta });
    }
    return { beliefs: newBeliefs };
  }),

  setCoverage: (coverage) => set({ coverage }),

  invalidate: () => set({ lastFetched: null }),
}));
```

#### Quiz Store

```typescript
// apps/web/src/stores/quizStore.ts
import { create } from 'zustand';

type QuestionStrategy = 'max_info_gain' | 'max_uncertainty' | 'prerequisite_first';

interface QuizStore {
  sessionId: string | null;
  currentQuestion: Question | null;
  strategy: QuestionStrategy;
  questionsAnswered: number;

  // Actions
  startSession: (sessionId: string) => void;
  setQuestion: (question: Question) => void;
  setStrategy: (strategy: QuestionStrategy) => void;
  incrementAnswered: () => void;
  endSession: () => void;
}

export const useQuizStore = create<QuizStore>((set) => ({
  sessionId: null,
  currentQuestion: null,
  strategy: 'max_info_gain',
  questionsAnswered: 0,

  startSession: (sessionId) => set({ sessionId, questionsAnswered: 0 }),
  setQuestion: (question) => set({ currentQuestion: question }),
  setStrategy: (strategy) => set({ strategy }),
  incrementAnswered: () => set((state) => ({
    questionsAnswered: state.questionsAnswered + 1
  })),
  endSession: () => set({ sessionId: null, currentQuestion: null }),
}));
```

---

## API Services

### Belief Service

```typescript
// apps/web/src/services/beliefService.ts
import { api } from './api';
import { BeliefState } from '../types/belief';

export const beliefService = {
  async getAll(): Promise<BeliefState[]> {
    const response = await api.get('/api/v1/beliefs');
    return response.data;
  },

  async getByKnowledgeArea(knowledgeArea: string): Promise<BeliefState[]> {
    const response = await api.get('/api/v1/beliefs', {
      params: { knowledge_area: knowledgeArea },
    });
    return response.data;
  },

  async getConcept(conceptId: string): Promise<BeliefState> {
    const response = await api.get(`/api/v1/beliefs/${conceptId}`);
    return response.data;
  },
};
```

### Coverage Service

```typescript
// apps/web/src/services/coverageService.ts
import { api } from './api';
import { CoverageReport, CoverageSummary } from '../types/coverage';

export const coverageService = {
  async getSummary(): Promise<CoverageSummary> {
    const response = await api.get('/api/v1/coverage/summary');
    return response.data;
  },

  async getByKnowledgeArea(): Promise<Record<string, CoverageSummary>> {
    const response = await api.get('/api/v1/coverage/by-knowledge-area');
    return response.data;
  },

  async getGaps(): Promise<ConceptStatus[]> {
    const response = await api.get('/api/v1/coverage/gaps');
    return response.data;
  },

  async getDetails(): Promise<CoverageReport> {
    const response = await api.get('/api/v1/coverage/details');
    return response.data;
  },
};
```

### Quiz Service

```typescript
// apps/web/src/services/quizService.ts
import { v4 as uuidv4 } from 'uuid';
import { api } from './api';

export const quizService = {
  async getNextQuestion(strategy: string = 'max_info_gain'): Promise<Question> {
    const response = await api.post('/api/v1/quiz/next-question', { strategy });
    return response.data;
  },

  async submitAnswer(questionId: string, answer: string): Promise<AnswerResponse> {
    const requestId = uuidv4(); // Client-generated idempotency key

    const response = await api.post('/api/v1/quiz/answer', {
      question_id: questionId,
      selected_answer: answer,
    }, {
      headers: {
        'X-Request-ID': requestId,
      },
    });

    return response.data;
  },
};
```

---

## Custom Hooks

### useBeliefs Hook

```typescript
// apps/web/src/hooks/useBeliefs.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { beliefService } from '../services/beliefService';
import { useBeliefStore } from '../stores/beliefStore';

export function useBeliefs() {
  const { setBeliefs } = useBeliefStore();

  return useQuery({
    queryKey: ['beliefs'],
    queryFn: async () => {
      const beliefs = await beliefService.getAll();
      setBeliefs(beliefs);
      return beliefs;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useBelief(conceptId: string) {
  return useQuery({
    queryKey: ['belief', conceptId],
    queryFn: () => beliefService.getConcept(conceptId),
  });
}
```

### useCoverage Hook

```typescript
// apps/web/src/hooks/useCoverage.ts
import { useQuery } from '@tanstack/react-query';
import { coverageService } from '../services/coverageService';

export function useCoverageSummary() {
  return useQuery({
    queryKey: ['coverage', 'summary'],
    queryFn: coverageService.getSummary,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}

export function useCoverageByKA() {
  return useQuery({
    queryKey: ['coverage', 'by-ka'],
    queryFn: coverageService.getByKnowledgeArea,
    staleTime: 2 * 60 * 1000,
  });
}

export function useGaps() {
  return useQuery({
    queryKey: ['coverage', 'gaps'],
    queryFn: coverageService.getGaps,
    staleTime: 2 * 60 * 1000,
  });
}
```

### useQuiz Hook

```typescript
// apps/web/src/hooks/useQuiz.ts
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { quizService } from '../services/quizService';
import { useQuizStore } from '../stores/quizStore';
import { useBeliefStore } from '../stores/beliefStore';

export function useQuiz() {
  const queryClient = useQueryClient();
  const { strategy, setQuestion, incrementAnswered } = useQuizStore();
  const { updateBelief } = useBeliefStore();

  const getNextQuestion = useMutation({
    mutationFn: () => quizService.getNextQuestion(strategy),
    onSuccess: (question) => {
      setQuestion(question);
    },
  });

  const submitAnswer = useMutation({
    mutationFn: ({ questionId, answer }: { questionId: string; answer: string }) =>
      quizService.submitAnswer(questionId, answer),
    onSuccess: (response) => {
      incrementAnswered();

      // Update local belief cache with server response
      response.belief_updates.forEach((update: BeliefUpdate) => {
        updateBelief(update.concept_id, update.new_alpha, update.new_beta);
      });

      // Invalidate coverage queries to reflect updates
      queryClient.invalidateQueries({ queryKey: ['coverage'] });
    },
  });

  return { getNextQuestion, submitAnswer };
}
```

---

## Frontend Types

### Belief Types

```typescript
// apps/web/src/types/belief.ts
export interface BeliefState {
  concept_id: string;
  user_id: string;
  alpha: number;
  beta: number;
  last_response_at: string | null;
  response_count: number;

  // Computed on frontend for display
  mean?: number;        // alpha / (alpha + beta)
  confidence?: number;  // (alpha + beta) / (alpha + beta + 10)
}

export interface ConceptStatus {
  concept_id: string;
  concept_name: string;
  status: 'mastered' | 'gap' | 'borderline' | 'uncertain';
  probability: number;
  confidence: number;
}

export interface BeliefUpdate {
  concept_id: string;
  concept_name: string;
  old_alpha: number;
  old_beta: number;
  new_alpha: number;
  new_beta: number;
}
```

### Coverage Types

```typescript
// apps/web/src/types/coverage.ts
export interface CoverageSummary {
  total_concepts: number;
  mastered: number;
  gaps: number;
  uncertain: number;
  coverage_percentage: number;
  confidence_percentage: number;
  estimated_questions_remaining: number;
}

export interface CoverageReport extends CoverageSummary {
  mastered_concepts: ConceptStatus[];
  gap_concepts: ConceptStatus[];
  uncertain_concepts: ConceptStatus[];
}

export interface KnowledgeAreaCoverage {
  knowledge_area: string;
  total_concepts: number;
  mastered: number;
  gaps: number;
  readiness_score: number; // 0-100
}
```

---

## Routing

- **React Router v6** with protected routes pattern
- Nested routes with Outlet for layout composition
- Auth guard redirects to login with return URL preservation

### Route Structure

```typescript
// apps/web/src/routes.tsx
const routes = [
  {
    path: '/',
    element: <ProtectedLayout />,
    children: [
      { index: true, element: <Dashboard /> },
      { path: 'quiz', element: <Quiz /> },
      { path: 'coverage', element: <Coverage /> },
      { path: 'coverage/:conceptId', element: <ConceptDetail /> },
      { path: 'gaps', element: <Gaps /> },
      { path: 'settings', element: <Settings /> },
    ],
  },
  { path: '/login', element: <Login /> },
  { path: '/register', element: <Register /> },
];
```

---

## API Client

- **Axios** with request/response interceptors
- Automatic JWT token attachment
- Token refresh on 401 responses
- Service layer abstracts API calls

```typescript
// apps/web/src/services/api.ts
import axios from 'axios';
import { useAuthStore } from '../stores/authStore';

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
});

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Handle token refresh or logout
      await useAuthStore.getState().refreshToken();
      return api.request(error.config);
    }
    return Promise.reject(error);
  }
);
```

---

## Browser Support Matrix

**Supported Browsers (Latest 2 Versions):**

| Browser | Versions | Platform | Priority | Notes |
|---------|----------|----------|----------|-------|
| **Chrome** | Latest 2 major versions | Windows, macOS, Linux | Primary | Development primary target |
| **Edge** | Latest 2 major versions | Windows, macOS | Primary | Chromium-based |
| **Firefox** | Latest 2 major versions | Windows, macOS, Linux | Secondary | Gecko engine |
| **Safari** | Latest 2 major versions | macOS, iOS | Primary | WebKit engine |

**Mobile Browser Support:**

| Browser | Versions | Platform | Priority |
|---------|----------|----------|----------|
| **Safari Mobile** | iOS 14+ | iPhone, iPad | Primary |
| **Chrome Mobile** | Latest 2 versions | Android | Primary |
| **Samsung Internet** | Latest version | Android Samsung | Tertiary |

**Minimum Screen Resolutions:**

| Device Category | Minimum Width | Breakpoint |
|-----------------|---------------|------------|
| **Mobile** | 375px | 0-767px |
| **Tablet** | 768px | 768-1279px |
| **Desktop** | 1280px | 1280px+ |

**Browser Target (vite.config.ts):**
```typescript
export default {
  build: {
    target: ['es2020', 'edge88', 'firefox78', 'chrome87', 'safari14'],
  },
};
```

---

## Progressive Web App (PWA)

### MVP PWA Features

**1. Web App Manifest**

Location: `apps/web/public/manifest.json`

```json
{
  "name": "LearnR - CBAP Exam Preparation",
  "short_name": "LearnR",
  "description": "AI-powered adaptive learning for CBAP certification",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#FFFFFF",
  "theme_color": "#0066CC",
  "orientation": "portrait-primary"
}
```

**2. Service Worker for Offline Error Handling**

Strategy: Network-first with graceful offline error page

**3. Add to Home Screen (A2HS) Prompt**

- Show prompt after user completes first quiz session
- Defer using `beforeinstallprompt` event
- User can dismiss permanently

### Post-MVP PWA Features

1. **Offline Quiz Mode** - Cache questions in IndexedDB
2. **Background Sync** - Queue belief updates during offline
3. **Push Notifications** - Spaced repetition reminders
4. **Offline Reading** - Cache BABOK content

---

## Accessibility Architecture

LearnR is committed to WCAG 2.1 Level AA compliance, ensuring the platform is usable by learners with disabilities. As an educational platform, accessibility is not optional—it's core to our mission of enabling learning for all.

### Accessibility Standards & Compliance

#### Target Standard: WCAG 2.1 Level AA

| Requirement | Standard | LearnR Implementation |
|-------------|----------|----------------------|
| **Compliance Level** | WCAG 2.1 AA | Full AA compliance for all user-facing features |
| **Legal Framework** | ADA (US), Section 508, EN 301 549 (EU) | Design meets or exceeds all requirements |
| **Assistive Technology** | Screen readers, voice control, switch devices | Tested with NVDA, JAWS, VoiceOver |
| **Mobile Accessibility** | WCAG 2.1 mobile-specific criteria | Touch targets, gesture alternatives |

#### Accessibility Principles (POUR)

1. **Perceivable** - Information presentable in ways all users can perceive
2. **Operable** - Interface components operable by all users
3. **Understandable** - Information and UI operation understandable
4. **Robust** - Content interpretable by assistive technologies

---

### Technical Implementation

#### Semantic HTML Requirements

All components MUST use semantic HTML as the foundation:

```tsx
// ✅ CORRECT - Semantic structure
<main>
  <article aria-labelledby="quiz-title">
    <h1 id="quiz-title">Practice Quiz</h1>
    <section aria-label="Question 1 of 10">
      <h2>Question</h2>
      <fieldset>
        <legend>Select your answer:</legend>
        {/* Radio buttons for answers */}
      </fieldset>
    </section>
  </article>
</main>

// ❌ INCORRECT - div soup
<div className="main">
  <div className="quiz">
    <div className="title">Practice Quiz</div>
    <div className="question">
      <div className="answers">
        {/* Clickable divs */}
      </div>
    </div>
  </div>
</div>
```

**Required Semantic Elements:**

| Element | Usage | Example |
|---------|-------|---------|
| `<main>` | Primary page content | One per page |
| `<nav>` | Navigation sections | Header nav, sidebar |
| `<article>` | Self-contained content | Quiz, lesson |
| `<section>` | Thematic grouping | Question section |
| `<aside>` | Tangentially related | Progress sidebar |
| `<header>`, `<footer>` | Page/section headers | App header |
| `<h1>`-`<h6>` | Heading hierarchy | Never skip levels |
| `<button>` | Interactive actions | Never use `<div onClick>` |
| `<a>` | Navigation links | With meaningful href |

#### ARIA Implementation Patterns

**Live Regions for Dynamic Content:**

```tsx
// apps/web/src/components/quiz/AnswerFeedback.tsx
export function AnswerFeedback({ isCorrect, explanation }: AnswerFeedbackProps) {
  return (
    <div
      role="status"
      aria-live="polite"
      aria-atomic="true"
      className={`feedback ${isCorrect ? 'correct' : 'incorrect'}`}
    >
      <p className="result">
        {isCorrect ? 'Correct!' : 'Incorrect'}
      </p>
      <p className="explanation">{explanation}</p>
    </div>
  );
}
```

**ARIA Live Region Guidelines:**

| Scenario | `aria-live` Value | `aria-atomic` |
|----------|-------------------|---------------|
| Quiz feedback | `polite` | `true` |
| Error messages | `assertive` | `true` |
| Progress updates | `polite` | `false` |
| Toast notifications | `polite` | `true` |
| Loading states | `polite` | `true` |

**ARIA Patterns for Custom Components:**

```tsx
// Custom progress bar with ARIA
<div
  role="progressbar"
  aria-valuenow={75}
  aria-valuemin={0}
  aria-valuemax={100}
  aria-label="Knowledge area progress: 75% complete"
>
  <span className="sr-only">75% complete</span>
</div>

// Custom tabs (Headless UI handles this)
<Tab.Group>
  <Tab.List aria-label="Coverage views">
    <Tab>Overview</Tab>
    <Tab>Details</Tab>
  </Tab.List>
</Tab.Group>
```

#### Keyboard Navigation

**All interactive elements MUST be keyboard accessible:**

| Action | Key(s) | Component Examples |
|--------|--------|-------------------|
| Focus next | `Tab` | All focusable elements |
| Focus previous | `Shift+Tab` | All focusable elements |
| Activate | `Enter`, `Space` | Buttons, links, checkboxes |
| Navigate options | `Arrow keys` | Radio groups, menus, tabs |
| Close/Cancel | `Escape` | Dialogs, dropdowns, menus |
| Submit | `Enter` (in forms) | Form submission |

**Focus Management Requirements:**

```tsx
// apps/web/src/components/common/Dialog.tsx
import { Dialog } from '@headlessui/react';
import { useRef, useEffect } from 'react';

export function AccessibleDialog({ isOpen, onClose, title, children }) {
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  return (
    <Dialog
      open={isOpen}
      onClose={onClose}
      initialFocus={closeButtonRef}
    >
      <Dialog.Overlay className="dialog-overlay" />
      <Dialog.Panel>
        <Dialog.Title>{title}</Dialog.Title>
        <Dialog.Description>
          {/* Screen reader description */}
        </Dialog.Description>
        {children}
        <button ref={closeButtonRef} onClick={onClose}>
          Close
        </button>
      </Dialog.Panel>
    </Dialog>
  );
}
```

**Focus Trap Pattern (Dialogs, Modals):**
- Focus trapped within dialog when open
- Focus returns to trigger element on close
- Headless UI `Dialog` component handles this automatically

**Skip Links:**

```tsx
// apps/web/src/components/layout/SkipLinks.tsx
export function SkipLinks() {
  return (
    <nav aria-label="Skip links" className="skip-links">
      <a href="#main-content" className="skip-link">
        Skip to main content
      </a>
      <a href="#main-navigation" className="skip-link">
        Skip to navigation
      </a>
    </nav>
  );
}

// CSS - visible only on focus
.skip-link {
  position: absolute;
  left: -9999px;
  z-index: 999;
  padding: 1rem;
  background: white;
  color: black;
}
.skip-link:focus {
  left: 0;
  top: 0;
}
```

#### Color and Contrast Requirements

**Contrast Ratios (WCAG 2.1 AA):**

| Element Type | Minimum Ratio | Example |
|--------------|---------------|---------|
| Normal text (< 18pt) | 4.5:1 | Body text, labels |
| Large text (≥ 18pt or 14pt bold) | 3:1 | Headings |
| UI components & graphics | 3:1 | Buttons, icons, focus indicators |
| Disabled elements | No requirement | But maintain readability |

**LearnR Color Palette (Accessible):**

```css
/* apps/web/src/styles/colors.css */
:root {
  /* Primary - passes 4.5:1 on white */
  --color-primary: #0066CC;       /* 5.3:1 on white */
  --color-primary-dark: #004C99;  /* 7.1:1 on white */

  /* Status colors - passes 4.5:1 on white */
  --color-success: #0A6E0A;       /* 5.9:1 on white */
  --color-error: #B91C1C;         /* 5.7:1 on white */
  --color-warning: #92400E;       /* 4.7:1 on white */

  /* Coverage heatmap - with text labels for colorblind users */
  --color-mastered: #0A6E0A;      /* Green + "Mastered" label */
  --color-gap: #B91C1C;           /* Red + "Gap" label */
  --color-uncertain: #6B7280;     /* Gray + "Uncertain" label */
  --color-borderline: #92400E;    /* Orange + "Review" label */
}
```

**Never Rely on Color Alone:**

```tsx
// ✅ CORRECT - Color + icon + text
<div className="status-correct">
  <CheckIcon aria-hidden="true" />
  <span>Correct</span>
</div>

// ❌ INCORRECT - Color only
<div className="status-correct" /> // Green background, no text
```

---

### Component-Level Accessibility

#### Form Accessibility

**Required Patterns for All Forms:**

```tsx
// apps/web/src/components/auth/LoginForm.tsx
export function LoginForm() {
  const [errors, setErrors] = useState<Record<string, string>>({});

  return (
    <form onSubmit={handleSubmit} noValidate>
      {/* Form-level error summary for screen readers */}
      {Object.keys(errors).length > 0 && (
        <div role="alert" aria-live="assertive">
          <h2>Please fix the following errors:</h2>
          <ul>
            {Object.entries(errors).map(([field, message]) => (
              <li key={field}>
                <a href={`#${field}`}>{message}</a>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="form-group">
        <label htmlFor="email">
          Email address
          <span aria-hidden="true" className="required">*</span>
          <span className="sr-only">(required)</span>
        </label>
        <input
          id="email"
          name="email"
          type="email"
          required
          aria-required="true"
          aria-invalid={!!errors.email}
          aria-describedby={errors.email ? 'email-error' : undefined}
          autoComplete="email"
        />
        {errors.email && (
          <p id="email-error" className="error" role="alert">
            {errors.email}
          </p>
        )}
      </div>

      <button type="submit">
        Sign In
      </button>
    </form>
  );
}
```

**Form Accessibility Checklist:**
- [ ] All inputs have associated `<label>` elements (via `htmlFor`/`id`)
- [ ] Required fields indicated visually AND for screen readers
- [ ] Error messages linked via `aria-describedby`
- [ ] Error summary with links to invalid fields
- [ ] `aria-invalid` set on fields with errors
- [ ] Appropriate `autocomplete` attributes
- [ ] Submit button is a `<button type="submit">`

#### Quiz Component Accessibility

```tsx
// apps/web/src/components/quiz/QuestionCard.tsx
export function QuestionCard({ question, onAnswer }: QuestionCardProps) {
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null);

  return (
    <article
      aria-labelledby="question-text"
      className="question-card"
    >
      <header>
        <p className="question-number" aria-live="polite">
          Question {question.number} of {question.total}
        </p>
      </header>

      <h2 id="question-text">{question.text}</h2>

      <fieldset>
        <legend className="sr-only">
          Choose your answer for: {question.text}
        </legend>

        {question.answers.map((answer, index) => (
          <div key={answer.id} className="answer-option">
            <input
              type="radio"
              id={`answer-${answer.id}`}
              name="answer"
              value={answer.id}
              checked={selectedAnswer === answer.id}
              onChange={() => setSelectedAnswer(answer.id)}
              aria-describedby={`answer-label-${answer.id}`}
            />
            <label
              id={`answer-label-${answer.id}`}
              htmlFor={`answer-${answer.id}`}
            >
              <span className="answer-letter" aria-hidden="true">
                {String.fromCharCode(65 + index)}.
              </span>
              {answer.text}
            </label>
          </div>
        ))}
      </fieldset>

      <button
        type="button"
        onClick={() => onAnswer(selectedAnswer)}
        disabled={!selectedAnswer}
        aria-disabled={!selectedAnswer}
      >
        Submit Answer
      </button>
    </article>
  );
}
```

#### Data Visualization Accessibility (Charts & Heatmaps)

**Coverage Heatmap (Accessible Version):**

```tsx
// apps/web/src/components/coverage/CoverageHeatmap.tsx
export function CoverageHeatmap({ beliefs, onConceptClick }: CoverageHeatmapProps) {
  const getStatusInfo = (belief: BeliefState) => {
    const mean = belief.alpha / (belief.alpha + belief.beta);
    const confidence = (belief.alpha + belief.beta) / (belief.alpha + belief.beta + 10);

    if (confidence < 0.7) return { color: 'gray', label: 'Uncertain', description: 'Not enough data' };
    if (mean >= 0.8) return { color: 'green', label: 'Mastered', description: 'Strong understanding' };
    if (mean <= 0.5) return { color: 'red', label: 'Gap', description: 'Needs review' };
    return { color: 'yellow', label: 'Review', description: 'Borderline understanding' };
  };

  return (
    <div
      role="grid"
      aria-label="Concept mastery heatmap. Use arrow keys to navigate."
      className="heatmap-grid"
    >
      {/* Accessible table alternative for screen readers */}
      <table className="sr-only">
        <caption>Concept Mastery Summary</caption>
        <thead>
          <tr>
            <th>Concept</th>
            <th>Status</th>
            <th>Mastery Level</th>
          </tr>
        </thead>
        <tbody>
          {beliefs.map((belief) => {
            const status = getStatusInfo(belief);
            return (
              <tr key={belief.concept_id}>
                <td>{belief.concept_name}</td>
                <td>{status.label}</td>
                <td>{Math.round(belief.alpha / (belief.alpha + belief.beta) * 100)}%</td>
              </tr>
            );
          })}
        </tbody>
      </table>

      {/* Visual heatmap (aria-hidden from screen readers, who get the table) */}
      <div aria-hidden="true" className="visual-heatmap">
        {beliefs.map((belief) => {
          const status = getStatusInfo(belief);
          return (
            <button
              key={belief.concept_id}
              className="concept-cell"
              style={{ backgroundColor: status.color }}
              onClick={() => onConceptClick(belief.concept_id)}
              title={`${belief.concept_name}: ${status.label}`}
            >
              <span className="cell-label">{status.label[0]}</span>
            </button>
          );
        })}
      </div>

      {/* Legend */}
      <div className="heatmap-legend" role="img" aria-label="Legend">
        <div className="legend-item">
          <span className="legend-color mastered" aria-hidden="true"></span>
          <span>Mastered (M)</span>
        </div>
        <div className="legend-item">
          <span className="legend-color review" aria-hidden="true"></span>
          <span>Review (R)</span>
        </div>
        <div className="legend-item">
          <span className="legend-color gap" aria-hidden="true"></span>
          <span>Gap (G)</span>
        </div>
        <div className="legend-item">
          <span className="legend-color uncertain" aria-hidden="true"></span>
          <span>Uncertain (U)</span>
        </div>
      </div>
    </div>
  );
}
```

**Chart Accessibility Requirements:**
- [ ] Provide data table alternative (visible or `sr-only`)
- [ ] Don't rely on color alone—use patterns, labels, or icons
- [ ] Include text summaries of key insights
- [ ] Keyboard navigable data points
- [ ] Descriptive `aria-label` on chart containers

#### Toast/Notification Accessibility

```tsx
// apps/web/src/components/common/Toast.tsx
export function Toast({ message, type, onDismiss }: ToastProps) {
  const autoFocusRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Don't steal focus for non-critical notifications
    if (type === 'error') {
      autoFocusRef.current?.focus();
    }
  }, [type]);

  return (
    <div
      ref={autoFocusRef}
      role={type === 'error' ? 'alert' : 'status'}
      aria-live={type === 'error' ? 'assertive' : 'polite'}
      aria-atomic="true"
      tabIndex={-1}
      className={`toast toast-${type}`}
    >
      <span className="toast-icon" aria-hidden="true">
        {type === 'success' && '✓'}
        {type === 'error' && '✕'}
        {type === 'info' && 'ℹ'}
      </span>
      <span className="toast-message">{message}</span>
      <button
        onClick={onDismiss}
        aria-label="Dismiss notification"
        className="toast-dismiss"
      >
        <XIcon aria-hidden="true" />
      </button>
    </div>
  );
}
```

---

### Assistive Technology Support

#### Screen Reader Compatibility

**Tested Screen Readers:**

| Screen Reader | Browser | Platform | Priority |
|--------------|---------|----------|----------|
| NVDA | Firefox, Chrome | Windows | Primary |
| JAWS | Chrome | Windows | Primary |
| VoiceOver | Safari | macOS, iOS | Primary |
| TalkBack | Chrome | Android | Secondary |

**Screen Reader Testing Requirements:**
- All pages navigable via headings (`H` key)
- All interactive elements reachable via Tab
- Form labels announced correctly
- Error messages announced automatically
- Dynamic content updates announced via live regions
- Images have descriptive alt text or are decorative (`alt=""`)

**Screen Reader Utility Classes:**

```css
/* Screen reader only - visually hidden but accessible */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

/* Visible only when focused (for skip links) */
.sr-only-focusable:focus {
  position: static;
  width: auto;
  height: auto;
  overflow: visible;
  clip: auto;
  white-space: normal;
}
```

#### Reduced Motion Support

**Respect User Preferences:**

```css
/* apps/web/src/styles/motion.css */

/* Default animations */
.animate-fade-in {
  animation: fadeIn 0.3s ease-in-out;
}

.animate-slide-up {
  animation: slideUp 0.2s ease-out;
}

/* Disable animations for users who prefer reduced motion */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }

  .animate-fade-in,
  .animate-slide-up,
  .animate-pulse {
    animation: none;
  }
}
```

**React Hook for Motion Preference:**

```tsx
// apps/web/src/hooks/useReducedMotion.ts
export function useReducedMotion(): boolean {
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setPrefersReducedMotion(mediaQuery.matches);

    const handler = (event: MediaQueryListEvent) => {
      setPrefersReducedMotion(event.matches);
    };

    mediaQuery.addEventListener('change', handler);
    return () => mediaQuery.removeEventListener('change', handler);
  }, []);

  return prefersReducedMotion;
}

// Usage
function BeliefUpdateIndicator({ updates }: Props) {
  const prefersReducedMotion = useReducedMotion();

  return (
    <div className={prefersReducedMotion ? '' : 'animate-slide-up'}>
      {/* Content */}
    </div>
  );
}
```

#### High Contrast Mode Support

```css
/* apps/web/src/styles/high-contrast.css */

/* Windows High Contrast Mode */
@media (forced-colors: active) {
  /* Ensure focus indicators are visible */
  :focus {
    outline: 3px solid CanvasText !important;
    outline-offset: 2px;
  }

  /* Preserve button boundaries */
  button,
  .btn {
    border: 2px solid ButtonText !important;
  }

  /* Ensure links are distinguishable */
  a {
    text-decoration: underline !important;
  }

  /* Heatmap cells need borders in high contrast */
  .concept-cell {
    border: 2px solid CanvasText;
  }
}
```

#### Zoom and Magnification

**Requirements:**
- Content reflows at 200% zoom (no horizontal scrolling)
- Text resizable to 200% without loss of content
- Touch targets minimum 44x44px (48x48px recommended)

```css
/* Ensure content reflows */
.container {
  max-width: 100%;
  padding: clamp(1rem, 5vw, 2rem);
}

/* Minimum touch targets */
button,
a,
input[type="checkbox"],
input[type="radio"] {
  min-height: 44px;
  min-width: 44px;
}

/* Relative font sizing for user zoom */
html {
  font-size: 100%; /* Respects user browser settings */
}

body {
  font-size: 1rem; /* 16px default, scales with user preference */
  line-height: 1.5;
}
```

---

### Accessibility Testing Strategy

#### Automated Testing

**Tools:**
- **axe-core** - Integration with Vitest for unit tests
- **eslint-plugin-jsx-a11y** - Linting for accessibility issues
- **pa11y-ci** - CI pipeline accessibility scanning

**axe-core Integration:**

```typescript
// apps/web/src/test/setup.ts
import { configureAxe, toHaveNoViolations } from 'jest-axe';

expect.extend(toHaveNoViolations);

// apps/web/src/components/__tests__/QuestionCard.test.tsx
import { axe } from 'jest-axe';
import { render } from '@testing-library/react';
import { QuestionCard } from '../quiz/QuestionCard';

describe('QuestionCard accessibility', () => {
  it('should have no accessibility violations', async () => {
    const { container } = render(<QuestionCard {...mockProps} />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
```

**ESLint Configuration:**

```javascript
// apps/web/.eslintrc.js
module.exports = {
  extends: [
    'plugin:jsx-a11y/recommended',
  ],
  rules: {
    'jsx-a11y/anchor-is-valid': 'error',
    'jsx-a11y/click-events-have-key-events': 'error',
    'jsx-a11y/no-static-element-interactions': 'error',
    'jsx-a11y/label-has-associated-control': 'error',
  },
};
```

#### Manual Testing

**Testing Checklist (Per Feature):**

- [ ] **Keyboard-only navigation** - Complete all tasks without mouse
- [ ] **Screen reader testing** - Test with NVDA/VoiceOver
- [ ] **Zoom testing** - Test at 200% browser zoom
- [ ] **Color contrast** - Verify with browser dev tools
- [ ] **Reduced motion** - Test with `prefers-reduced-motion` enabled
- [ ] **Focus visibility** - Ensure focus indicator always visible

#### Accessibility Audit Schedule

| Audit Type | Frequency | Scope | Owner |
|------------|-----------|-------|-------|
| Automated (axe-core) | Every PR | Changed components | CI Pipeline |
| Manual testing | Every sprint | New features | QA Team |
| Screen reader testing | Monthly | Full application | QA Team |
| Third-party audit | Pre-launch, then annually | Full application | External vendor |

**Third-Party Audit Requirements:**
- WCAG 2.1 AA conformance testing
- Assistive technology compatibility testing
- Remediation recommendations with severity ratings
- Compliance certification upon passing

---

### Accessibility Governance

#### Design Review Requirements

Before development begins:
- [ ] Color contrast verified in designs (Figma accessibility plugins)
- [ ] Interactive states defined (hover, focus, active, disabled)
- [ ] Error states and messaging designed
- [ ] Keyboard interaction patterns documented

#### Development Requirements

- All components must pass axe-core automated testing
- No new `jsx-a11y` lint errors introduced
- Manual keyboard testing completed
- Screen reader testing for complex components

#### Definition of Done (Accessibility)

A feature is not complete until:
- [ ] Passes automated accessibility tests
- [ ] Keyboard navigable (Tab, Enter, Escape, Arrow keys)
- [ ] Screen reader announces content correctly
- [ ] Color contrast meets WCAG AA (4.5:1 text, 3:1 UI)
- [ ] Focus indicator visible on all interactive elements
- [ ] Error messages linked to form fields

---

## Performance Considerations

### Belief State Caching

- Cache beliefs in Zustand store for instant UI updates
- Use React Query for server state with stale-while-revalidate
- Optimistic updates on answer submission

### Coverage Aggregation

- Compute KA-level aggregations on frontend from belief cache
- Avoid re-fetching full coverage for minor updates

### Question Selection

- Pre-fetch next question while user reads current question
- Cache question data to avoid redundant fetches

---

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-12-08 | 2.1 | Added comprehensive Accessibility Architecture section (WCAG 2.1 AA compliance) | Winston (Architect) |
| 2025-12-03 | 2.0 | Aligned with BKT Architecture - added belief/coverage components, stores, services | Winston (Architect) |
| 2025-11-01 | 1.0 | Initial frontend architecture | Original |
