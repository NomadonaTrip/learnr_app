import { setupServer } from 'msw/node'
import { diagnosticHandlers } from './handlers/diagnosticHandlers'
import { quizHandlers } from './handlers/quizHandlers'

export const server = setupServer(...diagnosticHandlers, ...quizHandlers)
