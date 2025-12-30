/**
 * ReviewQuestion Component
 *
 * Displays a review question with answer options and feedback.
 * Supports inline feedback after submission showing correctness
 * and reinforcement status.
 *
 * Story 4.9: Post-Session Review Mode
 */
import { useReducedMotion } from '../../hooks/useReducedMotion'
import { CheckIcon, XIcon } from '../shared/icons'
import type { ReviewQuestionResponse, ReviewAnswerResponse } from '../../services/reviewService'

interface ReviewQuestionProps {
  /** Question data */
  question: ReviewQuestionResponse
  /** Currently selected answer */
  selectedAnswer: string | null
  /** Handler when user selects an answer */
  onSelectAnswer: (answer: string) => void
  /** Whether to show feedback (after submission) */
  showFeedback?: boolean
  /** Feedback result after submission */
  feedbackResult?: ReviewAnswerResponse | null
}

/**
 * Review question card with inline feedback support.
 */
export function ReviewQuestion({
  question,
  selectedAnswer,
  onSelectAnswer,
  showFeedback = false,
  feedbackResult = null,
}: ReviewQuestionProps) {
  const prefersReducedMotion = useReducedMotion()
  const optionLabels = ['A', 'B', 'C', 'D']
  const optionEntries = Object.entries(question.options)

  /**
   * Get the styling classes for an answer option based on feedback state.
   */
  const getOptionClasses = (key: string, isSelected: boolean): string => {
    const baseClasses = 'w-full text-left p-4 rounded-[14px] border-2 focus:outline-none focus:ring-2 focus:ring-offset-2'
    const transitionClasses = prefersReducedMotion ? '' : 'transition-all duration-200 ease-in-out'

    if (showFeedback && feedbackResult) {
      const isCorrectAnswer = key === feedbackResult.correct_answer
      const isUserSelection = isSelected

      if (isCorrectAnswer) {
        return `${baseClasses} ${transitionClasses} border-green-500 bg-green-50 text-green-800 cursor-default focus:ring-green-500`
      } else if (isUserSelection && !feedbackResult.is_correct) {
        return `${baseClasses} ${transitionClasses} border-red-500 bg-red-50 text-red-800 cursor-default focus:ring-red-500`
      } else {
        return `${baseClasses} ${transitionClasses} border-gray-200 bg-gray-50 text-gray-400 opacity-60 cursor-default focus:ring-gray-300`
      }
    }

    if (isSelected) {
      return `${baseClasses} ${transitionClasses} border-primary-500 bg-primary-50 text-primary-900 focus:ring-primary-500`
    }
    return `${baseClasses} ${transitionClasses} border-gray-200 hover:border-gray-300 hover:bg-gray-50 text-gray-700 focus:ring-primary-500`
  }

  /**
   * Get the icon badge for an option.
   */
  const getOptionBadge = (key: string, isSelected: boolean, label: string) => {
    if (showFeedback && feedbackResult) {
      const isCorrectAnswer = key === feedbackResult.correct_answer
      const isUserSelection = isSelected
      const animationClass = prefersReducedMotion ? '' : 'animate-icon-appear'

      if (isCorrectAnswer) {
        return (
          <span
            className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center bg-green-500 text-white ${animationClass}`}
          >
            <CheckIcon className="w-5 h-5" />
          </span>
        )
      } else if (isUserSelection && !feedbackResult.is_correct) {
        return (
          <span
            className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center bg-red-500 text-white ${animationClass}`}
          >
            <XIcon className="w-5 h-5" />
          </span>
        )
      } else {
        return (
          <span className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold bg-gray-200 text-gray-400">
            {label}
          </span>
        )
      }
    }

    return (
      <span
        className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold ${
          isSelected ? 'bg-primary-500 text-white' : 'bg-gray-100 text-gray-600'
        }`}
      >
        {label}
      </span>
    )
  }

  return (
    <div
      className="bg-white rounded-[14px] shadow-sm border border-gray-200 p-6"
      aria-label="Review question card"
    >
      {/* Screen reader announcement for feedback */}
      {showFeedback && feedbackResult && (
        <div
          role="status"
          aria-live="polite"
          aria-atomic="true"
          className="sr-only"
        >
          {feedbackResult.was_reinforced
            ? 'Great improvement! You got it right this time.'
            : feedbackResult.is_correct
              ? 'Correct!'
              : `Still incorrect. The correct answer is ${feedbackResult.correct_answer}.`}
        </div>
      )}

      {/* Review banner */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-amber-700 bg-amber-100 px-2 py-1 rounded">
            Review Mode
          </span>
          <span className="text-xs text-gray-400">
            Question {question.review_number} of {question.total_to_review}
          </span>
        </div>
      </div>

      {/* Question text */}
      <h2 className="text-lg font-medium text-gray-900 mb-6 leading-relaxed">
        {question.question_text}
      </h2>

      {/* Answer options */}
      <div className="space-y-3" role="radiogroup" aria-label="Answer options">
        {optionEntries.map(([key, text], index) => {
          const label = optionLabels[index] || key
          const isSelected = selectedAnswer === key
          const isDisabled = showFeedback

          return (
            <button
              key={key}
              onClick={() => !isDisabled && onSelectAnswer(key)}
              disabled={isDisabled}
              className={getOptionClasses(key, isSelected)}
              role="radio"
              aria-checked={isSelected}
              aria-disabled={isDisabled}
              aria-label={`Option ${label}: ${text}${
                showFeedback && feedbackResult
                  ? key === feedbackResult.correct_answer
                    ? '. Correct answer.'
                    : isSelected && !feedbackResult.is_correct
                      ? '. Your incorrect selection.'
                      : ''
                  : ''
              }`}
            >
              <div className="flex items-start gap-3">
                {getOptionBadge(key, isSelected, label)}
                <span className="pt-1">{text}</span>
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}

/**
 * Review feedback component shown after submitting an answer.
 */
export function ReviewFeedback({
  feedbackResult,
  onNextQuestion,
  isLastQuestion,
}: {
  feedbackResult: ReviewAnswerResponse
  onNextQuestion: () => void
  isLastQuestion: boolean
}) {
  const { was_reinforced, is_correct, explanation, feedback_message, reading_link } = feedbackResult

  // Determine feedback styling based on result
  const feedbackClasses = was_reinforced
    ? 'bg-green-50 border-green-200'
    : is_correct
      ? 'bg-green-50 border-green-200'
      : 'bg-amber-50 border-amber-200'

  const feedbackTextColor = was_reinforced
    ? 'text-green-800'
    : is_correct
      ? 'text-green-800'
      : 'text-amber-800'

  return (
    <div
      className={`rounded-[14px] border p-6 ${feedbackClasses}`}
      role="status"
      aria-live="polite"
    >
      {/* Reinforcement badge */}
      {was_reinforced && (
        <div className="flex items-center gap-2 mb-3">
          <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                clipRule="evenodd"
              />
            </svg>
            Reinforced!
          </span>
        </div>
      )}

      {/* Feedback message */}
      <p className={`font-semibold mb-3 ${feedbackTextColor}`}>
        {feedback_message}
      </p>

      {/* Explanation */}
      {explanation && (
        <div className="prose prose-sm max-w-none">
          <p className="text-gray-700">{explanation}</p>
        </div>
      )}

      {/* Study link for incorrect answers */}
      {!is_correct && reading_link && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <a
            href={reading_link}
            className="inline-flex items-center gap-2 text-sm text-primary-600 hover:text-primary-700 font-medium"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
              />
            </svg>
            Study this concept
          </a>
        </div>
      )}

      {/* Next button */}
      <div className="mt-6 flex justify-center">
        <button
          onClick={onNextQuestion}
          className="px-8 py-3 bg-primary-600 text-white rounded-[14px] font-medium hover:bg-primary-700 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
        >
          {isLastQuestion ? 'View Summary' : 'Next Question'}
        </button>
      </div>
    </div>
  )
}
