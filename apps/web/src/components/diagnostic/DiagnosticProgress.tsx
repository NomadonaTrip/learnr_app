import clsx from 'clsx'

interface DiagnosticProgressProps {
  currentIndex: number
  total: number
  coveragePercentage?: number
}

/**
 * Displays diagnostic progress indicator with progress bar and coverage meter.
 * Includes accessible labels and respects prefers-reduced-motion.
 */
export function DiagnosticProgress({
  currentIndex,
  total,
  coveragePercentage,
}: DiagnosticProgressProps) {
  // Display 1-indexed for user (Question 1 of 15, not Question 0 of 15)
  const displayIndex = currentIndex + 1
  const progressPercent = total > 0 ? Math.round((displayIndex / total) * 100) : 0

  return (
    <div className="mb-6 w-full">
      {/* Question counter */}
      <p className="text-sm text-gray-600 mb-2">
        Question {displayIndex} of {total}
      </p>

      {/* Progress bar */}
      <div
        className="h-2 bg-gray-200 rounded-full overflow-hidden"
        role="progressbar"
        aria-valuenow={displayIndex}
        aria-valuemin={1}
        aria-valuemax={total}
        aria-label={`Progress: question ${displayIndex} of ${total}`}
      >
        <div
          className={clsx(
            'h-full bg-primary-600',
            'transition-all duration-300 motion-reduce:transition-none'
          )}
          style={{ width: `${progressPercent}%` }}
        />
      </div>

      {/* Coverage meter (optional) */}
      {coveragePercentage !== undefined && (
        <div className="mt-3">
          <div className="flex justify-between items-center mb-1">
            <span className="text-xs text-gray-500">Concept coverage</span>
            <span className="text-xs text-gray-600 font-medium">
              {Math.round(coveragePercentage * 100)}%
            </span>
          </div>
          <div
            className="h-1 bg-gray-100 rounded-full overflow-hidden"
            role="progressbar"
            aria-valuenow={Math.round(coveragePercentage * 100)}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label={`Concept coverage: ${Math.round(coveragePercentage * 100)}%`}
          >
            <div
              className={clsx(
                'h-full bg-green-500',
                'transition-all duration-300 motion-reduce:transition-none'
              )}
              style={{ width: `${coveragePercentage * 100}%` }}
            />
          </div>
        </div>
      )}

      {/* Building profile message */}
      <p className="text-xs text-gray-500 mt-2">
        Building your knowledge profile...
      </p>
    </div>
  )
}
