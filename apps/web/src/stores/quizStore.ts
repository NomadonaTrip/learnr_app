import { create } from 'zustand'
import type {
  SessionType,
  QuestionStrategy,
  SelectedQuestion,
  AnswerResponse,
  SessionSummary,
  TargetProgress,
} from '../services/quizService'

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
 * Focus context for focused sessions.
 * Story 4.8: Focused Practice Mode.
 */
export interface FocusContext {
  focusType: 'ka' | 'concept'
  focusTargetId: string
  focusTargetName?: string
}

/**
 * Session data for setting the store state.
 */
export interface SessionData {
  sessionId: string
  sessionType: SessionType
  questionStrategy: QuestionStrategy
  questionTarget: number
  status: string
  isResumed: boolean
  totalQuestions: number
  correctCount: number
  version: number
  startedAt: string
  // Story 4.8: Focus context for focused sessions
  focusContext?: FocusContext | null
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

  // Story 4.7: Progress tracking state
  currentQuestionNumber: number
  questionTarget: number

  // Story 4.8: Focus context for focused sessions
  focusContext: FocusContext | null
  targetProgress: TargetProgress | null

  // Question state
  currentQuestion: SelectedQuestion | null
  questionsRemaining: number
  isLoadingQuestion: boolean
  selectedAnswer: string | null

  // Feedback state
  feedbackResult: AnswerResponse | null
  isSubmitting: boolean
  showFeedback: boolean

  // Story 4.7: Session summary state
  sessionSummary: SessionSummary | null

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
  setQuestion: (question: SelectedQuestion, questionsRemaining: number, currentQuestionNumber?: number, questionTarget?: number) => void
  setLoadingQuestion: (isLoading: boolean) => void
  setSelectedAnswer: (answer: string | null) => void
  clearQuestion: () => void

  // Story 4.7: Progress actions
  setProgress: (currentQuestionNumber: number, questionTarget: number) => void
  setSessionSummary: (summary: SessionSummary | null) => void

  // Story 4.8: Focus actions
  setFocusContext: (context: FocusContext | null) => void
  setTargetProgress: (progress: TargetProgress | null) => void

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

  // Story 4.7: Progress tracking state
  currentQuestionNumber: 1,
  questionTarget: 10,

  // Story 4.8: Focus context for focused sessions
  focusContext: null,
  targetProgress: null,

  // Question state
  currentQuestion: null,
  questionsRemaining: 0,
  isLoadingQuestion: false,
  selectedAnswer: null,

  // Feedback state
  feedbackResult: null,
  isSubmitting: false,
  showFeedback: false,

  // Story 4.7: Session summary state
  sessionSummary: null,

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
      questionTarget: session.questionTarget,
      status: session.status === 'paused' ? 'paused' : 'active',
      isResumed: session.isResumed,
      totalQuestions: session.totalQuestions,
      correctCount: session.correctCount,
      version: session.version,
      startedAt: session.startedAt,
      endedAt: null,
      error: null,
      // Story 4.8: Set focus context if provided
      focusContext: session.focusContext || null,
      // Reset target progress when starting new session
      targetProgress: null,
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
      // Story 4.7: Reset progress tracking
      currentQuestionNumber: 1,
      questionTarget: 10,
      currentQuestion: null,
      questionsRemaining: 0,
      isLoadingQuestion: false,
      selectedAnswer: null,
      feedbackResult: null,
      isSubmitting: false,
      showFeedback: false,
      // Story 4.7: Reset session summary
      sessionSummary: null,
      // Story 4.8: Reset focus context and target progress
      focusContext: null,
      targetProgress: null,
    })
  },

  // Action: set current question (Story 4.7: added progress parameters)
  setQuestion: (question, questionsRemaining, currentQuestionNumber, questionTarget) => {
    set({
      currentQuestion: question,
      questionsRemaining,
      isLoadingQuestion: false,
      selectedAnswer: null,
      feedbackResult: null,
      isSubmitting: false,
      showFeedback: false,
      // Story 4.7: Update progress if provided
      ...(currentQuestionNumber !== undefined && { currentQuestionNumber }),
      ...(questionTarget !== undefined && { questionTarget }),
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

  // Story 4.7: Action to set progress
  setProgress: (currentQuestionNumber, questionTarget) => {
    set({ currentQuestionNumber, questionTarget })
  },

  // Story 4.7: Action to set session summary
  setSessionSummary: (summary) => {
    set({ sessionSummary: summary })
  },

  // Story 4.8: Action to set focus context
  setFocusContext: (context) => {
    set({ focusContext: context })
  },

  // Story 4.8: Action to set target progress
  setTargetProgress: (progress) => {
    set({ targetProgress: progress })
  },
}))
