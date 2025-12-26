/**
 * ReadingBadge Component Tests
 * Story 5.6: Silent Badge Updates in Navigation
 */
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ReadingBadge } from '../../../components/layout/ReadingBadge'

describe('ReadingBadge', () => {
  describe('rendering', () => {
    it('renders with correct count', () => {
      render(<ReadingBadge count={7} />)
      expect(screen.getByText('7')).toBeInTheDocument()
    })

    it('renders count of 1 correctly', () => {
      render(<ReadingBadge count={1} />)
      expect(screen.getByText('1')).toBeInTheDocument()
    })

    it('renders large count with 99+ overflow', () => {
      render(<ReadingBadge count={150} />)
      expect(screen.getByText('99+')).toBeInTheDocument()
    })

    it('renders count of exactly 99 without overflow', () => {
      render(<ReadingBadge count={99} />)
      expect(screen.getByText('99')).toBeInTheDocument()
    })
  })

  describe('visibility', () => {
    it('does not render when count is 0', () => {
      const { container } = render(<ReadingBadge count={0} />)
      expect(container.firstChild).toBeNull()
    })

    it('does not render when count is negative', () => {
      const { container } = render(<ReadingBadge count={-1} />)
      expect(container.firstChild).toBeNull()
    })
  })

  describe('accessibility', () => {
    it('has role="status" attribute for live region', () => {
      render(<ReadingBadge count={5} />)
      expect(screen.getByRole('status')).toBeInTheDocument()
    })

    it('has aria-label with count and plural items', () => {
      render(<ReadingBadge count={7} />)
      expect(screen.getByLabelText('7 unread reading items')).toBeInTheDocument()
    })

    it('has aria-label with singular item when count is 1', () => {
      render(<ReadingBadge count={1} />)
      expect(screen.getByLabelText('1 unread reading item')).toBeInTheDocument()
    })

    it('uses correct singular/plural grammar in aria-label', () => {
      const { rerender } = render(<ReadingBadge count={1} />)
      expect(screen.getByRole('status')).toHaveAttribute(
        'aria-label',
        '1 unread reading item'
      )

      rerender(<ReadingBadge count={2} />)
      expect(screen.getByRole('status')).toHaveAttribute(
        'aria-label',
        '2 unread reading items'
      )
    })
  })

  describe('styling', () => {
    it('has orange background color class', () => {
      render(<ReadingBadge count={5} />)
      const badge = screen.getByRole('status')
      expect(badge.className).toContain('bg-orange-500')
    })

    it('has white text color class', () => {
      render(<ReadingBadge count={5} />)
      const badge = screen.getByRole('status')
      expect(badge.className).toContain('text-white')
    })

    it('has rounded-full class for circular shape', () => {
      render(<ReadingBadge count={5} />)
      const badge = screen.getByRole('status')
      expect(badge.className).toContain('rounded-full')
    })

    it('accepts additional className prop', () => {
      render(<ReadingBadge count={5} className="custom-class" />)
      const badge = screen.getByRole('status')
      expect(badge.className).toContain('custom-class')
    })
  })
})
