/**
 * useReadingStats Hook
 * Story 5.6: Silent Badge Updates in Navigation
 *
 * Provides reading queue statistics with automatic polling.
 * Implements error handling with exponential backoff.
 */
import { useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getReadingStats, ReadingStatsResponse } from '../services/readingService'
import { useReadingStore } from '../stores/readingStore'
import { useAuthStore } from '../stores/authStore'

/** Default polling interval in milliseconds */
const DEFAULT_POLL_INTERVAL = 10000 // 10 seconds

/** Maximum polling interval during error backoff */
const MAX_BACKOFF_INTERVAL = 60000 // 60 seconds

interface UseReadingStatsOptions {
  /** Whether polling should be active (e.g., during quiz session) */
  enabled?: boolean
  /** Custom polling interval in milliseconds */
  pollInterval?: number
}

interface UseReadingStatsResult {
  /** Count of unread items */
  unreadCount: number
  /** Count of high-priority unread items */
  highPriorityCount: number
  /** Whether the initial fetch is in progress */
  isLoading: boolean
  /** Whether there was an error (stale data still shown) */
  isError: boolean
  /** Manually trigger a refetch */
  refetch: () => void
}

/**
 * Hook for fetching and polling reading queue statistics.
 *
 * Features:
 * - Automatic polling with configurable interval (default: 10 seconds)
 * - Exponential backoff on errors (10s -> 20s -> 40s -> 60s max)
 * - Stale data preservation on error (never hides badge)
 * - Syncs with Zustand store for global access
 * - Only polls when user is authenticated and enabled
 *
 * @param options - Configuration options
 * @returns Reading stats with loading/error states
 */
export function useReadingStats(
  options: UseReadingStatsOptions = {}
): UseReadingStatsResult {
  const { enabled = true, pollInterval = DEFAULT_POLL_INTERVAL } = options
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const { unreadCount, highPriorityCount, setStats, isInitialized } =
    useReadingStore()

  const shouldFetch = enabled && isAuthenticated

  const {
    data,
    isLoading,
    isError,
    refetch,
  } = useQuery<ReadingStatsResponse>({
    queryKey: ['readingStats'],
    queryFn: getReadingStats,
    enabled: shouldFetch,
    // Polling configuration with exponential backoff on error
    refetchInterval: (query) => {
      if (!shouldFetch) return false

      // Exponential backoff on error: 10s -> 20s -> 40s -> 60s (max)
      if (query.state.error) {
        const failureCount = query.state.errorUpdateCount
        return Math.min(pollInterval * Math.pow(2, failureCount), MAX_BACKOFF_INTERVAL)
      }

      // Normal polling interval
      return pollInterval
    },
    // Consider data stale after 5 seconds
    staleTime: 5000,
    // Retry twice before showing error state
    retry: 2,
    // Exponential retry delay
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 10000),
    // Keep previous data on error (stale is better than missing)
    placeholderData: (previousData) => previousData,
    // Don't refetch on window focus during polling (avoid duplicate requests)
    refetchOnWindowFocus: false,
  })

  // Sync successful fetches to Zustand store
  useEffect(() => {
    if (data) {
      setStats(data.unread_count, data.high_priority_count)
    }
  }, [data, setStats])

  return {
    // Use store values (which may be stale but preserved on error)
    unreadCount: data?.unread_count ?? unreadCount,
    highPriorityCount: data?.high_priority_count ?? highPriorityCount,
    isLoading: isLoading && !isInitialized,
    isError,
    refetch,
  }
}

export default useReadingStats
