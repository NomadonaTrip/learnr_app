import { useCallback, useMemo, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { diagnosticService } from '../services/diagnosticService'
import { courseService } from '../services/courseService'
import { useDiagnosticStore } from '../stores/diagnosticStore'
import type { AnswerLetter } from '../types/diagnostic'

/** Storage key for onboarding data */
const ONBOARDING_STORAGE_KEY = 'learnr_onboarding'

/** Default course slug if none selected (must match backend database) */
const DEFAULT_COURSE_SLUG = 'cbap'

/**
 * Get the selected course slug from sessionStorage.
 */
function getSelectedCourseSlug(): string {
  try {
    const stored = sessionStorage.getItem(ONBOARDING_STORAGE_KEY)
    if (stored) {
      const data = JSON.parse(stored)
      return data.course || DEFAULT_COURSE_SLUG
    }
  } catch {
    // Ignore parse errors
  }
  return DEFAULT_COURSE_SLUG
}

/**
 * Hook for managing diagnostic assessment flow.
 * Wraps diagnosticService calls with React Query and handles state updates.
 */
export function useDiagnostic() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const {
    questions,
    currentIndex,
    answers,
    startTime,
    isSubmitting,
    isComplete,
    totalConcepts,
    coveragePercentage,
    progressPercentage,
    currentQuestion,
    setQuestions,
    submitAnswer,
    nextQuestion,
    resetDiagnostic,
    setSubmitting,
    completeDiagnostic,
  } = useDiagnosticStore()

  // Track if questions have been initialized to prevent re-fetching
  const isInitializedRef = useRef(questions.length > 0)

  // Get course slug from onboarding selection
  const courseSlug = useMemo(() => getSelectedCourseSlug(), [])

  // Fetch course details to get UUID
  const courseQuery = useQuery({
    queryKey: ['course', courseSlug],
    queryFn: () => courseService.fetchCourseBySlug(courseSlug),
    enabled: !isInitializedRef.current && !isComplete,
    staleTime: Infinity,
    retry: 2,
  })

  // Fetch diagnostic questions (depends on course UUID)
  const questionsQuery = useQuery({
    queryKey: ['diagnostic', 'questions', courseQuery.data?.id],
    queryFn: () => diagnosticService.fetchDiagnosticQuestions(courseQuery.data!.id),
    enabled: !!courseQuery.data?.id && !isInitializedRef.current && !isComplete,
    staleTime: Infinity, // Don't refetch once loaded
    retry: 2,
  })

  // Initialize store when questions are fetched
  useEffect(() => {
    if (questionsQuery.data && !isInitializedRef.current) {
      isInitializedRef.current = true
      setQuestions(
        questionsQuery.data.questions,
        questionsQuery.data.concepts_covered,
        questionsQuery.data.coverage_percentage
      )
    }
  }, [questionsQuery.data, setQuestions])

  // Submit answer mutation
  const answerMutation = useMutation({
    mutationFn: ({ questionId, answer }: { questionId: string; answer: AnswerLetter }) =>
      diagnosticService.submitDiagnosticAnswer(questionId, answer),
    onMutate: () => {
      setSubmitting(true)
    },
    onSuccess: (_data, { questionId, answer }) => {
      // Record answer in store
      submitAnswer(questionId, answer)

      // Check if this was the last question
      const isLastQuestion = currentIndex >= questions.length - 1

      if (isLastQuestion) {
        // Complete diagnostic and redirect to results
        completeDiagnostic()
        navigate('/diagnostic/results')
      } else {
        // Auto-advance to next question
        nextQuestion()
      }
    },
    onSettled: () => {
      setSubmitting(false)
    },
    onError: (error) => {
      console.error('Failed to submit answer:', error)
    },
  })

  // Handle answer submission
  const handleSubmitAnswer = useCallback(
    (answer: AnswerLetter) => {
      const question = currentQuestion()
      if (!question || isSubmitting) return

      answerMutation.mutate({
        questionId: question.id,
        answer,
      })
    },
    [currentQuestion, isSubmitting, answerMutation]
  )

  // Handle session timeout
  const handleTimeout = useCallback(() => {
    completeDiagnostic()
    navigate('/diagnostic/results')
  }, [completeDiagnostic, navigate])

  // Reset and refetch
  const restartDiagnostic = useCallback(() => {
    isInitializedRef.current = false
    resetDiagnostic()
    queryClient.invalidateQueries({ queryKey: ['diagnostic', 'questions'] })
  }, [resetDiagnostic, queryClient])

  return {
    // State
    questions,
    currentIndex,
    currentQuestion: currentQuestion(),
    answers,
    startTime,
    isSubmitting,
    isComplete,
    totalConcepts,
    coveragePercentage,
    progressPercentage: progressPercentage(),

    // Query state (combine course and questions loading/error states)
    isLoading: courseQuery.isLoading || questionsQuery.isLoading,
    isError: courseQuery.isError || questionsQuery.isError,
    error: courseQuery.error || questionsQuery.error,

    // Actions
    handleSubmitAnswer,
    handleTimeout,
    restartDiagnostic,
    refetch: questionsQuery.refetch,
  }
}
