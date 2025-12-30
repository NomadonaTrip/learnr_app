import clsx from 'clsx'

interface FocusContextBannerProps {
  focusType: 'ka' | 'concept'
  targetName: string
  currentMastery?: number
  improvement?: number
  questionsInFocus?: number
}

/**
 * Displays focus context during a focused quiz session.
 * Shows the focus type (KA or concept), target name, and progress metrics.
 * Story 4.8 - Focused Practice Mode.
 */
export function FocusContextBanner({
  focusType,
  targetName,
  currentMastery,
  improvement,
  questionsInFocus,
}: FocusContextBannerProps) {
  const focusLabel = focusType === 'ka' ? 'Knowledge Area' : 'Concept'
  const hasMetrics = currentMastery !== undefined || improvement !== undefined

  // Determine mastery color
  const getMasteryColor = (mastery: number) => {
    if (mastery >= 0.8) return 'text-green-600'
    if (mastery >= 0.5) return 'text-amber-600'
    return 'text-red-600'
  }

  // Determine improvement color
  const getImprovementColor = (delta: number) => {
    if (delta > 0) return 'text-green-600'
    if (delta < 0) return 'text-red-600'
    return 'text-gray-500'
  }

  // Format improvement with sign
  const formatImprovement = (delta: number) => {
    const percent = Math.round(delta * 100)
    if (percent > 0) return `+${percent}%`
    if (percent < 0) return `${percent}%`
    return '0%'
  }

  return (
    <div
      className={clsx(
        'rounded-lg px-4 py-3',
        'bg-indigo-50 border border-indigo-200',
        'flex flex-wrap items-center justify-between gap-3'
      )}
      role="banner"
      aria-label="Focused practice context"
    >
      <div className="flex items-center gap-3">
        <div
          className={clsx(
            'flex items-center justify-center',
            'w-8 h-8 rounded-full',
            'bg-indigo-100 text-indigo-600'
          )}
          aria-hidden="true"
        >
          {focusType === 'ka' ? (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
          ) : (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          )}
        </div>
        <div>
          <p className="text-xs text-indigo-600 font-medium uppercase tracking-wide">
            Focused {focusLabel}
          </p>
          <p className="font-semibold text-gray-900">{targetName}</p>
        </div>
      </div>

      {hasMetrics && (
        <div className="flex items-center gap-4">
          {currentMastery !== undefined && (
            <div className="text-center">
              <p className="text-xs text-gray-500">Mastery</p>
              <p className={clsx('text-lg font-bold', getMasteryColor(currentMastery))}>
                {Math.round(currentMastery * 100)}%
              </p>
            </div>
          )}

          {improvement !== undefined && (
            <div className="text-center">
              <p className="text-xs text-gray-500">Session</p>
              <p className={clsx('text-lg font-bold', getImprovementColor(improvement))}>
                {formatImprovement(improvement)}
              </p>
            </div>
          )}

          {questionsInFocus !== undefined && questionsInFocus > 0 && (
            <div className="text-center">
              <p className="text-xs text-gray-500">In Focus</p>
              <p className="text-lg font-bold text-indigo-600">
                {questionsInFocus}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
