import { useMemo, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { diagnosticService } from '../services/diagnosticService'
import { courseService } from '../services/courseService'
import type { DiagnosticResultsResponse } from '../types/diagnostic'

/** Storage key for onboarding data */
const ONBOARDING_STORAGE_KEY = 'learnr_onboarding'

/** Default course slug if none selected */
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
 * Hook for fetching and managing diagnostic results.
 * Uses React Query for caching and automatic refetching.
 */
export function useDiagnosticResults() {
  const queryClient = useQueryClient()

  // Get course slug from onboarding selection
  const courseSlug = useMemo(() => getSelectedCourseSlug(), [])

  // Fetch course details to get UUID
  const courseQuery = useQuery({
    queryKey: ['course', courseSlug],
    queryFn: () => courseService.fetchCourseBySlug(courseSlug),
    staleTime: Infinity,
    retry: 2,
  })

  // Fetch diagnostic results (depends on course UUID)
  const resultsQuery = useQuery<DiagnosticResultsResponse>({
    queryKey: ['diagnostic', 'results', courseQuery.data?.id],
    queryFn: () => diagnosticService.fetchDiagnosticResults(courseQuery.data!.id),
    enabled: !!courseQuery.data?.id,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 2,
  })

  // Submit feedback mutation
  const feedbackMutation = useMutation({
    mutationFn: ({ rating, comment }: { rating: number; comment?: string }) =>
      diagnosticService.submitDiagnosticFeedback(courseQuery.data!.id, rating, comment),
    onSuccess: () => {
      // Optionally invalidate any related queries
      queryClient.invalidateQueries({ queryKey: ['diagnostic', 'feedback'] })
    },
  })

  // Handle feedback submission
  const submitFeedback = useCallback(
    (rating: number, comment?: string) => {
      if (!courseQuery.data?.id) return
      feedbackMutation.mutate({ rating, comment })
    },
    [courseQuery.data?.id, feedbackMutation]
  )

  // Computed values for display
  const coveragePercentDisplay = useMemo(() => {
    if (!resultsQuery.data) return '0%'
    return `${Math.round(resultsQuery.data.coverage_percentage * 100)}%`
  }, [resultsQuery.data])

  return {
    // Data
    data: resultsQuery.data,
    course: courseQuery.data,

    // Query state
    isLoading: courseQuery.isLoading || resultsQuery.isLoading,
    isError: courseQuery.isError || resultsQuery.isError,
    error: courseQuery.error || resultsQuery.error,

    // Feedback
    submitFeedback,
    isFeedbackSubmitting: feedbackMutation.isPending,
    feedbackSuccess: feedbackMutation.isSuccess,
    feedbackError: feedbackMutation.error,

    // Computed display values
    coveragePercentDisplay,

    // Actions
    refetch: resultsQuery.refetch,
  }
}
