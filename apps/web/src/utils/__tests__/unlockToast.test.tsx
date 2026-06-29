import { describe, it, expect, vi, beforeEach } from 'vitest'
import toast from 'react-hot-toast'
import { showUnlockToast, buildUnlockMessage } from '../unlockToast'
import type { SessionUnlockItem } from '../../services/prerequisiteService'

vi.mock('react-hot-toast', () => ({
  default: Object.assign(vi.fn(), { dismiss: vi.fn() }),
}))

const item = (name: string): SessionUnlockItem => ({ concept_id: name, concept_name: name })

describe('buildUnlockMessage', () => {
  it('singular', () => {
    expect(buildUnlockMessage([item('Approach')])).toBe('🎉 You unlocked Approach!')
  })
  it('two named', () => {
    expect(buildUnlockMessage([item('A'), item('B')])).toBe('🎉 You unlocked A and B!')
  })
  it('more than two summarises', () => {
    expect(buildUnlockMessage([item('A'), item('B'), item('C')])).toBe(
      '🎉 You unlocked 3 new concepts: A, B +1 more',
    )
  })
})

describe('showUnlockToast', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('does nothing when there are no unlocks', () => {
    showUnlockToast([], vi.fn())
    expect(toast).not.toHaveBeenCalled()
  })

  it('fires a toast when there are unlocks', () => {
    showUnlockToast([item('Approach')], vi.fn())
    expect(toast).toHaveBeenCalledTimes(1)
  })
})
