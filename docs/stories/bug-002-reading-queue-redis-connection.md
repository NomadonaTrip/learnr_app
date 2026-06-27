# Bug Report: BUG-002 - Reading Queue Not Populating (Redis Connection Refused)

## Status

**RESOLVED** - Celery/Redis connection fixed; tasks dispatching and executing successfully

## Summary

The reading queue is not being populated when users answer questions incorrectly. The Celery background task that populates the reading queue cannot connect to Redis, resulting in empty reading libraries despite incorrect quiz answers.

## Severity

**High** - Core feature broken; Reading Library feature (Epic 5 differentiator) is non-functional

## Environment

- Component: Backend (FastAPI + Celery)
- Service: `quiz_answer_service.py` → `reading_queue_tasks.py`
- Infrastructure: Redis (Celery broker)

## Error Log Evidence

```
2025-12-26 14:37:15 [warning  ] reading_queue_dispatch_failed
    error=[Errno 111] Connection refused
    question_id=5c609c8e-e5f5-41ee-8761-4006963911d6
    session_id=c950c98c-ad4c-4bfb-b190-357954108b7f
```

## Root Cause

**`[Errno 111] Connection refused`** indicates Redis is not running or not accessible.

The Celery task dispatch in `quiz_answer_service.py` (lines 326-345) attempts to call:
```python
add_reading_to_queue.delay(
    str(user_id),
    str(session.enrollment_id),
    str(question_id),
    str(session_id),
    is_correct,
    question.difficulty,
)
```

This fails because Celery cannot connect to its Redis broker, configured in `celery_app.py`:
```python
celery_app = Celery(
    "learnr",
    broker=settings.REDIS_URL,  # Redis connection failing here
    backend=settings.REDIS_URL,
    ...
)
```

## Impact

1. **Reading queue never gets populated** - Users complete quizzes but their Reading Library remains empty
2. **Silent failure** - The error is logged as a warning but doesn't block quiz functionality
3. **Feature appears broken** - Users see "Your reading library is empty" despite incorrect answers

## Steps to Reproduce

1. Ensure Redis is NOT running
2. Start the FastAPI backend
3. Log in and complete a quiz session with incorrect answers
4. Navigate to Reading Library
5. Observe empty state: "Your reading library is empty"
6. Check API logs for `reading_queue_dispatch_failed` warning

## Expected Behavior

1. Redis should be running and accessible
2. Celery worker should be running to process tasks
3. Incorrect answers should trigger reading queue population
4. Reading Library should show recommended materials

## Resolution Steps

### 1. Start Redis

```bash
# Using Docker
docker run -d --name redis -p 6379:6379 redis:7.2-alpine

# Or using docker-compose
cd infrastructure/docker
docker-compose -f docker-compose.dev.yml up -d redis
```

### 2. Verify Redis is Running

```bash
redis-cli ping
# Expected output: PONG
```

### 3. Start Celery Worker

```bash
cd apps/api
celery -A src.celery_app worker --loglevel=info
```

### 4. Verify Configuration

Check `apps/api/.env` or environment variables:
```
REDIS_URL=redis://localhost:6379/0
```

## Additional Requirements

For the reading queue to fully function, the following must also be verified:

| Requirement | Check Command | Expected |
|-------------|---------------|----------|
| Redis running | `redis-cli ping` | `PONG` |
| Celery worker running | Check process list | Worker consuming tasks |
| Qdrant running | `curl http://localhost:6333/health` | `{"status":"ok"}` |
| Qdrant seeded with chunks | Check `reading_chunks` collection | Has documents |

## Affected Components

| Component | File | Role |
|-----------|------|------|
| Quiz Answer Service | `apps/api/src/services/quiz_answer_service.py` | Dispatches Celery task |
| Celery Task | `apps/api/src/tasks/reading_queue_tasks.py` | Executes queue population |
| Celery App | `apps/api/src/celery_app.py` | Celery configuration |
| Reading Queue Service | `apps/api/src/services/reading_queue_service.py` | Business logic for queue |

## Acceptance Criteria for Resolution

