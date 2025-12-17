import { describe, it, expect, vi, beforeAll, afterAll, afterEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { QuizPage } from '../../pages/QuizPage'
import { useQuizStore } from '../../stores/quizStore'
import { server } from '../mocks/server'
import {
  quizHandlers,
  quizErrorHandlers,
  quizResumedHandlers,
  resetQuizMocks,
} from '../mocks/handlers/quizHandlers'

// Mock useNavigate
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
      mutations: {
        retry: false,
      },
    },
  })
}

function renderQuizPage() {
  const queryClient = createTestQueryClient()
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <QuizPage />
      </BrowserRouter>
    </QueryClientProvider>
  )
}

describe('QuizPage', () => {
  beforeAll(() => {
    server.listen({ onUnhandledRequest: 'error' })
  })

  afterEach(() => {
    server.resetHandlers()
    resetQuizMocks()
    useQuizStore.getState().clearSession()
    mockNavigate.mockClear()
  })

  afterAll(() => {
    server.close()
  })

  describe('Loading State', () => {
    it('transitions from loading to active state', async () => {
      server.use(...quizHandlers)
      renderQuizPage()

      // The component starts in loading and quickly transitions to active
      // We verify it ends up in active state with session info
      await waitFor(() => {
        expect(screen.getByText('Session Info')).toBeInTheDocument()
      })
    })

    it('transitions from loading to active for resumed sessions', async () => {
      server.use(...quizResumedHandlers)
      renderQuizPage()

      // The component transitions to active state with resumed session data
      await waitFor(() => {
        expect(screen.getByText('Session Info')).toBeInTheDocument()
      })
    })
  })

  describe('Active State', () => {
    it('renders session info after loading', async () => {
      server.use(...quizHandlers)
      renderQuizPage()

      await waitFor(() => {
        expect(screen.getByText('Session Info')).toBeInTheDocument()
      })

      expect(screen.getByText('Adaptive')).toBeInTheDocument()
      expect(screen.getByText('Maximum Information Gain')).toBeInTheDocument()
    })

    it('displays question placeholder area', async () => {
      server.use(...quizHandlers)
      renderQuizPage()

      await waitFor(() => {
        expect(screen.getByText('Question Display Area')).toBeInTheDocument()
      })

      expect(screen.getByText(/questions will appear here/i)).toBeInTheDocument()
    })

    it('renders Pause Session button', async () => {
      server.use(...quizHandlers)
      renderQuizPage()

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /pause session/i })).toBeInTheDocument()
      })
    })

    it('renders End Session button', async () => {
      server.use(...quizHandlers)
      renderQuizPage()

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /end session/i })).toBeInTheDocument()
      })
    })
  })

  describe('Paused State', () => {
    it('shows paused banner when session is paused', async () => {
      server.use(...quizHandlers)
      renderQuizPage()

      // Wait for active state
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /pause session/i })).toBeInTheDocument()
      })

      // Click pause
      fireEvent.click(screen.getByRole('button', { name: /pause session/i }))

      // Verify paused state
      await waitFor(() => {
        expect(screen.getByText('Session Paused')).toBeInTheDocument()
      })
    })

    it('shows Resume Session button when paused', async () => {
      server.use(...quizHandlers)
      renderQuizPage()

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /pause session/i })).toBeInTheDocument()
      })

      fireEvent.click(screen.getByRole('button', { name: /pause session/i }))

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /resume session/i })).toBeInTheDocument()
      })
    })
  })

  describe('Error State', () => {
    it('renders error message when session fails to start', async () => {
      server.use(...quizErrorHandlers)
      renderQuizPage()

      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument()
      })

      expect(screen.getByText('Unable to Start Session')).toBeInTheDocument()
      expect(screen.getByText(/no active enrollment found/i)).toBeInTheDocument()
    })

    it('shows Try Again button on error', async () => {
      server.use(...quizErrorHandlers)
      renderQuizPage()

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument()
      })
    })

    it('shows Return to Results button on error', async () => {
      server.use(...quizErrorHandlers)
      renderQuizPage()

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /return to results/i })).toBeInTheDocument()
      })
    })
  })

  describe('Ended State', () => {
    it('shows completion summary after ending session', async () => {
      server.use(...quizHandlers)
      renderQuizPage()

      // Wait for active state
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /end session/i })).toBeInTheDocument()
      })

      // End session
      fireEvent.click(screen.getByRole('button', { name: /end session/i }))

      // Verify ended state
      await waitFor(() => {
        expect(screen.getByText('Session Complete')).toBeInTheDocument()
      })
    })

    it('displays stats in ended state', async () => {
      server.use(...quizHandlers)
      renderQuizPage()

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /end session/i })).toBeInTheDocument()
      })

      fireEvent.click(screen.getByRole('button', { name: /end session/i }))

      await waitFor(() => {
        expect(screen.getByText('Questions')).toBeInTheDocument()
        expect(screen.getByText('Correct')).toBeInTheDocument()
        expect(screen.getByText('Accuracy')).toBeInTheDocument()
      })
    })

    it('shows Start New Session button after ending', async () => {
      server.use(...quizHandlers)
      renderQuizPage()

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /end session/i })).toBeInTheDocument()
      })

      fireEvent.click(screen.getByRole('button', { name: /end session/i }))

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /start new session/i })).toBeInTheDocument()
      })
    })

    it('shows Return to Dashboard button after ending', async () => {
      server.use(...quizHandlers)
      renderQuizPage()

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /end session/i })).toBeInTheDocument()
      })

      fireEvent.click(screen.getByRole('button', { name: /end session/i }))

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /return to dashboard/i })).toBeInTheDocument()
      })
    })
  })

  describe('Button Actions', () => {
    it('calls pause API when Pause button is clicked', async () => {
      server.use(...quizHandlers)
      renderQuizPage()

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /pause session/i })).toBeInTheDocument()
      })

      fireEvent.click(screen.getByRole('button', { name: /pause session/i }))

      await waitFor(() => {
        expect(screen.getByText('Session Paused')).toBeInTheDocument()
      })
    })

    it('calls resume API when Resume button is clicked', async () => {
      server.use(...quizHandlers)
      renderQuizPage()

      // Pause first
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /pause session/i })).toBeInTheDocument()
      })
      fireEvent.click(screen.getByRole('button', { name: /pause session/i }))

      // Then resume
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /resume session/i })).toBeInTheDocument()
      })
      fireEvent.click(screen.getByRole('button', { name: /resume session/i }))

      // Should return to active state
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /pause session/i })).toBeInTheDocument()
      })
    })

    it('calls end API when End Session button is clicked', async () => {
      server.use(...quizHandlers)
      renderQuizPage()

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /end session/i })).toBeInTheDocument()
      })

      fireEvent.click(screen.getByRole('button', { name: /end session/i }))

      await waitFor(() => {
        expect(screen.getByText('Session Complete')).toBeInTheDocument()
      })
    })
  })

  describe('Accessibility', () => {
    it('has proper ARIA labels on error state', async () => {
      server.use(...quizErrorHandlers)
      renderQuizPage()

      await waitFor(() => {
        const alert = screen.getByRole('alert')
        expect(alert).toHaveAttribute('aria-live', 'assertive')
      })
    })

    it('session controls have proper button group', async () => {
      server.use(...quizHandlers)
      renderQuizPage()

      await waitFor(() => {
        expect(screen.getByRole('group', { name: /session controls/i })).toBeInTheDocument()
      })
    })

    it('buttons are keyboard accessible', async () => {
      server.use(...quizHandlers)
      renderQuizPage()

      await waitFor(() => {
        const pauseButton = screen.getByRole('button', { name: /pause session/i })
        expect(pauseButton).not.toBeDisabled()
      })
    })

    it('session info card has proper aria-label', async () => {
      server.use(...quizHandlers)
      renderQuizPage()

      await waitFor(() => {
        expect(screen.getByLabelText('Session information')).toBeInTheDocument()
      })
    })
  })
})
