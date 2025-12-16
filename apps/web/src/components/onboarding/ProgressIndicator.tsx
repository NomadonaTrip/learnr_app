interface ProgressIndicatorProps {
  currentQuestion: number
  totalQuestions: number
}

/**
 * Progress indicator showing "Question X of Y" with visual progress bar.
 */
export function ProgressIndicator({
  currentQuestion,
  totalQuestions,
}: ProgressIndicatorProps) {
  const progressPercentage = ((currentQuestion - 1) / totalQuestions) * 100

  return (
    <div className="w-full" role="progressbar" aria-valuenow={currentQuestion} aria-valuemin={1} aria-valuemax={totalQuestions} aria-label={`Question ${currentQuestion} of ${totalQuestions}`}>
      {/* Progress bar */}
      <div className="h-1 bg-charcoal/10 rounded-full overflow-hidden mb-4">
        <div
          className="h-full bg-primary-500 transition-all duration-300 ease-out"
          style={{ width: `${progressPercentage}%` }}
        />
      </div>

      {/* Text indicator */}
      <p className="text-sm text-charcoal/60 font-medium">
        Question {currentQuestion} of {totalQuestions}
      </p>
    </div>
  )
}
