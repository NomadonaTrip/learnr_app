# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added

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

### Fixed

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
