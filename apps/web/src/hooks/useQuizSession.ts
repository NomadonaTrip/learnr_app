import { useCallback, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { quizService, SessionConfig, NextQuestionRequest } from '../services/quizService'
import { useQuizStore, QuizSessionStatus } from '../stores/quizStore'
import { AxiosError } from 'axios'

/**
 * API error response structure.
 */
interface ApiErrorResponse {
  detail?: string | { message?: string }
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
    if (typeof data?.detail === 'object' && data.detail?.message) {
      return data.detail.message
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
  const isInitializedRef = useRef(false)

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
        version: 1, // Initial version
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
      setQuestion(data.question, data.questions_remaining)
    },
    onError: (error) => {
      setLoadingQuestion(false)
      // Don't set error for "no questions" - this might mean quiz is complete
      const message = getErrorMessage(error)
      if (!message.includes('No questions available')) {
        setError(message)
      }
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
    if (sessionId && status === 'active' && !currentQuestion && !isLoadingQuestion) {
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

    // Question state
    currentQuestion,
    questionsRemaining,
    selectedAnswer,

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
  }
}
