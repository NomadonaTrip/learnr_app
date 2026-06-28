# Alembic Model↔DB Drift Reconciliation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `cd apps/api && alembic check` report "No new upgrade operations detected" by aligning the SQLAlchemy models to the live DB's index set (DB = source of truth) and fixing the one genuine schema bug (`questions` timestamps → tz-aware).

**Architecture:** One small migration alters `questions.created_at/updated_at` to `timestamptz`. Everything else is model-metadata cleanup (no DDL): each drifted model's index declarations are rewritten to exactly match the live DB indexes (names, columns, uniqueness, `postgresql_using='gin'`, `postgresql_where=...`), removing the inconsistent `index=True`/duplicate declarations. Functional/ordered indexes alembic cannot round-trip are excluded via a documented `include_object` hook in `env.py`.

**Tech Stack:** SQLAlchemy 2 (declarative `Column`/`Index`/`__table_args__`), Alembic, PostgreSQL, pytest.

## Global Constraints

- Run via venv: `cd /mnt/e/TOOLMAKER/PYTHON/LearnR_2/apps/api && .venv/bin/alembic …` and `.venv/bin/pytest …`.
- DB = source of truth. Do NOT add/drop/rename any DB index. The ONLY DDL in this whole plan is the `questions` timestamp `alter_column` in Task 1.
- The authoritative gate is `cd apps/api && .venv/bin/alembic check`. A table is "done" when no `Detected … on '<table>'` line mentions it.
- psql access: `docker exec -e PGPASSWORD=learnr123 learnr-postgres-dev psql -U learnr -d learnr_dev -c "…"`.
- Current alembic head (down_revision for the new migration): `38b668be7ca9`.
- Branch: `feature/alembic-reconciliation` (stacked on the chunking branch). Commit format `<type>: <description>`.
- Never use `--autogenerate` to write a migration in this plan (it emits the 67-op churn). Hand-write the one migration in Task 1.

### Index-type → SQLAlchemy translation reference (used by all model-cleanup tasks)

Match each live-DB index to a declaration that reproduces it EXACTLY. Live DDL is shown per task; translate by type:

| DB DDL pattern | Model declaration (in `__table_args__`) |
|---|---|
| `CREATE INDEX idx_x ON t USING btree (a)` | `Index('idx_x', 'a')` |
| `CREATE INDEX idx_x ON t USING btree (a, b)` | `Index('idx_x', 'a', 'b')` |
| `CREATE UNIQUE INDEX idx_x ON t USING btree (a)` | `Index('idx_x', 'a', unique=True)` |
| `… USING gin (a)` | `Index('idx_x', 'a', postgresql_using='gin')` |
| `… USING btree (a) WHERE (cond)` | `Index('idx_x', 'a', postgresql_where=sa.text("cond"))` |
| `… USING btree (a, b DESC, c)` | ordered/expression — see Task 6 (likely `include_object` exclusion) |
| `… USING btree (md5(col))` | functional — see Task 6 (`include_object` exclusion) |
| `<table>_pkey` | already the primary key — do NOT declare |
| `<col>_key` (e.g. `quiz_responses_request_id_key`) | produced by column `unique=True` — do NOT add a separate `Index` |

Rules:
- A column index named `ix_<table>_<col>` in the DB is produced by `index=True` on that column — KEEP `index=True` for those.
- A column index named `idx_…` in the DB must be declared explicitly in `__table_args__`; if the column currently has `index=True` producing an `ix_…` the DB does NOT have, REMOVE that `index=True`.
- Remove any `__table_args__` `Index(...)` whose name is NOT in the live DB.
- `import sqlalchemy as sa` (or `from sqlalchemy import text`) where `sa.text`/`text` is used.
- Partial predicates must match the DB's normalized form (e.g. `(is_active = true)` → `sa.text("is_active = true")`, `((status)::text = 'in_progress'::text)` → `sa.text("status = 'in_progress'")`). Verify with `alembic check`; if it still reports the index, copy the predicate text verbatim from `pg_indexes.indexdef`.

---

### Task 1: Reconciliation migration — `questions` timestamps → tz-aware

**Files:**
- Create: `apps/api/src/db/migrations/versions/<rev>_questions_timestamps_tz.py` (hand-written)

