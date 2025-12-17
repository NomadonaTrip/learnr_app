import { useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDiagnosticResults } from '../hooks/useDiagnosticResults'
import {
  ResultsHeroSection,
  RecommendationsSection,
  FeedbackSurvey,
  DetailsAccordion,
} from '../components/diagnostic-results'
import { ResetDiagnosticButton } from '../components/diagnostic/ResetDiagnosticButton'

/**
 * Diagnostic Results Page.
 * Displays comprehensive knowledge profile after completing diagnostic assessment.
 *
 * Sections (optimized for CTA visibility):
 * 1. Hero Section - Overall coverage donut chart and key stats
 * 2. Recommendations - Next steps with CTA buttons (visible without scrolling)
 * 3. Details Accordion (collapsed by default):
 *    - Knowledge Area Breakdown - Per-KA mastery bars
 *    - Top Gaps - Identified knowledge gaps
 *    - Uncertainty Callout - Educational note about uncertain concepts
 * 4. Feedback Survey - Post-diagnostic accuracy rating
 * 5. Reset Diagnostic Option
 */
export function DiagnosticResultsPage() {
  const navigate = useNavigate()
  const {
    data,
    course,
    isLoading,
    isError,
    error,
    submitFeedback,
    isFeedbackSubmitting,
    feedbackSuccess,
    refetch,
  } = useDiagnosticResults()

  // CTA handlers
  const handleStartQuiz = useCallback(() => {
    // Navigate to adaptive quiz page (placeholder path)
    navigate('/quiz')
  }, [navigate])

  const handleViewStudyPlan = useCallback(() => {
    // Navigate to study plan page (placeholder path)
    navigate('/study-plan')
  }, [navigate])

  // Loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4" />
          <p className="text-gray-600">Loading your results...</p>
        </div>
      </div>
    )
  }

  // Error state
  if (isError) {
    const errorMessage = error instanceof Error ? error.message : 'Failed to load results'
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
        <div className="text-center max-w-md">
          <div className="text-red-500 text-5xl mb-4">&#9888;</div>
          <h1 className="text-xl font-semibold text-gray-900 mb-2">
            Unable to Load Results
          </h1>
          <p className="text-gray-600 mb-6">{errorMessage}</p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <button
              onClick={() => refetch()}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
            >
              Try Again
            </button>
            <button
              onClick={() => navigate('/diagnostic')}
              className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Back to Diagnostic
            </button>
          </div>
        </div>
      </div>
    )
  }

  // No data state
  if (!data) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
        <div className="text-center max-w-md">
          <div className="text-gray-400 text-5xl mb-4">&#128202;</div>
          <h1 className="text-xl font-semibold text-gray-900 mb-2">
            No Results Available
          </h1>
          <p className="text-gray-600 mb-6">
            Complete the diagnostic assessment to see your knowledge profile.
          </p>
          <button
            onClick={() => navigate('/diagnostic')}
            className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
          >
            Start Diagnostic
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8 space-y-6">
        {/* Course header */}
        {course && (
          <div className="text-center mb-2">
            <p className="text-sm text-gray-500">{course.name}</p>
          </div>
        )}

        {/* Hero Section - Overall stats */}
        <ResultsHeroSection
          score={data.score}
          totalConcepts={data.total_concepts}
          conceptsTouched={data.concepts_touched}
          coveragePercentage={data.coverage_percentage}
          estimatedMastered={data.estimated_mastered}
          estimatedGaps={data.estimated_gaps}
          uncertain={data.uncertain}
          confidenceLevel={data.confidence_level}
        />

        {/* Recommendations and CTAs - Moved up for visibility without scrolling */}
        <RecommendationsSection
          recommendations={data.recommendations}
          onStartQuiz={handleStartQuiz}
          onViewStudyPlan={handleViewStudyPlan}
        />

        {/* Details Accordion - Collapsed by default */}
        <DetailsAccordion
          areas={data.by_knowledge_area}
          gaps={data.top_gaps}
          uncertainCount={data.uncertain}
          confidenceLevel={data.confidence_level}
          message={data.recommendations.message}
        />

        {/* Feedback Survey */}
        <FeedbackSurvey
          onSubmit={submitFeedback}
          isSubmitting={isFeedbackSubmitting}
          isSuccess={feedbackSuccess}
        />

        {/* Retake Diagnostic Option (Story 3.9) */}
        {course && (
          <div className="text-center pt-4 pb-2 border-t border-gray-200">
            <p className="text-sm text-gray-500 mb-3">
              Want to start fresh? Retaking the diagnostic will reset your knowledge estimates.
            </p>
            <ResetDiagnosticButton
              courseId={course.id}
              variant="text"
              buttonText="Retake Diagnostic"
            />
          </div>
        )}

        {/* Footer note */}
        <p className="text-xs text-gray-400 text-center pt-4">
          Your knowledge profile will continue to improve as you complete more quizzes.
        </p>
      </div>
    </div>
  )
}
