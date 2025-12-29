/**
 * PriorityBadge Component
 * Story 5.7: Reading Library Page with Queue Display
 *
 * Displays a colored badge indicating priority level.
 * High = red, Medium = orange, Low = blue
 */

export type PriorityLevel = 'High' | 'Medium' | 'Low'

interface PriorityBadgeProps {
  priority: PriorityLevel
  className?: string
}

const priorityStyles: Record<PriorityLevel, string> = {
  High: 'bg-red-500 text-white',
  Medium: 'bg-orange-500 text-white',
  Low: 'bg-blue-500 text-white',
}

export function PriorityBadge({ priority, className = '' }: PriorityBadgeProps) {
  return (
    <span
      className={`px-2 py-1 text-xs font-semibold rounded-lg ${priorityStyles[priority]} ${className}`}
      aria-label={`${priority} priority`}
    >
      {priority}
    </span>
  )
}
