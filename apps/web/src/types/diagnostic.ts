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

// ==================== Diagnostic Results Types (Story 3.8) ====================

/** Per-knowledge area statistics */
export interface KnowledgeAreaResult {
  ka: string
  ka_id: string
  concepts: number
  touched: number
  estimated_mastery: number
}

/** Identified gap concept */
export interface ConceptGap {
  concept_id: string
  name: string
  mastery_probability: number
  knowledge_area: string
}

/** Recommendations from diagnostic results */
export interface Recommendations {
  primary_focus: string
  estimated_questions_to_coverage: number
  message: string
}

/** Confidence level for knowledge profile */
export type ConfidenceLevel = 'initial' | 'developing' | 'established'

/** Diagnostic test score summary */
export interface DiagnosticScore {
  questions_answered: number
  questions_correct: number
  questions_incorrect: number
  score_percentage: number
}

/** Response from GET /api/v1/diagnostic/results */
export interface DiagnosticResultsResponse {
  score: DiagnosticScore
  total_concepts: number
  concepts_touched: number
  coverage_percentage: number
  estimated_mastered: number
  estimated_gaps: number
  uncertain: number
  confidence_level: ConfidenceLevel
  by_knowledge_area: KnowledgeAreaResult[]
  top_gaps: ConceptGap[]
  recommendations: Recommendations
}

/** Request body for POST /api/v1/diagnostic/feedback */
export interface DiagnosticFeedbackRequest {
  rating: number
  comment?: string
}

/** Response from POST /api/v1/diagnostic/feedback */
export interface DiagnosticFeedbackResponse {
  success: boolean
  message: string
}
