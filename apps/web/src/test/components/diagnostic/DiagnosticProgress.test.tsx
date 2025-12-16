import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { DiagnosticProgress } from '../../../components/diagnostic/DiagnosticProgress'

describe('DiagnosticProgress', () => {
  it('displays correct question number (1-indexed)', () => {
    render(<DiagnosticProgress currentIndex={0} total={15} />)
    expect(screen.getByText('Question 1 of 15')).toBeInTheDocument()
  })

  it('displays question 5 of 15 for index 4', () => {
    render(<DiagnosticProgress currentIndex={4} total={15} />)
    expect(screen.getByText('Question 5 of 15')).toBeInTheDocument()
  })

  it('displays last question correctly', () => {
    render(<DiagnosticProgress currentIndex={14} total={15} />)
    expect(screen.getByText('Question 15 of 15')).toBeInTheDocument()
  })

  it('renders progress bar with correct aria attributes', () => {
    render(<DiagnosticProgress currentIndex={4} total={15} />)
    const progressbar = screen.getByRole('progressbar', {
      name: /Progress: question 5 of 15/,
    })
    expect(progressbar).toHaveAttribute('aria-valuenow', '5')
    expect(progressbar).toHaveAttribute('aria-valuemin', '1')
    expect(progressbar).toHaveAttribute('aria-valuemax', '15')
  })

  it('renders progress bar at 0% for first question', () => {
    render(<DiagnosticProgress currentIndex={0} total={15} />)
    const progressFill = document.querySelector('[style*="width"]')
    // Question 1 of 15 = 1/15 = 6.67% rounded to 7%
    expect(progressFill).toHaveStyle({ width: '7%' })
  })

  it('renders progress bar at 100% for last question', () => {
    render(<DiagnosticProgress currentIndex={14} total={15} />)
    const progressFill = document.querySelector('[style*="width"]')
    expect(progressFill).toHaveStyle({ width: '100%' })
  })

  it('displays building profile message', () => {
    render(<DiagnosticProgress currentIndex={0} total={15} />)
    expect(screen.getByText('Building your knowledge profile...')).toBeInTheDocument()
  })

  describe('coverage meter', () => {
    it('does not render when coveragePercentage is undefined', () => {
      render(<DiagnosticProgress currentIndex={0} total={15} />)
      expect(screen.queryByText('Concept coverage')).not.toBeInTheDocument()
    })

    it('renders coverage meter when coveragePercentage is provided', () => {
      render(<DiagnosticProgress currentIndex={0} total={15} coveragePercentage={0.405} />)
      expect(screen.getByText('Concept coverage')).toBeInTheDocument()
    })

    it('displays coverage percentage correctly', () => {
      render(<DiagnosticProgress currentIndex={0} total={15} coveragePercentage={0.405} />)
      expect(screen.getByText('41%')).toBeInTheDocument()
    })

    it('renders coverage progressbar with correct aria attributes', () => {
      render(<DiagnosticProgress currentIndex={0} total={15} coveragePercentage={0.5} />)
      const coverageBar = screen.getByRole('progressbar', {
        name: /Concept coverage: 50%/,
      })
      expect(coverageBar).toHaveAttribute('aria-valuenow', '50')
      expect(coverageBar).toHaveAttribute('aria-valuemin', '0')
      expect(coverageBar).toHaveAttribute('aria-valuemax', '100')
    })
  })

  it('handles edge case of 0 total questions', () => {
    render(<DiagnosticProgress currentIndex={0} total={0} />)
    expect(screen.getByText('Question 1 of 0')).toBeInTheDocument()
  })
})
