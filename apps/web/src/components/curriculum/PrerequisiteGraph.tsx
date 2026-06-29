import { useMemo } from 'react'
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  MarkerType,
  type Node,
  type Edge,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import type { NeighborhoodResponse } from '../../services/prerequisiteService'
import { clusterNeighborhood } from '../../utils/graphClustering'
import { layoutGraph } from '../../utils/graphLayout'
import ConceptGraphNode, { type GraphNodeData } from './ConceptGraphNode'

interface PrerequisiteGraphProps {
  neighborhood: NeighborhoodResponse
  expanded: Set<string>
  kaColorMap: Record<string, string>
  onRecenter: (conceptId: string) => void
  onToggleCluster: (clusterId: string) => void
}

const NODE_TYPES = { graphNode: ConceptGraphNode }
const DEFAULT_KA_COLOR = '#94a3b8'

/** React Flow wrapper: clusters + lays out a neighborhood and renders it. */
export default function PrerequisiteGraph({
  neighborhood,
  expanded,
  kaColorMap,
  onRecenter,
  onToggleCluster,
}: PrerequisiteGraphProps) {
  const { nodes, edges } = useMemo(() => {
    const visible = clusterNeighborhood(neighborhood, expanded)
    const positioned = layoutGraph(visible.nodes, visible.edges)

    const rfNodes: Node<GraphNodeData>[] = positioned.map((n) => {
      if (n.data.kind === 'cluster') {
        return {
          id: n.id,
          type: 'graphNode',
          position: n.position,
          data: {
            kind: 'cluster',
            direction: n.data.direction,
            hiddenCount: n.data.hiddenCount,
            onExpand: () => onToggleCluster(n.id),
          },
        }
      }
      return {
        id: n.id,
        type: 'graphNode',
        position: n.position,
        data: {
          kind: 'concept',
          node: n.data.node,
          kaColor: kaColorMap[n.data.node.knowledge_area_id] ?? DEFAULT_KA_COLOR,
          isCenter: n.data.node.direction === 'center',
          onRecenter,
        },
      }
    })

    const rfEdges: Edge[] = visible.edges.map((e) => ({
      id: e.id,
      source: e.source,
      target: e.target,
      markerEnd: { type: MarkerType.ArrowClosed },
    }))

    return { nodes: rfNodes, edges: rfEdges }
  }, [neighborhood, expanded, kaColorMap, onRecenter, onToggleCluster])

  return (
    <div className="h-[70vh] w-full rounded-[14px] border border-gray-200 bg-white">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={NODE_TYPES}
        fitView
        proOptions={{ hideAttribution: true }}
      >
        <Background />
        <Controls />
        <MiniMap pannable zoomable />
      </ReactFlow>
    </div>
  )
}
