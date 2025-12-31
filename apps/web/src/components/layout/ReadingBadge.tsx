/**
 * ReadingBadge Component
 * Story 5.6: Silent Badge Updates in Navigation
 *
 * Displays a circular badge with the count of unread reading items.
 * Only renders when count > 0. Includes accessibility features.
 */

interface ReadingBadgeProps {
  /** Number of unread items to display */
  count: number
  /** Additional CSS classes */
  className?: string
}

/**
 * Badge component for displaying unread reading item count.
 *
 * Features:
 * - Only renders when count > 0
 * - Accessible with role="status" for live region announcements
 * - aria-label provides context for screen readers
 * - Singular/plural grammar handling
 */
export function ReadingBadge({ count, className = '' }: ReadingBadgeProps) {
  // Don't render if count is 0 or negative
  if (count <= 0) {
    return null
  }

  // Format aria-label with proper singular/plural grammar
  const ariaLabel = `${count} unread reading ${count === 1 ? 'item' : 'items'}`

  return (
    <span
      role="status"
      aria-label={ariaLabel}
      className={`absolute -top-1 -right-2 bg-orange-500 text-white text-xs
                  font-bold rounded-full h-5 w-5 flex items-center justify-center
                  ${className}`}
    >
      {count > 99 ? '99+' : count}
    </span>
  )
}

export default ReadingBadge
