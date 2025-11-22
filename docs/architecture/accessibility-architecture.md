# Accessibility Architecture

### WCAG 2.1 Level AA Compliance

LearnR is committed to **WCAG 2.1 Level AA accessibility** to ensure the platform is usable by all learners, including those with disabilities. This is both a legal requirement and a core product value.

### Semantic HTML Strategy

**Foundation:**
- Use semantic HTML5 elements (`<nav>`, `<main>`, `<article>`, `<section>`, `<button>`, `<header>`) instead of generic `<div>` elements
- All form inputs have associated `<label>` elements with proper `for` attribute
- Headings follow logical hierarchy (single `<h1>` per page, no skipped levels)
- Lists use proper `<ul>`, `<ol>`, `<li>` structure

**Implementation Pattern:**
```tsx
// Good - Semantic
<nav aria-label="Main navigation">
  <button aria-label="Start quiz session">Continue Learning</button>
</nav>

// Bad - Non-semantic
<div className="nav">
  <div onClick={handleClick}>Continue Learning</div>
</div>
```

### ARIA Implementation Patterns

**When to Use ARIA:**
- Only when semantic HTML is insufficient
- For dynamic content updates (live regions)
- For custom interactive widgets (modals, tabs, tooltips)

**Key ARIA Patterns:**

| Component | ARIA Pattern | Example |
|-----------|-------------|---------|
| **Quiz Question** | `role="region"`, `aria-live="polite"` | Announce answer feedback to screen readers |
| **Competency Bars** | `role="progressbar"`, `aria-valuenow`, `aria-valuemin`, `aria-valuemax` | Progress visualization |
| **Modal Dialogs** | `role="dialog"`, `aria-modal="true"`, `aria-labelledby` | Reading content modal, settings |
| **Navigation Badge** | `aria-label="7 unread reading items"` | Reading queue count |
| **Loading States** | `aria-busy="true"`, `aria-live="assertive"` | Question loading |
| **Error Messages** | `role="alert"`, `aria-live="assertive"` | Form validation errors |

**Live Region Example:**
```tsx
// Answer feedback announces to screen readers
<div
  role="status"
  aria-live="polite"
  aria-atomic="true"
  className="answer-feedback"
>
  {isCorrect ? "Correct! Well done." : "Incorrect. Review the explanation below."}
</div>
```

### Keyboard Navigation Flow

**Tab Order Requirements:**
- All interactive elements accessible via `Tab` key
- Logical tab order follows visual layout (top-to-bottom, left-to-right)
- Focus trap implemented in modals (tab cycles within modal)
- Skip to main content link for screen reader users

**Keyboard Shortcuts:**
| Action | Shortcut | Context |
|--------|----------|---------|
| **Submit Answer** | `Enter` | When answer option focused |
| **Next Question** | `Enter` or `Space` | After reviewing explanation |
| **Close Modal** | `Esc` | Reading content, settings |
| **Navigate Quiz Options** | Arrow keys (optional enhancement) | Answer selection |

**Focus Management:**
```tsx
// After submitting answer, focus moves to explanation
useEffect(() => {
  if (answerSubmitted) {
    explanationRef.current?.focus();
  }
}, [answerSubmitted]);
```

### Screen Reader Support

**Testing Requirements:**
- Test with NVDA (Windows), JAWS (Windows), VoiceOver (macOS/iOS)
- All interactive elements have descriptive labels
- Dynamic content changes announced via ARIA live regions
- Images have meaningful `alt` text (or `alt=""` for decorative images)

**Screen Reader Optimizations:**
- Competency scores announced as percentages: "Business Analysis Planning and Monitoring: 73 percent"
- Question progress: "Question 5 of 12"
- Review status: "This is a review question from 3 days ago"
- Reading priority: "High priority reading item"

### Color Contrast Requirements

