# Alembic Model↔DB Drift Reconciliation — Design

**Date:** 2026-06-27
**Status:** Proposed
**Context:** Surfaced while adding `courses.corpus_config` (PR #18) — `alembic --autogenerate` emits 67 spurious operations because the SQLAlchemy models have drifted from the live `learnr_dev` schema. This makes every future autogenerate untrustworthy: a careless apply would **drop real DB indexes** (GIN/partial/composite) the models don't declare. Goal: a solid, trustworthy migration foundation before further backend work.

## Problem

`alembic check` reports 67 operations. Classified:

- **~55 index-naming**: the live DB carries the hand-written `001_initial_schema.py` index names (`idx_<table>_<col>`), while the models declare `index=True` (implying `ix_<table>_<col>`) — frequently *both* on the same column (e.g. `quiz_response.request_id`, `password_reset_token.token`). Same physical index, mismatched name → autogenerate churn.
- **DB-only indexes the models never declare** (real risk — autogenerate would DROP them): GIN on array columns (`idx_questions_competencies_gin`, `idx_questions_perspectives_gin`, `idx_reading_chunks_concepts`), partial/expression indexes (`idx_quiz_sessions_user_active_unique`, `idx_reading_queue_priority`), composite/secondary (`idx_questions_difficulty`, `idx_courses_active`).
- **Genuine bugs** (decided: fix both): `questions.created_at/updated_at` are `timestamp without time zone` while every other table is tz-aware; `quiz_responses.request_id` is `unique=True` in the model (idempotency) but the DB lacks the unique constraint.
- **Cosmetic type diff**: `quiz_responses.time_taken_ms` is `DOUBLE PRECISION` in DB vs `Integer` in model.

The app runs fine today — this is a developer-workflow/foundation hazard, not a runtime outage.

## Decisions (locked)

1. **DB is the source of truth.** The live schema has the complete, intentional index set; the models are an incomplete, inconsistent shadow. We align the *models* to the DB (no DDL for the index work), not the DB to the models.
2. **Fix the two genuine bugs** with one small, safe migration (0 dup `request_id`s confirmed; `questions` = 236 rows).
3. Assumes a single dev environment (`learnr-postgres-data-dev`); no other deployed DB needs to replay history.

## Goal / success criteria

`cd apps/api && alembic check` reports **"No new upgrade operations detected"** (modulo a documented, explicit exclusion list for any index alembic genuinely cannot round-trip — see Risks). The app boots and the backend test suite passes.

## Design

### Part A — Model index cleanup (no DDL)

For each of the 14 drifted tables (`concept_prerequisites`, `concept_unlock_events`, `concepts`, `courses`, `diagnostic_sessions`, `enrollments`, `password_reset_tokens`, `question_concepts`, `questions`, `quiz_responses`, `quiz_sessions`, `reading_chunks`, `reading_queue`, `review_sessions`), edit the model so its declared indexes **exactly match the live DB** — same name, columns, uniqueness, type, and predicate:

- Remove `index=True` on columns whose DB index uses an `idx_*` name; declare that index explicitly in `__table_args__` with the DB's exact name instead. (Eliminates the `ix_*`-vs-`idx_*` churn and the duplicate declarations.)
- Add the missing DB-only indexes to `__table_args__`:
  - GIN: `Index('idx_questions_competencies_gin', 'competencies', postgresql_using='gin')`, `idx_questions_perspectives_gin`, `idx_reading_chunks_concepts` (gin on `concept_ids`).
  - Partial unique: `idx_quiz_sessions_user_active_unique` → `Index(..., unique=True, postgresql_where=text('ended_at IS NULL'))` (verify the exact predicate against the DB).
  - Expression/ordered: `idx_reading_queue_priority` (carries a `DESC` ordering expression — verify and declare with `.desc()` / `text(...)`).
  - Plain composite/secondary: `idx_questions_difficulty`, `idx_courses_active`, etc.

This is **iterative**: edit → `alembic check` → repair the remaining diffs → repeat until clean. The DB is never modified by Part A; only model metadata.

Set the cosmetic type to match the DB: `quiz_responses.time_taken_ms` → `Float`/`Double` (matching `DOUBLE PRECISION`).

### Part B — Reconciliation migration (the two real fixes)

One new alembic migration, `down_revision = '38b668be7ca9'` (current head):

```python
def upgrade():
    # questions timestamps -> tz-aware (treat stored naive values as UTC)
    op.alter_column('questions', 'created_at', type_=sa.DateTime(timezone=True),
                    postgresql_using="created_at AT TIME ZONE 'UTC'", existing_nullable=False)
    op.alter_column('questions', 'updated_at', type_=sa.DateTime(timezone=True),
                    postgresql_using="updated_at AT TIME ZONE 'UTC'", existing_nullable=False)
    # enforce request_id idempotency at the DB (0 dups confirmed)
    op.drop_index('idx_quiz_responses_request_id', table_name='quiz_responses')  # if present
    op.create_index('idx_quiz_responses_request_id', 'quiz_responses', ['request_id'], unique=True)

def downgrade():
    op.drop_index('idx_quiz_responses_request_id', table_name='quiz_responses')
    op.create_index('idx_quiz_responses_request_id', 'quiz_responses', ['request_id'], unique=False)
    op.alter_column('questions', 'updated_at', type_=sa.TIMESTAMP(),
                    postgresql_using="updated_at AT TIME ZONE 'UTC'", existing_nullable=False)
    op.alter_column('questions', 'created_at', type_=sa.TIMESTAMP(),
                    postgresql_using="created_at AT TIME ZONE 'UTC'", existing_nullable=False)
```

(Exact index name/uniqueness reconciliation for `request_id` to be finalized against what the DB actually has — there may be both a non-unique `idx_` and an `ix_`; the migration must end with exactly one unique index that the model also declares.)

The models for `questions` (already `DateTime(timezone=True)`) and `quiz_responses.request_id` (already `unique=True`) then match the post-migration DB, contributing to a clean `alembic check`.

### Part C — env.py exclusion (only if needed)

If a partial/expression index genuinely cannot be round-tripped by autogenerate (alembic's known limitation for functional/expression indexes), add a narrowly-scoped `include_object` hook in `apps/api/.../env.py` that excludes *only* those specifically-named indexes from comparison, with a comment listing them and why. Prefer exact model declaration first; use the hook only as a last resort, and document every excluded name.

## Testing / verification

- `cd apps/api && alembic upgrade head` applies the reconciliation migration cleanly; `alembic downgrade -1` then `upgrade head` round-trips without error.
- `cd apps/api && alembic check` → "No new upgrade operations detected" (or only the documented Part C exclusions).
- App import smoke + existing backend test suite (`pytest`) pass.
- Spot-check: `questions.created_at` is `timestamp with time zone`; a duplicate `request_id` insert is rejected.

## Out of scope

- Adding/removing indexes for performance, or any query-pattern changes.
- Collapsing migration history / baseline reset.
- Non-drifted tables (`users`, `belief_states`, etc. already match).

## Risks

- **Alembic can't round-trip expression/partial indexes** → may never report fully clean for `idx_reading_queue_priority` / partial uniques. Mitigation: declare as precisely as possible; fall back to the documented `include_object` exclusion (Part C). The success criterion explicitly allows this documented residue.
- **Matching 35 indexes exactly is fiddly** → iterative `alembic check` loop is the safeguard; each step is verifiable.
- **`alter_column ... USING`** on populated `questions` (236 rows) — safe; values reinterpreted as UTC. Backup `questions` before the migration.
