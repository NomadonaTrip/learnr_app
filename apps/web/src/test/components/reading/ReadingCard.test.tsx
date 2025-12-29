/**
 * ReadingCard Component Tests
 * Story 5.7: Reading Library Page with Queue Display
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ReadingCard } from '../../../components/reading/ReadingCard'

const defaultProps = {
  queueId: 'queue-123',
  title: 'Introduction to Strategy Analysis',
  preview: 'This chunk covers the basics of strategy analysis in business...',
  babokSection: '3.1',
  kaName: 'Strategy Analysis',
  priority: 'High' as const,
  estimatedReadMinutes: 5,
  addedAt: '2025-01-15T10:30:00Z',
  onReadNow: vi.fn(),
}

describe('ReadingCard', () => {
  describe('rendering', () => {
    it('renders the title with BABOK section', () => {
      render(<ReadingCard {...defaultProps} />)
      expect(screen.getByText('3.1: Introduction to Strategy Analysis')).toBeInTheDocument()
    })

    it('renders the preview text', () => {
      render(<ReadingCard {...defaultProps} />)
      expect(
        screen.getByText('This chunk covers the basics of strategy analysis in business...')
      ).toBeInTheDocument()
    })

    it('renders the knowledge area name', () => {
      render(<ReadingCard {...defaultProps} />)
      expect(screen.getByText('Strategy Analysis')).toBeInTheDocument()
    })

    it('renders the estimated read time', () => {
      render(<ReadingCard {...defaultProps} />)
      expect(screen.getByText('5 min read')).toBeInTheDocument()
    })

    it('renders the priority badge', () => {
      render(<ReadingCard {...defaultProps} />)
      expect(screen.getByText('High')).toBeInTheDocument()
    })

    it('renders the Read Now button', () => {
      render(<ReadingCard {...defaultProps} />)
      expect(screen.getByRole('button', { name: 'Read Now' })).toBeInTheDocument()
    })
  })

  describe('question context', () => {
    it('renders question preview when provided and wasIncorrect is true', () => {
      render(
        <ReadingCard
          {...defaultProps}
          questionPreview="What is the best technique for..."
          wasIncorrect={true}
        />
      )
      expect(
        screen.getByText(/Added after incorrect answer on:.*What is the best technique for.../)
      ).toBeInTheDocument()
    })

    it('does not render question preview when wasIncorrect is false', () => {
      render(
        <ReadingCard
          {...defaultProps}
          questionPreview="What is the best technique for..."
          wasIncorrect={false}
        />
      )
      expect(
        screen.queryByText(/Added after incorrect answer/)
      ).not.toBeInTheDocument()
    })

    it('does not render question context when no questionPreview provided', () => {
      render(<ReadingCard {...defaultProps} wasIncorrect={true} />)
      expect(
        screen.queryByText(/Added after incorrect answer/)
      ).not.toBeInTheDocument()
    })
  })

  describe('interactions', () => {
    it('calls onReadNow with queueId when Read Now is clicked', () => {
      const onReadNow = vi.fn()
      render(<ReadingCard {...defaultProps} onReadNow={onReadNow} />)

      fireEvent.click(screen.getByRole('button', { name: 'Read Now' }))

      expect(onReadNow).toHaveBeenCalledTimes(1)
      expect(onReadNow).toHaveBeenCalledWith('queue-123')
    })
  })

  describe('accessibility', () => {
    it('has article role', () => {
      render(<ReadingCard {...defaultProps} />)
      expect(screen.getByRole('article')).toBeInTheDocument()
    })

    it('is focusable', () => {
      render(<ReadingCard {...defaultProps} />)
      const card = screen.getByRole('article')
      expect(card).toHaveAttribute('tabIndex', '0')
    })

    it('has aria-labelledby pointing to title', () => {
      render(<ReadingCard {...defaultProps} />)
      const card = screen.getByRole('article')
      const titleId = card.getAttribute('aria-labelledby')
      expect(titleId).toBeTruthy()

      // Verify the title element has this ID
      const title = screen.getByText('3.1: Introduction to Strategy Analysis')
      expect(title).toHaveAttribute('id', titleId)
    })
  })

  describe('priority variants', () => {
    it('renders High priority badge', () => {
      render(<ReadingCard {...defaultProps} priority="High" />)
      const badge = screen.getByText('High')
      expect(badge.className).toContain('bg-red-500')
    })

    it('renders Medium priority badge', () => {
      render(<ReadingCard {...defaultProps} priority="Medium" />)
      const badge = screen.getByText('Medium')
      expect(badge.className).toContain('bg-orange-500')
    })

    it('renders Low priority badge', () => {
      render(<ReadingCard {...defaultProps} priority="Low" />)
      const badge = screen.getByText('Low')
      expect(badge.className).toContain('bg-blue-500')
    })
  })
})
