import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import { useRecentUnlocks } from '../useConceptLockStatus'
import { prerequisiteService } from '../../services/prerequisiteService'

vi.mock('../../services/prerequisiteService', () => ({
  prerequisiteService: { getRecentUnlocks: vi.fn() },
}))

function wrapper({ children }: { children: ReactNode }) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>
}

describe('useRecentUnlocks', () => {
  beforeEach(() => vi.clearAllMocks())

  it('fetches recent unlocks with the given limit', async () => {
    vi.mocked(prerequisiteService.getRecentUnlocks).mockResolvedValue({
      unlocks: [
        { id: '1', user_id: 'u', concept_id: 'c', concept_name: 'Approach',
          prerequisite_concept_id: null, prerequisite_concept_name: null,
          unlocked_at: '2026-06-28T00:00:00Z' },
      ],
      total_unlocked: 1,
    })

    const { result } = renderHook(() => useRecentUnlocks(3), { wrapper })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data?.total_unlocked).toBe(1)
    expect(prerequisiteService.getRecentUnlocks).toHaveBeenCalledWith(3)
  })
})
