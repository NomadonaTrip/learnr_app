import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { diagnosticService } from '../../services/diagnosticService'
import { useDiagnosticStore } from '../../stores/diagnosticStore'

interface ResetDiagnosticButtonProps {
  courseId: string
  /** Button variant */
  variant?: 'primary' | 'secondary' | 'text'
  /** Custom button text */
  buttonText?: string
}

const CONFIRMATION_TEXT = 'RESET DIAGNOSTIC'

/**
 * Button component that triggers the diagnostic reset flow.
 * Shows a confirmation dialog requiring user to type "RESET DIAGNOSTIC".
 * On success, clears local state and redirects to /diagnostic.
 * (Story 3.9)
 */
export function ResetDiagnosticButton({
  courseId,
  variant = 'secondary',
  buttonText = 'Retake Diagnostic',
}: ResetDiagnosticButtonProps) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const resetLocalDiagnostic = useDiagnosticStore((state) => state.resetDiagnostic)

  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [confirmationInput, setConfirmationInput] = useState('')
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  // Reset mutation
  const resetMutation = useMutation({
    mutationFn: () => diagnosticService.resetDiagnostic(courseId, CONFIRMATION_TEXT),
    onSuccess: () => {
      // Clear local diagnostic state
      resetLocalDiagnostic()
      // Invalidate diagnostic queries so fresh data is fetched
      queryClient.invalidateQueries({ queryKey: ['diagnostic'] })
      // Close dialog and redirect
      setIsDialogOpen(false)
      setConfirmationInput('')
      navigate('/diagnostic')
    },
    onError: (error) => {
      setErrorMessage(
        error instanceof Error ? error.message : 'Failed to reset diagnostic. Please try again.'
      )
    },
  })

  const handleOpenDialog = useCallback(() => {
    setIsDialogOpen(true)
    setErrorMessage(null)
    setConfirmationInput('')
  }, [])

  const handleCloseDialog = useCallback(() => {
    setIsDialogOpen(false)
    setConfirmationInput('')
    setErrorMessage(null)
  }, [])

  const handleConfirm = useCallback(() => {
    if (confirmationInput !== CONFIRMATION_TEXT) {
      setErrorMessage(`Please type "${CONFIRMATION_TEXT}" to confirm.`)
      return
    }
    resetMutation.mutate()
  }, [confirmationInput, resetMutation])

  const isConfirmDisabled = confirmationInput !== CONFIRMATION_TEXT || resetMutation.isPending

  // Button styles based on variant
  const buttonStyles = {
    primary:
      'px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-medium',
    secondary:
      'px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium',
    text: 'text-primary-600 hover:text-primary-700 underline font-medium',
  }

  return (
    <>
      <button type="button" onClick={handleOpenDialog} className={buttonStyles[variant]}>
        {buttonText}
      </button>

      {/* Confirmation Dialog */}
      {isDialogOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
          role="dialog"
          aria-modal="true"
          aria-labelledby="reset-dialog-title"
        >
          <div className="bg-white rounded-lg p-6 max-w-md mx-4 shadow-xl">
            <h2 id="reset-dialog-title" className="text-lg font-semibold text-gray-900 mb-2">
              Reset Diagnostic?
            </h2>
            <p className="text-gray-600 mb-4">
              This will clear your diagnostic session and reset all your knowledge estimates to
              their initial state. You will need to retake the diagnostic from the beginning.
            </p>
            <p className="text-gray-600 mb-4">
              Type <span className="font-mono font-semibold text-red-600">{CONFIRMATION_TEXT}</span>{' '}
              to confirm:
            </p>

            <input
              type="text"
              value={confirmationInput}
              onChange={(e) => {
                setConfirmationInput(e.target.value)
                setErrorMessage(null)
              }}
              placeholder={CONFIRMATION_TEXT}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent mb-4 font-mono"
              aria-label="Confirmation text"
              disabled={resetMutation.isPending}
            />

            {/* Error message */}
            {errorMessage && (
              <p className="text-red-600 text-sm mb-4" role="alert">
                {errorMessage}
              </p>
            )}

            {/* Success/loading feedback */}
            {resetMutation.isPending && (
              <p className="text-gray-500 text-sm mb-4">Resetting diagnostic...</p>
            )}

            <div className="flex gap-3 justify-end">
              <button
                type="button"
                onClick={handleCloseDialog}
                disabled={resetMutation.isPending}
                className="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg font-medium hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleConfirm}
                disabled={isConfirmDisabled}
                className="px-4 py-2 bg-red-600 text-white rounded-lg font-medium hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {resetMutation.isPending ? 'Resetting...' : 'Reset Diagnostic'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
