import { useCallback, useEffect, useRef } from 'react'
import { useMutation } from '@tanstack/react-query'
import { AxiosError } from 'axios'
import { reviewService, ReviewAnswerRequest } from '../services/reviewService'
import { useReviewStore, ReviewSessionStatus } from '../stores/reviewStore'

/**
 * API error response structure.
 */
interface ApiErrorResponse {
  detail?: string | { message?: string; error?: { message?: string; code?: string } }
}

/**
 * Extract error message from API error.
 */
function getErrorMessage(error: unknown): string {
  if (error instanceof AxiosError) {
    const data = error.response?.data as ApiErrorResponse | undefined
    if (typeof data?.detail === 'string') {
      return data.detail
    }
    if (typeof data?.detail === 'object') {
      if (data.detail.error?.message) {
        return data.detail.error.message
      }
      if (data.detail.message) {
        return data.detail.message
      }
    }
    if (error.response?.status === 404) {
      return 'Review session not found'
    }
    if (error.response?.status === 409) {
      return 'Question already reviewed'
    }
  }
  if (error instanceof Error) {
    return error.message
  }
  return 'An unexpected error occurred'
}

/**
 * Options for useReview hook.
 * Story 4.9: Post-Session Review Mode
 */
interface UseReviewOptions {
  /** Original quiz session ID to check for review availability */
  originalSessionId?: string
  /** Skip auto-checking review availability on mount */
  skipAutoCheck?: boolean
}

/**
 * Hook for managing review session lifecycle.
 * Story 4.9: Post-Session Review Mode
 *
 * @param options - Optional configuration
 * @returns Review state and control functions
 */
