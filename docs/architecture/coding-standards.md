# Coding Standards

### Critical Fullstack Rules

- **Type Sharing:** Always define types in `packages/shared-types` and import from there - never duplicate type definitions between frontend/backend
- **API Calls:** Never make direct HTTP calls with axios in components - use the service layer (`quizService`, `authService`, etc.)
- **Environment Variables:** Access only through config objects, never `process.env` directly in components/services
- **Error Handling:** All API routes must use the standard error handler middleware - return consistent error format
- **State Updates:** Never mutate state directly in Zustand stores - use immutable update patterns
- **Database Access:** Never write raw SQL - use SQLAlchemy ORM and repository pattern exclusively
- **Async/Await:** All database and API operations must use async/await - no callbacks or .then() chains
- **Component Props:** Keep prop drilling to max 2 levels - use context or global state for deeper nesting

### Naming Conventions

| Element | Frontend | Backend | Example |
|---------|----------|---------|---------|
| **Components** | PascalCase | - | `UserProfile.tsx` |
| **Hooks** | camelCase with 'use' | - | `useAuth.ts` |
| **API Routes** | - | kebab-case | `/api/user-profile` |
| **Database Tables** | - | snake_case | `user_profiles` |
| **TypeScript Interfaces** | PascalCase | - | `interface User` |
| **Python Classes** | PascalCase | PascalCase | `class UserRepository` |
| **Functions/Methods** | camelCase | snake_case | `getUserById()` (TS), `get_user_by_id()` (Python) |
| **Constants** | UPPER_SNAKE_CASE | UPPER_SNAKE_CASE | `MAX_QUESTIONS` |
| **Env Variables** | UPPER_SNAKE_CASE | UPPER_SNAKE_CASE | `VITE_API_BASE_URL` |

---
