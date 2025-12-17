import type {
  SessionStartResponse,
  SessionDetailsResponse,
  SessionPauseResponse,
  SessionResumeResponse,
  SessionEndResponse,
} from '../../services/quizService'

/**
 * Mock response for starting a new session.
 */
export const mockSessionStartResponse: SessionStartResponse = {
  session_id: 'session-uuid-123',
  session_type: 'adaptive',
  question_strategy: 'max_info_gain',
  is_resumed: false,
  status: 'active',
  started_at: '2025-12-17T10:00:00Z',
  total_questions: 0,
  correct_count: 0,
  first_question: null,
}

/**
 * Mock response for resuming an existing session.
 */
export const mockSessionResumedResponse: SessionStartResponse = {
  session_id: 'session-uuid-existing',
  session_type: 'adaptive',
  question_strategy: 'max_info_gain',
  is_resumed: true,
  status: 'active',
  started_at: '2025-12-17T09:00:00Z',
  total_questions: 5,
  correct_count: 3,
  first_question: null,
}

/**
 * Mock response for session details.
 */
export const mockSessionDetailsResponse: SessionDetailsResponse = {
  id: 'session-uuid-123',
  session_type: 'adaptive',
  question_strategy: 'max_info_gain',
  status: 'active',
  is_paused: false,
  started_at: '2025-12-17T10:00:00Z',
  ended_at: null,
  total_questions: 5,
  correct_count: 3,
  accuracy: 60,
  version: 2,
}

/**
 * Mock response for pausing a session.
 */
export const mockSessionPauseResponse: SessionPauseResponse = {
  session_id: 'session-uuid-123',
  status: 'paused',
  is_paused: true,
}

/**
 * Mock response for resuming a session.
 */
export const mockSessionResumeResponse: SessionResumeResponse = {
  session_id: 'session-uuid-123',
  status: 'active',
  is_paused: false,
}

/**
 * Mock response for ending a session.
 */
export const mockSessionEndResponse: SessionEndResponse = {
  session_id: 'session-uuid-123',
  ended_at: '2025-12-17T11:00:00Z',
  total_questions: 10,
  correct_count: 7,
  accuracy: 70,
}

/**
 * Create mock start response with custom properties.
 */
export function createMockStartResponse(
  overrides?: Partial<SessionStartResponse>
): SessionStartResponse {
  return {
    ...mockSessionStartResponse,
    ...overrides,
  }
}

/**
 * Create mock details response with custom properties.
 */
export function createMockDetailsResponse(
  overrides?: Partial<SessionDetailsResponse>
): SessionDetailsResponse {
  return {
    ...mockSessionDetailsResponse,
    ...overrides,
  }
}

/**
 * Create mock end response with custom properties.
 */
export function createMockEndResponse(
  overrides?: Partial<SessionEndResponse>
): SessionEndResponse {
  return {
    ...mockSessionEndResponse,
    ...overrides,
  }
}
