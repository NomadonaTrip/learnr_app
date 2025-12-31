/**
 * Reading Service
 * Story 5.6: Silent Badge Updates in Navigation
 * Story 5.7: Reading Library Page with Queue Display
 * Story 5.8: Reading Item Detail View and Engagement Tracking
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
 * Reading queue item from API
 */
export interface ReadingQueueItem {
  queue_id: string
  chunk_id: string
  title: string
  preview: string
  babok_section: string
  ka_name: string
  ka_id: string
  relevance_score: number | null
  priority: 'High' | 'Medium' | 'Low'
  status: string
  word_count: number
  estimated_read_minutes: number
  question_preview: string | null
  was_incorrect: boolean
  added_at: string
}

/**
 * Pagination metadata
 */
export interface PaginationMeta {
  page: number
  per_page: number
  total_items: number
  total_pages: number
}

/**
 * Response type for reading queue list
 */
export interface ReadingQueueListResponse {
  items: ReadingQueueItem[]
  pagination: PaginationMeta
}

/**
 * Filter parameters for reading queue
 */
export interface ReadingQueueFilters {
  status?: 'unread' | 'reading' | 'completed' | 'dismissed' | 'all'
  ka_id?: string | null
  priority?: 'High' | 'Medium' | 'Low' | null
  sort_by?: 'priority' | 'date' | 'relevance'
  page?: number
  per_page?: number
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

/**
 * Fetch paginated reading queue items for the current user's enrollment.
 * Story 5.7: Reading Library Page with Queue Display
 *
 * @param filters - Optional filter parameters (status, ka_id, priority, sort_by, page, per_page)
 * @returns Promise resolving to paginated list of queue items
 * @throws AxiosError on network or server errors (handled by interceptors)
 */
export async function getQueueItems(
  filters: ReadingQueueFilters = {}
): Promise<ReadingQueueListResponse> {
  // Build query params, excluding null/undefined values
  const params = new URLSearchParams()

  if (filters.status) {
    params.append('status', filters.status)
  }
  if (filters.ka_id) {
    params.append('ka_id', filters.ka_id)
  }
  if (filters.priority) {
    params.append('priority', filters.priority)
  }
  if (filters.sort_by) {
    params.append('sort_by', filters.sort_by)
  }
  if (filters.page !== undefined) {
    params.append('page', String(filters.page))
  }
  if (filters.per_page !== undefined) {
    params.append('per_page', String(filters.per_page))
  }

  const queryString = params.toString()
  const url = queryString ? `/reading/queue?${queryString}` : '/reading/queue'

  const response = await api.get<ReadingQueueListResponse>(url)
  return response.data
}

/**
 * Question context for reading detail
 * Story 5.8: Reading Item Detail View and Engagement Tracking
 */
export interface QuestionContext {
  question_id: string | null
  question_preview: string | null
  was_incorrect: boolean
}

/**
 * Reading queue item detail with full content
 * Story 5.8: Reading Item Detail View and Engagement Tracking
 */
export interface ReadingQueueDetail {
  queue_id: string
  chunk_id: string
  title: string
  text_content: string
  babok_section: string
  ka_name: string
  priority: 'High' | 'Medium' | 'Low'
  status: string
  word_count: number
  estimated_read_minutes: number
  times_opened: number
  total_reading_time_seconds: number
  first_opened_at: string | null
  question_context: QuestionContext
  added_at: string
}

/**
 * Fetch a single reading queue item with full content.
 * Story 5.8: Reading Detail Page
 *
 * @param queueId - Queue item ID
 * @returns Promise resolving to full queue item details
 * @throws AxiosError on network or server errors (handled by interceptors)
 */
export async function getQueueItemDetail(
  queueId: string
): Promise<ReadingQueueDetail> {
  const response = await api.get<ReadingQueueDetail>(`/reading/queue/${queueId}`)
  return response.data
}

/**
 * Response for status update
 */
export interface StatusUpdateResponse {
  success: boolean
  queue_id: string
  status: string
}

/**
 * Update the status of a reading queue item (legacy PATCH).
 * Story 5.8: Reading Detail Page
 *
 * @param queueId - Queue item ID
 * @param status - New status: 'reading', 'completed', or 'dismissed'
 * @returns Promise resolving to update confirmation
 * @throws AxiosError on network or server errors (handled by interceptors)
 * @deprecated Use updateStatus instead
 */
export async function updateQueueItemStatus(
  queueId: string,
  status: 'reading' | 'completed' | 'dismissed'
): Promise<StatusUpdateResponse> {
  const response = await api.patch<StatusUpdateResponse>(
    `/reading/queue/${queueId}`,
    { status }
  )
  return response.data
}

/**
 * Engagement update response
 * Story 5.8: Reading Item Detail View and Engagement Tracking
 */
export interface EngagementUpdateResponse {
  queue_id: string
  total_reading_time_seconds: number
  times_opened: number
}

/**
 * Update reading engagement metrics.
 * Story 5.8: Reading Item Detail View and Engagement Tracking
 *
 * @param queueId - Queue item ID
 * @param timeSpentSeconds - Time spent reading in seconds
 * @returns Promise resolving to updated engagement metrics
 * @throws AxiosError on network or server errors
 */
export async function updateEngagement(
  queueId: string,
  timeSpentSeconds: number
): Promise<EngagementUpdateResponse> {
  const response = await api.put<EngagementUpdateResponse>(
    `/reading/queue/${queueId}/engagement`,
    { time_spent_seconds: timeSpentSeconds }
  )
  return response.data
}

/**
 * Status update response with timestamps
 * Story 5.8: Reading Item Detail View and Engagement Tracking
 */
export interface StatusUpdateResponseNew {
  queue_id: string
  status: string
  completed_at: string | null
  dismissed_at: string | null
}

/**
 * Update queue item status using PUT endpoint.
 * Story 5.8: Reading Item Detail View and Engagement Tracking
 *
 * @param queueId - Queue item ID
 * @param status - New status: 'completed' or 'dismissed'
 * @returns Promise resolving to status update with timestamps
 * @throws AxiosError on network or server errors
 */
export async function updateStatus(
  queueId: string,
  status: 'completed' | 'dismissed'
): Promise<StatusUpdateResponseNew> {
  const response = await api.put<StatusUpdateResponseNew>(
    `/reading/queue/${queueId}/status`,
    { status }
  )
  return response.data
}

/**
 * Batch dismiss response
 * Story 5.8: Reading Item Detail View and Engagement Tracking
 */
export interface BatchDismissResponse {
  dismissed_count: number
  remaining_unread_count: number
}

/**
 * Batch dismiss multiple reading queue items.
 * Story 5.8: Reading Item Detail View and Engagement Tracking
 *
 * @param queueIds - Array of queue item IDs to dismiss (max 100)
 * @returns Promise resolving to dismissed count and remaining unread
 * @throws AxiosError on network or server errors
 */
export async function batchDismiss(
  queueIds: string[]
): Promise<BatchDismissResponse> {
  const response = await api.post<BatchDismissResponse>(
    '/reading/queue/batch-dismiss',
    { queue_ids: queueIds }
  )
  return response.data
}
