import { describe, it, expect, beforeEach } from 'vitest'
import { useAuthStore } from '../../stores/authStore'

describe('useAuthStore', () => {
  beforeEach(() => {
    // Reset the store state (merge mode, keeps methods)
    useAuthStore.setState({
      user: null,
      token: null,
      isAuthenticated: false,
    })
  })

  describe('initial state', () => {
    it('has null user and token after reset', () => {
      const state = useAuthStore.getState()
      expect(state.user).toBeNull()
      expect(state.token).toBeNull()
      expect(state.isAuthenticated).toBe(false)
    })

    it('has login, logout, and checkAuth methods', () => {
      const state = useAuthStore.getState()
      expect(typeof state.login).toBe('function')
      expect(typeof state.logout).toBe('function')
      expect(typeof state.checkAuth).toBe('function')
    })
  })

  describe('login', () => {
    const mockUser = {
      id: 'user-123',
      email: 'test@example.com',
      name: 'Test User',
      created_at: '2024-01-01T00:00:00Z',
    }
    const mockToken = 'jwt-token-123'

    it('sets user and token on login', () => {
      useAuthStore.getState().login(mockUser, mockToken)

      const state = useAuthStore.getState()
      expect(state.user).toEqual(mockUser)
      expect(state.token).toBe(mockToken)
      expect(state.isAuthenticated).toBe(true)
    })

    it('sets isAuthenticated to true', () => {
      useAuthStore.getState().login(mockUser, mockToken)

      expect(useAuthStore.getState().isAuthenticated).toBe(true)
    })
  })

  describe('logout', () => {
    it('clears user and token on logout', () => {
      // First login
      useAuthStore.getState().login(
        { id: '123', email: 'test@example.com', created_at: '2024-01-01' },
        'token'
      )

      // Then logout
      useAuthStore.getState().logout()

      const state = useAuthStore.getState()
      expect(state.user).toBeNull()
      expect(state.token).toBeNull()
      expect(state.isAuthenticated).toBe(false)
    })
  })

  describe('checkAuth', () => {
    it('returns false when not logged in', () => {
      const result = useAuthStore.getState().checkAuth()
      expect(result).toBe(false)
    })

    it('returns true when logged in', () => {
      useAuthStore.getState().login(
        { id: '123', email: 'test@example.com', created_at: '2024-01-01' },
        'token'
      )

      const result = useAuthStore.getState().checkAuth()
      expect(result).toBe(true)
    })

    it('returns false after logout', () => {
      useAuthStore.getState().login(
        { id: '123', email: 'test@example.com', created_at: '2024-01-01' },
        'token'
      )
      useAuthStore.getState().logout()

      const result = useAuthStore.getState().checkAuth()
      expect(result).toBe(false)
    })
  })

  describe('state transitions', () => {
    it('login followed by logout resets state', () => {
      const mockUser = {
        id: 'user-123',
        email: 'test@example.com',
        created_at: '2024-01-01T00:00:00Z',
      }

      useAuthStore.getState().login(mockUser, 'token')
      expect(useAuthStore.getState().isAuthenticated).toBe(true)

      useAuthStore.getState().logout()
      expect(useAuthStore.getState().isAuthenticated).toBe(false)
      expect(useAuthStore.getState().user).toBeNull()
      expect(useAuthStore.getState().token).toBeNull()
    })

    it('multiple logins overwrite previous state', () => {
      const user1 = { id: '1', email: 'user1@example.com', created_at: '2024-01-01' }
      const user2 = { id: '2', email: 'user2@example.com', created_at: '2024-01-02' }

      useAuthStore.getState().login(user1, 'token1')
      useAuthStore.getState().login(user2, 'token2')

      const state = useAuthStore.getState()
      expect(state.user).toEqual(user2)
      expect(state.token).toBe('token2')
    })
  })
})
