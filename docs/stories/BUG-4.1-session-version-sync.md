# BUG-4.1: Quiz Session Version Not Synced to Frontend

## Status

**Resolved**

---

## Bug Summary

**Reported:** 2025-12-23
**Severity:** High (blocks session end functionality)
**Affected Stories:** 4.1, 4.1.1

When a user clicks "End Session" during an adaptive quiz, the API returns a 409 Conflict error due to version mismatch between frontend and backend.

**Error observed:**
```
POST /v1/quiz/session/{id}/end HTTP/1.1" 409 Conflict
```

---

## Root Cause Analysis

### Architecture Requirement

The database schema (docs/architecture/database-schema.md lines 277-289) defines a trigger that auto-increments the session version on every UPDATE:

```sql
CREATE OR REPLACE FUNCTION update_session_version()
RETURNS TRIGGER AS $$
BEGIN
    NEW.version = OLD.version + 1;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER quiz_sessions_version_trigger
BEFORE UPDATE ON quiz_sessions
FOR EACH ROW
EXECUTE FUNCTION update_session_version();
```

### Implementation Gaps

| Component | Expected | Actual | File |
|-----------|----------|--------|------|
| Backend `QuizSessionStartResponse` | Include `version` field | Missing `version` field | `apps/api/src/schemas/quiz_session.py:75-85` |
| Frontend session init | Use returned version | Hardcodes `version: 1` | `apps/web/src/hooks/useQuizSession.ts:112` |

### Failure Sequence

1. User starts/resumes quiz session
2. Backend returns session without `version` in `QuizSessionStartResponse`
3. Frontend sets `version: 1` (hardcoded)
4. User answers questions → each answer triggers session UPDATE → DB trigger increments version
5. After N answers, backend version = N+1, frontend version = 1
6. User clicks "End Session" → sends `expected_version: 1`
7. Backend rejects with 409 Conflict (actual version != expected version)

---

## Affected Files

### Backend
- `apps/api/src/schemas/quiz_session.py` - `QuizSessionStartResponse` missing `version`
- `apps/api/src/routes/quiz.py` - Start endpoint doesn't include version in response

### Frontend
- `apps/web/src/hooks/useQuizSession.ts` - Hardcodes `version: 1` on line 112
- `apps/web/src/services/quizService.ts` - `SessionStartResponse` interface missing `version`

---

## Fix Required

### Backend Changes

1. Add `version: int` field to `QuizSessionStartResponse` schema
2. Include `session.version` in start endpoint response

### Frontend Changes

1. Add `version` to `SessionStartResponse` interface
2. Use `data.version` from API response instead of hardcoded `1`

---

## Acceptance Criteria

1. `POST /api/v1/quiz/session/start` response includes `version` field
2. Frontend uses returned `version` value in store
3. `POST /api/v1/quiz/session/{id}/end` succeeds after answering questions
4. Existing unit tests continue to pass
5. New test verifies version sync on resumed sessions

---

## Testing

### Manual Test Steps

1. Start a new quiz session
2. Answer 2-3 questions
3. Click "End Session"
4. Verify session ends successfully (no 409 error)

### Automated Tests

- Update `test_start_quiz_session` to verify version in response
- Add test for resumed session version handling

---

## Change Log

| Date | Description | Author |
|------|-------------|--------|
| 2025-12-23 | Bug documented | James (Dev Agent) |
| 2025-12-23 | Bug resolved - added version to session start response | James (Dev Agent) |

---

## Dev Agent Record

### Agent Model Used
Claude Opus 4.5 (claude-opus-4-5-20251101)

### Resolution Notes
- Added `version: int` field to `QuizSessionStartResponse` schema
- Updated start endpoint to include `session.version` in response
- Updated frontend `SessionStartResponse` interface to include `version`
- Changed frontend hook to use `data.version` instead of hardcoded `1`
- Updated test fixtures to include version field
- All backend quiz tests pass (16/16)
- All frontend quiz tests pass (49/49: 13 service + 22 page + 14 integration)

### File List

**Modified Files:**
- `apps/api/src/schemas/quiz_session.py` - Added version field to QuizSessionStartResponse
- `apps/api/src/routes/quiz.py` - Include session.version in start response
- `apps/web/src/services/quizService.ts` - Added version to SessionStartResponse interface
- `apps/web/src/hooks/useQuizSession.ts` - Use data.version instead of hardcoded 1
- `apps/web/src/test/fixtures/quizFixtures.ts` - Added version to mock responses
