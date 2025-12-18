import { http, HttpResponse } from 'msw'
import {
  mockSessionStartResponse,
  mockSessionResumedResponse,
  mockSessionPauseResponse,
  mockSessionResumeResponse,
  mockSessionEndResponse,
  mockSessionDetailsResponse,
} from '../../fixtures/quizFixtures'

let mockIsResumed = false
let mockSessionPaused = false

/**
 * Default handlers for quiz session endpoints.
 */
export const quizHandlers = [
  // Start session
  http.post('*/quiz/session/start', () => {
    if (mockIsResumed) {
      return HttpResponse.json(mockSessionResumedResponse)
    }
    return HttpResponse.json(mockSessionStartResponse)
  }),

  // Get session details
  http.get('*/quiz/session/:id', () => {
    return HttpResponse.json({
      ...mockSessionDetailsResponse,
      is_paused: mockSessionPaused,
      status: mockSessionPaused ? 'paused' : 'active',
    })
  }),

  // Pause session
  http.post('*/quiz/session/:id/pause', () => {
    mockSessionPaused = true
    return HttpResponse.json(mockSessionPauseResponse)
  }),

  // Resume session
  http.post('*/quiz/session/:id/resume', () => {
    mockSessionPaused = false
    return HttpResponse.json(mockSessionResumeResponse)
  }),

  // End session
  http.post('*/quiz/session/:id/end', () => {
    return HttpResponse.json(mockSessionEndResponse)
  }),
]

/**
 * Error handlers for testing error states.
 */
export const quizErrorHandlers = [
  http.post('*/quiz/session/start', () => {
    return HttpResponse.json(
      { detail: 'No active enrollment found. Please complete the diagnostic first.' },
      { status: 400 }
    )
  }),
]

/**
 * Handlers for resumed session testing.
 */
export const quizResumedHandlers = [
  http.post('*/quiz/session/start', () => {
    return HttpResponse.json(mockSessionResumedResponse)
  }),
]

/**
 * Handlers for version conflict testing.
 */
export const quizConflictHandlers = [
  ...quizHandlers.filter((h) => !h.info.path?.toString().includes('end')),
  http.post('*/quiz/session/:id/end', () => {
    return HttpResponse.json(
      { detail: 'Session has been modified. Please refresh and try again.' },
      { status: 409 }
    )
  }),
]

/**
 * Reset mock state.
 */
export function resetQuizMocks() {
  mockIsResumed = false
  mockSessionPaused = false
}

/**
 * Configure mock for resumed session.
 */
export function setMockResumedSession(isResumed: boolean) {
  mockIsResumed = isResumed
}

/**
 * Configure mock for paused session.
 */
export function setMockSessionPaused(isPaused: boolean) {
  mockSessionPaused = isPaused
}
