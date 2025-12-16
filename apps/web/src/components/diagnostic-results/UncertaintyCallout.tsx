import type { ConfidenceLevel } from '../../types/diagnostic'

interface UncertaintyCalloutProps {
  uncertainCount: number
  confidenceLevel: ConfidenceLevel
  message: string
}

/**
 * Educational callout explaining what "uncertain" means in the context
 * of Bayesian Knowledge Tracing and how to improve profile confidence.
 */
export function UncertaintyCallout({
  uncertainCount,
  confidenceLevel,
  message,
}: UncertaintyCalloutProps) {
  // Only show callout if there are uncertain concepts and profile isn't established
  if (uncertainCount === 0 || confidenceLevel === 'established') {
    return null
  }

  return (
    <section
      className="bg-amber-50 border border-amber-200 rounded-xl p-6"
      role="note"
      aria-labelledby="uncertainty-title"
    >
      <div className="flex gap-4">
        <div className="flex-shrink-0">
          <svg
            className="w-6 h-6 text-amber-600"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        </div>
        <div>
          <h3 id="uncertainty-title" className="font-semibold text-amber-800 mb-2">
            Building Your Knowledge Profile
          </h3>
          <p className="text-sm text-amber-700 mb-3">
            {message}
          </p>
          <div className="text-sm text-amber-600 space-y-2">
            <p>
              <strong>{uncertainCount}</strong> concept{uncertainCount !== 1 ? 's' : ''} need{uncertainCount === 1 ? 's' : ''} more
              data for confident classification. This is normal after a diagnostic assessment.
            </p>
            <p>
              As you continue with adaptive quizzes, the system will learn more about your
              knowledge level and provide increasingly accurate recommendations.
            </p>
          </div>
        </div>
      </div>
    </section>
  )
}
