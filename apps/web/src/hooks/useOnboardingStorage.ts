import { useState, useCallback } from 'react'

const STORAGE_KEY = 'learnr_onboarding'

export interface OnboardingAnswers {
  course?: string
  motivation?: string
  familiarity?: string
  initialBeliefPrior?: number
}

/**
 * Familiarity level to BKT prior mapping.
 * These values initialize the Bayesian Knowledge Tracing model.
 */
export const FAMILIARITY_PRIOR_MAP: Record<string, number> = {
  new: 0.1,
  basics: 0.3,
  intermediate: 0.5,
  expert: 0.7,
}

/**
 * Get the BKT belief prior from a familiarity level.
 */
export function getFamiliarityPrior(familiarity: string): number {
  return FAMILIARITY_PRIOR_MAP[familiarity] ?? 0.3
}

/**
 * Hook for managing onboarding answers in sessionStorage.
 * Persists data across questions and supports resume scenario.
 */
export function useOnboardingStorage() {
  const [answers, setAnswersState] = useState<OnboardingAnswers>(() => {
    try {
      const stored = sessionStorage.getItem(STORAGE_KEY)
      return stored ? JSON.parse(stored) : {}
    } catch {
      return {}
    }
  })

  const setAnswer = useCallback(
    <K extends keyof OnboardingAnswers>(key: K, value: OnboardingAnswers[K]) => {
      setAnswersState((prev) => {
        const updated = { ...prev, [key]: value }

        // Auto-compute belief prior when familiarity changes
        if (key === 'familiarity' && typeof value === 'string') {
          updated.initialBeliefPrior = getFamiliarityPrior(value)
        }

        try {
          sessionStorage.setItem(STORAGE_KEY, JSON.stringify(updated))
        } catch (error) {
          console.error('Failed to save onboarding progress', error)
        }

        return updated
      })
    },
    []
  )

  const clearAnswers = useCallback(() => {
    setAnswersState({})
    try {
      sessionStorage.removeItem(STORAGE_KEY)
    } catch (error) {
      console.error('Failed to clear onboarding progress', error)
    }
  }, [])

  return { answers, setAnswer, clearAnswers }
}
