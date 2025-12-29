/**
 * ContextCard Component
 * Story 5.8: Reading Item Detail View and Engagement Tracking
 *
 * Displays recommendation context explaining why a reading item
 * was recommended (typically after an incorrect answer).
 * Accessible with proper ARIA attributes.
 */
import { InformationCircleIcon } from '../shared/icons'

interface ContextCardProps {
  questionPreview: string | null
  wasIncorrect: boolean
  className?: string
}

export function ContextCard({
  questionPreview,
  wasIncorrect,
  className = '',
}: ContextCardProps) {
  if (!questionPreview) {
    return null
  }

  return (
    <aside
      role="complementary"
      aria-label="Why this was recommended"
      className={`bg-amber-50 border-l-4 border-amber-400 p-4 rounded-r-lg ${className}`}
    >
      <div className="flex items-start gap-3">
        <InformationCircleIcon className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
        <div>
          <p className="text-sm font-medium text-amber-800">
            {wasIncorrect
              ? 'Recommended after incorrect answer'
              : 'Recommended for you'}
          </p>
          <p className="text-sm text-amber-700 mt-1 line-clamp-2">
            &quot;{questionPreview}&quot;
          </p>
        </div>
      </div>
    </aside>
  )
}
