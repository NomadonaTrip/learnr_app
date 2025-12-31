/**
 * ReviewSummary Component
 *
 * Displays the summary of a completed review session including
 * reinforcement rate and study links for still-incorrect concepts.
 *
 * Story 4.9: Post-Session Review Mode
 */
import type { ReviewSummaryResponse } from '../../services/reviewService'

interface ReviewSummaryProps {
  /** Review summary data */
  summary: ReviewSummaryResponse
  /** Handler to return to dashboard */
  onReturnToDashboard: () => void
  /** Handler to start a new quiz */
  onStartNewQuiz?: () => void
}

/**
 * Review session summary component.
 */
export function ReviewSummary({
  summary,
  onReturnToDashboard,
  onStartNewQuiz,
}: ReviewSummaryProps) {
  const {
    total_reviewed,
    reinforced_count,
    still_incorrect_count,
    reinforcement_rate,
    still_incorrect_concepts,
  } = summary

  // Format reinforcement rate as percentage
  const reinforcementPercent = Math.round(reinforcement_rate * 100)

  // Determine overall message based on performance
  const getMessage = () => {
    if (reinforcementPercent >= 80) {
      return {
        title: 'Excellent Review!',
        message: 'You\'ve significantly reinforced your understanding.',
        emoji: '🎉',
        bgColor: 'bg-green-50',
        borderColor: 'border-green-200',
        textColor: 'text-green-800',
      }
    } else if (reinforcementPercent >= 50) {
      return {
        title: 'Good Progress!',
        message: 'You\'re making solid improvement on these concepts.',
        emoji: '👍',
        bgColor: 'bg-blue-50',
        borderColor: 'border-blue-200',
        textColor: 'text-blue-800',
      }
    } else if (reinforcementPercent > 0) {
      return {
        title: 'Keep Practicing',
        message: 'Some concepts need more attention. Check the study links below.',
        emoji: '📚',
        bgColor: 'bg-amber-50',
        borderColor: 'border-amber-200',
        textColor: 'text-amber-800',
      }
    } else {
      return {
        title: 'More Study Needed',
        message: 'These concepts are still challenging. Review the materials linked below.',
        emoji: '💪',
        bgColor: 'bg-amber-50',
        borderColor: 'border-amber-200',
        textColor: 'text-amber-800',
      }
    }
  }

  const { title, message, emoji, bgColor, borderColor, textColor } = getMessage()

  return (
    <div className="max-w-lg mx-auto space-y-6">
      {/* Summary card */}
      <div
        className="bg-white rounded-[14px] shadow-sm border border-gray-200 p-8"
        role="region"
        aria-label="Review session summary"
      >
        {/* Header with emoji */}
        <div className="text-center mb-6">
          <div className="text-5xl mb-3" aria-hidden="true">
            {emoji}
          </div>
          <h2 className="text-2xl font-bold text-gray-900">{title}</h2>
          <p className="text-gray-600 mt-1">{message}</p>
        </div>

        {/* Stats grid */}
        <div
          className="grid grid-cols-3 gap-4 mb-6"
          role="group"
          aria-label="Review statistics"
        >
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <p className="text-2xl font-bold text-gray-900">{total_reviewed}</p>
            <p className="text-xs text-gray-500">Reviewed</p>
          </div>
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <p className="text-2xl font-bold text-green-600">{reinforced_count}</p>
            <p className="text-xs text-gray-500">Reinforced</p>
          </div>
          <div className="text-center p-4 bg-amber-50 rounded-lg">
            <p className="text-2xl font-bold text-amber-600">{still_incorrect_count}</p>
            <p className="text-xs text-gray-500">Still Incorrect</p>
          </div>
        </div>

        {/* Reinforcement rate */}
        <div className={`${bgColor} ${borderColor} border rounded-lg p-4 mb-6`}>
          <div className="flex items-center justify-between">
            <span className={`text-sm font-medium ${textColor}`}>Reinforcement Rate</span>
            <span className={`text-lg font-bold ${textColor}`}>{reinforcementPercent}%</span>
          </div>
          {/* Progress bar */}
          <div className="mt-2 h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className={`h-full ${reinforcementPercent >= 50 ? 'bg-green-500' : 'bg-amber-500'} transition-all duration-500`}
              style={{ width: `${reinforcementPercent}%` }}
              role="progressbar"
              aria-valuenow={reinforcementPercent}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label={`Reinforcement rate: ${reinforcementPercent}%`}
            />
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex flex-col sm:flex-row gap-3">
          <button
            onClick={onReturnToDashboard}
            className="flex-1 px-6 py-3 bg-primary-600 text-white rounded-[14px] font-medium hover:bg-primary-700 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
          >
            Return to Dashboard
          </button>
          {onStartNewQuiz && (
            <button
              onClick={onStartNewQuiz}
              className="flex-1 px-6 py-3 border border-gray-300 text-gray-700 rounded-[14px] font-medium hover:bg-gray-50 transition-colors focus:outline-none focus:ring-2 focus:ring-gray-300 focus:ring-offset-2"
            >
              Start New Quiz
            </button>
          )}
        </div>
      </div>

      {/* Still incorrect concepts with study links */}
      {still_incorrect_concepts.length > 0 && (
        <div
          className="bg-white rounded-[14px] shadow-sm border border-gray-200 p-6"
          role="region"
          aria-label="Concepts needing review"
        >
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <svg
              className="w-5 h-5 text-amber-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
              />
            </svg>
            Concepts to Study
          </h3>
          <p className="text-sm text-gray-600 mb-4">
            These concepts were still incorrect after review. Click to access reading materials.
          </p>
          <ul className="space-y-2">
            {still_incorrect_concepts.map((concept) => (
              <li key={concept.concept_id}>
                <a
                  href={concept.reading_link}
                  className="flex items-center justify-between p-3 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors group"
                >
                  <span className="text-gray-800 font-medium">{concept.name}</span>
                  <svg
                    className="w-5 h-5 text-gray-400 group-hover:text-primary-600 transition-colors"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 5l7 7-7 7"
                    />
                  </svg>
                </a>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
