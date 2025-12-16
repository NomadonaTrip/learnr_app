import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ProgressIndicator } from '../../../components/onboarding/ProgressIndicator'

describe('ProgressIndicator', () => {
  it('displays "Question 1 of 3"', () => {
    render(<ProgressIndicator currentQuestion={1} totalQuestions={3} />)
    expect(screen.getByText('Question 1 of 3')).toBeInTheDocument()
  })

  it('displays "Question 2 of 3"', () => {
    render(<ProgressIndicator currentQuestion={2} totalQuestions={3} />)
    expect(screen.getByText('Question 2 of 3')).toBeInTheDocument()
  })

  it('displays "Question 3 of 3"', () => {
    render(<ProgressIndicator currentQuestion={3} totalQuestions={3} />)
    expect(screen.getByText('Question 3 of 3')).toBeInTheDocument()
  })

  it('has progressbar role', () => {
    render(<ProgressIndicator currentQuestion={1} totalQuestions={3} />)
    expect(screen.getByRole('progressbar')).toBeInTheDocument()
  })

  it('has correct aria attributes', () => {
    render(<ProgressIndicator currentQuestion={2} totalQuestions={3} />)
    const progressbar = screen.getByRole('progressbar')
    expect(progressbar).toHaveAttribute('aria-valuenow', '2')
    expect(progressbar).toHaveAttribute('aria-valuemin', '1')
    expect(progressbar).toHaveAttribute('aria-valuemax', '3')
  })

  it('has accessible label', () => {
    render(<ProgressIndicator currentQuestion={1} totalQuestions={3} />)
    const progressbar = screen.getByRole('progressbar')
    expect(progressbar).toHaveAttribute('aria-label', 'Question 1 of 3')
  })

  it('renders progress bar element', () => {
    const { container } = render(
      <ProgressIndicator currentQuestion={2} totalQuestions={3} />
    )
    // Progress bar should have some width for question 2 (33% = (2-1)/3 * 100)
    const progressBar = container.querySelector('[style*="width"]')
    expect(progressBar).toBeInTheDocument()
  })
})
