interface FamiliarityLevel {
  id: string
  label: string
  labelWithCourse: string
}

const FAMILIARITY_LEVELS: FamiliarityLevel[] = [
  { id: 'new', label: "I'm new to this", labelWithCourse: "I'm new to {course}" },
  { id: 'basics', label: 'I know the basics', labelWithCourse: 'I know the basics' },
  {
    id: 'intermediate',
    label: 'I have intermediate experience',
    labelWithCourse: 'I have intermediate experience',
  },
  {
    id: 'expert',
    label: "I'm an expert brushing up my skills",
    labelWithCourse: "I'm an expert brushing up my skills",
  },
]

interface QuestionFamiliarityProps {
  value?: string
  onChange: (familiarityId: string) => void
  courseName: string
}

/**
 * Q3: Familiarity level question.
 * Maps to BKT initial belief priors.
 */
export function QuestionFamiliarity({
  value,
  onChange,
  courseName,
}: QuestionFamiliarityProps) {
  return (
    <fieldset className="w-full">
      <legend className="text-2xl md:text-3xl font-semibold text-charcoal mb-8">
        How familiar are you with {courseName}?
      </legend>

      <div className="space-y-3">
        {FAMILIARITY_LEVELS.map((option) => {
          const isSelected = value === option.id
          const displayLabel = option.labelWithCourse.replace('{course}', courseName)
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
                {displayLabel}
              </span>
            </button>
          )
        })}
      </div>
    </fieldset>
  )
}
