import { http, HttpResponse } from 'msw'
import {
  mockDiagnosticQuestionsResponse,
  createMockAnswerResponse,
} from '../../fixtures/diagnosticFixtures'

let answerCount = 0

export const diagnosticHandlers = [
  // Match both relative and absolute URLs
  http.get('*/diagnostic/questions', () => {
    return HttpResponse.json(mockDiagnosticQuestionsResponse)
  }),

  http.post('*/diagnostic/answer', async () => {
    answerCount++
    return HttpResponse.json(createMockAnswerResponse(answerCount, 3))
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

export const resetDiagnosticMocks = () => {
  answerCount = 0
}
