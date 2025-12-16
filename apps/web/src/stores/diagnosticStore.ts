import { create } from 'zustand'
import type { DiagnosticQuestion, DiagnosticAnswer, AnswerLetter } from '../types/diagnostic'

interface DiagnosticState {
  // State
  questions: DiagnosticQuestion[]
  currentIndex: number
  answers: DiagnosticAnswer[]
  startTime: Date | null
  isSubmitting: boolean
  isComplete: boolean
  totalConcepts: number
  coveragePercentage: number

  // Computed
  progressPercentage: () => number
  currentQuestion: () => DiagnosticQuestion | null

  // Actions
  setQuestions: (questions: DiagnosticQuestion[], totalConcepts: number, coveragePercentage: number) => void
  submitAnswer: (questionId: string, answer: AnswerLetter) => void
  nextQuestion: () => void
  resetDiagnostic: () => void
  setSubmitting: (isSubmitting: boolean) => void
  completeDiagnostic: () => void
}

/**
 * Zustand store for diagnostic assessment state.
 * Manages the diagnostic session including questions, answers, and progress.
 */
export const useDiagnosticStore = create<DiagnosticState>()((set, get) => ({
  // Initial state
  questions: [],
  currentIndex: 0,
  answers: [],
  startTime: null,
  isSubmitting: false,
  isComplete: false,
  totalConcepts: 0,
  coveragePercentage: 0,

  // Computed: progress percentage (0-100)
  progressPercentage: () => {
    const { questions, currentIndex } = get()
    if (questions.length === 0) return 0
    return Math.round((currentIndex / questions.length) * 100)
  },

  // Computed: current question
  currentQuestion: () => {
    const { questions, currentIndex } = get()
    return questions[currentIndex] ?? null
  },

  // Action: set questions from API
  setQuestions: (questions, totalConcepts, coveragePercentage) => {
    set({
      questions,
      totalConcepts,
      coveragePercentage,
      currentIndex: 0,
      answers: [],
      startTime: new Date(),
      isComplete: false,
      isSubmitting: false,
    })
  },

  // Action: submit answer for current question
  submitAnswer: (questionId, answer) => {
    const { answers } = get()
    const newAnswer: DiagnosticAnswer = {
      questionId,
      selectedAnswer: answer,
      submittedAt: new Date(),
    }
    set({
      answers: [...answers, newAnswer],
    })
  },

  // Action: advance to next question
  nextQuestion: () => {
    const { currentIndex, questions } = get()
    if (currentIndex < questions.length - 1) {
      set({ currentIndex: currentIndex + 1 })
    }
  },

  // Action: reset diagnostic state
  resetDiagnostic: () => {
    set({
      questions: [],
      currentIndex: 0,
      answers: [],
      startTime: null,
      isSubmitting: false,
      isComplete: false,
      totalConcepts: 0,
      coveragePercentage: 0,
    })
  },

  // Action: set submitting state
  setSubmitting: (isSubmitting) => {
    set({ isSubmitting })
  },

  // Action: mark diagnostic as complete
  completeDiagnostic: () => {
    set({ isComplete: true })
  },
}))
