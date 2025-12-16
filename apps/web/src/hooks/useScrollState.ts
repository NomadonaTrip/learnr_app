import { useState, useEffect } from 'react'

interface ScrollState {
  isScrolled: boolean
  scrollY: number
  scrollDirection: 'up' | 'down' | null
}

interface UseScrollStateOptions {
  threshold?: number
}

/**
 * Hook for tracking scroll state (position and direction).
 * Useful for navbar styling changes on scroll.
 */
export function useScrollState(options: UseScrollStateOptions = {}): ScrollState {
  const { threshold = 10 } = options

  const [scrollState, setScrollState] = useState<ScrollState>({
    isScrolled: false,
    scrollY: 0,
    scrollDirection: null,
  })

  useEffect(() => {
    let lastScrollY = window.scrollY

    const handleScroll = () => {
      const currentScrollY = window.scrollY
      const isScrolled = currentScrollY > threshold
      const scrollDirection = currentScrollY > lastScrollY ? 'down' : 'up'

      setScrollState({
        isScrolled,
        scrollY: currentScrollY,
        scrollDirection,
      })

      lastScrollY = currentScrollY
    }

    // Check initial state
    handleScroll()

    window.addEventListener('scroll', handleScroll, { passive: true })

    return () => {
      window.removeEventListener('scroll', handleScroll)
    }
  }, [threshold])

  return scrollState
}

export default useScrollState
