import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import ConceptGraphPage from '../ConceptGraphPage'
import { courseService } from '../../services/courseService'
import { prerequisiteService } from '../../services/prerequisiteService'

const navigate = vi.fn()
vi.mock('react-router-dom', async (orig) => ({
  ...(await orig<typeof import('react-router-dom')>()),
  useNavigate: () => navigate,
}))
vi.mock('../../components/layout/Navigation', () => ({ Navigation: () => null }))
vi.mock('../../services/courseService', () => ({ courseService: { fetchCourseBySlug: vi.fn() } }))
vi.mock('../../services/prerequisiteService', () => ({ prerequisiteService: { getNeighborhood: vi.fn() } }))
// Stub the graph: expose buttons to trigger re-center + cluster toggle.
vi.mock('../../components/curriculum/PrerequisiteGraph', () => ({
  default: ({ onRecenter, onToggleCluster }: { onRecenter: (id: string) => void; onToggleCluster: (id: string) => void }) => (
    <div>
      <button onClick={() => onRecenter('p1')}>recenter</button>
      <button onClick={() => onToggleCluster('cluster:c:prereq')}>toggle</button>
    </div>
  ),
}))

const course = { id: 'course-1', slug: 'cbap', name: 'CBAP', knowledge_areas: [{ id: 'ka-1', name: 'Planning', abbreviation: 'P', color_hex: '#3b82f6' }] }
const neighborhood = {
  center_id: 'c', depth: 2, truncated: false,
  nodes: [
    { concept_id: 'c', name: 'Center Concept', knowledge_area_id: 'ka-1', difficulty: 0.5, is_unlocked: true, mastery_progress: 1, depth: 0, direction: 'center' },
    { concept_id: 'p1', name: 'Prereq One', knowledge_area_id: 'ka-1', difficulty: 0.4, is_unlocked: false, mastery_progress: 0.3, depth: -1, direction: 'prereq' },
  ],
  edges: [{ source: 'p1', target: 'c', relationship_type: 'required', strength: 0.8 }],
}

const loneCenter = {
  center_id: 'c', depth: 2, truncated: false,
  nodes: [{ concept_id: 'c', name: 'Center Concept', knowledge_area_id: 'ka-1', difficulty: 0.5, is_unlocked: true, mastery_progress: 1, depth: 0, direction: 'center' }],
  edges: [],
}

function renderAt(conceptId: string) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[`/curriculum/graph/${conceptId}`]}>
        <Routes><Route path="/curriculum/graph/:conceptId" element={<ConceptGraphPage />} /></Routes>
      </MemoryRouter>
    </QueryClientProvider>
  )
}

describe('ConceptGraphPage', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('renders the center concept name on success', async () => {
    vi.mocked(courseService.fetchCourseBySlug).mockResolvedValue(course as never)
    vi.mocked(prerequisiteService.getNeighborhood).mockResolvedValue(neighborhood as never)
    renderAt('c')
    await waitFor(() => expect(screen.getByText('Center Concept')).toBeInTheDocument())
  })

  it('re-centers by navigating to the clicked concept', async () => {
    vi.mocked(courseService.fetchCourseBySlug).mockResolvedValue(course as never)
    vi.mocked(prerequisiteService.getNeighborhood).mockResolvedValue(neighborhood as never)
    renderAt('c')
    await waitFor(() => screen.getByText('recenter'))
    fireEvent.click(screen.getByText('recenter'))
    expect(navigate).toHaveBeenCalledWith('/curriculum/graph/p1')
  })

  it('shows an error state with retry', async () => {
    vi.mocked(courseService.fetchCourseBySlug).mockResolvedValue(course as never)
    vi.mocked(prerequisiteService.getNeighborhood).mockRejectedValue(new Error('boom'))
    renderAt('c')
    await waitFor(() => expect(screen.getByText(/couldn't load/i)).toBeInTheDocument())
  })

  it('shows the empty state for a lone-center concept (no prereqs, no dependents)', async () => {
    vi.mocked(courseService.fetchCourseBySlug).mockResolvedValue(course as never)
    vi.mocked(prerequisiteService.getNeighborhood).mockResolvedValue(loneCenter as never)
    renderAt('c')
    await waitFor(() => expect(screen.getByText('No prerequisites')).toBeInTheDocument())
  })
})
