import { useNavigate } from 'react-router-dom'
import { useScrollAnimation } from '../../hooks/useScrollAnimation'
import { trackLandingCtaClicked } from '../../services/analyticsService'

interface HeroSectionProps {
  onStartExamPrep?: () => void
  onLogin?: () => void
}

/**
 * Hero section with compelling headline, subtitle, and CTAs.
 * Features spring-based appear animation and parallax background elements.
 */
export function HeroSection({ onStartExamPrep, onLogin }: HeroSectionProps) {
  const navigate = useNavigate()
  const [contentRef, isVisible] = useScrollAnimation<HTMLDivElement>({
    threshold: 0.1,
    triggerOnce: true,
  })

  const handleStartExamPrep = () => {
    trackLandingCtaClicked('start_exam_prep')
    if (onStartExamPrep) {
      onStartExamPrep()
    } else {
      navigate('/onboarding')
    }
  }

  const handleLogin = () => {
    trackLandingCtaClicked('login')
    if (onLogin) {
      onLogin()
    } else {
      navigate('/login')
    }
  }

  return (
    <section
      className="relative overflow-hidden px-4 sm:px-6 lg:px-8 py-120px"
      aria-labelledby="hero-heading"
    >
      {/* Parallax background elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none" aria-hidden="true">
        {/* Gradient orb - top right */}
        <div
          className="absolute -top-40 -right-40 w-[500px] h-[500px] rounded-full opacity-30"
          style={{
            background: 'radial-gradient(circle, rgba(59, 130, 246, 0.3) 0%, transparent 70%)',
          }}
        />
        {/* Gradient orb - bottom left */}
        <div
          className="absolute -bottom-60 -left-40 w-[600px] h-[600px] rounded-full opacity-20"
          style={{
            background: 'radial-gradient(circle, rgba(59, 130, 246, 0.2) 0%, transparent 70%)',
          }}
        />
      </div>

      {/* Content */}
      <div
        ref={contentRef}
        className={`relative mx-auto max-w-content text-center transition-all duration-700 ease-out ${
          isVisible
            ? 'opacity-100 translate-y-0 scale-100'
            : 'opacity-0 translate-y-8 scale-95'
        }`}
      >
        <div className="mx-auto max-w-3xl">
          {/* Headline */}
          <h1
            id="hero-heading"
            className="text-hero-sm sm:text-hero-md lg:text-hero-lg text-charcoal tracking-tight"
          >
            Master your certification exam
          </h1>

          {/* Subtitle */}
          <p className="mt-6 text-lg sm:text-xl text-charcoal/70 max-w-2xl mx-auto leading-relaxed">
            Personalized learning that adapts to you. Build real competence, not just test-taking skills.
          </p>

          {/* CTAs */}
          <div className="mt-10 flex flex-col sm:flex-row gap-4 justify-center items-center">
            {/* Primary CTA */}
            <button
              onClick={handleStartExamPrep}
              className="w-full sm:w-auto px-8 py-4 bg-primary-600 text-white rounded-card font-semibold text-lg
                hover:bg-primary-700 hover-lift shadow-card hover:shadow-card-hover
                transition-all duration-200
                focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2"
            >
              Start exam prep
            </button>

            {/* Secondary link */}
            <button
              onClick={handleLogin}
              className="w-full sm:w-auto px-8 py-4 text-charcoal/80 font-medium
                hover:text-charcoal transition-colors duration-200
                focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2 rounded-card"
            >
              I already have an account
            </button>
          </div>
        </div>
      </div>
    </section>
  )
}

export default HeroSection
