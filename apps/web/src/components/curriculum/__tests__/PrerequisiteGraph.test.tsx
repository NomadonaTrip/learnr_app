import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import PrerequisiteGraph from '../PrerequisiteGraph'
import type { NeighborhoodResponse } from '../../../services/prerequisiteService'

// Render a lightweight stand-in for the canvas: expose node count + ids.
vi.mock('@xyflow/react', () => ({
  ReactFlow: ({ nodes }: { nodes: Array<{ id: string }> }) => (
    <div data-testid="rf">
      {nodes.map((n) => <span key={n.id} data-testid="rf-node">{n.id}</span>)}
    </div>
  ),
  Background: () => null,
  Controls: () => null,
  MiniMap: () => null,
  MarkerType: { ArrowClosed: 'arrowclosed' },
}))

const neighborhood: NeighborhoodResponse = {
  center_id: 'c', depth: 2, truncated: false,
  nodes: [
    { concept_id: 'c', name: 'C', knowledge_area_id: 'ka-1', difficulty: 0.5, is_unlocked: true, mastery_progress: 1, depth: 0, direction: 'center' },
    { concept_id: 'p', name: 'P', knowledge_area_id: 'ka-1', difficulty: 0.4, is_unlocked: false, mastery_progress: 0.3, depth: -1, direction: 'prereq' },
  ],
  edges: [{ source: 'p', target: 'c', relationship_type: 'required', strength: 0.8 }],
}

describe('PrerequisiteGraph', () => {
  it('renders one React Flow node per visible node', () => {
    render(
      <PrerequisiteGraph
        neighborhood={neighborhood}
        expanded={new Set()}
        kaColorMap={{ 'ka-1': '#3b82f6' }}
        onRecenter={vi.fn()}
        onToggleCluster={vi.fn()}
      />
    )
    expect(screen.getByTestId('rf')).toBeInTheDocument()
    expect(screen.getAllByTestId('rf-node')).toHaveLength(2)
  })
})
