/**
 * MSW handlers for reading stats endpoint.
 * Story 5.6: Silent Badge Updates in Navigation
 */
import { http, HttpResponse } from 'msw'

let mockUnreadCount = 0
let mockHighPriorityCount = 0
let mockShouldFail = false
let mockFailCount = 0

/**
 * Default handlers for reading stats endpoints.
 */
export const readingStatsHandlers = [
  // GET /v1/reading/stats
  http.get('*/reading/stats', () => {
    if (mockShouldFail) {
      mockFailCount++
      return new HttpResponse(null, { status: 500 })
    }

    return HttpResponse.json({
      unread_count: mockUnreadCount,
      high_priority_count: mockHighPriorityCount,
    })
  }),
]

/**
 * Set the mock unread counts for testing.
 */
export function setMockReadingStats(unreadCount: number, highPriorityCount: number) {
  mockUnreadCount = unreadCount
  mockHighPriorityCount = highPriorityCount
}

/**
 * Configure the endpoint to return an error.
 */
export function setMockReadingStatsError(shouldFail: boolean) {
  mockShouldFail = shouldFail
}

/**
 * Get the number of times the endpoint has failed.
 */
export function getMockFailCount(): number {
  return mockFailCount
}

/**
 * Reset all mock state to defaults.
 */
export function resetReadingStatsMocks() {
  mockUnreadCount = 0
  mockHighPriorityCount = 0
  mockShouldFail = false
  mockFailCount = 0
}
