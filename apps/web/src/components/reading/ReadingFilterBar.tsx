/**
 * ReadingFilterBar Component
 * Story 5.7: Reading Library Page with Queue Display
 *
 * Filter bar with status tabs, sort dropdown, and KA filter.
 * Uses Headless UI for accessible dropdowns.
 */
import { Fragment } from 'react'
import { Tab, Listbox, Transition } from '@headlessui/react'

// Simple icon components to avoid heroicons dependency
function ChevronUpDownIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
      <path
        fillRule="evenodd"
        d="M10 3a.75.75 0 01.55.24l3.25 3.5a.75.75 0 11-1.1 1.02L10 4.852 7.3 7.76a.75.75 0 01-1.1-1.02l3.25-3.5A.75.75 0 0110 3zm-3.76 9.2a.75.75 0 011.06.04l2.7 2.908 2.7-2.908a.75.75 0 111.1 1.02l-3.25 3.5a.75.75 0 01-1.1 0l-3.25-3.5a.75.75 0 01.04-1.06z"
        clipRule="evenodd"
      />
    </svg>
  )
}

function CheckIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
      <path
        fillRule="evenodd"
        d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z"
        clipRule="evenodd"
      />
    </svg>
  )
}

export type FilterStatus = 'unread' | 'reading' | 'completed' | 'all'
export type SortOption = 'priority' | 'date' | 'relevance'

export interface KnowledgeArea {
  id: string
  name: string
}

export interface FilterBarProps {
  selectedStatus: FilterStatus
  selectedSort: SortOption
  selectedKaId: string | null
  knowledgeAreas: KnowledgeArea[]
  onFilterChange: (filters: {
    status?: FilterStatus
    sort?: SortOption
    kaId?: string | null
  }) => void
}

const statusTabs: { value: FilterStatus; label: string }[] = [
  { value: 'unread', label: 'Unread' },
  { value: 'reading', label: 'Reading' },
  { value: 'completed', label: 'Completed' },
]

const sortOptions: { value: SortOption; label: string }[] = [
  { value: 'priority', label: 'Priority' },
  { value: 'date', label: 'Date Added' },
  { value: 'relevance', label: 'Relevance Score' },
]

function classNames(...classes: string[]) {
  return classes.filter(Boolean).join(' ')
}

