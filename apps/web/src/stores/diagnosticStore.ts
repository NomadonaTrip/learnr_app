import { create } from 'zustand'
import type {
  DiagnosticQuestion,
  DiagnosticAnswer,
  AnswerLetter,
  DiagnosticSessionStatus,
} from '../types/diagnostic'

/** Parameters for setQuestions action (Story 3.9) */
interface SetQuestionsParams {
  questions: DiagnosticQuestion[]
  totalConcepts: number
  coveragePercentage: number
  sessionId: string
  sessionStatus: DiagnosticSessionStatus
  /** Absolute progress in session (questions already answered) */
  sessionProgress: number
  /** Total questions in the session */
  sessionTotal: number
  isResumed: boolean
}

interface DiagnosticState {
  // State
  questions: DiagnosticQuestion[]
  /** Index into the questions array (always 0-based for remaining questions) */
  currentIndex: number
  answers: DiagnosticAnswer[]
  startTime: Date | null
  isSubmitting: boolean
  isComplete: boolean
  totalConcepts: number
  coveragePercentage: number
  // Session state (Story 3.9)
  sessionId: string | null
  sessionStatus: DiagnosticSessionStatus | null
  isResumed: boolean
  /** Absolute progress - questions already answered in session */
  sessionProgress: number
  /** Total questions in the session */
  sessionTotal: number

  // Computed
  progressPercentage: () => number
  currentQuestion: () => DiagnosticQuestion | null

  // Actions
  setQuestions: (params: SetQuestionsParams) => void
  submitAnswer: (questionId: string, answer: AnswerLetter) => void
  nextQuestion: () => void
  resetDiagnostic: () => void
  setSubmitting: (isSubmitting: boolean) => void
  completeDiagnostic: () => void
  setSessionStatus: (status: DiagnosticSessionStatus) => void
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
  // Session state (Story 3.9)
  sessionId: null,
  sessionStatus: null,
  isResumed: false,
  sessionProgress: 0,
  sessionTotal: 0,

  // Computed: progress percentage (0-100) based on absolute session progress
  progressPercentage: () => {
    const { sessionProgress, currentIndex, sessionTotal } = get()
    if (sessionTotal === 0) return 0
    // Total answered = questions answered before + current local progress
    const totalAnswered = sessionProgress + currentIndex
    return Math.round((totalAnswered / sessionTotal) * 100)
  },

  // Computed: current question
  currentQuestion: () => {
    const { questions, currentIndex } = get()
    return questions[currentIndex] ?? null
  },

  // Action: set questions from API (updated for Story 3.9 session support)
  setQuestions: (params) => {
    const {
      questions,
      totalConcepts,
      coveragePercentage,
      sessionId,
      sessionStatus,
      sessionProgress,
      sessionTotal,
      isResumed,
    } = params
    set({
      questions,
      totalConcepts,
      coveragePercentage,
      // Always start at index 0 of the questions array (which contains remaining questions)
      currentIndex: 0,
      answers: [],
      startTime: new Date(),
      isComplete: false,
      isSubmitting: false,
      // Session state (Story 3.9)
      sessionId,
      sessionStatus,
      isResumed,
      // Track absolute progress separately from array index
      sessionProgress,
      sessionTotal,
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

  // Action: reset diagnostic state (updated for Story 3.9 session support)
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
      // Clear session state (Story 3.9)
      sessionId: null,
      sessionStatus: null,
      isResumed: false,
      sessionProgress: 0,
      sessionTotal: 0,
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

  // Action: update session status from answer response (Story 3.9)
  setSessionStatus: (status) => {
    set({ sessionStatus: status })
  },
}))
