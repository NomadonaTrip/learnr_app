import { useEffect, useCallback } from 'react'
import { useBlocker } from 'react-router-dom'
import { useDiagnostic } from '../hooks/useDiagnostic'
import { DiagnosticQuestionCard } from '../components/diagnostic/DiagnosticQuestionCard'
import { DiagnosticProgress } from '../components/diagnostic/DiagnosticProgress'
import { SessionTimer } from '../components/diagnostic/SessionTimer'

/**
 * Full-screen diagnostic assessment page.
 * Minimal chrome, no navigation header or sidebar.
 */
export function DiagnosticPage() {
  const {
    questions,
    currentIndex,
    currentQuestion,
    startTime,
    isSubmitting,
    isComplete,
    coveragePercentage,
    isLoading,
    isError,
    error,
    handleSubmitAnswer,
    handleTimeout,
    refetch,
  } = useDiagnostic()

  const diagnosticInProgress = questions.length > 0 && !isComplete

  // Block browser navigation (refresh, close tab)
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (diagnosticInProgress) {
        e.preventDefault()
        e.returnValue = 'Your diagnostic progress will be lost. Are you sure?'
        return e.returnValue
      }
    }

    window.addEventListener('beforeunload', handleBeforeUnload)
    return () => window.removeEventListener('beforeunload', handleBeforeUnload)
  }, [diagnosticInProgress])

  // Block React Router navigation (except to results page)
  const blocker = useBlocker(
    ({ currentLocation, nextLocation }) =>
      diagnosticInProgress &&
      currentLocation.pathname !== nextLocation.pathname &&
      !nextLocation.pathname.startsWith('/diagnostic/results')
  )

  // Handle warning callback
  const handleWarning = useCallback(() => {
    // Optional: Could log analytics here
  }, [])

  // Loading state
  if (isLoading) {
    return (
      <main className="min-h-screen flex flex-col items-center justify-center p-4 bg-gray-50">
        <div className="w-full max-w-2xl text-center">
          <div className="animate-pulse space-y-4">
            <div className="h-4 bg-gray-200 rounded w-32 mx-auto" />
            <div className="h-2 bg-gray-200 rounded-full w-full" />
            <div className="h-8 bg-gray-200 rounded w-3/4 mx-auto mt-8" />
            <div className="space-y-3 mt-6">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="h-14 bg-gray-200 rounded-card" />
              ))}
            </div>
          </div>
          <p className="text-gray-500 mt-6">Loading diagnostic questions...</p>
        </div>
      </main>
    )
  }

  // Error state
  if (isError) {
    return (
      <main className="min-h-screen flex flex-col items-center justify-center p-4 bg-gray-50">
        <div className="w-full max-w-md text-center">
          <div className="mx-auto w-12 h-12 rounded-full bg-red-100 flex items-center justify-center mb-4">
            <svg
              className="w-6 h-6 text-red-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
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
            Failed to load diagnostic
          </h1>
          <p className="text-gray-600 mb-6">
            {error instanceof Error ? error.message : 'An unexpected error occurred'}
          </p>
          <button
            type="button"
            onClick={() => refetch()}
            className="px-6 py-2 bg-primary-600 text-white rounded-card font-medium hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
          >
            Try Again
          </button>
        </div>
      </main>
    )
  }

  // No question to display
  if (!currentQuestion) {
    return (
      <main className="min-h-screen flex flex-col items-center justify-center p-4 bg-gray-50">
        <p className="text-gray-500">No questions available.</p>
      </main>
    )
  }

  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-4 bg-gray-50">
      {/* Skip link for keyboard navigation */}
      <a
        href="#question-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:bg-primary-600 focus:text-white focus:px-4 focus:py-2 focus:rounded-card focus:outline-none"
      >
        Skip to question
      </a>

      {/* Screen reader announcement for question changes */}
      <div aria-live="polite" aria-atomic="true" className="sr-only">
        Question {currentIndex + 1} of {questions.length}: {currentQuestion.question_text}
      </div>

      <div className="w-full max-w-2xl">
        {/* Header with timer */}
        <div className="flex justify-between items-start mb-6">
          <h1 className="text-sm font-medium text-gray-700 uppercase tracking-wide">
            Diagnostic Assessment
          </h1>
          <SessionTimer
            startTime={startTime}
            onTimeout={handleTimeout}
            onWarning={handleWarning}
          />
        </div>

        {/* Progress indicator */}
        <DiagnosticProgress
          currentIndex={currentIndex}
          total={questions.length}
          coveragePercentage={coveragePercentage}
        />

        {/* Question card */}
        <div
          id="question-content"
          className="bg-white rounded-card shadow-sm border border-gray-200 p-6 sm:p-8"
        >
          <DiagnosticQuestionCard
            question={currentQuestion}
            onSubmit={handleSubmitAnswer}
            isSubmitting={isSubmitting}
          />
        </div>

        {/* Submitting indicator */}
        {isSubmitting && (
          <div aria-live="polite" className="sr-only">
            Submitting answer...
          </div>
        )}
      </div>

      {/* Navigation blocker dialog */}
      {blocker.state === 'blocked' && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
          role="dialog"
          aria-modal="true"
          aria-labelledby="blocker-title"
        >
          <div className="bg-white rounded-card p-6 max-w-md mx-4 shadow-xl">
            <h2 id="blocker-title" className="text-lg font-semibold text-gray-900 mb-2">
              Leave diagnostic?
            </h2>
            <p className="text-gray-600 mb-6">
              Your diagnostic progress will be lost. Are you sure you want to leave?
            </p>
            <div className="flex gap-3 justify-end">
              <button
                type="button"
                onClick={() => blocker.reset?.()}
                className="px-4 py-2 text-gray-700 border border-gray-300 rounded-card font-medium hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
              >
                Stay
              </button>
              <button
                type="button"
                onClick={() => blocker.proceed?.()}
                className="px-4 py-2 bg-red-600 text-white rounded-card font-medium hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
              >
                Leave
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  )
}
