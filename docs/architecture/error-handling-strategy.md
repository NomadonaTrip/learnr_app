# Error Handling Strategy

### Error Response Format

```typescript
interface ApiError {
  error: {
    code: string;           // VALIDATION_ERROR, AUTH_ERROR, etc.
    message: string;        // User-friendly message
    details?: Record<string, any>;  // Field-specific errors
    timestamp: string;      // ISO 8601
    request_id: string;     // For tracing
  };
}
```

### Frontend Error Handling

Axios interceptors handle errors globally, displaying user-friendly toast messages and logging to Sentry for monitoring.

### Backend Error Handling

FastAPI global exception handlers return consistent error format with request IDs for tracing and structured logging for debugging.

---