- [ ] Redis is running and accessible on configured URL
- [ ] Celery worker is running and consuming tasks
- [ ] `reading_queue_dispatch_failed` warnings no longer appear in logs
- [ ] Incorrect quiz answers result in reading queue items being created
- [ ] Reading Library page displays recommended materials after quiz completion

## Documentation Update Needed

Consider adding to developer setup documentation:
1. Redis startup instructions
2. Celery worker startup instructions
3. Qdrant seeding instructions for reading chunks

## Related Issues

- BUG-001: Navigation to Reading Library (UI access issue)
- Story 5.5: Background Reading Queue Population (implementation story)

## Reporter

Quinn (Test Architect) - QA Review

## Date Reported

2025-12-26

## Resolution

**Resolved on 2025-12-26**

### Code Fix Applied

Added broker connection retry settings to `apps/api/src/celery_app.py`:

```python
celery_app.conf.update(
    # Broker connection settings (critical for Celery 6.x+)
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=3,
    broker_connection_timeout=10,
    # ... other settings
)
```

### Infrastructure Status (Verified)

| Service | Status | Verification |
|---------|--------|--------------|
| Redis | Running | `docker exec learnr-redis-dev redis-cli -a learnr123 ping` → `PONG` |
| Qdrant | Running | `curl http://localhost:6333/` → `{"title":"qdrant","version":"1.7.3"}` |
| PostgreSQL | Running | `docker ps` shows healthy |

### How Services Were Started

```bash
cd /mnt/e/TOOLMAKER/PYTHON/LearnR_2
docker-compose -f infrastructure/docker/docker-compose.dev.yml up -d redis qdrant
```

### Required Steps to Complete Resolution

#### Step 1: Restart the API

The API must be restarted for the Celery configuration changes to take effect:

```bash
# Stop the current API (Ctrl+C in the terminal running uvicorn)
# Then restart:
cd apps/api
.venv/bin/uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

#### Step 2: Start Celery Worker

The Celery worker must be started for background tasks to process:

```bash
cd apps/api
.venv/bin/celery -A src.celery_app worker --loglevel=info
```

The worker will output:
```
[config]
.> app:         learnr:0x...
.> transport:   redis://:***@localhost:6379/0
.> results:     redis://:***@localhost:6379/0

[tasks]
  . src.tasks.reading_queue_tasks.add_reading_to_queue
  . src.tasks.session_cleanup.expire_stale_diagnostic_sessions_task
```

### Verification

After completing both steps:
1. Answer a quiz question incorrectly
2. Check API logs - should see `reading_queue_populated` instead of `reading_queue_dispatch_failed`
3. Navigate to Reading Library - should show recommended materials

## Change Log

| Date | Description | Author |
|------|-------------|--------|
| 2025-12-26 | Bug report created from API log analysis | Quinn (Test Architect) |
| 2025-12-26 | Infrastructure started; Celery worker instructions provided | Developer |
| 2025-12-26 | Added broker connection retry settings to celery_app.py | Developer |
| 2025-12-26 | **FIXED**: Changed REDIS_URL from `localhost` to `127.0.0.1` for WSL2/Docker Desktop compatibility | Developer |
| 2025-12-26 | Verified: Tasks now dispatching and executing successfully (reading_queue_task_completed) | Developer |

## Additional Notes

### Issue 1: Redis Connection (FIXED)
Changed `REDIS_URL` from `localhost` to `127.0.0.1` for WSL2/Docker Desktop compatibility.

### Issue 2: Async Event Loop in Celery (FIXED)
Celery fork workers were reusing database connections across different event loops, causing "attached to a different loop" errors. Fixed by creating a fresh database engine for each task in `reading_queue_service.py:populate_reading_queue_async()`.

### Issue 3: No Chunks Found (FIXED)
Sample reading chunks were seeded with incorrect `course_id` and `knowledge_area_id` format. Re-seeded with correct values matching the actual course data.

### Verification
- Reading queue tasks now dispatch and execute successfully
- Chunks are added to the queue when knowledge_area_id matches seeded content
- Reading Library page displays recommended materials
