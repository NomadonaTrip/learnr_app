/**
 * KebabMenu Component
 * Story 5.12: Clear Completed Reading Materials
 *
 * Three-dot action menu for individual completed reading cards.
 * Uses Headless UI Menu for accessibility (keyboard navigation, focus management).
 * 44x44px touch target for mobile accessibility.
 */
import { Fragment } from 'react'
import { Menu, Transition } from '@headlessui/react'
import { EllipsisVerticalIcon, TrashIcon } from '../shared/icons'

export interface KebabMenuProps {
  onRemove: () => void
}

export function KebabMenu({ onRemove }: KebabMenuProps) {
  return (
    <Menu as="div" className="relative">
      <Menu.Button
        className="flex items-center justify-center w-11 h-11 rounded-full
                   text-gray-400 hover:text-gray-600 hover:bg-gray-100
                   focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
                   transition-colors"
        aria-label="Card actions menu"
      >
        <EllipsisVerticalIcon className="h-5 w-5" />
      </Menu.Button>

      <Transition
        as={Fragment}
        enter="transition ease-out duration-100"
        enterFrom="transform opacity-0 scale-95"
        enterTo="transform opacity-100 scale-100"
        leave="transition ease-in duration-75"
        leaveFrom="transform opacity-100 scale-100"
        leaveTo="transform opacity-0 scale-95"
      >
        <Menu.Items
          className="absolute right-0 mt-1 w-48 origin-top-right rounded-lg bg-white
                     shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none
                     z-10"
        >
          <div className="py-1">
            <Menu.Item>
              {({ active }) => (
                <button
                  onClick={onRemove}
                  className={`${
                    active ? 'bg-red-50 text-red-700' : 'text-gray-700'
                  } group flex w-full items-center gap-3 px-4 py-2 text-sm transition-colors`}
                >
                  <TrashIcon
                    className={`h-4 w-4 ${active ? 'text-red-600' : 'text-gray-400'}`}
                  />
                  <span>Remove from library</span>
                </button>
              )}
            </Menu.Item>
          </div>
        </Menu.Items>
      </Transition>
    </Menu>
  )
}
