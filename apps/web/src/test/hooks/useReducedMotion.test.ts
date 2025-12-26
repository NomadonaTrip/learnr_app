import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useReducedMotion } from '../../hooks/useReducedMotion'

describe('useReducedMotion', () => {
  let matchMediaMock: ReturnType<typeof vi.fn>
  let listeners: ((event: MediaQueryListEvent) => void)[] = []

  beforeEach(() => {
    listeners = []
    matchMediaMock = vi.fn().mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn((event: string, callback: (event: MediaQueryListEvent) => void) => {
        if (event === 'change') {
          listeners.push(callback)
        }
      }),
      removeEventListener: vi.fn((event: string, callback: (event: MediaQueryListEvent) => void) => {
        if (event === 'change') {
          listeners = listeners.filter((l) => l !== callback)
        }
      }),
      dispatchEvent: vi.fn(),
    }))

    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: matchMediaMock,
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('returns false when user does not prefer reduced motion', () => {
    matchMediaMock.mockImplementation(() => ({
      matches: false,
      media: '(prefers-reduced-motion: reduce)',
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    }))

    const { result } = renderHook(() => useReducedMotion())

    expect(result.current).toBe(false)
  })

  it('returns true when user prefers reduced motion', () => {
    matchMediaMock.mockImplementation(() => ({
      matches: true,
      media: '(prefers-reduced-motion: reduce)',
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    }))

    const { result } = renderHook(() => useReducedMotion())

    expect(result.current).toBe(true)
  })

  it('calls matchMedia with correct query', () => {
    renderHook(() => useReducedMotion())

    expect(matchMediaMock).toHaveBeenCalledWith('(prefers-reduced-motion: reduce)')
  })

  it('updates when preference changes', () => {
    const { result } = renderHook(() => useReducedMotion())

    expect(result.current).toBe(false)

    // Simulate preference change
    act(() => {
      listeners.forEach((listener) => {
        listener({ matches: true } as MediaQueryListEvent)
      })
    })

    expect(result.current).toBe(true)
  })

  it('cleans up event listener on unmount', () => {
    const removeEventListenerMock = vi.fn()
    matchMediaMock.mockImplementation(() => ({
      matches: false,
      media: '(prefers-reduced-motion: reduce)',
      addEventListener: vi.fn(),
      removeEventListener: removeEventListenerMock,
    }))

    const { unmount } = renderHook(() => useReducedMotion())

    unmount()

    expect(removeEventListenerMock).toHaveBeenCalledWith('change', expect.any(Function))
  })
})
