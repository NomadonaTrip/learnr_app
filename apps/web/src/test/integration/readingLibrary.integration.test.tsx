/**
 * Reading Library Page Integration Tests
 * Story 5.7: Reading Library Page with Queue Display
 *
 * Tests the integration between the ReadingLibraryPage component,
 * useReadingQueue hook, and the reading queue API.
 */
import { describe, it, expect, beforeAll, afterAll, afterEach, vi } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReadingLibraryPage } from '../../pages/ReadingLibraryPage'
import { useAuthStore } from '../../stores/authStore'
import { server } from '../mocks/server'
import {
  setMockQueueItems,
  setMockQueueError,
  setMockQueueDelay,
  resetReadingQueueMocks,
} from '../mocks/handlers/readingQueueHandlers'

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
function renderWithProviders() {
  const queryClient = createTestQueryClient()

  const router = createMemoryRouter(
    [
      {
        path: '/reading-library',
        element: <ReadingLibraryPage />,
      },
      {
        path: '/reading-library/:queueId',
        element: <div data-testid="reading-detail-page">Reading Detail</div>,
      },
    ],
    { initialEntries: ['/reading-library'] }
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

describe('Reading Library Page Integration', () => {
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
    resetReadingQueueMocks()
    vi.clearAllTimers()
  })

  describe('page rendering', () => {
    it('renders the page header', async () => {
      renderWithProviders()

      expect(screen.getByText('Reading Library')).toBeInTheDocument()
      expect(
        screen.getByText('Study materials recommended based on your quiz performance')
      ).toBeInTheDocument()
    })

    it('renders filter bar with status tabs', async () => {
      renderWithProviders()

      await waitFor(() => {
        expect(screen.getByRole('tab', { name: 'Unread' })).toBeInTheDocument()
        expect(screen.getByRole('tab', { name: 'Reading' })).toBeInTheDocument()
        expect(screen.getByRole('tab', { name: 'Completed' })).toBeInTheDocument()
      })
    })
  })

  describe('loading state', () => {
    it('shows skeleton cards while loading', async () => {
      setMockQueueDelay(500)
      renderWithProviders()

      // Should show skeleton cards
      const skeletons = document.querySelectorAll('.animate-pulse')
      expect(skeletons.length).toBeGreaterThan(0)
    })
  })

  describe('data display', () => {
    it('displays queue items from API', async () => {
      renderWithProviders()

      await waitFor(() => {
        expect(screen.getByText('3.1: Introduction to Strategy Analysis')).toBeInTheDocument()
        expect(screen.getByText('4.2: Elicitation Techniques Overview')).toBeInTheDocument()
        expect(screen.getByText('5.1: Requirements Traceability')).toBeInTheDocument()
      })
    })

    it('displays priority badges correctly', async () => {
      renderWithProviders()

      await waitFor(() => {
        const highBadges = screen.getAllByText('High')
        const mediumBadges = screen.getAllByText('Medium')

        expect(highBadges.length).toBe(2)
        expect(mediumBadges.length).toBe(1)
      })
    })

    it('displays knowledge area labels', async () => {
      renderWithProviders()

      await waitFor(() => {
        expect(screen.getByText('Strategy Analysis')).toBeInTheDocument()
        expect(screen.getByText('Elicitation and Collaboration')).toBeInTheDocument()
        expect(screen.getByText('Requirements Life Cycle Management')).toBeInTheDocument()
      })
    })

    it('displays question preview context when available', async () => {
      renderWithProviders()

      await waitFor(() => {
        expect(
          screen.getByText(/What technique is best for stakeholder identification/)
        ).toBeInTheDocument()
      })
    })
  })

  describe('empty state', () => {
    it('shows empty state when no items', async () => {
      setMockQueueItems([])
      renderWithProviders()

      await waitFor(() => {
        expect(screen.getByText('Your reading library is empty')).toBeInTheDocument()
        expect(
          screen.getByText('Complete quiz sessions to get personalized recommendations!')
        ).toBeInTheDocument()
      })
    })
  })

  describe('error state', () => {
    it('shows error message and retry button on API failure', async () => {
      // Set error state BEFORE render
      setMockQueueError(true)

      renderWithProviders()

      // Wait for query to fail and error state to render
      await waitFor(
        () => {
          expect(screen.getByText('Unable to load your reading queue.')).toBeInTheDocument()
          expect(screen.getByRole('button', { name: 'Try Again' })).toBeInTheDocument()
        },
        { timeout: 5000 }
      )
    })

    it('retries when Try Again button is clicked', async () => {
      // Set error state BEFORE render
      setMockQueueError(true)

      renderWithProviders()

      // Wait for error state
      await waitFor(
        () => {
          expect(screen.getByText('Unable to load your reading queue.')).toBeInTheDocument()
        },
        { timeout: 5000 }
      )

      // Fix the error and click retry
      setMockQueueError(false)
      fireEvent.click(screen.getByRole('button', { name: 'Try Again' }))

      await waitFor(
        () => {
          expect(screen.getByText('3.1: Introduction to Strategy Analysis')).toBeInTheDocument()
        },
        { timeout: 5000 }
      )
    })
  })

  describe('filtering', () => {
    it('filters by status when tab is clicked', async () => {
      setMockQueueItems([
        {
          queue_id: 'queue-completed',
          chunk_id: 'chunk-completed',
          title: 'Completed Reading',
          preview: 'This is a completed reading item...',
          babok_section: '2.1',
          ka_name: 'BA Planning',
          ka_id: 'planning',
          relevance_score: null,
          priority: 'Low',
          status: 'completed',
          word_count: 400,
          estimated_read_minutes: 2,
          question_preview: null,
          was_incorrect: true,
          added_at: '2025-01-10T10:00:00Z',
        },
      ])
      renderWithProviders()

      // Click completed tab
      await waitFor(() => {
        expect(screen.getByRole('tab', { name: 'Completed' })).toBeInTheDocument()
      })
      fireEvent.click(screen.getByRole('tab', { name: 'Completed' }))

      await waitFor(() => {
        expect(screen.getByText('2.1: Completed Reading')).toBeInTheDocument()
      })
    })
  })

  describe('navigation', () => {
    it('navigates to detail view when Read Now is clicked', async () => {
      const { router } = renderWithProviders()

      await waitFor(() => {
        expect(screen.getByText('3.1: Introduction to Strategy Analysis')).toBeInTheDocument()
      })

      // Click the first Read Now button
      const readNowButtons = screen.getAllByRole('button', { name: 'Read Now' })
      fireEvent.click(readNowButtons[0])

      // Should navigate to detail page
      await waitFor(() => {
        expect(router.state.location.pathname).toMatch(/\/reading-library\/queue-1/)
      })
    })
  })

  describe('accessibility', () => {
    it('reading cards have article role', async () => {
      renderWithProviders()

      await waitFor(() => {
        const articles = screen.getAllByRole('article')
        expect(articles.length).toBe(3)
      })
    })

    it('reading cards are focusable', async () => {
      renderWithProviders()

      await waitFor(() => {
        const articles = screen.getAllByRole('article')
        articles.forEach((article) => {
          expect(article).toHaveAttribute('tabIndex', '0')
        })
      })
    })
  })
})
