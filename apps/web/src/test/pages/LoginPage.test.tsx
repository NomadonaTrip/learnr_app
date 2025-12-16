import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { LoginPage } from '../../pages/LoginPage'
import { useAuthStore } from '../../stores/authStore'
import * as authService from '../../services/authService'
import axios from 'axios'
import toast from 'react-hot-toast'

// Mock react-hot-toast
vi.mock('react-hot-toast', async () => {
  const actual = await vi.importActual('react-hot-toast')
  return {
    ...actual,
    default: {
      success: vi.fn(),
      error: vi.fn(),
    },
  }
})

// Mock react-router-dom navigate
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

// Mock auth service
vi.mock('../../services/authService', () => ({
  authService: {
    login: vi.fn(),
  },
}))

// Helper functions for querying form elements
function getEmailInput() {
  return screen.getByRole('textbox', { name: /email/i })
}

function getPasswordInput() {
  return document.getElementById('password') as HTMLInputElement
}

function getSubmitButton() {
  return screen.getByRole('button', { name: /sign in/i })
}

function renderLoginPage() {
  return render(
    <BrowserRouter>
      <LoginPage />
    </BrowserRouter>
  )
}

describe('LoginPage', () => {
  beforeEach(() => {
    // Reset auth store
    useAuthStore.setState({
      user: null,
      token: null,
      isAuthenticated: false,
    })
    localStorage.clear()
    vi.clearAllMocks()
    vi.useFakeTimers({ shouldAdvanceTime: true })
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.resetAllMocks()
  })

  describe('rendering', () => {
    it('renders the login form', () => {
      renderLoginPage()

      expect(screen.getByRole('heading', { name: /welcome back/i })).toBeInTheDocument()
      expect(getEmailInput()).toBeInTheDocument()
      expect(getPasswordInput()).toBeInTheDocument()
      expect(getSubmitButton()).toBeInTheDocument()
    })

    it('renders forgot password link', () => {
      renderLoginPage()

      const forgotLink = screen.getByRole('link', { name: /forgot password/i })
      expect(forgotLink).toBeInTheDocument()
      expect(forgotLink).toHaveAttribute('href', '/forgot-password')
    })

    it('renders sign up link for new users', () => {
      renderLoginPage()

      const signUpLink = screen.getByRole('link', { name: /sign up/i })
      expect(signUpLink).toBeInTheDocument()
      expect(signUpLink).toHaveAttribute('href', '/onboarding')
    })

    it('displays subtitle text', () => {
      renderLoginPage()

      expect(screen.getByText(/sign in to continue your learning journey/i)).toBeInTheDocument()
    })
  })

  describe('form validation', () => {
    it('shows error when email is empty on blur', async () => {
      vi.useRealTimers()
      renderLoginPage()
      const user = userEvent.setup()

      const emailInput = getEmailInput()
      await user.click(emailInput)
      await user.tab()

      await waitFor(() => {
        expect(screen.getByText(/email is required/i)).toBeInTheDocument()
      })
    })

    it('shows error for invalid email format', async () => {
      vi.useRealTimers()
      renderLoginPage()
      const user = userEvent.setup()

      const emailInput = getEmailInput()
      await user.type(emailInput, 'invalid-email')
      await user.tab()

      await waitFor(() => {
        expect(screen.getByText(/please enter a valid email address/i)).toBeInTheDocument()
      })
    })

    it('shows error when password is empty on blur', async () => {
      vi.useRealTimers()
      renderLoginPage()
      const user = userEvent.setup()

      const passwordInput = getPasswordInput()
      await user.click(passwordInput)
      await user.tab()

      await waitFor(() => {
        expect(screen.getByText(/password is required/i)).toBeInTheDocument()
      })
    })

    it('clears validation error when valid input is provided', async () => {
      vi.useRealTimers()
      renderLoginPage()
      const user = userEvent.setup()

      const emailInput = getEmailInput()
      await user.click(emailInput)
      await user.tab()

      await waitFor(() => {
        expect(screen.getByText(/email is required/i)).toBeInTheDocument()
      })

      await user.type(emailInput, 'valid@example.com')
      await user.tab()

      await waitFor(() => {
        expect(screen.queryByText(/email is required/i)).not.toBeInTheDocument()
      })
    })
  })

  describe('form submission', () => {
    it('calls login API with form data', async () => {
      vi.useRealTimers()
      vi.mocked(authService.authService.login).mockResolvedValue({
        user: { id: '123', email: 'test@example.com', created_at: '2024-01-01' },
        token: 'jwt-token',
      })

      renderLoginPage()
      const user = userEvent.setup()

      await user.type(getEmailInput(), 'test@example.com')
      await user.type(getPasswordInput(), 'mypassword123')
      await user.click(getSubmitButton())

      await waitFor(() => {
        expect(authService.authService.login).toHaveBeenCalledWith({
          email: 'test@example.com',
          password: 'mypassword123',
        })
      })
    })

    it('redirects to /diagnostic on successful login', async () => {
      vi.useRealTimers()
      vi.mocked(authService.authService.login).mockResolvedValue({
        user: { id: '123', email: 'test@example.com', created_at: '2024-01-01' },
        token: 'jwt-token',
      })

      renderLoginPage()
      const user = userEvent.setup()

      await user.type(getEmailInput(), 'test@example.com')
      await user.type(getPasswordInput(), 'mypassword123')
      await user.click(getSubmitButton())

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/diagnostic')
      })
    })

    it('shows success toast on successful login', async () => {
      vi.useRealTimers()
      vi.mocked(authService.authService.login).mockResolvedValue({
        user: { id: '123', email: 'test@example.com', created_at: '2024-01-01' },
        token: 'jwt-token',
      })

      renderLoginPage()
      const user = userEvent.setup()

      await user.type(getEmailInput(), 'test@example.com')
      await user.type(getPasswordInput(), 'mypassword123')
      await user.click(getSubmitButton())

      await waitFor(() => {
        expect(toast.success).toHaveBeenCalledWith('Welcome back!')
      })
    })

    it('stores JWT token in auth store on success', async () => {
      vi.useRealTimers()
      vi.mocked(authService.authService.login).mockResolvedValue({
        user: { id: '123', email: 'test@example.com', created_at: '2024-01-01' },
        token: 'jwt-token-123',
      })

      renderLoginPage()
      const user = userEvent.setup()

      await user.type(getEmailInput(), 'test@example.com')
      await user.type(getPasswordInput(), 'mypassword123')
      await user.click(getSubmitButton())

      await waitFor(() => {
        const state = useAuthStore.getState()
        expect(state.isAuthenticated).toBe(true)
        expect(state.token).toBe('jwt-token-123')
      })
    })

    it('shows loading state during submission', async () => {
      vi.useRealTimers()
      let resolveLogin: ((value: authService.LoginResponse) => void) | undefined
      vi.mocked(authService.authService.login).mockImplementation(
        () =>
          new Promise<authService.LoginResponse>((resolve) => {
            resolveLogin = resolve
          })
      )

      renderLoginPage()
      const user = userEvent.setup()

      await user.type(getEmailInput(), 'test@example.com')
      await user.type(getPasswordInput(), 'mypassword123')
      await user.click(getSubmitButton())

      await waitFor(() => {
        expect(screen.getByText(/signing in/i)).toBeInTheDocument()
      })

      // Resolve the promise
      resolveLogin?.({
        user: { id: '123', email: 'test@example.com', created_at: '2024-01-01' },
        token: 'jwt-token',
      })

      await waitFor(() => {
        expect(screen.queryByText(/signing in/i)).not.toBeInTheDocument()
      })
    })
  })

  describe('error handling', () => {
    it('shows inline error for invalid credentials (401)', async () => {
      vi.useRealTimers()
      const error = new Error('Unauthorized') as Error & { response?: { status: number } }
      error.response = { status: 401 }
      vi.mocked(authService.authService.login).mockRejectedValue(error)
      vi.spyOn(axios, 'isAxiosError').mockReturnValue(true)

      renderLoginPage()
      const user = userEvent.setup()

      await user.type(getEmailInput(), 'test@example.com')
      await user.type(getPasswordInput(), 'wrongpassword')
      await user.click(getSubmitButton())

      await waitFor(() => {
        expect(screen.getByText(/invalid email or password/i)).toBeInTheDocument()
      })
    })

    it('shows rate limit error with countdown for 429', async () => {
      vi.useRealTimers()
      const error = new Error('Rate limited') as Error & {
        response?: {
          status: number
          data?: { error?: { details?: { retry_after_seconds: number } } }
        }
      }
      error.response = {
        status: 429,
        data: {
          error: {
            details: { retry_after_seconds: 60 },
          },
        },
      }
      vi.mocked(authService.authService.login).mockRejectedValue(error)
      vi.spyOn(axios, 'isAxiosError').mockReturnValue(true)

      renderLoginPage()
      const user = userEvent.setup()

      await user.type(getEmailInput(), 'test@example.com')
      await user.type(getPasswordInput(), 'password')
      await user.click(getSubmitButton())

      await waitFor(() => {
        expect(screen.getByText(/too many login attempts/i)).toBeInTheDocument()
      })
    })

    it('disables form when rate limited', async () => {
      vi.useRealTimers()
      const error = new Error('Rate limited') as Error & {
        response?: {
          status: number
          data?: { error?: { details?: { retry_after_seconds: number } } }
        }
      }
      error.response = {
        status: 429,
        data: {
          error: {
            details: { retry_after_seconds: 60 },
          },
        },
      }
      vi.mocked(authService.authService.login).mockRejectedValue(error)
      vi.spyOn(axios, 'isAxiosError').mockReturnValue(true)

      renderLoginPage()
      const user = userEvent.setup()

      await user.type(getEmailInput(), 'test@example.com')
      await user.type(getPasswordInput(), 'password')
      await user.click(getSubmitButton())

      await waitFor(() => {
        expect(getEmailInput()).toBeDisabled()
        expect(getPasswordInput()).toBeDisabled()
        expect(getSubmitButton()).toBeDisabled()
      })
    })

    it('shows toast for server error (500)', async () => {
      vi.useRealTimers()
      const error = new Error('Server error') as Error & { response?: { status: number } }
      error.response = { status: 500 }
      vi.mocked(authService.authService.login).mockRejectedValue(error)
      vi.spyOn(axios, 'isAxiosError').mockReturnValue(true)

      renderLoginPage()
      const user = userEvent.setup()

      await user.type(getEmailInput(), 'test@example.com')
      await user.type(getPasswordInput(), 'password')
      await user.click(getSubmitButton())

      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith('Unable to log in. Please try again.')
      })
    })

    it('shows toast for network error', async () => {
      vi.useRealTimers()
      const error = new Error('Network error')
      vi.mocked(authService.authService.login).mockRejectedValue(error)
      vi.spyOn(axios, 'isAxiosError').mockReturnValue(false)

      renderLoginPage()
      const user = userEvent.setup()

      await user.type(getEmailInput(), 'test@example.com')
      await user.type(getPasswordInput(), 'password')
      await user.click(getSubmitButton())

      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith('Network error. Check your connection.')
      })
    })
  })

  describe('authentication redirect', () => {
    it('redirects to /diagnostic if already authenticated', async () => {
      vi.useRealTimers()
      // Set authenticated state before render
      useAuthStore.setState({
        user: { id: '123', email: 'test@example.com', created_at: '2024-01-01' },
        token: 'existing-token',
        isAuthenticated: true,
      })

      renderLoginPage()

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/diagnostic')
      })
    })
  })

  describe('accessibility', () => {
    it('has proper ARIA labels on form fields', () => {
      renderLoginPage()

      const emailInput = getEmailInput()
      expect(emailInput).toHaveAttribute('aria-required', 'true')

      const passwordInput = getPasswordInput()
      expect(passwordInput).toHaveAttribute('aria-required', 'true')
    })

    it('marks invalid fields with aria-invalid', async () => {
      vi.useRealTimers()
      renderLoginPage()
      const user = userEvent.setup()

      const emailInput = getEmailInput()
      await user.type(emailInput, 'invalid')
      await user.tab()

      await waitFor(() => {
        expect(emailInput).toHaveAttribute('aria-invalid', 'true')
      })
    })

    it('has error messages with role="alert"', async () => {
      vi.useRealTimers()
      renderLoginPage()
      const user = userEvent.setup()

      const emailInput = getEmailInput()
      await user.click(emailInput)
      await user.tab()

      await waitFor(() => {
        const errorMessages = screen.getAllByRole('alert')
        expect(errorMessages.length).toBeGreaterThan(0)
      })
    })

    it('submit button has aria-busy attribute', () => {
      // Verify the button has aria-busy attribute in the DOM
      // The actual loading state is tested in "shows loading state during submission"
      renderLoginPage()

      const submitButton = getSubmitButton()
      // Button should have aria-busy attribute (false when not loading)
      expect(submitButton).toHaveAttribute('aria-busy', 'false')
    })

    it('error alert container has aria-live="polite"', async () => {
      vi.useRealTimers()
      const error = new Error('Unauthorized') as Error & { response?: { status: number } }
      error.response = { status: 401 }
      vi.mocked(authService.authService.login).mockRejectedValue(error)
      vi.spyOn(axios, 'isAxiosError').mockReturnValue(true)

      renderLoginPage()
      const user = userEvent.setup()

      await user.type(getEmailInput(), 'test@example.com')
      await user.type(getPasswordInput(), 'wrongpassword')
      await user.click(getSubmitButton())

      await waitFor(() => {
        const alertContainer = screen.getByRole('alert')
        expect(alertContainer).toHaveAttribute('aria-live', 'polite')
      })
    })
  })

  describe('navigation links', () => {
    it('forgot password link points to /forgot-password', () => {
      renderLoginPage()

      const forgotLink = screen.getByRole('link', { name: /forgot password/i })
      expect(forgotLink).toHaveAttribute('href', '/forgot-password')
    })

    it('sign up link points to /onboarding', () => {
      renderLoginPage()

      const signUpLink = screen.getByRole('link', { name: /sign up/i })
      expect(signUpLink).toHaveAttribute('href', '/onboarding')
    })
  })
})
