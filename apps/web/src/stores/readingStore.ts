/**
 * Reading Store
 * Story 5.6: Silent Badge Updates in Navigation
 *
 * Zustand store for reading queue state management.
 * Stores unread counts for badge display.
 */
import { create } from 'zustand'

interface ReadingState {
  /** Count of unread items in the reading queue */
  unreadCount: number
  /** Count of high-priority unread items */
  highPriorityCount: number
  /** Whether data has been loaded at least once */
  isInitialized: boolean
  /** Update counts from API response */
  setStats: (unreadCount: number, highPriorityCount: number) => void
  /** Reset store to initial state */
  reset: () => void
}

const initialState = {
  unreadCount: 0,
  highPriorityCount: 0,
  isInitialized: false,
}

/**
 * Zustand store for reading queue statistics.
 * Used by the navigation badge to display unread counts.
 *
 * Note: Not persisted - fetched fresh on each session.
 */
export const useReadingStore = create<ReadingState>()((set) => ({
  ...initialState,

  setStats: (unreadCount, highPriorityCount) =>
    set({
      unreadCount,
      highPriorityCount,
      isInitialized: true,
    }),

  reset: () => set(initialState),
}))
