import api from './api'

/**
 * Response from checking if review is available.
 * Story 4.9: Post-Session Review Mode
 */
export interface ReviewAvailableResponse {
  available: boolean
  incorrect_count: number
  question_ids: string[]
}

/**
 * Response from starting/getting a review session.
 * Story 4.9: Post-Session Review Mode
 */
export interface ReviewSessionResponse {
  id: string
  original_session_id: string
  status: 'pending' | 'in_progress' | 'completed' | 'skipped'
  total_to_review: number
  reviewed_count: number
  reinforced_count: number
  still_incorrect_count: number
  started_at: string | null
  created_at: string
}

/**
 * Response from getting next review question.
 * Story 4.9: Post-Session Review Mode
 */
export interface ReviewQuestionResponse {
  question_id: string
  question_text: string
  options: Record<string, string>
  review_number: number
  total_to_review: number
}

/**
 * Request for submitting a review answer.
 * Story 4.9: Post-Session Review Mode
 */
export interface ReviewAnswerRequest {
  question_id: string
  selected_answer: string
}

/**
 * Concept update information from review answer.
 * Story 4.9: Post-Session Review Mode
 */
export interface ReviewConceptUpdate {
  concept_id: string
  name: string
  new_mastery: number
}

/**
 * Response from submitting a review answer.
 * Story 4.9: Post-Session Review Mode
 */
export interface ReviewAnswerResponse {
  is_correct: boolean
  was_reinforced: boolean
  correct_answer: string
  explanation: string
  concepts_updated: ReviewConceptUpdate[]
  feedback_message: string
  reading_link: string | null
}

/**
 * Concept that was still incorrect after review.
 * Story 4.9: Post-Session Review Mode
 */
export interface StillIncorrectConcept {
  concept_id: string
  name: string
  reading_link: string
}

/**
 * Response from skipping a review session.
 * Story 4.9: Post-Session Review Mode
 */
export interface ReviewSkipResponse {
  message: string
  session_id: string
  questions_skipped: number
}

/**
 * Response from getting review summary.
 * Story 4.9: Post-Session Review Mode
 */
export interface ReviewSummaryResponse {
  total_reviewed: number
  reinforced_count: number
  still_incorrect_count: number
  reinforcement_rate: number
  still_incorrect_concepts: StillIncorrectConcept[]
}

/**
 * Service for review session API calls.
 * Story 4.9: Post-Session Review Mode
 */
export const reviewService = {
  /**
   * Check if review is available for a quiz session.
   * @param sessionId - Original quiz session UUID
   * @returns Review availability response
   */
  async checkReviewAvailable(sessionId: string): Promise<ReviewAvailableResponse> {
    const response = await api.get<ReviewAvailableResponse>(
      `/quiz/session/${sessionId}/review-available`
    )
    return response.data
  },

  /**
   * Start a review session for a quiz session.
   * @param sessionId - Original quiz session UUID
   * @returns Review session response
   */
  async startReview(sessionId: string): Promise<ReviewSessionResponse> {
    const response = await api.post<ReviewSessionResponse>(
      `/quiz/session/${sessionId}/review/start`
    )
    return response.data
  },

  /**
   * Get the next question to review.
   * @param reviewSessionId - Review session UUID
   * @returns Next review question or null if all reviewed
   */
  async getNextReviewQuestion(reviewSessionId: string): Promise<ReviewQuestionResponse | null> {
    const response = await api.get<ReviewQuestionResponse | null>(
      `/quiz/review/${reviewSessionId}/next-question`
    )
    return response.data
  },

  /**
   * Submit an answer to a review question.
   * @param reviewSessionId - Review session UUID
   * @param request - Answer submission data
   * @returns Answer feedback response
   */
  async submitReviewAnswer(
    reviewSessionId: string,
    request: ReviewAnswerRequest
  ): Promise<ReviewAnswerResponse> {
    const response = await api.post<ReviewAnswerResponse>(
      `/quiz/review/${reviewSessionId}/answer`,
      request
    )
    return response.data
  },

  /**
   * Skip the review session.
   * @param reviewSessionId - Review session UUID
   * @returns Skip confirmation response
   */
  async skipReview(reviewSessionId: string): Promise<ReviewSkipResponse> {
    const response = await api.post<ReviewSkipResponse>(
      `/quiz/review/${reviewSessionId}/skip`
    )
    return response.data
  },

  /**
   * Get the summary of a completed review session.
   * @param reviewSessionId - Review session UUID
   * @returns Review summary response
   */
  async getReviewSummary(reviewSessionId: string): Promise<ReviewSummaryResponse> {
    const response = await api.get<ReviewSummaryResponse>(
      `/quiz/review/${reviewSessionId}/summary`
    )
    return response.data
  },
}