export function useReview(options?: UseReviewOptions) {
  const { originalSessionId, skipAutoCheck = false } = options || {}
  const hasCheckedRef = useRef(false)

  const {
    reviewSessionId,
    originalSessionId: storeOriginalSessionId,
    status,
    totalToReview,
    reviewedCount,
    reinforcedCount,
    stillIncorrectCount,
    error,
    currentQuestion,
    selectedAnswer,
    isLoadingQuestion,
    feedbackResult,
    isSubmitting,
    showFeedback,
    summary,
    reinforcementRate,
    setReviewAvailable,
    setSession,
    setStatus,
    setError,
    clearSession,
    updateProgress,
    setQuestion,
    setLoadingQuestion,
    setSelectedAnswer,
    setFeedback,
    setSubmitting,
    clearFeedback,
    setSummary,
  } = useReviewStore()

  // Check review availability mutation
  const checkAvailabilityMutation = useMutation({
    mutationFn: (sessionId: string) => reviewService.checkReviewAvailable(sessionId),
    onSuccess: (data, sessionId) => {
      if (data.available && data.incorrect_count > 0) {
        setReviewAvailable(sessionId, data.incorrect_count)
      } else {
        setStatus('idle')
      }
    },
    onError: (error) => {
      setError(getErrorMessage(error))
    },
  })

  // Start review mutation
  const startReviewMutation = useMutation({
    mutationFn: (sessionId: string) => reviewService.startReview(sessionId),
    onMutate: () => {
      setStatus('loading')
    },
    onSuccess: (data) => {
      setSession({
        reviewSessionId: data.id,
        originalSessionId: data.original_session_id,
        totalToReview: data.total_to_review,
        reviewedCount: data.reviewed_count,
        reinforcedCount: data.reinforced_count,
        stillIncorrectCount: data.still_incorrect_count,
      })
    },
    onError: (error) => {
      setError(getErrorMessage(error))
      setStatus('error')
    },
  })

  // Fetch next question mutation
  const fetchQuestionMutation = useMutation({
    mutationFn: (reviewSessionId: string) => reviewService.getNextReviewQuestion(reviewSessionId),
    onMutate: () => {
      setLoadingQuestion(true)
    },
    onSuccess: (data) => {
      if (data === null) {
        // All questions reviewed, fetch summary
        if (reviewSessionId) {
          fetchSummaryMutation.mutate(reviewSessionId)
        }
      } else {
        setQuestion(data)
      }
    },
    onError: (error) => {
      setLoadingQuestion(false)
      setError(getErrorMessage(error))
    },
  })

  // Submit answer mutation
  const submitAnswerMutation = useMutation({
    mutationFn: ({ reviewSessionId, request }: { reviewSessionId: string; request: ReviewAnswerRequest }) =>
      reviewService.submitReviewAnswer(reviewSessionId, request),
    onMutate: () => {
      setSubmitting(true)
    },
    onSuccess: (data) => {
      setFeedback(data)
      // Update progress counts based on response
      const newReviewedCount = reviewedCount + 1
      const newReinforcedCount = data.was_reinforced ? reinforcedCount + 1 : reinforcedCount
      const newStillIncorrectCount = !data.is_correct ? stillIncorrectCount + 1 : stillIncorrectCount
      updateProgress(newReviewedCount, newReinforcedCount, newStillIncorrectCount)
    },
    onError: (error) => {
      setSubmitting(false)
      setError(getErrorMessage(error))
    },
  })

  // Skip review mutation
  const skipReviewMutation = useMutation({
    mutationFn: (reviewSessionId: string) => reviewService.skipReview(reviewSessionId),
    onSuccess: () => {
      setStatus('skipped')
    },
    onError: (error) => {
      setError(getErrorMessage(error))
    },
  })

  // Fetch summary mutation
  const fetchSummaryMutation = useMutation({
    mutationFn: (reviewSessionId: string) => reviewService.getReviewSummary(reviewSessionId),
    onSuccess: (data) => {
      setSummary(data)
    },
    onError: (error) => {
      setError(getErrorMessage(error))
    },
  })

  // Auto-check review availability on mount
  useEffect(() => {
    if (!skipAutoCheck && originalSessionId && !hasCheckedRef.current && status === 'idle') {
      hasCheckedRef.current = true
      checkAvailabilityMutation.mutate(originalSessionId)
    }
  }, [originalSessionId, skipAutoCheck, status, checkAvailabilityMutation])

  // Fetch first question when session becomes active
  useEffect(() => {
    if (reviewSessionId && status === 'active' && !currentQuestion && !isLoadingQuestion) {
      fetchQuestionMutation.mutate(reviewSessionId)
    }
  }, [reviewSessionId, status, currentQuestion, isLoadingQuestion, fetchQuestionMutation])

  // Check review availability handler
  const checkAvailability = useCallback(
    (sessionId: string) => {
      hasCheckedRef.current = true
      checkAvailabilityMutation.mutate(sessionId)
    },
    [checkAvailabilityMutation]
  )

  // Start review handler
  const startReview = useCallback(() => {
    const sessionIdToUse = storeOriginalSessionId || originalSessionId
    if (sessionIdToUse) {
      startReviewMutation.mutate(sessionIdToUse)
    }
  }, [storeOriginalSessionId, originalSessionId, startReviewMutation])

  // Skip review handler
  const skipReview = useCallback(() => {
    if (reviewSessionId) {
      skipReviewMutation.mutate(reviewSessionId)
    } else {
      // No review session started yet, just clear
      clearSession()
    }
  }, [reviewSessionId, skipReviewMutation, clearSession])

  // Select answer handler
  const selectAnswer = useCallback(
    (answer: string) => {
      setSelectedAnswer(answer)
    },
    [setSelectedAnswer]
  )

  // Submit answer handler
  const submitAnswer = useCallback(() => {
    if (!reviewSessionId || !currentQuestion || !selectedAnswer) {
      return
    }

    const request: ReviewAnswerRequest = {
      question_id: currentQuestion.question_id,
      selected_answer: selectedAnswer,
    }

    submitAnswerMutation.mutate({ reviewSessionId, request })
  }, [reviewSessionId, currentQuestion, selectedAnswer, submitAnswerMutation])

  // Proceed to next question handler
  const proceedToNextQuestion = useCallback(() => {
    clearFeedback()
    if (reviewSessionId) {
      setQuestion(null)
      fetchQuestionMutation.mutate(reviewSessionId)
    }
  }, [reviewSessionId, clearFeedback, setQuestion, fetchQuestionMutation])

  // Dismiss review (return to dashboard without starting)
  const dismissReview = useCallback(() => {
    clearSession()
  }, [clearSession])

  // Computed loading states
  const isLoading = status === 'loading'
  const isCheckingAvailability = checkAvailabilityMutation.isPending
  const isStartingReview = startReviewMutation.isPending
  const isFetchingQuestion = fetchQuestionMutation.isPending || isLoadingQuestion
  const isSkipping = skipReviewMutation.isPending
  const isFetchingSummary = fetchSummaryMutation.isPending

  return {
    // Session state
    reviewSessionId,
    originalSessionId: storeOriginalSessionId || originalSessionId,
    status: status as ReviewSessionStatus,
    totalToReview,
    reviewedCount,
    reinforcedCount,
    stillIncorrectCount,
    error,

    // Question state
    currentQuestion,
    selectedAnswer,

    // Feedback state
    feedbackResult,
    isSubmitting,
    showFeedback,

    // Summary state
    summary,

    // Computed
    reinforcementRate: reinforcementRate(),

    // Loading states
    isLoading,
    isCheckingAvailability,
    isStartingReview,
    isFetchingQuestion,
    isSkipping,
    isFetchingSummary,

    // Actions
    checkAvailability,
    startReview,
    skipReview,
    selectAnswer,
    submitAnswer,
    proceedToNextQuestion,
    dismissReview,
    clearSession,
  }
}
