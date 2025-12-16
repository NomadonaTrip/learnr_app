interface Motivation {
  id: string
  label: string
}

const MOTIVATIONS: Motivation[] = [
  { id: 'personal-interest', label: 'Personal interest' },
  { id: 'certification', label: 'Certification' },
  { id: 'professional-development', label: 'Professional development' },
  { id: 'career-change', label: 'Career change' },
  { id: 'other', label: 'Other' },
]

interface QuestionMotivationProps {
  value?: string
  onChange: (motivationId: string) => void
  courseName: string
}

/**
 * Q2: Motivation question.
 * Asks why the user wants to learn the selected course.
 */
export function QuestionMotivation({
  value,
  onChange,
  courseName,
}: QuestionMotivationProps) {
  return (
    <fieldset className="w-full">
      <legend className="text-2xl md:text-3xl font-semibold text-charcoal mb-8">
        What's your 'why' for learning {courseName}?
      </legend>

      <div className="space-y-3">
        {MOTIVATIONS.map((option) => {
          const isSelected = value === option.id
          return (
            <button
              key={option.id}
              type="button"
              onClick={() => onChange(option.id)}
              aria-pressed={isSelected}
              className={`
                w-full py-4 px-6 text-left rounded-card border-2 transition-all duration-150
                hover-lift focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2
                ${
                  isSelected
                    ? 'border-primary-500 bg-primary-50'
                    : 'border-charcoal/10 bg-white/90 hover:border-charcoal/20 hover:shadow-card-hover'
                }
              `}
            >
              <span className="text-base md:text-lg font-medium text-charcoal">
                {option.label}
              </span>
            </button>
          )
        })}
      </div>
    </fieldset>
  )
}
