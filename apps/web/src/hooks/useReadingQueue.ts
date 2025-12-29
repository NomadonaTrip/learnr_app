/**
 * useReadingQueue Hook
 * Story 5.7: Reading Library Page with Queue Display
 *
 * React Query hook for fetching and managing reading queue data.
 * Supports filtering, sorting, and pagination.
 */
import { useQuery } from '@tanstack/react-query'
import {
  getQueueItems,
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
