interface ConceptLockTooltipProps {
  isLoading: boolean
  error: boolean
  blockingPrerequisites: { concept_id: string; name: string }[]
  closestName: string | null
  /** Optional id so a trigger can reference this tooltip via aria-describedby. */
  id?: string
}

/**
 * Presentational popover listing the unmastered prerequisites blocking a
 * concept (AC 5), annotating the one closest to unlock (AC 6).
 */
export function ConceptLockTooltip({
  isLoading,
  error,
  blockingPrerequisites,
  closestName,
  id,
}: ConceptLockTooltipProps) {
  return (
    <div
      id={id}
      role="tooltip"
      className="mt-2 rounded-lg border border-gray-200 bg-white p-3 text-sm shadow-md"
    >
      {isLoading && <p className="text-gray-500">Loading prerequisites…</p>}
      {!isLoading && error && (
        <p className="text-amber-600">Couldn't load prerequisites</p>
      )}
      {!isLoading && !error && blockingPrerequisites.length === 0 && (
        <p className="text-green-700">All prerequisites met</p>
      )}
      {!isLoading && !error && blockingPrerequisites.length > 0 && (
        <>
          <p className="mb-1 font-medium text-gray-700">Master these first:</p>
          <ul className="space-y-1">
            {blockingPrerequisites.map((p) => (
              <li key={p.concept_id} className="text-gray-600">
                {p.name}
                {closestName === p.name && (
                  <span className="ml-1 text-xs text-primary-600">(closest to unlock)</span>
                )}
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  )
}
