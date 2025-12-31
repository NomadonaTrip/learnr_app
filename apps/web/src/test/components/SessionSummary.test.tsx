import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { SessionSummary } from '../../components/quiz/SessionSummary'
import { mockSessionSummary } from '../fixtures/quizFixtures'

describe('SessionSummary', () => {
  describe('display elements', () => {
    it('displays "Session Complete!" header', () => {
      render(
        <SessionSummary
          summary={mockSessionSummary}
          onStartNew={() => {}}
          onReturnToDashboard={() => {}}
        />
      )

      expect(screen.getByText('Session Complete!')).toBeInTheDocument()
    })

    it('displays questions answered and target', () => {
      render(
        <SessionSummary
          summary={mockSessionSummary}
          onStartNew={() => {}}
          onReturnToDashboard={() => {}}
        />
      )

      expect(screen.getByText('12/12')).toBeInTheDocument()
      expect(screen.getByText('Questions')).toBeInTheDocument()
    })

    it('displays accuracy percentage', () => {
      render(
        <SessionSummary
          summary={mockSessionSummary}
          onStartNew={() => {}}
          onReturnToDashboard={() => {}}
        />
      )

      expect(screen.getByText('75%')).toBeInTheDocument()
      expect(screen.getByText('Accuracy')).toBeInTheDocument()
    })

    it('displays correct count', () => {
      render(
        <SessionSummary
          summary={mockSessionSummary}
          onStartNew={() => {}}
          onReturnToDashboard={() => {}}
        />
      )

      expect(screen.getByText('9')).toBeInTheDocument()
      expect(screen.getByText('Correct')).toBeInTheDocument()
    })

    it('displays concepts strengthened', () => {
      render(
        <SessionSummary
          summary={mockSessionSummary}
          onStartNew={() => {}}
          onReturnToDashboard={() => {}}
        />
      )

      expect(screen.getByText('8')).toBeInTheDocument()
      expect(screen.getByText('Concepts')).toBeInTheDocument()
    })

    it('displays session duration', () => {
      render(
        <SessionSummary
          summary={mockSessionSummary}
          onStartNew={() => {}}
          onReturnToDashboard={() => {}}
        />
      )

      // 480 seconds = 8 minutes
      expect(screen.getByText('8m')).toBeInTheDocument()
      expect(screen.getByText('Duration')).toBeInTheDocument()
    })

    it('displays total quizzes completed', () => {
      render(
        <SessionSummary
          summary={mockSessionSummary}
          onStartNew={() => {}}
          onReturnToDashboard={() => {}}
        />
      )

      expect(screen.getByText('5')).toBeInTheDocument()
      expect(screen.getByText('Total Quizzes')).toBeInTheDocument()
    })
  })

  describe('performance level styling', () => {
    it('displays "Excellent work!" for accuracy >= 80%', () => {
      const excellentSummary = {
        ...mockSessionSummary,
        accuracy: 85.0,
        correct_count: 10,
      }

      render(
        <SessionSummary
          summary={excellentSummary}
          onStartNew={() => {}}
          onReturnToDashboard={() => {}}
        />
      )

      expect(screen.getByText('Excellent work!')).toBeInTheDocument()
    })

    it('displays "Good job!" for accuracy 60-79%', () => {
      render(
        <SessionSummary
          summary={mockSessionSummary}  // 75% accuracy
          onStartNew={() => {}}
          onReturnToDashboard={() => {}}
        />
      )

      expect(screen.getByText('Good job!')).toBeInTheDocument()
    })

    it('displays "Keep practicing!" for accuracy < 60%', () => {
      const lowAccuracySummary = {
        ...mockSessionSummary,
        accuracy: 50.0,
        correct_count: 6,
      }

      render(
        <SessionSummary
          summary={lowAccuracySummary}
          onStartNew={() => {}}
          onReturnToDashboard={() => {}}
        />
      )

      expect(screen.getByText('Keep practicing!')).toBeInTheDocument()
    })
  })

  describe('button interactions', () => {
    it('calls onStartNew when New Quiz button is clicked', () => {
      const onStartNew = vi.fn()

      render(
        <SessionSummary
          summary={mockSessionSummary}
          onStartNew={onStartNew}
          onReturnToDashboard={() => {}}
        />
      )

      fireEvent.click(screen.getByRole('button', { name: /new quiz/i }))

      expect(onStartNew).toHaveBeenCalledTimes(1)
    })

    it('calls onReturnToDashboard when Dashboard button is clicked', () => {
      const onReturnToDashboard = vi.fn()

      render(
        <SessionSummary
          summary={mockSessionSummary}
          onStartNew={() => {}}
          onReturnToDashboard={onReturnToDashboard}
        />
      )

      fireEvent.click(screen.getByRole('button', { name: /dashboard/i }))

      expect(onReturnToDashboard).toHaveBeenCalledTimes(1)
    })
  })

  describe('accessibility', () => {
    it('has correct ARIA attributes', () => {
      render(
        <SessionSummary
          summary={mockSessionSummary}
          onStartNew={() => {}}
          onReturnToDashboard={() => {}}
        />
      )

      const alert = screen.getByRole('alert')
      expect(alert).toHaveAttribute('aria-live', 'polite')
      expect(alert).toHaveAttribute('aria-label', 'Quiz session completed')
    })

    it('buttons have accessible labels', () => {
      render(
        <SessionSummary
          summary={mockSessionSummary}
          onStartNew={() => {}}
          onReturnToDashboard={() => {}}
        />
      )

      expect(screen.getByRole('button', { name: /return to dashboard/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /start a new quiz/i })).toBeInTheDocument()
    })
  })

  describe('duration formatting', () => {
    it('displays only seconds for < 60 seconds', () => {
      const shortSummary = {
        ...mockSessionSummary,
        session_duration_seconds: 45,
      }

      render(
        <SessionSummary
          summary={shortSummary}
          onStartNew={() => {}}
          onReturnToDashboard={() => {}}
        />
      )

      expect(screen.getByText('45s')).toBeInTheDocument()
    })

    it('displays minutes and seconds for > 60 seconds', () => {
      const summary = {
        ...mockSessionSummary,
        session_duration_seconds: 125,  // 2m 5s
      }

      render(
        <SessionSummary
          summary={summary}
          onStartNew={() => {}}
          onReturnToDashboard={() => {}}
        />
      )

      expect(screen.getByText('2m 5s')).toBeInTheDocument()
    })

    it('displays only minutes for exact minute values', () => {
      const summary = {
        ...mockSessionSummary,
        session_duration_seconds: 600,  // 10m
      }

      render(
        <SessionSummary
          summary={summary}
          onStartNew={() => {}}
          onReturnToDashboard={() => {}}
        />
      )

      expect(screen.getByText('10m')).toBeInTheDocument()
    })
  })
})
