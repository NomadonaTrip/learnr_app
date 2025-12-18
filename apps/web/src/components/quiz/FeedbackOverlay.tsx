import type { AnswerResponse } from '../../services/quizService'

/**
 * Check icon for correct answers.
 */
function CheckIcon({ className }: { className?: string }) {
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
        d="M5 13l4 4L19 7"
      />
    </svg>
  )
}

/**
 * X icon for incorrect answers.
 */
function XIcon({ className }: { className?: string }) {
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
        d="M6 18L18 6M6 6l12 12"
      />
    </svg>
  )
}

interface FeedbackOverlayProps {
  feedbackResult: AnswerResponse
  onNextQuestion: () => void
  isLastQuestion?: boolean
}

/**
 * FeedbackOverlay Component
 *
 * Displays immediate feedback after answer submission.
 * - Correct: Green background, checkmark, "Correct!" message
 * - Incorrect: Orange background, X icon, shows correct answer
 * - Includes explanation and session stats
 */
export function FeedbackOverlay({
  feedbackResult,
  onNextQuestion,
  isLastQuestion = false,
}: FeedbackOverlayProps) {
  const { is_correct, correct_answer, explanation, session_stats } = feedbackResult

  return (
    <div
      className={`rounded-[14px] p-6 ${
        is_correct
          ? 'bg-green-50 border border-green-200'
          : 'bg-orange-50 border border-orange-200'
      }`}
      role="alert"
      aria-live="polite"
      aria-label={is_correct ? 'Correct answer feedback' : 'Incorrect answer feedback'}
    >
      {/* Result header */}
      <div className="flex items-center gap-3 mb-4">
        <div
          className={`w-12 h-12 rounded-full flex items-center justify-center ${
            is_correct ? 'bg-green-100' : 'bg-orange-100'
          }`}
        >
          {is_correct ? (
            <CheckIcon className="w-6 h-6 text-green-600" />
          ) : (
            <XIcon className="w-6 h-6 text-orange-600" />
          )}
        </div>
        <div>
          <h3
            className={`text-xl font-semibold ${
              is_correct ? 'text-green-800' : 'text-orange-800'
            }`}
          >
            {is_correct ? 'Correct!' : `Incorrect. The correct answer is ${correct_answer}`}
          </h3>
        </div>
      </div>

      {/* Explanation */}
      {explanation && (
        <div
          className={`mb-6 p-4 rounded-[14px] ${
            is_correct ? 'bg-green-100/50' : 'bg-orange-100/50'
          }`}
        >
          <p className="text-sm font-medium text-gray-700 mb-1">Explanation</p>
          <p className={`text-sm ${is_correct ? 'text-green-800' : 'text-orange-800'}`}>
            {explanation}
          </p>
        </div>
      )}

      {/* Session stats */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex gap-6">
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-900">
              {session_stats.questions_answered}
            </p>
            <p className="text-xs text-gray-500">Questions</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-green-600">
              {Math.round(session_stats.accuracy * 100)}%
            </p>
            <p className="text-xs text-gray-500">Accuracy</p>
          </div>
          {session_stats.coverage_progress > 0 && (
            <div className="text-center">
              <p className="text-2xl font-bold text-primary-600">
                {Math.round(session_stats.coverage_progress * 100)}%
              </p>
              <p className="text-xs text-gray-500">Coverage</p>
            </div>
          )}
        </div>
      </div>

      {/* Next question button */}
      <button
        onClick={onNextQuestion}
        className={`w-full py-3 px-6 rounded-[14px] font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 ${
          is_correct
            ? 'bg-green-600 hover:bg-green-700 text-white focus:ring-green-500'
            : 'bg-orange-600 hover:bg-orange-700 text-white focus:ring-orange-500'
        }`}
        aria-label={isLastQuestion ? 'Finish quiz session' : 'Proceed to next question'}
      >
        {isLastQuestion ? 'Finish Session' : 'Next Question'}
      </button>
    </div>
  )
}
