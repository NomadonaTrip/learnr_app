/**
 * ReadingLibraryPage Component
 * Story 5.7: Reading Library Page with Queue Display
 * Story 5.8: Reading Item Detail View and Engagement Tracking
 *
 * Main page component for browsing reading queue items.
 * Displays filterable, sortable, paginated list of reading cards.
 * Includes batch dismiss functionality for low-priority items.
 */
import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useReadingQueue } from '../hooks/useReadingQueue'
import { ReadingCard } from '../components/reading/ReadingCard'
import {
  ReadingFilterBar,
  type FilterStatus,
  type SortOption,
  type KnowledgeArea,
} from '../components/reading/ReadingFilterBar'
import type { PriorityLevel } from '../components/common/PriorityBadge'
import { Navigation } from '../components/layout/Navigation'
import { Toast, type ToastVariant } from '../components/common/Toast'
import { batchDismiss } from '../services/readingService'

// Knowledge areas from CBAP course
const KNOWLEDGE_AREAS: KnowledgeArea[] = [
  { id: 'planning', name: 'Business Analysis Planning and Monitoring' },
  { id: 'elicitation', name: 'Elicitation and Collaboration' },
  { id: 'rlcm', name: 'Requirements Life Cycle Management' },
  { id: 'strategy', name: 'Strategy Analysis' },
  { id: 'radd', name: 'Requirements Analysis and Design Definition' },
  { id: 'solution', name: 'Solution Evaluation' },
]

/**
 * Skeleton card for loading state
 */
function SkeletonCard() {
  return (
    <div className="bg-white rounded-[14px] shadow-sm p-6 animate-pulse">
      <div className="flex items-start gap-4">
        <div className="w-16 h-6 bg-gray-200 rounded" />
        <div className="flex-1">
          <div className="h-5 bg-gray-200 rounded w-3/4 mb-2" />
          <div className="h-4 bg-gray-200 rounded w-full mb-1" />
          <div className="h-4 bg-gray-200 rounded w-2/3 mb-4" />
          <div className="flex gap-2">
            <div className="h-6 w-20 bg-gray-200 rounded" />
            <div className="h-6 w-16 bg-gray-200 rounded" />
          </div>
        </div>
      </div>
    </div>
  )
}

/**
 * Pagination controls component
 */
interface PaginationProps {
  currentPage: number
  totalPages: number
  onPageChange: (page: number) => void
}

function Pagination({ currentPage, totalPages, onPageChange }: PaginationProps) {
  if (totalPages <= 1) return null

  return (
    <div className="flex justify-center items-center gap-2 mt-6">
      <button
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
        className="px-3 py-2 rounded-lg bg-white border border-gray-200 disabled:opacity-50
                   hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        Previous
      </button>
      <span className="text-sm text-gray-600">
        Page {currentPage} of {totalPages}
      </span>
      <button
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
        className="px-3 py-2 rounded-lg bg-white border border-gray-200 disabled:opacity-50
                   hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        Next
      </button>
    </div>
  )
}

interface ToastState {
  message: string
  variant: ToastVariant
}

