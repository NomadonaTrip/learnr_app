import { describe, it, expect, beforeEach } from 'vitest'
import { useDiagnosticStore } from '../../stores/diagnosticStore'
import type { DiagnosticQuestion } from '../../types/diagnostic'

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
  })

  describe('setQuestions', () => {
    it('sets questions array', () => {
      useDiagnosticStore.getState().setQuestions(mockQuestions, 487, 0.405)
      expect(useDiagnosticStore.getState().questions).toEqual(mockQuestions)
    })

    it('sets totalConcepts', () => {
      useDiagnosticStore.getState().setQuestions(mockQuestions, 487, 0.405)
      expect(useDiagnosticStore.getState().totalConcepts).toBe(487)
    })

    it('sets coveragePercentage', () => {
      useDiagnosticStore.getState().setQuestions(mockQuestions, 487, 0.405)
      expect(useDiagnosticStore.getState().coveragePercentage).toBe(0.405)
    })

    it('sets startTime to current date', () => {
      const before = new Date()
      useDiagnosticStore.getState().setQuestions(mockQuestions, 487, 0.405)
      const after = new Date()

      const startTime = useDiagnosticStore.getState().startTime
      expect(startTime).not.toBeNull()
      expect(startTime!.getTime()).toBeGreaterThanOrEqual(before.getTime())
      expect(startTime!.getTime()).toBeLessThanOrEqual(after.getTime())
    })

    it('resets currentIndex to 0', () => {
      useDiagnosticStore.getState().setQuestions(mockQuestions, 487, 0.405)
      useDiagnosticStore.getState().nextQuestion()
      useDiagnosticStore.getState().setQuestions(mockQuestions, 487, 0.405)
      expect(useDiagnosticStore.getState().currentIndex).toBe(0)
    })

    it('resets answers to empty', () => {
      useDiagnosticStore.getState().setQuestions(mockQuestions, 487, 0.405)
      useDiagnosticStore.getState().submitAnswer('q1-uuid', 'A')
      useDiagnosticStore.getState().setQuestions(mockQuestions, 487, 0.405)
      expect(useDiagnosticStore.getState().answers).toEqual([])
    })
  })

  describe('submitAnswer', () => {
    it('adds answer to answers array', () => {
      useDiagnosticStore.getState().setQuestions(mockQuestions, 487, 0.405)
      useDiagnosticStore.getState().submitAnswer('q1-uuid', 'B')

      const answers = useDiagnosticStore.getState().answers
      expect(answers).toHaveLength(1)
      expect(answers[0].questionId).toBe('q1-uuid')
      expect(answers[0].selectedAnswer).toBe('B')
    })

    it('records submittedAt timestamp', () => {
      const before = new Date()
      useDiagnosticStore.getState().setQuestions(mockQuestions, 487, 0.405)
      useDiagnosticStore.getState().submitAnswer('q1-uuid', 'A')
      const after = new Date()

      const answers = useDiagnosticStore.getState().answers
      expect(answers[0].submittedAt.getTime()).toBeGreaterThanOrEqual(before.getTime())
      expect(answers[0].submittedAt.getTime()).toBeLessThanOrEqual(after.getTime())
    })

    it('accumulates multiple answers', () => {
      useDiagnosticStore.getState().setQuestions(mockQuestions, 487, 0.405)
      useDiagnosticStore.getState().submitAnswer('q1-uuid', 'A')
      useDiagnosticStore.getState().submitAnswer('q2-uuid', 'C')

      const answers = useDiagnosticStore.getState().answers
      expect(answers).toHaveLength(2)
    })
  })

  describe('nextQuestion', () => {
    it('increments currentIndex', () => {
      useDiagnosticStore.getState().setQuestions(mockQuestions, 487, 0.405)
      useDiagnosticStore.getState().nextQuestion()
      expect(useDiagnosticStore.getState().currentIndex).toBe(1)
    })

    it('does not go past last question', () => {
      useDiagnosticStore.getState().setQuestions(mockQuestions, 487, 0.405)
      useDiagnosticStore.getState().nextQuestion() // 1
      useDiagnosticStore.getState().nextQuestion() // 2
      useDiagnosticStore.getState().nextQuestion() // should stay at 2
      expect(useDiagnosticStore.getState().currentIndex).toBe(2)
    })
  })

  describe('progressPercentage', () => {
    it('returns 0 when no questions', () => {
      expect(useDiagnosticStore.getState().progressPercentage()).toBe(0)
    })

    it('returns 0 for first question', () => {
      useDiagnosticStore.getState().setQuestions(mockQuestions, 487, 0.405)
      expect(useDiagnosticStore.getState().progressPercentage()).toBe(0)
    })

    it('returns 33 for second of three questions', () => {
      useDiagnosticStore.getState().setQuestions(mockQuestions, 487, 0.405)
      useDiagnosticStore.getState().nextQuestion()
      expect(useDiagnosticStore.getState().progressPercentage()).toBe(33)
    })

    it('returns 67 for third of three questions', () => {
      useDiagnosticStore.getState().setQuestions(mockQuestions, 487, 0.405)
      useDiagnosticStore.getState().nextQuestion()
      useDiagnosticStore.getState().nextQuestion()
      expect(useDiagnosticStore.getState().progressPercentage()).toBe(67)
    })
  })

  describe('currentQuestion', () => {
    it('returns null when no questions', () => {
      expect(useDiagnosticStore.getState().currentQuestion()).toBeNull()
    })

    it('returns first question at index 0', () => {
      useDiagnosticStore.getState().setQuestions(mockQuestions, 487, 0.405)
      expect(useDiagnosticStore.getState().currentQuestion()).toEqual(mockQuestions[0])
    })

    it('returns correct question after advancing', () => {
      useDiagnosticStore.getState().setQuestions(mockQuestions, 487, 0.405)
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

  describe('resetDiagnostic', () => {
    it('resets all state to initial values', () => {
      useDiagnosticStore.getState().setQuestions(mockQuestions, 487, 0.405)
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
    })
  })
})
