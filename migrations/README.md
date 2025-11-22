# LearnR Platform Database Migrations

This directory contains Alembic database migrations for the LearnR Platform.

## Overview

**Migration Structure:**
- `001_initial_schema.py` - Base tables (users, courses, questions, reading_content, competency, onboarding)
- `002_v2_1_features.py` - v2.1 features (session management, reviews, reading library, admin tools, feedback)

**Total Tables:** 23 tables
- **Base (Migration 001):** 10 tables
- **v2.1 (Migration 002):** 11 new tables + 1 updated table (user_responses)

---

## Prerequisites

```bash
# Install Alembic and dependencies
pip install alembic psycopg2-binary sqlalchemy

# PostgreSQL 15+ required
# Ensure pg_crypto extension available (for UUID generation)
```

---

## Setup Alembic (First Time Only)

### 1. Initialize Alembic

```bash
# From project root
cd learnr-backend
alembic init alembic
```

This creates:
```
learnr-backend/
├── alembic/
│   ├── env.py           # Alembic environment
│   ├── script.py.mako   # Migration template
│   └── versions/        # Migration files (empty initially)
├── alembic.ini          # Alembic configuration
```

### 2. Configure Alembic

**Edit `alembic.ini`:**

```ini
# Set database URL (use environment variable for security)
sqlalchemy.url = postgresql+asyncpg://user:password@localhost:5432/learnr

# Or use environment variable:
# sqlalchemy.url =

# Prepend sys.path for project imports (uncomment if needed)
# prepend_sys_path = .
```

**Edit `alembic/env.py`:**

```python
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Import your models' MetaData (when using declarative models)
# from app.models import Base
# target_metadata = Base.metadata

# For now, we'll use manual migrations (no auto-generation)
target_metadata = None

# Get database URL from environment or config
config = context.config
if not config.get_main_option("sqlalchemy.url"):
    config.set_main_option(
        "sqlalchemy.url",
        os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/learnr")
    )

# Logging setup
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (SQL output only)"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (execute against DB)"""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### 3. Copy Migration Files

```bash
# Copy migration files to alembic/versions/
cp migrations/versions/001_initial_schema.py alembic/versions/
cp migrations/versions/002_v2_1_features.py alembic/versions/
```

---

## Running Migrations

### Check Current Database Version

```bash
alembic current
```

### View Migration History

```bash
alembic history --verbose
```

### Upgrade Database

```bash
# Upgrade to latest version
alembic upgrade head

# Upgrade one version at a time
alembic upgrade +1

# Upgrade to specific version
alembic upgrade 001  # Base schema only
alembic upgrade 002  # Base + v2.1 features
```

### Downgrade Database

```bash
# Downgrade one version
alembic downgrade -1

# Downgrade to specific version
alembic downgrade 001  # Remove v2.1 features, keep base
alembic downgrade base  # Remove all tables (⚠️ DESTRUCTIVE)
```

### Generate SQL (Offline Mode)

```bash
# Generate SQL without executing
alembic upgrade head --sql > migration.sql
```

---

## Typical Workflow

### Development Environment Setup

```bash
# 1. Start PostgreSQL (Docker)
docker run -d \
  --name learnr-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=learnr \
  -p 5432:5432 \
  postgres:15

# 2. Wait for PostgreSQL to be ready
sleep 5

# 3. Run migrations
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/learnr"
alembic upgrade head

# 4. Verify tables created
psql -h localhost -U postgres -d learnr -c "\dt"
```

### Production Deployment

```bash
# 1. Set production DATABASE_URL
export DATABASE_URL="postgresql+asyncpg://user:password@prod-host:5432/learnr"

# 2. Backup database before migration
pg_dump -h prod-host -U user learnr > backup_$(date +%Y%m%d_%H%M%S).sql

# 3. Run migration (with rollback plan ready)
alembic upgrade head

# 4. Verify migration success
alembic current
psql $DATABASE_URL -c "SELECT COUNT(*) FROM quiz_sessions;"  # Should work if v2.1 applied

