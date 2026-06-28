import { useEffect, useRef } from 'react'

interface LockedConceptConfirmDialogProps {
  conceptName: string
  blockingPrerequisites: { concept_id: string; name: string }[]
  isSubmitting: boolean
  isError?: boolean
  onConfirm: () => void
  onCancel: () => void
}

const TITLE_ID = 'locked-concept-dialog-title'
const FOCUSABLE =
  'button:not([disabled]), [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'

/**
 * Soft-gate confirmation before practicing a locked concept (AC 8).
 * Confirming triggers the override-attempt call, then the focused quiz launch.
 */
export function LockedConceptConfirmDialog({
  conceptName,
  blockingPrerequisites,
  isSubmitting,
  isError,
  onConfirm,
  onCancel,
}: LockedConceptConfirmDialogProps) {
  const dialogRef = useRef<HTMLDivElement>(null)

  // Autofocus the dialog on open so Escape works immediately and focus enters the modal.
  useEffect(() => {
    dialogRef.current?.focus()
  }, [])

  const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.key === 'Escape') {
      onCancel()
      return
    }
    if (e.key !== 'Tab') return
    // Trap focus within the dialog.
    const focusable = dialogRef.current?.querySelectorAll<HTMLElement>(FOCUSABLE)
    if (!focusable || focusable.length === 0) return
    const first = focusable[0]
    const last = focusable[focusable.length - 1]
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault()
      last.focus()
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault()
      first.focus()
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      onClick={(e) => {
        if (e.target === e.currentTarget) onCancel()
      }}
    >
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={TITLE_ID}
        tabIndex={-1}
        onKeyDown={handleKeyDown}
        className="w-full max-w-md rounded-[14px] bg-white p-6 shadow-xl outline-none"
      >
        <h2 id={TITLE_ID} className="text-lg font-semibold text-charcoal">
          Practice "{conceptName}" anyway?
        </h2>
        <p className="mt-2 text-sm text-gray-600">
          These prerequisites aren't mastered yet. You can still practice, but
          mastering them first usually leads to better results.
        </p>
        {blockingPrerequisites.length > 0 && (
          <ul className="mt-3 space-y-1 text-sm text-gray-700">
            {blockingPrerequisites.map((p) => (
              <li key={p.concept_id}>
                <span aria-hidden="true">•</span> <span>{p.name}</span>
              </li>
            ))}
          </ul>
        )}
        {isError && (
          <p className="mt-3 text-sm text-red-600">Something went wrong. Please try again.</p>
        )}
        <div className="mt-6 flex justify-end gap-3">
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 text-sm font-medium text-gray-700 rounded-[14px] border border-gray-300 hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={isSubmitting}
            className="px-4 py-2 text-sm font-medium text-white rounded-[14px] bg-primary-600 hover:bg-primary-700 disabled:opacity-50"
          >
            {isSubmitting ? 'Starting…' : 'Practice anyway'}
          </button>
        </div>
      </div>
    </div>
  )
}
