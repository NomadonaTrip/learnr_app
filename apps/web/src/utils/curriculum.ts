import type { ConceptUnlockStatus } from '../services/prerequisiteService'

export interface KnowledgeAreaMeta {
  id: string
  name: string
  abbreviation: string
  color_hex: string
}

export interface KaGroup {
  knowledgeArea: KnowledgeAreaMeta
  concepts: ConceptUnlockStatus[]
  unlockedCount: number
  totalCount: number
}

/**
 * Group concepts under their knowledge area, preserving KA order and
 * dropping KAs with no concepts.
 */
export function groupConceptsByKa(
  concepts: ConceptUnlockStatus[],
  knowledgeAreas: KnowledgeAreaMeta[],
): KaGroup[] {
  return knowledgeAreas
    .map((knowledgeArea) => {
      const kaConcepts = concepts.filter(
        (c) => c.knowledge_area_id === knowledgeArea.id,
      )
      return {
        knowledgeArea,
        concepts: kaConcepts,
        unlockedCount: kaConcepts.filter((c) => c.is_unlocked).length,
        totalCount: kaConcepts.length,
      }
    })
    .filter((group) => group.totalCount > 0)
}

/**
 * Build the focused-practice quiz URL for a single concept, matching the
 * existing `/quiz?focus=concept&targets=…` convention (QuizPage parses these).
 */
export function buildFocusQuizUrl(conceptId: string, conceptName: string): string {
  return `/quiz?focus=concept&targets=${encodeURIComponent(
    conceptId,
  )}&name=${encodeURIComponent(conceptName)}`
}
