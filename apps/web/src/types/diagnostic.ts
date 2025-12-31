// Diagnostic Assessment Types (Story 3.6, 3.9)

/** Answer option letter type */
export type AnswerLetter = 'A' | 'B' | 'C' | 'D'

/** Diagnostic session status (Story 3.9) */
export type DiagnosticSessionStatus = 'in_progress' | 'completed' | 'expired' | 'reset'

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
  /** Session ID for tracking progress (Story 3.9) */
  session_id: string
  /** Current session status (Story 3.9) */
  session_status: DiagnosticSessionStatus
  /** Current position in question sequence (Story 3.9) */
  current_index: number
  /** Whether this is resuming an existing session (Story 3.9) */
  is_resumed: boolean
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
  /** Updated session status after answer (Story 3.9) */
  session_status: DiagnosticSessionStatus
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
  /** Overall competence as percentage (0-100), based on assessed concepts only */
  overall_competence: number | null
  /** Number of concepts that have been assessed (response_count > 0) */
  concepts_assessed: number
  /** Whether user has completed at least one adaptive quiz session */
  has_completed_adaptive_quiz: boolean
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

// ==================== Diagnostic Session Management Types (Story 3.9) ====================

/** Request body for POST /api/v1/diagnostic/reset */
export interface DiagnosticResetRequest {
  /** Must be 'RESET DIAGNOSTIC' to confirm */
  confirmation: string
}

/** Response from POST /api/v1/diagnostic/reset */
export interface DiagnosticResetResponse {
  message: string
  session_cleared: boolean
  beliefs_reset_count: number
  can_retake: boolean
}
