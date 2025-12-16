import { describe, it, expect } from 'vitest'
import {
  accountCreationSchema,
  calculatePasswordStrength,
} from '../../utils/accountValidation'

describe('accountCreationSchema', () => {
  describe('email validation', () => {
    it('validates correct email format', () => {
      const result = accountCreationSchema.safeParse({
        email: 'user@example.com',
        password: 'SecurePass123',
        agreeToTerms: true,
      })
      expect(result.success).toBe(true)
    })

    it('rejects empty email', () => {
      const result = accountCreationSchema.safeParse({
        email: '',
        password: 'SecurePass123',
        agreeToTerms: true,
      })
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.errors[0].path).toEqual(['email'])
        expect(result.error.errors[0].message).toBe('Email is required')
      }
    })

    it('rejects invalid email format', () => {
      const result = accountCreationSchema.safeParse({
        email: 'invalid-email',
        password: 'SecurePass123',
        agreeToTerms: true,
      })
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.errors[0].path).toEqual(['email'])
        expect(result.error.errors[0].message).toBe('Please enter a valid email address')
      }
    })

    it('rejects email without domain', () => {
      const result = accountCreationSchema.safeParse({
        email: 'user@',
        password: 'SecurePass123',
        agreeToTerms: true,
      })
      expect(result.success).toBe(false)
    })
  })

  describe('password validation', () => {
    it('accepts valid password with 8+ chars, uppercase, and number', () => {
      const result = accountCreationSchema.safeParse({
        email: 'user@example.com',
        password: 'SecurePass123',
        agreeToTerms: true,
      })
      expect(result.success).toBe(true)
    })

    it('rejects password shorter than 8 characters', () => {
      const result = accountCreationSchema.safeParse({
        email: 'user@example.com',
        password: 'Short1',
        agreeToTerms: true,
      })
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.errors[0].path).toEqual(['password'])
        expect(result.error.errors[0].message).toBe('Password must be at least 8 characters')
      }
    })

    it('rejects password without uppercase letter', () => {
      const result = accountCreationSchema.safeParse({
        email: 'user@example.com',
        password: 'lowercase123',
        agreeToTerms: true,
      })
      expect(result.success).toBe(false)
      if (!result.success) {
        const passwordErrors = result.error.errors.filter((e) => e.path[0] === 'password')
        expect(passwordErrors.some((e) => e.message.includes('uppercase'))).toBe(true)
      }
    })

    it('rejects password without number', () => {
      const result = accountCreationSchema.safeParse({
        email: 'user@example.com',
        password: 'NoNumbers',
        agreeToTerms: true,
      })
      expect(result.success).toBe(false)
      if (!result.success) {
        const passwordErrors = result.error.errors.filter((e) => e.path[0] === 'password')
        expect(passwordErrors.some((e) => e.message.includes('number'))).toBe(true)
      }
    })

    it('accepts password with special characters', () => {
      const result = accountCreationSchema.safeParse({
        email: 'user@example.com',
        password: 'Secure@Pass123!',
        agreeToTerms: true,
      })
      expect(result.success).toBe(true)
    })
  })

  describe('name validation', () => {
    it('allows optional name field', () => {
      const result = accountCreationSchema.safeParse({
        email: 'user@example.com',
        password: 'SecurePass123',
        agreeToTerms: true,
      })
      expect(result.success).toBe(true)
    })

    it('allows empty string for name', () => {
      const result = accountCreationSchema.safeParse({
        email: 'user@example.com',
        password: 'SecurePass123',
        name: '',
        agreeToTerms: true,
      })
      expect(result.success).toBe(true)
    })

    it('accepts valid name', () => {
      const result = accountCreationSchema.safeParse({
        email: 'user@example.com',
        password: 'SecurePass123',
        name: 'John Doe',
        agreeToTerms: true,
      })
      expect(result.success).toBe(true)
    })

    it('rejects name longer than 100 characters', () => {
      const result = accountCreationSchema.safeParse({
        email: 'user@example.com',
        password: 'SecurePass123',
        name: 'A'.repeat(101),
        agreeToTerms: true,
      })
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.errors[0].path).toEqual(['name'])
      }
    })
  })

  describe('agreeToTerms validation', () => {
    it('requires terms agreement', () => {
      const result = accountCreationSchema.safeParse({
        email: 'user@example.com',
        password: 'SecurePass123',
        agreeToTerms: false,
      })
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.errors[0].path).toEqual(['agreeToTerms'])
      }
    })

    it('accepts true for terms agreement', () => {
      const result = accountCreationSchema.safeParse({
        email: 'user@example.com',
        password: 'SecurePass123',
        agreeToTerms: true,
      })
      expect(result.success).toBe(true)
    })
  })
})

describe('calculatePasswordStrength', () => {
  it('returns empty state for empty password', () => {
    const result = calculatePasswordStrength('')
    expect(result.score).toBe(0)
    expect(result.label).toBe('')
  })

  it('returns Weak for short password', () => {
    const result = calculatePasswordStrength('abc')
    expect(result.score).toBeLessThanOrEqual(1)
    expect(result.label).toBe('Weak')
  })

  it('returns Fair for 8 char password with mixed case', () => {
    const result = calculatePasswordStrength('Abcdefgh')
    expect(result.score).toBeGreaterThanOrEqual(2)
    expect(['Fair', 'Good']).toContain(result.label)
  })

  it('returns Good for password with length, case, and numbers', () => {
    const result = calculatePasswordStrength('Abcdefgh1')
    expect(result.score).toBeGreaterThanOrEqual(3)
    expect(['Good', 'Strong']).toContain(result.label)
  })

  it('returns Strong for 12+ char password with all criteria', () => {
    const result = calculatePasswordStrength('Abcdefghij12')
    expect(result.score).toBeGreaterThanOrEqual(4)
    expect(['Strong', 'Very Strong']).toContain(result.label)
  })

  it('returns Very Strong for password with special characters', () => {
    const result = calculatePasswordStrength('Abcdefghij12!')
    expect(result.score).toBe(5)
    expect(result.label).toBe('Very Strong')
  })

  it('increments score for password length >= 8', () => {
    const short = calculatePasswordStrength('Ab1')
    const medium = calculatePasswordStrength('Abcdefg1')
    expect(medium.score).toBeGreaterThan(short.score)
  })

  it('increments score for password length >= 12', () => {
    const medium = calculatePasswordStrength('Abcdefg1')
    const long = calculatePasswordStrength('Abcdefghijk1')
    expect(long.score).toBeGreaterThan(medium.score)
  })
})
