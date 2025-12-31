import { create } from 'zustand'
import type {
  ReviewQuestionResponse,
  ReviewAnswerResponse,
  ReviewSummaryResponse,
} from '../services/reviewService'

/**
 * Review session status.
 * Story 4.9: Post-Session Review Mode
 */
export type ReviewSessionStatus =
  | 'idle'
  | 'prompt'
  | 'loading'
  | 'active'
  | 'completed'
  | 'skipped'
  | 'error'

/**
 * Review session data.
 * Story 4.9: Post-Session Review Mode
 */
export interface ReviewSessionData {
  reviewSessionId: string
  originalSessionId: string
  totalToReview: number
  reviewedCount: number
  reinforcedCount: number
  stillIncorrectCount: number
}

interface ReviewState {
  // Session state
  reviewSessionId: string | null
  originalSessionId: string | null
  status: ReviewSessionStatus
  totalToReview: number
  reviewedCount: number
  reinforcedCount: number
  stillIncorrectCount: number
  error: string | null

  // Question state
  currentQuestion: ReviewQuestionResponse | null
  selectedAnswer: string | null
  isLoadingQuestion: boolean

  // Feedback state
  feedbackResult: ReviewAnswerResponse | null
  isSubmitting: boolean
  showFeedback: boolean

  // Summary state
  summary: ReviewSummaryResponse | null

  // Computed: reinforcement rate
  reinforcementRate: () => number

  // Actions
  setReviewAvailable: (originalSessionId: string, incorrectCount: number) => void
  setSession: (session: ReviewSessionData) => void
  setStatus: (status: ReviewSessionStatus) => void
  setError: (error: string | null) => void
  clearSession: () => void
  updateProgress: (reviewedCount: number, reinforcedCount: number, stillIncorrectCount: number) => void

  // Question actions
  setQuestion: (question: ReviewQuestionResponse | null) => void
  setLoadingQuestion: (isLoading: boolean) => void
  setSelectedAnswer: (answer: string | null) => void

  // Feedback actions
  setFeedback: (result: ReviewAnswerResponse) => void
  setSubmitting: (isSubmitting: boolean) => void
  clearFeedback: () => void

  // Summary actions
  setSummary: (summary: ReviewSummaryResponse) => void
}

/**
 * Zustand store for review session state.
 * Story 4.9: Post-Session Review Mode
 */
export const useReviewStore = create<ReviewState>()((set, get) => ({
  // Initial state
  reviewSessionId: null,
  originalSessionId: null,
  status: 'idle',
  totalToReview: 0,
  reviewedCount: 0,
  reinforcedCount: 0,
  stillIncorrectCount: 0,
  error: null,

  // Question state
  currentQuestion: null,
  selectedAnswer: null,
  isLoadingQuestion: false,

  // Feedback state
  feedbackResult: null,
  isSubmitting: false,
  showFeedback: false,

  // Summary state
  summary: null,

  // Computed: reinforcement rate
  reinforcementRate: () => {
    const { reviewedCount, reinforcedCount } = get()
    if (reviewedCount === 0) return 0
    return reinforcedCount / reviewedCount
  },

  // Action: set review available state (prompt to start review)
  setReviewAvailable: (originalSessionId, incorrectCount) => {
    set({
      originalSessionId,
      totalToReview: incorrectCount,
      status: 'prompt',
    })
  },

  // Action: set session from API response
  setSession: (session) => {
    set({
      reviewSessionId: session.reviewSessionId,
      originalSessionId: session.originalSessionId,
      status: 'active',
      totalToReview: session.totalToReview,
      reviewedCount: session.reviewedCount,
      reinforcedCount: session.reinforcedCount,
      stillIncorrectCount: session.stillIncorrectCount,
      error: null,
    })
  },

  // Action: set session status
  setStatus: (status) => {
    set({ status })
  },

  // Action: set error state
  setError: (error) => {
    set({
      error,
      status: error ? 'error' : get().status,
    })
  },

  // Action: clear session state
  clearSession: () => {
    set({
      reviewSessionId: null,
      originalSessionId: null,
      status: 'idle',
      totalToReview: 0,
      reviewedCount: 0,
      reinforcedCount: 0,
      stillIncorrectCount: 0,
      error: null,
      currentQuestion: null,
      selectedAnswer: null,
      isLoadingQuestion: false,
      feedbackResult: null,
      isSubmitting: false,
      showFeedback: false,
      summary: null,
    })
  },

  // Action: update progress
  updateProgress: (reviewedCount, reinforcedCount, stillIncorrectCount) => {
    set({ reviewedCount, reinforcedCount, stillIncorrectCount })
  },

  // Action: set current question
  setQuestion: (question) => {
    set({
      currentQuestion: question,
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

  // Action: set summary
  setSummary: (summary) => {
    set({
      summary,
      status: 'completed',
    })
  },
}))
