/**
 * UndoToast Component
 * Story 5.12: Clear Completed Reading Materials
 *
 * Toast notification with optional undo action and Framer Motion animations.
 * Auto-dismisses after duration (default 5 seconds).
 * Accessible with aria-live for screen reader announcements.
 * Responsive: centered on mobile, bottom-right on larger screens.
 */
import { useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { CheckCircleIcon } from '../shared/icons'

export interface UndoToastProps {
  message: string
  onUndo?: () => void
  duration?: number
  isVisible: boolean
  onDismiss: () => void
}

const toastVariants = {
  initial: { x: 100, opacity: 0 },
  animate: { x: 0, opacity: 1 },
  exit: { x: 100, opacity: 0 },
}

export function UndoToast({
  message,
  onUndo,
  duration = 5000,
  isVisible,
  onDismiss,
}: UndoToastProps) {
  // Auto-dismiss timer
  useEffect(() => {
    if (!isVisible) return

    const timer = setTimeout(() => {
      onDismiss()
    }, duration)

    return () => clearTimeout(timer)
  }, [isVisible, duration, onDismiss])

  const handleUndo = useCallback(() => {
    onUndo?.()
    onDismiss()
  }, [onUndo, onDismiss])

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          role="status"
          aria-live="polite"
          variants={toastVariants}
          initial="initial"
          animate="animate"
          exit="exit"
          transition={{ type: 'spring', damping: 25, stiffness: 300 }}
          className="fixed bottom-4 right-4 z-50
                     max-sm:left-4 max-sm:right-4 max-sm:mx-auto
                     sm:bottom-6 sm:right-6"
        >
          <div
            className="flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg
                       bg-green-600 text-white
                       max-sm:justify-center"
          >
            <CheckCircleIcon className="h-5 w-5 flex-shrink-0" />
            <span className="text-sm font-medium">{message}</span>
            {onUndo && (
              <button
                onClick={handleUndo}
                className="ml-2 px-3 py-1 text-sm font-medium rounded
                           bg-white/20 hover:bg-white/30
                           focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-green-600
                           transition-colors"
              >
                Undo
              </button>
            )}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
