import api from './api'
import type {
  DiagnosticQuestionsResponse,
  DiagnosticAnswerRequest,
  DiagnosticAnswerResponse,
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
}
