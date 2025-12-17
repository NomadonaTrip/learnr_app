import { http, HttpResponse } from 'msw'
import {
  mockDiagnosticQuestionsResponse,
  createMockAnswerResponse,
  createMockResumedQuestionsResponse,
  mockDiagnosticResetResponse,
} from '../../fixtures/diagnosticFixtures'

let answerCount = 0
let isSessionResumed = false
let sessionCurrentIndex = 0

export const diagnosticHandlers = [
  // Match both relative and absolute URLs
  http.get('*/diagnostic/questions', () => {
    // Support resumed sessions for testing (Story 3.9)
    if (isSessionResumed) {
      return HttpResponse.json(createMockResumedQuestionsResponse(sessionCurrentIndex))
    }
    return HttpResponse.json(mockDiagnosticQuestionsResponse)
  }),

  // Updated to return session_status (Story 3.9)
  http.post('*/diagnostic/answer', async () => {
    answerCount++
    const total = 3
    // Mark as completed when all answers submitted
    const sessionStatus = answerCount >= total ? 'completed' : 'in_progress'
    return HttpResponse.json(createMockAnswerResponse(answerCount, total, sessionStatus))
  }),

  // Reset diagnostic endpoint (Story 3.9)
  http.post('*/diagnostic/reset', async ({ request }) => {
    const body = (await request.json()) as { confirmation?: string }
    if (body.confirmation !== 'RESET DIAGNOSTIC') {
      return HttpResponse.json(
        { error: { code: 'BAD_REQUEST', message: "Confirmation text must be 'RESET DIAGNOSTIC'" } },
        { status: 400 }
      )
    }
    // Reset mock state
    answerCount = 0
    isSessionResumed = false
    sessionCurrentIndex = 0
    return HttpResponse.json(mockDiagnosticResetResponse)
  }),
]

export const diagnosticErrorHandlers = [
  http.get('*/diagnostic/questions', () => {
    return HttpResponse.json(
      { error: { code: 'INTERNAL_ERROR', message: 'Failed to fetch questions' } },
      { status: 500 }
    )
  }),
]

/** Handlers for testing resumed session flow (Story 3.9) */
export const diagnosticResumedHandlers = [
  http.get('*/diagnostic/questions', () => {
    return HttpResponse.json(createMockResumedQuestionsResponse(1))
  }),
]

export const resetDiagnosticMocks = () => {
  answerCount = 0
  isSessionResumed = false
  sessionCurrentIndex = 0
}

/** Configure mock to return resumed session (Story 3.9) */
export const setMockResumedSession = (currentIndex: number) => {
  isSessionResumed = true
  sessionCurrentIndex = currentIndex
}
