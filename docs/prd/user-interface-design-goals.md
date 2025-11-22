# User Interface Design Goals

This section captures the high-level UI/UX vision to guide design and development. The LearnR platform must deliver a professional, focused learning experience optimized for adult professionals preparing for career-advancing certifications.

### Overall UX Vision

LearnR's user experience should feel like **a personal learning coach** rather than a static testing tool. The platform continuously assesses, adapts, teaches, and motivates - creating a supportive environment that builds confidence while maintaining rigor. Every interaction should reinforce the value proposition: "This platform understands where I am, what I need to learn, and how to help me retain it."

**Key UX Principles:**
- **Trust through transparency**: Users always see their competency scores, gaps, and progress - no hiding weaknesses
- **Efficiency over entertainment**: Minimal distractions during study sessions; data visualizations are clear and actionable
- **Supportive, not patronizing**: Encouraging feedback without condescension; professional tone appropriate for career-focused adults
- **Personalized journey**: Every user's path is different based on their diagnostic results and ongoing performance

### Key Interaction Paradigms

**Progressive Disclosure (Onboarding)**
- One question at a time during onboarding flow (7 questions total)
- Clear progress indicators (Question 3 of 7)
- Friendly, conversational tone to set expectations and build rapport

**Focused Assessment Mode (Diagnostic & Quiz)**
- Minimal UI chrome during question answering - just question, options, and submit button
- Full-screen or centered focus to eliminate distractions
- Immediate visual feedback (correct = green, incorrect = orange/red) without interrupting flow
- Sequential flow: Question → Answer → Explanation → Reading → Next (guided progression)

**Data Dashboard (Progress Tracking)**
- At-a-glance competency visualization (6 KA bars with scores)
- Hero metrics prominent: Exam Readiness Score, Reviews Due, Days Until Exam
- Hover/tap interactions for drill-down details (KA-specific performance)
- Clear call-to-action: "Continue Learning" or "Start Reviews" based on state
- Weekly progress trends show improvement over time (motivational fuel)

**Contextual Content Presentation (Reading)**
- Reading content appears after explanations (logical learning sequence)
- Optional, not forced: Users can skip to next question or expand to read
- Readable formatting: Proper spacing, highlighted key points, BABOK section references
- Progress tracking: Mark as read, time spent, completion indicators

### Core Screens and Views

From a product perspective, these are the critical screens necessary to deliver the PRD values and goals:

1. **Landing Screen with Inline First Question** - Value proposition + first onboarding question (immediate engagement, no separate CTA)
2. **Onboarding Flow (Questions 2-7)** - Progressive disclosure, personalization questionnaire
3. **Account Creation Screen** - Prompted after question 7, email/password registration
4. **Diagnostic Assessment Screen** - 12-question baseline test (3 per KA), focused quiz mode
5. **Diagnostic Results Screen** - Competency breakdown by KA, gap analysis, recommendations
5. **Progress Dashboard (Home)** - 6 KA bars, exam readiness, reviews due, weekly trends, primary CTA
6. **Knowledge Area Detail View** - Drill-down per KA: competency, concept gaps, recent performance
7. **Quiz Session Screen** - Question display, answer selection, submission
8. **Explanation & Reading Screen** - Detailed explanations, targeted BABOK content, next question navigation
9. **Settings/Profile Screen** - Account management, preferences, exam date, privacy policy access

### Accessibility: WCAG 2.1 Level AA

LearnR commits to WCAG 2.1 Level AA compliance to ensure professional learners with disabilities can access the platform effectively and to demonstrate product quality.

**Critical Accessibility Features:**
- Keyboard navigation for all interactive elements (tab order, focus management)
- Screen reader compatibility (semantic HTML, ARIA labels, alt text for any images)
- Color contrast ratios: 4.5:1 for normal text, 3:1 for large text
- Text resizing up to 200% without loss of functionality
- Visible focus indicators on all interactive elements
- No flashing content (avoid seizure triggers)
- Descriptive labels and error messages

**Rationale:** Professional learners may have visual, motor, or cognitive disabilities. Accessibility broadens market reach and signals platform quality/professionalism.

### Branding

**Design Tone:**
- Professional & trustworthy (this is career advancement, not casual learning)
- Clean & focused (minimal distractions during study sessions)
- Encouraging & supportive (motivational without being patronizing)
- Data-driven & transparent (show progress, competency, gaps clearly)

**Color Psychology:**
- **Primary**: Professional blue (trust, competence, learning)
- **Success**: Green (correct answers, progress, achievement)
- **Attention**: Warm orange (reviews due, areas needing focus - not alarming red)
- **Neutrals**: Clean grays and whites (text, backgrounds, cards)

