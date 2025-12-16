import { useNavigate } from 'react-router-dom'
import { useScrollState } from '../../hooks/useScrollState'
import { trackLandingCtaClicked } from '../../services/analyticsService'

interface NavbarProps {
  onGetStarted?: () => void
}

/**
 * Sticky navigation bar with glassmorphism effect on scroll.
 * Contains logo and "Get Started" CTA.
 */
export function Navbar({ onGetStarted }: NavbarProps) {
  const navigate = useNavigate()
  const { isScrolled } = useScrollState({ threshold: 20 })

  const handleGetStarted = () => {
    trackLandingCtaClicked('start_exam_prep')
    if (onGetStarted) {
      onGetStarted()
    } else {
      navigate('/onboarding')
    }
  }

  return (
    <nav
      className={`sticky top-0 z-40 transition-all duration-300 ${
        isScrolled ? 'glass-nav-scrolled' : 'glass-nav'
      }`}
      role="navigation"
      aria-label="Main navigation"
    >
      <div className="mx-auto max-w-content px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <a
            href="/"
            className="flex items-center gap-2 text-charcoal focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2 rounded-lg"
            aria-label="LearnR - Home"
          >
            <span className="text-xl font-semibold tracking-tight">LearnR</span>
          </a>

          {/* Get Started CTA */}
          <button
            onClick={handleGetStarted}
            className="px-5 py-2.5 bg-primary-600 text-white rounded-card font-medium text-sm
              hover:bg-primary-700 transition-colors duration-200
              focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2"
          >
            Get Started
          </button>
        </div>
      </div>
    </nav>
  )
}

export default Navbar
