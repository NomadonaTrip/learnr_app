/**
 * Toast Component
 * Story 5.8: Reading Item Detail View and Engagement Tracking
 *
 * Displays temporary notification messages with auto-dismiss.
 * Accessible with aria-live for screen reader announcements.
 */
import { useEffect } from 'react'
import {
  CheckCircleIcon,
  InformationCircleIcon,
  XCircleIcon,
  XMarkIcon,
} from '../shared/icons'

export type ToastVariant = 'success' | 'error' | 'info'

interface ToastProps {
  message: string
  variant: ToastVariant
  duration?: number
  onClose: () => void
}

const variantStyles: Record<ToastVariant, string> = {
  success: 'bg-green-500',
  error: 'bg-red-500',
  info: 'bg-blue-500',
}

const variantIcons: Record<ToastVariant, React.ComponentType<{ className?: string }>> = {
  success: CheckCircleIcon,
  error: XCircleIcon,
  info: InformationCircleIcon,
}

export function Toast({
  message,
  variant,
  duration = 3000,
  onClose,
}: ToastProps) {
  useEffect(() => {
    const timer = setTimeout(onClose, duration)
    return () => clearTimeout(timer)
  }, [duration, onClose])

  const Icon = variantIcons[variant]

  return (
    <div
      role="status"
      aria-live="polite"
      className={`fixed bottom-4 right-4 px-4 py-3 rounded-lg text-white shadow-lg
                  flex items-center gap-3 ${variantStyles[variant]}
                  animate-[slideUp_0.3s_ease-out]`}
    >
      <Icon className="w-5 h-5 flex-shrink-0" />
      <span>{message}</span>
      <button
        onClick={onClose}
        className="ml-2 p-1 rounded hover:bg-white/20 focus:outline-none focus:ring-2 focus:ring-white"
        aria-label="Dismiss notification"
      >
        <XMarkIcon className="w-4 h-4" />
      </button>
    </div>
  )
}
