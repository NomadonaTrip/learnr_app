import { useState } from 'react'
import clsx from 'clsx'
import type { KnowledgeAreaResult, ConceptGap, ConfidenceLevel } from '../../types/diagnostic'
import { KnowledgeAreaBreakdown } from './KnowledgeAreaBreakdown'
import { GapHighlights } from './GapHighlights'
import { UncertaintyCallout } from './UncertaintyCallout'

interface DetailsAccordionProps {
  /** Knowledge area breakdown data */
  areas: KnowledgeAreaResult[]
  /** Gap highlights data */
  gaps: ConceptGap[]
  /** Uncertainty callout data */
  uncertainCount: number
  confidenceLevel: ConfidenceLevel
  message: string
}

/**
 * Collapsible accordion wrapper for detailed diagnostic results.
 * Contains KnowledgeAreaBreakdown, GapHighlights, and UncertaintyCallout.
 * Collapsed by default to prioritize the "Start Learning" CTA visibility.
 */
export function DetailsAccordion({
  areas,
  gaps,
  uncertainCount,
  confidenceLevel,
  message,
}: DetailsAccordionProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  const toggleId = 'details-accordion-toggle'
  const contentId = 'details-accordion-content'

  const handleToggle = () => {
    setIsExpanded((prev) => !prev)
  }

  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      handleToggle()
    }
  }

  // Determine if there's any content to show
  const hasContent =
    areas.length > 0 ||
    gaps.length > 0 ||
    (uncertainCount > 0 && confidenceLevel !== 'established')

  // Don't render if there's no content
  if (!hasContent) {
    return null
  }

  return (
    <div className="details-accordion">
      <button
        id={toggleId}
        type="button"
        aria-expanded={isExpanded}
        aria-controls={contentId}
        onClick={handleToggle}
        onKeyDown={handleKeyDown}
        className={clsx(
          'w-full flex items-center justify-center gap-2',
          'px-4 py-3 text-center',
          'bg-white border border-gray-200 rounded-lg',
          'hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
          'transition-colors duration-200 motion-reduce:transition-none',
          'min-h-[44px]' // Ensure touch target size >= 44px
        )}
      >
        <span className="font-medium text-gray-700">
          {isExpanded ? 'Hide Details' : 'View Detailed Breakdown'}
        </span>
        <svg
          className={clsx(
            'w-5 h-5 text-gray-500 flex-shrink-0',
            'transition-transform duration-300 motion-reduce:transition-none',
            isExpanded && 'rotate-180'
          )}
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

      <div
        id={contentId}
        role="region"
        aria-labelledby={toggleId}
        className={clsx(
          'overflow-hidden',
          'transition-all duration-300 motion-reduce:transition-none',
          isExpanded ? 'max-h-[2000px] opacity-100' : 'max-h-0 opacity-0'
        )}
      >
        <div className="pt-6 space-y-6">
          {/* Knowledge Area Breakdown */}
          <KnowledgeAreaBreakdown areas={areas} />

          {/* Top Gaps */}
          <GapHighlights gaps={gaps} />

          {/* Uncertainty Callout */}
          <UncertaintyCallout
            uncertainCount={uncertainCount}
            confidenceLevel={confidenceLevel}
            message={message}
          />
        </div>
      </div>
    </div>
  )
}
