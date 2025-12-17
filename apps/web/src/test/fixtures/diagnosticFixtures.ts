import type {
  DiagnosticQuestion,
  DiagnosticQuestionsResponse,
  DiagnosticAnswerResponse,
  DiagnosticResetResponse,
  DiagnosticSessionStatus,
} from '../../types/diagnostic'

export const mockDiagnosticQuestions: DiagnosticQuestion[] = [
  {
    id: 'q1-uuid',
    question_text: 'Which technique is BEST suited for identifying stakeholder concerns early in a project?',
    options: {
      A: 'SWOT Analysis',
      B: 'Stakeholder Map',
      C: 'Requirements Workshop',
      D: 'Document Analysis',
    },
    knowledge_area_id: 'ba-planning',
    difficulty: 0.55,
    discrimination: 1.1,
  },
  {
    id: 'q2-uuid',
    question_text: 'What is the PRIMARY purpose of a business case?',
    options: {
      A: 'To document requirements',
      B: 'To justify the investment in a project',
      C: 'To create a project schedule',
      D: 'To assign resources',
    },
    knowledge_area_id: 'strategy',
    difficulty: 0.45,
    discrimination: 1.3,
  },
  {
    id: 'q3-uuid',
    question_text: 'Which elicitation technique is MOST effective for understanding tacit knowledge?',
    options: {
      A: 'Survey',
      B: 'Document Analysis',
      C: 'Observation',
      D: 'Interface Analysis',
    },
    knowledge_area_id: 'elicitation',
    difficulty: 0.65,
    discrimination: 1.2,
  },
]

/** Mock session ID for testing */
export const mockSessionId = 'session-uuid-12345'

export const mockDiagnosticQuestionsResponse: DiagnosticQuestionsResponse = {
  questions: mockDiagnosticQuestions,
  total: 3,
  concepts_covered: 487,
  coverage_percentage: 0.405,
  // Session fields (Story 3.9)
  session_id: mockSessionId,
  session_status: 'in_progress',
  current_index: 0,
  is_resumed: false,
}

/** Create mock questions response for resumed session (Story 3.9) */
export const createMockResumedQuestionsResponse = (
  currentIndex: number
): DiagnosticQuestionsResponse => ({
  questions: mockDiagnosticQuestions.slice(currentIndex),
  total: 3,
  concepts_covered: 487,
  coverage_percentage: 0.405,
  session_id: mockSessionId,
  session_status: 'in_progress',
  current_index: currentIndex,
  is_resumed: true,
})

export const mockDiagnosticAnswerResponse: DiagnosticAnswerResponse = {
  is_recorded: true,
  concepts_updated: ['concept-1-uuid', 'concept-2-uuid'],
  diagnostic_progress: 1,
  diagnostic_total: 3,
  session_status: 'in_progress', // Story 3.9
}

/** Factory to create answer response with custom progress (Story 3.9 updated) */
export const createMockAnswerResponse = (
  progress: number,
  total: number = 3,
  sessionStatus: DiagnosticSessionStatus = 'in_progress'
): DiagnosticAnswerResponse => ({
  is_recorded: true,
  concepts_updated: ['concept-uuid'],
  diagnostic_progress: progress,
  diagnostic_total: total,
  session_status: sessionStatus,
})

/** Mock reset response (Story 3.9) */
export const mockDiagnosticResetResponse: DiagnosticResetResponse = {
  message: 'Diagnostic reset successfully',
  session_cleared: true,
  beliefs_reset_count: 487,
  can_retake: true,
}

/** Helper to create SetQuestionsParams for store tests */
export const createMockSetQuestionsParams = (overrides?: {
  questions?: DiagnosticQuestion[]
  sessionProgress?: number
  sessionTotal?: number
  isResumed?: boolean
}) => ({
  questions: overrides?.questions ?? mockDiagnosticQuestions,
  totalConcepts: 487,
  coveragePercentage: 0.405,
  sessionId: mockSessionId,
  sessionStatus: 'in_progress' as DiagnosticSessionStatus,
  sessionProgress: overrides?.sessionProgress ?? 0,
  sessionTotal: overrides?.sessionTotal ?? 3,
  isResumed: overrides?.isResumed ?? false,
})
