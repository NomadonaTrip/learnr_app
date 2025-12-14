import { useStaggeredAnimation } from '../../hooks/useScrollAnimation'

interface Benefit {
  id: string
  icon: React.ReactNode
  headline: string
  description: string
}

const benefits: Benefit[] = [
  {
    id: 'career',
    icon: (
      <svg className="w-8 h-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21M3 3h12m-.75 4.5H21m-3.75 0v6.75" />
      </svg>
    ),
    headline: 'Change your career with ease',
    description: 'Build the skills employers are looking for and transition into your dream role with confidence.',
  },
  {
    id: 'certification',
    icon: (
      <svg className="w-8 h-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path strokeLinecap="round" strokeLinejoin="round" d="M4.26 10.147a60.438 60.438 0 0 0-.491 6.347A48.62 48.62 0 0 1 12 20.904a48.62 48.62 0 0 1 8.232-4.41 60.46 60.46 0 0 0-.491-6.347m-15.482 0a50.636 50.636 0 0 0-2.658-.813A59.906 59.906 0 0 1 12 3.493a59.903 59.903 0 0 1 10.399 5.84c-.896.248-1.783.52-2.658.814m-15.482 0A50.717 50.717 0 0 1 12 13.489a50.702 50.702 0 0 1 7.74-3.342M6.75 15a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5Zm0 0v-3.675A55.378 55.378 0 0 1 12 8.443m-7.007 11.55A5.981 5.981 0 0 0 6.75 15.75v-1.5" />
      </svg>
    ),
    headline: 'Ace that certification the first time',
    description: 'Our adaptive learning ensures you truly understand the material, not just memorize answers.',
  },
  {
    id: 'lifelong',
    icon: (
      <svg className="w-8 h-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 0 0 6 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 0 1 6 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 0 1 6-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0 0 18 18a8.967 8.967 0 0 0-6 2.292m0-14.25v14.25" />
      </svg>
    ),
    headline: 'Life-long learning made easy',
    description: 'Stay current in your field with bite-sized learning sessions that fit your busy schedule.',
  },
  {
    id: 'promotion',
    icon: (
      <svg className="w-8 h-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 18 9 11.25l4.306 4.306a11.95 11.95 0 0 1 5.814-5.518l2.74-1.22m0 0-5.94-2.281m5.94 2.28-2.28 5.941" />
      </svg>
    ),
    headline: 'Get that promotion',
    description: 'Demonstrate proven competence to stand out from the crowd and advance your career.',
  },
]

/**
 * Benefits section showcasing customer-focused outcomes.
 * Features staggered fade-in animations and glassmorphism cards.
 */
export function BenefitsSection() {
  const [containerRef, visibleItems] = useStaggeredAnimation<HTMLDivElement>({
    itemCount: benefits.length,
    threshold: 0.1,
    staggerDelay: 100,
  })

  return (
    <section
      className="px-4 sm:px-6 lg:px-8 py-120px bg-gradient-to-b from-cream to-white/50"
      aria-labelledby="benefits-heading"
    >
      <div className="mx-auto max-w-content">
        {/* Section header */}
        <div className="text-center mb-16">
          <h2
            id="benefits-heading"
            className="text-section-sm sm:text-section-md text-charcoal"
          >
            Achieve your goals
          </h2>
          <p className="mt-4 text-lg text-charcoal/70 max-w-2xl mx-auto">
            Join thousands of professionals who have transformed their careers with LearnR.
          </p>
        </div>

        {/* Benefits grid */}
        <div
          ref={containerRef}
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6"
          role="list"
        >
          {benefits.map((benefit, index) => (
            <article
              key={benefit.id}
              role="listitem"
              className={`glass-card p-6 hover-lift shadow-glass hover:shadow-glass-hover
                transition-all duration-500 ease-out
                ${visibleItems[index]
                  ? 'opacity-100 translate-y-0'
                  : 'opacity-0 translate-y-8'
                }`}
              style={{
                transitionDelay: visibleItems[index] ? '0ms' : `${index * 100}ms`,
              }}
            >
              {/* Icon */}
              <div className="w-12 h-12 rounded-xl bg-primary-100 text-primary-600 flex items-center justify-center mb-4">
                {benefit.icon}
              </div>

              {/* Content */}
              <h3 className="text-lg font-semibold text-charcoal mb-2">
                {benefit.headline}
              </h3>
              <p className="text-charcoal/70 text-sm leading-relaxed">
                {benefit.description}
              </p>
            </article>
          ))}
        </div>
      </div>
    </section>
  )
}

export default BenefitsSection
