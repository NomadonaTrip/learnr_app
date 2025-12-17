import { describe, it, expect, vi, beforeAll, afterAll, afterEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { QuizPage } from '../../pages/QuizPage'
import { useQuizStore } from '../../stores/quizStore'
import { useAuthStore } from '../../stores/authStore'
import { server } from '../mocks/server'
import {
  quizHandlers,
  quizResumedHandlers,
  resetQuizMocks,
} from '../mocks/handlers/quizHandlers'
import { http, HttpResponse } from 'msw'

// Mock navigation for testing route changes
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
      queries: { retry: false },
      mutations: { retry: false },
    },
  })
}

function renderWithRouter(
  initialRoute: string,
  routes: Array<{ path: string; element: React.ReactNode }>
) {
  const queryClient = createTestQueryClient()
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[initialRoute]}>
        <Routes>
          {routes.map(({ path, element }) => (
            <Route key={path} path={path} element={element} />
          ))}
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  )
}

describe('Quiz Session Integration', () => {
  beforeAll(() => {
    server.listen({ onUnhandledRequest: 'error' })
    // Set up authenticated state
    useAuthStore.getState().login(
      {
        id: 'user-123',
        email: 'test@example.com',
        name: 'Test User',
        created_at: '2025-12-17T00:00:00Z',
      },
      'test-token'
    )
  })

  afterEach(() => {
    server.resetHandlers()
    resetQuizMocks()
    useQuizStore.getState().clearSession()
    mockNavigate.mockClear()
  })

  afterAll(() => {
    server.close()
    useAuthStore.getState().logout()
  })

  describe('Navigation', () => {
    it('quiz page is accessible at /quiz route', async () => {
      server.use(...quizHandlers)
      renderWithRouter('/quiz', [{ path: '/quiz', element: <QuizPage /> }])

      // Verify quiz page loads and displays session info
      await waitFor(() => {
        expect(screen.getByText('Session Info')).toBeInTheDocument()
      })
    })
  })

  describe('Session Start Flow', () => {
    it('starts new session and displays active state', async () => {
      server.use(...quizHandlers)
      renderWithRouter('/quiz', [{ path: '/quiz', element: <QuizPage /> }])

      // Wait for loading to finish
      await waitFor(() => {
        expect(screen.getByText('Session Info')).toBeInTheDocument()
      })

      // Verify session info is displayed
      expect(screen.getByText('Adaptive')).toBeInTheDocument()
      expect(screen.getByText('Maximum Information Gain')).toBeInTheDocument()
    })

    it('resumes existing session and shows session info', async () => {
      server.use(...quizResumedHandlers)
      renderWithRouter('/quiz', [{ path: '/quiz', element: <QuizPage /> }])

      // After loading, session info shows resumed session data
      await waitFor(() => {
        expect(screen.getByText('Session Info')).toBeInTheDocument()
      })
    })
  })

  describe('Pause/Resume Flow', () => {
    it('pauses and resumes session correctly', async () => {
      server.use(...quizHandlers)
      renderWithRouter('/quiz', [{ path: '/quiz', element: <QuizPage /> }])

      // Wait for active state
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /pause session/i })).toBeInTheDocument()
      })

      // Pause session
      fireEvent.click(screen.getByRole('button', { name: /pause session/i }))

      // Verify paused state
      await waitFor(() => {
        expect(screen.getByText('Session Paused')).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /resume session/i })).toBeInTheDocument()
      })

      // Resume session
      fireEvent.click(screen.getByRole('button', { name: /resume session/i }))

      // Verify back to active state
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /pause session/i })).toBeInTheDocument()
      })
    })
  })

  describe('End Session Flow', () => {
    it('ends session and shows completion summary', async () => {
      server.use(...quizHandlers)
      renderWithRouter('/quiz', [{ path: '/quiz', element: <QuizPage /> }])

      // Wait for active state
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /end session/i })).toBeInTheDocument()
      })

      // End session
      fireEvent.click(screen.getByRole('button', { name: /end session/i }))

      // Verify ended state with summary
      await waitFor(() => {
        expect(screen.getByText('Session Complete')).toBeInTheDocument()
      })

      // Verify stats are shown
      expect(screen.getByText('10')).toBeInTheDocument() // total questions
      expect(screen.getByText('7')).toBeInTheDocument() // correct count
      expect(screen.getByText('70%')).toBeInTheDocument() // accuracy
    })

    it('can start new session after ending', async () => {
      server.use(...quizHandlers)
      renderWithRouter('/quiz', [{ path: '/quiz', element: <QuizPage /> }])

      // End session
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /end session/i })).toBeInTheDocument()
      })
      fireEvent.click(screen.getByRole('button', { name: /end session/i }))

      // Wait for ended state
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /start new session/i })).toBeInTheDocument()
      })

      // Start new session
      fireEvent.click(screen.getByRole('button', { name: /start new session/i }))

      // Should show loading then active state again
      await waitFor(() => {
        expect(screen.getByText('Session Info')).toBeInTheDocument()
      })
    })

    it('navigates to dashboard when Return to Dashboard is clicked', async () => {
      server.use(...quizHandlers)
      renderWithRouter('/quiz', [{ path: '/quiz', element: <QuizPage /> }])

      // End session
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /end session/i })).toBeInTheDocument()
      })
      fireEvent.click(screen.getByRole('button', { name: /end session/i }))

      // Wait for ended state
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /return to dashboard/i })).toBeInTheDocument()
      })

      // Click return to dashboard
      fireEvent.click(screen.getByRole('button', { name: /return to dashboard/i }))

      // Verify navigate was called
      expect(mockNavigate).toHaveBeenCalledWith('/diagnostic/results')
    })
  })

  describe('Error Handling', () => {
    it('shows error state when no enrollment exists', async () => {
      server.use(
        http.post('*/quiz/session/start', () => {
          return HttpResponse.json(
            { detail: 'No active enrollment found. Please complete the diagnostic first.' },
            { status: 400 }
          )
        })
      )

      renderWithRouter('/quiz', [{ path: '/quiz', element: <QuizPage /> }])

      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument()
        expect(screen.getByText(/no active enrollment found/i)).toBeInTheDocument()
      })
    })

    it('allows retry after error', async () => {
      let requestCount = 0
      server.use(
        http.post('*/quiz/session/start', () => {
          requestCount++
          if (requestCount === 1) {
            return HttpResponse.json(
              { detail: 'Temporary error' },
              { status: 500 }
            )
          }
          return HttpResponse.json({
            session_id: 'session-uuid-123',
            session_type: 'adaptive',
            question_strategy: 'max_info_gain',
            is_resumed: false,
            status: 'active',
            started_at: '2025-12-17T10:00:00Z',
            total_questions: 0,
            correct_count: 0,
            first_question: null,
          })
        })
      )

      renderWithRouter('/quiz', [{ path: '/quiz', element: <QuizPage /> }])

      // Wait for error
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument()
      })

      // Retry
      fireEvent.click(screen.getByRole('button', { name: /try again/i }))

      // Should succeed on retry
      await waitFor(() => {
        expect(screen.getByText('Session Info')).toBeInTheDocument()
      })
    })
  })
})
