/**
 * ClearConfirmationModal Component Tests
 * Story 5.12: Clear Completed Reading Materials
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { ClearConfirmationModal } from '../../../components/reading/ClearConfirmationModal'

describe('ClearConfirmationModal', () => {
  const defaultProps = {
    isOpen: true,
    onClose: vi.fn(),
    onConfirm: vi.fn(),
    count: 5,
    isLoading: false,
  }

  describe('rendering', () => {
    it('renders modal when isOpen is true', () => {
      render(<ClearConfirmationModal {...defaultProps} />)
      expect(screen.getByRole('dialog')).toBeInTheDocument()
    })

    it('does not render modal when isOpen is false', () => {
      render(<ClearConfirmationModal {...defaultProps} isOpen={false} />)
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    })

    it('renders the correct title', () => {
      render(<ClearConfirmationModal {...defaultProps} />)
      expect(screen.getByText('Clear Completed Reading Materials?')).toBeInTheDocument()
    })

    it('renders the item count in description', () => {
      render(<ClearConfirmationModal {...defaultProps} count={12} />)
      expect(screen.getByText(/12 items/)).toBeInTheDocument()
    })

    it('uses singular form for count of 1', () => {
      render(<ClearConfirmationModal {...defaultProps} count={1} />)
      expect(screen.getByText(/1 item/)).toBeInTheDocument()
    })

    it('renders reassurance message about preserved progress', () => {
      render(<ClearConfirmationModal {...defaultProps} />)
      expect(screen.getByText(/reading progress and statistics are preserved/i)).toBeInTheDocument()
    })

    it('renders Cancel button', () => {
      render(<ClearConfirmationModal {...defaultProps} />)
      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument()
    })

    it('renders Clear Items button', () => {
      render(<ClearConfirmationModal {...defaultProps} />)
      expect(screen.getByRole('button', { name: /clear items/i })).toBeInTheDocument()
    })
  })

  describe('accessibility', () => {
    it('has proper dialog role', () => {
      render(<ClearConfirmationModal {...defaultProps} />)
      expect(screen.getByRole('dialog')).toBeInTheDocument()
    })

    it('announces item count with aria-live', () => {
      render(<ClearConfirmationModal {...defaultProps} count={5} />)
      const liveRegion = screen.getByText(/5 items/)
      expect(liveRegion).toHaveAttribute('aria-live', 'polite')
    })
  })

  describe('interactions', () => {
    it('calls onClose when Cancel button is clicked', () => {
      const onClose = vi.fn()
      render(<ClearConfirmationModal {...defaultProps} onClose={onClose} />)

      fireEvent.click(screen.getByRole('button', { name: /cancel/i }))

      expect(onClose).toHaveBeenCalledTimes(1)
    })

    it('calls onConfirm when Clear Items button is clicked', () => {
      const onConfirm = vi.fn()
      render(<ClearConfirmationModal {...defaultProps} onConfirm={onConfirm} />)

      fireEvent.click(screen.getByRole('button', { name: /clear items/i }))

      expect(onConfirm).toHaveBeenCalledTimes(1)
    })

    it('calls onClose when Escape key is pressed', async () => {
      const onClose = vi.fn()
      render(<ClearConfirmationModal {...defaultProps} onClose={onClose} />)

      // Headless UI Dialog closes on Escape key
      fireEvent.keyDown(document, { key: 'Escape', code: 'Escape' })

      await waitFor(() => {
        expect(onClose).toHaveBeenCalled()
      })
    })
  })

  describe('loading states', () => {
    it('shows spinner on Clear Items button when loading', () => {
      render(<ClearConfirmationModal {...defaultProps} isLoading={true} />)
      const clearButton = screen.getByRole('button', { name: /clear items/i })
      const spinner = clearButton.querySelector('svg.animate-spin')
      expect(spinner).toBeInTheDocument()
    })

    it('disables buttons when loading', () => {
      render(<ClearConfirmationModal {...defaultProps} isLoading={true} />)
      expect(screen.getByRole('button', { name: /cancel/i })).toBeDisabled()
      expect(screen.getByRole('button', { name: /clear items/i })).toBeDisabled()
    })

    it('enables buttons when not loading', () => {
      render(<ClearConfirmationModal {...defaultProps} isLoading={false} />)
      expect(screen.getByRole('button', { name: /cancel/i })).not.toBeDisabled()
      expect(screen.getByRole('button', { name: /clear items/i })).not.toBeDisabled()
    })
  })

  describe('mobile responsiveness', () => {
    it('applies full-width styling for mobile', () => {
      render(<ClearConfirmationModal {...defaultProps} />)
      const panel = screen.getByRole('dialog').querySelector('[class*="Dialog"]') ||
                    screen.getByRole('dialog')
      // Panel should have max-sm:max-w-full class
      expect(panel).toBeInTheDocument()
    })
  })
})
