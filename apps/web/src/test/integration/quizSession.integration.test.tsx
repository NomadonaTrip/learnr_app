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
  setMockNextAnswerCorrect,
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

  describe('Answer Submission Flow', () => {
    it('selects answer and enables submit button', async () => {
      server.use(...quizHandlers)

      renderWithRouter('/quiz', [{ path: '/quiz', element: <QuizPage /> }])

      // Wait for question to load (using default mock question)
      await waitFor(() => {
        expect(screen.getByText('Default mock question?')).toBeInTheDocument()
      })

      // Select an answer
      fireEvent.click(screen.getByRole('radio', { name: /option a/i }))

      // Submit button should appear
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /submit answer/i })).toBeInTheDocument()
      })
    })

    it('shows correct feedback after correct answer submission', async () => {
      setMockNextAnswerCorrect(true)
      server.use(...quizHandlers)

      renderWithRouter('/quiz', [{ path: '/quiz', element: <QuizPage /> }])

      // Wait for question
      await waitFor(() => {
        expect(screen.getByText('Default mock question?')).toBeInTheDocument()
      })

      // Select answer and submit
      fireEvent.click(screen.getByRole('radio', { name: /option a/i }))
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /submit answer/i })).toBeInTheDocument()
      })
      fireEvent.click(screen.getByRole('button', { name: /submit answer/i }))

      // Should show correct feedback
      await waitFor(() => {
        expect(screen.getByText('Correct!')).toBeInTheDocument()
      })

      expect(screen.getByRole('alert')).toHaveClass('bg-green-50')
    })

    it('shows incorrect feedback after wrong answer submission', async () => {
      setMockNextAnswerCorrect(false)
      server.use(...quizHandlers)

      renderWithRouter('/quiz', [{ path: '/quiz', element: <QuizPage /> }])

      // Wait for question
      await waitFor(() => {
        expect(screen.getByText('Default mock question?')).toBeInTheDocument()
      })

      // Select wrong answer and submit
      fireEvent.click(screen.getByRole('radio', { name: /option c/i }))
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /submit answer/i })).toBeInTheDocument()
      })
      fireEvent.click(screen.getByRole('button', { name: /submit answer/i }))

      // Should show incorrect feedback with correct answer
      await waitFor(() => {
        expect(screen.getByText(/incorrect.*correct answer is B/i)).toBeInTheDocument()
      })

      expect(screen.getByRole('alert')).toHaveClass('bg-orange-50')
    })

    it('proceeds to next question after clicking Next Question button', async () => {
      setMockNextAnswerCorrect(true)
      server.use(...quizHandlers)

      renderWithRouter('/quiz', [{ path: '/quiz', element: <QuizPage /> }])

      // Wait for first question
      await waitFor(() => {
        expect(screen.getByText('Default mock question?')).toBeInTheDocument()
      })

      // Answer and submit
      fireEvent.click(screen.getByRole('radio', { name: /option a/i }))
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /submit answer/i })).toBeInTheDocument()
      })
      fireEvent.click(screen.getByRole('button', { name: /submit answer/i }))

      // Wait for feedback
      await waitFor(() => {
        expect(screen.getByText('Correct!')).toBeInTheDocument()
      })

      // Click Next Question
      fireEvent.click(screen.getByRole('button', { name: /next question/i }))

      // Feedback should be cleared and question should reload
      await waitFor(() => {
        expect(screen.queryByText('Correct!')).not.toBeInTheDocument()
      })
    })

    it('submit button transitions to feedback after submission', async () => {
      setMockNextAnswerCorrect(true)
      server.use(...quizHandlers)

      renderWithRouter('/quiz', [{ path: '/quiz', element: <QuizPage /> }])

      // Wait for question
      await waitFor(() => {
        expect(screen.getByText('Default mock question?')).toBeInTheDocument()
      })

      // Select answer and submit
      fireEvent.click(screen.getByRole('radio', { name: /option a/i }))
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /submit answer/i })).toBeInTheDocument()
      })

      // Submit button should be enabled
      expect(screen.getByRole('button', { name: /submit answer/i })).not.toBeDisabled()

      fireEvent.click(screen.getByRole('button', { name: /submit answer/i }))

      // After submission, feedback should appear and submit button should be gone
      await waitFor(() => {
        expect(screen.getByText('Correct!')).toBeInTheDocument()
        expect(screen.queryByRole('button', { name: /submit answer/i })).not.toBeInTheDocument()
      })
    })
  })

  /**
   * Story 4.7: Auto-Completion Flow Integration Tests
   */
  describe('Auto-Completion Flow (Story 4.7)', () => {
    it('session auto-completes when reaching question target', async () => {
      // Set up handler that returns session_completed: true
      server.use(
        http.post('*/quiz/session/start', () => {
          return HttpResponse.json({
            session_id: 'session-uuid-123',
            session_type: 'adaptive',
            question_strategy: 'max_info_gain',
            is_resumed: false,
            status: 'active',
            started_at: '2025-12-17T10:00:00Z',
            version: 1,
            total_questions: 11,
            correct_count: 8,
            first_question: null,
            question_target: 12,
          })
        }),
        http.post('*/quiz/next-question', () => {
          return HttpResponse.json({
            session_id: 'session-uuid-123',
            question: {
              question_id: 'q-12',
              question_text: 'Last question of the session?',
              options: { A: 'Option A', B: 'Option B', C: 'Option C', D: 'Option D' },
              knowledge_area_id: 'ba-planning',
              knowledge_area_name: 'Planning',
              difficulty: 0.5,
              estimated_info_gain: 0.3,
              concepts_tested: ['Concept 1'],
            },
            questions_remaining: 0,
            current_question_number: 12,
            question_target: 12,
            progress_percentage: 0.917,
          })
        }),
        http.post('*/quiz/answer', () => {
          return HttpResponse.json({
            is_correct: true,
            correct_answer: 'A',
            explanation: 'Final explanation.',
            concepts_updated: [],
            session_stats: {
              questions_answered: 12,
              accuracy: 0.75,
              total_info_gain: 18.0,
              coverage_progress: 0.8,
              session_version: 13,
            },
            session_completed: true,
            session_summary: {
              questions_answered: 12,
              question_target: 12,
              correct_count: 9,
              accuracy: 75.0,
              concepts_strengthened: 8,
              quizzes_completed_total: 5,
              session_duration_seconds: 480,
            },
          })
        })
      )

      renderWithRouter('/quiz', [{ path: '/quiz', element: <QuizPage /> }])

      // Wait for question to load
      await waitFor(() => {
        expect(screen.getByText('Last question of the session?')).toBeInTheDocument()
      })

      // Answer and submit
      fireEvent.click(screen.getByRole('radio', { name: /option a/i }))
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /submit answer/i })).toBeInTheDocument()
      })
      fireEvent.click(screen.getByRole('button', { name: /submit answer/i }))

      // Verify session ended state is shown (session summary replaces feedback)
      await waitFor(() => {
        // The store should transition to ended state when session_completed is true
        const state = useQuizStore.getState()
        expect(state.sessionSummary).not.toBeNull()
        expect(state.status).toBe('ended')
      })
    })

    it('progress indicator shows correct question number', async () => {
      server.use(
        http.post('*/quiz/session/start', () => {
          return HttpResponse.json({
            session_id: 'session-uuid-123',
            session_type: 'adaptive',
            question_strategy: 'max_info_gain',
            is_resumed: false,
            status: 'active',
            started_at: '2025-12-17T10:00:00Z',
            version: 1,
            total_questions: 7,
            correct_count: 5,
            first_question: null,
            question_target: 12,
          })
        }),
        http.post('*/quiz/next-question', () => {
          return HttpResponse.json({
            session_id: 'session-uuid-123',
            question: {
              question_id: 'q-8',
              question_text: 'Question eight?',
              options: { A: 'A', B: 'B', C: 'C', D: 'D' },
              knowledge_area_id: 'ba-planning',
              knowledge_area_name: 'Planning',
              difficulty: 0.5,
              estimated_info_gain: 0.3,
              concepts_tested: [],
            },
            questions_remaining: 50,
            current_question_number: 8,
            question_target: 12,
            progress_percentage: 0.583,
          })
        })
      )

      renderWithRouter('/quiz', [{ path: '/quiz', element: <QuizPage /> }])

      // Verify store receives progress data
      await waitFor(() => {
        const state = useQuizStore.getState()
        expect(state.currentQuestionNumber).toBe(8)
        expect(state.questionTarget).toBe(12)
      })
    })
  })
})
