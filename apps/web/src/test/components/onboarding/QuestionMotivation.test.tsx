import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QuestionMotivation } from '../../../components/onboarding/QuestionMotivation'

describe('QuestionMotivation', () => {
  const defaultProps = {
    onChange: vi.fn(),
    courseName: 'Business Analysis',
  }

  it('renders question with dynamic course name', () => {
    render(<QuestionMotivation {...defaultProps} />)
    expect(
      screen.getByText("What's your 'why' for learning Business Analysis?")
    ).toBeInTheDocument()
  })

  it('renders all 5 motivation options', () => {
    render(<QuestionMotivation {...defaultProps} />)
    expect(screen.getByText('Personal interest')).toBeInTheDocument()
    expect(screen.getByText('Certification')).toBeInTheDocument()
    expect(screen.getByText('Professional development')).toBeInTheDocument()
    expect(screen.getByText('Career change')).toBeInTheDocument()
    expect(screen.getByText('Other')).toBeInTheDocument()
  })

  it('calls onChange when motivation is selected', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    render(<QuestionMotivation {...defaultProps} onChange={onChange} />)

    await user.click(screen.getByText('Certification'))
    expect(onChange).toHaveBeenCalledWith('certification')
  })

  it('calls onChange with career-change', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    render(<QuestionMotivation {...defaultProps} onChange={onChange} />)

    await user.click(screen.getByText('Career change'))
    expect(onChange).toHaveBeenCalledWith('career-change')
  })

  it('marks selected motivation as pressed', () => {
    render(
      <QuestionMotivation {...defaultProps} value="certification" />
    )
    const button = screen.getByRole('button', { name: /certification/i })
    expect(button).toHaveAttribute('aria-pressed', 'true')
  })

  it('marks non-selected motivations as not pressed', () => {
    render(
      <QuestionMotivation {...defaultProps} value="certification" />
    )
    const button = screen.getByRole('button', { name: /personal interest/i })
    expect(button).toHaveAttribute('aria-pressed', 'false')
  })

  it('uses fieldset and legend for accessibility', () => {
    render(<QuestionMotivation {...defaultProps} />)
    expect(screen.getByRole('group')).toBeInTheDocument()
  })

  it('updates course name dynamically', () => {
    render(<QuestionMotivation {...defaultProps} courseName="Data Science" />)
    expect(
      screen.getByText("What's your 'why' for learning Data Science?")
    ).toBeInTheDocument()
  })
})
