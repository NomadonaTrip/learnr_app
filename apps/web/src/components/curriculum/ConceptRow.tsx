import { useState } from 'react'
import type { ConceptUnlockStatus } from '../../services/prerequisiteService'
import { useConceptLockStatus } from '../../hooks/useConceptLockStatus'
import { useConceptPractice } from '../../hooks/useConceptPractice'
import { ConceptLockBadge } from './ConceptLockBadge'
import { ConceptLockTooltip } from './ConceptLockTooltip'
import { LockedConceptConfirmDialog } from './LockedConceptConfirmDialog'

interface ConceptRowProps {
  concept: ConceptUnlockStatus
}

/**
 * One concept row: badge, mastery progress, lazy prerequisite tooltip, and a
 * Practice action with a soft-gate confirm for locked concepts.
 */
export function ConceptRow({ concept }: ConceptRowProps) {
  const [showDetail, setShowDetail] = useState(false)
  const practice = useConceptPractice({
    conceptId: concept.concept_id,
    conceptName: concept.concept_name,
    isUnlocked: concept.is_unlocked,
  })

  // Lazy: only fetch blocking-prerequisite detail once the row is hovered/focused,
  // and only for locked concepts (no useful data to fetch for unlocked ones).
  const status = useConceptLockStatus(showDetail && !concept.is_unlocked ? concept.concept_id : null)
  const blockers = (status.data?.blocking_prerequisites ?? []).map((b) => ({
    concept_id: b.concept_id,
    name: b.name,
  }))
  const closestName = status.data?.closest_to_unlock?.name ?? null

  const tooltipId = `concept-lock-tooltip-${concept.concept_id}`
  const showTooltip = showDetail && !concept.is_unlocked

  return (
    <div
      className="border-b border-gray-100 py-3"
      onMouseEnter={() => setShowDetail(true)}
      onMouseLeave={() => setShowDetail(false)}
      onFocus={() => setShowDetail(true)}
      onBlur={() => setShowDetail(false)}
    >
      <div className="flex items-center justify-between gap-3">
        <div className="min-w-0">
          <p className="truncate text-sm font-medium text-gray-900">
            {concept.concept_name}
          </p>
          <div className="mt-1 flex items-center gap-2">
            <ConceptLockBadge isUnlocked={concept.is_unlocked} />
            {concept.has_prerequisites && (
              <span className="text-xs text-gray-500">
                {concept.mastered_prerequisite_count}/{concept.prerequisite_count} prerequisites
              </span>
            )}
          </div>
          <div className="mt-2 h-1.5 w-40 overflow-hidden rounded-full bg-gray-100">
            <div
              className="h-full rounded-full bg-primary-500"
              style={{ width: `${Math.round(concept.mastery_progress * 100)}%` }}
            />
          </div>
        </div>
        <button
          type="button"
          onClick={practice.handlePractice}
          aria-describedby={showTooltip ? tooltipId : undefined}
          className="shrink-0 px-3 py-1.5 text-sm font-medium text-primary-700 rounded-[14px] border border-primary-200 hover:bg-primary-50"
        >
          Practice
        </button>
      </div>

      {showTooltip && (
        <ConceptLockTooltip
          id={tooltipId}
          isLoading={status.isLoading}
          error={status.isError}
          blockingPrerequisites={blockers}
          closestName={closestName}
        />
      )}

      {practice.showDialog && (
        <LockedConceptConfirmDialog
          conceptName={concept.concept_name}
          blockingPrerequisites={blockers}
          isSubmitting={practice.isSubmitting}
          isError={practice.isError}
          onConfirm={practice.confirm}
          onCancel={practice.cancel}
        />
      )}
    </div>
  )
}
