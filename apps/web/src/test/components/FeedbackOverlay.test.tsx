import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { FeedbackOverlay } from '../../components/quiz/FeedbackOverlay'
import {
  mockCorrectAnswerResponse,
  mockIncorrectAnswerResponse,
} from '../fixtures/quizFixtures'

describe('FeedbackOverlay', () => {
  describe('correct answer display', () => {
    it('displays green checkmark and "Correct!" text', () => {
      render(
        <FeedbackOverlay
          feedbackResult={mockCorrectAnswerResponse}
          onNextQuestion={() => {}}
        />
      )

      expect(screen.getByText('Correct!')).toBeInTheDocument()
      expect(screen.getByRole('alert')).toHaveClass('bg-green-50')
    })

    it('displays explanation text', () => {
      render(
        <FeedbackOverlay
          feedbackResult={mockCorrectAnswerResponse}
          onNextQuestion={() => {}}
        />
      )

      expect(screen.getByText(mockCorrectAnswerResponse.explanation)).toBeInTheDocument()
    })

    it('displays session stats', () => {
      render(
        <FeedbackOverlay
          feedbackResult={mockCorrectAnswerResponse}
          onNextQuestion={() => {}}
        />
      )

      expect(screen.getByText('8')).toBeInTheDocument() // questions_answered
      expect(screen.getByText('75%')).toBeInTheDocument() // accuracy (0.75 * 100)
    })
  })

  describe('incorrect answer display', () => {
    it('displays orange X and correct answer text', () => {
      render(
        <FeedbackOverlay
          feedbackResult={mockIncorrectAnswerResponse}
          onNextQuestion={() => {}}
        />
      )

      expect(screen.getByText('Incorrect. The correct answer is B')).toBeInTheDocument()
      expect(screen.getByRole('alert')).toHaveClass('bg-orange-50')
    })

    it('displays explanation text', () => {
      render(
        <FeedbackOverlay
          feedbackResult={mockIncorrectAnswerResponse}
          onNextQuestion={() => {}}
        />
      )

      expect(screen.getByText(mockIncorrectAnswerResponse.explanation)).toBeInTheDocument()
    })

    it('displays session stats', () => {
      render(
        <FeedbackOverlay
          feedbackResult={mockIncorrectAnswerResponse}
          onNextQuestion={() => {}}
        />
      )

      expect(screen.getByText('9')).toBeInTheDocument() // questions_answered
      expect(screen.getByText('67%')).toBeInTheDocument() // accuracy (0.67 * 100)
    })
  })

  describe('next question button', () => {
    it('calls onNextQuestion handler when clicked', () => {
      const onNextQuestion = vi.fn()
      render(
        <FeedbackOverlay
          feedbackResult={mockCorrectAnswerResponse}
          onNextQuestion={onNextQuestion}
        />
      )

      fireEvent.click(screen.getByRole('button', { name: /next question/i }))

      expect(onNextQuestion).toHaveBeenCalledTimes(1)
    })

    it('displays "Finish Session" when isLastQuestion is true', () => {
      render(
        <FeedbackOverlay
          feedbackResult={mockCorrectAnswerResponse}
          onNextQuestion={() => {}}
          isLastQuestion={true}
        />
      )

      expect(screen.getByRole('button', { name: /finish/i })).toBeInTheDocument()
    })

    it('displays "Next Question" when isLastQuestion is false', () => {
      render(
        <FeedbackOverlay
          feedbackResult={mockCorrectAnswerResponse}
          onNextQuestion={() => {}}
          isLastQuestion={false}
        />
      )

      expect(screen.getByRole('button', { name: /next question/i })).toBeInTheDocument()
    })
  })

  describe('accessibility', () => {
    it('has correct ARIA attributes for correct answer', () => {
      render(
        <FeedbackOverlay
          feedbackResult={mockCorrectAnswerResponse}
          onNextQuestion={() => {}}
        />
      )

      const alert = screen.getByRole('alert')
      expect(alert).toHaveAttribute('aria-live', 'polite')
      expect(alert).toHaveAttribute('aria-label', 'Correct answer feedback')
    })

    it('has correct ARIA attributes for incorrect answer', () => {
      render(
        <FeedbackOverlay
          feedbackResult={mockIncorrectAnswerResponse}
          onNextQuestion={() => {}}
        />
      )

      const alert = screen.getByRole('alert')
      expect(alert).toHaveAttribute('aria-live', 'polite')
      expect(alert).toHaveAttribute('aria-label', 'Incorrect answer feedback')
    })
  })
})
