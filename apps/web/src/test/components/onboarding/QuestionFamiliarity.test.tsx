import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QuestionFamiliarity } from '../../../components/onboarding/QuestionFamiliarity'

describe('QuestionFamiliarity', () => {
  const defaultProps = {
    onChange: vi.fn(),
    courseName: 'Business Analysis',
  }

  it('renders question with dynamic course name', () => {
    render(<QuestionFamiliarity {...defaultProps} />)
    expect(
      screen.getByText('How familiar are you with Business Analysis?')
    ).toBeInTheDocument()
  })

  it('renders all 4 familiarity options', () => {
    render(<QuestionFamiliarity {...defaultProps} />)
    expect(screen.getByText("I'm new to Business Analysis")).toBeInTheDocument()
    expect(screen.getByText('I know the basics')).toBeInTheDocument()
    expect(screen.getByText('I have intermediate experience')).toBeInTheDocument()
    expect(
      screen.getByText("I'm an expert brushing up my skills")
    ).toBeInTheDocument()
  })

  it('calls onChange when familiarity is selected', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    render(<QuestionFamiliarity {...defaultProps} onChange={onChange} />)

    await user.click(screen.getByText('I know the basics'))
    expect(onChange).toHaveBeenCalledWith('basics')
  })

  it('calls onChange with new', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    render(<QuestionFamiliarity {...defaultProps} onChange={onChange} />)

    await user.click(screen.getByText("I'm new to Business Analysis"))
    expect(onChange).toHaveBeenCalledWith('new')
  })

  it('calls onChange with intermediate', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    render(<QuestionFamiliarity {...defaultProps} onChange={onChange} />)

    await user.click(screen.getByText('I have intermediate experience'))
    expect(onChange).toHaveBeenCalledWith('intermediate')
  })

  it('calls onChange with expert', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    render(<QuestionFamiliarity {...defaultProps} onChange={onChange} />)

    await user.click(screen.getByText("I'm an expert brushing up my skills"))
    expect(onChange).toHaveBeenCalledWith('expert')
  })

  it('marks selected familiarity as pressed', () => {
    render(<QuestionFamiliarity {...defaultProps} value="intermediate" />)
    const button = screen.getByRole('button', {
      name: /intermediate experience/i,
    })
    expect(button).toHaveAttribute('aria-pressed', 'true')
  })

  it('uses fieldset and legend for accessibility', () => {
    render(<QuestionFamiliarity {...defaultProps} />)
    expect(screen.getByRole('group')).toBeInTheDocument()
  })

  it('dynamically replaces course name in first option', () => {
    render(<QuestionFamiliarity {...defaultProps} courseName="Data Science" />)
    expect(screen.getByText("I'm new to Data Science")).toBeInTheDocument()
  })
})
