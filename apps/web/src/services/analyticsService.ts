/**
 * Analytics service for tracking user events.
 * Uses PostHog for product analytics when available.
 * Falls back to console logging in development or when PostHog is not configured.
 */

type EventProperties = Record<string, string | number | boolean | null | undefined>

interface AnalyticsProvider {
  capture: (eventName: string, properties?: EventProperties) => void
}

/**
 * Check if PostHog is available on the window object.
 * PostHog is loaded via script tag and attaches to window.posthog
 */
function getPostHog(): AnalyticsProvider | null {
  if (typeof window !== 'undefined' && 'posthog' in window) {
    return window.posthog as AnalyticsProvider
  }
  return null
}

/**
 * Track an analytics event.
 * Uses PostHog if available, otherwise logs to console in development.
 */
export function trackEvent(eventName: string, properties?: EventProperties): void {
  const posthog = getPostHog()

  if (posthog) {
    posthog.capture(eventName, properties)
  } else if (import.meta.env.DEV) {
    console.log('[Analytics]', eventName, properties)
  }
}

/**
 * Landing page events
 */
export const LandingEvents = {
  PAGE_VIEWED: 'landing_page_viewed',
  CTA_CLICKED: 'landing_cta_clicked',
  SCROLL_DEPTH: 'landing_scroll_depth',
} as const

/**
 * Onboarding events
 */
export const OnboardingEvents = {
  STARTED: 'onboarding_started',
  QUESTION_VIEWED: 'onboarding_question_viewed',
  QUESTION_ANSWERED: 'onboarding_question_answered',
  COMPLETED: 'onboarding_completed',
} as const

/**
 * Track landing page view
 */
export function trackLandingPageViewed(): void {
  trackEvent(LandingEvents.PAGE_VIEWED)
}

/**
 * Track landing page CTA click
 */
export function trackLandingCtaClicked(cta: 'start_exam_prep' | 'login'): void {
  trackEvent(LandingEvents.CTA_CLICKED, { cta })
}

/**
 * Track onboarding started
 */
export function trackOnboardingStarted(): void {
  trackEvent(OnboardingEvents.STARTED)
}

/**
 * Track onboarding question viewed
 */
export function trackOnboardingQuestionViewed(questionId: string): void {
  trackEvent(OnboardingEvents.QUESTION_VIEWED, { questionId })
}

/**
 * Track onboarding question answered
 */
export function trackOnboardingQuestionAnswered(
  questionId: string,
  answer: string
): void {
  trackEvent(OnboardingEvents.QUESTION_ANSWERED, { questionId, answer })
}

/**
 * Track onboarding completed
 */
export function trackOnboardingCompleted(data: {
  course: string
  motivation: string
  familiarity: string
  initialBeliefPrior: number
}): void {
  trackEvent(OnboardingEvents.COMPLETED, data)
}

// Type declaration for PostHog on window
declare global {
  interface Window {
    posthog?: AnalyticsProvider
  }
}
