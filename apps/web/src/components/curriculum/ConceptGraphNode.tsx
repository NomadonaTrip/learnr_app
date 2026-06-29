import { Handle, Position } from '@xyflow/react'
import type { NeighborhoodNode } from '../../services/prerequisiteService'
import { useConceptPractice } from '../../hooks/useConceptPractice'
import { ConceptLockBadge } from './ConceptLockBadge'
import { LockedConceptConfirmDialog } from './LockedConceptConfirmDialog'

export type GraphNodeData =
  | {
      kind: 'concept'
      node: NeighborhoodNode
      kaColor: string
      isCenter: boolean
      onRecenter: (conceptId: string) => void
    }
  | {
      kind: 'cluster'
      direction: 'prereq' | 'unlock'
      hiddenCount: number
      onExpand: () => void
    }

const DIRECTION_LABEL = { prereq: 'prerequisites', unlock: 'unlocks' } as const

/** A React Flow custom node: either a concept card or an expandable cluster. */
export default function ConceptGraphNode({ data }: { data: GraphNodeData }) {
  if (data.kind === 'cluster') {
    return (
      <>
        <Handle type="target" position={Position.Top} />
        <button
          type="button"
          onClick={data.onExpand}
          aria-expanded={false}
          className="rounded-[14px] border border-dashed border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-600 hover:bg-gray-50"
        >
          +{data.hiddenCount} more {DIRECTION_LABEL[data.direction]} &#9658;
        </button>
        <Handle type="source" position={Position.Bottom} />
      </>
    )
  }

  const { node, kaColor, isCenter, onRecenter } = data
  return <ConceptCard node={node} kaColor={kaColor} isCenter={isCenter} onRecenter={onRecenter} />
}

function ConceptCard({
  node,
  kaColor,
  isCenter,
  onRecenter,
}: {
  node: NeighborhoodNode
  kaColor: string
  isCenter: boolean
  onRecenter: (conceptId: string) => void
}) {
  const practice = useConceptPractice({
    conceptId: node.concept_id,
    conceptName: node.name,
    isUnlocked: node.is_unlocked,
  })

  return (
    <div
      onClick={() => { if (!isCenter) onRecenter(node.concept_id) }}
      className={`w-[200px] rounded-[14px] border-l-4 bg-white p-3 shadow-sm ${
        isCenter ? 'ring-2 ring-primary-500' : 'cursor-pointer hover:shadow-md'
      }`}
      style={{ borderLeftColor: kaColor }}
    >
      <Handle type="target" position={Position.Top} />
      <p className="truncate text-sm font-medium text-gray-900">{node.name}</p>
      <div className="mt-1 flex items-center gap-2">
        <ConceptLockBadge isUnlocked={node.is_unlocked} />
        <span className="text-xs text-gray-500">
          {Math.round(node.mastery_progress * 100)}%
        </span>
      </div>
      <button
        type="button"
        onClick={(e) => { e.stopPropagation(); practice.handlePractice() }}
        className="mt-2 w-full rounded-[14px] border border-primary-200 px-2 py-1 text-xs font-medium text-primary-700 hover:bg-primary-50"
      >
        Practice
      </button>
      {practice.showDialog && (
        <LockedConceptConfirmDialog
          conceptName={node.name}
          blockingPrerequisites={[]}
          isSubmitting={practice.isSubmitting}
          isError={practice.isError}
          onConfirm={practice.confirm}
          onCancel={practice.cancel}
        />
      )}
      <Handle type="source" position={Position.Bottom} />
    </div>
  )
}
