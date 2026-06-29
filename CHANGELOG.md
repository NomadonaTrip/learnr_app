# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added

- **Interactive prerequisite graph (#15, Story 4.11 Slice D)** — new
  `GET /concepts/{id}/neighborhood` endpoint and a deep-linkable
  `/curriculum/graph/:conceptId` page rendering a concept's prerequisite and
  dependent neighborhood (React Flow + dagre), with KA color-coding, lock
  status, click-to-re-center, per-node practice launch, and expandable hub
  clusters for dense concepts.

- **Concept unlock notifications (Story 4.11 AC 7, #14)** — concept-unlock events are now recorded when a quiz or post-session-review belief update crosses a mastery gate (`MasteryGateService.check_and_record_unlocks` wired into `QuizAnswerService.submit_answer` and `ReviewSessionService`, defensively so recording can never fail a submission). The concepts unlocked during a session are returned inline on the session/review summary (`new_unlocks`, anchored on the session start time) and surfaced as a single aggregate toast ("🎉 You unlocked N new concepts!", click → `/curriculum`, fired once per session). A new "Recently unlocked" strip on the curriculum page (`RecentlyUnlockedStrip` + `useRecentUnlocks` over `/concepts/recent-unlocks`) lets users revisit recent unlocks; it stays invisible until there is data.

- **Performance indexes** (migration `ab01perfindexes`) — `idx_questions_difficulty_label` on `questions(course_id, difficulty_label)` (difficulty-tier selection / Story 10.1 IRT) and `idx_review_responses_question` on `review_responses(question_id)` (FK lookups/joins). Declared in both the migration and the models, so `alembic check` stays clean.

- **Course-agnostic corpus chunking pipeline** (`scripts/utils/corpus_markdown.py`, `scripts/parse_corpus.py`, `courses.corpus_config`)
  - Generic markdown parser `CorpusMarkdownParser` with caller-supplied `allowed_chapters`; KA chapters derived from `knowledge_areas[].section_prefix` (no hardcoded chapter numbers). Shared with `extract_babok_concepts.py`.
  - New nullable `courses.corpus_config` JSONB column (`chunk_chapters` {min,max} + `heading_style`); CLI `--min-chapter`/`--max-chapter` overrides. cbap configured for chapters 1–8.
  - `parse_corpus.py --replace` flag for clean, idempotent re-parsing.

- **Story 4.9: Post-Session Review Mode** - Complete implementation of post-session review functionality allowing users to review incorrect answers after completing a quiz session.
  - Backend: ReviewSession and ReviewResponse models, service, repository, and API endpoints
  - Frontend: ReviewPrompt, ReviewQuestion, ReviewSummary components with QuizPage integration
  - Belief update multipliers: 1.5x for reinforcement, 0.5x for still-incorrect
  - Comprehensive test coverage (unit, route, integration)

- **Integration tests for belief update multipliers** (`apps/api/tests/integration/test_review_session_api.py`)
  - `TestBeliefUpdateMultipliers` class verifying 1.5x and 0.5x multipliers are correctly applied

### Changed

- **Accessibility polish for curriculum lock/unlock components (#13)** — `LockedConceptConfirmDialog` now autofocuses on open with a focus trap (Escape works immediately, Tab cycles within), dismisses on backdrop click, and uses `aria-labelledby` referencing its heading; `ConceptLockBadge` uses `role="img"` so its label is reliably announced; `ConceptLockTooltip` accepts an optional `id` and `ConceptRow` wires `aria-describedby` on the Practice button so screen readers hear the blocking prerequisites.
- **Reconciled SQLAlchemy models with the live DB schema (alembic drift)** — `alembic check` now reports "No new upgrade operations detected" (was 67 spurious ops). Models now declare the DB's actual index set exactly (GIN, partial `WHERE`, composite, ordered `priority DESC`), removing the inconsistent `index=True`/`idx_*` duplicates; DB was left untouched except the one fix below. Makes future `--autogenerate` migrations trustworthy. Covers `concepts`, `concept_prerequisites`, `concept_unlock_events`, `courses`, `diagnostic_sessions`, `enrollments`, `password_reset_tokens`, `question_concepts`, `questions`, `quiz_responses`, `quiz_sessions`, `reading_chunks`, `reading_queue`, `review_responses`, `review_sessions`.

### Fixed

- **Backend test suite collection** — removed a stale duplicate `tests/unit/test_quiz_answer_service.py` whose basename collided with the maintained `tests/unit/services/test_quiz_answer_service.py`, aborting pytest collection for the entire suite (`import file mismatch`). The removed copy never ran and was outdated against the current `QuizAnswerService`. Follow-up: port its unique coverage (answer-correctness, idempotency, normalization, error-handling) into the maintained file.
- **`questions.created_at`/`updated_at` made timezone-aware** (migration `aa01questionstz`) — they were `timestamp without time zone` while every other table is tz-aware; stored values reinterpreted as UTC.
- **`quiz_responses.time_taken_ms` model type** corrected to `Float` to match the DB `DOUBLE PRECISION` column.

- **Rebuilt `reading_chunks` concept links after CBAP re-extraction (#12)** — `reading_chunks.concept_ids` referenced stale pre-re-extraction concept UUIDs (0/58 resolved). Re-ran the corpus + embedding pipeline; cbap now has 327 chunks with 0 unresolved concept references and Qdrant vectors in sync (327/327).
- **Corpus chunker producing unusable chunks** (`scripts/parse_corpus.py`) — raw-PDF (fitz) sectioning + `\n\n`-only splitter yielded 42 header-only stubs and giant blobs (one 466,987-char chunk holding ~80% of the corpus). Rewrote to chunk from heading-structured markdown with a token-budget splitter (sentence → token-window hard fallback); every chunk is now ≤ 500 tokens, and section coverage rose from ~35 to 263 sections.

- **N+1 Query in Review Summary** (`apps/api/src/services/review_session_service.py`, `apps/api/src/repositories/review_session_repository.py`)
  - Issue: `_get_still_incorrect_concepts()` made separate database queries for each incorrect response
  - Fix: Added `get_questions_with_concepts_batch()` for batch loading with eager-loaded concepts
  - Impact: Improved performance for review summary generation

- **Incorrect Reading Library URL** (`apps/api/src/services/review_session_service.py`)
  - Issue: "Study this concept" links pointed to `/reading/library?concept=...` which doesn't exist
  - Fix: Changed to `/reading-library?concept=...` to match frontend routes
  - Impact: Study links now navigate correctly from review feedback

- **Quiz Session Conflict Error** (`apps/api/src/services/quiz_session_service.py`, `apps/api/src/repositories/quiz_session_repository.py`)
  - Issue: Starting a new quiz failed with 500 error when orphaned active sessions existed due to unique constraint violation
  - Fix: Added `force_end_active_sessions()` method and try-catch with automatic recovery around session creation
  - Impact: System now self-heals from orphaned sessions instead of failing

- **Reading Queue Items Not Appearing** (`apps/api/src/repositories/reading_queue_repository.py`, `apps/api/src/services/reading_queue_service.py`)
  - Issue: Reading queue items added during quiz were not visible in the reading library
  - Root cause 1: Raw SQL insert in `add_to_queue()` didn't include `status` field (Python defaults don't apply to Core inserts)
  - Root cause 2: Transaction commit timing issue - items were flushed but not committed before request ended
  - Fix 1: Added explicit `status="unread"` to insert values
  - Fix 2: Added explicit `await self.session.commit()` in `populate_reading_queue()`
  - Impact: Reading queue items now appear immediately after submitting quiz answers

### Changed

- **Story 4.9 Status** - Updated from "Approved" to "Done"
- **Dev Agent Record** - Populated with implementation details and file list

## [Previous Releases]

See git history for changes prior to this changelog.
