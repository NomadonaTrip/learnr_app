import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { useConceptPractice } from '../useConceptPractice'

const navigate = vi.fn()
vi.mock('react-router-dom', async (orig) => ({
  ...(await orig<typeof import('react-router-dom')>()),
  useNavigate: () => navigate,
}))
const mutateAsync = vi.fn().mockResolvedValue({})
vi.mock('../useConceptLockStatus', () => ({
  useAttemptLockedConcept: () => ({ mutateAsync, isPending: false, isError: false }),
}))

function wrap() {
  const client = new QueryClient()
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={client}><MemoryRouter>{children}</MemoryRouter></QueryClientProvider>
  )
}

describe('useConceptPractice', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('navigates immediately when unlocked', () => {
    const { result } = renderHook(
      () => useConceptPractice({ conceptId: 'c1', conceptName: 'C', isUnlocked: true }),
      { wrapper: wrap() })
    act(() => result.current.handlePractice())
    expect(navigate).toHaveBeenCalledWith(expect.stringContaining('c1'))
    expect(result.current.showDialog).toBe(false)
  })

  it('opens the dialog when locked, then confirms + launches', async () => {
    const { result } = renderHook(
      () => useConceptPractice({ conceptId: 'c2', conceptName: 'C', isUnlocked: false }),
      { wrapper: wrap() })
    act(() => result.current.handlePractice())
    expect(result.current.showDialog).toBe(true)
    expect(navigate).not.toHaveBeenCalled()
    await act(async () => { await result.current.confirm() })
    expect(mutateAsync).toHaveBeenCalledWith('c2')
    await waitFor(() => expect(navigate).toHaveBeenCalledWith(expect.stringContaining('c2')))
  })
})
