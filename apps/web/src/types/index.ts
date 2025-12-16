// Shared TypeScript type definitions
// TODO: Move to packages/shared-types when implementing cross-app type sharing

export interface User {
  id: string
  email: string
  name: string
}

export interface ApiError {
  message: string
  code: string
}

// Onboarding types (Story 3.2)
export type FamiliarityLevel = 'new' | 'basics' | 'intermediate' | 'expert'
export type MotivationType = 'personal-interest' | 'certification' | 'professional-development' | 'career-change' | 'other'

export interface OnboardingAnswers {
  course?: string           // Q1: 'business-analysis'
  motivation?: MotivationType  // Q2: learning motivation
  familiarity?: FamiliarityLevel  // Q3: familiarity level
  initialBeliefPrior?: number  // Derived from Q3 (0.1, 0.3, 0.5, 0.7)
}

// Familiarity to BKT prior mapping
export const FAMILIARITY_PRIORS: Record<FamiliarityLevel, number> = {
  'new': 0.1,
  'basics': 0.3,
  'intermediate': 0.5,
  'expert': 0.7,
}
