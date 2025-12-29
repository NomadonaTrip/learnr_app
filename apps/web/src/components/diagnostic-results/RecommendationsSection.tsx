import clsx from 'clsx'
import type { Recommendations } from '../../types/diagnostic'

interface RecommendationsSectionProps {
  recommendations: Recommendations
  onStartQuiz: () => void
  onViewReadingLibrary: () => void
}

/**
 * Displays personalized recommendations and CTA buttons.
 * Primary action: Start Adaptive Quiz, Secondary: View Reading Library
 */
export function RecommendationsSection({
  recommendations,
  onStartQuiz,
  onViewReadingLibrary,
}: RecommendationsSectionProps) {
  return (
    <section
      className="bg-gradient-to-br from-primary-600 to-primary-700 rounded-xl p-6 text-white"
      aria-labelledby="recommendations-title"
    >
      <h2 id="recommendations-title" className="text-xl font-semibold mb-4">
        Your Next Steps
      </h2>

      <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4 mb-6">
        <p className="text-white/90 mb-3">{recommendations.message}</p>
        <div className="flex items-center gap-4 text-sm">
          <div className="flex items-center gap-2">
            <svg
              className="w-5 h-5 text-white/80"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <span>Focus on: <strong>{recommendations.primary_focus}</strong></span>
          </div>
          <div className="flex items-center gap-2">
            <svg
              className="w-5 h-5 text-white/80"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <span>~{recommendations.estimated_questions_to_coverage} questions to improve coverage</span>
          </div>
        </div>
      </div>

      {/* CTA Buttons */}
      <div className="flex flex-col sm:flex-row gap-3">
        <button
          onClick={onStartQuiz}
          className={clsx(
            'flex-1 px-6 py-3 rounded-lg font-semibold',
            'bg-white text-primary-700',
            'hover:bg-gray-50 active:bg-gray-100',
            'focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-primary-600',
            'transition-colors'
          )}
          aria-label="Start an adaptive quiz based on your results"
        >
          <span className="flex items-center justify-center gap-2">
            <svg
              className="w-5 h-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
              />
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            Start Adaptive Quiz
          </span>
        </button>

        <button
          onClick={onViewReadingLibrary}
          className={clsx(
            'flex-1 px-6 py-3 rounded-lg font-semibold',
            'bg-transparent text-white border-2 border-white/50',
            'hover:bg-white/10 active:bg-white/20',
            'focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-primary-600',
            'transition-colors'
          )}
          aria-label="View your curated reading library"
        >
          <span className="flex items-center justify-center gap-2">
            <svg
              className="w-5 h-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
              />
            </svg>
            View Reading Library
          </span>
        </button>
      </div>
    </section>
  )
}
