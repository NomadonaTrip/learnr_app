import clsx from 'clsx'
import type { KnowledgeAreaResult } from '../../types/diagnostic'

interface KnowledgeAreaBreakdownProps {
  areas: KnowledgeAreaResult[]
  onFocusClick?: (kaId: string, kaName: string) => void
}

/**
 * Displays per-knowledge area breakdown with mastery bars.
 * Shows concepts touched and estimated mastery for each KA.
 * Includes "Focus" button for KAs below mastery threshold (Story 4.8).
 */
export function KnowledgeAreaBreakdown({ areas, onFocusClick }: KnowledgeAreaBreakdownProps) {
  if (areas.length === 0) {
    return null
  }

  return (
    <section
      className="bg-white rounded-xl p-6 shadow-sm"
      aria-labelledby="ka-breakdown-title"
    >
      <h2 id="ka-breakdown-title" className="text-xl font-semibold text-gray-900 mb-4">
        Knowledge Area Breakdown
      </h2>

      <div className="space-y-4">
        {areas.map((area) => {
          const masteryPercent = Math.round(area.estimated_mastery * 100)
          const touchedPercent = area.concepts > 0
            ? Math.round((area.touched / area.concepts) * 100)
            : 0

          // Determine color based on mastery level
          const getMasteryColor = (mastery: number) => {
            if (mastery >= 0.8) return 'bg-green-500'
            if (mastery >= 0.5) return 'bg-amber-500'
            return 'bg-red-500'
          }

          // Show Focus button for KAs below mastery (< 80%)
          const showFocusButton = onFocusClick && area.estimated_mastery < 0.8

          return (
            <div key={area.ka_id} className="border-b border-gray-100 pb-4 last:border-0 last:pb-0">
              <div className="flex justify-between items-center mb-2">
                <h3 className="font-medium text-gray-900">{area.ka}</h3>
                <div className="flex items-center gap-3">
                  <span className="text-sm text-gray-500">
                    {area.touched} / {area.concepts} concepts
                  </span>
                  {showFocusButton && (
                    <button
                      onClick={() => onFocusClick(area.ka_id, area.ka)}
                      className={clsx(
                        'px-3 py-1 text-xs font-medium rounded-full',
                        'bg-indigo-100 text-indigo-700 hover:bg-indigo-200',
                        'transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2'
                      )}
                      aria-label={`Start focused practice for ${area.ka}`}
                    >
                      Focus
                    </button>
                  )}
                </div>
              </div>

              {/* Mastery bar */}
              <div className="relative">
                <div
                  className="h-3 bg-gray-100 rounded-full overflow-hidden"
                  role="progressbar"
                  aria-valuenow={masteryPercent}
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-label={`${area.ka}: ${masteryPercent}% estimated mastery`}
                >
                  <div
                    className={clsx(
                      'h-full rounded-full',
                      getMasteryColor(area.estimated_mastery),
                      'transition-all duration-500 motion-reduce:transition-none'
                    )}
                    style={{ width: `${masteryPercent}%` }}
                  />
                </div>

                {/* Mastery percentage label */}
                <div className="flex justify-between items-center mt-1">
                  <span className="text-xs text-gray-500">
                    {touchedPercent}% assessed
                  </span>
                  <span
                    className={clsx(
                      'text-sm font-medium',
                      area.estimated_mastery >= 0.8 ? 'text-green-600' :
                      area.estimated_mastery >= 0.5 ? 'text-amber-600' : 'text-red-600'
                    )}
                  >
                    {masteryPercent}% mastery
                  </span>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Legend */}
      <div className="mt-6 pt-4 border-t border-gray-100">
        <div className="flex flex-wrap gap-4 text-xs text-gray-500">
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-3 rounded-full bg-green-500" />
            <span>Mastered (80%+)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-3 rounded-full bg-amber-500" />
            <span>Developing (50-80%)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-3 rounded-full bg-red-500" />
            <span>Needs Work (&lt;50%)</span>
          </div>
        </div>
      </div>
    </section>
  )
}
