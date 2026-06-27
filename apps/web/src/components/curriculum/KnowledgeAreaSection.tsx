import { useState } from 'react'
import { ConceptRow } from './ConceptRow'
import type { KaGroup } from '../../utils/curriculum'

interface KnowledgeAreaSectionProps {
  group: KaGroup
}

/**
 * Collapsible group of concepts for one knowledge area, with an unlocked/total
 * count in the header (AC 10).
 *
 * Self-contained — does NOT use CollapsibleSection because that component caps
 * content at max-h-[2000px], which clips ~200-concept KAs. Instead we render
 * the list inside a max-h-[70vh] scrollable container so every row is reachable.
 */
export function KnowledgeAreaSection({ group }: KnowledgeAreaSectionProps) {
  const { knowledgeArea, concepts, unlockedCount, totalCount } = group
  const [isExpanded, setIsExpanded] = useState(true)

  return (
    <div>
      <button
        type="button"
        aria-expanded={isExpanded}
        onClick={() => setIsExpanded((prev) => !prev)}
        className="w-full flex items-center justify-between px-4 py-3 text-left bg-white border border-gray-200 rounded-lg hover:bg-gray-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2 min-h-[44px]"
      >
        <span className="font-medium text-gray-900">
          {`${knowledgeArea.name} — ${unlockedCount}/${totalCount} unlocked`}
        </span>
        <svg
          className={`w-5 h-5 text-gray-500 flex-shrink-0 ml-2 transition-transform duration-300 motion-reduce:transition-none${isExpanded ? ' rotate-180' : ''}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>

      {isExpanded && (
        <div className="max-h-[70vh] overflow-y-auto">
          <div className="divide-y divide-gray-100">
            {concepts.map((concept) => (
              <ConceptRow key={concept.concept_id} concept={concept} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
