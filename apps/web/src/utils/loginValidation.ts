import { z } from 'zod'

/**
 * Zod schema for login form validation.
 * Only requires valid email format and password presence.
 * No strength requirements for login (backend validates auth).
 */
export const loginSchema = z.object({
  email: z
    .string()
    .min(1, 'Email is required')
    .email('Please enter a valid email address'),

  password: z
    .string()
    .min(1, 'Password is required'),
})

export type LoginFormData = z.infer<typeof loginSchema>
