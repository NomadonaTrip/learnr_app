import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { SessionTimer } from '../../../components/diagnostic/SessionTimer'

describe('SessionTimer', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('renders nothing when startTime is null', () => {
    const { container } = render(
      <SessionTimer startTime={null} onTimeout={vi.fn()} />
    )
    expect(container.firstChild).toBeNull()
  })

  it('displays initial time of 30 minutes', () => {
    render(
      <SessionTimer startTime={new Date()} onTimeout={vi.fn()} />
    )
    expect(screen.getByText(/Time remaining: 30:00/)).toBeInTheDocument()
  })

  it('counts down correctly', () => {
    render(
      <SessionTimer startTime={new Date()} onTimeout={vi.fn()} />
    )

    act(() => {
      vi.advanceTimersByTime(1000)
    })

    expect(screen.getByText(/Time remaining: 29:59/)).toBeInTheDocument()
  })

  it('displays correct time after 10 minutes', () => {
    render(
      <SessionTimer startTime={new Date()} onTimeout={vi.fn()} />
    )

    act(() => {
      vi.advanceTimersByTime(10 * 60 * 1000)
    })

    expect(screen.getByText(/Time remaining: 20:00/)).toBeInTheDocument()
  })

  describe('warning at 25 minutes', () => {
    it('shows warning notification at 25 minutes', () => {
      render(
        <SessionTimer startTime={new Date()} onTimeout={vi.fn()} />
      )

      expect(screen.queryByRole('alert')).not.toBeInTheDocument()

      act(() => {
        vi.advanceTimersByTime(25 * 60 * 1000)
      })

      expect(screen.getByRole('alert')).toBeInTheDocument()
      expect(screen.getByText('5 minutes remaining!')).toBeInTheDocument()
    })

    it('calls onWarning callback at 25 minutes', () => {
      const onWarning = vi.fn()
      render(
        <SessionTimer startTime={new Date()} onTimeout={vi.fn()} onWarning={onWarning} />
      )

      act(() => {
        vi.advanceTimersByTime(25 * 60 * 1000)
      })

      expect(onWarning).toHaveBeenCalledTimes(1)
    })

    it('only calls onWarning once', () => {
      const onWarning = vi.fn()
      render(
        <SessionTimer startTime={new Date()} onTimeout={vi.fn()} onWarning={onWarning} />
      )

      act(() => {
        vi.advanceTimersByTime(25 * 60 * 1000)
      })

      act(() => {
        vi.advanceTimersByTime(1 * 60 * 1000)
      })

      expect(onWarning).toHaveBeenCalledTimes(1)
    })

    it('allows dismissing warning', async () => {
      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime })
      render(
        <SessionTimer startTime={new Date()} onTimeout={vi.fn()} />
      )

      act(() => {
        vi.advanceTimersByTime(25 * 60 * 1000)
      })

      expect(screen.getByRole('alert')).toBeInTheDocument()

      await user.click(screen.getByLabelText('Dismiss warning'))

      expect(screen.queryByRole('alert')).not.toBeInTheDocument()
    })
  })

  describe('timeout at 30 minutes', () => {
    it('calls onTimeout at 30 minutes', () => {
      const onTimeout = vi.fn()
      render(
        <SessionTimer startTime={new Date()} onTimeout={onTimeout} />
      )

      act(() => {
        vi.advanceTimersByTime(30 * 60 * 1000)
      })

      expect(onTimeout).toHaveBeenCalledTimes(1)
    })

    it('displays 0:00 at timeout', () => {
      render(
        <SessionTimer startTime={new Date()} onTimeout={vi.fn()} />
      )

      act(() => {
        vi.advanceTimersByTime(30 * 60 * 1000)
      })

      expect(screen.getByText(/Time remaining: 0:00/)).toBeInTheDocument()
    })
  })

  it('has aria-live assertive on warning', () => {
    render(
      <SessionTimer startTime={new Date()} onTimeout={vi.fn()} />
    )

    act(() => {
      vi.advanceTimersByTime(25 * 60 * 1000)
    })

    const alert = screen.getByRole('alert')
    expect(alert).toHaveAttribute('aria-live', 'assertive')
  })

  it('handles startTime in the past', () => {
    const pastTime = new Date(Date.now() - 10 * 60 * 1000) // 10 minutes ago
    render(
      <SessionTimer startTime={pastTime} onTimeout={vi.fn()} />
    )

    // Should show 20 minutes remaining
    expect(screen.getByText(/Time remaining: 20:00/)).toBeInTheDocument()
  })

  it('cleans up interval on unmount', () => {
    const clearIntervalSpy = vi.spyOn(globalThis, 'clearInterval')
    const { unmount } = render(
      <SessionTimer startTime={new Date()} onTimeout={vi.fn()} />
    )

    unmount()

    expect(clearIntervalSpy).toHaveBeenCalled()
  })
})
