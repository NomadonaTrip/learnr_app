import { COURSES } from './courseData'

interface QuestionCourseSelectionProps {
  value?: string
  onChange: (courseId: string) => void
}

/**
 * Q1: Course selection question.
 * Displays large button cards for each available course.
 */
export function QuestionCourseSelection({
  value,
  onChange,
}: QuestionCourseSelectionProps) {
  return (
    <fieldset className="w-full">
      <legend className="text-2xl md:text-3xl font-semibold text-charcoal mb-8">
        I want to learn...
      </legend>

      <div className="space-y-4">
        {COURSES.map((course) => {
          const isSelected = value === course.id
          return (
            <button
              key={course.id}
              type="button"
              onClick={() => onChange(course.id)}
              aria-pressed={isSelected}
              className={`
                w-full p-6 text-left rounded-card border-2 transition-all duration-150
                hover-lift focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2
                ${
                  isSelected
                    ? 'border-primary-500 bg-primary-50'
                    : 'border-charcoal/10 bg-white/90 hover:border-charcoal/20 hover:shadow-card-hover'
                }
              `}
            >
              <span className="block text-xl font-medium text-charcoal">
                {course.name}
              </span>
              <span className="block mt-1 text-sm text-charcoal/60">
                {course.description}
              </span>
            </button>
          )
        })}
      </div>
    </fieldset>
  )
}
