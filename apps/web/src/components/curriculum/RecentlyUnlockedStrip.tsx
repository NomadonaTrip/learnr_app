import { useRecentUnlocks } from '../../hooks/useConceptLockStatus'

/**
 * Horizontal strip of the user's recently unlocked concepts (Story 4.11 AC 7).
 * Renders nothing until there is data, so it is invisible on a fresh account.
 */
export function RecentlyUnlockedStrip() {
  const { data, isLoading, isError } = useRecentUnlocks(5)

  if (isLoading || isError) return null
  const unlocks = data?.unlocks ?? []
  if (unlocks.length === 0) return null

  return (
    <section className="mt-4" aria-label="Recently unlocked concepts">
      <h2 className="text-xs font-semibold uppercase tracking-wide text-gray-500">
        Recently unlocked
      </h2>
      <ul
        aria-label="Recently unlocked concepts"
        className="mt-2 flex gap-2 overflow-x-auto pb-1"
      >
        {unlocks.map((u) => (
          <li
            key={u.id}
            tabIndex={0}
            className="flex shrink-0 items-center gap-1 rounded-full border border-green-200 bg-green-50 px-3 py-1 text-sm font-medium text-green-800 focus:outline-none focus:ring-2 focus:ring-green-500"
          >
            <span aria-hidden="true">🔓</span>
            {u.concept_name}
          </li>
        ))}
      </ul>
    </section>
  )
}

export default RecentlyUnlockedStrip
