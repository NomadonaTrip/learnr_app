import type { OnboardingAnswers, FamiliarityLevel } from '../types'
import { FAMILIARITY_PRIORS } from '../types'

const ONBOARDING_KEY = 'learnr_onboarding'

/**
 * Saves onboarding answers to sessionStorage.
 * Wrapped in try/catch to handle private browsing mode where sessionStorage may be unavailable.
 */
export function saveOnboardingAnswers(answers: OnboardingAnswers): void {
  try {
    sessionStorage.setItem(ONBOARDING_KEY, JSON.stringify(answers))
  } catch {
    console.warn('Unable to save onboarding answers to sessionStorage')
  }
}

/**
 * Updates a single answer in sessionStorage, preserving existing answers.
 */
export function updateOnboardingAnswer<K extends keyof OnboardingAnswers>(
  key: K,
  value: OnboardingAnswers[K]
): void {
  try {
    const current = getOnboardingAnswers() || {}
    const updated = { ...current, [key]: value }

    // If updating familiarity, also update the initialBeliefPrior
    if (key === 'familiarity' && value) {
      updated.initialBeliefPrior = FAMILIARITY_PRIORS[value as FamiliarityLevel]
    }

    sessionStorage.setItem(ONBOARDING_KEY, JSON.stringify(updated))
  } catch {
    console.warn('Unable to update onboarding answer in sessionStorage')
  }
}

/**
 * Retrieves onboarding answers from sessionStorage.
 * Returns null if no answers exist or sessionStorage is unavailable.
 */
export function getOnboardingAnswers(): OnboardingAnswers | null {
  try {
    const stored = sessionStorage.getItem(ONBOARDING_KEY)
    if (!stored) return null
    return JSON.parse(stored) as OnboardingAnswers
  } catch {
    return null
  }
}

/**
 * Clears all onboarding answers from sessionStorage.
 * Should be called after successful account creation.
 */
export function clearOnboardingAnswers(): void {
  try {
    sessionStorage.removeItem(ONBOARDING_KEY)
  } catch {
    // Ignore errors
  }
}

/**
 * Checks if onboarding is complete (all 3 questions answered).
 */
export function isOnboardingComplete(): boolean {
  const answers = getOnboardingAnswers()
  if (!answers) return false
  return !!(answers.course && answers.motivation && answers.familiarity)
}