**Typography:**
- **Font Family:** Inter (primary typeface for all UI text)
- Larger font sizes for questions and explanations (readability priority)
- Adequate line spacing for sustained reading (BABOK content must be comfortable to read)
- Font weight hierarchy: 400 (regular), 500 (medium), 600 (semibold), 700 (bold)

**Visual Design System:**
- **Design Inspiration:** Framer website templates (modern, polished, professional aesthetic)
- **Icons:** Vector icons only - NO emojis used anywhere in the application
- **Card-based layouts** with hierarchical border radius system:
  - **Main screen containers:** 35px border radius (dashboard, quiz screens, major views)
  - **Primary information cards:** 22px border radius (competency cards, KA detail cards, explanation panels)
  - **Secondary cards:** 14px border radius (reading content chunks, stat cards, list items)
  - **Icon containers:** 8-12px border radius (avatar containers, small badges, icon buttons)
- **Buttons:** Pill-rounded shape (full border-radius: 9999px or 50%) for all CTAs and action buttons
- **Spacing & Layout:** Consistent padding and margins following 8px grid system
- **Elevation:** Subtle shadows for card depth, avoid heavy drop shadows

**Design System Tokens - Complete Specifications**

This section provides implementation-ready design tokens for all visual elements.

---

#### Color Palette (Light Mode)

| Color Token | Hex Code | Usage | Contrast |
|-------------|----------|-------|----------|
| `--color-primary` | `#0066CC` | Primary buttons, links, brand accents, progress bars | 4.5:1 on white |
| `--color-primary-dark` | `#004999` | Hover states, active buttons | 7:1 on white |
| `--color-primary-light` | `#E6F2FF` | Competency card backgrounds, subtle highlights | N/A |
| `--color-secondary` | `#6B7280` | Secondary text, metadata | 4.5:1 on white |
| `--color-success` | `#10B981` | Correct answers, high competency (>80%) | 4.5:1 on white |
| `--color-success-light` | `#D1FAE5` | Success backgrounds | N/A |
| `--color-warning` | `#F59E0B` | Reviews due, medium competency (60-80%) | 4.5:1 on white |
| `--color-warning-light` | `#FEF3C7` | Warning backgrounds | N/A |
| `--color-error` | `#EF4444` | Incorrect answers, low competency (<60%), high priority | 4.5:1 on white |
| `--color-error-light` | `#FEE2E2` | Error backgrounds | N/A |
| `--color-text-primary` | `#111827` | Headings, primary text | 12:1 on white |
| `--color-text-secondary` | `#374151` | Body text | 9:1 on white |
| `--color-text-tertiary` | `#6B7280` | Metadata, labels | 4.7:1 on white |
| `--color-border` | `#D1D5DB` | Dividers, card borders | N/A |
| `--color-bg-primary` | `#FFFFFF` | Page backgrounds | N/A |
| `--color-bg-secondary` | `#F9FAFB` | Card surfaces, subtle backgrounds | N/A |
| `--color-bg-tertiary` | `#F3F4F6` | Elevated cards | N/A |

**Color Psychology:**
- **Primary Blue (`#0066CC`)**: Trust, competence, learning (educational context)
- **Success Green (`#10B981`)**: Positive reinforcement, celebrates progress
- **Warning Orange (`#F59E0B`)**: Attention without panic (reviews due, not "failing")
- **Error Red (`#EF4444`)**: Clear feedback, paired with supportive messaging

---

#### Dark Mode Color Palette

**Activation:** Settings toggle - persists across devices via user profile

| Color Token | Dark Mode Value | Light Mode | Contrast |
|-------------|-----------------|------------|----------|
| `--bg-primary` | `#0F172A` (Slate 900) | `#FFFFFF` | N/A |
| `--bg-secondary` | `#1E293B` (Slate 800) | `#F9FAFB` | N/A |
| `--bg-tertiary` | `#334155` (Slate 700) | `#F3F4F6` | N/A |
| `--text-primary` | `#F1F5F9` (Slate 100) | `#111827` | 12:1 on Slate 900 |
| `--text-secondary` | `#CBD5E1` (Slate 300) | `#374151` | 8:1 on Slate 900 |
| `--text-tertiary` | `#94A3B8` (Slate 400) | `#6B7280` | 5:1 on Slate 900 |
| `--color-primary` | `#3B82F6` (Blue 500) | `#0066CC` | 4.5:1 on Slate 900 |
| `--color-primary-hover` | `#60A5FA` (Blue 400) | `#004999` | 6:1 on Slate 900 |
| `--color-success` | `#34D399` (Green 400) | `#10B981` | 4.5:1 on Slate 900 |
| `--color-warning` | `#FBBF24` (Amber 400) | `#F59E0B` | 4.5:1 on Slate 900 |
| `--color-error` | `#F87171` (Red 400) | `#EF4444` | 4.5:1 on Slate 900 |
| `--color-border` | `#475569` (Slate 600) | `#D1D5DB` | N/A |

