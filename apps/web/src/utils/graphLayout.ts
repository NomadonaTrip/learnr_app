import dagre from 'dagre'
import type { VisibleEdge, VisibleNode } from './graphClustering'

export type PositionedNode = VisibleNode & {
  position: { x: number; y: number }
}

const NODE_WIDTH = 200
const NODE_HEIGHT = 84

/**
 * Lay out the neighborhood top-to-bottom with prerequisites below the concepts
 * they unlock (rankdir 'BT' so arrows read upward). Pure. Story 4.11 Slice D.
 */
export function layoutGraph(
  nodes: VisibleNode[],
  edges: VisibleEdge[]
): PositionedNode[] {
  const g = new dagre.graphlib.Graph()
  g.setGraph({ rankdir: 'BT', nodesep: 48, ranksep: 96 })
  g.setDefaultEdgeLabel(() => ({}))

  for (const node of nodes) {
    g.setNode(node.id, { width: NODE_WIDTH, height: NODE_HEIGHT })
  }
  for (const edge of edges) {
    g.setEdge(edge.source, edge.target)
  }

  dagre.layout(g)

  return nodes.map((node) => {
    const { x, y } = g.node(node.id)
    return {
      ...node,
      position: { x: x - NODE_WIDTH / 2, y: y - NODE_HEIGHT / 2 },
    }
  })
}
