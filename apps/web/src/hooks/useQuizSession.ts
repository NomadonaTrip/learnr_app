import { useCallback, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { quizService, SessionConfig, NextQuestionRequest, AnswerSubmissionRequest } from '../services/quizService'
import { useQuizStore, QuizSessionStatus } from '../stores/quizStore'
import { AxiosError } from 'axios'

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
      // Handle nested error structure: { detail: { error: { message, code } } }
      if (data.detail.error?.message) {
        return data.detail.error.message
      }
      // Handle flat structure: { detail: { message } }
      if (data.detail.message) {
        return data.detail.message
      }
    }
    if (error.response?.status === 400) {
      return 'No active enrollment found. Please complete the diagnostic first.'
    }
    if (error.response?.status === 409) {
      return 'Session has been modified. Please refresh and try again.'
    }
  }
  if (error instanceof Error) {
    return error.message
  }
  return 'An unexpected error occurred'
}

/**
 * Hook for managing quiz session lifecycle.
 * Handles starting, pausing, resuming, and ending quiz sessions.
 *
 * @param config - Optional session configuration (session_type, question_strategy, etc.)
 * @returns Session state and control functions
 */
export function useQuizSession(config?: SessionConfig) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const isInitializedRef = useRef(false)
  const questionStartTimeRef = useRef<number | null>(null)
  const isEndingSessionRef = useRef(false)

  const {
    sessionId,
    sessionType,
    questionStrategy,
    status,
    isResumed,
    totalQuestions,
    correctCount,
    version,
    startedAt,
    endedAt,
    error,
    accuracy,
    currentQuestion,
    questionsRemaining,
    isLoadingQuestion,
    selectedAnswer,
    feedbackResult,
    isSubmitting,
    showFeedback,
    // Story 4.7: Progress tracking
    currentQuestionNumber,
    questionTarget,
    sessionSummary,
    setSession,
    setStatus,
    setPaused,
    setEnded,
    setError,
    clearSession,
    setQuestion,
    setLoadingQuestion,
    setSelectedAnswer,
    clearQuestion,
    setFeedback,
    setSubmitting,
    clearFeedback,
    setSessionSummary,
  } = useQuizStore()

  // Start session mutation
  const startMutation = useMutation({
    mutationFn: (sessionConfig?: SessionConfig) =>
      quizService.startSession(sessionConfig),
    onMutate: () => {
      setStatus('loading')
      setError(null)
    },
    onSuccess: (data) => {
      setSession({
        sessionId: data.session_id,
        sessionType: data.session_type,
        questionStrategy: data.question_strategy,
        status: data.status,
        isResumed: data.is_resumed,
        totalQuestions: data.total_questions,
        correctCount: data.correct_count,
        version: data.version,
        startedAt: data.started_at,
      })
    },
    onError: (error) => {
      setError(getErrorMessage(error))
      setStatus('error')
    },
  })

  // Pause session mutation
  const pauseMutation = useMutation({
    mutationFn: (id: string) => quizService.pauseSession(id),
    onSuccess: (data) => {
      setPaused(data.is_paused)
      // Update version from pause response
      useQuizStore.setState({ version: data.version })
    },
    onError: (error) => {
      setError(getErrorMessage(error))
    },
  })

  // Resume session mutation
  const resumeMutation = useMutation({
    mutationFn: (id: string) => quizService.resumeSession(id),
    onSuccess: (data) => {
      setPaused(data.is_paused)
      // Update version from resume response
      useQuizStore.setState({ version: data.version })
    },
    onError: (error) => {
      setError(getErrorMessage(error))
    },
  })

  // End session mutation
  const endMutation = useMutation({
    mutationFn: ({ id, expectedVersion }: { id: string; expectedVersion: number }) =>
      quizService.endSession(id, expectedVersion),
    onSuccess: (data) => {
      setEnded(data.ended_at, {
        totalQuestions: data.total_questions,
        correctCount: data.correct_count,
      })
      // Invalidate diagnostic results cache so updated belief states are reflected
      queryClient.invalidateQueries({ queryKey: ['diagnostic', 'results'] })
    },
    onError: (error) => {
      setError(getErrorMessage(error))
    },
  })

  // Fetch next question mutation
  const fetchQuestionMutation = useMutation({
    mutationFn: (request: NextQuestionRequest) =>
      quizService.getNextQuestion(request),
    onMutate: () => {
      setLoadingQuestion(true)
    },
    onSuccess: (data) => {
      // Story 4.7: Pass progress data to setQuestion
      setQuestion(
        data.question,
        data.questions_remaining,
        data.current_question_number,
        data.question_target
      )
      // Reset question start time when new question loads
      questionStartTimeRef.current = Date.now()
    },
    onError: async (error) => {
      setLoadingQuestion(false)
      const message = getErrorMessage(error)

      // Check if this is a "no questions available" error
      if (message.includes('No questions available') || message.includes('No eligible questions')) {
        // Prevent race condition - mark that we're ending the session
        if (isEndingSessionRef.current) {
          return // Already handling session end
        }
        isEndingSessionRef.current = true

        // Try to end the session on the backend
        if (sessionId) {
          try {
            // Fetch current session to get the correct version for optimistic locking
            const currentSession = await quizService.getSession(sessionId)
            await quizService.endSession(sessionId, currentSession.version)
          } catch {
            // Ignore errors - session may already be ended
          }
        }

        if (totalQuestions > 0) {
          // Session had questions answered - quiz is complete
          setEnded(new Date().toISOString(), {
            totalQuestions,
            correctCount,
          })
          // Invalidate diagnostic results cache so updated belief states are reflected
          queryClient.invalidateQueries({ queryKey: ['diagnostic', 'results'] })
          navigate('/diagnostic/results')
        } else {
          // Fresh session but no questions available - user has answered all questions recently
          setEnded(new Date().toISOString(), { totalQuestions: 0, correctCount: 0 })
          // Invalidate diagnostic results cache so updated belief states are reflected
          queryClient.invalidateQueries({ queryKey: ['diagnostic', 'results'] })
          // Navigate to results - they'll see their existing progress
          navigate('/diagnostic/results')
        }
      } else {
        setError(message)
      }
    },
  })

  // Submit answer mutation
  const submitAnswerMutation = useMutation({
    mutationFn: ({ request, requestId }: { request: AnswerSubmissionRequest; requestId: string }) =>
      quizService.submitAnswer(request, requestId),
    onMutate: () => {
      setSubmitting(true)
    },
    onSuccess: (data) => {
      setFeedback(data)
      // Update session stats and version from response
      useQuizStore.setState({
        totalQuestions: data.session_stats.questions_answered,
        correctCount: Math.round(data.session_stats.accuracy * data.session_stats.questions_answered),
        version: data.session_stats.session_version,
      })

      // Story 4.7: Handle auto-completion
      if (data.session_completed && data.session_summary) {
        setSessionSummary(data.session_summary)
        setEnded(new Date().toISOString(), {
          totalQuestions: data.session_summary.questions_answered,
          correctCount: data.session_summary.correct_count,
        })
        // Invalidate diagnostic results cache so updated belief states are reflected
        queryClient.invalidateQueries({ queryKey: ['diagnostic', 'results'] })
      }
    },
    onError: (error) => {
      setSubmitting(false)
      const message = getErrorMessage(error)
      setError(message)
    },
  })

  // Start session on mount
  useEffect(() => {
    if (!isInitializedRef.current && status === 'idle') {
      isInitializedRef.current = true
      startMutation.mutate(config)
    }
  }, [config, status, startMutation])

  // Fetch first question when session becomes active
  useEffect(() => {
    if (sessionId && status === 'active' && !currentQuestion && !isLoadingQuestion && !isEndingSessionRef.current) {
      fetchQuestionMutation.mutate({ session_id: sessionId })
    }
  }, [sessionId, status, currentQuestion, isLoadingQuestion, fetchQuestionMutation])

  // Pause session handler
  const pause = useCallback(() => {
    if (sessionId && status === 'active') {
      pauseMutation.mutate(sessionId)
    }
  }, [sessionId, status, pauseMutation])

  // Resume session handler
  const resume = useCallback(() => {
    if (sessionId && status === 'paused') {
      resumeMutation.mutate(sessionId)
    }
  }, [sessionId, status, resumeMutation])

  // End session handler
  const end = useCallback(() => {
    if (sessionId && (status === 'active' || status === 'paused')) {
      endMutation.mutate({ id: sessionId, expectedVersion: version })
    }
  }, [sessionId, status, version, endMutation])

  // Retry starting session after error
  const retry = useCallback(() => {
    isInitializedRef.current = false
    clearSession()
    startMutation.mutate(config)
  }, [config, clearSession, startMutation])

  // Start a new session (after ending current one)
  const startNew = useCallback(() => {
    isInitializedRef.current = false
    clearSession()
    startMutation.mutate(config)
  }, [config, clearSession, startMutation])

  // Return to dashboard
  const returnToDashboard = useCallback(() => {
    clearSession()
    navigate('/diagnostic/results')
  }, [clearSession, navigate])

  // Fetch next question handler
  const fetchNextQuestion = useCallback(() => {
    if (sessionId && status === 'active') {
      clearQuestion()
      fetchQuestionMutation.mutate({ session_id: sessionId })
    }
  }, [sessionId, status, clearQuestion, fetchQuestionMutation])

  // Select answer handler
  const selectAnswer = useCallback((answer: string) => {
    setSelectedAnswer(answer)
  }, [setSelectedAnswer])

  // Submit answer handler
  const submitAnswer = useCallback(() => {
    if (!sessionId || !currentQuestion || !selectedAnswer) {
      return
    }

    const requestId = crypto.randomUUID()
    const request: AnswerSubmissionRequest = {
      session_id: sessionId,
      question_id: currentQuestion.question_id,
      selected_answer: selectedAnswer,
    }

    submitAnswerMutation.mutate({ request, requestId })
  }, [sessionId, currentQuestion, selectedAnswer, submitAnswerMutation])

  // Proceed to next question after feedback
  const proceedToNextQuestion = useCallback(() => {
    clearFeedback()
    if (sessionId && status === 'active') {
      clearQuestion()
      fetchQuestionMutation.mutate({ session_id: sessionId })
    }
  }, [sessionId, status, clearFeedback, clearQuestion, fetchQuestionMutation])

  // Computed loading states
  const isLoading = status === 'loading'
  const isPausing = pauseMutation.isPending
  const isResuming = resumeMutation.isPending
  const isEnding = endMutation.isPending
  const isFetchingQuestion = fetchQuestionMutation.isPending || isLoadingQuestion
  const isActionPending = isPausing || isResuming || isEnding

  return {
    // Session state
    sessionId,
    sessionType,
    questionStrategy,
    status: status as QuizSessionStatus,
    isResumed,
    totalQuestions,
    correctCount,
    version,
    startedAt,
    endedAt,
    error,
    accuracy: accuracy(),

    // Story 4.7: Progress tracking
    currentQuestionNumber,
    questionTarget,
    sessionSummary,

    // Question state
    currentQuestion,
    questionsRemaining,
    selectedAnswer,

    // Feedback state
    feedbackResult,
    isSubmitting,
    showFeedback,

    // Loading states
    isLoading,
    isPausing,
    isResuming,
    isEnding,
    isFetchingQuestion,
    isActionPending,

    // Actions
    pause,
    resume,
    end,
    retry,
    startNew,
    returnToDashboard,
    fetchNextQuestion,
    selectAnswer,
    submitAnswer,
    proceedToNextQuestion,
  }
}
