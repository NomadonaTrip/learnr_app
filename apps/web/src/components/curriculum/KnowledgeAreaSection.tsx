import { CollapsibleSection } from '../ui/CollapsibleSection'
import { ConceptRow } from './ConceptRow'
import type { KaGroup } from '../../utils/curriculum'

interface KnowledgeAreaSectionProps {
  group: KaGroup
}

/**
 * Collapsible group of concepts for one knowledge area, with an unlocked/total
 * count in the header (AC 10).
 */
export function KnowledgeAreaSection({ group }: KnowledgeAreaSectionProps) {
  const { knowledgeArea, concepts, unlockedCount, totalCount } = group
  return (
    <CollapsibleSection
      id={`ka-${knowledgeArea.id}`}
      title={`${knowledgeArea.name} — ${unlockedCount}/${totalCount} unlocked`}
      defaultExpanded
    >
      <div className="divide-y divide-gray-100">
        {concepts.map((concept) => (
          <ConceptRow key={concept.concept_id} concept={concept} />
        ))}
      </div>
    </CollapsibleSection>
  )
}
