import api from './api'

/**
 * Quiz session type determines question selection strategy.
 */
export type SessionType = 'diagnostic' | 'adaptive' | 'focused' | 'review'

/**
 * Question selection strategy for the session.
 */
export type QuestionStrategy =
  | 'max_info_gain'
  | 'max_uncertainty'
  | 'prerequisite_first'
  | 'balanced'

/**
 * Configuration for starting a quiz session.
 */
export interface SessionConfig {
  session_type?: SessionType
  question_strategy?: QuestionStrategy
  knowledge_area_filter?: string
}

/**
 * Response from starting a quiz session.
 */
export interface SessionStartResponse {
  session_id: string
  session_type: SessionType
  question_strategy: QuestionStrategy
  is_resumed: boolean
  status: string
  started_at: string
  version: number
  total_questions: number
  correct_count: number
  first_question: null // Placeholder for Story 4.2
}

/**
 * Response from getting session details.
 */
export interface SessionDetailsResponse {
  id: string
  session_type: SessionType
  question_strategy: QuestionStrategy
  status: string
  is_paused: boolean
  started_at: string
  ended_at: string | null
  total_questions: number
  correct_count: number
  accuracy: number | null
  version: number
}

/**
 * Response from pausing a session.
 */
export interface SessionPauseResponse {
  session_id: string
  status: string
  is_paused: boolean
  version: number
}

/**
 * Response from resuming a session.
 */
export interface SessionResumeResponse {
  session_id: string
  status: string
  is_paused: boolean
  version: number
}

/**
 * Response from ending a session.
 */
export interface SessionEndResponse {
  session_id: string
  ended_at: string
  total_questions: number
  correct_count: number
  accuracy: number | null
}

/**
 * Selected question returned from next-question endpoint.
 */
export interface SelectedQuestion {
  question_id: string
  question_text: string
  options: Record<string, string>
  knowledge_area_id: string
  knowledge_area_name: string | null
  difficulty: number
  estimated_info_gain: number
  concepts_tested: string[]
}

/**
 * Request for getting next question.
 */
export interface NextQuestionRequest {
  session_id: string
  strategy?: QuestionStrategy
}

/**
 * Response from next-question endpoint.
 */
export interface NextQuestionResponse {
  session_id: string
  question: SelectedQuestion
  questions_remaining: number
}

/**
 * Request for submitting an answer.
 */
export interface AnswerSubmissionRequest {
  session_id: string
  question_id: string
  selected_answer: string
}

/**
 * Concept update information after answer submission.
 */
export interface ConceptUpdate {
  concept_id: string
  name: string
  new_mastery: number
}

/**
 * Session statistics after answer submission.
 */
export interface SessionStats {
  questions_answered: number
  accuracy: number
  total_info_gain: number
  coverage_progress: number
  session_version: number
}

/**
 * Response from answer submission endpoint.
 */
export interface AnswerResponse {
  is_correct: boolean
  correct_answer: string
  explanation: string
  concepts_updated: ConceptUpdate[]
  session_stats: SessionStats
}

/**
 * Service for quiz session API calls.
 * Uses axios with JWT token from authStore.
 */
export const quizService = {
  /**
   * Start a new quiz session or resume an existing active session.
   * @param config - Optional session configuration
   * @returns Session start response including session_id and is_resumed flag
   * @throws AxiosError with status 401 if not authenticated
   * @throws AxiosError with status 400 if no enrollment found
   */
  async startSession(config?: SessionConfig): Promise<SessionStartResponse> {
    const response = await api.post<SessionStartResponse>(
      '/quiz/session/start',
      config || {}
    )
    return response.data
  },

  /**
   * Get details of a quiz session.
   * @param sessionId - UUID of the session
   * @returns Session details including status and statistics
   * @throws AxiosError with status 401 if not authenticated
   * @throws AxiosError with status 404 if session not found
   */
  async getSession(sessionId: string): Promise<SessionDetailsResponse> {
    const response = await api.get<SessionDetailsResponse>(
      `/quiz/session/${sessionId}`
    )
    return response.data
  },

  /**
   * Pause an active quiz session.
   * @param sessionId - UUID of the session
   * @returns Updated session status
   * @throws AxiosError with status 401 if not authenticated
   * @throws AxiosError with status 404 if session not found
   * @throws AxiosError with status 400 if session cannot be paused
   */
  async pauseSession(sessionId: string): Promise<SessionPauseResponse> {
    const response = await api.post<SessionPauseResponse>(
      `/quiz/session/${sessionId}/pause`
    )
    return response.data
  },

  /**
   * Resume a paused quiz session.
   * @param sessionId - UUID of the session
   * @returns Updated session status
   * @throws AxiosError with status 401 if not authenticated
   * @throws AxiosError with status 404 if session not found
   * @throws AxiosError with status 400 if session cannot be resumed
   */
  async resumeSession(sessionId: string): Promise<SessionResumeResponse> {
    const response = await api.post<SessionResumeResponse>(
      `/quiz/session/${sessionId}/resume`
    )
    return response.data
  },

  /**
   * End a quiz session.
   * Uses optimistic locking via expected_version to prevent race conditions.
   * @param sessionId - UUID of the session
   * @param expectedVersion - Version number for optimistic locking
   * @returns Session summary with final statistics
   * @throws AxiosError with status 401 if not authenticated
   * @throws AxiosError with status 404 if session not found
   * @throws AxiosError with status 409 if version conflict
   */
  async endSession(
    sessionId: string,
    expectedVersion: number
  ): Promise<SessionEndResponse> {
    const response = await api.post<SessionEndResponse>(
      `/quiz/session/${sessionId}/end`,
      { expected_version: expectedVersion }
    )
    return response.data
  },

  /**
   * Get the next question for an active quiz session.
   * Uses Bayesian question selection to maximize information gain.
   * @param request - Session ID and optional strategy override
   * @returns Selected question with metadata
   * @throws AxiosError with status 401 if not authenticated
   * @throws AxiosError with status 404 if session not found
   * @throws AxiosError with status 400 if no questions available
   */
  async getNextQuestion(request: NextQuestionRequest): Promise<NextQuestionResponse> {
    const response = await api.post<NextQuestionResponse>(
      '/quiz/next-question',
      request
    )
    return response.data
  },

  /**
   * Submit an answer for the current question.
   * @param request - Answer submission data (session_id, question_id, selected_answer)
   * @param requestId - Unique request ID for idempotency
   * @returns Answer feedback including correctness, explanation, and stats
   * @throws AxiosError with status 401 if not authenticated
   * @throws AxiosError with status 404 if session or question not found
   * @throws AxiosError with status 409 if question already answered
   * @throws AxiosError with status 400 if invalid answer format
   */
  async submitAnswer(
    request: AnswerSubmissionRequest,
    requestId: string
  ): Promise<AnswerResponse> {
    const response = await api.post<AnswerResponse>(
      '/quiz/answer',
      request,
      {
        headers: {
          'X-Request-ID': requestId,
        },
      }
    )
    return response.data
  },
}
