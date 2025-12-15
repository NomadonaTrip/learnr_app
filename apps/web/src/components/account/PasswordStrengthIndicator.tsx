import { calculatePasswordStrength } from '../../utils/accountValidation'

interface PasswordStrengthIndicatorProps {
  password: string
}

/**
 * Visual indicator showing password strength with color-coded bars.
 * Displays strength level: Weak, Fair, Good, Strong, Very Strong
 */
export function PasswordStrengthIndicator({ password }: PasswordStrengthIndicatorProps) {
  if (!password) return null

  const strength = calculatePasswordStrength(password)

  // Map color names to Tailwind classes
  const colorClasses: Record<string, { bar: string; text: string }> = {
    red: { bar: 'bg-red-500', text: 'text-red-600' },
    orange: { bar: 'bg-orange-500', text: 'text-orange-600' },
    yellow: { bar: 'bg-yellow-500', text: 'text-yellow-600' },
    green: { bar: 'bg-green-500', text: 'text-green-600' },
    emerald: { bar: 'bg-emerald-500', text: 'text-emerald-600' },
    gray: { bar: 'bg-gray-300', text: 'text-gray-500' },
  }

  const colors = colorClasses[strength.color] || colorClasses.gray

  return (
    <div className="mt-2" role="status" aria-live="polite">
      {/* Strength bars */}
      <div className="flex gap-1" aria-hidden="true">
        {[0, 1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className={`h-1 flex-1 rounded transition-colors duration-200 ${
              i < strength.score ? colors.bar : 'bg-gray-200'
            }`}
          />
        ))}
      </div>
      {/* Strength label */}
      <p className={`text-sm mt-1 ${colors.text}`}>
        <span className="sr-only">Password strength: </span>
        {strength.label}
      </p>
    </div>
  )
}
