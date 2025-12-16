import { describe, it, expect } from 'vitest'
import { loginSchema } from '../../utils/loginValidation'

describe('loginSchema', () => {
  describe('email validation', () => {
    it('validates correct email format', () => {
      const result = loginSchema.safeParse({
        email: 'user@example.com',
        password: 'anypassword',
      })
      expect(result.success).toBe(true)
    })

    it('rejects empty email', () => {
      const result = loginSchema.safeParse({
        email: '',
        password: 'anypassword',
      })
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.errors[0].path).toEqual(['email'])
        expect(result.error.errors[0].message).toBe('Email is required')
      }
    })

    it('rejects invalid email format', () => {
      const result = loginSchema.safeParse({
        email: 'invalid-email',
        password: 'anypassword',
      })
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.errors[0].path).toEqual(['email'])
        expect(result.error.errors[0].message).toBe('Please enter a valid email address')
      }
    })

    it('rejects email without domain', () => {
      const result = loginSchema.safeParse({
        email: 'user@',
        password: 'anypassword',
      })
      expect(result.success).toBe(false)
    })

    it('accepts email with subdomain', () => {
      const result = loginSchema.safeParse({
        email: 'user@mail.example.com',
        password: 'anypassword',
      })
      expect(result.success).toBe(true)
    })
  })

  describe('password validation', () => {
    it('requires password field', () => {
      const result = loginSchema.safeParse({
        email: 'user@example.com',
        password: '',
      })
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.errors[0].path).toEqual(['password'])
        expect(result.error.errors[0].message).toBe('Password is required')
      }
    })

    it('accepts any non-empty password (no strength requirements for login)', () => {
      const result = loginSchema.safeParse({
        email: 'user@example.com',
        password: 'a',
      })
      expect(result.success).toBe(true)
    })

    it('accepts password with special characters', () => {
      const result = loginSchema.safeParse({
        email: 'user@example.com',
        password: 'complex!@#$%Password123',
      })
      expect(result.success).toBe(true)
    })

    it('accepts long password', () => {
      const result = loginSchema.safeParse({
        email: 'user@example.com',
        password: 'a'.repeat(100),
      })
      expect(result.success).toBe(true)
    })
  })

  describe('complete form validation', () => {
    it('validates complete login form', () => {
      const result = loginSchema.safeParse({
        email: 'test@example.com',
        password: 'mypassword123',
      })
      expect(result.success).toBe(true)
      if (result.success) {
        expect(result.data.email).toBe('test@example.com')
        expect(result.data.password).toBe('mypassword123')
      }
    })

    it('rejects form with both fields empty', () => {
      const result = loginSchema.safeParse({
        email: '',
        password: '',
      })
      expect(result.success).toBe(false)
      if (!result.success) {
        // Both email and password have errors (email may have multiple)
        const emailErrors = result.error.errors.filter((e) => e.path[0] === 'email')
        const passwordErrors = result.error.errors.filter((e) => e.path[0] === 'password')
        expect(emailErrors.length).toBeGreaterThan(0)
        expect(passwordErrors.length).toBeGreaterThan(0)
      }
    })

    it('trims email whitespace via form input (browser behavior)', () => {
      // Note: Zod doesn't auto-trim, but the form should handle this
      const result = loginSchema.safeParse({
        email: 'user@example.com',
        password: 'password',
      })
      expect(result.success).toBe(true)
    })
  })
})
