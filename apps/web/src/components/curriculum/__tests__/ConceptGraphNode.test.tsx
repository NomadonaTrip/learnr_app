import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import ConceptGraphNode, { type GraphNodeData } from '../ConceptGraphNode'

// React Flow Handle needs a provider/DOM; stub the bits we use.
vi.mock('@xyflow/react', () => ({
  Handle: () => null,
  Position: { Top: 'top', Bottom: 'bottom' },
}))

function renderNode(data: GraphNodeData) {
  const client = new QueryClient()
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        {/* React Flow calls the node with { data }; emulate that. */}
        <ConceptGraphNode data={data} />
      </MemoryRouter>
    </QueryClientProvider>
  )
}

const conceptNode = {
  concept_id: 'p1', name: 'Stakeholder Analysis', knowledge_area_id: 'ka-1',
  difficulty: 0.5, is_unlocked: false, mastery_progress: 0.3, depth: -1, direction: 'prereq' as const,
}

describe('ConceptGraphNode', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('renders a concept node with name and re-centers on click', () => {
    const onRecenter = vi.fn()
    renderNode({ kind: 'concept', node: conceptNode, kaColor: '#3b82f6', isCenter: false, onRecenter })
    expect(screen.getByText('Stakeholder Analysis')).toBeInTheDocument()
    fireEvent.click(screen.getByText('Stakeholder Analysis'))
    expect(onRecenter).toHaveBeenCalledWith('p1')
  })

  it('does not re-center when the node is the center', () => {
    const onRecenter = vi.fn()
    renderNode({ kind: 'concept', node: { ...conceptNode, direction: 'center', depth: 0 }, kaColor: '#3b82f6', isCenter: true, onRecenter })
    fireEvent.click(screen.getByText('Stakeholder Analysis'))
    expect(onRecenter).not.toHaveBeenCalled()
  })

  it('renders a cluster node and calls onExpand', () => {
    const onExpand = vi.fn()
    renderNode({ kind: 'cluster', direction: 'prereq', hiddenCount: 7, onExpand })
    const btn = screen.getByRole('button', { name: /7 more prerequisites/i })
    fireEvent.click(btn)
    expect(onExpand).toHaveBeenCalled()
  })
})
