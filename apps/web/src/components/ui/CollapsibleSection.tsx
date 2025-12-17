import { useState, type ReactNode } from 'react'
import clsx from 'clsx'

interface CollapsibleSectionProps {
  /** Unique identifier for ARIA relationships */
  id: string
  /** Title displayed on the toggle button */
  title: string
  /** Content to show/hide */
  children: ReactNode
  /** Initial expanded state (defaults to false) */
  defaultExpanded?: boolean
  /** Optional class name for the container */
  className?: string
}

/**
 * Accessible collapsible section component.
 * Supports keyboard navigation, screen readers, and reduced motion preferences.
 */
export function CollapsibleSection({
  id,
  title,
  children,
  defaultExpanded = false,
  className,
}: CollapsibleSectionProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded)

  const toggleId = `${id}-toggle`
  const contentId = `${id}-content`

  const handleToggle = () => {
    setIsExpanded((prev) => !prev)
  }

  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      handleToggle()
    }
  }

  return (
    <div className={clsx('collapsible-section', className)}>
      <button
        id={toggleId}
        type="button"
        aria-expanded={isExpanded}
        aria-controls={contentId}
        onClick={handleToggle}
        onKeyDown={handleKeyDown}
        className={clsx(
          'w-full flex items-center justify-between',
          'px-4 py-3 text-left',
          'bg-white border border-gray-200 rounded-lg',
          'hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
          'transition-colors duration-200 motion-reduce:transition-none',
          'min-h-[44px]' // Ensure touch target size >= 44px
        )}
      >
        <span className="font-medium text-gray-900">{title}</span>
        <svg
          className={clsx(
            'w-5 h-5 text-gray-500 flex-shrink-0 ml-2',
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
        <div className="pt-4">{children}</div>
      </div>
    </div>
  )
}
