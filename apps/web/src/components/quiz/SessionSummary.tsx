import type { SessionSummary as SessionSummaryType } from '../../services/quizService'

/**
 * Trophy icon for session completion.
 */
function TrophyIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
      aria-hidden="true"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"
      />
    </svg>
  )
}

/**
 * Format seconds into human-readable duration.
 */
function formatDuration(seconds: number): string {
  if (seconds < 60) {
    return `${seconds}s`
  }
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  if (remainingSeconds === 0) {
    return `${minutes}m`
  }
  return `${minutes}m ${remainingSeconds}s`
}

interface SessionSummaryProps {
  summary: SessionSummaryType
  onStartNew: () => void
  onReturnToDashboard: () => void
}

/**
 * SessionSummary Component
 * Story 4.7: Fixed-Length Session Auto-Completion
 *
 * Displays session completion summary with:
 * - Questions answered / target
 * - Accuracy percentage
 * - Correct answers count
 * - Concepts strengthened
 * - Session duration
 * - Total quizzes completed (lifetime)
 */
export function SessionSummary({
  summary,
  onStartNew,
  onReturnToDashboard,
}: SessionSummaryProps) {
  const {
    questions_answered,
    question_target,
    correct_count,
    accuracy,
    concepts_strengthened,
    quizzes_completed_total,
    session_duration_seconds,
  } = summary

  // Determine performance level for styling
  const performanceLevel =
    accuracy >= 80 ? 'excellent' : accuracy >= 60 ? 'good' : 'needs_work'

  const performanceColors = {
    excellent: {
      bg: 'bg-green-50',
      border: 'border-green-200',
      accent: 'text-green-600',
      button: 'bg-green-600 hover:bg-green-700 focus:ring-green-500',
    },
    good: {
      bg: 'bg-blue-50',
      border: 'border-blue-200',
      accent: 'text-blue-600',
      button: 'bg-blue-600 hover:bg-blue-700 focus:ring-blue-500',
    },
    needs_work: {
      bg: 'bg-orange-50',
      border: 'border-orange-200',
      accent: 'text-orange-600',
      button: 'bg-orange-600 hover:bg-orange-700 focus:ring-orange-500',
    },
  }

  const colors = performanceColors[performanceLevel]

  const performanceMessage =
    performanceLevel === 'excellent'
      ? 'Excellent work!'
      : performanceLevel === 'good'
        ? 'Good job!'
        : 'Keep practicing!'

  return (
    <div
      className={`rounded-[14px] p-6 ${colors.bg} border ${colors.border}`}
      role="alert"
      aria-live="polite"
      aria-label="Quiz session completed"
    >
      {/* Header with trophy */}
      <div className="flex items-center gap-3 mb-6">
        <div className={`w-14 h-14 rounded-full flex items-center justify-center bg-white shadow-sm`}>
          <TrophyIcon className={`w-8 h-8 ${colors.accent}`} />
        </div>
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Session Complete!</h2>
          <p className={`text-lg font-medium ${colors.accent}`}>{performanceMessage}</p>
        </div>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        {/* Questions */}
        <div className="bg-white rounded-[14px] p-4 shadow-sm">
          <p className="text-3xl font-bold text-gray-900">
            {questions_answered}/{question_target}
          </p>
          <p className="text-sm text-gray-500">Questions</p>
        </div>

        {/* Accuracy */}
        <div className="bg-white rounded-[14px] p-4 shadow-sm">
          <p className={`text-3xl font-bold ${colors.accent}`}>
            {Math.round(accuracy)}%
          </p>
          <p className="text-sm text-gray-500">Accuracy</p>
        </div>

        {/* Correct answers */}
        <div className="bg-white rounded-[14px] p-4 shadow-sm">
          <p className="text-3xl font-bold text-gray-900">{correct_count}</p>
          <p className="text-sm text-gray-500">Correct</p>
        </div>

        {/* Concepts strengthened */}
        <div className="bg-white rounded-[14px] p-4 shadow-sm">
          <p className="text-3xl font-bold text-gray-900">{concepts_strengthened}</p>
          <p className="text-sm text-gray-500">Concepts</p>
        </div>
      </div>

      {/* Additional stats */}
      <div className="flex justify-between items-center mb-6 px-2">
        <div className="text-center">
          <p className="text-lg font-semibold text-gray-700">
            {formatDuration(session_duration_seconds)}
          </p>
          <p className="text-xs text-gray-500">Duration</p>
        </div>
        <div className="h-8 w-px bg-gray-200" />
        <div className="text-center">
          <p className="text-lg font-semibold text-gray-700">{quizzes_completed_total}</p>
          <p className="text-xs text-gray-500">Total Quizzes</p>
        </div>
      </div>

      {/* Action buttons */}
      <div className="flex gap-3">
        <button
          onClick={onReturnToDashboard}
          className="flex-1 py-3 px-6 rounded-[14px] font-medium bg-white border border-gray-200 text-gray-700 hover:bg-gray-50 transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-400"
          aria-label="Return to dashboard"
        >
          Dashboard
        </button>
        <button
          onClick={onStartNew}
          className={`flex-1 py-3 px-6 rounded-[14px] font-medium text-white transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 ${colors.button}`}
          aria-label="Start a new quiz session"
        >
          New Quiz
        </button>
      </div>
    </div>
  )
}
