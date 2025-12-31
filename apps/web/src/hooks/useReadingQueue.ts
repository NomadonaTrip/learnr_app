/**
 * useReadingQueue Hook
 * Story 5.7: Reading Library Page with Queue Display
 * Story 5.12: Clear Completed Reading Materials
 *
 * React Query hook for fetching and managing reading queue data.
 * Supports filtering, sorting, pagination, and clear operations.
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getQueueItems,
  batchDismiss,
  updateStatus,
  type ReadingQueueFilters,
  type ReadingQueueItem,
  type PaginationMeta,
} from '../services/readingService'

export interface UseReadingQueueParams {
  status?: 'unread' | 'reading' | 'completed' | 'dismissed' | 'all'
  kaId?: string | null
  priority?: 'High' | 'Medium' | 'Low' | null
  sortBy?: 'priority' | 'date' | 'relevance'
  page?: number
  perPage?: number
  enabled?: boolean
}

export interface UseReadingQueueResult {
  items: ReadingQueueItem[]
  pagination: PaginationMeta | null
  isLoading: boolean
  isError: boolean
  error: Error | null
  refetch: () => void
}

/**
 * Hook for fetching reading queue items with React Query.
 *
 * @param params - Filter and pagination parameters
 * @returns Query result with items, pagination, loading/error states, and refetch function
 *
 * @example
 * ```tsx
 * const { items, pagination, isLoading, isError, refetch } = useReadingQueue({
 *   status: 'unread',
 *   sortBy: 'priority',
 *   page: 1,
 * })
 * ```
 */
export function useReadingQueue(params: UseReadingQueueParams = {}): UseReadingQueueResult {
  const { status, kaId, priority, sortBy, page, perPage, enabled = true } = params

  // Build filters object for service
  const filters: ReadingQueueFilters = {
    status: status ?? 'unread',
    ka_id: kaId ?? undefined,
    priority: priority ?? undefined,
    sort_by: sortBy ?? 'priority',
    page: page ?? 1,
    per_page: perPage ?? 20,
  }

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['readingQueue', filters],
    queryFn: () => getQueueItems(filters),
    staleTime: 30000, // 30 seconds
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 10000),
    enabled,
  })

  return {
    items: data?.items ?? [],
    pagination: data?.pagination ?? null,
    isLoading,
    isError,
    error: error as Error | null,
    refetch,
  }
}

/**
 * Hook for batch clearing completed reading queue items.
 * Story 5.12: Clear Completed Reading Materials
 *
 * @returns Mutation for batch clearing completed items
 */
export function useClearCompletedMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (queueIds: string[]) => batchDismiss(queueIds),
    onSuccess: () => {
      // Invalidate all reading queue queries to refresh data
      queryClient.invalidateQueries({ queryKey: ['readingQueue'] })
      queryClient.invalidateQueries({ queryKey: ['readingStats'] })
    },
  })
}

/**
 * Hook for removing a single reading queue item with optimistic update.
 * Story 5.12: Clear Completed Reading Materials
 *
 * @param filters - Current filter state for optimistic update
 * @returns Mutation for removing item with rollback capability
 */
export function useRemoveItemMutation(filters?: ReadingQueueFilters) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (queueId: string) => updateStatus(queueId, 'dismissed'),
    onMutate: async (queueId: string) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['readingQueue'] })

      // Snapshot the previous value
      const previousData = queryClient.getQueryData(['readingQueue', filters])

      // Optimistically remove from cache
      queryClient.setQueryData(
        ['readingQueue', filters],
        (old: { items: ReadingQueueItem[]; pagination: PaginationMeta } | undefined) => {
          if (!old) return old
          return {
            ...old,
            items: old.items.filter((item) => item.queue_id !== queueId),
          }
        }
      )

      // Return context with snapshot for rollback
      return { previousData, removedQueueId: queueId }
    },
    onError: (_err, _queueId, context) => {
      // Rollback on error
      if (context?.previousData) {
        queryClient.setQueryData(['readingQueue', filters], context.previousData)
      }
    },
    onSettled: () => {
      // Always refetch after error or success
      queryClient.invalidateQueries({ queryKey: ['readingQueue'] })
      queryClient.invalidateQueries({ queryKey: ['readingStats'] })
    },
  })
}

/**
 * Hook for restoring a dismissed item back to completed status (undo).
 * Story 5.12: Clear Completed Reading Materials
 *
 * @returns Mutation for restoring item to completed status
 */
export function useRestoreItemMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (queueId: string) => updateStatus(queueId, 'completed'),
    onSuccess: () => {
      // Invalidate queries to refresh data
      queryClient.invalidateQueries({ queryKey: ['readingQueue'] })
      queryClient.invalidateQueries({ queryKey: ['readingStats'] })
    },
  })
}
