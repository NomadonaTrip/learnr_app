/**
 * ReviewPrompt Component
 *
 * Displays a prompt to the user after completing a quiz session
 * asking if they want to review their incorrect answers.
 *
 * Story 4.9: Post-Session Review Mode
 */

interface ReviewPromptProps {
  /** Number of incorrect questions available for review */
  incorrectCount: number
  /** Handler when user chooses to start review */
  onStartReview: () => void
  /** Handler when user chooses to skip review */
  onSkipReview: () => void
  /** Whether the start review action is loading */
  isStarting?: boolean
  /** Whether the skip action is loading */
  isSkipping?: boolean
}

/**
 * Prompt component shown after quiz completion when there are incorrect answers.
 */
export function ReviewPrompt({
  incorrectCount,
  onStartReview,
  onSkipReview,
  isStarting = false,
  isSkipping = false,
}: ReviewPromptProps) {
  const isDisabled = isStarting || isSkipping

  return (
    <div
      className="bg-white rounded-[14px] shadow-sm border border-gray-200 p-8 max-w-lg mx-auto"
      role="dialog"
      aria-labelledby="review-prompt-title"
      aria-describedby="review-prompt-description"
    >
      {/* Icon */}
      <div className="flex justify-center mb-4">
        <div
          className="w-16 h-16 rounded-full bg-amber-100 flex items-center justify-center"
          aria-hidden="true"
        >
          <svg
            className="w-8 h-8 text-amber-600"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        </div>
      </div>

      {/* Title */}
      <h2
        id="review-prompt-title"
        className="text-xl font-semibold text-gray-900 text-center mb-2"
      >
        Review Your Mistakes?
      </h2>

      {/* Description */}
      <p
        id="review-prompt-description"
        className="text-gray-600 text-center mb-6"
      >
        You got <span className="font-semibold text-amber-600">{incorrectCount}</span>{' '}
        {incorrectCount === 1 ? 'question' : 'questions'} wrong. Reviewing them now will help
        reinforce your learning and strengthen those concepts.
      </p>

      {/* Benefits */}
      <div className="bg-gray-50 rounded-lg p-4 mb-6">
        <p className="text-sm font-medium text-gray-700 mb-2">Benefits of Review:</p>
        <ul className="text-sm text-gray-600 space-y-1">
          <li className="flex items-start gap-2">
            <svg
              className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5 13l4 4L19 7"
              />
            </svg>
            <span>Reinforces correct understanding</span>
          </li>
          <li className="flex items-start gap-2">
            <svg
              className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5 13l4 4L19 7"
              />
            </svg>
            <span>Stronger belief updates for mastered concepts</span>
          </li>
          <li className="flex items-start gap-2">
            <svg
              className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5 13l4 4L19 7"
              />
            </svg>
            <span>Identify concepts needing more study</span>
          </li>
        </ul>
      </div>

      {/* Action buttons */}
      <div className="flex flex-col sm:flex-row gap-3">
        <button
          onClick={onStartReview}
          disabled={isDisabled}
          className="flex-1 px-6 py-3 bg-primary-600 text-white rounded-[14px] font-medium hover:bg-primary-700 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
          aria-label={`Start review of ${incorrectCount} incorrect questions`}
        >
          {isStarting ? 'Starting Review...' : `Review ${incorrectCount} ${incorrectCount === 1 ? 'Question' : 'Questions'}`}
        </button>
        <button
          onClick={onSkipReview}
          disabled={isDisabled}
          className="flex-1 px-6 py-3 border border-gray-300 text-gray-700 rounded-[14px] font-medium hover:bg-gray-50 transition-colors focus:outline-none focus:ring-2 focus:ring-gray-300 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
          aria-label="Skip review and continue"
        >
          {isSkipping ? 'Skipping...' : 'Skip for Now'}
        </button>
      </div>

      {/* Skip hint */}
      <p className="text-xs text-gray-400 text-center mt-4">
        You can always review your quiz history later from the dashboard.
      </p>
    </div>
  )
}
