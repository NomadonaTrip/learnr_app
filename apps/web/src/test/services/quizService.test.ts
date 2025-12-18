import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest'
import { quizService } from '../../services/quizService'
import { server } from '../mocks/server'
import {
  quizHandlers,
  quizErrorHandlers,
  quizConflictHandlers,
  quizAnswerAlreadyAnsweredHandlers,
  quizAnswerInvalidSessionHandlers,
  resetQuizMocks,
  setMockNextAnswerCorrect,
  getLastRequestId,
} from '../mocks/handlers/quizHandlers'
import {
  mockAnswerSubmissionRequest,
} from '../fixtures/quizFixtures'

describe('quizService', () => {
  beforeAll(() => {
    server.listen({ onUnhandledRequest: 'error' })
  })

  afterEach(() => {
    server.resetHandlers()
    resetQuizMocks()
  })

  afterAll(() => {
    server.close()
  })

  describe('startSession', () => {
    it('calls POST /quiz/session/start', async () => {
      server.use(...quizHandlers)
      const response = await quizService.startSession()

      expect(response.session_id).toBe('session-uuid-123')
      expect(response.session_type).toBe('adaptive')
      expect(response.question_strategy).toBe('max_info_gain')
      expect(response.is_resumed).toBe(false)
      expect(response.status).toBe('active')
    })

    it('sends session config when provided', async () => {
      server.use(...quizHandlers)
      const response = await quizService.startSession({
        session_type: 'focused',
        question_strategy: 'prerequisite_first',
        knowledge_area_filter: 'planning',
      })

      expect(response.session_id).toBeDefined()
    })

    it('handles no enrollment error', async () => {
      server.use(...quizErrorHandlers)

      await expect(quizService.startSession()).rejects.toThrow()
    })
  })

  describe('getSession', () => {
    it('calls GET /quiz/session/{id}', async () => {
      server.use(...quizHandlers)
      const response = await quizService.getSession('session-uuid-123')

      expect(response.id).toBe('session-uuid-123')
      expect(response.session_type).toBe('adaptive')
      expect(response.status).toBe('active')
      expect(response.is_paused).toBe(false)
      expect(response.version).toBe(2)
    })
  })

  describe('pauseSession', () => {
    it('calls POST /quiz/session/{id}/pause', async () => {
      server.use(...quizHandlers)
      const response = await quizService.pauseSession('session-uuid-123')

      expect(response.session_id).toBe('session-uuid-123')
      expect(response.status).toBe('paused')
      expect(response.is_paused).toBe(true)
    })
  })

  describe('resumeSession', () => {
    it('calls POST /quiz/session/{id}/resume', async () => {
      server.use(...quizHandlers)
      const response = await quizService.resumeSession('session-uuid-123')

      expect(response.session_id).toBe('session-uuid-123')
      expect(response.status).toBe('active')
      expect(response.is_paused).toBe(false)
    })
  })

  describe('endSession', () => {
    it('calls POST /quiz/session/{id}/end with version', async () => {
      server.use(...quizHandlers)
      const response = await quizService.endSession('session-uuid-123', 2)

      expect(response.session_id).toBe('session-uuid-123')
      expect(response.ended_at).toBeDefined()
      expect(response.total_questions).toBe(10)
      expect(response.correct_count).toBe(7)
      expect(response.accuracy).toBe(70)
    })

    it('handles version conflict error', async () => {
      server.use(...quizConflictHandlers)

      await expect(quizService.endSession('session-uuid-123', 1)).rejects.toThrow()
    })
  })

  describe('submitAnswer', () => {
    it('calls POST /quiz/answer with X-Request-ID header', async () => {
      server.use(...quizHandlers)
      const requestId = 'test-request-id-123'

      await quizService.submitAnswer(mockAnswerSubmissionRequest, requestId)

      expect(getLastRequestId()).toBe(requestId)
    })

    it('returns correct answer response', async () => {
      server.use(...quizHandlers)
      setMockNextAnswerCorrect(true)

      const response = await quizService.submitAnswer(
        mockAnswerSubmissionRequest,
        'test-request-id'
      )

      expect(response.is_correct).toBe(true)
      expect(response.correct_answer).toBe('A')
      expect(response.explanation).toBeDefined()
      expect(response.concepts_updated).toBeInstanceOf(Array)
      expect(response.session_stats).toBeDefined()
      expect(response.session_stats.questions_answered).toBe(8)
      expect(response.session_stats.accuracy).toBe(0.75)
    })

    it('returns incorrect answer response', async () => {
      server.use(...quizHandlers)
      setMockNextAnswerCorrect(false)

      const response = await quizService.submitAnswer(
        { ...mockAnswerSubmissionRequest, selected_answer: 'C' },
        'test-request-id'
      )

      expect(response.is_correct).toBe(false)
      expect(response.correct_answer).toBe('B')
      expect(response.explanation).toBeDefined()
    })

    it('handles already answered error (409)', async () => {
      server.use(...quizAnswerAlreadyAnsweredHandlers)

      await expect(
        quizService.submitAnswer(mockAnswerSubmissionRequest, 'test-request-id')
      ).rejects.toThrow()
    })

    it('handles invalid session error (404)', async () => {
      server.use(...quizAnswerInvalidSessionHandlers)

      await expect(
        quizService.submitAnswer(mockAnswerSubmissionRequest, 'test-request-id')
      ).rejects.toThrow()
    })
  })
})
