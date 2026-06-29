import { describe, it, expect } from 'vitest'
import { layoutGraph } from '../graphLayout'
import type { VisibleNode, VisibleEdge } from '../graphClustering'

const center: VisibleNode = { id: 'c', data: { kind: 'concept', node: { concept_id: 'c', name: 'C', knowledge_area_id: 'ka', difficulty: 0.5, is_unlocked: true, mastery_progress: 1, depth: 0, direction: 'center' } } }
const prereq: VisibleNode = { id: 'p', data: { kind: 'concept', node: { concept_id: 'p', name: 'P', knowledge_area_id: 'ka', difficulty: 0.4, is_unlocked: false, mastery_progress: 0.3, depth: -1, direction: 'prereq' } } }
const edges: VisibleEdge[] = [{ id: 'p->c', source: 'p', target: 'c' }]

describe('layoutGraph', () => {
  it('assigns a numeric position to every node', () => {
    const positioned = layoutGraph([center, prereq], edges)
    expect(positioned).toHaveLength(2)
    for (const n of positioned) {
      expect(typeof n.position.x).toBe('number')
      expect(typeof n.position.y).toBe('number')
    }
  })

  it('places the prerequisite below the concept it unlocks (bottom-up rank)', () => {
    const positioned = layoutGraph([center, prereq], edges)
    const c = positioned.find((n) => n.id === 'c')!
    const p = positioned.find((n) => n.id === 'p')!
    expect(p.position.y).toBeGreaterThan(c.position.y) // larger y = lower on screen
  })
})
