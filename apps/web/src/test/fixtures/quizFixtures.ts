import type {
  SessionStartResponse,
  SessionDetailsResponse,
  SessionPauseResponse,
  SessionResumeResponse,
  SessionEndResponse,
  AnswerResponse,
  AnswerSubmissionRequest,
  SessionSummary,
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
  version: 1,
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
  version: 6,  // Resumed session has higher version due to previous updates
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
  version: 3,
}

/**
 * Mock response for resuming a session.
 */
export const mockSessionResumeResponse: SessionResumeResponse = {
  session_id: 'session-uuid-123',
  status: 'active',
  is_paused: false,
  version: 4,
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

/**
 * Mock correct answer response.
 */
export const mockCorrectAnswerResponse: AnswerResponse = {
  is_correct: true,
  correct_answer: 'A',
  explanation: 'Stakeholder analysis is the process of identifying individuals or groups that may be affected by a project.',
  concepts_updated: [
    {
      concept_id: 'concept-uuid-1',
      name: 'Stakeholder Analysis',
      new_mastery: 0.72,
    },
  ],
  session_stats: {
    questions_answered: 8,
    accuracy: 0.75,
    total_info_gain: 12.4,
    coverage_progress: 0.52,
    session_version: 9,
  },
  // Story 4.7: Auto-completion fields
  session_completed: false,
  session_summary: null,
}

/**
 * Mock incorrect answer response.
 */
export const mockIncorrectAnswerResponse: AnswerResponse = {
  is_correct: false,
  correct_answer: 'B',
  explanation: 'Requirements traceability ensures that all requirements are linked to their sources and downstream artifacts.',
  concepts_updated: [
    {
      concept_id: 'concept-uuid-2',
      name: 'Requirements Traceability',
      new_mastery: 0.45,
    },
  ],
  session_stats: {
    questions_answered: 9,
    accuracy: 0.67,
    total_info_gain: 14.2,
    coverage_progress: 0.58,
    session_version: 10,
  },
  // Story 4.7: Auto-completion fields
  session_completed: false,
  session_summary: null,
}

/**
 * Story 4.7: Mock session summary for completed session.
 */
export const mockSessionSummary: SessionSummary = {
  questions_answered: 12,
  question_target: 12,
  correct_count: 9,
  accuracy: 75.0,
  concepts_strengthened: 8,
  quizzes_completed_total: 5,
  session_duration_seconds: 480,
}

/**
 * Story 4.7: Mock answer response with session completion.
 */
export const mockCompletedSessionAnswerResponse: AnswerResponse = {
  is_correct: true,
  correct_answer: 'C',
  explanation: 'Final question explanation.',
  concepts_updated: [
    {
      concept_id: 'concept-uuid-3',
      name: 'Business Process Modeling',
      new_mastery: 0.85,
    },
  ],
  session_stats: {
    questions_answered: 12,
    accuracy: 0.75,
    total_info_gain: 18.5,
    coverage_progress: 0.72,
    session_version: 13,
  },
  session_completed: true,
  session_summary: mockSessionSummary,
}

/**
 * Mock answer submission request.
 */
export const mockAnswerSubmissionRequest: AnswerSubmissionRequest = {
  session_id: 'session-uuid-123',
  question_id: 'question-uuid-456',
  selected_answer: 'A',
}

/**
 * Create mock answer response with custom properties.
 */
export function createMockAnswerResponse(
  overrides?: Partial<AnswerResponse>
): AnswerResponse {
  return {
    ...mockCorrectAnswerResponse,
    ...overrides,
  }
}