**Implementation:**
- CSS custom properties updated via root class: `<html class="dark">`
- 200ms `ease-in-out` transition when toggling modes (prevents jarring flash)
- Tailwind dark mode variant: `dark:bg-slate-900`, `dark:text-slate-100`

---

#### Typography System

**Font Family:** Inter (Google Fonts)
- **Fallback:** system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif
- **Loading:** `font-display: swap` to prevent FOIT
- **Weights Used:** 400 (regular), 500 (medium), 600 (semibold), 700 (bold)

| Element | Size | Weight | Line Height | Usage |
|---------|------|--------|-------------|-------|
| `--text-h1` | 36px (2.25rem) | 700 | 1.2 (43px) | Page titles (rare) |
| `--text-h2` | 30px (1.875rem) | 700 | 1.3 (39px) | Section headers |
| `--text-h3` | 24px (1.5rem) | 600 | 1.4 (34px) | Subsection headers, KA names |
| `--text-h4` | 20px (1.25rem) | 600 | 1.5 (30px) | Component headers |
| `--text-body-lg` | 18px (1.125rem) | 400 | 1.6 (29px) | Question text, primary content |
| `--text-body` | 16px (1rem) | 400 | 1.5 (24px) | Default UI text, explanations |
| `--text-body-sm` | 14px (0.875rem) | 400 | 1.5 (21px) | Metadata, labels |
| `--text-caption` | 12px (0.75rem) | 500 | 1.4 (17px) | Badges, tags, timestamps |

**Typography Guidelines:**
- **Question Text:** 18-20px for readability during learning
- **Reading Content:** 16px with max-width 65-75 characters (optimal line length)
- **Mobile:** Scale down 10-15%, maintain line-height ratios
- **Paragraph Spacing:** 1.5-2em for multi-paragraph content

---

#### Spacing System

**Base Unit:** 4px (all spacing is multiple of 4)

| Token | Value | Usage |
|-------|-------|-------|
| `--space-xs` | 4px (0.25rem) | Tight spacing (icon + text) |
| `--space-sm` | 8px (0.5rem) | Component internal padding (badges, tags) |
| `--space-md` | 16px (1rem) | Default spacing (card padding, section gaps) |
| `--space-lg` | 24px (1.5rem) | Section spacing, generous card padding |
| `--space-xl` | 32px (2rem) | Major section breaks, dashboard sections |
| `--space-2xl` | 48px (3rem) | Page sections |
| `--space-3xl` | 64px (4rem) | Large breakouts |

**Layout Constraints:**
- **Touch Targets:** Minimum 48x48px on mobile (accessibility)
- **Container Max-Widths:**
  - Dashboard: 1280px
  - Quiz Session: 800px (focused, centered)
  - Reading Library: 1200px (3-column grid)
  - Reading Detail: 700px (optimal line length)

---

#### Border Radius Hierarchy

| Token | Value | Usage |
|-------|-------|-------|
| `--radius-main` | 35px | Main screen containers (dashboard, quiz screens) |
| `--radius-primary` | 22px | Primary cards (competency cards, KA detail, explanations) |
| `--radius-secondary` | 14px | Secondary cards (reading chunks, stat cards, list items) |
| `--radius-icons` | 8-12px | Icon containers, small badges |
| `--radius-pill` | 9999px (full) | All buttons (pill-rounded CTAs) |

---

#### Icon System

**Library:** Heroicons (MIT License) - Outline style (24x24px) for most UI

**Core Icons:**
- Reading Library: Book icon (outline) + badge count
- Correct Answer: Check circle (solid, green)
- Incorrect Answer: X circle (solid, red)
- Master Level: Trophy/award icon
- Tooltip Info: Information circle (outline)
- Flag Question: Flag icon (outline)
- Navigation: Arrow icons (left/right)
- Settings: Cog icon
- Profile: User circle
- Dark Mode Toggle: Moon/Sun icons

**Icon Specifications:**
- **Sizes:** 20px (inline), 24px (standalone), 48px (hero)
- **Stroke Width:** 1.5-2px for outline icons
- **Color:** Inherit from parent or use theme colors
- **Accessibility:** Always paired with text label or ARIA label

---

#### CSS Custom Properties Structure

