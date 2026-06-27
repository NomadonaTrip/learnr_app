interface LockedConceptConfirmDialogProps {
  conceptName: string
  blockingPrerequisites: { concept_id: string; name: string }[]
  isSubmitting: boolean
  onConfirm: () => void
  onCancel: () => void
}

/**
 * Soft-gate confirmation before practicing a locked concept (AC 8).
 * Confirming triggers the override-attempt call, then the focused quiz launch.
 */
export function LockedConceptConfirmDialog({
  conceptName,
  blockingPrerequisites,
  isSubmitting,
  onConfirm,
  onCancel,
}: LockedConceptConfirmDialogProps) {
  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={`Practice ${conceptName} before prerequisites are mastered?`}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      onKeyDown={(e) => e.key === 'Escape' && onCancel()}
    >
      <div className="w-full max-w-md rounded-[14px] bg-white p-6 shadow-xl">
        <h2 className="text-lg font-semibold text-charcoal">
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
