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
 * Displays diagnostic score in donut chart and coverage statistics below.
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

  const getScoreStrokeColor = (percentage: number) => {
    if (percentage >= 80) return 'text-green-500'
    if (percentage >= 60) return 'text-blue-500'
    if (percentage >= 40) return 'text-amber-500'
    return 'text-red-500'
  }

  // Calculate circumference for SVG donut chart
  const radius = 70
  const circumference = 2 * Math.PI * radius

  // Use score percentage for donut if available, otherwise coverage
  const scorePercentage = score?.score_percentage ?? 0
  const scoreDecimal = scorePercentage / 100
  const scoreStrokeDashoffset = circumference - (scoreDecimal * circumference)

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
        Your Diagnostic Results
      </h1>
      <p className={clsx('text-sm font-medium mb-6', confidenceColor)}>
        {confidenceLabel}
      </p>

      {/* Main content: Score donut + stats */}
      <div className="flex flex-col md:flex-row items-center gap-8">
        {/* Diagnostic Score donut chart */}
        {score && score.questions_answered > 0 ? (
          <div
            className="relative w-48 h-48 flex-shrink-0"
            role="img"
            aria-label={`Score: ${scorePercentage}% - ${score.questions_correct} of ${score.questions_answered} correct`}
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
                  getScoreStrokeColor(scorePercentage),
                  'transition-all duration-700 ease-out motion-reduce:transition-none'
                )}
                strokeDasharray={circumference}
                strokeDashoffset={scoreStrokeDashoffset}
              />
            </svg>
            {/* Center text */}
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className={clsx('text-4xl font-bold', getScoreColor(scorePercentage))}>
                {scorePercentage}%
              </span>
              <span className="text-sm text-gray-600">Your Score</span>
              <span className="text-xs text-gray-500 mt-1">
                {score.questions_correct}/{score.questions_answered} correct
              </span>
            </div>
          </div>
        ) : (
          <div
            className="relative w-48 h-48 flex-shrink-0"
            role="img"
            aria-label="No score available"
          >
            <svg
              className="w-full h-full transform -rotate-90"
              viewBox="0 0 160 160"
            >
              <circle
                cx="80"
                cy="80"
                r={radius}
                fill="none"
                stroke="currentColor"
                strokeWidth="12"
                className="text-gray-200"
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-4xl font-bold text-gray-400">--</span>
              <span className="text-sm text-gray-500">No Score</span>
            </div>
          </div>
        )}

        {/* Stats grid */}
        <div className="grid grid-cols-2 gap-4 flex-1 w-full max-w-md">
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <p className="text-2xl font-bold text-green-600">{score?.questions_correct ?? 0}</p>
            <p className="text-sm text-gray-600">Correct Answers</p>
          </div>
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <p className="text-2xl font-bold text-red-600">{score?.questions_incorrect ?? 0}</p>
            <p className="text-sm text-gray-600">Incorrect Answers</p>
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

      {/* Coverage/Competence Banner - now secondary */}
      <div className="bg-white rounded-xl p-4 mt-6 shadow-sm">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="text-center sm:text-left">
            <h2 className="text-lg font-semibold text-gray-700 mb-1">Knowledge Coverage</h2>
            <p className="text-sm text-gray-500">
              {conceptsTouched} of {totalConcepts} concepts assessed
            </p>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-4xl font-bold text-primary-600">
              {coveragePercent}%
            </div>
            <div className="text-left text-sm text-gray-600 hidden sm:block">
              <div className="flex items-center gap-1">
                <span className="inline-block w-3 h-3 rounded-full bg-primary-500" />
                <span>{conceptsTouched} assessed</span>
              </div>
              <div className="flex items-center gap-1">
                <span className="inline-block w-3 h-3 rounded-full bg-gray-300" />
                <span>{totalConcepts - conceptsTouched} remaining</span>
              </div>
            </div>
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
