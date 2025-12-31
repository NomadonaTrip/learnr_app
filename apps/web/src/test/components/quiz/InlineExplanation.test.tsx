import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { InlineExplanation } from '../../../components/quiz/InlineExplanation'

describe('InlineExplanation', () => {
  const defaultProps = {
    explanation: 'This is the explanation text for the answer.',
    onNextQuestion: vi.fn(),
    isLastQuestion: false,
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('explanation display', () => {
    it('displays the explanation heading', () => {
      render(<InlineExplanation {...defaultProps} />)

      expect(screen.getByText('Explanation')).toBeInTheDocument()
    })

    it('displays the explanation text', () => {
      render(<InlineExplanation {...defaultProps} />)

      expect(screen.getByText(defaultProps.explanation)).toBeInTheDocument()
    })

    it('has proper styling for the explanation container', () => {
      render(<InlineExplanation {...defaultProps} />)

      const container = screen.getByText(defaultProps.explanation).closest('div')
      expect(container).toHaveClass('bg-gray-50')
      expect(container).toHaveClass('rounded-[14px]')
    })
  })

  describe('next question button', () => {
    it('displays "Next Question" when not last question', () => {
      render(<InlineExplanation {...defaultProps} isLastQuestion={false} />)

      expect(screen.getByRole('button', { name: /next question/i })).toBeInTheDocument()
    })

    it('displays "Finish Session" when last question', () => {
      render(<InlineExplanation {...defaultProps} isLastQuestion={true} />)

      expect(screen.getByRole('button', { name: /finish/i })).toBeInTheDocument()
    })

    it('calls onNextQuestion when clicked', () => {
      const onNextQuestion = vi.fn()
      render(<InlineExplanation {...defaultProps} onNextQuestion={onNextQuestion} />)

      fireEvent.click(screen.getByRole('button', { name: /next question/i }))

      expect(onNextQuestion).toHaveBeenCalledTimes(1)
    })

    it('has proper button styling', () => {
      render(<InlineExplanation {...defaultProps} />)

      const button = screen.getByRole('button', { name: /next question/i })
      expect(button).toHaveClass('bg-primary-600')
      expect(button).toHaveClass('rounded-[14px]')
    })
  })

  describe('accessibility', () => {
    it('has proper aria-labelledby for explanation section', () => {
      render(<InlineExplanation {...defaultProps} />)

      const explanationContainer = screen.getByText(defaultProps.explanation).closest('div')
      expect(explanationContainer).toHaveAttribute('aria-labelledby', 'explanation-heading')
    })

    it('has correct aria-label for next question button', () => {
      render(<InlineExplanation {...defaultProps} isLastQuestion={false} />)

      const button = screen.getByRole('button')
      expect(button).toHaveAttribute('aria-label', 'Proceed to next question')
    })

    it('has correct aria-label for finish session button', () => {
      render(<InlineExplanation {...defaultProps} isLastQuestion={true} />)

      const button = screen.getByRole('button')
      expect(button).toHaveAttribute('aria-label', 'Finish quiz session')
    })

    it('container is focusable for programmatic focus', () => {
      render(<InlineExplanation {...defaultProps} />)

      const container = screen.getByText('Explanation').closest('div[tabindex]')
      expect(container).toHaveAttribute('tabindex', '-1')
    })
  })

  describe('animation classes', () => {
    it('applies animation class when reduced motion is not preferred', () => {
      render(<InlineExplanation {...defaultProps} />)

      const container = screen.getByText('Explanation').closest('div[tabindex]')
      expect(container).toHaveClass('animate-fade-slide-in')
    })
  })
})
