import { useStaggeredAnimation } from '../../hooks/useScrollAnimation'

interface Feature {
  id: string
  icon: React.ReactNode
  headline: string
  description: string
}

const features: Feature[] = [
  {
    id: 'personalized',
    icon: (
      <svg className="w-10 h-10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09ZM18.259 8.715 18 9.75l-.259-1.035a3.375 3.375 0 0 0-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 0 0 2.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 0 0 2.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 0 0-2.456 2.456ZM16.894 20.567 16.5 21.75l-.394-1.183a2.25 2.25 0 0 0-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 0 0 1.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 0 0 1.423 1.423l1.183.394-1.183.394a2.25 2.25 0 0 0-1.423 1.423Z" />
      </svg>
    ),
    headline: 'Personalized Learning Path',
    description: 'Your learning journey adapts to your unique strengths and gaps. No two paths are the same, because no two learners are the same.',
  },
  {
    id: 'mastery',
    icon: (
      <svg className="w-10 h-10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12c0 1.268-.63 2.39-1.593 3.068a3.745 3.745 0 0 1-1.043 3.296 3.745 3.745 0 0 1-3.296 1.043A3.745 3.745 0 0 1 12 21c-1.268 0-2.39-.63-3.068-1.593a3.746 3.746 0 0 1-3.296-1.043 3.745 3.745 0 0 1-1.043-3.296A3.745 3.745 0 0 1 3 12c0-1.268.63-2.39 1.593-3.068a3.745 3.745 0 0 1 1.043-3.296 3.746 3.746 0 0 1 3.296-1.043A3.746 3.746 0 0 1 12 3c1.268 0 2.39.63 3.068 1.593a3.746 3.746 0 0 1 3.296 1.043 3.746 3.746 0 0 1 1.043 3.296A3.745 3.745 0 0 1 21 12Z" />
      </svg>
    ),
    headline: 'Complete Concept Mastery',
    description: 'Never miss a topic. We track what you know and systematically fill the gaps until you\'ve truly mastered every concept.',
  },
  {
    id: 'growth',
    icon: (
      <svg className="w-10 h-10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" />
      </svg>
    ),
    headline: 'Proven Competence Growth',
    description: 'Watch your skills develop with precision-measured progress. Know exactly where you stand and see real improvement over time.',
  },
]

/**
 * Features section explaining how the platform delivers benefits.
 * Uses friendly, non-technical language to explain BKT and IRT concepts.
 */
export function FeaturesSection() {
  const [containerRef, visibleItems] = useStaggeredAnimation<HTMLDivElement>({
    itemCount: features.length,
    threshold: 0.1,
    staggerDelay: 150,
  })

  return (
    <section
      className="px-4 sm:px-6 lg:px-8 py-120px"
      aria-labelledby="features-heading"
    >
      <div className="mx-auto max-w-content">
        {/* Section header */}
        <div className="text-center mb-16">
          <h2
            id="features-heading"
            className="text-section-sm sm:text-section-md text-charcoal"
          >
            How LearnR works
          </h2>
          <p className="mt-4 text-lg text-charcoal/70 max-w-2xl mx-auto">
            Cutting-edge learning science, wrapped in a simple and intuitive experience.
          </p>
        </div>

        {/* Features grid */}
        <div
          ref={containerRef}
          className="grid grid-cols-1 md:grid-cols-3 gap-8"
          role="list"
        >
          {features.map((feature, index) => (
            <article
              key={feature.id}
              role="listitem"
              className={`glass-card-solid p-8 text-center hover-lift shadow-card hover:shadow-card-hover
                transition-all duration-500 ease-out
                ${visibleItems[index]
                  ? 'opacity-100 translate-y-0'
                  : 'opacity-0 translate-y-8'
                }`}
            >
              {/* Icon */}
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary-100 to-primary-50 text-primary-600 flex items-center justify-center mx-auto mb-6">
                {feature.icon}
              </div>

              {/* Content */}
              <h3 className="text-xl font-semibold text-charcoal mb-3">
                {feature.headline}
              </h3>
              <p className="text-charcoal/70 leading-relaxed">
                {feature.description}
              </p>
            </article>
          ))}
        </div>
      </div>
    </section>
  )
}

export default FeaturesSection
