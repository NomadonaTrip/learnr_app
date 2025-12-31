/**
 * ReadingDetailPage Component
 * Story 5.8: Reading Item Detail View and Engagement Tracking
 *
 * Displays full reading content for a queue item.
 * Tracks reading time and provides mark complete/dismiss actions.
 */
import { useState, useCallback } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import { Navigation } from '../components/layout/Navigation'
import { PriorityBadge } from '../components/common/PriorityBadge'
import { ContextCard } from '../components/reading/ContextCard'
import { Toast, type ToastVariant } from '../components/common/Toast'
import { useReadingDetail } from '../hooks/useReadingDetail'
import { useReadingTimeTracker } from '../hooks/useReadingTimeTracker'

interface ToastState {
  message: string
  variant: ToastVariant
}

export function ReadingDetailPage() {
  const { queueId } = useParams<{ queueId: string }>()
  const navigate = useNavigate()
  const [toast, setToast] = useState<ToastState | null>(null)

  // Fetch item details with React Query
  const {
    item,
    isLoading,
    isError,
    error,
    markComplete,
    dismiss,
    isMarkingComplete,
    isDismissing,
  } = useReadingDetail(queueId || '')

  // Track reading time
  useReadingTimeTracker({
    queueId: queueId || '',
    enabled: !!queueId && !!item,
  })

  const showToast = useCallback((message: string, variant: ToastVariant) => {
    setToast({ message, variant })
  }, [])

  const handleMarkComplete = useCallback(async () => {
    try {
      await markComplete()
      showToast('Marked as complete!', 'success')
      setTimeout(() => navigate('/reading-library'), 1500)
    } catch {
      showToast('Failed to mark as complete. Please try again.', 'error')
    }
  }, [markComplete, showToast, navigate])

  const handleDismiss = useCallback(async () => {
    try {
      await dismiss()
      showToast('Item dismissed.', 'info')
      setTimeout(() => navigate('/reading-library'), 1500)
    } catch {
      showToast('Failed to dismiss. Please try again.', 'error')
    }
  }, [dismiss, showToast, navigate])

  if (!queueId) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navigation enablePolling={false} />
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="bg-white rounded-[35px] shadow-sm p-6 sm:p-8">
            <div className="text-center py-12">
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Invalid reading item ID
              </h3>
              <Link
                to="/reading-library"
                className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Back to Library
              </Link>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navigation enablePolling={false} />
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="bg-white rounded-[35px] shadow-sm p-6 sm:p-8 animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-3/4 mb-4" />
            <div className="h-4 bg-gray-200 rounded w-1/4 mb-8" />
            <div className="space-y-3">
              <div className="h-4 bg-gray-200 rounded w-full" />
              <div className="h-4 bg-gray-200 rounded w-full" />
              <div className="h-4 bg-gray-200 rounded w-5/6" />
              <div className="h-4 bg-gray-200 rounded w-full" />
              <div className="h-4 bg-gray-200 rounded w-4/5" />
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (isError || !item) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navigation enablePolling={false} />
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="bg-white rounded-[35px] shadow-sm p-6 sm:p-8">
            <div className="text-center py-12">
              <div className="text-red-500 mb-4">
                <svg
                  className="mx-auto h-12 w-12"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.5}
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                  />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                {error?.message || 'Reading content not found'}
              </h3>
              <Link
                to="/reading-library"
                className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Back to Library
              </Link>
            </div>
          </div>
        </div>
      </div>
    )
  }

  const isCompleted = item.status === 'completed'
  const isDismissed = item.status === 'dismissed'
  const isActionDisabled = isCompleted || isDismissed || isMarkingComplete || isDismissing

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation enablePolling={false} />
      <main role="main" className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-[35px] shadow-sm p-6 sm:p-8">
          {/* Back link */}
          <Link
            to="/reading-library"
            className="inline-flex items-center text-blue-600 hover:text-blue-700 mb-6"
          >
            <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Library
          </Link>

          {/* Header */}
          <header className="mb-8">
            <div className="flex items-start gap-4 mb-4">
              <PriorityBadge priority={item.priority} />
              <div className="flex-1">
                <h1 className="text-2xl font-bold text-gray-900">{item.title}</h1>
                <div className="flex flex-wrap items-center gap-3 mt-2 text-sm text-gray-600">
                  <span className="flex items-center gap-1">
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
                      />
                    </svg>
                    {item.babok_section}
                  </span>
                  <span className="text-gray-300">|</span>
                  <span>{item.ka_name}</span>
                  <span className="text-gray-300">|</span>
                  <span>{item.estimated_read_minutes} min read</span>
                  <span className="text-gray-300">|</span>
                  <span>{item.word_count} words</span>
                </div>
              </div>
            </div>

            {/* Question context card */}
            <ContextCard
              questionPreview={item.question_context.question_preview}
              wasIncorrect={item.question_context.was_incorrect}
              className="mt-4"
            />
          </header>

          {/* Content */}
          <article className="prose prose-gray max-w-none">
            <ReactMarkdown>{item.text_content}</ReactMarkdown>
          </article>

          {/* Status badge if already completed/dismissed */}
          {(isCompleted || isDismissed) && (
            <div className="mt-6 p-4 rounded-lg bg-gray-100">
              <span className={`text-sm font-medium ${isCompleted ? 'text-green-700' : 'text-gray-600'}`}>
                {isCompleted ? 'You have already completed this reading.' : 'This item has been dismissed.'}
              </span>
            </div>
          )}

          {/* Footer */}
          <footer className="mt-8 pt-6 border-t border-gray-200">
            <div className="flex justify-between items-center">
              <button
                onClick={() => navigate('/reading-library')}
                className="px-4 py-2 text-gray-600 hover:text-gray-800"
              >
                Back to Library
              </button>
              <div className="flex gap-3">
                {/* Dismiss button */}
                <button
                  onClick={handleDismiss}
                  disabled={isActionDisabled}
                  className={`px-4 py-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-400 ${
                    isActionDisabled
                      ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  {isDismissing ? 'Dismissing...' : 'Dismiss'}
                </button>
                {/* Mark Complete button */}
                <button
                  onClick={handleMarkComplete}
                  disabled={isActionDisabled}
                  className={`px-6 py-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 ${
                    isCompleted
                      ? 'bg-gray-400 text-white cursor-not-allowed'
                      : isActionDisabled
                      ? 'bg-green-400 text-white cursor-wait'
                      : 'bg-green-600 text-white hover:bg-green-700'
                  }`}
                >
                  {isCompleted
                    ? 'Completed'
                    : isMarkingComplete
                    ? 'Marking...'
                    : 'Mark as Complete'}
                </button>
              </div>
            </div>
          </footer>
        </div>
      </main>

      {/* Toast notification */}
      {toast && (
        <Toast
          message={toast.message}
          variant={toast.variant}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  )
}
