import { useState, useEffect, useCallback } from 'react'

/**
 * Hook for managing countdown timers.
 * Used for rate limit cooldown display.
 */
export function useCountdown(onComplete?: () => void) {
  const [seconds, setSeconds] = useState<number | null>(null)

  useEffect(() => {
    if (seconds === null || seconds <= 0) {
      if (seconds === 0 && onComplete) {
        onComplete()
      }
      return
    }

    const timer = setInterval(() => {
      setSeconds((prev) => (prev !== null && prev > 0 ? prev - 1 : null))
    }, 1000)

    return () => clearInterval(timer)
  }, [seconds, onComplete])

  const start = useCallback((newSeconds: number) => {
    setSeconds(newSeconds)
  }, [])

  const reset = useCallback(() => {
    setSeconds(null)
  }, [])

  return { seconds, start, reset, isActive: seconds !== null && seconds > 0 }
}

/**
 * Format seconds as human-readable countdown string.
 * @example formatCountdown(125) => "2 minutes 5 seconds"
 * @example formatCountdown(45) => "45 seconds"
 */
export function formatCountdown(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60

  if (mins > 0 && secs > 0) {
    return `${mins} minute${mins !== 1 ? 's' : ''} ${secs} second${secs !== 1 ? 's' : ''}`
  } else if (mins > 0) {
    return `${mins} minute${mins !== 1 ? 's' : ''}`
  }
  return `${secs} second${secs !== 1 ? 's' : ''}`
}
