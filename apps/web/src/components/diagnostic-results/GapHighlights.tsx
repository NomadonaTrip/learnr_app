import clsx from 'clsx'
import { useState, useCallback } from 'react'
import type { ConceptGap } from '../../types/diagnostic'

interface GapHighlightsProps {
  gaps: ConceptGap[]
  maxDisplay?: number
  onConceptPracticeClick?: (conceptIds: string[]) => void
}

/**
 * Displays top identified knowledge gaps.
 * Shows concept name, mastery probability, and knowledge area.
 * Includes Practice buttons for focused concept sessions (Story 4.8).
 */
export function GapHighlights({ gaps, maxDisplay = 10, onConceptPracticeClick }: GapHighlightsProps) {
  const [selectedConceptIds, setSelectedConceptIds] = useState<Set<string>>(new Set())

  const toggleConceptSelection = useCallback((conceptId: string) => {
    setSelectedConceptIds(prev => {
      const next = new Set(prev)
      if (next.has(conceptId)) {
        next.delete(conceptId)
      } else {
        next.add(conceptId)
      }
      return next
    })
  }, [])

  const handlePracticeSingle = useCallback((conceptId: string) => {
    console.log('[DEBUG] GapHighlights: Practice single concept clicked', {
      conceptId,
      timestamp: new Date().toISOString(),
    })
    if (onConceptPracticeClick) {
      onConceptPracticeClick([conceptId])
    }
  }, [onConceptPracticeClick])

  const handlePracticeSelected = useCallback(() => {
    if (onConceptPracticeClick && selectedConceptIds.size > 0) {
      onConceptPracticeClick(Array.from(selectedConceptIds))
    }
  }, [onConceptPracticeClick, selectedConceptIds])

  const handleSelectAll = useCallback(() => {
    const displayedGaps = gaps.slice(0, maxDisplay)
    if (selectedConceptIds.size === displayedGaps.length) {
      setSelectedConceptIds(new Set())
    } else {
      setSelectedConceptIds(new Set(displayedGaps.map(g => g.concept_id)))
    }
  }, [gaps, maxDisplay, selectedConceptIds.size])

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
        <div className="flex items-center gap-3">
          {gaps.length > 0 && (
            <span className="text-sm text-gray-500 bg-red-50 px-2 py-1 rounded-full">
              {gaps.length} gap{gaps.length !== 1 ? 's' : ''} identified
            </span>
          )}
          {onConceptPracticeClick && selectedConceptIds.size > 0 && (
            <button
              onClick={handlePracticeSelected}
              className={clsx(
                'px-4 py-1.5 text-sm font-medium rounded-full',
                'bg-indigo-600 text-white hover:bg-indigo-700',
                'transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2'
              )}
              aria-label={`Practice ${selectedConceptIds.size} selected concepts`}
            >
              Practice Selected ({selectedConceptIds.size})
            </button>
          )}
        </div>
      </div>

      <div className="flex justify-between items-center mb-4">
        <p className="text-sm text-gray-600">
          These concepts showed the lowest mastery probability during your diagnostic assessment.
        </p>
        {onConceptPracticeClick && displayedGaps.length > 1 && (
          <button
            onClick={handleSelectAll}
            className="text-sm text-indigo-600 hover:text-indigo-700 font-medium"
          >
            {selectedConceptIds.size === displayedGaps.length ? 'Deselect All' : 'Select All'}
          </button>
        )}
      </div>

      <ul className="space-y-3" aria-label="List of knowledge gaps">
        {displayedGaps.map((gap, index) => {
          const masteryPercent = Math.round(gap.mastery_probability * 100)
          const isSelected = selectedConceptIds.has(gap.concept_id)

          return (
            <li
              key={gap.concept_id}
              className={clsx(
                'flex items-center justify-between p-3 rounded-lg',
                'border transition-colors',
                isSelected
                  ? 'bg-indigo-50 border-indigo-200'
                  : 'bg-red-50 border-red-100 hover:bg-red-100'
              )}
            >
              <div className="flex items-center gap-3">
                {onConceptPracticeClick && (
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => toggleConceptSelection(gap.concept_id)}
                    className={clsx(
                      'h-4 w-4 rounded border-gray-300',
                      'text-indigo-600 focus:ring-indigo-500'
                    )}
                    aria-label={`Select ${gap.name} for practice`}
                  />
                )}
                <span
                  className={clsx(
                    'flex-shrink-0 w-6 h-6 flex items-center justify-center',
                    'text-xs font-medium rounded-full',
                    isSelected
                      ? 'bg-indigo-200 text-indigo-700'
                      : 'bg-red-200 text-red-700'
                  )}
                  aria-hidden="true"
                >
                  {index + 1}
                </span>
                <div>
                  <p className="font-medium text-gray-900">{gap.name}</p>
                  <p className="text-xs text-gray-500">{gap.knowledge_area}</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
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
                {onConceptPracticeClick && (
                  <button
                    onClick={() => handlePracticeSingle(gap.concept_id)}
                    className={clsx(
                      'px-3 py-1 text-xs font-medium rounded-full',
                      'bg-indigo-100 text-indigo-700 hover:bg-indigo-200',
                      'transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2'
                    )}
                    aria-label={`Practice ${gap.name}`}
                  >
                    Practice
                  </button>
                )}
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
