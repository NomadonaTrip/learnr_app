import toast from 'react-hot-toast'
import type { SessionUnlockItem } from '../services/prerequisiteService'

/** Build the aggregate unlock message (pure; exported for testing). */
export function buildUnlockMessage(unlocks: SessionUnlockItem[]): string {
  const names = unlocks.map((u) => u.concept_name)
  if (names.length === 1) return `🎉 You unlocked ${names[0]}!`
  if (names.length === 2) return `🎉 You unlocked ${names[0]} and ${names[1]}!`
  const shown = names.slice(0, 2).join(', ')
  return `🎉 You unlocked ${names.length} new concepts: ${shown} +${names.length - 2} more`
}

/**
 * Fire a single aggregate "concepts unlocked" toast. Clicking it navigates to
 * the curriculum page. No-op when there are no unlocks. Story 4.11 AC 7.
 */
export function showUnlockToast(
  unlocks: SessionUnlockItem[],
  navigate: (to: string) => void,
): void {
  if (unlocks.length === 0) return
  const message = buildUnlockMessage(unlocks)

  toast(
    (t) => (
      <button
        type="button"
        onClick={() => {
          toast.dismiss(t.id)
          navigate('/curriculum')
        }}
        className="flex items-center gap-2 text-left text-sm font-medium text-charcoal"
        aria-label={`${message} View curriculum.`}
      >
        {message}
      </button>
    ),
    { duration: 6000, ariaProps: { role: 'status', 'aria-live': 'polite' } },
  )
}
