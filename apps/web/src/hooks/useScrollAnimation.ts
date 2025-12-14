import { useEffect, useRef, useState } from 'react'

interface UseScrollAnimationOptions {
  threshold?: number
  rootMargin?: string
  triggerOnce?: boolean
}

/**
 * Hook for scroll-triggered animations using Intersection Observer.
 * Returns a ref to attach to the element and a boolean indicating if it's visible.
 */
export function useScrollAnimation<T extends HTMLElement = HTMLDivElement>(
  options: UseScrollAnimationOptions = {}
): [React.RefObject<T>, boolean] {
  const { threshold = 0.1, rootMargin = '0px', triggerOnce = true } = options
  const ref = useRef<T>(null)
  const [isVisible, setIsVisible] = useState(false)

  useEffect(() => {
    const element = ref.current
    if (!element) return

    // Check for reduced motion preference
    const prefersReducedMotion = window.matchMedia(
      '(prefers-reduced-motion: reduce)'
    ).matches

    if (prefersReducedMotion) {
      setIsVisible(true)
      return
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true)
          if (triggerOnce) {
            observer.unobserve(element)
          }
        } else if (!triggerOnce) {
          setIsVisible(false)
        }
      },
      { threshold, rootMargin }
    )

    observer.observe(element)

    return () => {
      observer.disconnect()
    }
  }, [threshold, rootMargin, triggerOnce])

  return [ref, isVisible]
}

interface UseStaggeredAnimationOptions extends UseScrollAnimationOptions {
  staggerDelay?: number
  itemCount: number
}

/**
 * Hook for staggered scroll animations on a group of items.
 * Returns a ref for the container and an array of visibility states with stagger delays.
 */
export function useStaggeredAnimation<T extends HTMLElement = HTMLDivElement>(
  options: UseStaggeredAnimationOptions
): [React.RefObject<T>, boolean[], number[]] {
  const { itemCount, staggerDelay = 75, ...scrollOptions } = options
  const [containerRef, isContainerVisible] = useScrollAnimation<T>(scrollOptions)
  const [visibleItems, setVisibleItems] = useState<boolean[]>(
    Array(itemCount).fill(false)
  )
  const [delays, setDelays] = useState<number[]>([])

  useEffect(() => {
    setDelays(Array.from({ length: itemCount }, (_, i) => i * staggerDelay))
  }, [itemCount, staggerDelay])

  useEffect(() => {
    if (!isContainerVisible) {
      setVisibleItems(Array(itemCount).fill(false))
      return
    }

    // Check for reduced motion preference
    const prefersReducedMotion = window.matchMedia(
      '(prefers-reduced-motion: reduce)'
    ).matches

    if (prefersReducedMotion) {
      setVisibleItems(Array(itemCount).fill(true))
      return
    }

    // Stagger the visibility of each item
    const timeouts: ReturnType<typeof setTimeout>[] = []

    for (let i = 0; i < itemCount; i++) {
      const timeout = setTimeout(() => {
        setVisibleItems((prev) => {
          const next = [...prev]
          next[i] = true
          return next
        })
      }, i * staggerDelay)
      timeouts.push(timeout)
    }

    return () => {
      timeouts.forEach((t) => clearTimeout(t))
    }
  }, [isContainerVisible, itemCount, staggerDelay])

  return [containerRef, visibleItems, delays]
}

/**
 * Hook for detecting if an element is in the viewport.
 * Simpler version without animation state management.
 */
export function useInView<T extends HTMLElement = HTMLDivElement>(
  options: UseScrollAnimationOptions = {}
): [React.RefObject<T>, boolean] {
  return useScrollAnimation<T>(options)
}

/**
 * Animation constants matching the design system
 */
export const ANIMATION_CONFIG = {
  spring: {
    damping: 30,
    stiffness: 400,
  },
  staggerDelay: 75,
  duration: {
    fast: 200,
    normal: 300,
    slow: 500,
  },
} as const
