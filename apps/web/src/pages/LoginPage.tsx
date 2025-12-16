import { useEffect, useRef } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import toast, { Toaster } from 'react-hot-toast'
import axios from 'axios'

import { loginSchema, type LoginFormData } from '../utils/loginValidation'
import { useAuthStore } from '../stores/authStore'
import { authService } from '../services/authService'
import { useCountdown, formatCountdown } from '../hooks/useCountdown'

/**
 * Login Page component.
 * Displays login form for returning users, handles authentication via API,
 * and manages error states including rate limiting.
 */
export function LoginPage() {
  const navigate = useNavigate()
  const { login, isAuthenticated } = useAuthStore()
  const formContainerRef = useRef<HTMLDivElement>(null)
  const emailInputRef = useRef<HTMLInputElement | null>(null)

  // Rate limit countdown
  const { seconds: rateLimitSeconds, start: startCountdown, isActive: isRateLimited } = useCountdown(() => {
    // Auto-clear when countdown completes
    clearErrors('root')
  })

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setError,
    clearErrors,
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    mode: 'onBlur',
    defaultValues: {
      email: '',
      password: '',
    },
  })

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/diagnostic')
    }
  }, [isAuthenticated, navigate])

  // Auto-focus email field on mount
  useEffect(() => {
    if (emailInputRef.current) {
      emailInputRef.current.focus()
    }
  }, [])

  const onSubmit = async (data: LoginFormData) => {
    // Prevent submission if rate limited
    if (isRateLimited) {
      return
    }

    try {
      const response = await authService.login({
        email: data.email,
        password: data.password,
      })

      // Success: store auth state and redirect
      login(response.user, response.token)
      toast.success('Welcome back!')
      navigate('/diagnostic')
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const status = error.response?.status
        const errorData = error.response?.data?.error

        if (status === 401) {
          // Invalid credentials - show inline error
          setError('root', {
            type: 'manual',
            message: 'Invalid email or password',
          })
        } else if (status === 429) {
          // Rate limited - start countdown
          const retryAfter = errorData?.details?.retry_after_seconds || 900
          startCountdown(retryAfter)
          setError('root', {
            type: 'rate_limit',
            message: `Too many login attempts. Please try again in ${formatCountdown(retryAfter)}.`,
          })
        } else {
          // Server error - show toast
          toast.error('Unable to log in. Please try again.')
        }
      } else {
        // Network error
        toast.error('Network error. Check your connection.')
      }
    }
  }

  // Check if form should be disabled
  const isFormDisabled = isSubmitting || isRateLimited

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
                Welcome back
              </h1>
              <p className="mt-2 text-charcoal/70">
                Sign in to continue your learning journey
              </p>
            </div>

            {/* Root error display (401 / 429) */}
            {errors.root && (
              <div
                className={`mb-6 p-4 rounded-card border ${
                  isRateLimited
                    ? 'bg-amber-50 border-amber-200'
                    : 'bg-red-50 border-red-200'
                }`}
                role="alert"
                aria-live="polite"
              >
                <p className={`text-sm ${isRateLimited ? 'text-amber-700' : 'text-red-600'}`}>
                  {isRateLimited && rateLimitSeconds !== null
                    ? `Too many login attempts. Please try again in ${formatCountdown(rateLimitSeconds)}.`
                    : errors.root.message}
                </p>
              </div>
            )}

            {/* Login form */}
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6" noValidate>
              {/* Email field */}
              <div>
                <label
                  htmlFor="email"
                  className="block text-sm font-medium text-charcoal mb-1"
                >
                  Email
                </label>
                <input
                  id="email"
                  type="email"
                  autoComplete="email"
                  {...register('email')}
                  ref={(e) => {
                    register('email').ref(e)
                    emailInputRef.current = e
                  }}
                  disabled={isFormDisabled}
                  aria-required="true"
                  aria-invalid={!!errors.email}
                  aria-describedby={errors.email ? 'email-error' : undefined}
                  className={`
                    w-full px-4 py-3 text-base rounded-card border
                    bg-white/70 text-charcoal placeholder-charcoal/40
                    transition-colors duration-150
                    focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent
                    disabled:opacity-50 disabled:cursor-not-allowed
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
                <div className="flex items-center justify-between mb-1">
                  <label
                    htmlFor="password"
                    className="block text-sm font-medium text-charcoal"
                  >
                    Password
                  </label>
                  <Link
                    to="/forgot-password"
                    className="text-sm text-primary-600 hover:text-primary-700 font-medium"
                    tabIndex={isFormDisabled ? -1 : 0}
                  >
                    Forgot password?
                  </Link>
                </div>
                <input
                  id="password"
                  type="password"
                  autoComplete="current-password"
                  {...register('password')}
                  disabled={isFormDisabled}
                  aria-required="true"
                  aria-invalid={!!errors.password}
                  aria-describedby={errors.password ? 'password-error' : undefined}
                  className={`
                    w-full px-4 py-3 text-base rounded-card border
                    bg-white/70 text-charcoal placeholder-charcoal/40
                    transition-colors duration-150
                    focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent
                    disabled:opacity-50 disabled:cursor-not-allowed
                    ${errors.password ? 'border-red-500' : 'border-charcoal/20 hover:border-charcoal/30'}
                  `}
                  placeholder="Enter your password"
                />
                {errors.password && (
                  <p
                    id="password-error"
                    className="mt-1 text-sm text-red-600"
                    role="alert"
                  >
                    {errors.password.message}
                  </p>
                )}
              </div>

              {/* Submit button */}
              <button
                type="submit"
                disabled={isFormDisabled}
                aria-busy={isSubmitting}
                aria-disabled={isFormDisabled}
                className={`
                  w-full py-3 px-6 text-base font-semibold rounded-card
                  transition-all duration-150
                  focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2
                  ${
                    isFormDisabled
                      ? 'bg-primary-400 text-white cursor-not-allowed'
                      : 'bg-primary-500 text-white hover:bg-primary-600 hover-lift shadow-glass hover:shadow-glass-hover'
                  }
                `}
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
                    <span aria-live="polite">Signing in...</span>
                  </span>
                ) : (
                  'Sign In'
                )}
              </button>
            </form>

            {/* Register link */}
            <p className="mt-6 text-center text-sm text-charcoal/70">
              Don't have an account?{' '}
              <Link
                to="/onboarding"
                className="text-primary-600 hover:text-primary-700 font-medium underline"
              >
                Sign up
              </Link>
            </p>
          </div>
        </div>
      </main>
    </div>
  )
}
