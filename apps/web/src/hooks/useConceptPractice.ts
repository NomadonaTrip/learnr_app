import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAttemptLockedConcept } from './useConceptLockStatus'
import { buildFocusQuizUrl } from '../utils/curriculum'

interface UseConceptPracticeArgs {
  conceptId: string
  conceptName: string
  isUnlocked: boolean
}

/**
 * Encapsulates the "Practice this concept" flow shared by the curriculum list
 * and the prerequisite graph: launch directly when unlocked, otherwise open a
 * soft-gate confirm that logs the override before launching. Story 4.11.
 */
export function useConceptPractice({
  conceptId,
  conceptName,
  isUnlocked,
}: UseConceptPracticeArgs) {
  const navigate = useNavigate()
  const [showDialog, setShowDialog] = useState(false)
  const attemptLocked = useAttemptLockedConcept()

  const launch = () => navigate(buildFocusQuizUrl(conceptId, conceptName))

  const handlePractice = () => {
    if (isUnlocked) launch()
    else setShowDialog(true)
  }

  const confirm = async () => {
    try {
      await attemptLocked.mutateAsync(conceptId)
      setShowDialog(false)
      launch()
    } catch {
      // Keep the dialog open on failure; mutation error surfaced via isError.
    }
  }

  const cancel = () => setShowDialog(false)

  return {
    showDialog,
    isSubmitting: attemptLocked.isPending,
    isError: attemptLocked.isError,
    handlePractice,
    confirm,
    cancel,
  }
}
