import { useEffect, useRef, useCallback } from 'react'
import { trackEvent } from '../services/analyticsService'

interface ScrollDepthOptions {
  milestones?: number[]
  eventName?: string
}

/**
 * Hook for tracking scroll depth milestones.
 * Tracks when user scrolls to 25%, 50%, 75%, and 100% of the page.
 */
export function useScrollDepthTracking(options: ScrollDepthOptions = {}): void {
  const {
    milestones = [25, 50, 75, 100],
    eventName = 'landing_scroll_depth'
  } = options

  const trackedMilestones = useRef<Set<number>>(new Set())

  const handleScroll = useCallback(() => {
    const scrollHeight = document.documentElement.scrollHeight - window.innerHeight
    if (scrollHeight <= 0) return

    const scrollTop = window.scrollY
    const scrollPercentage = Math.round((scrollTop / scrollHeight) * 100)

    for (const milestone of milestones) {
      if (
        scrollPercentage >= milestone &&
        !trackedMilestones.current.has(milestone)
      ) {
        trackedMilestones.current.add(milestone)
        trackEvent(eventName, { depth: `${milestone}%` })
      }
    }
  }, [milestones, eventName])

  useEffect(() => {
    // Reset tracked milestones on mount
    trackedMilestones.current = new Set()

    // Check initial scroll position
    handleScroll()

    // Add scroll listener with passive option for performance
    window.addEventListener('scroll', handleScroll, { passive: true })

    return () => {
      window.removeEventListener('scroll', handleScroll)
    }
  }, [handleScroll])
}

export default useScrollDepthTracking
