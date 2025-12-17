import { describe, it, expect, beforeEach } from 'vitest'
import { useDiagnosticStore } from '../../stores/diagnosticStore'
import type { DiagnosticQuestion, DiagnosticSessionStatus } from '../../types/diagnostic'

/** Mock session data for testing (Story 3.9) */
const mockSessionId = 'session-uuid-12345'
const mockSessionStatus: DiagnosticSessionStatus = 'in_progress'

const mockQuestions: DiagnosticQuestion[] = [
  {
    id: 'q1-uuid',
    question_text: 'Question 1',
    options: { A: 'Option A', B: 'Option B', C: 'Option C', D: 'Option D' },
    knowledge_area_id: 'ba-planning',
    difficulty: 0.5,
    discrimination: 1.0,
  },
  {
    id: 'q2-uuid',
    question_text: 'Question 2',
    options: { A: 'Option A', B: 'Option B', C: 'Option C', D: 'Option D' },
    knowledge_area_id: 'strategy',
    difficulty: 0.6,
    discrimination: 1.1,
  },
  {
    id: 'q3-uuid',
    question_text: 'Question 3',
    options: { A: 'Option A', B: 'Option B', C: 'Option C', D: 'Option D' },
    knowledge_area_id: 'elicitation',
    difficulty: 0.7,
    discrimination: 1.2,
  },
]

