/**
 * Unit tests for ReviewPrompt component.
 * Story 4.9: Post-Session Review Mode
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ReviewPrompt } from '../ReviewPrompt'

describe('ReviewPrompt', () => {
  const defaultProps = {
    incorrectCount: 3,
    onStartReview: vi.fn(),
    onSkipReview: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('basic rendering', () => {
    it('renders the review prompt dialog', () => {
      render(<ReviewPrompt {...defaultProps} />)

      expect(screen.getByRole('dialog')).toBeInTheDocument()
      expect(screen.getByText('Review Your Mistakes?')).toBeInTheDocument()
    })

    it('displays the correct count of incorrect questions', () => {
      render(<ReviewPrompt {...defaultProps} incorrectCount={5} />)

      expect(screen.getByText('5')).toBeInTheDocument()
      expect(screen.getByText(/questions wrong/)).toBeInTheDocument()
    })

    it('uses singular form for one question', () => {
      render(<ReviewPrompt {...defaultProps} incorrectCount={1} />)

      expect(screen.getByText(/question wrong/)).toBeInTheDocument()
      expect(screen.getByText('Review 1 Question')).toBeInTheDocument()
    })

    it('uses plural form for multiple questions', () => {
      render(<ReviewPrompt {...defaultProps} incorrectCount={3} />)

      expect(screen.getByText(/questions wrong/)).toBeInTheDocument()
      expect(screen.getByText('Review 3 Questions')).toBeInTheDocument()
    })
  })

  describe('benefits section', () => {
    it('displays review benefits list', () => {
      render(<ReviewPrompt {...defaultProps} />)

      expect(screen.getByText('Benefits of Review:')).toBeInTheDocument()
      expect(screen.getByText('Reinforces correct understanding')).toBeInTheDocument()
      expect(screen.getByText('Stronger belief updates for mastered concepts')).toBeInTheDocument()
      expect(screen.getByText('Identify concepts needing more study')).toBeInTheDocument()
    })
  })

  describe('button interactions', () => {
    it('calls onStartReview when start button is clicked', () => {
      const onStartReview = vi.fn()
      render(<ReviewPrompt {...defaultProps} onStartReview={onStartReview} />)

      fireEvent.click(screen.getByText('Review 3 Questions'))

      expect(onStartReview).toHaveBeenCalledTimes(1)
    })

    it('calls onSkipReview when skip button is clicked', () => {
      const onSkipReview = vi.fn()
      render(<ReviewPrompt {...defaultProps} onSkipReview={onSkipReview} />)

      fireEvent.click(screen.getByText('Skip for Now'))

      expect(onSkipReview).toHaveBeenCalledTimes(1)
    })
  })

  describe('loading states', () => {
    it('shows loading text when starting review', () => {
      render(<ReviewPrompt {...defaultProps} isStarting={true} />)

      expect(screen.getByText('Starting Review...')).toBeInTheDocument()
    })

    it('shows loading text when skipping', () => {
      render(<ReviewPrompt {...defaultProps} isSkipping={true} />)

      expect(screen.getByText('Skipping...')).toBeInTheDocument()
    })

    it('disables both buttons when starting', () => {
      render(<ReviewPrompt {...defaultProps} isStarting={true} />)

      const startButton = screen.getByText('Starting Review...')
      const skipButton = screen.getByText('Skip for Now')

      expect(startButton).toBeDisabled()
      expect(skipButton).toBeDisabled()
    })

    it('disables both buttons when skipping', () => {
      render(<ReviewPrompt {...defaultProps} isSkipping={true} />)

      const startButton = screen.getByText('Review 3 Questions')
      const skipButton = screen.getByText('Skipping...')

      expect(startButton).toBeDisabled()
      expect(skipButton).toBeDisabled()
    })
  })

  describe('accessibility', () => {
    it('has accessible labels for buttons', () => {
      render(<ReviewPrompt {...defaultProps} incorrectCount={3} />)

      expect(screen.getByLabelText('Start review of 3 incorrect questions')).toBeInTheDocument()
      expect(screen.getByLabelText('Skip review and continue')).toBeInTheDocument()
    })

    it('has proper dialog role and labels', () => {
      render(<ReviewPrompt {...defaultProps} />)

      const dialog = screen.getByRole('dialog')
      expect(dialog).toHaveAttribute('aria-labelledby', 'review-prompt-title')
      expect(dialog).toHaveAttribute('aria-describedby', 'review-prompt-description')
    })

    it('displays hint about reviewing later', () => {
      render(<ReviewPrompt {...defaultProps} />)

      expect(screen.getByText(/review your quiz history later/)).toBeInTheDocument()
    })
  })
})
