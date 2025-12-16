import { z } from 'zod'

/**
 * Validation schema for account creation form.
 * Enforces password requirements: 8+ chars, 1 uppercase, 1 number.
 */
export const accountCreationSchema = z.object({
  email: z
    .string()
    .min(1, 'Email is required')
    .email('Please enter a valid email address'),

  password: z
    .string()
    .min(8, 'Password must be at least 8 characters')
    .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
    .regex(/[0-9]/, 'Password must contain at least one number'),

  name: z
    .string()
    .max(100, 'Name must be less than 100 characters')
    .optional()
    .or(z.literal('')),

  agreeToTerms: z
    .boolean()
    .refine((val) => val === true, 'You must agree to the Terms of Service'),
})

export type AccountCreationFormData = z.infer<typeof accountCreationSchema>

/**
 * Password strength calculation.
 * Returns a score from 0-4 with corresponding label and color.
 */
export interface PasswordStrength {
  score: number
  label: string
  color: string
}

export function calculatePasswordStrength(password: string): PasswordStrength {
  if (!password) {
    return { score: 0, label: '', color: 'gray' }
  }

  let score = 0

  // Length checks
  if (password.length >= 8) score++
  if (password.length >= 12) score++

  // Character variety checks
  if (/[a-z]/.test(password) && /[A-Z]/.test(password)) score++
  if (/[0-9]/.test(password)) score++
  if (/[^A-Za-z0-9]/.test(password)) score++

  const labels = ['Weak', 'Fair', 'Good', 'Strong', 'Very Strong']
  const colors = ['red', 'orange', 'yellow', 'green', 'emerald']

  const index = Math.min(score, 4)
  return {
    score,
    label: labels[index],
    color: colors[index],
  }
}