describe('diagnosticStore', () => {
  beforeEach(() => {
    useDiagnosticStore.getState().resetDiagnostic()
  })

  describe('initial state', () => {
    it('starts with empty questions', () => {
      expect(useDiagnosticStore.getState().questions).toEqual([])
    })

    it('starts with currentIndex at 0', () => {
      expect(useDiagnosticStore.getState().currentIndex).toBe(0)
    })

    it('starts with empty answers', () => {
      expect(useDiagnosticStore.getState().answers).toEqual([])
    })

    it('starts with null startTime', () => {
      expect(useDiagnosticStore.getState().startTime).toBeNull()
    })

    it('starts with isSubmitting false', () => {
      expect(useDiagnosticStore.getState().isSubmitting).toBe(false)
    })

    it('starts with isComplete false', () => {
      expect(useDiagnosticStore.getState().isComplete).toBe(false)
    })

    // Story 3.9: Session state initial values
    it('starts with null sessionId', () => {
      expect(useDiagnosticStore.getState().sessionId).toBeNull()
    })

    it('starts with null sessionStatus', () => {
      expect(useDiagnosticStore.getState().sessionStatus).toBeNull()
    })

    it('starts with isResumed false', () => {
      expect(useDiagnosticStore.getState().isResumed).toBe(false)
    })
  })

  describe('setQuestions', () => {
    /** Helper to create setQuestions params with defaults */
    const createSetQuestionsParams = (overrides = {}) => ({
      questions: mockQuestions,
      totalConcepts: 487,
      coveragePercentage: 0.405,
      sessionId: mockSessionId,
      sessionStatus: mockSessionStatus,
      sessionProgress: 0,
      sessionTotal: 3,
      isResumed: false,
      ...overrides,
    })

    it('sets questions array', () => {
      useDiagnosticStore.getState().setQuestions(createSetQuestionsParams())
      expect(useDiagnosticStore.getState().questions).toEqual(mockQuestions)
    })

    it('sets totalConcepts', () => {
      useDiagnosticStore.getState().setQuestions(createSetQuestionsParams())
      expect(useDiagnosticStore.getState().totalConcepts).toBe(487)
    })

    it('sets coveragePercentage', () => {
      useDiagnosticStore.getState().setQuestions(createSetQuestionsParams())
      expect(useDiagnosticStore.getState().coveragePercentage).toBe(0.405)
    })

    it('sets startTime to current date', () => {
      const before = new Date()
      useDiagnosticStore.getState().setQuestions(createSetQuestionsParams())
      const after = new Date()

      const startTime = useDiagnosticStore.getState().startTime
      expect(startTime).not.toBeNull()
      expect(startTime!.getTime()).toBeGreaterThanOrEqual(before.getTime())
      expect(startTime!.getTime()).toBeLessThanOrEqual(after.getTime())
    })

    it('always sets currentIndex to 0 (start of questions array)', () => {
      useDiagnosticStore.getState().setQuestions(createSetQuestionsParams({ sessionProgress: 0 }))
      expect(useDiagnosticStore.getState().currentIndex).toBe(0)
    })

    // Story 3.9: Test session progress tracking for resumed sessions
    it('tracks sessionProgress separately from currentIndex for resumed session', () => {
      useDiagnosticStore.getState().setQuestions(
        createSetQuestionsParams({ sessionProgress: 5, sessionTotal: 10, isResumed: true })
      )
      // currentIndex should always be 0 (start of remaining questions array)
      expect(useDiagnosticStore.getState().currentIndex).toBe(0)
      // sessionProgress tracks absolute progress
      expect(useDiagnosticStore.getState().sessionProgress).toBe(5)
      expect(useDiagnosticStore.getState().sessionTotal).toBe(10)
    })

    it('resets answers to empty', () => {
      useDiagnosticStore.getState().setQuestions(createSetQuestionsParams())
      useDiagnosticStore.getState().submitAnswer('q1-uuid', 'A')
      useDiagnosticStore.getState().setQuestions(createSetQuestionsParams())
      expect(useDiagnosticStore.getState().answers).toEqual([])
    })

    // Story 3.9: Session state tests
    it('sets sessionId from params', () => {
      useDiagnosticStore.getState().setQuestions(createSetQuestionsParams())
      expect(useDiagnosticStore.getState().sessionId).toBe(mockSessionId)
    })

    it('sets sessionStatus from params', () => {
      useDiagnosticStore.getState().setQuestions(createSetQuestionsParams())
      expect(useDiagnosticStore.getState().sessionStatus).toBe('in_progress')
    })

    it('sets isResumed to false for new session', () => {
      useDiagnosticStore.getState().setQuestions(createSetQuestionsParams({ isResumed: false }))
      expect(useDiagnosticStore.getState().isResumed).toBe(false)
    })

    it('sets isResumed to true for resumed session', () => {
      useDiagnosticStore.getState().setQuestions(createSetQuestionsParams({ isResumed: true }))
      expect(useDiagnosticStore.getState().isResumed).toBe(true)
    })
  })

  /** Helper for default params used in other test blocks */
  const defaultParams = {
    questions: mockQuestions,
    totalConcepts: 487,
    coveragePercentage: 0.405,
    sessionId: mockSessionId,
    sessionStatus: mockSessionStatus,
    sessionProgress: 0,
    sessionTotal: 3,
    isResumed: false,
  }

  describe('submitAnswer', () => {
    it('adds answer to answers array', () => {
      useDiagnosticStore.getState().setQuestions(defaultParams)
      useDiagnosticStore.getState().submitAnswer('q1-uuid', 'B')

      const answers = useDiagnosticStore.getState().answers
      expect(answers).toHaveLength(1)
      expect(answers[0].questionId).toBe('q1-uuid')
      expect(answers[0].selectedAnswer).toBe('B')
    })

    it('records submittedAt timestamp', () => {
      const before = new Date()
      useDiagnosticStore.getState().setQuestions(defaultParams)
      useDiagnosticStore.getState().submitAnswer('q1-uuid', 'A')
      const after = new Date()

      const answers = useDiagnosticStore.getState().answers
      expect(answers[0].submittedAt.getTime()).toBeGreaterThanOrEqual(before.getTime())
      expect(answers[0].submittedAt.getTime()).toBeLessThanOrEqual(after.getTime())
    })

    it('accumulates multiple answers', () => {
      useDiagnosticStore.getState().setQuestions(defaultParams)
      useDiagnosticStore.getState().submitAnswer('q1-uuid', 'A')
      useDiagnosticStore.getState().submitAnswer('q2-uuid', 'C')

      const answers = useDiagnosticStore.getState().answers
      expect(answers).toHaveLength(2)
    })
  })

  describe('nextQuestion', () => {
    it('increments currentIndex', () => {
      useDiagnosticStore.getState().setQuestions(defaultParams)
      useDiagnosticStore.getState().nextQuestion()
      expect(useDiagnosticStore.getState().currentIndex).toBe(1)
    })

    it('does not go past last question', () => {
      useDiagnosticStore.getState().setQuestions(defaultParams)
      useDiagnosticStore.getState().nextQuestion() // 1
      useDiagnosticStore.getState().nextQuestion() // 2
      useDiagnosticStore.getState().nextQuestion() // should stay at 2
      expect(useDiagnosticStore.getState().currentIndex).toBe(2)
    })
  })

  describe('progressPercentage', () => {
    it('returns 0 when sessionTotal is 0', () => {
      expect(useDiagnosticStore.getState().progressPercentage()).toBe(0)
    })

    it('returns 0 for first question of new session', () => {
      useDiagnosticStore.getState().setQuestions(defaultParams)
      // sessionProgress=0, currentIndex=0, sessionTotal=3 => 0/3 = 0%
      expect(useDiagnosticStore.getState().progressPercentage()).toBe(0)
    })

    it('returns 33 after answering first of three questions', () => {
      useDiagnosticStore.getState().setQuestions(defaultParams)
      useDiagnosticStore.getState().nextQuestion()
      // sessionProgress=0, currentIndex=1, sessionTotal=3 => 1/3 = 33%
      expect(useDiagnosticStore.getState().progressPercentage()).toBe(33)
    })

    it('returns 67 after answering two of three questions', () => {
      useDiagnosticStore.getState().setQuestions(defaultParams)
      useDiagnosticStore.getState().nextQuestion()
      useDiagnosticStore.getState().nextQuestion()
      // sessionProgress=0, currentIndex=2, sessionTotal=3 => 2/3 = 67%
      expect(useDiagnosticStore.getState().progressPercentage()).toBe(67)
    })

    it('calculates progress correctly for resumed session', () => {
      // Resumed session: 2 already answered out of 10 total
      useDiagnosticStore.getState().setQuestions({
        ...defaultParams,
        sessionProgress: 2,
        sessionTotal: 10,
        isResumed: true,
      })
      // sessionProgress=2, currentIndex=0, sessionTotal=10 => 2/10 = 20%
      expect(useDiagnosticStore.getState().progressPercentage()).toBe(20)

      // Answer one more question
      useDiagnosticStore.getState().nextQuestion()
      // sessionProgress=2, currentIndex=1, sessionTotal=10 => 3/10 = 30%
      expect(useDiagnosticStore.getState().progressPercentage()).toBe(30)
    })
  })

  describe('currentQuestion', () => {
    it('returns null when no questions', () => {
      expect(useDiagnosticStore.getState().currentQuestion()).toBeNull()
    })

    it('returns first question at index 0', () => {
      useDiagnosticStore.getState().setQuestions(defaultParams)
      expect(useDiagnosticStore.getState().currentQuestion()).toEqual(mockQuestions[0])
    })

    it('returns correct question after advancing', () => {
      useDiagnosticStore.getState().setQuestions(defaultParams)
      useDiagnosticStore.getState().nextQuestion()
      expect(useDiagnosticStore.getState().currentQuestion()).toEqual(mockQuestions[1])
    })
  })

  describe('setSubmitting', () => {
    it('sets isSubmitting to true', () => {
      useDiagnosticStore.getState().setSubmitting(true)
      expect(useDiagnosticStore.getState().isSubmitting).toBe(true)
    })

    it('sets isSubmitting to false', () => {
      useDiagnosticStore.getState().setSubmitting(true)
      useDiagnosticStore.getState().setSubmitting(false)
      expect(useDiagnosticStore.getState().isSubmitting).toBe(false)
    })
  })

  describe('completeDiagnostic', () => {
    it('sets isComplete to true', () => {
      useDiagnosticStore.getState().completeDiagnostic()
      expect(useDiagnosticStore.getState().isComplete).toBe(true)
    })
  })

  describe('setSessionStatus (Story 3.9)', () => {
    it('updates sessionStatus', () => {
      useDiagnosticStore.getState().setQuestions(defaultParams)
      useDiagnosticStore.getState().setSessionStatus('completed')
      expect(useDiagnosticStore.getState().sessionStatus).toBe('completed')
    })

    it('can set sessionStatus to expired', () => {
      useDiagnosticStore.getState().setQuestions(defaultParams)
      useDiagnosticStore.getState().setSessionStatus('expired')
      expect(useDiagnosticStore.getState().sessionStatus).toBe('expired')
    })
  })

  describe('resetDiagnostic', () => {
    it('resets all state to initial values', () => {
      useDiagnosticStore.getState().setQuestions(defaultParams)
      useDiagnosticStore.getState().nextQuestion()
      useDiagnosticStore.getState().submitAnswer('q1-uuid', 'A')
      useDiagnosticStore.getState().setSubmitting(true)
      useDiagnosticStore.getState().completeDiagnostic()

      useDiagnosticStore.getState().resetDiagnostic()

      const state = useDiagnosticStore.getState()
      expect(state.questions).toEqual([])
      expect(state.currentIndex).toBe(0)
      expect(state.answers).toEqual([])
      expect(state.startTime).toBeNull()
      expect(state.isSubmitting).toBe(false)
      expect(state.isComplete).toBe(false)
      expect(state.totalConcepts).toBe(0)
      expect(state.coveragePercentage).toBe(0)
      expect(state.sessionProgress).toBe(0)
      expect(state.sessionTotal).toBe(0)
    })

    // Story 3.9: Verify session state is cleared
    it('clears session state', () => {
      useDiagnosticStore.getState().setQuestions({
        ...defaultParams,
        sessionId: 'some-session-id',
        sessionStatus: 'in_progress',
        sessionProgress: 5,
        sessionTotal: 10,
        isResumed: true,
      })

      useDiagnosticStore.getState().resetDiagnostic()

      const state = useDiagnosticStore.getState()
      expect(state.sessionId).toBeNull()
      expect(state.sessionStatus).toBeNull()
      expect(state.isResumed).toBe(false)
      expect(state.sessionProgress).toBe(0)
      expect(state.sessionTotal).toBe(0)
    })
  })
})
