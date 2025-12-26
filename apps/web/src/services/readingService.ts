/**
 * Reading Service
 * Story 5.6: Silent Badge Updates in Navigation
 *
 * Service layer for reading-related API calls.
 * Uses the configured Axios instance with interceptors.
 */
import api from './api'

/**
 * Response type for reading queue statistics
 */
export interface ReadingStatsResponse {
  unread_count: number
  high_priority_count: number
}

/**
 * Fetch reading queue statistics for the current user's enrollment.
 *
 * @returns Promise resolving to reading stats with unread and high-priority counts
 * @throws AxiosError on network or server errors (handled by interceptors)
 */
export async function getReadingStats(): Promise<ReadingStatsResponse> {
  const response = await api.get<ReadingStatsResponse>('/reading/stats')
  return response.data
}
