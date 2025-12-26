/**
 * Reading Badge Integration Tests
 * Story 5.6: Silent Badge Updates in Navigation
 *
 * Tests the integration between the Navigation component,
 * useReadingStats hook, and the reading stats API.
 */
import { describe, it, expect, beforeAll, afterAll, afterEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Navigation } from '../../components/layout/Navigation'
import { useAuthStore } from '../../stores/authStore'
import { useReadingStore } from '../../stores/readingStore'
import { server } from '../mocks/server'
import {
  setMockReadingStats,
  setMockReadingStatsError,
  resetReadingStatsMocks,
} from '../mocks/handlers/readingStatsHandlers'

// Create a fresh QueryClient for each test
function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        staleTime: 0,
      },
    },
  })
}

// Wrapper component with all providers
function renderWithProviders({ route = '/quiz' } = {}) {
  const queryClient = createTestQueryClient()

  const router = createMemoryRouter(
    [
      {
        path: '/quiz',
        element: <Navigation enablePolling={true} />,
      },
      {
        path: '/reading-library',
        element: <div data-testid="reading-library-page">Reading Library</div>,
      },
    ],
    { initialEntries: [route] }
  )

  return {
    ...render(
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
      </QueryClientProvider>
    ),
    queryClient,
    router,
  }
}

describe('Reading Badge Integration', () => {
  beforeAll(() => {
    server.listen({ onUnhandledRequest: 'bypass' })
    // Mock authenticated user
    useAuthStore.setState({
      user: { id: 'user-1', email: 'test@example.com', created_at: new Date().toISOString() },
      token: 'mock-token',
      isAuthenticated: true,
    })
  })

  afterAll(() => {
    server.close()
  })

  afterEach(() => {
    server.resetHandlers()
    resetReadingStatsMocks()
    useReadingStore.getState().reset()
    vi.clearAllTimers()
  })

  describe('badge display', () => {
    it('displays badge with correct count after API response', async () => {
      setMockReadingStats(7, 3)
      renderWithProviders()

      await waitFor(() => {
        expect(screen.getByRole('status')).toBeInTheDocument()
        expect(screen.getByText('7')).toBeInTheDocument()
      })
    })

    it('does not display badge when count is zero', async () => {
      setMockReadingStats(0, 0)
      renderWithProviders()

      // Wait for potential render
      await new Promise((resolve) => setTimeout(resolve, 100))

      // Badge should not be in the document when count is 0
      expect(screen.queryByRole('status')).not.toBeInTheDocument()
    })

    it('updates badge when count changes', async () => {
      setMockReadingStats(3, 1)
      const { queryClient } = renderWithProviders()

      await waitFor(() => {
        expect(screen.getByText('3')).toBeInTheDocument()
      })

      // Simulate count update
      setMockReadingStats(5, 2)
      await queryClient.invalidateQueries({ queryKey: ['readingStats'] })

      await waitFor(() => {
        expect(screen.getByText('5')).toBeInTheDocument()
      })
    })
  })

  describe('error handling', () => {
    it('keeps displaying last known count on error (stale data)', async () => {
      // Start with successful response
      setMockReadingStats(5, 2)
      const { queryClient } = renderWithProviders()

      await waitFor(() => {
        expect(screen.getByText('5')).toBeInTheDocument()
      })

      // Now make the endpoint fail
      setMockReadingStatsError(true)
      await queryClient.invalidateQueries({ queryKey: ['readingStats'] })

      // Badge should still show the last known count (stale data preserved)
      await waitFor(() => {
        // The badge should still be visible with the old count
        expect(screen.getByRole('status')).toBeInTheDocument()
      })
    })
  })

  describe('accessibility', () => {
    it('has accessible aria-label on badge', async () => {
      setMockReadingStats(5, 2)
      renderWithProviders()

      await waitFor(() => {
        const badge = screen.getByRole('status')
        expect(badge).toHaveAttribute('aria-label', '5 unread reading items')
      })
    })

    it('uses singular grammar for single item', async () => {
      setMockReadingStats(1, 0)
      renderWithProviders()

      await waitFor(() => {
        const badge = screen.getByRole('status')
        expect(badge).toHaveAttribute('aria-label', '1 unread reading item')
      })
    })

    it('reading library link has accessible label', async () => {
      setMockReadingStats(7, 3)
      renderWithProviders()

      await waitFor(() => {
        const link = screen.getByRole('link', {
          name: /reading library with 7 unread items/i,
        })
        expect(link).toBeInTheDocument()
      })
    })
  })

  describe('navigation', () => {
    it('renders Reading Library link', async () => {
      setMockReadingStats(5, 2)
      renderWithProviders()

      await waitFor(() => {
        expect(screen.getByText('Reading')).toBeInTheDocument()
      })
    })

    it('has correct href to reading library page', async () => {
      setMockReadingStats(5, 2)
      renderWithProviders()

      await waitFor(() => {
        const link = screen.getByRole('link', { name: /reading/i })
        expect(link).toHaveAttribute('href', '/reading-library')
      })
    })
  })

  describe('authentication', () => {
    it('does not render when user is not authenticated', () => {
      useAuthStore.setState({
        user: null,
        token: null,
        isAuthenticated: false,
      })

      renderWithProviders()

      // Navigation should not render when not authenticated
      expect(screen.queryByText('Reading')).not.toBeInTheDocument()

      // Restore authenticated state for other tests
      useAuthStore.setState({
        user: {
          id: 'user-1',
          email: 'test@example.com',
          created_at: new Date().toISOString(),
        },
        token: 'mock-token',
        isAuthenticated: true,
      })
    })
  })
})
