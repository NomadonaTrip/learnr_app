import { useEffect, useRef } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { useQuizSession } from '../hooks/useQuizSession'
import { useReview } from '../hooks/useReview'
import { useReducedMotion } from '../hooks/useReducedMotion'
import type { SelectedQuestion, AnswerResponse } from '../services/quizService'
import { InlineExplanation } from '../components/quiz/InlineExplanation'
import { FocusContextBanner } from '../components/quiz/FocusContextBanner'
import { CheckIcon, XIcon } from '../components/shared/icons'
import { Navigation } from '../components/layout/Navigation'
import { ReviewPrompt, ReviewQuestion, ReviewFeedback, ReviewSummary } from '../components/review'
// Note: FeedbackOverlay retained in codebase for session summary overlay (future use)

/**
 * Format session type for display.
 */
function formatSessionType(type: string | null): string {
  if (!type) return 'Unknown'
  const typeMap: Record<string, string> = {
    diagnostic: 'Diagnostic',
    adaptive: 'Adaptive',
    focused: 'Focused',
    focused_ka: 'Focused KA',
    focused_concept: 'Focused Concept',
    review: 'Review',
  }
  return typeMap[type] || type
}

/**
 * Format question strategy for display.
 */
function formatStrategy(strategy: string | null): string {
  if (!strategy) return 'Unknown'
  const strategyMap: Record<string, string> = {
    max_info_gain: 'Maximum Information Gain',
    max_uncertainty: 'Maximum Uncertainty',
    prerequisite_first: 'Prerequisite First',
    balanced: 'Balanced',
  }
  return strategyMap[strategy] || strategy
}

/**
 * Loading state component.
 */
function LoadingState({ isResumed }: { isResumed: boolean }) {
  return (
    <div
      className="min-h-screen bg-gray-50 flex items-center justify-center"
      role="status"
      aria-live="polite"
      aria-label={isResumed ? 'Resuming session' : 'Starting new session'}
    >
      <div className="text-center">
        <div
          className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"
          aria-hidden="true"
        />
        <p className="text-gray-600 text-lg">
          {isResumed ? 'Resuming session...' : 'Starting quiz session...'}
        </p>
      </div>
    </div>
  )
}

/**
 * Error state component.
 */
function ErrorState({
  error,
  onRetry,
  onReturn,
}: {
  error: string
  onRetry: () => void
  onReturn: () => void
}) {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div
        className="text-center max-w-md"
        role="alert"
        aria-live="assertive"
      >
        <div
          className="w-16 h-16 mx-auto mb-4 rounded-full bg-red-100 flex items-center justify-center"
          aria-hidden="true"
        >
          <svg
            className="w-8 h-8 text-red-600"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
        </div>
        <h1 className="text-xl font-semibold text-gray-900 mb-2">
          Unable to Start Session
        </h1>
        <p className="text-gray-600 mb-6">{error}</p>
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <button
            onClick={onRetry}
            className="px-6 py-2.5 bg-primary-600 text-white rounded-[14px] hover:bg-primary-700 transition-colors font-medium focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
          >
            Try Again
          </button>
          <button
            onClick={onReturn}
            className="px-6 py-2.5 border border-gray-300 text-gray-700 rounded-[14px] hover:bg-gray-50 transition-colors font-medium focus:outline-none focus:ring-2 focus:ring-gray-300 focus:ring-offset-2"
          >
            Return to Results
          </button>
        </div>
      </div>
    </div>
  )
}

/**
 * Session info card component.
 */
function SessionInfoCard({
  sessionType,
  questionStrategy,
  status,
  totalQuestions,
  correctCount,
  accuracy,
}: {
  sessionType: string | null
  questionStrategy: string | null
  status: string
  totalQuestions: number
  correctCount: number
  accuracy: number | null
}) {
  return (
    <div
      className="bg-white rounded-[14px] shadow-sm border border-gray-200 p-6"
      aria-label="Session information"
    >
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Session Info</h2>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <p className="text-sm text-gray-500">Type</p>
          <p className="font-medium text-gray-900">{formatSessionType(sessionType)}</p>
        </div>
        <div>
          <p className="text-sm text-gray-500">Strategy</p>
          <p className="font-medium text-gray-900">{formatStrategy(questionStrategy)}</p>
        </div>
        <div>
          <p className="text-sm text-gray-500">Status</p>
          <p className="font-medium text-gray-900 capitalize">{status}</p>
        </div>
        <div>
          <p className="text-sm text-gray-500">Progress</p>
          <p className="font-medium text-gray-900">
            {totalQuestions > 0
              ? `${correctCount}/${totalQuestions} correct`
              : 'No questions yet'}
          </p>
        </div>
        {accuracy !== null && (
          <div className="col-span-2">
            <p className="text-sm text-gray-500">Accuracy</p>
            <p className="font-medium text-gray-900">{accuracy}%</p>
          </div>
        )}
      </div>
    </div>
  )
}