```css
:root {
  /* Colors - Light Mode */
  --color-primary: #0066CC;
  --color-primary-dark: #004999;
  --color-success: #10B981;
  --color-warning: #F59E0B;
  --color-error: #EF4444;

  --text-primary: #111827;
  --text-secondary: #374151;
  --bg-primary: #FFFFFF;
  --bg-secondary: #F9FAFB;

  /* Typography */
  --font-family-primary: 'Inter', system-ui, sans-serif;
  --text-h1: 2.25rem;
  --text-body: 1rem;
  --line-height-body: 1.5;

  /* Spacing */
  --space-xs: 0.25rem;
  --space-sm: 0.5rem;
  --space-md: 1rem;
  --space-lg: 1.5rem;

  /* Border Radius */
  --radius-primary: 22px;
  --radius-secondary: 14px;
  --radius-pill: 9999px;
}

html.dark {
  /* Colors - Dark Mode Override */
  --color-primary: #3B82F6;
  --text-primary: #F1F5F9;
  --text-secondary: #CBD5E1;
  --bg-primary: #0F172A;
  --bg-secondary: #1E293B;
}
```

**Development Rule:** NO hard-coded colors or spacing. All components must use design tokens via CSS custom properties.

### Dark Mode Typography Specifications (NEW MVP FEATURE)

Dark mode requires enhanced typography for optimal readability during extended study sessions:

**Light Mode Reading Typography:**
- Font size: 16px Inter
- Line height: 1.6 (26px)
- Color: `#374151` (Gray 700 - high contrast on white)

**Dark Mode Reading Typography (Enhanced):**
- Font size: **17px Inter** (1px larger for dark backgrounds)
- Line height: **1.7** (28.9px) - increased breathing room
- Color: `#CBD5E1` (Slate 300 - softer than pure white, reduces eye strain)
- Background: `#1E293B` (Slate 800 - not pure black, easier on eyes)

**Rationale:** Dark mode requires different typography settings for optimal readability. Larger font size and increased line height compensate for reduced contrast on dark backgrounds, reducing eye strain during extended reading sessions (critical for BABOK content consumption).

**Complete dark mode specs:** See `/docs/front-end-spec.md` Lines 2193-2227 (color palette), Lines 929-969 (reading view typography).

### Animation & Motion Design Specifications

LearnR uses subtle animations to enhance UX without overwhelming users. All animations respect cognitive flow and accessibility requirements.

**Animation Principles:**
- **Purposeful:** Every animation serves a functional purpose (feedback, guidance, or state transition)
- **Fast:** Animations complete in 200-400ms to feel responsive, not sluggish
- **Subtle:** No excessive bouncing, spinning, or attention-seeking effects (professional, not playful)
- **Accessible:** Respect `prefers-reduced-motion` media query - disable non-essential animations for users with vestibular disorders

**Key Animation Patterns:**

Complete animation specifications documented in `/docs/front-end-spec.md` Lines 2541-2643:

| Element | Animation | Timing | Purpose |
|---------|-----------|--------|---------|
| **Answer Feedback** | Pulse or shake | 200-300ms `ease-out` | Immediate visual confirmation of correct/incorrect |
| **Competency Bar Update** | Fill animation | 400ms `ease-in-out` | Show progress increase smoothly |
| **Reading Badge Pulse** | Scale 1.0 → 1.1 → 1.0 | 1000ms loop | Draw attention to new unread items (subtle) |
| **Perfect Session Celebration** | Confetti physics | 1500-2000ms | Reward achievement |
| **Dark Mode Toggle** | Color transition | 200ms `ease-in-out` | Prevent jarring flash when switching themes |
| **Modal Entry/Exit** | Fade + scale | 250ms `ease-out` | Smooth dialog transitions |
| **Question Transition** | Fade-in | 300ms | Smooth progression between questions |

**Accessibility Requirement:**
```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

### Target Device and Platforms: Web Responsive

**Primary Target:** Web browsers (desktop and mobile)
- Desktop-optimized (1280x720 minimum, 1920x1080 ideal)
- Tablet-responsive (768x1024 iPad standard)
- Mobile-responsive (375x667 iPhone SE and up)

**Browser Support:**
- Chrome/Chromium-based browsers (primary target)
- Firefox, Safari, Edge (latest 2 versions)
- iOS Safari (iPhone/iPad), Chrome Mobile (Android)

**Post-MVP:** Native mobile apps (iOS & Android via React Native) planned for Phase 3 (Q2-Q3 2026) with offline mode and push notifications.

**Rationale:** Responsive web provides maximum reach with minimal development investment for MVP. Mobile-responsive design allows study anywhere. Native apps deferred until web platform validated.

---
