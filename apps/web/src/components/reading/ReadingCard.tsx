/**
 * ReadingCard Component
 * Story 5.7: Reading Library Page with Queue Display
 * Story 5.12: Clear Completed Reading Materials
 *
 * Displays a reading queue item as a card with priority, title,
 * preview, context, and "Read Now" CTA button.
 * Shows kebab menu for completed items to allow removal.
 * Accessible with keyboard navigation and screen reader support.
 */
import { PriorityBadge, type PriorityLevel } from '../common/PriorityBadge'
import { KebabMenu } from './KebabMenu'

export interface ReadingCardProps {
  queueId: string
  title: string
  preview: string
  babokSection: string
  kaName: string
  priority: PriorityLevel
  estimatedReadMinutes: number
  questionPreview?: string
  wasIncorrect?: boolean
  addedAt: string
  onReadNow: (queueId: string) => void
  /** Current status of the item (for conditional kebab menu) */
  status?: string
  /** Handler for removing item from library (only for completed items) */
  onRemove?: (queueId: string) => void
}

export function ReadingCard({
  queueId,
  title,
  preview,
  babokSection,
  kaName,
  priority,
  estimatedReadMinutes,
  questionPreview,
  wasIncorrect,
  onReadNow,
  status,
  onRemove,
}: ReadingCardProps) {
  const titleId = `card-title-${queueId}`
  const showKebabMenu = status === 'completed' && onRemove

  return (
    <article
      role="article"
      aria-labelledby={titleId}
      tabIndex={0}
      className="relative bg-white rounded-[14px] shadow-sm p-6 hover:shadow-md transition-shadow
                 focus:outline-none focus:ring-2 focus:ring-blue-500"
    >
      {/* Kebab menu for completed items */}
      {showKebabMenu && (
        <div className="absolute top-4 right-4">
          <KebabMenu onRemove={() => onRemove(queueId)} />
        </div>
      )}
      <div className="flex items-start gap-4">
        <PriorityBadge priority={priority} />
        <div className="flex-1">
          <h3 id={titleId} className="font-semibold text-gray-900">
            {babokSection}: {title}
          </h3>
          <p className="text-gray-600 text-sm mt-1 line-clamp-2">{preview}</p>
          {questionPreview && wasIncorrect && (
            <p className="text-gray-500 text-xs mt-2 italic">
              Added after incorrect answer on: &quot;{questionPreview}&quot;
            </p>
          )}
          <div className="flex items-center gap-3 mt-3">
            <span className="text-xs bg-gray-100 px-2 py-1 rounded">{kaName}</span>
            <span className="text-xs text-gray-500">{estimatedReadMinutes} min read</span>
          </div>
          <button
            onClick={() => onReadNow(queueId)}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700
                       focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            Read Now
          </button>
        </div>
      </div>
    </article>
  )
}
