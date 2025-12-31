/**
 * QuizProgress Component
 * Story 4.7: Fixed-Length Session Auto-Completion
 *
 * Displays session progress with:
 * - Current question number / target (e.g., "8 of 12")
 * - Visual progress bar
 * - Accuracy percentage
 */

interface QuizProgressProps {
  currentQuestionNumber: number
  questionTarget: number
  correctCount: number
  totalAnswered: number
}

export function QuizProgress({
  currentQuestionNumber,
  questionTarget,
  correctCount,
  totalAnswered,
}: QuizProgressProps) {
  // Calculate progress percentage (0-100)
  const progressPercentage = Math.round(
    ((currentQuestionNumber - 1) / questionTarget) * 100
  )

  // Calculate accuracy
  const accuracy = totalAnswered > 0 ? Math.round((correctCount / totalAnswered) * 100) : 0

  return (
    <div className="w-full" aria-label="Quiz progress">
      {/* Header with question count and accuracy */}
      <div className="flex justify-between items-center mb-2">
        <div className="flex items-center gap-2">
          <span className="text-lg font-semibold text-gray-900">
            Question {currentQuestionNumber}
          </span>
          <span className="text-sm text-gray-500">of {questionTarget}</span>
        </div>
        {totalAnswered > 0 && (
          <div className="flex items-center gap-1">
            <span
              className={`text-sm font-medium ${
                accuracy >= 70 ? 'text-green-600' : accuracy >= 50 ? 'text-orange-600' : 'text-red-600'
              }`}
            >
              {accuracy}%
            </span>
            <span className="text-xs text-gray-400">accuracy</span>
          </div>
        )}
      </div>

      {/* Progress bar */}
      <div
        className="w-full h-2 bg-gray-200 rounded-full overflow-hidden"
        role="progressbar"
        aria-valuenow={progressPercentage}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`Quiz progress: ${currentQuestionNumber - 1} of ${questionTarget} questions completed`}
      >
        <div
          className="h-full bg-primary-600 transition-all duration-300 ease-out rounded-full"
          style={{ width: `${progressPercentage}%` }}
        />
      </div>

      {/* Compact stats row */}
      <div className="flex justify-between items-center mt-2 text-xs text-gray-500">
        <span>{progressPercentage}% complete</span>
        <span>
          {correctCount}/{totalAnswered} correct
        </span>
      </div>
    </div>
  )
}
