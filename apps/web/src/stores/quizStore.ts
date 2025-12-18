import { create } from 'zustand'
import type { SessionType, QuestionStrategy, SelectedQuestion, AnswerResponse } from '../services/quizService'

/**
 * Quiz session status.
 */
export type QuizSessionStatus =
  | 'idle'
  | 'loading'
  | 'active'
  | 'paused'
  | 'ended'
  | 'error'

/**
 * Session data for setting the store state.
 */
export interface SessionData {
  sessionId: string
  sessionType: SessionType
  questionStrategy: QuestionStrategy
  status: string
  isResumed: boolean
  totalQuestions: number
  correctCount: number
  version: number
  startedAt: string
}

interface QuizState {
  // Session state
  sessionId: string | null
  sessionType: SessionType | null
  questionStrategy: QuestionStrategy | null
  status: QuizSessionStatus
  isResumed: boolean
  totalQuestions: number
  correctCount: number
  version: number
  startedAt: string | null
  endedAt: string | null
  error: string | null

  // Question state
  currentQuestion: SelectedQuestion | null
  questionsRemaining: number
  isLoadingQuestion: boolean
  selectedAnswer: string | null

  // Feedback state
  feedbackResult: AnswerResponse | null
  isSubmitting: boolean
  showFeedback: boolean

  // Computed: accuracy percentage
  accuracy: () => number | null

  // Actions
  setSession: (session: SessionData) => void
  setStatus: (status: QuizSessionStatus) => void
  setPaused: (isPaused: boolean) => void
  setEnded: (endedAt: string, finalStats?: { totalQuestions: number; correctCount: number }) => void
  setError: (error: string | null) => void
  incrementVersion: () => void
  clearSession: () => void

  // Question actions
  setQuestion: (question: SelectedQuestion, questionsRemaining: number) => void
  setLoadingQuestion: (isLoading: boolean) => void
  setSelectedAnswer: (answer: string | null) => void
  clearQuestion: () => void

  // Feedback actions
  setFeedback: (result: AnswerResponse) => void
  setSubmitting: (isSubmitting: boolean) => void
  clearFeedback: () => void
}

/**
 * Zustand store for quiz session state.
 * Manages the adaptive quiz session including status, statistics, and error state.
 */
export const useQuizStore = create<QuizState>()((set, get) => ({
  // Initial state
  sessionId: null,
  sessionType: null,
  questionStrategy: null,
  status: 'idle',
  isResumed: false,
  totalQuestions: 0,
  correctCount: 0,
  version: 0,
  startedAt: null,
  endedAt: null,
  error: null,

  // Question state
  currentQuestion: null,
  questionsRemaining: 0,
  isLoadingQuestion: false,
  selectedAnswer: null,

  // Feedback state
  feedbackResult: null,
  isSubmitting: false,
  showFeedback: false,

  // Computed: accuracy percentage (null if no questions answered)
  accuracy: () => {
    const { totalQuestions, correctCount } = get()
    if (totalQuestions === 0) return null
    return Math.round((correctCount / totalQuestions) * 100)
  },

  // Action: set session from API response
  setSession: (session) => {
    set({
      sessionId: session.sessionId,
      sessionType: session.sessionType,
      questionStrategy: session.questionStrategy,
      status: session.status === 'paused' ? 'paused' : 'active',
      isResumed: session.isResumed,
      totalQuestions: session.totalQuestions,
      correctCount: session.correctCount,
      version: session.version,
      startedAt: session.startedAt,
      endedAt: null,
      error: null,
    })
  },

  // Action: set session status
  setStatus: (status) => {
    set({ status })
  },

  // Action: set paused state
  setPaused: (isPaused) => {
    set({ status: isPaused ? 'paused' : 'active' })
  },

  // Action: set session as ended
  setEnded: (endedAt, finalStats) => {
    set({
      status: 'ended',
      endedAt,
      ...(finalStats && {
        totalQuestions: finalStats.totalQuestions,
        correctCount: finalStats.correctCount,
      }),
    })
  },

  // Action: set error state
  setError: (error) => {
    set({
      error,
      status: error ? 'error' : get().status,
    })
  },

  // Action: increment version for optimistic locking
  incrementVersion: () => {
    set((state) => ({ version: state.version + 1 }))
  },

  // Action: clear session state
  clearSession: () => {
    set({
      sessionId: null,
      sessionType: null,
      questionStrategy: null,
      status: 'idle',
      isResumed: false,
      totalQuestions: 0,
      correctCount: 0,
      version: 0,
      startedAt: null,
      endedAt: null,
      error: null,
      currentQuestion: null,
      questionsRemaining: 0,
      isLoadingQuestion: false,
      selectedAnswer: null,
      feedbackResult: null,
      isSubmitting: false,
      showFeedback: false,
    })
  },

  // Action: set current question
  setQuestion: (question, questionsRemaining) => {
    set({
      currentQuestion: question,
      questionsRemaining,
      isLoadingQuestion: false,
      selectedAnswer: null,
      feedbackResult: null,
      isSubmitting: false,
      showFeedback: false,
    })
  },

  // Action: set loading question state
  setLoadingQuestion: (isLoading) => {
    set({ isLoadingQuestion: isLoading })
  },

  // Action: set selected answer
  setSelectedAnswer: (answer) => {
    set({ selectedAnswer: answer })
  },

  // Action: clear current question
  clearQuestion: () => {
    set({
      currentQuestion: null,
      selectedAnswer: null,
    })
  },

  // Action: set feedback result after answer submission
  setFeedback: (result) => {
    set({
      feedbackResult: result,
      isSubmitting: false,
      showFeedback: true,
    })
  },

  // Action: set submitting state
  setSubmitting: (isSubmitting) => {
    set({ isSubmitting })
  },

  // Action: clear feedback and prepare for next question
  clearFeedback: () => {
    set({
      feedbackResult: null,
      showFeedback: false,
      selectedAnswer: null,
    })
  },
}))
