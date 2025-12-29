/**
 * Toast Component Tests
 * Story 5.8: Reading Item Detail View and Engagement Tracking
 */
import { render, screen, fireEvent, act } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { Toast } from '../../../components/common/Toast'

describe('Toast', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('renders message and variant styling', () => {
    const onClose = vi.fn()
    render(
      <Toast message="Test message" variant="success" onClose={onClose} />
    )

    expect(screen.getByText('Test message')).toBeInTheDocument()
    expect(screen.getByRole('status')).toHaveClass('bg-green-500')
  })

  it('renders error variant with correct styling', () => {
    const onClose = vi.fn()
    render(
      <Toast message="Error message" variant="error" onClose={onClose} />
    )

    expect(screen.getByRole('status')).toHaveClass('bg-red-500')
  })

  it('renders info variant with correct styling', () => {
    const onClose = vi.fn()
    render(
      <Toast message="Info message" variant="info" onClose={onClose} />
    )

    expect(screen.getByRole('status')).toHaveClass('bg-blue-500')
  })

  it('calls onClose when dismiss button is clicked', () => {
    const onClose = vi.fn()
    render(
      <Toast message="Test message" variant="success" onClose={onClose} />
    )

    const dismissButton = screen.getByLabelText('Dismiss notification')
    fireEvent.click(dismissButton)

    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('auto-dismisses after default duration', () => {
    const onClose = vi.fn()
    render(
      <Toast message="Test message" variant="success" onClose={onClose} />
    )

    // Default duration is 3000ms
    act(() => {
      vi.advanceTimersByTime(3000)
    })

    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('auto-dismisses after custom duration', () => {
    const onClose = vi.fn()
    render(
      <Toast
        message="Test message"
        variant="success"
        duration={5000}
        onClose={onClose}
      />
    )

    // Should not have dismissed yet
    act(() => {
      vi.advanceTimersByTime(3000)
    })
    expect(onClose).not.toHaveBeenCalled()

    // Now it should dismiss
    act(() => {
      vi.advanceTimersByTime(2000)
    })
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('has proper accessibility attributes', () => {
    const onClose = vi.fn()
    render(
      <Toast message="Test message" variant="success" onClose={onClose} />
    )

    const toast = screen.getByRole('status')
    expect(toast).toHaveAttribute('aria-live', 'polite')
  })
})
