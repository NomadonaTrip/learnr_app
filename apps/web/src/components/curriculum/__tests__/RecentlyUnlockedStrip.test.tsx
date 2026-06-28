import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { RecentlyUnlockedStrip } from '../RecentlyUnlockedStrip'
import * as hooks from '../../../hooks/useConceptLockStatus'

vi.mock('../../../hooks/useConceptLockStatus', () => ({ useRecentUnlocks: vi.fn() }))

const ev = (name: string) => ({
  id: name, user_id: 'u', concept_id: name, concept_name: name,
  prerequisite_concept_id: null, prerequisite_concept_name: null,
  unlocked_at: '2026-06-28T00:00:00Z',
})

describe('RecentlyUnlockedStrip', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('renders nothing when there are no unlocks', () => {
    vi.mocked(hooks.useRecentUnlocks).mockReturnValue({
      data: { unlocks: [], total_unlocked: 0 }, isLoading: false, isError: false,
    } as never)
    const { container } = render(<RecentlyUnlockedStrip />)
    expect(container).toBeEmptyDOMElement()
  })

  it('renders nothing on error', () => {
    vi.mocked(hooks.useRecentUnlocks).mockReturnValue({
      data: undefined, isLoading: false, isError: true,
    } as never)
    const { container } = render(<RecentlyUnlockedStrip />)
    expect(container).toBeEmptyDOMElement()
  })

  it('renders a chip per unlock', () => {
    vi.mocked(hooks.useRecentUnlocks).mockReturnValue({
      data: { unlocks: [ev('Approach'), ev('Elicitation')], total_unlocked: 2 },
      isLoading: false, isError: false,
    } as never)
    render(<RecentlyUnlockedStrip />)
    expect(screen.getByText('Approach')).toBeInTheDocument()
    expect(screen.getByText('Elicitation')).toBeInTheDocument()
    expect(screen.getByRole('list', { name: /recently unlocked/i })).toBeInTheDocument()
  })
})
