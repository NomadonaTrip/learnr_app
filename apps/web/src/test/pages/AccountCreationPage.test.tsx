import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { AccountCreationPage } from '../../pages/AccountCreationPage'
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

const mockOnboardingData = {
  course: 'cbap',
  motivation: 'certification',
  familiarity: 'basics',
  initialBeliefPrior: 0.3,
}

const mockClearAnswers = vi.fn()

// Mock useOnboardingStorage hook
vi.mock('../../hooks/useOnboardingStorage', () => ({
  useOnboardingStorage: () => ({
    answers: mockOnboardingData,
    setAnswer: vi.fn(),
    clearAnswers: mockClearAnswers,
  }),
}))

// Mock auth service
vi.mock('../../services/authService', () => ({
  authService: {
    register: vi.fn(),
  },
  formatOnboardingData: vi.fn().mockImplementation((answers) => {
    if (!answers?.course || !answers?.motivation || !answers?.familiarity) {
      return undefined
    }
    return {
      course: answers.course,
      motivation: answers.motivation,
      familiarity: answers.familiarity,
      initialBeliefPrior: answers.initialBeliefPrior ?? 0.3,
    }
  }),
}))

// Mock analytics
vi.mock('../../services/analyticsService', () => ({
  trackRegistrationStarted: vi.fn(),
  trackRegistrationCompleted: vi.fn(),
  trackRegistrationFailed: vi.fn(),
}))

// Helper functions for querying form elements
function getEmailInput() {
  return screen.getByRole('textbox', { name: /email/i })
}

function getPasswordInput() {
  return document.getElementById('password') as HTMLInputElement
}

function getNameInput() {
  return screen.getByRole('textbox', { name: /name/i })
}

function getTermsCheckbox() {
  return screen.getByRole('checkbox')
}

function getSubmitButton() {
  return screen.getByRole('button', { name: /create account/i })
}

function renderAccountCreationPage() {
  return render(
    <BrowserRouter>
      <AccountCreationPage />
    </BrowserRouter>
  )
}

