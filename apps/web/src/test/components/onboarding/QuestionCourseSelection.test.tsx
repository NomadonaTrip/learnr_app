import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QuestionCourseSelection } from '../../../components/onboarding/QuestionCourseSelection'
import { getCourseDisplayName } from '../../../components/onboarding/courseData'

describe('QuestionCourseSelection', () => {
  it('renders the question text', () => {
    render(<QuestionCourseSelection onChange={vi.fn()} />)
    expect(screen.getByText('I want to learn...')).toBeInTheDocument()
  })

  it('renders Business Analysis course option', () => {
    render(<QuestionCourseSelection onChange={vi.fn()} />)
    expect(screen.getByText('Business Analysis')).toBeInTheDocument()
    expect(
      screen.getByText('CBAP, CCBA, and ECBA certification prep')
    ).toBeInTheDocument()
  })

  it('calls onChange when course is selected', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    render(<QuestionCourseSelection onChange={onChange} />)

    await user.click(screen.getByText('Business Analysis'))
    expect(onChange).toHaveBeenCalledWith('cbap')
  })

  it('marks selected course as pressed', () => {
    render(
      <QuestionCourseSelection value="cbap" onChange={vi.fn()} />
    )
    const button = screen.getByRole('button', { name: /business analysis/i })
    expect(button).toHaveAttribute('aria-pressed', 'true')
  })

  it('marks non-selected course as not pressed', () => {
    render(<QuestionCourseSelection value={undefined} onChange={vi.fn()} />)
    const button = screen.getByRole('button', { name: /business analysis/i })
    expect(button).toHaveAttribute('aria-pressed', 'false')
  })

  it('uses fieldset and legend for accessibility', () => {
    render(<QuestionCourseSelection onChange={vi.fn()} />)
    expect(screen.getByRole('group')).toBeInTheDocument()
  })

  it('course options are keyboard accessible', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    render(<QuestionCourseSelection onChange={onChange} />)

    const button = screen.getByRole('button', { name: /business analysis/i })
    button.focus()
    await user.keyboard('{Enter}')
    expect(onChange).toHaveBeenCalledWith('cbap')
  })
})

describe('getCourseDisplayName', () => {
  it('returns "Business Analysis" for cbap', () => {
    expect(getCourseDisplayName('cbap')).toBe('Business Analysis')
  })

  it('returns "this subject" for unknown course', () => {
    expect(getCourseDisplayName('unknown-course')).toBe('this subject')
  })
})
