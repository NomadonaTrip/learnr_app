import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useAttemptLockedConcept } from '../useConceptLockStatus'
import { prerequisiteService } from '../../services/prerequisiteService'

vi.mock('../../services/prerequisiteService', () => ({
  prerequisiteService: { attemptLockedConcept: vi.fn() },
}))

function wrapper({ children }: { children: React.ReactNode }) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>
}

describe('useAttemptLockedConcept', () => {
  beforeEach(() => vi.clearAllMocks())

  it('calls the override endpoint and returns the response', async () => {
    vi.mocked(prerequisiteService.attemptLockedConcept).mockResolvedValue({
      concept_id: 'c1',
      concept_name: 'Stakeholder Analysis',
      was_locked: true,
      override_allowed: true,
      blocking_prerequisites: [],
      mastery_progress: 0.5,
      message: 'Proceeding with locked concept.',
    })

    const { result } = renderHook(() => useAttemptLockedConcept(), { wrapper })
    const response = await result.current.mutateAsync('c1')

    expect(prerequisiteService.attemptLockedConcept).toHaveBeenCalledWith('c1')
    expect(response.was_locked).toBe(true)
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
  })
})
