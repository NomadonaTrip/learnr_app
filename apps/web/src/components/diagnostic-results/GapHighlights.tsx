import clsx from 'clsx'
import type { ConceptGap } from '../../types/diagnostic'

interface GapHighlightsProps {
  gaps: ConceptGap[]
  maxDisplay?: number
}

/**
 * Displays top identified knowledge gaps.
 * Shows concept name, mastery probability, and knowledge area.
 */
export function GapHighlights({ gaps, maxDisplay = 10 }: GapHighlightsProps) {
  if (gaps.length === 0) {
    return (
      <section
        className="bg-white rounded-xl p-6 shadow-sm"
        aria-labelledby="gaps-title"
      >
        <h2 id="gaps-title" className="text-xl font-semibold text-gray-900 mb-4">
          Knowledge Gaps
        </h2>
        <div className="text-center py-8">
          <div className="text-4xl mb-2">&#127881;</div>
          <p className="text-gray-600">
            Great news! No significant knowledge gaps were identified.
          </p>
          <p className="text-sm text-gray-500 mt-2">
            Continue with adaptive quizzes to maintain and strengthen your understanding.
          </p>
        </div>
      </section>
    )
  }

  const displayedGaps = gaps.slice(0, maxDisplay)

  return (
    <section
      className="bg-white rounded-xl p-6 shadow-sm"
      aria-labelledby="gaps-title"
    >
      <div className="flex justify-between items-center mb-4">
        <h2 id="gaps-title" className="text-xl font-semibold text-gray-900">
          Top Knowledge Gaps
        </h2>
        {gaps.length > 0 && (
          <span className="text-sm text-gray-500 bg-red-50 px-2 py-1 rounded-full">
            {gaps.length} gap{gaps.length !== 1 ? 's' : ''} identified
          </span>
        )}
      </div>

      <p className="text-sm text-gray-600 mb-4">
        These concepts showed the lowest mastery probability during your diagnostic assessment.
      </p>

      <ul className="space-y-3" aria-label="List of knowledge gaps">
        {displayedGaps.map((gap, index) => {
          const masteryPercent = Math.round(gap.mastery_probability * 100)

          return (
            <li
              key={gap.concept_id}
              className={clsx(
                'flex items-center justify-between p-3 rounded-lg',
                'bg-red-50 border border-red-100',
                'hover:bg-red-100 transition-colors'
              )}
            >
              <div className="flex items-center gap-3">
                <span
                  className="flex-shrink-0 w-6 h-6 flex items-center justify-center
                             bg-red-200 text-red-700 text-xs font-medium rounded-full"
                  aria-hidden="true"
                >
                  {index + 1}
                </span>
                <div>
                  <p className="font-medium text-gray-900">{gap.name}</p>
                  <p className="text-xs text-gray-500">{gap.knowledge_area}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <div
                  className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden"
                  role="progressbar"
                  aria-valuenow={masteryPercent}
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-label={`${gap.name}: ${masteryPercent}% mastery`}
                >
                  <div
                    className="h-full bg-red-500"
                    style={{ width: `${masteryPercent}%` }}
                  />
                </div>
                <span className="text-sm font-medium text-red-600 min-w-[3rem] text-right">
                  {masteryPercent}%
                </span>
              </div>
            </li>
          )
        })}
      </ul>

      {gaps.length > maxDisplay && (
        <p className="text-sm text-gray-500 mt-4 text-center">
          Showing top {maxDisplay} of {gaps.length} identified gaps
        </p>
      )}
    </section>
  )
}