/**
 * Question loading state component.
 */
function QuestionLoading() {
  return (
    <div
      className="bg-white rounded-[14px] shadow-sm border border-gray-200 p-8"
      role="status"
      aria-live="polite"
      aria-label="Loading question"
    >
      <div className="animate-pulse space-y-4">
        <div className="h-6 bg-gray-200 rounded w-3/4" />
        <div className="h-4 bg-gray-200 rounded w-1/2" />
        <div className="space-y-3 mt-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-12 bg-gray-200 rounded" />
          ))}
        </div>
      </div>
    </div>
  )
}

/**
 * Question card component with inline feedback support.
 */
function QuestionCard({
  question,
  selectedAnswer,
  onSelectAnswer,
  questionsRemaining,
  showFeedback = false,
  feedbackResult = null,
}: {
  question: SelectedQuestion
  selectedAnswer: string | null
  onSelectAnswer: (answer: string) => void
  questionsRemaining: number
  showFeedback?: boolean
  feedbackResult?: AnswerResponse | null
}) {
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
        // Correct answer - always green
        return `${baseClasses} ${transitionClasses} border-green-500 bg-green-50 text-green-800 cursor-default focus:ring-green-500`
      } else if (isUserSelection && !feedbackResult.is_correct) {
        // User's incorrect selection - red
        return `${baseClasses} ${transitionClasses} border-red-500 bg-red-50 text-red-800 cursor-default focus:ring-red-500`
      } else {
        // Neutral option (not selected, not correct)
        return `${baseClasses} ${transitionClasses} border-gray-200 bg-gray-50 text-gray-400 opacity-60 cursor-default focus:ring-gray-300`
      }
    }

    // Default interactive state (no feedback)
    if (isSelected) {
      return `${baseClasses} ${transitionClasses} border-primary-500 bg-primary-50 text-primary-900 focus:ring-primary-500`
    }
    return `${baseClasses} ${transitionClasses} border-gray-200 hover:border-gray-300 hover:bg-gray-50 text-gray-700 focus:ring-primary-500`
  }

  /**
   * Get the icon badge styling and content for an option.
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
        // Neutral - show label
        return (
          <span className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold bg-gray-200 text-gray-400">
            {label}
          </span>
        )
      }
    }

    // Default state - show label with selection styling
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
      aria-label="Question card"
    >
      {/* Screen reader announcement for feedback */}
      {showFeedback && feedbackResult && (
        <div
          role="status"
          aria-live="polite"
          aria-atomic="true"
          className="sr-only"
        >
          {feedbackResult.is_correct
            ? 'Correct! Your answer was right.'
            : `Incorrect. The correct answer is ${feedbackResult.correct_answer}.`}
        </div>
      )}

      {/* Question header with metadata */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-gray-500 bg-gray-100 px-2 py-1 rounded">
            {question.knowledge_area_name || question.knowledge_area_id}
          </span>
          <span className="text-xs text-gray-400">
            Difficulty: {Math.round(question.difficulty * 100)}%
          </span>
        </div>
        <span className="text-xs text-gray-400">
          {questionsRemaining} questions remaining
        </span>
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

      {/* Concepts tested (debug info) */}
      {question.concepts_tested.length > 0 && (
        <div className="mt-6 pt-4 border-t border-gray-100">
          <p className="text-xs text-gray-400">
            Testing: {question.concepts_tested.join(', ')}
          </p>
        </div>
      )}
    </div>
  )
}

// Story 4.8: Focus context type for display
interface FocusContextDisplay {
  focusType: 'ka' | 'concept'
  focusTargetId: string
  focusTargetName?: string
}

/**
 * Active session state component.
 */