export function ReadingFilterBar({
  selectedStatus,
  selectedSort,
  selectedKaId,
  knowledgeAreas,
  onFilterChange,
}: FilterBarProps) {
  // Find selected index for Tab component
  const selectedTabIndex = statusTabs.findIndex((tab) => tab.value === selectedStatus)
  const selectedSortOption = sortOptions.find((opt) => opt.value === selectedSort) || sortOptions[0]
  const selectedKa = knowledgeAreas.find((ka) => ka.id === selectedKaId)

  const handleTabChange = (index: number) => {
    const status = statusTabs[index]?.value
    if (status) {
      onFilterChange({ status })
    }
  }

  const handleSortChange = (option: (typeof sortOptions)[number]) => {
    onFilterChange({ sort: option.value })
  }

  const handleKaChange = (ka: KnowledgeArea | null) => {
    onFilterChange({ kaId: ka?.id ?? null })
  }

  return (
    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
      {/* Status Tabs */}
      <Tab.Group selectedIndex={selectedTabIndex} onChange={handleTabChange}>
        <Tab.List className="flex space-x-1 rounded-xl bg-gray-100 p-1">
          {statusTabs.map((tab) => (
            <Tab
              key={tab.value}
              className={({ selected }) =>
                classNames(
                  'w-full rounded-lg py-2.5 px-4 text-sm font-medium leading-5',
                  'ring-white ring-opacity-60 ring-offset-2 ring-offset-blue-400 focus:outline-none focus:ring-2',
                  selected
                    ? 'bg-white text-blue-700 shadow'
                    : 'text-gray-600 hover:bg-white/[0.12] hover:text-gray-800'
                )
              }
            >
              {tab.label}
            </Tab>
          ))}
        </Tab.List>
      </Tab.Group>

      {/* Sort and KA Filter Dropdowns */}
      <div className="flex items-center gap-3">
        {/* Sort Dropdown */}
        <Listbox value={selectedSortOption} onChange={handleSortChange}>
          <div className="relative">
            <Listbox.Label className="sr-only">Sort by</Listbox.Label>
            <Listbox.Button className="relative w-40 cursor-default rounded-lg bg-white py-2 pl-3 pr-10 text-left shadow-sm border border-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500 sm:text-sm">
              <span className="block truncate">{selectedSortOption.label}</span>
              <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
                <ChevronUpDownIcon className="h-5 w-5 text-gray-400" aria-hidden="true" />
              </span>
            </Listbox.Button>
            <Transition
              as={Fragment}
              leave="transition ease-in duration-100"
              leaveFrom="opacity-100"
              leaveTo="opacity-0"
            >
              <Listbox.Options className="absolute z-10 mt-1 max-h-60 w-full overflow-auto rounded-md bg-white py-1 text-base shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none sm:text-sm">
                {sortOptions.map((option) => (
                  <Listbox.Option
                    key={option.value}
                    className={({ active }) =>
                      classNames(
                        active ? 'bg-blue-100 text-blue-900' : 'text-gray-900',
                        'relative cursor-default select-none py-2 pl-10 pr-4'
                      )
                    }
                    value={option}
                  >
                    {({ selected }) => (
                      <>
                        <span
                          className={classNames(
                            selected ? 'font-medium' : 'font-normal',
                            'block truncate'
                          )}
                        >
                          {option.label}
                        </span>
                        {selected ? (
                          <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-blue-600">
                            <CheckIcon className="h-5 w-5" aria-hidden="true" />
                          </span>
                        ) : null}
                      </>
                    )}
                  </Listbox.Option>
                ))}
              </Listbox.Options>
            </Transition>
          </div>
        </Listbox>

        {/* KA Filter Dropdown */}
        <Listbox value={selectedKa ?? null} onChange={handleKaChange}>
          <div className="relative">
            <Listbox.Label className="sr-only">Filter by Knowledge Area</Listbox.Label>
            <Listbox.Button className="relative w-48 cursor-default rounded-lg bg-white py-2 pl-3 pr-10 text-left shadow-sm border border-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500 sm:text-sm">
              <span className="block truncate">{selectedKa?.name ?? 'All KAs'}</span>
              <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
                <ChevronUpDownIcon className="h-5 w-5 text-gray-400" aria-hidden="true" />
              </span>
            </Listbox.Button>
            <Transition
              as={Fragment}
              leave="transition ease-in duration-100"
              leaveFrom="opacity-100"
              leaveTo="opacity-0"
            >
              <Listbox.Options className="absolute z-10 mt-1 max-h-60 w-full overflow-auto rounded-md bg-white py-1 text-base shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none sm:text-sm">
                {/* All KAs option */}
                <Listbox.Option
                  className={({ active }) =>
                    classNames(
                      active ? 'bg-blue-100 text-blue-900' : 'text-gray-900',
                      'relative cursor-default select-none py-2 pl-10 pr-4'
                    )
                  }
                  value={null}
                >
                  {({ selected }) => (
                    <>
                      <span
                        className={classNames(
                          selected ? 'font-medium' : 'font-normal',
                          'block truncate'
                        )}
                      >
                        All KAs
                      </span>
                      {selected ? (
                        <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-blue-600">
                          <CheckIcon className="h-5 w-5" aria-hidden="true" />
                        </span>
                      ) : null}
                    </>
                  )}
                </Listbox.Option>
                {/* KA options */}
                {knowledgeAreas.map((ka) => (
                  <Listbox.Option
                    key={ka.id}
                    className={({ active }) =>
                      classNames(
                        active ? 'bg-blue-100 text-blue-900' : 'text-gray-900',
                        'relative cursor-default select-none py-2 pl-10 pr-4'
                      )
                    }
                    value={ka}
                  >
                    {({ selected }) => (
                      <>
                        <span
                          className={classNames(
                            selected ? 'font-medium' : 'font-normal',
                            'block truncate'
                          )}
                        >
                          {ka.name}
                        </span>
                        {selected ? (
                          <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-blue-600">
                            <CheckIcon className="h-5 w-5" aria-hidden="true" />
                          </span>
                        ) : null}
                      </>
                    )}
                  </Listbox.Option>
                ))}
              </Listbox.Options>
            </Transition>
          </div>
        </Listbox>
      </div>
    </div>
  )
}
