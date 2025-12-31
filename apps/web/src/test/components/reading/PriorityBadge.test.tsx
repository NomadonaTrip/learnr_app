/**
 * PriorityBadge Component Tests
 * Story 5.7: Reading Library Page with Queue Display
 */
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { PriorityBadge } from '../../../components/common/PriorityBadge'

describe('PriorityBadge', () => {
  describe('rendering', () => {
    it('renders High priority correctly', () => {
      render(<PriorityBadge priority="High" />)
      expect(screen.getByText('High')).toBeInTheDocument()
    })

    it('renders Medium priority correctly', () => {
      render(<PriorityBadge priority="Medium" />)
      expect(screen.getByText('Medium')).toBeInTheDocument()
    })

    it('renders Low priority correctly', () => {
      render(<PriorityBadge priority="Low" />)
      expect(screen.getByText('Low')).toBeInTheDocument()
    })
  })

  describe('styling', () => {
    it('has red background for High priority', () => {
      render(<PriorityBadge priority="High" />)
      const badge = screen.getByText('High')
      expect(badge.className).toContain('bg-red-500')
    })

    it('has orange background for Medium priority', () => {
      render(<PriorityBadge priority="Medium" />)
      const badge = screen.getByText('Medium')
      expect(badge.className).toContain('bg-orange-500')
    })

    it('has blue background for Low priority', () => {
      render(<PriorityBadge priority="Low" />)
      const badge = screen.getByText('Low')
      expect(badge.className).toContain('bg-blue-500')
    })

    it('has white text color for all priorities', () => {
      const { rerender } = render(<PriorityBadge priority="High" />)
      expect(screen.getByText('High').className).toContain('text-white')

      rerender(<PriorityBadge priority="Medium" />)
      expect(screen.getByText('Medium').className).toContain('text-white')

      rerender(<PriorityBadge priority="Low" />)
      expect(screen.getByText('Low').className).toContain('text-white')
    })

    it('accepts additional className prop', () => {
      render(<PriorityBadge priority="High" className="custom-class" />)
      const badge = screen.getByText('High')
      expect(badge.className).toContain('custom-class')
    })
  })

  describe('accessibility', () => {
    it('has aria-label indicating priority level', () => {
      render(<PriorityBadge priority="High" />)
      expect(screen.getByLabelText('High priority')).toBeInTheDocument()
    })

    it('uses correct aria-label for each priority', () => {
      const { rerender } = render(<PriorityBadge priority="High" />)
      expect(screen.getByLabelText('High priority')).toBeInTheDocument()

      rerender(<PriorityBadge priority="Medium" />)
      expect(screen.getByLabelText('Medium priority')).toBeInTheDocument()

      rerender(<PriorityBadge priority="Low" />)
      expect(screen.getByLabelText('Low priority')).toBeInTheDocument()
    })
  })
})
