import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import type { ConceptUnlockStatus } from '../../services/prerequisiteService'
import { useConceptLockStatus, useAttemptLockedConcept } from '../../hooks/useConceptLockStatus'
import { buildFocusQuizUrl } from '../../utils/curriculum'
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
  const navigate = useNavigate()
  const [showDetail, setShowDetail] = useState(false)
  const [showDialog, setShowDialog] = useState(false)
  const attemptLocked = useAttemptLockedConcept()

  // Lazy: only fetch blocking-prerequisite detail once the row is hovered/focused.
  const status = useConceptLockStatus(showDetail ? concept.concept_id : null)
  const blockers = (status.data?.blocking_prerequisites ?? []).map((b) => ({
    concept_id: b.concept_id,
    name: b.name,
  }))
  const closestName = status.data?.closest_to_unlock?.name ?? null

  const launch = () =>
    navigate(buildFocusQuizUrl(concept.concept_id, concept.concept_name))

  const handlePractice = () => {
    if (concept.is_unlocked) {
      launch()
    } else {
      setShowDialog(true)
    }
  }

  const handleConfirm = async () => {
    try {
      await attemptLocked.mutateAsync(concept.concept_id)
      setShowDialog(false)
      launch()
    } catch {
      // Keep the dialog open on failure; mutation error state is surfaced below.
    }
  }

  return (
    <div
      className="border-b border-gray-100 py-3"
      onMouseEnter={() => setShowDetail(true)}
      onFocus={() => setShowDetail(true)}
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
          onClick={handlePractice}
          className="shrink-0 px-3 py-1.5 text-sm font-medium text-primary-700 rounded-[14px] border border-primary-200 hover:bg-primary-50"
        >
          Practice
        </button>
      </div>

      {showDetail && !concept.is_unlocked && (
        <ConceptLockTooltip
          isLoading={status.isLoading}
          error={status.isError}
          blockingPrerequisites={blockers}
          closestName={closestName}
        />
      )}

      {showDialog && (
        <LockedConceptConfirmDialog
          conceptName={concept.concept_name}
          blockingPrerequisites={blockers}
          isSubmitting={attemptLocked.isPending}
          onConfirm={handleConfirm}
          onCancel={() => setShowDialog(false)}
        />
      )}
    </div>
  )
}
