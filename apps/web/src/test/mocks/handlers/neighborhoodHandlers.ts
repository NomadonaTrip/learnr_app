import { http, HttpResponse } from 'msw'

export const neighborhoodFixture = {
  center_id: 'center-1',
  depth: 2,
  truncated: false,
  nodes: [
    { concept_id: 'center-1', name: 'Center', knowledge_area_id: 'ka-1', difficulty: 0.5, is_unlocked: true, mastery_progress: 1, depth: 0, direction: 'center' as const },
    { concept_id: 'p-1', name: 'Prereq', knowledge_area_id: 'ka-1', difficulty: 0.4, is_unlocked: false, mastery_progress: 0.3, depth: -1, direction: 'prereq' as const },
  ],
  edges: [{ source: 'p-1', target: 'center-1', relationship_type: 'required', strength: 0.8 }],
}

export const neighborhoodHandlers = [
  http.get('*/concepts/:id/neighborhood', () => HttpResponse.json(neighborhoodFixture)),
]