**Interfaces:**
- Produces: a migration with `down_revision = '38b668be7ca9'` that converts `questions.created_at`/`updated_at` to `TIMESTAMP WITH TIME ZONE`.

- [ ] **Step 1: Back up the questions table**

```bash
docker exec -e PGPASSWORD=learnr123 learnr-postgres-dev pg_dump -U learnr -d learnr_dev -t questions > "$CLAUDE_JOB_DIR/tmp/questions_backup_pre_tz.sql"
```

- [ ] **Step 2: Confirm current (naive) type**

```bash
docker exec -e PGPASSWORD=learnr123 learnr-postgres-dev psql -U learnr -d learnr_dev -t -A -c "select column_name,data_type from information_schema.columns where table_name='questions' and column_name in ('created_at','updated_at');"
```
Expected: both `timestamp without time zone`.

- [ ] **Step 3: Hand-write the migration**

Create `apps/api/src/db/migrations/versions/aa01_questions_timestamps_tz.py`:

```python
"""questions timestamps -> timezone-aware

Revision ID: aa01questionstz
Revises: 38b668be7ca9
Create Date: 2026-06-27
"""
from alembic import op
import sqlalchemy as sa

revision = "aa01questionstz"
down_revision = "38b668be7ca9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("questions", "created_at", type_=sa.DateTime(timezone=True),
                    existing_nullable=False, postgresql_using="created_at AT TIME ZONE 'UTC'")
    op.alter_column("questions", "updated_at", type_=sa.DateTime(timezone=True),
                    existing_nullable=False, postgresql_using="updated_at AT TIME ZONE 'UTC'")


def downgrade() -> None:
    op.alter_column("questions", "updated_at", type_=sa.TIMESTAMP(),
                    existing_nullable=False, postgresql_using="updated_at AT TIME ZONE 'UTC'")
    op.alter_column("questions", "created_at", type_=sa.TIMESTAMP(),
                    existing_nullable=False, postgresql_using="created_at AT TIME ZONE 'UTC'")
```

- [ ] **Step 4: Apply and verify**

```bash
cd /mnt/e/TOOLMAKER/PYTHON/LearnR_2/apps/api && .venv/bin/alembic upgrade head
docker exec -e PGPASSWORD=learnr123 learnr-postgres-dev psql -U learnr -d learnr_dev -t -A -c "select column_name,data_type from information_schema.columns where table_name='questions' and column_name in ('created_at','updated_at');"
```
Expected: both now `timestamp with time zone`.

- [ ] **Step 5: Round-trip the migration**

```bash
cd /mnt/e/TOOLMAKER/PYTHON/LearnR_2/apps/api && .venv/bin/alembic downgrade -1 && .venv/bin/alembic upgrade head
```
Expected: no errors; ends at head.

- [ ] **Step 6: Confirm the timestamp drift is gone**

```bash
cd /mnt/e/TOOLMAKER/PYTHON/LearnR_2/apps/api && .venv/bin/alembic check 2>&1 | grep -i "questions.*created_at\|questions.*updated_at" || echo "no timestamp drift"
```
Expected: `no timestamp drift`.

- [ ] **Step 7: Commit**

```bash
git add apps/api/src/db/migrations/versions/aa01_questions_timestamps_tz.py
git commit -m "feat: migrate questions timestamps to timezone-aware"
```

---

### Task 2: Model index cleanup — plain/gin/unique tables

Align these models to the live DB indexes. **No DDL.** Tables: `concept_prerequisites`, `concept_unlock_events`, `concepts`, `question_concepts`, `reading_chunks`, `review_sessions`, `password_reset_tokens`.

**Files (locate each by `grep -rl "__tablename__ = \"<table>\"" apps/api/src/models/`):**
- Modify: the model module for each table above.