describe('AccountCreationPage', () => {
  beforeEach(() => {
    // Reset auth store
    useAuthStore.setState({
      user: null,
      token: null,
      isAuthenticated: false,
    })
    localStorage.clear()
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.resetAllMocks()
  })

  describe('rendering', () => {
    it('renders the registration form', () => {
      renderAccountCreationPage()

      expect(screen.getByRole('heading', { name: /create your account/i })).toBeInTheDocument()
      expect(getEmailInput()).toBeInTheDocument()
      expect(getPasswordInput()).toBeInTheDocument()
      expect(getNameInput()).toBeInTheDocument()
      expect(getSubmitButton()).toBeInTheDocument()
    })

    it('renders terms and privacy policy links', () => {
      renderAccountCreationPage()

      expect(screen.getByRole('link', { name: /terms of service/i })).toBeInTheDocument()
      expect(screen.getByRole('link', { name: /privacy policy/i })).toBeInTheDocument()
    })

    it('renders login link for existing users', () => {
      renderAccountCreationPage()

      expect(screen.getByRole('link', { name: /sign in/i })).toBeInTheDocument()
    })
  })

  describe('form validation', () => {
    it('shows error when email is empty on blur', async () => {
      renderAccountCreationPage()
      const user = userEvent.setup()

      const emailInput = getEmailInput()
      await user.click(emailInput)
      await user.tab()

      await waitFor(() => {
        expect(screen.getByText(/email is required/i)).toBeInTheDocument()
      })
    })

    it('shows error for invalid email format', async () => {
      renderAccountCreationPage()
      const user = userEvent.setup()

      const emailInput = getEmailInput()
      await user.type(emailInput, 'invalid-email')
      await user.tab()

      await waitFor(() => {
        expect(screen.getByText(/please enter a valid email address/i)).toBeInTheDocument()
      })
    })

    it('shows error for short password', async () => {
      renderAccountCreationPage()
      const user = userEvent.setup()

      const passwordInput = getPasswordInput()
      await user.type(passwordInput, 'short')
      await user.tab()

      await waitFor(() => {
        expect(screen.getByText(/password must be at least 8 characters/i)).toBeInTheDocument()
      })
    })

    it('shows error for password without uppercase', async () => {
      renderAccountCreationPage()
      const user = userEvent.setup()

      const passwordInput = getPasswordInput()
      await user.type(passwordInput, 'lowercase123')
      await user.tab()

      await waitFor(() => {
        expect(screen.getByText(/password must contain at least one uppercase letter/i)).toBeInTheDocument()
      })
    })

    it('shows error for password without number', async () => {
      renderAccountCreationPage()
      const user = userEvent.setup()

      const passwordInput = getPasswordInput()
      await user.type(passwordInput, 'NoNumbers')
      await user.tab()

      await waitFor(() => {
        expect(screen.getByText(/password must contain at least one number/i)).toBeInTheDocument()
      })
    })

    it('shows error when terms not agreed', async () => {
      renderAccountCreationPage()
      const user = userEvent.setup()

      await user.type(getEmailInput(), 'test@example.com')
      await user.type(getPasswordInput(), 'SecurePass123')
      await user.click(getSubmitButton())

      await waitFor(() => {
        expect(screen.getByText(/you must agree to the terms of service/i)).toBeInTheDocument()
      })
    })
  })

  describe('password visibility toggle', () => {
    it('toggles password visibility', async () => {
      renderAccountCreationPage()
      const user = userEvent.setup()

      const passwordInput = getPasswordInput()
      await user.type(passwordInput, 'SecurePass123')

      expect(passwordInput.type).toBe('password')

      const toggleButton = screen.getByRole('button', { name: /show password/i })
      await user.click(toggleButton)

      expect(passwordInput.type).toBe('text')

      await user.click(screen.getByRole('button', { name: /hide password/i }))
      expect(passwordInput.type).toBe('password')
    })
  })

  describe('form submission', () => {
    it('calls register API with form data', async () => {
      vi.mocked(authService.authService.register).mockResolvedValue({
        user: { id: '123', email: 'test@example.com', created_at: '2024-01-01' },
        token: 'jwt-token',
      })

      renderAccountCreationPage()
      const user = userEvent.setup()

      await user.type(getEmailInput(), 'test@example.com')
      await user.type(getPasswordInput(), 'SecurePass123')
      await user.type(getNameInput(), 'Test User')
      await user.click(getTermsCheckbox())
      await user.click(getSubmitButton())

      await waitFor(() => {
        expect(authService.authService.register).toHaveBeenCalledWith(
          expect.objectContaining({
            email: 'test@example.com',
            password: 'SecurePass123',
            name: 'Test User',
          })
        )
      })
    })

    it('redirects to /diagnostic on successful registration', async () => {
      vi.mocked(authService.authService.register).mockResolvedValue({
        user: { id: '123', email: 'test@example.com', created_at: '2024-01-01' },
        token: 'jwt-token',
      })

      renderAccountCreationPage()
      const user = userEvent.setup()

      await user.type(getEmailInput(), 'test@example.com')
      await user.type(getPasswordInput(), 'SecurePass123')
      await user.click(getTermsCheckbox())
      await user.click(getSubmitButton())

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/diagnostic')
      })
    })

    it('clears onboarding data after successful registration', async () => {
      vi.mocked(authService.authService.register).mockResolvedValue({
        user: { id: '123', email: 'test@example.com', created_at: '2024-01-01' },
        token: 'jwt-token',
      })

      renderAccountCreationPage()
      const user = userEvent.setup()

      await user.type(getEmailInput(), 'test@example.com')
      await user.type(getPasswordInput(), 'SecurePass123')
      await user.click(getTermsCheckbox())
      await user.click(getSubmitButton())

      await waitFor(() => {
        expect(mockClearAnswers).toHaveBeenCalled()
      })
    })

    it('stores JWT token in auth store on success', async () => {
      vi.mocked(authService.authService.register).mockResolvedValue({
        user: { id: '123', email: 'test@example.com', created_at: '2024-01-01' },
        token: 'jwt-token-123',
      })

      renderAccountCreationPage()
      const user = userEvent.setup()

      await user.type(getEmailInput(), 'test@example.com')
      await user.type(getPasswordInput(), 'SecurePass123')
      await user.click(getTermsCheckbox())
      await user.click(getSubmitButton())

      await waitFor(() => {
        const state = useAuthStore.getState()
        expect(state.isAuthenticated).toBe(true)
        expect(state.token).toBe('jwt-token-123')
      })
    })
  })

  describe('error handling', () => {
    it('shows inline error for duplicate email (409)', async () => {
      const error = new Error('Email exists') as Error & { response?: { status: number } }
      error.response = { status: 409 }
      vi.mocked(authService.authService.register).mockRejectedValue(error)
      vi.spyOn(axios, 'isAxiosError').mockReturnValue(true)

      renderAccountCreationPage()
      const user = userEvent.setup()

      await user.type(getEmailInput(), 'existing@example.com')
      await user.type(getPasswordInput(), 'SecurePass123')
      await user.click(getTermsCheckbox())
      await user.click(getSubmitButton())

      await waitFor(() => {
        expect(screen.getByText(/this email is already registered/i)).toBeInTheDocument()
      })
    })

    it('shows inline errors for validation error (422)', async () => {
      const error = new Error('Validation error') as Error & {
        response?: { status: number; data?: { error?: { details?: Record<string, string> } } }
      }
      error.response = {
        status: 422,
        data: {
          error: {
            details: {
              email: 'Invalid email domain',
              password: 'Password is too common',
            },
          },
        },
      }
      vi.mocked(authService.authService.register).mockRejectedValue(error)
      vi.spyOn(axios, 'isAxiosError').mockReturnValue(true)

      renderAccountCreationPage()
      const user = userEvent.setup()

      await user.type(getEmailInput(), 'test@invalid-domain.xyz')
      await user.type(getPasswordInput(), 'Password123')
      await user.click(getTermsCheckbox())
      await user.click(getSubmitButton())

      await waitFor(() => {
        expect(screen.getByText(/invalid email domain/i)).toBeInTheDocument()
      })
    })

    it('shows toast for server error (500)', async () => {
      const error = new Error('Server error') as Error & { response?: { status: number } }
      error.response = { status: 500 }
      vi.mocked(authService.authService.register).mockRejectedValue(error)
      vi.spyOn(axios, 'isAxiosError').mockReturnValue(true)

      renderAccountCreationPage()
      const user = userEvent.setup()

      await user.type(getEmailInput(), 'test@example.com')
      await user.type(getPasswordInput(), 'SecurePass123')
      await user.click(getTermsCheckbox())
      await user.click(getSubmitButton())

      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith('Unable to create account. Please try again.')
      })
    })

    it('shows toast for unexpected error', async () => {
      const error = new Error('Network error')
      vi.mocked(authService.authService.register).mockRejectedValue(error)
      vi.spyOn(axios, 'isAxiosError').mockReturnValue(false)

      renderAccountCreationPage()
      const user = userEvent.setup()

      await user.type(getEmailInput(), 'test@example.com')
      await user.type(getPasswordInput(), 'SecurePass123')
      await user.click(getTermsCheckbox())
      await user.click(getSubmitButton())

      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith('An unexpected error occurred. Please try again.')
      })
    })
  })

  describe('accessibility', () => {
    it('has proper ARIA labels on form fields', () => {
      renderAccountCreationPage()

      const emailInput = getEmailInput()
      expect(emailInput).toHaveAttribute('aria-required', 'true')

      const passwordInput = getPasswordInput()
      expect(passwordInput).toHaveAttribute('aria-required', 'true')
    })

    it('marks invalid fields with aria-invalid', async () => {
      renderAccountCreationPage()
      const user = userEvent.setup()

      const emailInput = getEmailInput()
      await user.type(emailInput, 'invalid')
      await user.tab()

      await waitFor(() => {
        expect(emailInput).toHaveAttribute('aria-invalid', 'true')
      })
    })

    it('has error messages with role="alert"', async () => {
      renderAccountCreationPage()
      const user = userEvent.setup()

      const emailInput = getEmailInput()
      await user.click(emailInput)
      await user.tab()

      await waitFor(() => {
        const errorMessages = screen.getAllByRole('alert')
        expect(errorMessages.length).toBeGreaterThan(0)
      })
    })
  })
})

