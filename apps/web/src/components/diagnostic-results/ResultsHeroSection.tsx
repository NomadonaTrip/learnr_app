import clsx from 'clsx'
import type { ConfidenceLevel, DiagnosticScore } from '../../types/diagnostic'

interface ResultsHeroSectionProps {
  score?: DiagnosticScore
  totalConcepts: number
  conceptsTouched: number
  coveragePercentage: number
  estimatedMastered: number
  estimatedGaps: number
  uncertain: number
  confidenceLevel: ConfidenceLevel
}

/**
 * Hero section for diagnostic results page.
 * Displays overall coverage donut chart and key statistics.
 */
export function ResultsHeroSection({
  score,
  totalConcepts,
  conceptsTouched,
  coveragePercentage,
  estimatedMastered,
  estimatedGaps,
  uncertain,
  confidenceLevel,
}: ResultsHeroSectionProps) {
  const coveragePercent = Math.round(coveragePercentage * 100)

  // Determine score color based on percentage
  const getScoreColor = (percentage: number) => {
    if (percentage >= 80) return 'text-green-600'
    if (percentage >= 60) return 'text-blue-600'
    if (percentage >= 40) return 'text-amber-600'
    return 'text-red-600'
  }

  // Calculate circumference for SVG donut chart
  const radius = 70
  const circumference = 2 * Math.PI * radius
  const strokeDashoffset = circumference - (coveragePercentage * circumference)

  // Confidence level display text
  const confidenceDisplay: Record<ConfidenceLevel, { label: string; color: string }> = {
    initial: { label: 'Initial Profile', color: 'text-amber-600' },
    developing: { label: 'Developing Profile', color: 'text-blue-600' },
    established: { label: 'Established Profile', color: 'text-green-600' },
  }

  const { label: confidenceLabel, color: confidenceColor } = confidenceDisplay[confidenceLevel]

  return (
    <section
      className="bg-gradient-to-br from-primary-50 to-primary-100 rounded-2xl p-6 md:p-8"
      aria-labelledby="results-hero-title"
    >
      <h1 id="results-hero-title" className="text-2xl md:text-3xl font-bold text-gray-900 mb-2">
        Your Knowledge Profile
      </h1>
      <p className={clsx('text-sm font-medium mb-6', confidenceColor)}>
        {confidenceLabel}
      </p>

      {/* Diagnostic Score Banner */}
      {score && score.questions_answered > 0 && (
        <div className="bg-white rounded-xl p-6 mb-6 shadow-sm">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="text-center sm:text-left">
              <h2 className="text-lg font-semibold text-gray-700 mb-1">Diagnostic Score</h2>
              <p className="text-sm text-gray-500">
                {score.questions_correct} of {score.questions_answered} questions correct
              </p>
            </div>
            <div className="flex items-center gap-4">
              <div className={clsx('text-5xl font-bold', getScoreColor(score.score_percentage))}>
                {score.score_percentage}%
              </div>
              <div className="text-left text-sm text-gray-600 hidden sm:block">
                <div className="flex items-center gap-1">
                  <span className="inline-block w-3 h-3 rounded-full bg-green-500" />
                  <span>{score.questions_correct} correct</span>
                </div>
                <div className="flex items-center gap-1">
                  <span className="inline-block w-3 h-3 rounded-full bg-red-500" />
                  <span>{score.questions_incorrect} incorrect</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="flex flex-col md:flex-row items-center gap-8">
        {/* Coverage donut chart */}
        <div
          className="relative w-48 h-48 flex-shrink-0"
          role="img"
          aria-label={`Coverage: ${coveragePercent}% of ${totalConcepts} concepts assessed`}
        >
          <svg
            className="w-full h-full transform -rotate-90"
            viewBox="0 0 160 160"
          >
            {/* Background circle */}
            <circle
              cx="80"
              cy="80"
              r={radius}
              fill="none"
              stroke="currentColor"
              strokeWidth="12"
              className="text-gray-200"
            />
            {/* Progress circle */}
            <circle
              cx="80"
              cy="80"
              r={radius}
              fill="none"
              stroke="currentColor"
              strokeWidth="12"
              strokeLinecap="round"
              className={clsx(
                'text-primary-600',
                'transition-all duration-700 ease-out motion-reduce:transition-none'
              )}
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
            />
          </svg>
          {/* Center text */}
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-4xl font-bold text-gray-900">{coveragePercent}%</span>
            <span className="text-sm text-gray-600">Coverage</span>
          </div>
        </div>

        {/* Stats grid */}
        <div className="grid grid-cols-2 gap-4 flex-1 w-full max-w-md">
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <p className="text-2xl font-bold text-gray-900">{conceptsTouched}</p>
            <p className="text-sm text-gray-600">Concepts Assessed</p>
          </div>
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <p className="text-2xl font-bold text-gray-900">{totalConcepts}</p>
            <p className="text-sm text-gray-600">Total Concepts</p>
          </div>
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <p className="text-2xl font-bold text-green-600">{estimatedMastered}</p>
            <p className="text-sm text-gray-600">Likely Mastered</p>
          </div>
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <p className="text-2xl font-bold text-red-600">{estimatedGaps}</p>
            <p className="text-sm text-gray-600">Identified Gaps</p>
          </div>
        </div>
      </div>

      {/* Uncertain concepts note */}
      {uncertain > 0 && (
        <p className="mt-4 text-sm text-gray-600 text-center md:text-left">
          {uncertain} concept{uncertain !== 1 ? 's' : ''} need{uncertain === 1 ? 's' : ''} more assessment for confident classification
        </p>
      )}
    </section>
  )
}