**Live DB indexes to reproduce (from `pg_indexes`; `*_pkey` = primary key, do NOT declare):**
```
concept_prerequisites: idx_concept_prereqs_concept (concept_id); idx_concept_prereqs_prereq (prerequisite_concept_id)
concept_unlock_events: idx_unlock_events_unlocked_at (unlocked_at); idx_unlock_events_user (user_id); idx_unlock_events_user_concept (user_id, concept_id); uq_unlock_events_user_concept UNIQUE (user_id, concept_id)
concepts: idx_concepts_course (course_id); idx_concepts_knowledge_area (course_id, knowledge_area_id); idx_concepts_section (corpus_section_ref)
question_concepts: idx_question_concepts_concept (concept_id); idx_question_concepts_question (question_id)
reading_chunks: idx_reading_chunks_concepts GIN (concept_ids); idx_reading_chunks_course (course_id); idx_reading_chunks_knowledge_area (course_id, knowledge_area_id); idx_reading_chunks_section (corpus_section)
review_sessions: idx_review_sessions_original (original_session_id); idx_review_sessions_status (status); idx_review_sessions_user (user_id)
password_reset_tokens: idx_password_reset_tokens_expires_at (expires_at); idx_password_reset_tokens_token UNIQUE (token); idx_password_reset_tokens_user_id (user_id)
```

- [ ] **Step 1: Baseline the drift for these tables**

```bash
cd /mnt/e/TOOLMAKER/PYTHON/LearnR_2/apps/api && .venv/bin/alembic check 2>&1 | grep -iE "concept_prerequisites|concept_unlock_events|'concepts'|question_concepts|reading_chunks|review_sessions|password_reset_tokens"
```
Note the lines — these are what you must drive to zero.

- [ ] **Step 2: Edit each model to match the DB index set**

For each table: open its model, and using the translation reference in Global Constraints, make `__table_args__` declare exactly the indexes listed above (e.g. for `reading_chunks`: `Index('idx_reading_chunks_concepts', 'concept_ids', postgresql_using='gin')`, `Index('idx_reading_chunks_course', 'course_id')`, `Index('idx_reading_chunks_knowledge_area', 'course_id', 'knowledge_area_id')`, `Index('idx_reading_chunks_section', 'corpus_section')`). Remove any `index=True` whose implied `ix_*` name is not in the DB; remove any `__table_args__` `Index` whose name is not listed above. Keep `unique=True` on columns that back a `*_key` constraint. Ensure `from sqlalchemy import Index` (and `text` if needed) is imported.

- [ ] **Step 3: Drive the drift to zero for these tables (iterate)**

```bash
cd /mnt/e/TOOLMAKER/PYTHON/LearnR_2/apps/api && .venv/bin/alembic check 2>&1 | grep -iE "concept_prerequisites|concept_unlock_events|'concepts'|question_concepts|reading_chunks|review_sessions|password_reset_tokens" || echo "GROUP CLEAN"
```
Repeat Step 2 fixes until this prints `GROUP CLEAN`.

- [ ] **Step 4: Import smoke**

```bash
cd /mnt/e/TOOLMAKER/PYTHON/LearnR_2/apps/api && .venv/bin/python -c "import src.models.concept, src.models.reading_chunk, src.models.review_session, src.models.password_reset_token"
```
Expected: exits 0, no error.

- [ ] **Step 5: Commit**

```bash
git add apps/api/src/models/
git commit -m "refactor: align plain/gin model indexes to live DB (alembic drift)"
```

---

### Task 3: Model index cleanup — `quiz_responses` (type fix + redundant index removal)

**Files:**
- Modify: `apps/api/src/models/quiz_response.py`

**Live DB indexes:**
```
idx_quiz_responses_session (session_id); idx_quiz_responses_user_created (user_id, created_at);
idx_quiz_responses_user_question (user_id, question_id);
ix_quiz_responses_question_id (question_id); ix_quiz_responses_request_id (request_id);
ix_quiz_responses_session_id (session_id); ix_quiz_responses_user_id (user_id);
quiz_responses_request_id_key UNIQUE (request_id)   # from column unique=True
```

- [ ] **Step 1: Baseline**

```bash
cd /mnt/e/TOOLMAKER/PYTHON/LearnR_2/apps/api && .venv/bin/alembic check 2>&1 | grep -i quiz_responses
```

- [ ] **Step 2: Apply the three fixes**

