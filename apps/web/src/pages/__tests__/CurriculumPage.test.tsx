import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { CurriculumPage } from '../CurriculumPage'
import { courseService } from '../../services/courseService'
import { prerequisiteService } from '../../services/prerequisiteService'

vi.mock('../../components/layout/Navigation', () => ({ Navigation: () => null }))
// KnowledgeAreaSection pulls ConceptRow (router/hooks); stub for a page-level test.
vi.mock('../../components/curriculum/KnowledgeAreaSection', () => ({
  KnowledgeAreaSection: ({ group }: { group: { knowledgeArea: { name: string } } }) => (
    <div data-testid="ka-section">{group.knowledgeArea.name}</div>
  ),
}))
vi.mock('../../services/courseService', () => ({
  courseService: { fetchCourseBySlug: vi.fn() },
}))
vi.mock('../../services/prerequisiteService', () => ({
  prerequisiteService: { getBulkUnlockStatus: vi.fn() },
}))
vi.mock('../../components/curriculum/RecentlyUnlockedStrip', () => ({
  RecentlyUnlockedStrip: () => null,
}))

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <CurriculumPage />
    </QueryClientProvider>,
  )
}

const course = {
  id: 'course-1', slug: 'cbap', name: 'CBAP', knowledge_areas: [
    { id: 'ka-1', name: 'Planning', abbreviation: 'BAPM', color_hex: '#3b82f6' },
  ],
}

describe('CurriculumPage', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('renders KA sections on success', async () => {
    vi.mocked(courseService.fetchCourseBySlug).mockResolvedValue(course as never)
    vi.mocked(prerequisiteService.getBulkUnlockStatus).mockResolvedValue({
      knowledge_area_id: null, total_concepts: 1, unlocked_count: 1, locked_count: 0,
      no_prerequisites_count: 1, concepts: [
        { concept_id: 'a', concept_name: 'Approach', knowledge_area_id: 'ka-1', is_unlocked: true, has_prerequisites: false, prerequisite_count: 0, mastered_prerequisite_count: 0, mastery_progress: 1 },
      ],
    })
    renderPage()
    await waitFor(() => expect(screen.getByTestId('ka-section')).toHaveTextContent('Planning'))
  })

  it('shows the not-ready empty state when there are no concepts', async () => {
    vi.mocked(courseService.fetchCourseBySlug).mockResolvedValue(course as never)
    vi.mocked(prerequisiteService.getBulkUnlockStatus).mockResolvedValue({
      knowledge_area_id: null, total_concepts: 0, unlocked_count: 0, locked_count: 0,
      no_prerequisites_count: 0, concepts: [],
    })
    renderPage()
    await waitFor(() =>
      expect(screen.getByText(/curriculum map isn't ready/i)).toBeInTheDocument(),
    )
  })

  it('shows an error card when the status request fails', async () => {
    vi.mocked(courseService.fetchCourseBySlug).mockResolvedValue(course as never)
    vi.mocked(prerequisiteService.getBulkUnlockStatus).mockRejectedValue(new Error('boom'))
    renderPage()
    await waitFor(() =>
      expect(screen.getByText(/couldn't load your curriculum/i)).toBeInTheDocument(),
    )
  })
})