# If issues, rollback:
# alembic downgrade -1
# psql $DATABASE_URL < backup_YYYYMMDD_HHMMSS.sql
```

---

## Migration Details

### Migration 001: Initial Schema

**Creates 10 Tables:**

| Table | Purpose |
|-------|---------|
| `users` | User accounts and authentication |
| `courses` | Certification courses (CBAP MVP) |
| `knowledge_areas` | KA domains per course (4 KAs for CBAP) |
| `questions` | Multiple choice questions with embeddings |
| `reading_content` | BABOK content chunks with embeddings |
| `user_responses` | User question answers (base version) |
| `user_competency` | Current competency scores per KA |
| `concept_mastery` | Spaced repetition tracking (SM-2) |
| `user_onboarding` | 7-question onboarding data |
| `subscriptions` | Future subscription tiers |

**Run Time:** ~5-10 seconds
**Indexes Created:** 18

---

### Migration 002: v2.1 Features

**Creates 11 New Tables:**

| Table | Purpose | PRD Reference |
|-------|---------|---------------|
| `competency_history` | Weekly competency snapshots | Epic 6, Story 6.2 |
| `password_reset_tokens` | Password reset flow | Epic 1, Story 1.5 |
| `quiz_sessions` | Session lifecycle (start/pause/end) | Epic 4, Story 4.1 |
| `session_reviews` | Post-session review state | Epic 4, Stories 4.6-4.9 |
| `review_attempts` | Review answer attempts | Epic 4, Story 4.7 |
| `reading_queue` | Async reading library queue | Epic 5, Stories 5.5-5.9 |
| `reading_bookmarks` | User-bookmarked materials | Front-end spec Screen 7 |
| `reading_engagement` | Reading analytics tracking | Epic 5, Story 5.3 |
| `explanation_feedback` | Explanation thumbs up/down | Epic 4, Story 4.5 |
| `reading_feedback` | Reading relevance feedback | Epic 5, Story 5.4 |
| `admin_audit_log` | Admin action audit trail | Epic 8, Story 8.7 |

**Updates 1 Table:**
- `user_responses` → Adds `session_id` FK (links answers to sessions)

**Run Time:** ~10-15 seconds
**Indexes Created:** 42
**Foreign Keys:** 28

---

## Troubleshooting

### "relation already exists" Error

```bash
# Check what's in your database
psql $DATABASE_URL -c "\dt"

# If tables partially exist, determine state
alembic current

# Option 1: Drop all tables and start fresh (⚠️ DESTRUCTIVE)
psql $DATABASE_URL -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
alembic upgrade head

# Option 2: Manually stamp version (if tables match migration)
alembic stamp 001  # Or 002 if all v2.1 tables exist
```

### "Cannot add foreign key constraint" Error

**Cause:** Table creation order issue (FK points to non-existent table)

**Solution:** Migration 002 creates tables in dependency order:
1. `quiz_sessions` (no dependencies on new tables)
2. `user_responses` update (depends on quiz_sessions)
3. `session_reviews` (depends on quiz_sessions)
4. `review_attempts` (depends on session_reviews)
5. `reading_queue` (depends on quiz_sessions)
6. `reading_engagement`, `reading_bookmarks` (depend on reading_queue)
7. `explanation_feedback`, `reading_feedback` (depend on quiz_sessions, reading_queue)

If error persists, run migrations one at a time.

### UUID Generation Not Working

```sql
-- Enable pg_crypto extension (required for gen_random_uuid())
psql $DATABASE_URL -c "CREATE EXTENSION IF NOT EXISTS pgcrypto;"
```

### Slow Migration Performance

```bash
# Disable indexes during initial load, create after
# Edit migration to comment out index creation temporarily
# Load data
# Uncomment indexes and re-run: alembic upgrade head
```

---

## Testing Migrations

### Test Upgrade/Downgrade Cycle

```bash
# Start fresh
docker run -d --name test-postgres -e POSTGRES_PASSWORD=test -e POSTGRES_DB=test -p 5433:5432 postgres:15
export TEST_DB="postgresql+asyncpg://postgres:test@localhost:5433/test"

# Test upgrade
alembic -x dbUrl=$TEST_DB upgrade head
psql $TEST_DB -c "\dt"  # Verify 23 tables

# Test downgrade to 001
alembic -x dbUrl=$TEST_DB downgrade 001
psql $TEST_DB -c "\dt"  # Verify 10 tables (v2.1 removed)

# Test downgrade to base
alembic -x dbUrl=$TEST_DB downgrade base
psql $TEST_DB -c "\dt"  # Should be empty

# Cleanup
docker stop test-postgres && docker rm test-postgres
```

### Validate Schema Against Architecture

```bash
# After migration, verify table structure
psql $DATABASE_URL -c "\d+ quiz_sessions"
psql $DATABASE_URL -c "\d+ reading_queue"

# Check foreign keys created
psql $DATABASE_URL -c "
  SELECT
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name
  FROM information_schema.table_constraints AS tc
  JOIN information_schema.key_column_usage AS kcu ON tc.constraint_name = kcu.constraint_name
  JOIN information_schema.constraint_column_usage AS ccu ON ccu.constraint_name = tc.constraint_name
  WHERE tc.constraint_type = 'FOREIGN KEY'
  ORDER BY tc.table_name;
"
```

---

## Next Steps

1. **Seed Development Data:**
   ```bash
   python scripts/seed_database.py  # Create sample users, questions, KAs
   ```

2. **Verify Vector Integration:**
   ```bash
   # Start Qdrant
   docker run -d --name qdrant -p 6333:6333 qdrant/qdrant:v1.7.4

   # Create collections
   python scripts/setup_qdrant.py
   ```

3. **Run Backend:**
   ```bash
   uvicorn app.main:app --reload --port 8000
   # Test API docs: http://localhost:8000/docs
   ```

---

## Migration File Reference

**Location:** `migrations/versions/`

```
migrations/
├── README.md                      # This file
└── versions/
    ├── 001_initial_schema.py      # Base tables (10 tables)
    └── 002_v2_1_features.py       # v2.1 features (11 tables + 1 update)
```

**Generated by:** Winston - Holistic System Architect
**Architecture Version:** v2.1 (PRD-Aligned)
**Last Updated:** 2025-11-20
**BMAD Method:** Solution Architecture Workflow v1.3