**WCAG AA Standards:**
- **Normal text (< 18px):** Minimum 4.5:1 contrast ratio
- **Large text (≥ 18px or 14px bold):** Minimum 3:1 contrast ratio
- **Interactive elements:** Minimum 3:1 contrast for borders/icons

**Validation Process:**
- All color combinations validated using WebAIM Contrast Checker
- Design tokens include contrast ratios in documentation
- Automated contrast testing in CI pipeline (axe-core)

**Dark Mode Considerations:**
- Dark mode palette independently validated for contrast
- Enhanced contrast in dark mode (ratios often exceed WCAG AA)
- Text size increased in dark mode (17px vs 16px) for better readability

### Focus Indicators

**Visibility Requirements:**
- All interactive elements have visible focus indicator
- Focus outline: 2px solid, high contrast color
- Minimum 3:1 contrast ratio against background
- Focus indicators never removed (`outline: none` prohibited without replacement)

**Implementation:**
```css
/* Default focus style */
:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
  border-radius: 4px;
}

/* Custom focus for buttons */
.button:focus-visible {
  box-shadow: 0 0 0 3px rgba(0, 102, 204, 0.4);
}
```

### Form Accessibility

**Input Requirements:**
- Every input has associated `<label>` (explicit association via `for`/`id`)
- Required fields marked with `aria-required="true"` and visual indicator
- Error messages associated with inputs via `aria-describedby`
- Validation errors announced to screen readers via `role="alert"`

**Error Handling Example:**
```tsx
<div>
  <label htmlFor="email">Email Address *</label>
  <input
    id="email"
    type="email"
    aria-required="true"
    aria-invalid={hasError}
    aria-describedby={hasError ? "email-error" : undefined}
  />
  {hasError && (
    <div id="email-error" role="alert" className="error-message">
      Please enter a valid email address
    </div>
  )}
</div>
```

### Responsive & Mobile Accessibility

**Touch Target Size:**
- Minimum 44x44px touch targets (WCAG AAA guideline, adopted for quality)
- Adequate spacing between interactive elements (minimum 8px)
- Mobile buttons use pill-rounded design for larger touch area

**Zoom & Scaling:**
- Support 200% text zoom without loss of functionality
- No horizontal scrolling at 320px width (mobile)
- Responsive layout adapts to portrait and landscape orientations

### Motion & Animation Accessibility

**Respect User Preferences:**
```css
/* Disable animations for users who prefer reduced motion */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

**Animation Guidelines:**
- No flashing content (avoid seizure triggers)
- Animations are decorative, not required for understanding content
- Provide alternative feedback for users with reduced motion (e.g., instant state change instead of fade)

### Testing & Validation

**Automated Testing:**
- **axe-core** integrated into Playwright E2E tests (runs on every build)
- **eslint-plugin-jsx-a11y** for React accessibility linting
- Lighthouse accessibility audits (target score: 95+)

**Manual Testing:**
- Keyboard-only navigation testing (unplug mouse)
- Screen reader testing (NVDA, VoiceOver)
- Color contrast validation (WebAIM tool)
- Zoom testing (200% browser zoom)

**Accessibility Checklist (Pre-Release):**
- [ ] All interactive elements keyboard accessible
- [ ] Screen reader announces all dynamic content changes
- [ ] Color contrast meets WCAG AA for all text and icons
- [ ] Focus indicators visible on all interactive elements
- [ ] Forms have proper labels, error messages, and validation
- [ ] No keyboard traps (except intentional modal focus traps)
- [ ] Images have appropriate alt text
- [ ] Headings follow logical hierarchy
- [ ] ARIA used appropriately (not overused)
- [ ] Automated axe-core tests pass with 0 violations

### Accessibility Statement

**User-Facing Commitment:**
- Accessibility statement published at `/accessibility`
- Contact information for reporting accessibility issues
- Commitment to WCAG 2.1 Level AA compliance
- Known limitations documented (if any)
- Roadmap for accessibility improvements

---
