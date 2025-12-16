import api from './api'
import type {
  DiagnosticQuestionsResponse,
  DiagnosticAnswerRequest,
  DiagnosticAnswerResponse,
  DiagnosticResultsResponse,
  DiagnosticFeedbackRequest,
  DiagnosticFeedbackResponse,
} from '../types/diagnostic'

/**
 * Service for diagnostic assessment API calls.
 * Uses axios with JWT token from authStore.
 */
export const diagnosticService = {
  /**
   * Fetch the optimally-selected diagnostic questions for a course.
   * Response excludes correct_answer and explanation.
   * @param courseId - UUID of the course
   * @param targetCount - Target number of questions (12-20, default 15)
   * @returns Questions with metadata (total, coverage)
   * @throws AxiosError with status 401 if not authenticated
   * @throws AxiosError with status 422 if courseId is missing
   */
  async fetchDiagnosticQuestions(
    courseId: string,
    targetCount: number = 15
  ): Promise<DiagnosticQuestionsResponse> {
    const response = await api.get<DiagnosticQuestionsResponse>('/diagnostic/questions', {
      params: {
        course_id: courseId,
        target_count: targetCount,
      },
    })
    return response.data
  },

  /**
   * Submit an answer for a diagnostic question.
   * No immediate feedback returned during diagnostic.
   * @param questionId - UUID of the question
   * @param selectedAnswer - Letter of selected option (A/B/C/D)
   * @returns Recording confirmation and progress
   * @throws AxiosError with status 401 if not authenticated
   */
  async submitDiagnosticAnswer(
    questionId: string,
    selectedAnswer: DiagnosticAnswerRequest['selected_answer']
  ): Promise<DiagnosticAnswerResponse> {
    const payload: DiagnosticAnswerRequest = {
      question_id: questionId,
      selected_answer: selectedAnswer,
    }
    const response = await api.post<DiagnosticAnswerResponse>('/diagnostic/answer', payload)
    return response.data
  },

  /**
   * Fetch diagnostic results after completing the assessment.
   * @param courseId - UUID of the course
   * @returns Comprehensive diagnostic results with coverage stats
   * @throws AxiosError with status 401 if not authenticated
   * @throws AxiosError with status 404 if no diagnostic completed
   */
  async fetchDiagnosticResults(courseId: string): Promise<DiagnosticResultsResponse> {
    const response = await api.get<DiagnosticResultsResponse>('/diagnostic/results', {
      params: { course_id: courseId },
    })
    return response.data
  },

  /**
   * Submit post-diagnostic feedback survey.
   * @param courseId - UUID of the course
   * @param rating - Accuracy rating 1-5
   * @param comment - Optional feedback comment
   * @returns Confirmation response
   * @throws AxiosError with status 401 if not authenticated
   */
  async submitDiagnosticFeedback(
    courseId: string,
    rating: number,
    comment?: string
  ): Promise<DiagnosticFeedbackResponse> {
    const payload: DiagnosticFeedbackRequest = { rating, comment }
    const response = await api.post<DiagnosticFeedbackResponse>('/diagnostic/feedback', payload, {
      params: { course_id: courseId },
    })
    return response.data
  },
}
