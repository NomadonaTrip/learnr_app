import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { KnowledgeAreaSection } from '../KnowledgeAreaSection'
import type { KaGroup } from '../../../utils/curriculum'

// ConceptRow pulls in router/hooks; stub it to keep this a pure section test.
vi.mock('../ConceptRow', () => ({
  ConceptRow: ({ concept }: { concept: { concept_name: string } }) => (
    <div data-testid="concept-row">{concept.concept_name}</div>
  ),
}))

const group: KaGroup = {
  knowledgeArea: { id: 'ka-1', name: 'Planning', abbreviation: 'BAPM', color_hex: '#3b82f6' },
  concepts: [
    { concept_id: 'a', concept_name: 'Approach', knowledge_area_id: 'ka-1', is_unlocked: true, has_prerequisites: false, prerequisite_count: 0, mastered_prerequisite_count: 0, mastery_progress: 1 },
    { concept_id: 'b', concept_name: 'Governance', knowledge_area_id: 'ka-1', is_unlocked: false, has_prerequisites: true, prerequisite_count: 2, mastered_prerequisite_count: 1, mastery_progress: 0.5 },
  ],
  unlockedCount: 1,
  totalCount: 2,
}

describe('KnowledgeAreaSection', () => {
  it('renders the KA title with unlocked/total count', () => {
    render(<KnowledgeAreaSection group={group} />)
    expect(screen.getByText(/Planning — 1\/2 unlocked/)).toBeInTheDocument()
  })

  it('renders a row per concept when expanded by default', () => {
    render(<KnowledgeAreaSection group={group} />)
    expect(screen.getAllByTestId('concept-row')).toHaveLength(2)
  })
})
