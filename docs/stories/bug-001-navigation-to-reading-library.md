# Bug Report: BUG-001 - Missing Navigation to Reading Library

## Status

**Resolved**

## Summary

Users cannot navigate to the Reading Library from the Diagnostic Results page (dashboard). The "View Study Plan" button incorrectly navigates to a placeholder `/study-plan` route instead of the Reading Library at `/reading-library`.

## Severity

**Medium** - Feature accessibility issue; users cannot discover/access implemented functionality

## Environment

- Component: Frontend (React)
- Pages Affected: `DiagnosticResultsPage.tsx`, `ReadingLibraryPage.tsx`
- Route: `/diagnostic/results`

## Steps to Reproduce

1. Complete the diagnostic assessment
2. View the Diagnostic Results page (dashboard)
3. Observe the "View Study Plan" button in the Recommendations section
4. Click the button
5. User is navigated to `/study-plan` (placeholder page) instead of `/reading-library`

## Expected Behavior

- The button should be labeled "View Reading Library" (or similar)
- Clicking the button should navigate to `/reading-library`
- The Navigation component with Reading Library link should be present on the page

## Actual Behavior

- Button is labeled "View Study Plan"
- Button navigates to `/study-plan` (a placeholder page for a future feature)
- No Navigation component is present, so no Reading Library link is visible

## Root Cause Analysis

1. **Incorrect Button**: The "View Study Plan" button was implemented referencing a future feature ("Personalized study plans with AI coaching" - PRD product-scope.md line 114) rather than the MVP Reading Library feature.

2. **Missing Navigation Component**: The `DiagnosticResultsPage` does not include the `<Navigation />` component that provides the Reading Library link with badge.

## PRD Reference

Per PRD `product-scope.md`:
- **Reading Library** (lines 34-44): MVP feature - "Asynchronous Reading Library" for curated study materials
- **Study Plan** (line 114): Future/Vision feature - "Personalized study plans with AI coaching" (explicitly deferred)

Per PRD `epic-5.md` Story 5.7:
- "Dedicated page/route: `/reading-library` accessible from main navigation"

## Affected Files

| File | Issue |
|------|-------|
| `apps/web/src/pages/DiagnosticResultsPage.tsx` | Missing `<Navigation />` component; incorrect "View Study Plan" button |
| `apps/web/src/pages/ReadingLibraryPage.tsx` | Should also include `<Navigation />` component for consistency |

## Proposed Fix

### 1. Update DiagnosticResultsPage.tsx

```tsx
// Add import
import { Navigation } from '../components/layout/Navigation'

// Change handler name and route
const handleViewReadingLibrary = useCallback(() => {
  navigate('/reading-library')
}, [navigate])

// Add Navigation component to render
return (
  <div className="min-h-screen bg-gray-50">
    <Navigation />
    {/* ... rest of content */}
  </div>
)

// Update button label from "View Study Plan" to "View Reading Library"
```

### 2. Update ReadingLibraryPage.tsx

```tsx
// Add Navigation component for consistency
import { Navigation } from '../components/layout/Navigation'

return (
  <div className="min-h-screen bg-gray-50">
    <Navigation enablePolling={false} />
    {/* ... rest of content */}
  </div>
)
```

## Acceptance Criteria for Fix

- [ ] "View Study Plan" button renamed to "View Reading Library"
- [ ] Button navigates to `/reading-library` route
- [ ] `DiagnosticResultsPage` includes `<Navigation />` component
- [ ] `ReadingLibraryPage` includes `<Navigation />` component
- [ ] Reading Library link with badge is visible on all authenticated pages
- [ ] Unit tests updated to reflect navigation changes

## Related Issues

- **BUG-002**: Reading Queue Not Populating (Redis Connection Refused) - Infrastructure issue preventing queue population

## Reporter

Quinn (Test Architect) - QA Review

## Date Reported

2025-12-26

## Resolution

**Fixed on 2025-12-26**

Changes made:
1. `apps/web/src/pages/DiagnosticResultsPage.tsx`:
   - Added `Navigation` component import and render
   - Renamed `handleViewStudyPlan` to `handleViewReadingLibrary`
   - Updated navigation route from `/study-plan` to `/reading-library`

2. `apps/web/src/components/diagnostic-results/RecommendationsSection.tsx`:
   - Renamed prop `onViewStudyPlan` to `onViewReadingLibrary`
   - Updated button text from "View Study Plan" to "View Reading Library"
   - Updated icon to book icon (matching Reading Library theme)
   - Updated aria-label to "View your curated reading library"

3. `apps/web/src/pages/ReadingLibraryPage.tsx`:
   - Added `Navigation` component for consistent navigation across authenticated pages

All related tests pass (54/54).

## Change Log

| Date | Description | Author |
|------|-------------|--------|
| 2025-12-26 | Bug report created from QA investigation | Quinn (Test Architect) |
| 2025-12-26 | Bug fixed - Navigation and button updated | Developer |