In `quiz_response.py`:
1. Change `time_taken_ms` column type from `Integer` to `Float` (DB is `DOUBLE PRECISION`): `time_taken_ms = Column(Float, nullable=True)` (import `Float`).
2. Keep `request_id = Column(UUID(as_uuid=True), nullable=True, unique=True, index=True)` (produces `quiz_responses_request_id_key` + `ix_quiz_responses_request_id` — both in DB).
3. In `__table_args__`, REMOVE `Index("idx_quiz_responses_request_id", "request_id")` (not in DB). Keep `idx_quiz_responses_session`, `idx_quiz_responses_user_created`, `idx_quiz_responses_user_question`. Keep `index=True` on `session_id`/`user_id`/`question_id` columns (they back `ix_*` names present in DB).

- [ ] **Step 3: Drive drift to zero (iterate)**

```bash
cd /mnt/e/TOOLMAKER/PYTHON/LearnR_2/apps/api && .venv/bin/alembic check 2>&1 | grep -i quiz_responses || echo "quiz_responses CLEAN"
```
Repeat Step 2 until `quiz_responses CLEAN`.

- [ ] **Step 4: Commit**

```bash
git add apps/api/src/models/quiz_response.py
git commit -m "refactor: align quiz_responses model to live DB (time_taken_ms Float, drop redundant request_id index)"
```

---

### Task 4: Model index cleanup — partial-index tables

Tables with `WHERE` predicates. **No DDL.** Tables: `courses`, `enrollments`, `diagnostic_sessions`, `quiz_sessions`.

**Files:** model module for each of the four tables.

**Live DB indexes (partials shown with predicate):**
```
courses: idx_courses_active (is_active) WHERE (is_active = true); idx_courses_slug UNIQUE (slug)
enrollments: idx_enrollments_course (course_id); idx_enrollments_user (user_id);
  idx_enrollments_user_active (user_id, status) WHERE ((status)::text = 'active'::text);
  uq_enrollments_user_course UNIQUE (user_id, course_id)
diagnostic_sessions: idx_diagnostic_sessions_enrollment (enrollment_id); idx_diagnostic_sessions_user (user_id);
  idx_diagnostic_sessions_user_enrollment_status (user_id, enrollment_id, status);
  idx_diagnostic_sessions_active_enrollment UNIQUE (enrollment_id) WHERE ((status)::text = 'in_progress'::text);
  idx_diagnostic_sessions_stale (started_at) WHERE ((status)::text = 'in_progress'::text)
quiz_sessions: idx_quiz_sessions_enrollment (enrollment_id); idx_quiz_sessions_user (user_id);
  idx_quiz_sessions_user_active (user_id, ended_at) WHERE (ended_at IS NULL);
  idx_quiz_sessions_user_active_unique UNIQUE (user_id) WHERE (ended_at IS NULL)
```

- [ ] **Step 1: Baseline**

```bash
cd /mnt/e/TOOLMAKER/PYTHON/LearnR_2/apps/api && .venv/bin/alembic check 2>&1 | grep -iE "'courses'|enrollments|diagnostic_sessions|quiz_sessions"
```

- [ ] **Step 2: Edit each model**

Declare each partial index with `postgresql_where`, e.g.:
```python
from sqlalchemy import Index, text
# courses
Index('idx_courses_active', 'is_active', postgresql_where=text('is_active = true')),
Index('idx_courses_slug', 'slug', unique=True),
# quiz_sessions
Index('idx_quiz_sessions_user_active', 'user_id', 'ended_at', postgresql_where=text('ended_at IS NULL')),
Index('idx_quiz_sessions_user_active_unique', 'user_id', unique=True, postgresql_where=text('ended_at IS NULL')),
# enrollments / diagnostic_sessions: predicate "status = 'active'" / "status = 'in_progress'"
Index('idx_enrollments_user_active', 'user_id', 'status', postgresql_where=text("status = 'active'")),
Index('idx_diagnostic_sessions_active_enrollment', 'enrollment_id', unique=True, postgresql_where=text("status = 'in_progress'")),
Index('idx_diagnostic_sessions_stale', 'started_at', postgresql_where=text("status = 'in_progress'")),
```
Plus the plain/unique indexes per the list. Remove `index=True` that produces non-DB `ix_*` names; keep `unique=True` backing `uq_*`/`*_key`.

