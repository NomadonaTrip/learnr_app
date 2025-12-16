import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface User {
  id: string
  email: string
  name?: string
  created_at: string
}

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  login: (user: User, token: string) => void
  logout: () => void
  checkAuth: () => boolean
}

/**
 * Zustand store for authentication state.
 * Persists user data to localStorage for session persistence.
 * JWT token stored separately in localStorage for Axios interceptor access.
 */
export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,

      login: (user, token) => {
        // Store token in localStorage for Axios interceptor
        localStorage.setItem('auth_token', token)

        set({
          user,
          token,
          isAuthenticated: true,
        })
      },

      logout: () => {
        localStorage.removeItem('auth_token')
        set({
          user: null,
          token: null,
          isAuthenticated: false,
        })
      },

      checkAuth: () => {
        // Check store state directly for consistency
        const state = get()
        return !!state.token && !!state.user
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)
