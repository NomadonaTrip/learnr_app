# AI UI Generation Prompt: Delete Completed Reading Materials

> **Usage:** Copy the prompt below into v0, Lovable, or similar AI UI generation tools to prototype this feature.

---

## Prompt for AI UI Tool

```
## High-Level Goal

Create UI components for a "Clear Completed Reading Materials" feature in an existing React learning application. Users need to remove completed reading items from their library to keep it focused on areas needing improvement.

## Tech Stack & Design System

- **Framework:** React 18+ with TypeScript
- **Styling:** Tailwind CSS
- **Component Library:** Headless UI for accessible dropdowns and modals
- **Primary Color:** Blue (blue-600 for buttons, blue-500 for focus rings)
- **Card Style:** White background, rounded-[14px], shadow-sm, hover:shadow-md
- **Button Style:** Rounded-lg, focus:ring-2 focus:ring-blue-500 focus:ring-offset-2

## Components to Create

### 1. ClearCompletedButton Component

Create a button component that appears in a filter bar when viewing completed items.

**Requirements:**
- Ghost/outline style button (not primary blue)
- Trash icon on the left side of text
- Text: "Clear All Completed" or dynamically "Clear {count} Completed"
- Muted gray styling by default: `text-gray-600 border-gray-300`
- Hover state: subtle red tint `hover:text-red-600 hover:border-red-300`
- Disabled state with spinner when loading
- Props: `count: number`, `onClick: () => void`, `isLoading: boolean`

**Example styling:**
```tsx
className="inline-flex items-center gap-2 px-4 py-2 border rounded-lg
           text-gray-600 border-gray-300 bg-white
           hover:text-red-600 hover:border-red-300 hover:bg-red-50
           disabled:opacity-50 disabled:cursor-not-allowed
           focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2
           transition-colors text-sm font-medium"
```

### 2. ClearConfirmationModal Component

Create a confirmation modal using Headless UI Dialog.

**Requirements:**
- Centered modal with backdrop overlay (bg-black/50)
- Click outside backdrop to dismiss
- White rounded-xl modal container, max-w-md
- Title: "Clear Completed Reading Materials?"
- Body text: "This will remove {count} items from your library. Your reading progress and statistics are preserved."
- Two buttons: Cancel (secondary/ghost) and "Clear Items" (subtle destructive)
- "Clear Items" button shows spinner and disables when `isLoading: true`
- Keyboard accessible: Escape to close, Enter to confirm
- Focus trap within modal
- **Focus management:** Return focus to triggering button after modal closes
- Props: `isOpen: boolean`, `onClose: () => void`, `onConfirm: () => void`, `count: number`, `isLoading: boolean`

**Modal structure:**
```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│   Clear Completed Reading Materials?                         │
│                                                              │
│   This will remove 12 items from your library.               │
│   Your reading progress and statistics are preserved.        │
│                                                              │
│                          [Cancel]  [Clear Items]             │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**Button styling:**
- Cancel: `px-4 py-2 text-gray-600 hover:text-gray-800 rounded-lg`
- Clear Items: `px-4 py-2 bg-red-50 text-red-700 hover:bg-red-100 rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed`

### 3. KebabMenu Component for Cards

Create a kebab menu (three dots) dropdown for completed reading cards.

**Requirements:**
- Three vertical dots icon button in top-right corner of card
- Icon button must be minimum 44x44px touch target (use `p-2 min-w-[44px] min-h-[44px]`)
- Dropdown menu with single option: "Remove from library" with trash icon
- Uses Headless UI Menu component
- Position: absolute top-right of parent card
- Menu item has red text on hover
- Props: `onRemove: () => void`

**Placement context:**
```tsx
<article className="relative bg-white rounded-[14px] shadow-sm p-6">
  {/* Kebab menu - only shown for completed items */}
  <div className="absolute top-4 right-4">
    <KebabMenu onRemove={() => handleRemove(queueId)} />
  </div>
  {/* Rest of card content */}
</article>
```

### 4. UndoToast Component

Create a toast notification with optional undo action. Supports both single-item removal (with undo) and batch success messages (no undo).

**Requirements:**
- Fixed position bottom-right
- White background with shadow-lg, rounded-lg
- Green checkmark icon, success message, and optional "Undo" button
- Auto-dismiss after 5 seconds (configurable via duration prop)
- Undo button: blue text, hover:underline (only shown when `onUndo` provided)
- Smooth slide-in animation from right
- Use `aria-live="polite"` for screen reader announcements
- Props: `message: string`, `onUndo?: () => void`, `duration?: number`

**Usage:**
- Single item removal: `<UndoToast message="Item removed" onUndo={handleUndo} />`
- Batch success: `<UndoToast message="Cleared 12 items from your library" />`

**Toast structure:**
```
┌──────────────────────────────────────────────────┐
│  ✓  Item removed from library          [Undo]   │
└──────────────────────────────────────────────────┘
```

## Code Examples & Constraints

**DO:**
- Use Tailwind CSS for all styling
- Use Headless UI for Modal (Dialog) and Menu components
- Include aria-labels for accessibility
- Handle keyboard navigation (Tab, Enter, Escape)
- Use TypeScript interfaces for all props
- Include loading and disabled states

**DO NOT:**
- Do not use any CSS-in-JS libraries
- Do not use inline styles
- Do not install additional UI libraries (no Radix, no Chakra)
- Do not create custom icons - use simple SVG or heroicons patterns

**Existing patterns to follow:**

Focus ring pattern:
```
focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
```

Card pattern:
```
bg-white rounded-[14px] shadow-sm hover:shadow-md transition-shadow
```

Button pattern:
```
px-4 py-2 rounded-lg font-medium transition-colors
```

## Scope

Create ONLY these 4 components:
1. `ClearCompletedButton.tsx`
2. `ClearConfirmationModal.tsx`
3. `KebabMenu.tsx`
4. `UndoToast.tsx`

Do NOT modify any existing components. These are new additions to the component library.

## Mobile-First Considerations

- Modal should be full-width on mobile (max-w-full on small screens)
- Toast should be centered on mobile, bottom-right on desktop
- Kebab menu dropdown should not overflow screen edges
- Touch targets minimum 44x44px for mobile
```

---

## Post-Generation Checklist

After the AI generates the code, verify:

- [ ] All components use TypeScript with proper interfaces
- [ ] Tailwind classes match existing design system
- [ ] Headless UI is used for Modal and Menu (not custom implementations)
- [ ] Keyboard navigation works (Tab, Enter, Escape)
- [ ] Focus states are visible and accessible
- [ ] Focus returns to trigger element after modal closes
- [ ] Loading states are implemented (especially on modal confirm button)
- [ ] Toast uses `aria-live="polite"` for screen reader announcements
- [ ] Touch targets are minimum 44x44px on mobile
- [ ] No external dependencies were added
- [ ] Mobile responsiveness is included

---

## Integration Notes

Once prototyped, integrate into existing components:

| New Component | Integrates Into |
|---------------|-----------------|
| `ClearCompletedButton` | `ReadingFilterBar.tsx` |
| `ClearConfirmationModal` | `ReadingLibraryPage.tsx` |
| `KebabMenu` | `ReadingCard.tsx` |
| `UndoToast` | App-level toast system or `ReadingLibraryPage.tsx` |

---

**Important Reminder:** All AI-generated code requires careful human review, testing, and refinement before being considered production-ready. The generated components should be validated against your existing codebase patterns and accessibility requirements.

---

*Prompt created by Sally, UX Expert*