// Separate test suite for missing onboarding data redirect
describe('AccountCreationPage - Missing Onboarding Data', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('redirects to /onboarding when course is missing', async () => {
    // Override the mock for this specific test
    const useOnboardingStorageModule = await import('../../hooks/useOnboardingStorage')
    vi.spyOn(useOnboardingStorageModule, 'useOnboardingStorage').mockReturnValue({
      answers: {
        course: null,
        motivation: 'certification',
        familiarity: 'basics',
        initialBeliefPrior: 0.3,
      },
      setAnswer: vi.fn(),
      clearAnswers: vi.fn(),
    })

    await act(async () => {
      render(
        <BrowserRouter>
          <AccountCreationPage />
        </BrowserRouter>
      )
    })

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/onboarding')
    })
  })

  it('redirects to /onboarding when motivation is missing', async () => {
    const useOnboardingStorageModule = await import('../../hooks/useOnboardingStorage')
    vi.spyOn(useOnboardingStorageModule, 'useOnboardingStorage').mockReturnValue({
      answers: {
        course: 'cbap',
        motivation: null,
        familiarity: 'basics',
        initialBeliefPrior: 0.3,
      },
      setAnswer: vi.fn(),
      clearAnswers: vi.fn(),
    })

    await act(async () => {
      render(
        <BrowserRouter>
          <AccountCreationPage />
        </BrowserRouter>
      )
    })

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/onboarding')
    })
  })

  it('redirects to /onboarding when familiarity is missing', async () => {
    const useOnboardingStorageModule = await import('../../hooks/useOnboardingStorage')
    vi.spyOn(useOnboardingStorageModule, 'useOnboardingStorage').mockReturnValue({
      answers: {
        course: 'cbap',
        motivation: 'certification',
        familiarity: null,
        initialBeliefPrior: 0.3,
      },
      setAnswer: vi.fn(),
      clearAnswers: vi.fn(),
    })

    await act(async () => {
      render(
        <BrowserRouter>
          <AccountCreationPage />
        </BrowserRouter>
      )
    })

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/onboarding')
    })
  })
})
