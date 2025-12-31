import { setupServer } from 'msw/node'
import { diagnosticHandlers } from './handlers/diagnosticHandlers'
import { quizHandlers } from './handlers/quizHandlers'
import { readingStatsHandlers } from './handlers/readingStatsHandlers'
import { readingQueueHandlers } from './handlers/readingQueueHandlers'

export const server = setupServer(
  ...diagnosticHandlers,
  ...quizHandlers,
  ...readingStatsHandlers,
  ...readingQueueHandlers
)
