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
  const candidateEdges: VisibleEdge[] = []
  // Tracks every id that is part of the visible set (concept ids + cluster ids).
  // A group whose parent is not emitted is skipped entirely so collapsed parents
  // never leave orphan grandchildren or dangling edges.
  const emitted = new Set<string>()

  // Always include the center node; seed `emitted` with it.
  const center = neighborhood.nodes.find((n) => n.direction === 'center')
  if (center) {
    nodes.push({ id: center.concept_id, data: { kind: 'concept', node: center } })
    emitted.add(center.concept_id)
  }

  // Process groups CENTER-OUTWARD so a parent is emitted (or proven hidden)
  // before any of its own children's groups are considered.
  const sortedKeys = [...groups.keys()].sort((k1, k2) => {
    const p1 = byId.get(k1.slice(0, k1.lastIndexOf(':')))
    const p2 = byId.get(k2.slice(0, k2.lastIndexOf(':')))
    return Math.abs(p1?.depth ?? 0) - Math.abs(p2?.depth ?? 0)
  })

  for (const key of sortedKeys) {
    const splitAt = key.lastIndexOf(':')
    const parentId = key.slice(0, splitAt)
    const direction = key.slice(splitAt + 1) as 'prereq' | 'unlock'

    // If the parent was collapsed/hidden, its children must not appear at all.
    if (!emitted.has(parentId)) continue

    const children = [...(groups.get(key) ?? [])].sort(
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
      // A diamond's shared node is reachable from multiple parents: emit the node
      // once, but still record each legitimate parent edge.
      if (!emitted.has(child.node.concept_id)) {
        nodes.push({
          id: child.node.concept_id,
          data: { kind: 'concept', node: child.node },
        })
        emitted.add(child.node.concept_id)
      }
      candidateEdges.push({
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
      emitted.add(clusterId)
      // Edge orientation matches the direction: prereqs point up to the parent,
      // unlocks point down from the parent.
      candidateEdges.push(
        direction === 'prereq'
          ? { id: `${clusterId}->${parentId}`, source: clusterId, target: parentId }
          : { id: `${parentId}->${clusterId}`, source: parentId, target: clusterId }
      )
    }
  }

  // Keep only edges whose BOTH endpoints are part of the visible set, deduped by id.
  const edges: VisibleEdge[] = []
  const seenEdges = new Set<string>()
  for (const edge of candidateEdges) {
    if (!emitted.has(edge.source) || !emitted.has(edge.target)) continue
    if (seenEdges.has(edge.id)) continue
    seenEdges.add(edge.id)
    edges.push(edge)
  }

  return { nodes, edges }
}
