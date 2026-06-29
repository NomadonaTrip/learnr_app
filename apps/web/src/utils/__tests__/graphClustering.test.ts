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

  it('emits a shared depth-2 prereq exactly once (DIAMOND), with both parent edges', () => {
    // center c; depth-1 prereqs a,b (a->c, b->c); shared depth-2 prereq g (g->a, g->b).
    const nodes: NeighborhoodNode[] = [
      { concept_id: 'c', name: 'C', knowledge_area_id: 'ka', difficulty: 0.5, is_unlocked: true, mastery_progress: 1, depth: 0, direction: 'center' },
      { concept_id: 'a', name: 'A', knowledge_area_id: 'ka', difficulty: 0.4, is_unlocked: false, mastery_progress: 0.5, depth: -1, direction: 'prereq' },
      { concept_id: 'b', name: 'B', knowledge_area_id: 'ka', difficulty: 0.4, is_unlocked: false, mastery_progress: 0.5, depth: -1, direction: 'prereq' },
      { concept_id: 'g', name: 'G', knowledge_area_id: 'ka', difficulty: 0.3, is_unlocked: false, mastery_progress: 0.2, depth: -2, direction: 'prereq' },
    ]
    const edges = [
      { source: 'a', target: 'c', relationship_type: 'required', strength: 0.8 },
      { source: 'b', target: 'c', relationship_type: 'required', strength: 0.7 },
      { source: 'g', target: 'a', relationship_type: 'required', strength: 0.6 },
      { source: 'g', target: 'b', relationship_type: 'required', strength: 0.5 },
    ]
    const neighborhood: NeighborhoodResponse = { center_id: 'c', depth: 2, truncated: false, nodes, edges }
    const { nodes: visNodes, edges: visEdges } = clusterNeighborhood(neighborhood, new Set())

    // g appears exactly once
    expect(visNodes.filter((n) => n.id === 'g')).toHaveLength(1)
    // no duplicate node ids
    const ids = visNodes.map((n) => n.id)
    expect(new Set(ids).size).toBe(ids.length)
    // both diamond edges present
    expect(visEdges.some((e) => e.source === 'g' && e.target === 'a')).toBe(true)
    expect(visEdges.some((e) => e.source === 'g' && e.target === 'b')).toBe(true)
    // connectedness invariant: every edge endpoint is a visible node
    const idSet = new Set(ids)
    for (const e of visEdges) {
      expect(idSet.has(e.source)).toBe(true)
      expect(idSet.has(e.target)).toBe(true)
    }
  })

  it('drops grandchildren of a collapsed (hidden) parent (COLLAPSED PARENT)', () => {
    // center c with > threshold prereqs so some overflow; the LOWEST-strength one
    // (p0, hidden) has its own depth-2 child gc that must not appear.
    const hub = makeHub(CLUSTER_THRESHOLD + 2)
    // p0 is hidden (lowest strength). Give it a depth-2 child.
    hub.nodes.push({ concept_id: 'gc', name: 'GC', knowledge_area_id: 'ka', difficulty: 0.3, is_unlocked: false, mastery_progress: 0.1, depth: -2, direction: 'prereq' })
    hub.edges.push({ source: 'gc', target: 'p0', relationship_type: 'required', strength: 0.9 })

    const { nodes, edges } = clusterNeighborhood(hub, new Set())
    const ids = nodes.map((n) => n.id)
    // p0 is hidden, so neither p0 nor its grandchild gc are visible nodes
    expect(ids).not.toContain('gc')
    expect(ids).not.toContain('p0')
    // no edge references p0 as an endpoint (only the cluster chip + its edge to center remain)
    expect(edges.some((e) => e.source === 'p0' || e.target === 'p0')).toBe(false)
    // connectedness invariant
    const idSet = new Set(ids)
    for (const e of edges) {
      expect(idSet.has(e.source)).toBe(true)
      expect(idSet.has(e.target)).toBe(true)
    }
  })

  it('collapses overflow dependents into one unlock cluster oriented from center', () => {
    const nodes: NeighborhoodNode[] = [
      { concept_id: 'c', name: 'C', knowledge_area_id: 'ka', difficulty: 0.5, is_unlocked: true, mastery_progress: 1, depth: 0, direction: 'center' },
    ]
    const edges = []
    const depCount = CLUSTER_THRESHOLD + 3
    for (let i = 0; i < depCount; i++) {
      nodes.push({ concept_id: `d${i}`, name: `D${i}`, knowledge_area_id: 'ka', difficulty: 0.4, is_unlocked: false, mastery_progress: i / depCount, depth: 1, direction: 'unlock' as const })
      edges.push({ source: 'c', target: `d${i}`, relationship_type: 'required', strength: i / depCount })
    }
    const neighborhood: NeighborhoodResponse = { center_id: 'c', depth: 2, truncated: false, nodes, edges }
    const { nodes: visNodes, edges: visEdges } = clusterNeighborhood(neighborhood, new Set())

    const clusters = visNodes.filter((n) => n.data.kind === 'cluster')
    expect(clusters).toHaveLength(1)
    expect((clusters[0].data as { direction: string }).direction).toBe('unlock')
    const clusterId = clusters[0].id
    // unlock cluster edge oriented source=center, target=clusterId
    expect(visEdges.some((e) => e.source === 'c' && e.target === clusterId)).toBe(true)
  })
})
