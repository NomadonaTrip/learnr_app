/**
 * Unit tests for ReviewSummary component.
 * Story 4.9: Post-Session Review Mode
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ReviewSummary } from '../ReviewSummary'
import type { ReviewSummaryResponse } from '../../../services/reviewService'

describe('ReviewSummary', () => {
  const createSummary = (overrides: Partial<ReviewSummaryResponse> = {}): ReviewSummaryResponse => ({
    total_reviewed: 4,
    reinforced_count: 3,
    still_incorrect_count: 1,
    reinforcement_rate: 0.75,
    still_incorrect_concepts: [],
    ...overrides,
  })

  const defaultProps = {
    summary: createSummary(),
    onReturnToDashboard: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('basic rendering', () => {
    it('renders the summary region', () => {
      render(<ReviewSummary {...defaultProps} />)

      expect(screen.getByRole('region', { name: 'Review session summary' })).toBeInTheDocument()
    })

    it('displays review statistics', () => {
      render(<ReviewSummary {...defaultProps} />)

      expect(screen.getByText('4')).toBeInTheDocument()
      expect(screen.getByText('Reviewed')).toBeInTheDocument()
      expect(screen.getByText('3')).toBeInTheDocument()
      expect(screen.getByText('Reinforced')).toBeInTheDocument()
      expect(screen.getByText('1')).toBeInTheDocument()
      expect(screen.getByText('Still Incorrect')).toBeInTheDocument()
    })

    it('displays reinforcement rate as percentage', () => {
      render(<ReviewSummary {...defaultProps} />)

      expect(screen.getByText('75%')).toBeInTheDocument()
      expect(screen.getByText('Reinforcement Rate')).toBeInTheDocument()
    })
  })

  describe('performance messages', () => {
    it('shows excellent message for >= 80% reinforcement', () => {
      render(
        <ReviewSummary
          {...defaultProps}
          summary={createSummary({
            total_reviewed: 5,
            reinforced_count: 4,
            reinforcement_rate: 0.8,
          })}
        />
      )

      expect(screen.getByText('Excellent Review!')).toBeInTheDocument()
      expect(screen.getByText("You've significantly reinforced your understanding.")).toBeInTheDocument()
    })

    it('shows good progress message for 50-79% reinforcement', () => {
      render(
        <ReviewSummary
          {...defaultProps}
          summary={createSummary({
            total_reviewed: 4,
            reinforced_count: 2,
            reinforcement_rate: 0.5,
          })}
        />
      )

      expect(screen.getByText('Good Progress!')).toBeInTheDocument()
      expect(screen.getByText("You're making solid improvement on these concepts.")).toBeInTheDocument()
    })

    it('shows keep practicing message for 1-49% reinforcement', () => {
      render(
        <ReviewSummary
          {...defaultProps}
          summary={createSummary({
            total_reviewed: 4,
            reinforced_count: 1,
            reinforcement_rate: 0.25,
          })}
        />
      )

      expect(screen.getByText('Keep Practicing')).toBeInTheDocument()
      expect(screen.getByText(/Some concepts need more attention/)).toBeInTheDocument()
    })

    it('shows more study needed message for 0% reinforcement', () => {
      render(
        <ReviewSummary
          {...defaultProps}
          summary={createSummary({
            total_reviewed: 4,
            reinforced_count: 0,
            reinforcement_rate: 0,
          })}
        />
      )

      expect(screen.getByText('More Study Needed')).toBeInTheDocument()
      expect(screen.getByText(/These concepts are still challenging/)).toBeInTheDocument()
    })
  })

  describe('progress bar', () => {
    it('renders progress bar with correct aria attributes', () => {
      render(<ReviewSummary {...defaultProps} />)

      const progressBar = screen.getByRole('progressbar')
      expect(progressBar).toHaveAttribute('aria-valuenow', '75')
      expect(progressBar).toHaveAttribute('aria-valuemin', '0')
      expect(progressBar).toHaveAttribute('aria-valuemax', '100')
      expect(progressBar).toHaveAttribute('aria-label', 'Reinforcement rate: 75%')
    })

    it('uses green color for >= 50% reinforcement', () => {
      render(
        <ReviewSummary
          {...defaultProps}
          summary={createSummary({ reinforcement_rate: 0.6 })}
        />
      )

      const progressBar = screen.getByRole('progressbar')
      expect(progressBar).toHaveClass('bg-green-500')
    })

    it('uses amber color for < 50% reinforcement', () => {
      render(
        <ReviewSummary
          {...defaultProps}
          summary={createSummary({ reinforcement_rate: 0.3 })}
        />
      )

      const progressBar = screen.getByRole('progressbar')
      expect(progressBar).toHaveClass('bg-amber-500')
    })
  })

  describe('action buttons', () => {
    it('calls onReturnToDashboard when button is clicked', () => {
      const onReturnToDashboard = vi.fn()
      render(
        <ReviewSummary
          {...defaultProps}
          onReturnToDashboard={onReturnToDashboard}
        />
      )

      fireEvent.click(screen.getByText('Return to Dashboard'))

      expect(onReturnToDashboard).toHaveBeenCalledTimes(1)
    })

    it('shows Start New Quiz button when handler is provided', () => {
      render(
        <ReviewSummary
          {...defaultProps}
          onStartNewQuiz={vi.fn()}
        />
      )

      expect(screen.getByText('Start New Quiz')).toBeInTheDocument()
    })

    it('does not show Start New Quiz button when handler is not provided', () => {
      render(<ReviewSummary {...defaultProps} />)

      expect(screen.queryByText('Start New Quiz')).not.toBeInTheDocument()
    })

    it('calls onStartNewQuiz when button is clicked', () => {
      const onStartNewQuiz = vi.fn()
      render(
        <ReviewSummary
          {...defaultProps}
          onStartNewQuiz={onStartNewQuiz}
        />
      )

      fireEvent.click(screen.getByText('Start New Quiz'))

      expect(onStartNewQuiz).toHaveBeenCalledTimes(1)
    })
  })

  describe('still incorrect concepts', () => {
    const summaryWithConcepts = createSummary({
      still_incorrect_count: 2,
      still_incorrect_concepts: [
        { concept_id: 'c-1', name: 'Data Types', reading_link: '/reading?concept=data-types' },
        { concept_id: 'c-2', name: 'Variables', reading_link: '/reading?concept=variables' },
      ],
    })

    it('displays concepts needing review section', () => {
      render(<ReviewSummary {...defaultProps} summary={summaryWithConcepts} />)

      expect(screen.getByRole('region', { name: 'Concepts needing review' })).toBeInTheDocument()
      expect(screen.getByText('Concepts to Study')).toBeInTheDocument()
    })

    it('displays study links for each concept', () => {
      render(<ReviewSummary {...defaultProps} summary={summaryWithConcepts} />)

      const dataTypesLink = screen.getByText('Data Types').closest('a')
      const variablesLink = screen.getByText('Variables').closest('a')

      expect(dataTypesLink).toHaveAttribute('href', '/reading?concept=data-types')
      expect(variablesLink).toHaveAttribute('href', '/reading?concept=variables')
    })

    it('displays description about still incorrect concepts', () => {
      render(<ReviewSummary {...defaultProps} summary={summaryWithConcepts} />)

      expect(screen.getByText(/These concepts were still incorrect/)).toBeInTheDocument()
    })

    it('does not show concepts section when no concepts are still incorrect', () => {
      render(
        <ReviewSummary
          {...defaultProps}
          summary={createSummary({
            still_incorrect_count: 0,
            still_incorrect_concepts: [],
          })}
        />
      )

      expect(screen.queryByRole('region', { name: 'Concepts needing review' })).not.toBeInTheDocument()
    })
  })

  describe('accessibility', () => {
    it('has proper region labels', () => {
      render(
        <ReviewSummary
          {...defaultProps}
          summary={createSummary({
            still_incorrect_concepts: [
              { concept_id: 'c-1', name: 'Test', reading_link: '/reading' },
            ],
          })}
        />
      )

      expect(screen.getByRole('region', { name: 'Review session summary' })).toBeInTheDocument()
      expect(screen.getByRole('region', { name: 'Concepts needing review' })).toBeInTheDocument()
    })

    it('has accessible statistics group', () => {
      render(<ReviewSummary {...defaultProps} />)

      expect(screen.getByRole('group', { name: 'Review statistics' })).toBeInTheDocument()
    })
  })
})
