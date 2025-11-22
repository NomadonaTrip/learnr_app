// Shared TypeScript type definitions
// TODO: Move to packages/shared-types when implementing cross-app type sharing

export interface User {
  id: string
  email: string
  name: string
}

export interface ApiError {
  message: string
  code: string
}
