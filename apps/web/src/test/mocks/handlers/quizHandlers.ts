import { http, HttpResponse } from 'msw'
import {
  mockSessionStartResponse,
  mockSessionResumedResponse,
  mockSessionPauseResponse,
  mockSessionResumeResponse,
  mockSessionEndResponse,
  mockSessionDetailsResponse,
  mockCorrectAnswerResponse,
  mockIncorrectAnswerResponse,
} from '../../fixtures/quizFixtures'

let mockIsResumed = false
let mockSessionPaused = false
let mockNextAnswerCorrect = true
let mockLastRequestId: string | null = null

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

  // Submit answer
  http.post('*/quiz/answer', ({ request }) => {
    const requestId = request.headers.get('X-Request-ID')
    mockLastRequestId = requestId

    if (mockNextAnswerCorrect) {
      return HttpResponse.json(mockCorrectAnswerResponse)
    }
    return HttpResponse.json(mockIncorrectAnswerResponse)
  }),

  // Get next question (default mock - can be overridden in tests)
  http.post('*/quiz/next-question', () => {
    return HttpResponse.json({
      session_id: 'session-uuid-123',
      question: {
        question_id: 'question-uuid-default',
        question_text: 'Default mock question?',
        options: {
          A: 'Option A',
          B: 'Option B',
          C: 'Option C',
          D: 'Option D',
        },
        knowledge_area_id: 'ka-uuid-1',
        knowledge_area_name: 'Planning',
        difficulty: 0.5,
        estimated_info_gain: 0.8,
        concepts_tested: ['Concept 1'],
      },
      questions_remaining: 5,
    })
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
 * Handlers for answer already answered (409 conflict).
 */
export const quizAnswerAlreadyAnsweredHandlers = [
  http.post('*/quiz/answer', () => {
    return HttpResponse.json(
      { detail: 'Question has already been answered in this session' },
      { status: 409 }
    )
  }),
]

/**
 * Handlers for invalid session (404).
 */
export const quizAnswerInvalidSessionHandlers = [
  http.post('*/quiz/answer', () => {
    return HttpResponse.json(
      { detail: 'Session not found' },
      { status: 404 }
    )
  }),
]

/**
 * Handlers for invalid question (404).
 */
export const quizAnswerInvalidQuestionHandlers = [
  http.post('*/quiz/answer', () => {
    return HttpResponse.json(
      { detail: 'Question not found' },
      { status: 404 }
    )
  }),
]

/**
 * Reset mock state.
 */
export function resetQuizMocks() {
  mockIsResumed = false
  mockSessionPaused = false
  mockNextAnswerCorrect = true
  mockLastRequestId = null
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

/**
 * Configure mock for next answer correctness.
 */
export function setMockNextAnswerCorrect(isCorrect: boolean) {
  mockNextAnswerCorrect = isCorrect
}

/**
 * Get the last request ID received by the answer endpoint.
 */
export function getLastRequestId(): string | null {
  return mockLastRequestId
}
