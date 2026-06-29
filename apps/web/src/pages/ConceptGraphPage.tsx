import { useCallback, useEffect, useMemo, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Navigation } from '../components/layout/Navigation'
import { courseService } from '../services/courseService'
import { useConceptNeighborhood } from '../hooks/useConceptLockStatus'
import PrerequisiteGraph from '../components/curriculum/PrerequisiteGraph'

const ONBOARDING_STORAGE_KEY = 'learnr_onboarding'
const DEFAULT_COURSE_SLUG = 'cbap'

function getSelectedCourseSlug(): string {
  try {
    const stored = sessionStorage.getItem(ONBOARDING_STORAGE_KEY)
    if (stored) return JSON.parse(stored).course || DEFAULT_COURSE_SLUG
  } catch {
    // ignore
  }
  return DEFAULT_COURSE_SLUG
}

/** Full-page interactive prerequisite graph centered on one concept (Story 4.11 Slice D). */
export default function ConceptGraphPage() {
  const { conceptId } = useParams<{ conceptId: string }>()
  const navigate = useNavigate()
  const [expanded, setExpanded] = useState<Set<string>>(new Set())

  // Reset cluster expansion whenever the focused concept changes.
  useEffect(() => setExpanded(new Set()), [conceptId])

  const courseSlug = useMemo(() => getSelectedCourseSlug(), [])
  const courseQuery = useQuery({
    queryKey: ['course', courseSlug],
    queryFn: () => courseService.fetchCourseBySlug(courseSlug),
    staleTime: Infinity,
    retry: 2,
  })

  const neighborhoodQuery = useConceptNeighborhood(conceptId)

  const kaColorMap = useMemo(() => {
    const map: Record<string, string> = {}
    for (const ka of courseQuery.data?.knowledge_areas ?? []) {
      map[ka.id] = ka.color_hex
    }
    return map
  }, [courseQuery.data])

  const center = neighborhoodQuery.data?.nodes.find((n) => n.direction === 'center')
  // "Empty" when the neighborhood has only the lone center node (no prereqs, no dependents).
  // The backend always returns at least the center, so nodes.length === 1 means truly isolated.
  const isEmpty =
    !!neighborhoodQuery.data && neighborhoodQuery.data.nodes.length <= 1

  // useCallback so PrerequisiteGraph's internal useMemo doesn't thrash on every render.
  const onRecenter = useCallback(
    (id: string) => navigate(`/curriculum/graph/${id}`),
    [navigate]
  )

  const onToggleCluster = useCallback(
    (clusterId: string) =>
      setExpanded((prev) => {
        const next = new Set(prev)
        next.add(clusterId)
        return next
      }),
    []
  )

  return (
    <div className="min-h-screen bg-cream">
      <Navigation />
      <main className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
        <Link to="/curriculum" className="text-sm font-medium text-primary-700 underline">
          ← Back to curriculum
        </Link>
        <h1 className="mt-2 text-2xl font-bold text-charcoal">
          {center ? center.name : 'Prerequisite map'}
        </h1>
        <p className="mt-1 text-sm text-gray-600">
          Prerequisites to master first (below) and what this unlocks (above).
          Click a concept to explore it; use Practice to start a focused session.
        </p>

        <div className="mt-6">
          {neighborhoodQuery.isLoading && (
            <p className="text-gray-500">Loading the prerequisite map…</p>
          )}

          {neighborhoodQuery.isError && (
            <div className="rounded-[14px] border border-red-200 bg-red-50 p-4">
              <p className="font-medium text-red-800">Couldn't load the prerequisite map</p>
              <button
                type="button"
                onClick={() => void neighborhoodQuery.refetch()}
                className="mt-2 text-sm font-medium text-red-700 underline"
              >
                Try again
              </button>
            </div>
          )}

          {neighborhoodQuery.data && isEmpty && (
            <div className="rounded-[14px] border border-gray-200 bg-white p-6 text-center">
              <p className="font-medium text-charcoal">No prerequisites</p>
              <p className="mt-1 text-sm text-gray-600">
                This concept has no prerequisites or dependents — you can start it now.
              </p>
            </div>
          )}

          {neighborhoodQuery.data && !isEmpty && (
            <>
              <PrerequisiteGraph
                neighborhood={neighborhoodQuery.data}
                expanded={expanded}
                kaColorMap={kaColorMap}
                onRecenter={onRecenter}
                onToggleCluster={onToggleCluster}
              />
              {/* Accessible text equivalent of the canvas for keyboard/screen-reader users. */}
              <ol className="sr-only">
                {neighborhoodQuery.data.nodes.map((n) => (
                  <li key={n.concept_id}>
                    <Link to={`/curriculum/graph/${n.concept_id}`}>
                      {n.name} — {n.direction}, {n.is_unlocked ? 'unlocked' : 'locked'}
                    </Link>
                  </li>
                ))}
              </ol>
            </>
          )}
        </div>
      </main>
    </div>
  )
}
