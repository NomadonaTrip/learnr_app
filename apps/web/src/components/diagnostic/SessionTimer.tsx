import { useState, useEffect, useCallback } from 'react'
import clsx from 'clsx'

const TOTAL_TIME_MS = 30 * 60 * 1000 // 30 minutes
const WARNING_TIME_MS = 25 * 60 * 1000 // 25 minutes (5 min remaining)

interface SessionTimerProps {
  startTime: Date | null
  onTimeout: () => void
  onWarning?: () => void
}

/**
 * Session timer with 30-minute countdown and 5-minute warning.
 * Displays remaining time and shows warning notification when 5 minutes remain.
 */
export function SessionTimer({
  startTime,
  onTimeout,
  onWarning,
}: SessionTimerProps) {
  const [elapsedMs, setElapsedMs] = useState(0)
  const [showWarning, setShowWarning] = useState(false)
  const [warningDismissed, setWarningDismissed] = useState(false)

  // Calculate initial elapsed time from startTime
  const getElapsedMs = useCallback(() => {
    if (!startTime) return 0
    return Date.now() - startTime.getTime()
  }, [startTime])

  useEffect(() => {
    if (!startTime) return

    // Set initial elapsed time
    setElapsedMs(getElapsedMs())

    const interval = setInterval(() => {
      const newElapsed = getElapsedMs()
      setElapsedMs(newElapsed)

      // Show warning at 25 minutes
      if (newElapsed >= WARNING_TIME_MS && !showWarning) {
        setShowWarning(true)
        onWarning?.()
      }

      // Trigger timeout at 30 minutes
      if (newElapsed >= TOTAL_TIME_MS) {
        onTimeout()
        clearInterval(interval)
      }
    }, 1000)

    return () => clearInterval(interval)
  }, [startTime, getElapsedMs, onTimeout, onWarning, showWarning])

  const remainingMs = Math.max(0, TOTAL_TIME_MS - elapsedMs)
  const minutes = Math.floor(remainingMs / 60000)
  const seconds = Math.floor((remainingMs % 60000) / 1000)
  const isUrgent = remainingMs <= WARNING_TIME_MS - 25 * 60 * 1000 + 5 * 60 * 1000 // Last 5 minutes

  if (!startTime) return null

  return (
    <div className="relative">
      {/* Timer display */}
      <div
        className={clsx(
          'text-sm',
          isUrgent ? 'text-red-600 font-medium' : 'text-gray-500'
        )}
      >
        Time remaining: {minutes}:{seconds.toString().padStart(2, '0')}
      </div>

      {/* Warning toast notification */}
      {showWarning && !warningDismissed && (
        <div
          role="alert"
          aria-live="assertive"
          className={clsx(
            'fixed top-4 right-4 z-50',
            'bg-yellow-50 border border-yellow-200 rounded-card',
            'px-4 py-3 shadow-lg',
            'flex items-start gap-3',
            'max-w-sm'
          )}
        >
          <svg
            className="w-5 h-5 text-yellow-600 shrink-0 mt-0.5"
            fill="currentColor"
            viewBox="0 0 20 20"
            aria-hidden="true"
          >
            <path
              fillRule="evenodd"
              d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z"
              clipRule="evenodd"
            />
          </svg>
          <div className="flex-1">
            <p className="text-sm font-medium text-yellow-800">
              5 minutes remaining!
            </p>
            <p className="text-xs text-yellow-700 mt-1">
              Complete your diagnostic soon to save your progress.
            </p>
          </div>
          <button
            type="button"
            onClick={() => setWarningDismissed(true)}
            className="text-yellow-600 hover:text-yellow-800"
            aria-label="Dismiss warning"
          >
            <svg
              className="w-4 h-4"
              fill="currentColor"
              viewBox="0 0 20 20"
              aria-hidden="true"
            >
              <path
                fillRule="evenodd"
                d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                clipRule="evenodd"
              />
            </svg>
          </button>
        </div>
      )}
    </div>
  )
}
