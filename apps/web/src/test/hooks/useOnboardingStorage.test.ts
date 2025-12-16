import { describe, it, expect, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import {
  useOnboardingStorage,
  getFamiliarityPrior,
  FAMILIARITY_PRIOR_MAP,
} from '../../hooks/useOnboardingStorage'

const STORAGE_KEY = 'learnr_onboarding'

describe('useOnboardingStorage', () => {
  beforeEach(() => {
    // Clear all items from sessionStorage
    sessionStorage.clear()
    // Explicitly remove our key to ensure clean state
    sessionStorage.removeItem(STORAGE_KEY)
  })

  it('returns empty answers initially', () => {
    const { result } = renderHook(() => useOnboardingStorage())
    expect(result.current.answers).toEqual({})
  })

  it('persists course answer to sessionStorage', () => {
    const { result } = renderHook(() => useOnboardingStorage())

    act(() => {
      result.current.setAnswer('course', 'cbap')
    })

    expect(result.current.answers.course).toBe('cbap')
    const stored = sessionStorage.getItem(STORAGE_KEY)
    expect(stored).toBeTruthy()
    expect(JSON.parse(stored!)).toEqual({
      course: 'cbap',
    })
  })

  it('persists motivation answer to sessionStorage', () => {
    const { result } = renderHook(() => useOnboardingStorage())

    act(() => {
      result.current.setAnswer('motivation', 'certification')
    })

    expect(result.current.answers.motivation).toBe('certification')
  })

  it('auto-computes belief prior when familiarity is set', () => {
    const { result } = renderHook(() => useOnboardingStorage())

    act(() => {
      result.current.setAnswer('familiarity', 'basics')
    })

    expect(result.current.answers.familiarity).toBe('basics')
    expect(result.current.answers.initialBeliefPrior).toBe(0.3)
  })

  it('loads existing answers from sessionStorage on mount', () => {
    // Set up storage before hook renders
    const existingData = {
      course: 'cbap',
      motivation: 'career-change',
    }
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(existingData))

    // Render hook AFTER setting storage
    const { result } = renderHook(() => useOnboardingStorage())

    expect(result.current.answers.course).toBe('cbap')
    expect(result.current.answers.motivation).toBe('career-change')
  })

  it('clears all answers from sessionStorage', () => {
    const { result } = renderHook(() => useOnboardingStorage())

    act(() => {
      result.current.setAnswer('course', 'cbap')
      result.current.setAnswer('motivation', 'certification')
    })

    act(() => {
      result.current.clearAnswers()
    })

    expect(result.current.answers).toEqual({})
    // jsdom returns undefined for missing keys, so check for falsy
    expect(sessionStorage.getItem(STORAGE_KEY)).toBeFalsy()
  })

  it('handles corrupted sessionStorage gracefully', () => {
    sessionStorage.setItem(STORAGE_KEY, 'not-valid-json')

    const { result } = renderHook(() => useOnboardingStorage())
    expect(result.current.answers).toEqual({})
  })
})

describe('getFamiliarityPrior', () => {
  it('returns 0.1 for new', () => {
    expect(getFamiliarityPrior('new')).toBe(0.1)
  })

  it('returns 0.3 for basics', () => {
    expect(getFamiliarityPrior('basics')).toBe(0.3)
  })

  it('returns 0.5 for intermediate', () => {
    expect(getFamiliarityPrior('intermediate')).toBe(0.5)
  })

  it('returns 0.7 for expert', () => {
    expect(getFamiliarityPrior('expert')).toBe(0.7)
  })

  it('returns 0.3 (default) for unknown familiarity', () => {
    expect(getFamiliarityPrior('unknown')).toBe(0.3)
  })
})

describe('FAMILIARITY_PRIOR_MAP', () => {
  it('contains all four familiarity levels', () => {
    expect(Object.keys(FAMILIARITY_PRIOR_MAP)).toEqual([
      'new',
      'basics',
      'intermediate',
      'expert',
    ])
  })
})
