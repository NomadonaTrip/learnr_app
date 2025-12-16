import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useCountdown, formatCountdown } from '../../hooks/useCountdown'

describe('useCountdown', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('starts with null seconds and inactive state', () => {
    const { result } = renderHook(() => useCountdown())

    expect(result.current.seconds).toBeNull()
    expect(result.current.isActive).toBe(false)
  })

  it('starts countdown when start() is called', () => {
    const { result } = renderHook(() => useCountdown())

    act(() => {
      result.current.start(10)
    })

    expect(result.current.seconds).toBe(10)
    expect(result.current.isActive).toBe(true)
  })

  it('decrements seconds every second', () => {
    const { result } = renderHook(() => useCountdown())

    act(() => {
      result.current.start(5)
    })

    expect(result.current.seconds).toBe(5)

    act(() => {
      vi.advanceTimersByTime(1000)
    })

    expect(result.current.seconds).toBe(4)

    act(() => {
      vi.advanceTimersByTime(1000)
    })

    expect(result.current.seconds).toBe(3)
  })

  it('stops at zero and calls onComplete', () => {
    const onComplete = vi.fn()
    const { result } = renderHook(() => useCountdown(onComplete))

    act(() => {
      result.current.start(2)
    })

    act(() => {
      vi.advanceTimersByTime(2000)
    })

    expect(result.current.seconds).toBe(0)
    expect(onComplete).toHaveBeenCalledTimes(1)
  })

  it('becomes inactive when countdown reaches zero', () => {
    const { result } = renderHook(() => useCountdown())

    act(() => {
      result.current.start(1)
    })

    expect(result.current.isActive).toBe(true)

    act(() => {
      vi.advanceTimersByTime(1000)
    })

    expect(result.current.seconds).toBe(0)
    expect(result.current.isActive).toBe(false)
  })

  it('reset() clears the countdown', () => {
    const { result } = renderHook(() => useCountdown())

    act(() => {
      result.current.start(10)
    })

    expect(result.current.isActive).toBe(true)

    act(() => {
      result.current.reset()
    })

    expect(result.current.seconds).toBeNull()
    expect(result.current.isActive).toBe(false)
  })

  it('can restart countdown after reset', () => {
    const { result } = renderHook(() => useCountdown())

    act(() => {
      result.current.start(5)
    })

    act(() => {
      vi.advanceTimersByTime(2000)
    })

    expect(result.current.seconds).toBe(3)

    act(() => {
      result.current.reset()
    })

    act(() => {
      result.current.start(10)
    })

    expect(result.current.seconds).toBe(10)
  })

  it('handles large countdown values', () => {
    const { result } = renderHook(() => useCountdown())

    act(() => {
      result.current.start(900) // 15 minutes
    })

    expect(result.current.seconds).toBe(900)
    expect(result.current.isActive).toBe(true)

    act(() => {
      vi.advanceTimersByTime(60000) // 1 minute
    })

    expect(result.current.seconds).toBe(840)
  })
})

describe('formatCountdown', () => {
  it('formats seconds only when less than 60', () => {
    expect(formatCountdown(45)).toBe('45 seconds')
    expect(formatCountdown(1)).toBe('1 second')
    expect(formatCountdown(0)).toBe('0 seconds')
  })

  it('formats minutes and seconds', () => {
    expect(formatCountdown(125)).toBe('2 minutes 5 seconds')
    expect(formatCountdown(61)).toBe('1 minute 1 second')
    expect(formatCountdown(90)).toBe('1 minute 30 seconds')
  })

  it('formats minutes only when seconds is zero', () => {
    expect(formatCountdown(60)).toBe('1 minute')
    expect(formatCountdown(120)).toBe('2 minutes')
    expect(formatCountdown(300)).toBe('5 minutes')
  })

  it('handles large values (15 minutes default rate limit)', () => {
    expect(formatCountdown(900)).toBe('15 minutes')
    expect(formatCountdown(899)).toBe('14 minutes 59 seconds')
  })

  it('uses correct singular/plural forms', () => {
    expect(formatCountdown(1)).toBe('1 second')
    expect(formatCountdown(2)).toBe('2 seconds')
    expect(formatCountdown(60)).toBe('1 minute')
    expect(formatCountdown(120)).toBe('2 minutes')
    expect(formatCountdown(61)).toBe('1 minute 1 second')
    expect(formatCountdown(122)).toBe('2 minutes 2 seconds')
  })
})
