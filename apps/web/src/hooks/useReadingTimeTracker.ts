/**
 * useReadingTimeTracker Hook
 * Story 5.8: Reading Item Detail View and Engagement Tracking
 *
 * Tracks reading time and sends engagement updates to the API.
 * Handles tab visibility, page close, and component unmount.
 */
import { useEffect, useRef, useCallback } from 'react'
import { updateEngagement } from '../services/readingService'

const MIN_TIME_THRESHOLD = 3 // Minimum 3 seconds to filter accidental opens
const MAX_TIME_CAP = 1800 // Maximum 30 minutes per session

interface UseReadingTimeTrackerOptions {
  queueId: string
  enabled?: boolean
}

/**
 * Hook for tracking reading time and sending engagement updates.
 *
 * Features:
 * - Tracks time since component mount
 * - Pauses timer when tab is hidden (Page Visibility API)
 * - Sends engagement update on unmount or page close
 * - Uses sendBeacon for reliable delivery on page close
 * - Caps time at 30 minutes per session
 * - Minimum 3 second threshold to filter accidental opens
 *
 * @param options - Options with queueId and enabled flag
 *
 * @example
 * ```tsx
 * useReadingTimeTracker({ queueId: 'abc-123', enabled: true })
 * ```
 */
export function useReadingTimeTracker({
  queueId,
  enabled = true,
}: UseReadingTimeTrackerOptions): void {
  const startTimeRef = useRef<number>(0)
  const accumulatedTimeRef = useRef<number>(0)
  const isVisibleRef = useRef<boolean>(true)
  const hasSentRef = useRef<boolean>(false)

  // Calculate total time spent
  const calculateTimeSpent = useCallback((): number => {
    const currentSession = isVisibleRef.current
      ? performance.now() - startTimeRef.current
      : 0
    const totalMs = accumulatedTimeRef.current + currentSession
    return Math.floor(totalMs / 1000) // Convert to seconds
  }, [])

  // Send engagement update
  const sendEngagement = useCallback(async () => {
    if (hasSentRef.current || !enabled) return

    const timeSpent = calculateTimeSpent()

    // Skip if below minimum threshold
    if (timeSpent < MIN_TIME_THRESHOLD) return

    // Cap at maximum
    const cappedTime = Math.min(timeSpent, MAX_TIME_CAP)

    hasSentRef.current = true

    try {
      await updateEngagement(queueId, cappedTime)
    } catch {
      // Silent fail - engagement tracking shouldn't block user experience
      console.warn('Failed to send reading engagement')
    }
  }, [queueId, enabled, calculateTimeSpent])

  // Send engagement using sendBeacon for page close
  const sendEngagementBeacon = useCallback(() => {
    if (hasSentRef.current || !enabled) return

    const timeSpent = calculateTimeSpent()

    if (timeSpent < MIN_TIME_THRESHOLD) return

    const cappedTime = Math.min(timeSpent, MAX_TIME_CAP)

    hasSentRef.current = true

    // Use sendBeacon for reliable delivery on page close
    const data = JSON.stringify({ time_spent_seconds: cappedTime })
    navigator.sendBeacon(`/api/v1/reading/queue/${queueId}/engagement`, data)
  }, [queueId, enabled, calculateTimeSpent])

  useEffect(() => {
    if (!enabled) return

    // Initialize start time
    startTimeRef.current = performance.now()
    accumulatedTimeRef.current = 0
    isVisibleRef.current = true
    hasSentRef.current = false

    // Handle visibility changes (tab switch)
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'hidden') {
        // Tab hidden - pause and accumulate
        if (isVisibleRef.current) {
          accumulatedTimeRef.current +=
            performance.now() - startTimeRef.current
        }
        isVisibleRef.current = false
      } else {
        // Tab visible - resume
        startTimeRef.current = performance.now()
        isVisibleRef.current = true
      }
    }

    // Handle page unload
    const handleBeforeUnload = () => {
      sendEngagementBeacon()
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    window.addEventListener('beforeunload', handleBeforeUnload)

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange)
      window.removeEventListener('beforeunload', handleBeforeUnload)

      // Send engagement on unmount (navigation away)
      sendEngagement()
    }
  }, [queueId, enabled, sendEngagement, sendEngagementBeacon])
}
