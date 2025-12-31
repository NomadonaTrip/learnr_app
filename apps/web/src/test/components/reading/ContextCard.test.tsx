/**
 * ContextCard Component Tests
 * Story 5.8: Reading Item Detail View and Engagement Tracking
 */
import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { ContextCard } from '../../../components/reading/ContextCard'

describe('ContextCard', () => {
  it('renders nothing when questionPreview is null', () => {
    const { container } = render(
      <ContextCard questionPreview={null} wasIncorrect={true} />
    )
    expect(container.firstChild).toBeNull()
  })

  it('renders context card with question preview', () => {
    render(
      <ContextCard
        questionPreview="What is the primary purpose of strategy analysis?"
        wasIncorrect={true}
      />
    )

    expect(screen.getByRole('complementary')).toBeInTheDocument()
    expect(
      screen.getByText(/What is the primary purpose of strategy analysis\?/)
    ).toBeInTheDocument()
  })

  it('shows "Recommended after incorrect answer" when wasIncorrect is true', () => {
    render(
      <ContextCard
        questionPreview="Test question"
        wasIncorrect={true}
      />
    )

    expect(
      screen.getByText('Recommended after incorrect answer')
    ).toBeInTheDocument()
  })

  it('shows "Recommended for you" when wasIncorrect is false', () => {
    render(
      <ContextCard
        questionPreview="Test question"
        wasIncorrect={false}
      />
    )

    expect(screen.getByText('Recommended for you')).toBeInTheDocument()
  })

  it('has proper accessibility label', () => {
    render(
      <ContextCard
        questionPreview="Test question"
        wasIncorrect={true}
      />
    )

    const card = screen.getByRole('complementary')
    expect(card).toHaveAttribute('aria-label', 'Why this was recommended')
  })

  it('applies custom className', () => {
    render(
      <ContextCard
        questionPreview="Test question"
        wasIncorrect={true}
        className="mt-4"
      />
    )

    const card = screen.getByRole('complementary')
    expect(card.className).toContain('mt-4')
  })
})
