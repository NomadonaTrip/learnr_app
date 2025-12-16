import type {
  DiagnosticQuestion,
  DiagnosticQuestionsResponse,
  DiagnosticAnswerResponse,
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

export const mockDiagnosticQuestionsResponse: DiagnosticQuestionsResponse = {
  questions: mockDiagnosticQuestions,
  total: 3,
  concepts_covered: 487,
  coverage_percentage: 0.405,
}

export const mockDiagnosticAnswerResponse: DiagnosticAnswerResponse = {
  is_recorded: true,
  concepts_updated: ['concept-1-uuid', 'concept-2-uuid'],
  diagnostic_progress: 1,
  diagnostic_total: 3,
}

/** Factory to create answer response with custom progress */
export const createMockAnswerResponse = (
  progress: number,
  total: number = 3
): DiagnosticAnswerResponse => ({
  is_recorded: true,
  concepts_updated: ['concept-uuid'],
  diagnostic_progress: progress,
  diagnostic_total: total,
})
