/**
 * ReadingDetailPage Tests
 * Story 5.8: Reading Item Detail View and Engagement Tracking
 */
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi, beforeAll, beforeEach, afterEach, afterAll } from 'vitest'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReadingDetailPage } from '../../pages/ReadingDetailPage'
import { useAuthStore } from '../../stores/authStore'
import { server } from '../mocks/server'
import { resetReadingQueueMocks, setMockQueueError } from '../mocks/handlers/readingQueueHandlers'

// Mock the auth store
vi.mock('../../stores/authStore', () => ({
  useAuthStore: vi.fn(),
}))

// Mock the navigation
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

function renderWithProviders(queueId: string) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[`/reading-library/${queueId}`]}>
        <Routes>
          <Route path="/reading-library/:queueId" element={<ReadingDetailPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  )
}

describe('ReadingDetailPage', () => {
  beforeAll(() => {
    server.listen({ onUnhandledRequest: 'bypass' })
  })

  afterAll(() => {
    server.close()
  })

  beforeEach(() => {
    vi.clearAllMocks()
    resetReadingQueueMocks()
    ;(useAuthStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      isAuthenticated: true,
      token: 'test-token',
    })
  })

  afterEach(() => {
    server.resetHandlers()
    resetReadingQueueMocks()
  })

  it('shows loading state initially', async () => {
    renderWithProviders('queue-1')

    // Should show skeleton loading
    expect(document.querySelector('.animate-pulse')).toBeInTheDocument()
  })

  it('displays reading content after loading', async () => {
    renderWithProviders('queue-1')

    await waitFor(() => {
      expect(screen.getByText('Introduction to Strategy Analysis')).toBeInTheDocument()
    })

    // Check for content
    expect(screen.getByText(/This is the full content/)).toBeInTheDocument()
    expect(screen.getByText('3.1')).toBeInTheDocument()
    expect(screen.getByText('Strategy Analysis')).toBeInTheDocument()
  })

  it('displays question context card', async () => {
    renderWithProviders('queue-1')

    await waitFor(() => {
      expect(screen.getByText('Introduction to Strategy Analysis')).toBeInTheDocument()
    })

    expect(screen.getByText('Recommended after incorrect answer')).toBeInTheDocument()
    expect(screen.getByText(/What technique is best/)).toBeInTheDocument()
  })

  it('displays Mark as Complete and Dismiss buttons', async () => {
    renderWithProviders('queue-1')

    await waitFor(() => {
      expect(screen.getByText('Introduction to Strategy Analysis')).toBeInTheDocument()
    })

    expect(screen.getByRole('button', { name: 'Mark as Complete' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Dismiss' })).toBeInTheDocument()
  })

  it('shows error state when item not found', async () => {
    setMockQueueError(true)
    renderWithProviders('non-existent')

    // Wait longer to account for retries in the hook
    // Error message comes from axios, showing the HTTP status
    await waitFor(
      () => {
        expect(screen.getByText(/404|not found/i)).toBeInTheDocument()
      },
      { timeout: 15000 }
    )

    // Should show Back to Library link
    expect(screen.getByRole('link', { name: /Back to Library/i })).toBeInTheDocument()
  }, 20000)

  it('shows Back to Library link', async () => {
    renderWithProviders('queue-1')

    await waitFor(() => {
      expect(screen.getByText('Introduction to Strategy Analysis')).toBeInTheDocument()
    })

    const backLinks = screen.getAllByText('Back to Library')
    expect(backLinks.length).toBeGreaterThan(0)
  })

  it('shows toast after marking complete', async () => {
    renderWithProviders('queue-1')

    await waitFor(() => {
      expect(screen.getByText('Introduction to Strategy Analysis')).toBeInTheDocument()
    })

    const markCompleteButton = screen.getByRole('button', { name: 'Mark as Complete' })
    fireEvent.click(markCompleteButton)

    await waitFor(() => {
      expect(screen.getByText('Marked as complete!')).toBeInTheDocument()
    })
  })

  it('shows dismiss button and it is clickable', async () => {
    renderWithProviders('queue-1')

    await waitFor(() => {
      expect(screen.getByText('Introduction to Strategy Analysis')).toBeInTheDocument()
    })

    const dismissButton = screen.getByRole('button', { name: 'Dismiss' })
    expect(dismissButton).toBeEnabled()

    fireEvent.click(dismissButton)

    await waitFor(() => {
      expect(screen.getByText('Item dismissed.')).toBeInTheDocument()
    })
  })
})
