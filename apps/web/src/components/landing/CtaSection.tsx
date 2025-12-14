import { useNavigate } from 'react-router-dom'
import { useScrollAnimation } from '../../hooks/useScrollAnimation'
import { trackLandingCtaClicked } from '../../services/analyticsService'

interface CtaSectionProps {
  onStartExamPrep?: () => void
}

/**
 * Final CTA section positioned before footer.
 * Hero-variant design with compelling headline and gradient background.
 */
export function CtaSection({ onStartExamPrep }: CtaSectionProps) {
  const navigate = useNavigate()
  const [contentRef, isVisible] = useScrollAnimation<HTMLDivElement>({
    threshold: 0.2,
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

  return (
    <section
      className="relative px-4 sm:px-6 lg:px-8 py-120px overflow-hidden"
      aria-labelledby="cta-heading"
    >
      {/* Gradient background */}
      <div
        className="absolute inset-0 bg-gradient-to-br from-primary-600 via-primary-700 to-primary-800"
        aria-hidden="true"
      />

      {/* Decorative elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none" aria-hidden="true">
        <div
          className="absolute top-0 left-1/4 w-[600px] h-[600px] rounded-full opacity-10"
          style={{
            background: 'radial-gradient(circle, white 0%, transparent 70%)',
          }}
        />
        <div
          className="absolute bottom-0 right-1/4 w-[400px] h-[400px] rounded-full opacity-10"
          style={{
            background: 'radial-gradient(circle, white 0%, transparent 70%)',
          }}
        />
      </div>

      {/* Content */}
      <div
        ref={contentRef}
        className={`relative mx-auto max-w-content text-center transition-all duration-700 ease-out ${
          isVisible
            ? 'opacity-100 translate-y-0'
            : 'opacity-0 translate-y-8'
        }`}
      >
        {/* Glassmorphism container */}
        <div className="mx-auto max-w-2xl p-10 rounded-2xl bg-white/10 backdrop-blur-sm border border-white/20">
          <h2
            id="cta-heading"
            className="text-section-sm sm:text-section-md text-white"
          >
            Ready to start your journey?
          </h2>
          <p className="mt-4 text-lg text-white/80 max-w-xl mx-auto">
            Join thousands of learners who are achieving their certification goals with personalized, adaptive learning.
          </p>

          {/* CTA Button */}
          <button
            onClick={handleStartExamPrep}
            className="mt-8 px-10 py-4 bg-white text-primary-700 rounded-card font-semibold text-lg
              hover:bg-gray-50 hover-lift shadow-lg
              transition-all duration-200
              focus:outline-none focus-visible:ring-2 focus-visible:ring-white focus-visible:ring-offset-2 focus-visible:ring-offset-primary-700"
          >
            Start exam prep
          </button>
        </div>
      </div>
    </section>
  )
}

export default CtaSection
