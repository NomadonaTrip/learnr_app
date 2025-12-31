/**
 * Navigation Component
 * Story 5.6: Silent Badge Updates in Navigation
 *
 * Top navigation bar for authenticated pages.
 * Includes Reading Library link with badge showing unread count.
 */
import { Link, useLocation } from 'react-router-dom'
import { ReadingBadge } from './ReadingBadge'
import { useReadingStats } from '../../hooks/useReadingStats'
import { useAuthStore } from '../../stores/authStore'

interface NavigationProps {
  /** Whether to enable reading stats polling (default: true) */
  enablePolling?: boolean
}

/**
 * Navigation bar for authenticated app pages.
 *
 * Features:
 * - Logo/home link
 * - Dashboard link to diagnostic results/progress hub
 * - Reading Library link with unread badge
 * - Polling for reading stats updates during quiz sessions
 */
export function Navigation({ enablePolling = true }: NavigationProps) {
  const location = useLocation()
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const { unreadCount } = useReadingStats({ enabled: enablePolling })

  // Don't render if not authenticated
  if (!isAuthenticated) {
    return null
  }

  const isQuizPage = location.pathname === '/quiz'

  return (
    <nav
      className="sticky top-0 z-40 bg-white border-b border-gray-200 shadow-sm"
      role="navigation"
      aria-label="Main navigation"
    >
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-14 items-center justify-between">
          {/* Logo */}
          <Link
            to="/"
            className="flex items-center gap-2 text-gray-900 hover:text-gray-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2 rounded-lg px-2 py-1"
            aria-label="LearnR - Home"
          >
            <span className="text-lg font-semibold tracking-tight">LearnR</span>
          </Link>

          {/* Navigation Links */}
          <div className="flex items-center gap-6">
            {/* Dashboard Link */}
            <Link
              to="/diagnostic/results"
              className="flex items-center gap-1 text-sm font-medium text-gray-600 hover:text-gray-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2 rounded-lg px-3 py-2"
              aria-label="Dashboard"
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
                />
              </svg>
              <span>Dashboard</span>
            </Link>

            {/* Reading Library Link with Badge */}
            <Link
              to="/reading-library"
              className="relative flex items-center gap-1 text-sm font-medium text-gray-600 hover:text-gray-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2 rounded-lg px-3 py-2"
              aria-label={
                unreadCount > 0
                  ? `Reading Library with ${unreadCount} unread ${unreadCount === 1 ? 'item' : 'items'}`
                  : 'Reading Library'
              }
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
                />
              </svg>
              <span>Reading</span>
              <ReadingBadge count={unreadCount} />
            </Link>

            {/* Back to Quiz button (when not on quiz page) */}
            {!isQuizPage && (
              <Link
                to="/quiz"
                className="px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-[14px] hover:bg-primary-700 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2"
              >
                Continue Quiz
              </Link>
            )}
          </div>
        </div>
      </div>
    </nav>
  )
}

export default Navigation
