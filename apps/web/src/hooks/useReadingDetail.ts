/**
 * useReadingDetail Hook
 * Story 5.8: Reading Item Detail View and Engagement Tracking
 *
 * React Query hook for fetching reading item details and managing status updates.
 * Provides markComplete and dismiss mutations with optimistic updates.
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useCallback } from 'react'
import {
  getQueueItemDetail,
  updateStatus,
  type ReadingQueueDetail,
} from '../services/readingService'

export interface UseReadingDetailResult {
  item: ReadingQueueDetail | null
  isLoading: boolean
  isError: boolean
  error: Error | null
  markComplete: () => Promise<void>
  dismiss: () => Promise<void>
  isMarkingComplete: boolean
  isDismissing: boolean
  refetch: () => void
}

/**
 * Hook for fetching and managing reading item details.
 *
 * @param queueId - Queue item ID to fetch
 * @returns Query result with item data, loading/error states, and action handlers
 *
 * @example
 * ```tsx
 * const {
 *   item,
 *   isLoading,
 *   isError,
 *   markComplete,
 *   dismiss,
 *   refetch
 * } = useReadingDetail(queueId)
 * ```
 */
export function useReadingDetail(queueId: string): UseReadingDetailResult {
  const queryClient = useQueryClient()

  // Fetch item detail
  const {
    data: item,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ['readingDetail', queueId],
    queryFn: () => getQueueItemDetail(queueId),
    staleTime: 60000, // 1 minute
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 10000),
    enabled: !!queueId,
  })

  // Mark complete mutation
  const markCompleteMutation = useMutation({
    mutationFn: () => updateStatus(queueId, 'completed'),
    onSuccess: () => {
      // Invalidate related queries to update badge
      queryClient.invalidateQueries({ queryKey: ['readingStats'] })
      queryClient.invalidateQueries({ queryKey: ['readingQueue'] })
      queryClient.invalidateQueries({ queryKey: ['readingDetail', queueId] })
    },
  })

  // Dismiss mutation
  const dismissMutation = useMutation({
    mutationFn: () => updateStatus(queueId, 'dismissed'),
    onSuccess: () => {
      // Invalidate related queries to update badge
      queryClient.invalidateQueries({ queryKey: ['readingStats'] })
      queryClient.invalidateQueries({ queryKey: ['readingQueue'] })
      queryClient.invalidateQueries({ queryKey: ['readingDetail', queueId] })
    },
  })

  const markComplete = useCallback(async () => {
    await markCompleteMutation.mutateAsync()
  }, [markCompleteMutation])

  const dismiss = useCallback(async () => {
    await dismissMutation.mutateAsync()
  }, [dismissMutation])

  return {
    item: item ?? null,
    isLoading,
    isError,
    error: error as Error | null,
    markComplete,
    dismiss,
    isMarkingComplete: markCompleteMutation.isPending,
    isDismissing: dismissMutation.isPending,
    refetch,
  }
}
