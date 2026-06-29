import { describe, it, expect } from 'vitest'
import { clusterNeighborhood, CLUSTER_THRESHOLD } from '../graphClustering'
import type { NeighborhoodNode, NeighborhoodResponse } from '../../services/prerequisiteService'

function makeHub(prereqCount: number): NeighborhoodResponse {
  const nodes: NeighborhoodNode[] = [
    { concept_id: 'c', name: 'C', knowledge_area_id: 'ka', difficulty: 0.5, is_unlocked: true, mastery_progress: 1, depth: 0, direction: 'center' as const },
  ]
  const edges = []
  for (let i = 0; i < prereqCount; i++) {
    nodes.push({ concept_id: `p${i}`, name: `P${i}`, knowledge_area_id: 'ka', difficulty: 0.4, is_unlocked: false, mastery_progress: i / prereqCount, depth: -1, direction: 'prereq' as const })
    edges.push({ source: `p${i}`, target: 'c', relationship_type: 'required', strength: i / prereqCount })
  }
  return { center_id: 'c', depth: 2, truncated: false, nodes, edges }
}

describe('clusterNeighborhood', () => {
  it('shows all children when at or under the threshold', () => {
    const { nodes } = clusterNeighborhood(makeHub(CLUSTER_THRESHOLD), new Set())
    expect(nodes.filter((n) => n.data.kind === 'cluster')).toHaveLength(0)
    expect(nodes).toHaveLength(CLUSTER_THRESHOLD + 1) // + center
  })

  it('collapses overflow into one cluster node', () => {
    const { nodes, edges } = clusterNeighborhood(makeHub(CLUSTER_THRESHOLD + 5), new Set())
    const clusters = nodes.filter((n) => n.data.kind === 'cluster')
    expect(clusters).toHaveLength(1)
    expect((clusters[0].data as { hiddenCount: number }).hiddenCount).toBe(5)
    // top-K concept children + 1 cluster + center
    expect(nodes.filter((n) => n.data.kind === 'concept')).toHaveLength(CLUSTER_THRESHOLD + 1)
    // cluster has an edge to its parent
    expect(edges.some((e) => e.target === 'c' && e.source.startsWith('cluster:'))).toBe(true)
  })

  it('expands a cluster when its id is in the expanded set', () => {
    const hub = makeHub(CLUSTER_THRESHOLD + 5)
    const clusterId = `cluster:c:prereq`
    const { nodes } = clusterNeighborhood(hub, new Set([clusterId]))
    expect(nodes.filter((n) => n.data.kind === 'cluster')).toHaveLength(0)
    expect(nodes.filter((n) => n.data.kind === 'concept')).toHaveLength(CLUSTER_THRESHOLD + 5 + 1)
  })

  it('keeps top children ranked by strength desc', () => {
    const { nodes } = clusterNeighborhood(makeHub(CLUSTER_THRESHOLD + 3), new Set())
    const shown = nodes.filter((n) => n.data.kind === 'concept' && n.id !== 'c')
      .map((n) => (n.data as { node: { concept_id: string } }).node.concept_id)
    // highest-index prereqs have highest strength; the lowest-strength ones get hidden
    expect(shown).not.toContain('p0')
  })
})