function ActiveState({
  sessionType,
  questionStrategy,
  totalQuestions,
  correctCount,
  accuracy,
  question,
  selectedAnswer,
  isFetchingQuestion,
  onSelectAnswer,
  onPause,
  onEnd,
  isPausing,
  isEnding,
  questionsRemaining,
  onSubmit,
  isSubmitting,
  feedbackResult,
  showFeedback,
  onNextQuestion,
  focusContext,
}: {
  sessionType: string | null
  questionStrategy: string | null
  totalQuestions: number
  correctCount: number
  accuracy: number | null
  question: SelectedQuestion | null
  selectedAnswer: string | null
  isFetchingQuestion: boolean
  onSelectAnswer: (answer: string) => void
  onPause: () => void
  onEnd: () => void
  isPausing: boolean
  isEnding: boolean
  questionsRemaining: number
  onSubmit: () => void
  isSubmitting: boolean
  feedbackResult: AnswerResponse | null
  showFeedback: boolean
  onNextQuestion: () => void
  focusContext?: FocusContextDisplay | null
}) {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation with Reading Badge - Story 5.6 */}
      <Navigation enablePolling={true} />

      <div className="py-8 px-4">
        <div className="max-w-2xl mx-auto space-y-6">
          {/* Story 4.8: Focus Context Banner */}
          {focusContext && (
            <FocusContextBanner
              focusType={focusContext.focusType}
              targetName={focusContext.focusTargetName || focusContext.focusTargetId}
            />
          )}

          {/* Session Info */}
          <SessionInfoCard
          sessionType={sessionType}
          questionStrategy={questionStrategy}
          status="active"
          totalQuestions={totalQuestions}
          correctCount={correctCount}
          accuracy={accuracy}
        />

        {/* Question display with inline feedback */}
        {isFetchingQuestion ? (
          <QuestionLoading />
        ) : question ? (
          <>
            <QuestionCard
              question={question}
              selectedAnswer={selectedAnswer}
              onSelectAnswer={onSelectAnswer}
              questionsRemaining={questionsRemaining}
              showFeedback={showFeedback}
              feedbackResult={feedbackResult}
            />

            {/* Inline explanation (shown after submission) */}
            {showFeedback && feedbackResult && feedbackResult.explanation && (
              <InlineExplanation
                explanation={feedbackResult.explanation}
                onNextQuestion={onNextQuestion}
                isLastQuestion={questionsRemaining === 0}
              />
            )}

            {/* Submit button (shown when answer selected, before feedback) */}
            {selectedAnswer && !showFeedback && (
              <div className="flex justify-center">
                <button
                  onClick={onSubmit}
                  disabled={isSubmitting}
                  className="px-8 py-3 bg-primary-600 text-white rounded-[14px] font-medium hover:bg-primary-700 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
                  aria-label="Submit answer"
                >
                  {isSubmitting ? 'Submitting...' : 'Submit Answer'}
                </button>
              </div>
            )}
          </>
        ) : (
          <div
            className="bg-white rounded-[14px] shadow-sm border border-gray-200 p-8 text-center"
            aria-label="No questions available"
          >
            <p className="text-gray-600">No questions available.</p>
          </div>
        )}

        {/* Action buttons */}
        <div
          className="flex flex-col sm:flex-row gap-3 justify-center"
          role="group"
          aria-label="Session controls"
        >
          <button
            onClick={onPause}
            disabled={isPausing || isEnding}
            className="px-6 py-2.5 border border-gray-300 text-gray-700 rounded-[14px] hover:bg-gray-50 transition-colors font-medium focus:outline-none focus:ring-2 focus:ring-gray-300 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="Pause session"
          >
            {isPausing ? 'Pausing...' : 'Pause Session'}
          </button>
          <button
            onClick={onEnd}
            disabled={isPausing || isEnding}
            className="px-6 py-2.5 bg-red-600 text-white rounded-[14px] hover:bg-red-700 transition-colors font-medium focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="End session"
          >
            {isEnding ? 'Ending...' : 'End Session'}
          </button>
        </div>
        </div>
      </div>
    </div>
  )
}

/**
 * Paused session state component.
 */
