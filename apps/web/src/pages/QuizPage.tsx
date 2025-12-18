import { useQuizSession } from '../hooks/useQuizSession'
import type { SelectedQuestion } from '../services/quizService'

/**
 * Format session type for display.
 */
function formatSessionType(type: string | null): string {
  if (!type) return 'Unknown'
  const typeMap: Record<string, string> = {
    diagnostic: 'Diagnostic',
    adaptive: 'Adaptive',
    focused: 'Focused',
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
 * Question card component.
 */
function QuestionCard({
  question,
  selectedAnswer,
  onSelectAnswer,
  questionsRemaining,
}: {
  question: SelectedQuestion
  selectedAnswer: string | null
  onSelectAnswer: (answer: string) => void
  questionsRemaining: number
}) {
  const optionLabels = ['A', 'B', 'C', 'D']
  const optionEntries = Object.entries(question.options)

  return (
    <div
      className="bg-white rounded-[14px] shadow-sm border border-gray-200 p-6"
      aria-label="Question card"
    >
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

          return (
            <button
              key={key}
              onClick={() => onSelectAnswer(key)}
              className={`w-full text-left p-4 rounded-[14px] border-2 transition-all focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 ${
                isSelected
                  ? 'border-primary-500 bg-primary-50 text-primary-900'
                  : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50 text-gray-700'
              }`}
              role="radio"
              aria-checked={isSelected}
              aria-label={`Option ${label}: ${text}`}
            >
              <div className="flex items-start gap-3">
                <span
                  className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold ${
                    isSelected
                      ? 'bg-primary-500 text-white'
                      : 'bg-gray-100 text-gray-600'
                  }`}
                >
                  {label}
                </span>
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
}) {
  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-2xl mx-auto space-y-6">
        {/* Session Info */}
        <SessionInfoCard
          sessionType={sessionType}
          questionStrategy={questionStrategy}
          status="active"
          totalQuestions={totalQuestions}
          correctCount={correctCount}
          accuracy={accuracy}
        />

        {/* Question display */}
        {isFetchingQuestion ? (
          <QuestionLoading />
        ) : question ? (
          <QuestionCard
            question={question}
            selectedAnswer={selectedAnswer}
            onSelectAnswer={onSelectAnswer}
            questionsRemaining={questionsRemaining}
          />
        ) : (
          <div
            className="bg-white rounded-[14px] shadow-sm border border-gray-200 p-8 text-center"
            aria-label="No questions available"
          >
            <p className="text-gray-600">No questions available.</p>
          </div>
        )}

        {/* Submit button (shown when answer selected) */}
        {selectedAnswer && (
          <div className="flex justify-center">
            <button
              disabled
              className="px-8 py-3 bg-primary-600 text-white rounded-[14px] font-medium opacity-50 cursor-not-allowed"
              title="Answer submission will be available in Story 4.3"
            >
              Submit Answer (Coming Soon)
            </button>
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
 * Ended session state component.
 */
function EndedState({
  totalQuestions,
  correctCount,
  accuracy,
  onStartNew,
  onReturn,
}: {
  totalQuestions: number
  correctCount: number
  accuracy: number | null
  onStartNew: () => void
  onReturn: () => void
}) {
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

          {/* Placeholder for detailed results */}
          <p className="text-sm text-gray-400 text-center mb-6">
            Detailed results and review will be available in a future update.
          </p>

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
 */
export function QuizPage() {
  const {
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
    isLoading,
    isPausing,
    isResuming,
    isEnding,
    isFetchingQuestion,
    pause,
    resume,
    end,
    retry,
    startNew,
    returnToDashboard,
    selectAnswer,
  } = useQuizSession()

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
    />
  )
}