export function ReadingLibraryPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  // Filter state
  const [status, setStatus] = useState<FilterStatus>('unread')
  const [sortBy, setSortBy] = useState<SortOption>('priority')
  const [kaId, setKaId] = useState<string | null>(null)
  const [page, setPage] = useState(1)
  const [toast, setToast] = useState<ToastState | null>(null)

  // Fetch queue items
  const { items, pagination, isLoading, isError, refetch } = useReadingQueue({
    status,
    kaId,
    sortBy,
    page,
  })

  // Batch dismiss mutation
  const batchDismissMutation = useMutation({
    mutationFn: (queueIds: string[]) => batchDismiss(queueIds),
    onSuccess: (data) => {
      // Invalidate queries to refresh data
      queryClient.invalidateQueries({ queryKey: ['readingQueue'] })
      queryClient.invalidateQueries({ queryKey: ['readingStats'] })
      setToast({
        message: `Dismissed ${data.dismissed_count} items. ${data.remaining_unread_count} unread remaining.`,
        variant: 'success',
      })
    },
    onError: () => {
      setToast({
        message: 'Failed to dismiss items. Please try again.',
        variant: 'error',
      })
    },
  })

  // Get low priority item IDs for batch dismiss
  const lowPriorityIds = items
    .filter((item) => item.priority === 'Low' && item.status === 'unread')
    .map((item) => item.queue_id)

  const handleBatchDismissLowPriority = useCallback(() => {
    if (lowPriorityIds.length > 0) {
      batchDismissMutation.mutate(lowPriorityIds)
    }
  }, [lowPriorityIds, batchDismissMutation])

  // Handle filter changes
  const handleFilterChange = useCallback(
    (filters: { status?: FilterStatus; sort?: SortOption; kaId?: string | null }) => {
      if (filters.status !== undefined) {
        setStatus(filters.status)
        setPage(1) // Reset to first page on filter change
      }
      if (filters.sort !== undefined) {
        setSortBy(filters.sort)
        setPage(1)
      }
      if (filters.kaId !== undefined) {
        setKaId(filters.kaId)
        setPage(1)
      }
    },
    []
  )

  // Handle "Read Now" button click
  const handleReadNow = useCallback(
    (queueId: string) => {
      // Navigate to detail view (Story 5.8)
      navigate(`/reading-library/${queueId}`)
    },
    [navigate]
  )

  // Handle page change
  const handlePageChange = useCallback((newPage: number) => {
    setPage(newPage)
  }, [])

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation - disable polling on library page since we're already viewing it */}
      <Navigation enablePolling={false} />
      {/* Main container with Framer-inspired styling */}
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-[35px] shadow-sm p-6 sm:p-8">
          {/* Header */}
          <header className="mb-8">
            <div className="flex justify-between items-start">
              <div>
                <h1 className="text-2xl font-bold text-gray-900 font-sans">Reading Library</h1>
                <p className="text-gray-600 mt-1">
                  Study materials recommended based on your quiz performance
                </p>
              </div>
              {/* Batch dismiss button */}
              {lowPriorityIds.length > 0 && status === 'unread' && (
                <button
                  onClick={handleBatchDismissLowPriority}
                  disabled={batchDismissMutation.isPending}
                  className={`px-4 py-2 text-sm rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-400 ${
                    batchDismissMutation.isPending
                      ? 'bg-gray-200 text-gray-400 cursor-wait'
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  {batchDismissMutation.isPending
                    ? 'Dismissing...'
                    : `Dismiss All Low Priority (${lowPriorityIds.length})`}
                </button>
              )}
            </div>
          </header>

          {/* Filter Bar */}
          <ReadingFilterBar
            selectedStatus={status}
            selectedSort={sortBy}
            selectedKaId={kaId}
            knowledgeAreas={KNOWLEDGE_AREAS}
            onFilterChange={handleFilterChange}
          />

          {/* Content Area */}
          {isLoading ? (
            // Loading state - 4 skeleton cards
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {[1, 2, 3, 4].map((i) => (
                <SkeletonCard key={i} />
              ))}
            </div>
          ) : isError ? (
            // Error state
            <div className="bg-red-50 rounded-[14px] p-6 text-center">
              <p className="text-red-600 mb-4">Unable to load your reading queue.</p>
              <button
                onClick={() => refetch()}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700
                           focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                Try Again
              </button>
            </div>
          ) : items.length === 0 ? (
            // Empty state
            <div className="text-center py-12">
              <div className="text-gray-400 mb-4">
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
                    d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
                  />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Your reading library is empty
              </h3>
              <p className="text-gray-600">
                Complete quiz sessions to get personalized recommendations!
              </p>
            </div>
          ) : (
            // Cards grid
            <>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {items.map((item) => (
                  <ReadingCard
                    key={item.queue_id}
                    queueId={item.queue_id}
                    title={item.title}
                    preview={item.preview}
                    babokSection={item.babok_section}
                    kaName={item.ka_name}
                    priority={item.priority as PriorityLevel}
                    estimatedReadMinutes={item.estimated_read_minutes}
                    questionPreview={item.question_preview ?? undefined}
                    wasIncorrect={item.was_incorrect}
                    addedAt={item.added_at}
                    onReadNow={handleReadNow}
                  />
                ))}
              </div>

              {/* Pagination */}
              {pagination && (
                <Pagination
                  currentPage={pagination.page}
                  totalPages={pagination.total_pages}
                  onPageChange={handlePageChange}
                />
              )}
            </>
          )}
        </div>
      </div>

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
