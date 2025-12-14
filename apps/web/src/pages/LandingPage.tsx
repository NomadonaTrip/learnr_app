import { useEffect } from 'react'
import { Navbar } from '../components/layout/Navbar'
import { Footer } from '../components/layout/Footer'
import { HeroSection } from '../components/landing/HeroSection'
import { BenefitsSection } from '../components/landing/BenefitsSection'
import { FeaturesSection } from '../components/landing/FeaturesSection'
import { CtaSection } from '../components/landing/CtaSection'
import { trackLandingPageViewed } from '../services/analyticsService'
import { useScrollDepthTracking } from '../hooks/useScrollDepthTracking'

/**
 * Marketing Landing Page (Story 3.1)
 *
 * Entry point to the LearnR platform with:
 * - Sticky navigation with glassmorphism effect
 * - Hero section with spring-based animations
 * - Benefits section with staggered card reveals
 * - Features section explaining adaptive learning
 * - Final CTA section before footer
 * - Accessible, responsive design following WCAG AA
 */
export function LandingPage() {
  // Track page view on mount
  useEffect(() => {
    trackLandingPageViewed()
  }, [])

  // Track scroll depth milestones
  useScrollDepthTracking()

  return (
    <div className="min-h-screen bg-cream">
      {/* Skip link for accessibility */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50
          focus:px-4 focus:py-2 focus:bg-primary-600 focus:text-white focus:rounded-lg
          focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
      >
        Skip to main content
      </a>

      {/* Navigation */}
      <header>
        <Navbar />
      </header>

      {/* Main content */}
      <main id="main-content">
        <HeroSection />
        <BenefitsSection />
        <FeaturesSection />
        <CtaSection />
      </main>

      {/* Footer */}
      <Footer />
    </div>
  )
}

export default LandingPage
