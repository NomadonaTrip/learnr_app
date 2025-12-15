import { useState, useEffect, useRef } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import toast, { Toaster } from 'react-hot-toast'
import axios from 'axios'

import {
  accountCreationSchema,
  type AccountCreationFormData,
} from '../utils/accountValidation'
import { PasswordStrengthIndicator } from '../components/account/PasswordStrengthIndicator'
import { useOnboardingStorage } from '../hooks/useOnboardingStorage'
import { useAuthStore } from '../stores/authStore'
import { authService, formatOnboardingData } from '../services/authService'
import {
  trackRegistrationStarted,
  trackRegistrationCompleted,
  trackRegistrationFailed,
} from '../services/analyticsService'

/**
 * Account Creation Page component.
 * Displays registration form after onboarding, collects user info,
 * and submits to API with onboarding data.
 */
export function AccountCreationPage() {
  const navigate = useNavigate()
  const { answers, clearAnswers } = useOnboardingStorage()
  const { login } = useAuthStore()
  const [showPassword, setShowPassword] = useState(false)
  const hasTrackedView = useRef(false)
  const formContainerRef = useRef<HTMLDivElement>(null)

  const {
    register,
    handleSubmit,
    watch,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<AccountCreationFormData>({
    resolver: zodResolver(accountCreationSchema),
    mode: 'onBlur',
    defaultValues: {
      email: '',
      password: '',
      name: '',
      agreeToTerms: false,
    },
  })

  const password = watch('password')

  // Redirect to onboarding if missing required data
  useEffect(() => {
    if (!answers.course || !answers.motivation || !answers.familiarity) {
      navigate('/onboarding')
    }
  }, [answers, navigate])

  // Track page view
  useEffect(() => {
    if (!hasTrackedView.current) {
      trackRegistrationStarted()
      hasTrackedView.current = true
    }
  }, [])

  // Focus management on mount
  useEffect(() => {
    if (formContainerRef.current) {
      formContainerRef.current.focus()
    }
  }, [])

  const onSubmit = async (data: AccountCreationFormData) => {
    try {
      const onboardingData = formatOnboardingData(answers)

      const response = await authService.register({
        email: data.email,
        password: data.password,
        name: data.name || undefined,
        onboarding_data: onboardingData,
      })

      // Login user with returned token
      login(response.user, response.token)

      // Clear onboarding data from sessionStorage
      clearAnswers()

      // Track successful registration
      trackRegistrationCompleted({
        course: answers.course || '',
        motivation: answers.motivation || '',
      })

      // Show success message
      toast.success('Account created! Starting your diagnostic...')

      // Redirect to diagnostic
      navigate('/diagnostic')
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const status = error.response?.status

        if (status === 409) {
          // Email already exists
          setError('email', {
            type: 'manual',
            message: 'This email is already registered',
          })
          trackRegistrationFailed('email_exists')
        } else if (status === 422) {
          // Validation error from backend
          const details = error.response?.data?.error?.details
          if (details?.email) {
            setError('email', { type: 'manual', message: details.email })
          }
          if (details?.password) {
            setError('password', { type: 'manual', message: details.password })
          }
          trackRegistrationFailed('validation_error')
        } else {
          // Generic server error
          toast.error('Unable to create account. Please try again.')
          trackRegistrationFailed('server_error')
        }
      } else {
        toast.error('An unexpected error occurred. Please try again.')
        trackRegistrationFailed('unknown_error')
      }
    }
  }

  // If missing onboarding data, show nothing (will redirect)
  if (!answers.course || !answers.motivation || !answers.familiarity) {
    return null
  }

  return (
    <div className="min-h-screen bg-cream flex flex-col">
      <Toaster
        position="top-center"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#fff',
            color: '#121111',
            borderRadius: '14px',
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
          },
          success: {
            iconTheme: {
              primary: '#10b981',
              secondary: '#fff',
            },
          },
          error: {
            iconTheme: {
              primary: '#ef4444',
              secondary: '#fff',
            },
          },
        }}
      />

      <main className="flex-1 flex items-center justify-center px-4 py-8 sm:px-6 lg:px-8">
        <div className="w-full max-w-md">
          {/* Form card with glassmorphism */}
          <div
            ref={formContainerRef}
            tabIndex={-1}
            className="glass-card-solid p-8 sm:p-10 shadow-card animate-spring-in focus:outline-none"
          >
            {/* Header */}
            <div className="text-center mb-8">
              <h1 className="text-2xl sm:text-3xl font-semibold text-charcoal">
                Create your account
              </h1>
              <p className="mt-2 text-charcoal/70">
                You're almost ready to start learning
              </p>
            </div>

            {/* Registration form */}
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6" noValidate>
              {/* Email field */}
              <div>
                <label
                  htmlFor="email"
                  className="block text-sm font-medium text-charcoal mb-1"
                >
                  Email <span className="text-red-500" aria-label="required">*</span>
                </label>
                <input
                  id="email"
                  type="email"
                  autoComplete="email"
                  {...register('email')}
                  aria-required="true"
                  aria-invalid={!!errors.email}
                  aria-describedby={errors.email ? 'email-error' : undefined}
                  className={`
                    w-full px-4 py-3 text-base rounded-card border
                    bg-white/70 text-charcoal placeholder-charcoal/40
                    transition-colors duration-150
                    focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent
                    ${errors.email ? 'border-red-500' : 'border-charcoal/20 hover:border-charcoal/30'}
                  `}
                  placeholder="you@example.com"
                />
                {errors.email && (
                  <p
                    id="email-error"
                    className="mt-1 text-sm text-red-600"
                    role="alert"
                  >
                    {errors.email.message}
                  </p>
                )}
              </div>

              {/* Password field */}
              <div>
                <label
                  htmlFor="password"
                  className="block text-sm font-medium text-charcoal mb-1"
                >
                  Password <span className="text-red-500" aria-label="required">*</span>
                </label>
                <div className="relative">
                  <input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    autoComplete="new-password"
                    {...register('password')}
                    aria-required="true"
                    aria-invalid={!!errors.password}
                    aria-describedby={
                      errors.password
                        ? 'password-error password-requirements'
                        : 'password-requirements'
                    }
                    className={`
                      w-full px-4 py-3 pr-12 text-base rounded-card border
                      bg-white/70 text-charcoal placeholder-charcoal/40
                      transition-colors duration-150
                      focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent
                      ${errors.password ? 'border-red-500' : 'border-charcoal/20 hover:border-charcoal/30'}
                    `}
                    placeholder="Create a strong password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-charcoal/50 hover:text-charcoal transition-colors"
                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                  >
                    {showPassword ? (
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                      </svg>
                    ) : (
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                      </svg>
                    )}
                  </button>
                </div>
                <p
                  id="password-requirements"
                  className="mt-1 text-xs text-charcoal/50"
                >
                  8+ characters, 1 uppercase letter, 1 number
                </p>
                {errors.password && (
                  <p
                    id="password-error"
                    className="mt-1 text-sm text-red-600"
                    role="alert"
                  >
                    {errors.password.message}
                  </p>
                )}
                <PasswordStrengthIndicator password={password || ''} />
              </div>

              {/* Name field (optional) */}
              <div>
                <label
                  htmlFor="name"
                  className="block text-sm font-medium text-charcoal mb-1"
                >
                  Name <span className="text-charcoal/50">(optional)</span>
                </label>
                <input
                  id="name"
                  type="text"
                  autoComplete="name"
                  {...register('name')}
                  aria-invalid={!!errors.name}
                  aria-describedby={errors.name ? 'name-error' : undefined}
                  className={`
                    w-full px-4 py-3 text-base rounded-card border
                    bg-white/70 text-charcoal placeholder-charcoal/40
                    transition-colors duration-150
                    focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent
                    ${errors.name ? 'border-red-500' : 'border-charcoal/20 hover:border-charcoal/30'}
                  `}
                  placeholder="What should we call you?"
                />
                {errors.name && (
                  <p
                    id="name-error"
                    className="mt-1 text-sm text-red-600"
                    role="alert"
                  >
                    {errors.name.message}
                  </p>
                )}
              </div>

              {/* Terms checkbox */}
              <div>
                <label className="flex items-start gap-3 cursor-pointer group">
                  <div className="relative flex items-center">
                    <input
                      type="checkbox"
                      {...register('agreeToTerms')}
                      aria-required="true"
                      aria-invalid={!!errors.agreeToTerms}
                      aria-describedby={errors.agreeToTerms ? 'terms-error' : undefined}
                      className="
                        w-5 h-5 rounded border-2 border-charcoal/30
                        text-primary-500 focus:ring-2 focus:ring-primary-500 focus:ring-offset-2
                        cursor-pointer transition-colors
                        checked:border-primary-500
                      "
                    />
                  </div>
                  <span className="text-sm text-charcoal/70 group-hover:text-charcoal transition-colors">
                    I agree to the{' '}
                    <Link
                      to="/terms"
                      target="_blank"
                      className="text-primary-600 hover:text-primary-700 underline"
                      onClick={(e) => e.stopPropagation()}
                    >
                      Terms of Service
                    </Link>{' '}
                    and{' '}
                    <Link
                      to="/privacy"
                      target="_blank"
                      className="text-primary-600 hover:text-primary-700 underline"
                      onClick={(e) => e.stopPropagation()}
                    >
                      Privacy Policy
                    </Link>
                  </span>
                </label>
                {errors.agreeToTerms && (
                  <p
                    id="terms-error"
                    className="mt-1 text-sm text-red-600"
                    role="alert"
                  >
                    {errors.agreeToTerms.message}
                  </p>
                )}
              </div>

              {/* Submit button */}
              <button
                type="submit"
                disabled={isSubmitting}
                className={`
                  w-full py-3 px-6 text-base font-semibold rounded-card
                  transition-all duration-150
                  focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2
                  ${
                    isSubmitting
                      ? 'bg-primary-400 text-white cursor-not-allowed'
                      : 'bg-primary-500 text-white hover:bg-primary-600 hover-lift shadow-glass hover:shadow-glass-hover'
                  }
                `}
                aria-disabled={isSubmitting}
              >
                {isSubmitting ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg
                      className="animate-spin h-5 w-5"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                      aria-hidden="true"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      />
                    </svg>
                    Creating account...
                  </span>
                ) : (
                  'Create Account'
                )}
              </button>
            </form>

            {/* Login link */}
            <p className="mt-6 text-center text-sm text-charcoal/70">
              Already have an account?{' '}
              <Link
                to="/login"
                className="text-primary-600 hover:text-primary-700 font-medium underline"
              >
                Sign in
              </Link>
            </p>
          </div>
        </div>
      </main>
    </div>
  )
}
