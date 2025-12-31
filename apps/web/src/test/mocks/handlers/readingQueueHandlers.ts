/**
 * MSW handlers for reading queue endpoint.
 * Story 5.7: Reading Library Page with Queue Display
 * Story 5.8: Reading Item Detail View and Engagement Tracking
 */
import { http, HttpResponse } from 'msw'

interface MockQueueItem {
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

let mockQueueItems: MockQueueItem[] = []
let mockQueueItemsExplicitlySet = false
let mockShouldFail = false
let mockDelay = 0

/**
 * Default queue items for testing.
 */
const defaultQueueItems: MockQueueItem[] = [
  {
    queue_id: 'queue-1',
    chunk_id: 'chunk-1',
    title: 'Introduction to Strategy Analysis',
    preview: 'This chunk covers the basics of strategy analysis in business...',
    babok_section: '3.1',
    ka_name: 'Strategy Analysis',
    ka_id: 'strategy',
    relevance_score: null,
    priority: 'High',
    status: 'unread',
    word_count: 500,
    estimated_read_minutes: 3,
    question_preview: 'What technique is best for stakeholder identification?',
    was_incorrect: true,
    added_at: '2025-01-15T10:00:00Z',
  },
  {
    queue_id: 'queue-2',
    chunk_id: 'chunk-2',
    title: 'Elicitation Techniques Overview',
    preview: 'This section describes various elicitation techniques...',
    babok_section: '4.2',
    ka_name: 'Elicitation and Collaboration',
    ka_id: 'elicitation',
    relevance_score: null,
    priority: 'High',
    status: 'unread',
    word_count: 600,
    estimated_read_minutes: 3,
    question_preview: null,
    was_incorrect: true,
    added_at: '2025-01-15T09:30:00Z',
  },
  {
    queue_id: 'queue-3',
    chunk_id: 'chunk-3',
    title: 'Requirements Traceability',
    preview: 'Traceability is essential for managing requirements...',
    babok_section: '5.1',
    ka_name: 'Requirements Life Cycle Management',
    ka_id: 'rlcm',
    relevance_score: null,
    priority: 'Medium',
    status: 'unread',
    word_count: 450,
    estimated_read_minutes: 2,
    question_preview: 'Which tool helps track requirements changes?',
    was_incorrect: true,
    added_at: '2025-01-14T15:00:00Z',
  },
]

/**
 * Mock detail item for testing.
 */
interface MockDetailItem {
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
  question_context: {
    question_id: string | null
    question_preview: string | null
    was_incorrect: boolean
  }
  added_at: string
}

let mockDetailItem: MockDetailItem = {
  queue_id: 'queue-1',
  chunk_id: 'chunk-1',
  title: 'Introduction to Strategy Analysis',
  text_content: 'This is the full content of the reading chunk. It covers the basics of strategy analysis in business analysis, including stakeholder identification, requirements gathering, and solution evaluation.',
  babok_section: '3.1',
  ka_name: 'Strategy Analysis',
  priority: 'High',
  status: 'unread',
  word_count: 500,
  estimated_read_minutes: 3,
  times_opened: 1,
  total_reading_time_seconds: 0,
  first_opened_at: null,
  question_context: {
    question_id: 'question-1',
    question_preview: 'What technique is best for stakeholder identification?',
    was_incorrect: true,
  },
  added_at: '2025-01-15T10:00:00Z',
}

/**
 * Default handlers for reading queue endpoints.
 */
export const readingQueueHandlers = [
  // GET /v1/reading/queue/{queue_id}
  http.get('*/reading/queue/:queueId', async ({ params }) => {
    if (mockShouldFail) {
      return HttpResponse.json(
        { error: { code: 'QUEUE_ITEM_NOT_FOUND', message: 'Queue item not found' } },
        { status: 404 }
      )
    }

    const { queueId } = params

    // Return mock detail with incremented times_opened
    mockDetailItem.times_opened += 1
    if (!mockDetailItem.first_opened_at) {
      mockDetailItem.first_opened_at = new Date().toISOString()
    }

    return HttpResponse.json({
      ...mockDetailItem,
      queue_id: queueId,
    })
  }),

  // PUT /v1/reading/queue/{queue_id}/engagement
  http.put('*/reading/queue/:queueId/engagement', async ({ request, params }) => {
    if (mockShouldFail) {
      return HttpResponse.json(
        { error: { code: 'QUEUE_ITEM_NOT_FOUND', message: 'Queue item not found' } },
        { status: 404 }
      )
    }

    const body = await request.json() as { time_spent_seconds: number }
    const timeSpent = Math.min(body.time_spent_seconds, 1800)
    mockDetailItem.total_reading_time_seconds += timeSpent

    return HttpResponse.json({
      queue_id: params.queueId,
      total_reading_time_seconds: mockDetailItem.total_reading_time_seconds,
      times_opened: mockDetailItem.times_opened,
    })
  }),

  // PUT /v1/reading/queue/{queue_id}/status
  http.put('*/reading/queue/:queueId/status', async ({ request, params }) => {
    if (mockShouldFail) {
      return HttpResponse.json(
        { error: { code: 'QUEUE_ITEM_NOT_FOUND', message: 'Queue item not found' } },
        { status: 404 }
      )
    }

    const body = await request.json() as { status: string }
    mockDetailItem.status = body.status

    return HttpResponse.json({
      queue_id: params.queueId,
      status: body.status,
      completed_at: body.status === 'completed' ? new Date().toISOString() : null,
      dismissed_at: body.status === 'dismissed' ? new Date().toISOString() : null,
    })
  }),

  // POST /v1/reading/queue/batch-dismiss
  http.post('*/reading/queue/batch-dismiss', async ({ request }) => {
    if (mockShouldFail) {
      return HttpResponse.json(
        { error: { code: 'SERVER_ERROR', message: 'Server error' } },
        { status: 500 }
      )
    }

    const body = await request.json() as { queue_ids: string[] }
    const dismissedCount = body.queue_ids.length

    return HttpResponse.json({
      dismissed_count: dismissedCount,
      remaining_unread_count: Math.max(0, 3 - dismissedCount),
    })
  }),

  // GET /v1/reading/queue (list)
  http.get('*/reading/queue', async ({ request }) => {
    if (mockDelay > 0) {
      await new Promise((resolve) => setTimeout(resolve, mockDelay))
    }

    if (mockShouldFail) {
      return HttpResponse.json(
        { error: 'Internal Server Error', message: 'Failed to fetch reading queue' },
        { status: 500 }
      )
    }

    const url = new URL(request.url)
    const status = url.searchParams.get('status') || 'unread'
    const kaId = url.searchParams.get('ka_id')
    const priority = url.searchParams.get('priority')
    const page = parseInt(url.searchParams.get('page') || '1', 10)
    const perPage = parseInt(url.searchParams.get('per_page') || '20', 10)

    // Filter items - use explicitly set items (even if empty) or defaults
    let filteredItems = mockQueueItemsExplicitlySet ? mockQueueItems : defaultQueueItems

    if (status !== 'all') {
      filteredItems = filteredItems.filter((item) => item.status === status)
    }

    if (kaId) {
      filteredItems = filteredItems.filter((item) => item.ka_id === kaId)
    }

    if (priority) {
      filteredItems = filteredItems.filter((item) => item.priority === priority)
    }

    // Paginate
    const totalItems = filteredItems.length
    const totalPages = Math.ceil(totalItems / perPage)
    const startIndex = (page - 1) * perPage
    const paginatedItems = filteredItems.slice(startIndex, startIndex + perPage)

    return HttpResponse.json({
      items: paginatedItems,
      pagination: {
        page,
        per_page: perPage,
        total_items: totalItems,
        total_pages: totalPages,
      },
    })
  }),
]

/**
 * Set custom mock queue items for testing.
 * Pass empty array to test empty state.
 */
export function setMockQueueItems(items: MockQueueItem[]) {
  mockQueueItems = items
  mockQueueItemsExplicitlySet = true
}

/**
 * Configure the endpoint to return an error.
 */
export function setMockQueueError(shouldFail: boolean) {
  mockShouldFail = shouldFail
}

/**
 * Set artificial delay for testing loading states.
 */
export function setMockQueueDelay(delayMs: number) {
  mockDelay = delayMs
}

/**
 * Reset all mock state to defaults.
 */
export function resetReadingQueueMocks() {
  mockQueueItems = []
  mockQueueItemsExplicitlySet = false
  mockShouldFail = false
  mockDelay = 0
  // Reset detail item
  mockDetailItem = {
    queue_id: 'queue-1',
    chunk_id: 'chunk-1',
    title: 'Introduction to Strategy Analysis',
    text_content: 'This is the full content of the reading chunk.',
    babok_section: '3.1',
    ka_name: 'Strategy Analysis',
    priority: 'High',
    status: 'unread',
    word_count: 500,
    estimated_read_minutes: 3,
    times_opened: 1,
    total_reading_time_seconds: 0,
    first_opened_at: null,
    question_context: {
      question_id: 'question-1',
      question_preview: 'What technique is best for stakeholder identification?',
      was_incorrect: true,
    },
    added_at: '2025-01-15T10:00:00Z',
  }
}
