/**
 * ClearCompletedButton Component
 * Story 5.12: Clear Completed Reading Materials
 *
 * Ghost/outline style button for clearing all completed reading items.
 * Shows spinner when loading, disabled during API calls.
 * Accessible with proper ARIA labels.
 */
import { SpinnerIcon, TrashIcon } from '../shared/icons'

export interface ClearCompletedButtonProps {
  count: number
  onClick: () => void
  isLoading: boolean
}

export function ClearCompletedButton({
  count,
  onClick,
  isLoading,
}: ClearCompletedButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={isLoading || count === 0}
      aria-label={`Clear all ${count} completed items`}
      className="inline-flex items-center gap-2 px-4 py-2 border rounded-lg
                 text-gray-600 border-gray-300 bg-white
                 hover:text-red-600 hover:border-red-300 hover:bg-red-50
                 disabled:opacity-50 disabled:cursor-not-allowed
                 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2
                 transition-colors text-sm font-medium"
    >
      {isLoading ? (
        <SpinnerIcon className="h-4 w-4" />
      ) : (
        <TrashIcon className="h-4 w-4" />
      )}
      <span>Clear All Completed</span>
    </button>
  )
}
