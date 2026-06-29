import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest'
import { prerequisiteService } from '../../services/prerequisiteService'
import { server } from '../mocks/server'
import { neighborhoodHandlers, neighborhoodFixture } from '../mocks/handlers/neighborhoodHandlers'

describe('prerequisiteService.getNeighborhood', () => {
  beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
  afterEach(() => server.resetHandlers())
  afterAll(() => server.close())

  it('GETs the neighborhood and returns the parsed body', async () => {
    server.use(...neighborhoodHandlers)
    const result = await prerequisiteService.getNeighborhood('center-1', 2)
    expect(result.center_id).toBe(neighborhoodFixture.center_id)
    expect(result.nodes).toHaveLength(2)
    expect(result.edges[0].source).toBe('p-1')
  })
})