- [ ] **Step 3: Drive drift to zero (iterate)**

```bash
cd /mnt/e/TOOLMAKER/PYTHON/LearnR_2/apps/api && .venv/bin/alembic check 2>&1 | grep -iE "'courses'|enrollments|diagnostic_sessions|quiz_sessions" || echo "PARTIALS CLEAN"
```
If a partial index still appears, copy its predicate verbatim from `docker exec … psql -c "select indexdef from pg_indexes where indexname='<name>'"` into `postgresql_where`. Iterate until `PARTIALS CLEAN`.

- [ ] **Step 4: Commit**

```bash
git add apps/api/src/models/
git commit -m "refactor: align partial-index models (courses/enrollments/diagnostic/quiz sessions) to live DB"
```

---

### Task 5: Model index cleanup — `questions` (gin + partial) and `reading_queue`

**Files:**
- Modify: `apps/api/src/models/question.py`, `apps/api/src/models/reading_queue.py`

**Live DB indexes:**
```
questions: idx_questions_active (is_active) WHERE (is_active = true);
  idx_questions_competencies_gin GIN (competencies); idx_questions_perspectives_gin GIN (perspectives);
  idx_questions_course (course_id); idx_questions_course_ka (course_id, knowledge_area_id);
  idx_questions_difficulty (difficulty);
  idx_questions_text_hash_unique UNIQUE (md5(question_text))   # FUNCTIONAL — see Task 6
reading_queue: idx_reading_queue_enrollment (enrollment_id); idx_reading_queue_enrollment_status (enrollment_id, status);
  idx_reading_queue_user (user_id); uq_reading_queue_enrollment_chunk UNIQUE (enrollment_id, chunk_id);
  idx_reading_queue_priority (enrollment_id, priority DESC, added_at)   # ORDERED — see Task 6
```

- [ ] **Step 1: Declare everything declarable**

Add the GIN, partial, plain, and unique indexes per the reference (e.g. `Index('idx_questions_competencies_gin', 'competencies', postgresql_using='gin')`, `Index('idx_questions_active', 'is_active', postgresql_where=text('is_active = true'))`, `Index('idx_questions_course_ka', 'course_id', 'knowledge_area_id')`, etc.). For `reading_queue` declare the plain + unique ones. Do NOT yet worry about `idx_questions_text_hash_unique` or `idx_reading_queue_priority` (Task 6 decides their handling). Remove non-DB `index=True`/`Index` entries.

- [ ] **Step 2: Check residual drift for these two tables**

```bash
cd /mnt/e/TOOLMAKER/PYTHON/LearnR_2/apps/api && .venv/bin/alembic check 2>&1 | grep -iE "'questions'|reading_queue"
```
Expected residue: only `idx_questions_text_hash_unique` (functional `md5`) and `idx_reading_queue_priority` (ordered). If anything ELSE remains, fix it and re-run until only those two (or fewer) remain.

- [ ] **Step 3: Commit**

```bash
git add apps/api/src/models/question.py apps/api/src/models/reading_queue.py
git commit -m "refactor: align questions/reading_queue declarable indexes to live DB"
```

---

### Task 6: Exclude un-round-trippable indexes via `env.py`, then verify fully clean

Functional (`md5(question_text)`) and ordered (`priority DESC`) indexes cannot be reliably autogenerated/compared. Try declaring them; if they still show, exclude them explicitly.

**Files:**
- Modify: `apps/api/src/db/migrations/env.py` (locate with `find apps/api -name env.py -path "*migrations*"`)

- [ ] **Step 1: Attempt declaration first**

Try declaring them in their models:
```python
from sqlalchemy import Index, text
Index('idx_questions_text_hash_unique', text('md5(question_text)'), unique=True),  # questions
Index('idx_reading_queue_priority', 'enrollment_id', text('priority DESC'), 'added_at'),  # reading_queue
```
Then `cd apps/api && .venv/bin/alembic check 2>&1 | grep -iE "text_hash|reading_queue_priority"`. If BOTH are gone, skip to Step 3 (no env.py change). If either persists (expected for functional/ordered), proceed to Step 2.

- [ ] **Step 2: Add a documented `include_object` exclusion**

