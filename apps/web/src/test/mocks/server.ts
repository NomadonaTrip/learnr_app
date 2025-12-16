import { setupServer } from 'msw/node'
import { diagnosticHandlers } from './handlers/diagnosticHandlers'

export const server = setupServer(...diagnosticHandlers)
