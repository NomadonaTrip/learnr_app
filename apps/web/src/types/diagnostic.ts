// Diagnostic Assessment Types (Story 3.6)

/** Answer option letter type */
export type AnswerLetter = 'A' | 'B' | 'C' | 'D'

/** Question as returned from GET /api/v1/diagnostic/questions */
export interface DiagnosticQuestion {
  id: string
  question_text: string
  options: {
    A: string
    B: string
    C: string
    D: string
  }
  knowledge_area_id: string
  difficulty: number
  discrimination: number
}

/** Response from GET /api/v1/diagnostic/questions */
export interface DiagnosticQuestionsResponse {
  questions: DiagnosticQuestion[]
  total: number
  concepts_covered: number
  coverage_percentage: number
}

/** Request body for POST /api/v1/diagnostic/answer */
export interface DiagnosticAnswerRequest {
  question_id: string
  selected_answer: AnswerLetter
}

/** Response from POST /api/v1/diagnostic/answer */
export interface DiagnosticAnswerResponse {
  is_recorded: boolean
  concepts_updated: string[]
  diagnostic_progress: number
  diagnostic_total: number
}

/** User's answer record */
export interface DiagnosticAnswer {
  questionId: string
  selectedAnswer: AnswerLetter
  submittedAt: Date
}
