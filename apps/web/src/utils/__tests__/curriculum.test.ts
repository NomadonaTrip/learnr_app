import { describe, it, expect } from 'vitest'
import { groupConceptsByKa, buildFocusQuizUrl } from '../curriculum'
import type { ConceptUnlockStatus } from '../../services/prerequisiteService'

const ka = [
  { id: 'ka-plan', name: 'Planning', abbreviation: 'BAPM', color_hex: '#3b82f6' },
  { id: 'ka-elic', name: 'Elicitation', abbreviation: 'EC', color_hex: '#22c55e' },
]

function concept(id: string, kaId: string, unlocked: boolean): ConceptUnlockStatus {
  return {
    concept_id: id, concept_name: id, knowledge_area_id: kaId,
    is_unlocked: unlocked, has_prerequisites: !unlocked,
    prerequisite_count: unlocked ? 0 : 2, mastered_prerequisite_count: unlocked ? 0 : 1,
    mastery_progress: unlocked ? 1 : 0.5,
  }
}

describe('groupConceptsByKa', () => {
  it('groups concepts under their KA and counts unlocked/total', () => {
    const groups = groupConceptsByKa(
      [concept('a', 'ka-plan', true), concept('b', 'ka-plan', false), concept('c', 'ka-elic', true)],
      ka,
    )
    expect(groups).toHaveLength(2)
    expect(groups[0].knowledgeArea.id).toBe('ka-plan')
    expect(groups[0].totalCount).toBe(2)
    expect(groups[0].unlockedCount).toBe(1)
    expect(groups[1].knowledgeArea.id).toBe('ka-elic')
  })

  it('drops KAs that have no concepts', () => {
    const groups = groupConceptsByKa([concept('a', 'ka-plan', true)], ka)
    expect(groups).toHaveLength(1)
    expect(groups[0].knowledgeArea.id).toBe('ka-plan')
  })
})

describe('buildFocusQuizUrl', () => {
  it('encodes the concept id and name', () => {
    expect(buildFocusQuizUrl('c-1', 'Risk & Value')).toBe(
      '/quiz?focus=concept&targets=c-1&name=Risk%20%26%20Value',
    )
  })
})
