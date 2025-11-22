/**
 * Shared TypeScript type definitions
 * Used across frontend and backend to ensure type consistency
 */

// User types
export interface User {
  id: string
  email: string
  name: string
  createdAt: string
  updatedAt: string
}

export interface UserProfile extends User {
  competencyLevel: number
  sessionsCompleted: number
  targetExam: string
}

// API Response types
export interface ApiResponse<T> {
  data: T
  message?: string
}

export interface ApiError {
  message: string
  code: string
  details?: Record<string, unknown>
}

// TODO: Add more shared types as features are implemented
// - Session types
// - Question types
// - Response types
// - Competency types
