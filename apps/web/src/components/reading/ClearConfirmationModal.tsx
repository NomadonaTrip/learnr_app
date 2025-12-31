/**
 * ClearConfirmationModal Component
 * Story 5.12: Clear Completed Reading Materials
 *
 * Confirmation dialog for batch clearing completed reading materials.
 * Uses Headless UI Dialog for accessibility (focus trap, Escape to close).
 * Returns focus to trigger button on close.
 */
import { Fragment, useRef } from 'react'
import { Dialog, Transition } from '@headlessui/react'
import { SpinnerIcon, TrashIcon } from '../shared/icons'

export interface ClearConfirmationModalProps {
  isOpen: boolean
  onClose: () => void
  onConfirm: () => void
  count: number
  isLoading: boolean
}

export function ClearConfirmationModal({
  isOpen,
  onClose,
  onConfirm,
  count,
  isLoading,
}: ClearConfirmationModalProps) {
  const cancelButtonRef = useRef<HTMLButtonElement>(null)

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog
        as="div"
        className="relative z-50"
        onClose={onClose}
        initialFocus={cancelButtonRef}
      >
        {/* Backdrop */}
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black/25" aria-hidden="true" />
        </Transition.Child>

        {/* Modal container */}
        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4 text-center">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className="w-full max-w-md transform overflow-hidden rounded-xl bg-white p-6 text-left align-middle shadow-xl transition-all max-sm:max-w-full max-sm:mx-4">
                {/* Icon */}
                <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-red-50">
                  <TrashIcon className="h-6 w-6 text-red-600" />
                </div>

                {/* Title */}
                <Dialog.Title
                  as="h3"
                  className="mt-4 text-lg font-semibold leading-6 text-gray-900 text-center"
                >
                  Clear Completed Reading Materials?
                </Dialog.Title>

                {/* Description */}
                <Dialog.Description className="mt-2 text-sm text-gray-500 text-center">
                  This will remove{' '}
                  <span className="font-medium text-gray-700" aria-live="polite">
                    {count} {count === 1 ? 'item' : 'items'}
                  </span>{' '}
                  from your library. Your reading progress and statistics are preserved.
                </Dialog.Description>

                {/* Actions */}
                <div className="mt-6 flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
                  <button
                    ref={cancelButtonRef}
                    type="button"
                    onClick={onClose}
                    disabled={isLoading}
                    className="inline-flex w-full justify-center rounded-lg px-4 py-2 text-sm font-medium
                               text-gray-700 bg-white border border-gray-300
                               hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2
                               disabled:opacity-50 disabled:cursor-not-allowed
                               sm:w-auto"
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    onClick={onConfirm}
                    disabled={isLoading}
                    className="inline-flex w-full justify-center items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium
                               text-red-700 bg-red-50 border border-red-200
                               hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2
                               disabled:opacity-50 disabled:cursor-not-allowed
                               sm:w-auto"
                  >
                    {isLoading && <SpinnerIcon className="h-4 w-4" />}
                    <span>Clear Items</span>
                  </button>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  )
}
