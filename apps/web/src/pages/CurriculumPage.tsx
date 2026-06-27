import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Navigation } from '../components/layout/Navigation'
import { courseService } from '../services/courseService'
import { useBulkUnlockStatus } from '../hooks/useConceptLockStatus'
import { groupConceptsByKa } from '../utils/curriculum'
import { KnowledgeAreaSection } from '../components/curriculum/KnowledgeAreaSection'

const ONBOARDING_STORAGE_KEY = 'learnr_onboarding'
const DEFAULT_COURSE_SLUG = 'cbap'

/** Resolve the onboarding-selected course slug (mirrors useDiagnosticResults). */
function getSelectedCourseSlug(): string {
  try {
    const stored = sessionStorage.getItem(ONBOARDING_STORAGE_KEY)
    if (stored) {
      const data = JSON.parse(stored)
      return data.course || DEFAULT_COURSE_SLUG
    }
  } catch {
    // Ignore parse errors
  }
  return DEFAULT_COURSE_SLUG
}

/**
 * Curriculum / Concept Map page: lock-status per knowledge area with focused
 * practice launch (Story 4.11 UI, slice B).
 */
export function CurriculumPage() {
  const courseSlug = useMemo(() => getSelectedCourseSlug(), [])
  const courseQuery = useQuery({
    queryKey: ['course', courseSlug],
    queryFn: () => courseService.fetchCourseBySlug(courseSlug),
    staleTime: Infinity,
    retry: 2,
  })

  const courseId = courseQuery.data?.id ?? null
  const statusQuery = useBulkUnlockStatus(courseId)

  const groups = useMemo(() => {
    if (!courseQuery.data || !statusQuery.data) return []
    return groupConceptsByKa(
      statusQuery.data.concepts,
      courseQuery.data.knowledge_areas,
    )
  }, [courseQuery.data, statusQuery.data])

  const isLoading = courseQuery.isLoading || statusQuery.isLoading
  const isError = courseQuery.isError || statusQuery.isError
  const isEmptyGraph = statusQuery.data?.total_concepts === 0

  return (
    <div className="min-h-screen bg-cream">
      <Navigation />
      <main className="mx-auto max-w-3xl px-4 py-8 sm:px-6 lg:px-8">
        <h1 className="text-2xl font-bold text-charcoal">Curriculum</h1>
        <p className="mt-1 text-sm text-gray-600">
          Concepts grouped by knowledge area. Locked concepts list the
          prerequisites to master first.
        </p>

        <div className="mt-6 space-y-3">
          {isLoading && <p className="text-gray-500">Loading your curriculum…</p>}

          {!isLoading && isError && (
            <div className="rounded-[14px] border border-red-200 bg-red-50 p-4">
              <p className="font-medium text-red-800">Couldn't load your curriculum</p>
              <button
                type="button"
                onClick={() => statusQuery.refetch()}
                className="mt-2 text-sm font-medium text-red-700 underline"
              >
                Try again
              </button>
            </div>
          )}

          {!isLoading && !isError && isEmptyGraph && (
            <div className="rounded-[14px] border border-gray-200 bg-white p-6 text-center">
              <p className="font-medium text-charcoal">
                Your curriculum map isn't ready yet
              </p>
              <p className="mt-1 text-sm text-gray-600">
                Prerequisite data is still being prepared. Check back soon.
              </p>
            </div>
          )}

          {!isLoading && !isError && !isEmptyGraph &&
            groups.map((group) => (
              <KnowledgeAreaSection key={group.knowledgeArea.id} group={group} />
            ))}
        </div>
      </main>
    </div>
  )
}

export default CurriculumPage
