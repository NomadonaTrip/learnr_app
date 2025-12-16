import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { DiagnosticQuestionCard } from '../../../components/diagnostic/DiagnosticQuestionCard'
import type { DiagnosticQuestion } from '../../../types/diagnostic'

const mockQuestion: DiagnosticQuestion = {
  id: 'q1-uuid',
  question_text: 'Which technique is BEST suited for identifying stakeholder concerns?',
  options: {
    A: 'SWOT Analysis',
    B: 'Stakeholder Map',
    C: 'Requirements Workshop',
    D: 'Document Analysis',
  },
  knowledge_area_id: 'ba-planning',
  difficulty: 0.55,
  discrimination: 1.1,
}

describe('DiagnosticQuestionCard', () => {
  const defaultProps = {
    question: mockQuestion,
    onSubmit: vi.fn(),
    isSubmitting: false,
  }

  it('renders question text', () => {
    render(<DiagnosticQuestionCard {...defaultProps} />)
    expect(
      screen.getByText('Which technique is BEST suited for identifying stakeholder concerns?')
    ).toBeInTheDocument()
  })

  it('renders all 4 options', () => {
    render(<DiagnosticQuestionCard {...defaultProps} />)
    expect(screen.getByText('SWOT Analysis')).toBeInTheDocument()
    expect(screen.getByText('Stakeholder Map')).toBeInTheDocument()
    expect(screen.getByText('Requirements Workshop')).toBeInTheDocument()
    expect(screen.getByText('Document Analysis')).toBeInTheDocument()
  })

  it('renders option letters A, B, C, D', () => {
    render(<DiagnosticQuestionCard {...defaultProps} />)
    expect(screen.getByText('A.')).toBeInTheDocument()
    expect(screen.getByText('B.')).toBeInTheDocument()
    expect(screen.getByText('C.')).toBeInTheDocument()
    expect(screen.getByText('D.')).toBeInTheDocument()
  })

  it('submit button is disabled when no option selected', () => {
    render(<DiagnosticQuestionCard {...defaultProps} />)
    const submitButton = screen.getByRole('button', { name: 'Submit Answer' })
    expect(submitButton).toBeDisabled()
  })

  it('submit button is enabled when option is selected', async () => {
    const user = userEvent.setup()
    render(<DiagnosticQuestionCard {...defaultProps} />)

    await user.click(screen.getByText('SWOT Analysis'))
    const submitButton = screen.getByRole('button', { name: 'Submit Answer' })
    expect(submitButton).toBeEnabled()
  })

  it('calls onSubmit with selected answer', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    render(<DiagnosticQuestionCard {...defaultProps} onSubmit={onSubmit} />)

    await user.click(screen.getByText('Stakeholder Map'))
    await user.click(screen.getByRole('button', { name: 'Submit Answer' }))

    expect(onSubmit).toHaveBeenCalledWith('B')
  })

  it('shows submitting state', () => {
    render(<DiagnosticQuestionCard {...defaultProps} isSubmitting={true} />)
    expect(screen.getByRole('button', { name: 'Submitting...' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Submitting...' })).toBeDisabled()
  })

  it('uses fieldset and legend for accessibility', () => {
    render(<DiagnosticQuestionCard {...defaultProps} />)
    expect(screen.getByRole('group')).toBeInTheDocument()
  })

  it('has correct aria-labelledby on article', () => {
    render(<DiagnosticQuestionCard {...defaultProps} />)
    const article = screen.getByRole('article')
    expect(article).toHaveAttribute('aria-labelledby', 'question-text')
  })

  describe('keyboard navigation', () => {
    it('navigates down with ArrowDown key', async () => {
      const user = userEvent.setup()
      render(<DiagnosticQuestionCard {...defaultProps} />)

      const radios = screen.getAllByRole('radio')
      const radioA = radios[0]
      const radioB = radios[1]

      await user.click(radioA)
      await user.keyboard('{ArrowDown}')

      expect(radioB).toHaveFocus()
    })

    it('navigates up with ArrowUp key', async () => {
      const user = userEvent.setup()
      render(<DiagnosticQuestionCard {...defaultProps} />)

      const radios = screen.getAllByRole('radio')
      const radioA = radios[0]
      const radioB = radios[1]

      await user.click(radioB)
      await user.keyboard('{ArrowUp}')

      expect(radioA).toHaveFocus()
    })

    it('wraps around when navigating past last option', async () => {
      const user = userEvent.setup()
      render(<DiagnosticQuestionCard {...defaultProps} />)

      const radios = screen.getAllByRole('radio')
      const radioA = radios[0]
      const radioD = radios[3]

      await user.click(radioD)
      await user.keyboard('{ArrowDown}')

      expect(radioA).toHaveFocus()
    })

    it('selects option with Enter key', async () => {
      const user = userEvent.setup()
      render(<DiagnosticQuestionCard {...defaultProps} />)

      const radios = screen.getAllByRole('radio')
      const radioA = radios[0]
      await user.click(radioA)
      await user.keyboard('{Enter}')

      expect(radioA).toBeChecked()
    })

    it('selects option with Space key', async () => {
      const user = userEvent.setup()
      render(<DiagnosticQuestionCard {...defaultProps} />)

      const radios = screen.getAllByRole('radio')
      const radioA = radios[0]
      await user.click(radioA)
      await user.keyboard(' ')

      expect(radioA).toBeChecked()
    })
  })

  it('resets selection when question changes', async () => {
    const user = userEvent.setup()
    const { rerender } = render(<DiagnosticQuestionCard {...defaultProps} />)

    const radios = screen.getAllByRole('radio')
    await user.click(radios[0])
    expect(radios[0]).toBeChecked()

    const newQuestion = { ...mockQuestion, id: 'q2-uuid' }
    rerender(<DiagnosticQuestionCard {...defaultProps} question={newQuestion} />)

    const newRadios = screen.getAllByRole('radio')
    expect(newRadios[0]).not.toBeChecked()
  })

  it('announces selection to screen readers', async () => {
    const user = userEvent.setup()
    render(<DiagnosticQuestionCard {...defaultProps} />)

    await user.click(screen.getByText('Stakeholder Map'))

    // The aria-live region should contain the announcement
    const liveRegion = document.querySelector('[aria-live="polite"]')
    expect(liveRegion).toHaveTextContent('Selected option B')
  })
})
