import api from './api'
import type { OnboardingAnswers } from '../hooks/useOnboardingStorage'

export interface OnboardingData {
  course: string
  motivation: string
  familiarity: string
  initialBeliefPrior: number
}

export interface RegisterPayload {
  email: string
  password: string
  name?: string
  onboarding_data?: OnboardingData
}

export interface RegisterResponse {
  user: {
    id: string
    email: string
    name?: string
    created_at: string
  }
  token: string
}

export interface LoginPayload {
  email: string
  password: string
}

export interface LoginResponse {
  user: {
    id: string
    email: string
    name?: string
    created_at: string
  }
  token: string
}

/**
 * Authentication service for registration and login.
 */
export const authService = {
  /**
   * Register a new user account.
   * @param payload - User registration data including optional onboarding data
   * @returns User data and JWT token
   * @throws AxiosError with status 409 for duplicate email, 422 for validation errors
   */
  async register(payload: RegisterPayload): Promise<RegisterResponse> {
    const response = await api.post<RegisterResponse>('/auth/register', payload)
    return response.data
  },

  /**
   * Login with email and password.
   * @param payload - Login credentials
   * @returns User data and JWT token
   */
  async login(payload: LoginPayload): Promise<LoginResponse> {
    const response = await api.post<LoginResponse>('/auth/login', payload)
    return response.data
  },

  /**
   * Get current user profile.
   * Requires valid JWT token in Authorization header.
   */
  async getCurrentUser(): Promise<RegisterResponse['user']> {
    const response = await api.get<{ user: RegisterResponse['user'] }>('/auth/me')
    return response.data.user
  },
}

/**
 * Convert OnboardingAnswers hook format to API format.
 */
export function formatOnboardingData(answers: OnboardingAnswers): OnboardingData | undefined {
  if (!answers.course || !answers.motivation || !answers.familiarity) {
    return undefined
  }

  return {
    course: answers.course,
    motivation: answers.motivation,
    familiarity: answers.familiarity,
    initialBeliefPrior: answers.initialBeliefPrior ?? 0.3,
  }
}