In `env.py`, define and wire an `include_object` that drops ONLY the named residual indexes from comparison, then pass it to BOTH `context.configure(...)` calls (offline and online):

```python
# Indexes alembic cannot round-trip (functional/ordered). They exist in the DB and
# are intentionally excluded from autogenerate comparison. See
# docs/superpowers/specs/2026-06-27-alembic-model-db-reconciliation-design.md
_UNCOMPARABLE_INDEXES = {"idx_questions_text_hash_unique", "idx_reading_queue_priority"}

def include_object(object_, name, type_, reflected, compare_to):
    if type_ == "index" and name in _UNCOMPARABLE_INDEXES:
        return False
    return True
```
Add `include_object=include_object` to each `context.configure(...)`. Keep the model declarations from Step 1 if they were accepted; otherwise remove the un-acceptable `text(...)` Index to avoid a phantom "add".

- [ ] **Step 3: Full clean check**

```bash
cd /mnt/e/TOOLMAKER/PYTHON/LearnR_2/apps/api && .venv/bin/alembic check
```
Expected: `No new upgrade operations detected.` (If it still lists anything, return to the relevant table's task.)

- [ ] **Step 4: Commit**

```bash
git add apps/api/src/db/migrations/env.py apps/api/src/models/question.py apps/api/src/models/reading_queue.py
git commit -m "chore: exclude functional/ordered indexes from alembic autogen comparison"
```

---

### Task 7: Final verification (round-trip + app boot + tests)

**Files:** none.

- [ ] **Step 1: Migration round-trips cleanly**

```bash
cd /mnt/e/TOOLMAKER/PYTHON/LearnR_2/apps/api && .venv/bin/alembic downgrade -1 && .venv/bin/alembic upgrade head && .venv/bin/alembic check
```
Expected: ends at head; `No new upgrade operations detected.`

- [ ] **Step 2: Models import + app boots**

```bash
cd /mnt/e/TOOLMAKER/PYTHON/LearnR_2/apps/api && .venv/bin/python -c "import src.main"
```
Expected: exits 0 (or the project's documented boot smoke).

- [ ] **Step 3: Backend test suite**

```bash
cd /mnt/e/TOOLMAKER/PYTHON/LearnR_2/apps/api && .venv/bin/pytest -q
```
Expected: pass (same pass/fail baseline as before this work — note any pre-existing failures unrelated to schema).

- [ ] **Step 4: Spot-check the real fix**

```bash
docker exec -e PGPASSWORD=learnr123 learnr-postgres-dev psql -U learnr -d learnr_dev -t -A -c "select data_type from information_schema.columns where table_name='questions' and column_name='created_at';"
```
Expected: `timestamp with time zone`.

- [ ] **Step 5: Update CHANGELOG and commit**

Add an `### Changed`/`### Fixed` entry under `[Unreleased]` in `CHANGELOG.md` noting the model↔DB index reconciliation, the `questions` tz fix, and the `env.py` exclusion. Then:
```bash
git add CHANGELOG.md
git commit -m "docs: changelog for alembic model/DB reconciliation"
```

---

## Self-Review

**Spec coverage:**
- DB-as-truth model cleanup (Part A) → Tasks 2–6. ✓
- `questions` tz migration (Part B) → Task 1. ✓
- `request_id` is model-cleanup-only (corrected) → Task 3 (remove redundant index, keep unique). ✓
- env.py exclusion for un-round-trippable (Part C) → Task 6. ✓
- `time_taken_ms` type align → Task 3. ✓
- Success = `alembic check` clean → Tasks 6/7. ✓
- Verification (round-trip, app boot, tests, spot-check) → Task 7. ✓

**Placeholder scan:** Index DDL and translations are concrete; the only deliberately deferred specifics are partial-predicate exact text and the two functional/ordered indexes, both with an explicit `alembic check`-driven resolution path (copy predicate verbatim / exclude). No vague "handle edge cases". ✓

**Type consistency:** `idx_*`/`ix_*`/`uq_*` names used match the live `pg_indexes` output; `down_revision = '38b668be7ca9'` consistent; `include_object` name set matches the two indexes named in Task 5/6. ✓
