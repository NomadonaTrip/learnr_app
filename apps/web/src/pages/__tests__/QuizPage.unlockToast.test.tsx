import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook } from '@testing-library/react'
import { useUnlockToastOnSession } from '../QuizPage'
import * as unlockToast from '../../utils/unlockToast'
import type { SessionUnlockItem } from '../../services/prerequisiteService'

vi.mock('../../utils/unlockToast', () => ({ showUnlockToast: vi.fn() }))
vi.mock('react-router-dom', () => ({ useNavigate: () => vi.fn() }))

const unlocks: SessionUnlockItem[] = [{ concept_id: 'a', concept_name: 'Approach' }]

describe('useUnlockToastOnSession', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('fires once when unlocks are present', () => {
    const { rerender } = renderHook(
      ({ id, u }) => useUnlockToastOnSession(id, u),
      { initialProps: { id: 's1', u: unlocks } },
    )
    expect(unlockToast.showUnlockToast).toHaveBeenCalledTimes(1)
    rerender({ id: 's1', u: unlocks }) // remount/re-render of same session
    expect(unlockToast.showUnlockToast).toHaveBeenCalledTimes(1)
  })

  it('does not fire when there are no unlocks', () => {
    renderHook(() => useUnlockToastOnSession('s1', []))
    expect(unlockToast.showUnlockToast).not.toHaveBeenCalled()
  })

  it('fires again for a different session id', () => {
    const { rerender } = renderHook(
      ({ id, u }) => useUnlockToastOnSession(id, u),
      { initialProps: { id: 's1', u: unlocks } },
    )
    rerender({ id: 's2', u: unlocks })
    expect(unlockToast.showUnlockToast).toHaveBeenCalledTimes(2)
  })
})