function PausedState({
  sessionType,
  questionStrategy,
  totalQuestions,
  correctCount,
  accuracy,
  onResume,
  onEnd,
  isResuming,
  isEnding,
}: {
  sessionType: string | null
  questionStrategy: string | null
  totalQuestions: number
  correctCount: number
  accuracy: number | null
  onResume: () => void
  onEnd: () => void
  isResuming: boolean
  isEnding: boolean
}) {
  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-2xl mx-auto space-y-6">
        {/* Paused banner */}
        <div
          className="bg-amber-50 border border-amber-200 rounded-[14px] p-4 text-center"
          role="status"
          aria-live="polite"
        >
          <div className="flex items-center justify-center gap-2 text-amber-700">
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <span className="font-medium">Session Paused</span>
          </div>
          <p className="text-sm text-amber-600 mt-1">
            Your progress has been saved. Resume when you're ready.
          </p>
        </div>

        {/* Session Info */}
        <SessionInfoCard
          sessionType={sessionType}
          questionStrategy={questionStrategy}
          status="paused"
          totalQuestions={totalQuestions}
          correctCount={correctCount}
          accuracy={accuracy}
        />

        {/* Action buttons */}
        <div
          className="flex flex-col sm:flex-row gap-3 justify-center"
          role="group"
          aria-label="Session controls"
        >
          <button
            onClick={onResume}
            disabled={isResuming || isEnding}
            className="px-6 py-2.5 bg-primary-600 text-white rounded-[14px] hover:bg-primary-700 transition-colors font-medium focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="Resume session"
          >
            {isResuming ? 'Resuming...' : 'Resume Session'}
          </button>
          <button
            onClick={onEnd}
            disabled={isResuming || isEnding}
            className="px-6 py-2.5 border border-gray-300 text-gray-700 rounded-[14px] hover:bg-gray-50 transition-colors font-medium focus:outline-none focus:ring-2 focus:ring-gray-300 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="End session"
          >
            {isEnding ? 'Ending...' : 'End Session'}
          </button>
        </div>
      </div>
    </div>
  )
}

/**
 * Ended session state component with review integration.
 * Story 4.9: Post-Session Review Mode
 */
