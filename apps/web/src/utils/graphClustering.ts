import type {
  NeighborhoodNode,
  NeighborhoodResponse,
} from '../services/prerequisiteService'

/** Max children shown per (parent, direction) before overflow is collapsed. */
export const CLUSTER_THRESHOLD = 6

export interface ConceptNodeData {
  kind: 'concept'
  node: NeighborhoodNode
}

export interface ClusterNodeData {
  kind: 'cluster'
  parentId: string
  direction: 'prereq' | 'unlock'
  hiddenCount: number
  hiddenIds: string[]
}

export interface VisibleNode {
  id: string
  data: ConceptNodeData | ClusterNodeData
}

export interface VisibleEdge {
  id: string
  source: string
  target: string
}

interface Child {
  node: NeighborhoodNode
  strength: number
  edge: { source: string; target: string }
}

/**
 * Transform a neighborhood into render-ready nodes/edges, collapsing dense
 * (parent, direction) groups into expandable cluster nodes. Pure. Story 4.11 D.
 */
export function clusterNeighborhood(
  neighborhood: NeighborhoodResponse,
  expanded: Set<string>
): { nodes: VisibleNode[]; edges: VisibleEdge[] } {
  const byId = new Map(neighborhood.nodes.map((n) => [n.concept_id, n]))

  // Group children by (parentId, direction). The child is the endpoint with the
  // larger absolute depth; the parent is the more-central endpoint.
  const groups = new Map<string, Child[]>()
  for (const edge of neighborhood.edges) {
    const a = byId.get(edge.source)
    const b = byId.get(edge.target)
    if (!a || !b) continue
    const childNode = Math.abs(a.depth) >= Math.abs(b.depth) ? a : b
    const parentNode = childNode === a ? b : a
    const direction = childNode.direction === 'unlock' ? 'unlock' : 'prereq'
    const key = `${parentNode.concept_id}:${direction}`
    const list = groups.get(key) ?? []
    list.push({ node: childNode, strength: edge.strength, edge })
    groups.set(key, list)
  }

  const nodes: VisibleNode[] = []
  const edges: VisibleEdge[] = []

  // Always include the center node.
  const center = neighborhood.nodes.find((n) => n.direction === 'center')
  if (center) {
    nodes.push({ id: center.concept_id, data: { kind: 'concept', node: center } })
  }

  for (const [key, childrenRaw] of groups) {
    const [parentId, direction] = key.split(':') as [string, 'prereq' | 'unlock']
    const children = [...childrenRaw].sort(
      (x, y) =>
        y.strength - x.strength ||
        y.node.mastery_progress - x.node.mastery_progress
    )
    const clusterId = `cluster:${parentId}:${direction}`
    const isExpanded = expanded.has(clusterId)
    const overflow = children.length > CLUSTER_THRESHOLD && !isExpanded
    const shown = overflow ? children.slice(0, CLUSTER_THRESHOLD) : children
    const hidden = overflow ? children.slice(CLUSTER_THRESHOLD) : []

    for (const child of shown) {
      nodes.push({
        id: child.node.concept_id,
        data: { kind: 'concept', node: child.node },
      })
      edges.push({
        id: `${child.edge.source}->${child.edge.target}`,
        source: child.edge.source,
        target: child.edge.target,
      })
    }

    if (hidden.length > 0) {
      nodes.push({
        id: clusterId,
        data: {
          kind: 'cluster',
          parentId,
          direction,
          hiddenCount: hidden.length,
          hiddenIds: hidden.map((h) => h.node.concept_id),
        },
      })
      // Edge orientation matches the direction: prereqs point up to the parent,
      // unlocks point down from the parent.
      edges.push(
        direction === 'prereq'
          ? { id: `${clusterId}->${parentId}`, source: clusterId, target: parentId }
          : { id: `${parentId}->${clusterId}`, source: parentId, target: clusterId }
      )
    }
  }

  return { nodes, edges }
}
