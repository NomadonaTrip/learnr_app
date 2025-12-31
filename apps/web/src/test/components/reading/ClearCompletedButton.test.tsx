/**
 * ClearCompletedButton Component Tests
 * Story 5.12: Clear Completed Reading Materials
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ClearCompletedButton } from '../../../components/reading/ClearCompletedButton'

describe('ClearCompletedButton', () => {
  const defaultProps = {
    count: 5,
    onClick: vi.fn(),
    isLoading: false,
  }

  describe('rendering', () => {
    it('renders the button with correct text', () => {
      render(<ClearCompletedButton {...defaultProps} />)
      expect(screen.getByRole('button', { name: /clear all 5 completed items/i })).toBeInTheDocument()
      expect(screen.getByText('Clear All Completed')).toBeInTheDocument()
    })

    it('renders trash icon when not loading', () => {
      render(<ClearCompletedButton {...defaultProps} />)
      const button = screen.getByRole('button')
      const svg = button.querySelector('svg')
      expect(svg).toBeInTheDocument()
      expect(svg).not.toHaveClass('animate-spin')
    })

    it('renders spinner icon when loading', () => {
      render(<ClearCompletedButton {...defaultProps} isLoading={true} />)
      const button = screen.getByRole('button')
      const svg = button.querySelector('svg')
      expect(svg).toBeInTheDocument()
      expect(svg).toHaveClass('animate-spin')
    })
  })

  describe('accessibility', () => {
    it('has correct aria-label with item count', () => {
      render(<ClearCompletedButton {...defaultProps} count={10} />)
      expect(screen.getByLabelText('Clear all 10 completed items')).toBeInTheDocument()
    })

    it('updates aria-label when count changes', () => {
      const { rerender } = render(<ClearCompletedButton {...defaultProps} count={3} />)
      expect(screen.getByLabelText('Clear all 3 completed items')).toBeInTheDocument()

      rerender(<ClearCompletedButton {...defaultProps} count={7} />)
      expect(screen.getByLabelText('Clear all 7 completed items')).toBeInTheDocument()
    })
  })

  describe('interactions', () => {
    it('calls onClick when clicked', () => {
      const onClick = vi.fn()
      render(<ClearCompletedButton {...defaultProps} onClick={onClick} />)

      fireEvent.click(screen.getByRole('button'))

      expect(onClick).toHaveBeenCalledTimes(1)
    })

    it('does not call onClick when disabled (loading)', () => {
      const onClick = vi.fn()
      render(<ClearCompletedButton {...defaultProps} onClick={onClick} isLoading={true} />)

      fireEvent.click(screen.getByRole('button'))

      expect(onClick).not.toHaveBeenCalled()
    })

    it('does not call onClick when count is 0', () => {
      const onClick = vi.fn()
      render(<ClearCompletedButton {...defaultProps} onClick={onClick} count={0} />)

      fireEvent.click(screen.getByRole('button'))

      expect(onClick).not.toHaveBeenCalled()
    })
  })

  describe('disabled states', () => {
    it('is disabled when isLoading is true', () => {
      render(<ClearCompletedButton {...defaultProps} isLoading={true} />)
      expect(screen.getByRole('button')).toBeDisabled()
    })

    it('is disabled when count is 0', () => {
      render(<ClearCompletedButton {...defaultProps} count={0} />)
      expect(screen.getByRole('button')).toBeDisabled()
    })

    it('is enabled when count > 0 and not loading', () => {
      render(<ClearCompletedButton {...defaultProps} />)
      expect(screen.getByRole('button')).not.toBeDisabled()
    })
  })

  describe('styling', () => {
    it('has ghost/outline styling', () => {
      render(<ClearCompletedButton {...defaultProps} />)
      const button = screen.getByRole('button')
      expect(button.className).toContain('border')
      expect(button.className).toContain('bg-white')
    })
  })
})
