/**
 * UndoToast Component Tests
 * Story 5.12: Clear Completed Reading Materials
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, act } from '@testing-library/react'
import { UndoToast } from '../../../components/reading/UndoToast'

describe('UndoToast', () => {
  const defaultProps = {
    message: 'Item removed',
    isVisible: true,
    onDismiss: vi.fn(),
    onUndo: vi.fn(),
    duration: 5000,
  }

  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.clearAllMocks()
  })

  describe('rendering', () => {
    it('renders when isVisible is true', () => {
      render(<UndoToast {...defaultProps} />)
      expect(screen.getByRole('status')).toBeInTheDocument()
    })

    it('does not render when isVisible is false', () => {
      render(<UndoToast {...defaultProps} isVisible={false} />)
      expect(screen.queryByRole('status')).not.toBeInTheDocument()
    })

    it('renders the message', () => {
      render(<UndoToast {...defaultProps} message="Custom message" />)
      expect(screen.getByText('Custom message')).toBeInTheDocument()
    })

    it('renders checkmark icon', () => {
      render(<UndoToast {...defaultProps} />)
      const status = screen.getByRole('status')
      const svg = status.querySelector('svg')
      expect(svg).toBeInTheDocument()
    })

    it('renders Undo button when onUndo is provided', () => {
      render(<UndoToast {...defaultProps} />)
      expect(screen.getByRole('button', { name: /undo/i })).toBeInTheDocument()
    })

    it('does not render Undo button when onUndo is not provided', () => {
      render(<UndoToast {...defaultProps} onUndo={undefined} />)
      expect(screen.queryByRole('button', { name: /undo/i })).not.toBeInTheDocument()
    })
  })

  describe('accessibility', () => {
    it('has aria-live="polite" for screen reader announcements', () => {
      render(<UndoToast {...defaultProps} />)
      expect(screen.getByRole('status')).toHaveAttribute('aria-live', 'polite')
    })

    it('has role="status"', () => {
      render(<UndoToast {...defaultProps} />)
      expect(screen.getByRole('status')).toBeInTheDocument()
    })
  })

  describe('interactions', () => {
    it('calls onUndo and onDismiss when Undo button is clicked', () => {
      const onUndo = vi.fn()
      const onDismiss = vi.fn()
      render(<UndoToast {...defaultProps} onUndo={onUndo} onDismiss={onDismiss} />)

      fireEvent.click(screen.getByRole('button', { name: /undo/i }))

      expect(onUndo).toHaveBeenCalledTimes(1)
      expect(onDismiss).toHaveBeenCalledTimes(1)
    })
  })

  describe('auto-dismiss', () => {
    it('auto-dismisses after duration', () => {
      const onDismiss = vi.fn()
      render(<UndoToast {...defaultProps} onDismiss={onDismiss} duration={5000} />)

      expect(onDismiss).not.toHaveBeenCalled()

      act(() => {
        vi.advanceTimersByTime(5000)
      })

      expect(onDismiss).toHaveBeenCalledTimes(1)
    })

    it('uses custom duration', () => {
      const onDismiss = vi.fn()
      render(<UndoToast {...defaultProps} onDismiss={onDismiss} duration={3000} />)

      act(() => {
        vi.advanceTimersByTime(2999)
      })

      expect(onDismiss).not.toHaveBeenCalled()

      act(() => {
        vi.advanceTimersByTime(1)
      })

      expect(onDismiss).toHaveBeenCalledTimes(1)
    })

    it('does not auto-dismiss when not visible', () => {
      const onDismiss = vi.fn()
      render(<UndoToast {...defaultProps} isVisible={false} onDismiss={onDismiss} />)

      act(() => {
        vi.advanceTimersByTime(10000)
      })

      expect(onDismiss).not.toHaveBeenCalled()
    })

    it('clears timer when unmounted', () => {
      const onDismiss = vi.fn()
      const { unmount } = render(<UndoToast {...defaultProps} onDismiss={onDismiss} />)

      act(() => {
        vi.advanceTimersByTime(2500)
      })

      unmount()

      act(() => {
        vi.advanceTimersByTime(5000)
      })

      expect(onDismiss).not.toHaveBeenCalled()
    })

    it('resets timer when visibility changes', () => {
      const onDismiss = vi.fn()
      const { rerender } = render(
        <UndoToast {...defaultProps} onDismiss={onDismiss} duration={5000} />
      )

      act(() => {
        vi.advanceTimersByTime(3000)
      })

      // Hide and show again
      rerender(<UndoToast {...defaultProps} isVisible={false} onDismiss={onDismiss} />)
      rerender(<UndoToast {...defaultProps} isVisible={true} onDismiss={onDismiss} />)

      // Timer should reset, so 3000ms more should not trigger dismiss
      act(() => {
        vi.advanceTimersByTime(3000)
      })

      expect(onDismiss).not.toHaveBeenCalled()

      // But 5000ms total from new visibility should
      act(() => {
        vi.advanceTimersByTime(2000)
      })

      expect(onDismiss).toHaveBeenCalledTimes(1)
    })
  })

  describe('mobile responsiveness', () => {
    it('renders with responsive container', () => {
      render(<UndoToast {...defaultProps} />)
      const toast = screen.getByRole('status')
      // The toast should be inside a fixed positioned container
      // Check the element or its container has fixed positioning
      expect(toast).toBeInTheDocument()
      // The motion.div has the fixed class - check for it in the element or nearest ancestor
      const hasFixedPositioning =
        toast.className.includes('fixed') ||
        toast.parentElement?.className.includes('fixed') ||
        toast.closest('.fixed') !== null
      expect(hasFixedPositioning).toBe(true)
    })
  })

  describe('Framer Motion animations', () => {
    it('renders with motion wrapper', () => {
      render(<UndoToast {...defaultProps} />)
      // Framer Motion wraps the element - just verify it renders
      expect(screen.getByRole('status')).toBeInTheDocument()
    })
  })
})