function EndedState({
  sessionId,
  totalQuestions,
  correctCount,
  accuracy,
  onStartNew,
  onReturn,
}: {
  sessionId: string | null
  totalQuestions: number
  correctCount: number
  accuracy: number | null
  onStartNew: () => void
  onReturn: () => void
}) {
  const navigate = useNavigate()
  const incorrectCount = totalQuestions - correctCount

  // Story 4.9: Review hook integration
  const {
    status: reviewStatus,
    totalToReview,
    currentQuestion: reviewQuestion,
    selectedAnswer: reviewSelectedAnswer,
    feedbackResult: reviewFeedback,
    showFeedback: reviewShowFeedback,
    isSubmitting: reviewIsSubmitting,
    summary: reviewSummary,
    isStartingReview,
    isFetchingQuestion: reviewIsFetchingQuestion,
    isSkipping,
    isCheckingAvailability,
    checkAvailability,
    startReview,
    skipReview,
    selectAnswer: reviewSelectAnswer,
    submitAnswer: reviewSubmitAnswer,
    proceedToNextQuestion: reviewProceedToNext,
  } = useReview({ originalSessionId: sessionId || undefined })

  // Check for review availability when component mounts (if there are incorrect answers)
  // Guard with isCheckingAvailability to prevent duplicate requests
  useEffect(() => {
    if (sessionId && incorrectCount > 0 && reviewStatus === 'idle' && !isCheckingAvailability) {
      checkAvailability(sessionId)
    }
  }, [sessionId, incorrectCount, reviewStatus, isCheckingAvailability, checkAvailability])

  // Show review prompt state
  if (reviewStatus === 'prompt' && totalToReview > 0) {
    return (
      <div className="min-h-screen bg-gray-50 py-8 px-4">
        <ReviewPrompt
          incorrectCount={totalToReview}
          onStartReview={startReview}
          onSkipReview={skipReview}
          isStarting={isStartingReview}
          isSkipping={isSkipping}
        />
      </div>
    )
  }

  // Show active review state
  if (reviewStatus === 'active' || reviewStatus === 'loading') {
    return (
      <div className="min-h-screen bg-gray-50 py-8 px-4">
        <div className="max-w-2xl mx-auto space-y-6">
          {/* Review header */}
          <div className="flex items-center justify-between">
            <h1 className="text-xl font-semibold text-gray-900">Review Session</h1>
            <button
              onClick={skipReview}
              disabled={isSkipping}
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              Exit Review
            </button>
          </div>

          {/* Question loading */}
          {reviewIsFetchingQuestion ? (
            <div
              className="bg-white rounded-[14px] shadow-sm border border-gray-200 p-8"
              role="status"
              aria-label="Loading question"
            >
              <div className="animate-pulse space-y-4">
                <div className="h-6 bg-gray-200 rounded w-3/4" />
                <div className="h-4 bg-gray-200 rounded w-1/2" />
                <div className="space-y-3 mt-6">
                  {[1, 2, 3, 4].map((i) => (
                    <div key={i} className="h-12 bg-gray-200 rounded" />
                  ))}
                </div>
              </div>
            </div>
          ) : reviewQuestion ? (
            <>
              <ReviewQuestion
                question={reviewQuestion}
                selectedAnswer={reviewSelectedAnswer}
                onSelectAnswer={reviewSelectAnswer}
                showFeedback={reviewShowFeedback}
                feedbackResult={reviewFeedback}
              />

              {/* Submit button (shown when answer selected, before feedback) */}
              {reviewSelectedAnswer && !reviewShowFeedback && (
                <div className="flex justify-center">
                  <button
                    onClick={reviewSubmitAnswer}
                    disabled={reviewIsSubmitting}
                    className="px-8 py-3 bg-primary-600 text-white rounded-[14px] font-medium hover:bg-primary-700 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {reviewIsSubmitting ? 'Submitting...' : 'Submit Answer'}
                  </button>
                </div>
              )}

              {/* Feedback after submission */}
              {reviewShowFeedback && reviewFeedback && (
                <ReviewFeedback
                  feedbackResult={reviewFeedback}
                  onNextQuestion={reviewProceedToNext}
                  isLastQuestion={reviewQuestion.review_number === reviewQuestion.total_to_review}
                />
              )}
            </>
          ) : null}
        </div>
      </div>
    )
  }

  // Show review summary state
  if (reviewStatus === 'completed' && reviewSummary) {
    return (
      <div className="min-h-screen bg-gray-50 py-8 px-4">
        <ReviewSummary
          summary={reviewSummary}
          onReturnToDashboard={() => navigate('/diagnostic/results')}
          onStartNewQuiz={onStartNew}
        />
      </div>
    )
  }

  // Default: Show standard ended state (no incorrect answers or review skipped)
  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-2xl mx-auto">
        <div className="bg-white rounded-[14px] shadow-sm border border-gray-200 p-8">
          {/* Completed icon */}
          <div className="text-center mb-6">
            <div
              className="w-16 h-16 mx-auto mb-4 rounded-full bg-green-100 flex items-center justify-center"
              aria-hidden="true"
            >
              <svg
                className="w-8 h-8 text-green-600"
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
            </div>
            <h1 className="text-2xl font-bold text-gray-900">Session Complete</h1>
            <p className="text-gray-500 mt-1">Great work! Here's your summary.</p>
          </div>

          {/* Summary stats */}
          <div
            className="bg-gray-50 rounded-[14px] p-6 mb-6"
            aria-label="Session summary"
          >
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <p className="text-3xl font-bold text-gray-900">{totalQuestions}</p>
                <p className="text-sm text-gray-500">Questions</p>
              </div>
              <div>
                <p className="text-3xl font-bold text-green-600">{correctCount}</p>
                <p className="text-sm text-gray-500">Correct</p>
              </div>
              <div>
                <p className="text-3xl font-bold text-primary-600">
                  {accuracy !== null ? `${accuracy}%` : '-'}
                </p>
                <p className="text-sm text-gray-500">Accuracy</p>
              </div>
            </div>
          </div>

          {/* Action buttons */}
          <div
            className="flex flex-col sm:flex-row gap-3 justify-center"
            role="group"
            aria-label="Next actions"
          >
            <button
              onClick={onStartNew}
              className="px-6 py-2.5 bg-primary-600 text-white rounded-[14px] hover:bg-primary-700 transition-colors font-medium focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
            >
              Start New Session
            </button>
            <button
              onClick={onReturn}
              className="px-6 py-2.5 border border-gray-300 text-gray-700 rounded-[14px] hover:bg-gray-50 transition-colors font-medium focus:outline-none focus:ring-2 focus:ring-gray-300 focus:ring-offset-2"
            >
              Return to Dashboard
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

/**
 * Quiz Page Component.
 *
 * Manages the adaptive quiz session lifecycle:
 * - Automatically starts a session on mount (or resumes if active session exists)
 * - Displays session info and question placeholder
 * - Supports pause/resume/end session actions
 * - Handles loading, error, and completion states
 * - Story 4.8: Supports focused sessions via URL query parameters
 */
export function QuizPage() {
  const [searchParams] = useSearchParams()
  const focusInitializedRef = useRef(false)

  // Parse focus parameters from URL
  const focusType = searchParams.get('focus') // 'ka' or 'concept'
  const focusTarget = searchParams.get('target') // KA ID for focused_ka
  const focusTargets = searchParams.get('targets') // Comma-separated concept IDs for focused_concept
  const focusName = searchParams.get('name') // Optional target name for display

  // Determine if this is a focused session from URL params
  const hasFocusParams = Boolean((focusType === 'ka' && focusTarget) || (focusType === 'concept' && focusTargets))

  const {
    sessionId,
    sessionType,
    questionStrategy,
    status,
    isResumed,
    totalQuestions,
    correctCount,
    accuracy,
    error,
    currentQuestion,
    questionsRemaining,
    selectedAnswer,
    feedbackResult,
    isSubmitting,
    showFeedback,
    isLoading,
    isPausing,
    isResuming,
    isEnding,
    isFetchingQuestion,
    // Story 4.8: Focus context and actions
    focusContext,
    startFocusedKA,
    startFocusedConcept,
    pause,
    resume,
    end,
    retry,
    startNew,
    returnToDashboard,
    selectAnswer,
    submitAnswer,
    proceedToNextQuestion,
  } = useQuizSession({ skipAutoStart: hasFocusParams })

  // Story 4.8: Start focused session based on URL parameters
  useEffect(() => {
    // DEBUG: Log URL parameters on mount
    console.log('[DEBUG] QuizPage focus params', {
      focusType,
      focusTarget,
      focusTargets,
      focusName,
      status,
      focusInitialized: focusInitializedRef.current,
      timestamp: new Date().toISOString(),
    })

    if (focusInitializedRef.current) {
      console.log('[DEBUG] QuizPage: Already initialized, skipping')
      return
    }
    if (status !== 'idle') {
      console.log('[DEBUG] QuizPage: Status not idle, skipping', { status })
      return
    }

    if (focusType === 'ka' && focusTarget) {
      console.log('[DEBUG] QuizPage: Starting focused KA session', { focusTarget, focusName })
      focusInitializedRef.current = true
      startFocusedKA(focusTarget, focusName || undefined)
    } else if (focusType === 'concept' && focusTargets) {
      const conceptIds = focusTargets.split(',').map(id => decodeURIComponent(id))
      console.log('[DEBUG] QuizPage: Starting focused concept session', { conceptIds })
      focusInitializedRef.current = true
      startFocusedConcept(conceptIds)
    } else {
      console.log('[DEBUG] QuizPage: No focus params or already handled')
    }
  }, [focusType, focusTarget, focusTargets, focusName, status, startFocusedKA, startFocusedConcept])

  // Loading state
  if (isLoading || status === 'loading') {
    return <LoadingState isResumed={isResumed} />
  }

  // Error state
  if (status === 'error' && error) {
    return (
      <ErrorState
        error={error}
        onRetry={retry}
        onReturn={returnToDashboard}
      />
    )
  }

  // Ended state
  if (status === 'ended') {
    return (
      <EndedState
        sessionId={sessionId}
        totalQuestions={totalQuestions}
        correctCount={correctCount}
        accuracy={accuracy}
        onStartNew={startNew}
        onReturn={returnToDashboard}
      />
    )
  }

  // Paused state
  if (status === 'paused') {
    return (
      <PausedState
        sessionType={sessionType}
        questionStrategy={questionStrategy}
        totalQuestions={totalQuestions}
        correctCount={correctCount}
        accuracy={accuracy}
        onResume={resume}
        onEnd={end}
        isResuming={isResuming}
        isEnding={isEnding}
      />
    )
  }

  // Active state (default)
  return (
    <ActiveState
      sessionType={sessionType}
      questionStrategy={questionStrategy}
      totalQuestions={totalQuestions}
      correctCount={correctCount}
      accuracy={accuracy}
      question={currentQuestion}
      selectedAnswer={selectedAnswer}
      isFetchingQuestion={isFetchingQuestion}
      onSelectAnswer={selectAnswer}
      onPause={pause}
      onEnd={end}
      isPausing={isPausing}
      isEnding={isEnding}
      questionsRemaining={questionsRemaining}
      onSubmit={submitAnswer}
      isSubmitting={isSubmitting}
      feedbackResult={feedbackResult}
      showFeedback={showFeedback}
      onNextQuestion={proceedToNextQuestion}
      focusContext={focusContext}
    />
  )
}
