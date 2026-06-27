# Epic 2: Content Foundation, Knowledge Graph & Question Bank (BKT-First)

**Epic Goal:** Build the content processing pipeline with a concept-centric knowledge graph that enables Bayesian Knowledge Tracing. This epic delivers:
- BABOK corpus parsed into discrete, testable concepts (~500-1500 concepts)
- Concept prerequisite graph (DAG) for structured learning paths
- Question bank with question-to-concept mappings
- Vector embeddings for semantic retrieval
- Content retrieval APIs

**Key Difference from Original:** The fundamental unit is the **concept**, not the knowledge area. Questions test concepts, and the BKT engine tracks belief states per concept.

**Architecture Reference:** See `docs/architecture/bkt-architecture.md` for full Bayesian Knowledge Tracing design.

---

## Story 2.1: Qdrant Vector Database Setup

*Unchanged from original Epic 2.1*

As a **backend developer**,
I want to set up Qdrant locally via Docker and create collections for questions and reading content,
so that semantic search and content retrieval can function.

**Acceptance Criteria:**
1. Qdrant Docker container running locally (docker-compose.yml or standalone docker run command)
2. Qdrant accessible at `localhost:6333` with REST API and gRPC
3. Two collections created:
   - `cbap_questions`: Vector size 1536 (text-embedding-3-large), distance metric: Cosine
   - `babok_chunks`: Vector size 1536, distance metric: Cosine
4. Collection schemas include metadata fields (payload):
   - Questions: `question_id`, `ka`, `difficulty`, `concept_ids`, `question_text`, `options`, `correct_answer`
   - BABOK chunks: `chunk_id`, `ka`, `section_ref`, `difficulty`, `concept_ids`, `text_content`
5. Qdrant Python client installed and configured in backend
6. Connection test: Backend can create, read, update, delete (CRUD) vectors in both collections
7. Environment variable `QDRANT_URL` configurable (default: `http://localhost:6333`)
8. README documents Qdrant setup commands and how to verify collections exist
9. Qdrant data persisted to local volume (survives container restart)
10. Health check extended to verify Qdrant connectivity

---

## Story 2.2: BABOK v3 Concept Extraction (NEW - CRITICAL)

As a **knowledge engineer**,
I want to extract discrete, testable concepts from BABOK v3,
so that the BKT engine can track mastery at the concept level.

**Acceptance Criteria:**

1. Python script `/scripts/extract_babok_concepts.py` parses BABOK v3 PDF
2. Extract concepts using hybrid approach:
   - **Structural extraction:** Each numbered section (e.g., 3.2.1) represents one or more concepts
   - **Semantic extraction:** Within sections, identify distinct testable knowledge units
   - **NLP assistance:** Use GPT-4 to identify concept boundaries and names
3. Concept schema in PostgreSQL `concepts` table:
   ```
   - id (UUID, PK)
   - name (VARCHAR 255) - e.g., "Stakeholder Identification"
   - description (TEXT) - 1-2 sentence definition
   - babok_section_ref (VARCHAR 50) - e.g., "3.2.1"
   - knowledge_area_id (FK) - link to 6 KAs for aggregation
   - difficulty_estimate (FLOAT 0.0-1.0) - based on section depth/complexity
   - prerequisite_depth (INT) - distance from root concepts (0 = foundational)
   - parent_concept_id (FK, nullable) - for hierarchical organization
   - created_at, updated_at
   ```
4. Target: 500-1500 concepts extracted (granular enough for BKT, not too granular)
5. Distribution: Each KA has 75-250 concepts (balanced coverage)
6. Concept naming convention: Clear, specific, testable (e.g., "RACI Matrix Construction" not "RACI")
7. Human review checkpoint: Export concepts to CSV for SME validation before proceeding
8. Script logs: Total concepts extracted, breakdown by KA, section coverage percentage
9. Validation: 95%+ of BABOK sections have at least one concept mapped
10. Concepts stored in PostgreSQL with proper indexing

**Technical Notes:**
- Use GPT-4 with structured output for concept identification
- Prompt template: "Given this BABOK section, identify distinct testable concepts. Each concept should represent a single piece of knowledge that can be assessed with a quiz question."
- Chunk sections to fit context window
- Deduplicate concepts that appear in multiple sections

---

## Story 2.3: Concept Prerequisite Graph Construction (NEW - CRITICAL)

As a **knowledge engineer**,
I want to define prerequisite relationships between concepts,
so that the BKT engine can prioritize foundational knowledge.

**Acceptance Criteria:**

1. PostgreSQL `concept_prerequisites` table schema:
   ```
   - id (UUID, PK)
   - concept_id (FK to concepts)
   - prerequisite_concept_id (FK to concepts)
   - strength (FLOAT 0.0-1.0) - how strongly required (1.0 = must know first)
   - relationship_type (ENUM: 'required', 'helpful', 'related')
   - created_at
   - UNIQUE(concept_id, prerequisite_concept_id)
   - CHECK(concept_id != prerequisite_concept_id) - no self-loops
   ```
2. Python script `/scripts/build_prerequisite_graph.py`:
   - **Automatic inference:** Use BABOK section hierarchy (parent sections are prerequisites)
   - **Semantic inference:** Use embeddings to find related concepts
   - **GPT-4 assistance:** For complex cross-KA prerequisites
3. DAG validation: No cycles in prerequisite graph (topological sort must succeed)
4. Graph statistics:
   - Average prerequisites per concept: 2-5
   - Maximum prerequisite depth: 10 levels
   - Orphan concepts (no prerequisites): Only foundational concepts
5. Export graph to visualization format (GraphML, JSON) for review
6. Human review checkpoint: Subject matter expert validates critical paths
7. `prerequisite_depth` computed for each concept (BFS from roots)
8. API endpoint: GET `/api/v1/concepts/{id}/prerequisites` returns prerequisite chain
9. Integration: BKT question selection uses prerequisite depth for prioritization
10. Performance: Graph queries execute in <50ms

**Technical Notes:**
- Store as adjacency list in PostgreSQL
- Cache full graph in memory for BKT engine (refresh on startup)
- Use NetworkX for graph operations in Python

---

## Story 2.4: Vendor Question Import with Concept Mapping (REVISED)

As a **content manager**,
I want to import vendor CBAP questions and map them to concepts,
so that questions can update belief states for specific concepts.

**Acceptance Criteria:**

1. Questions table schema in PostgreSQL (revised):
   ```
   - id (UUID, PK)
   - question_text (TEXT)
   - option_a, option_b, option_c, option_d (TEXT)
   - correct_answer (CHAR 1) - A/B/C/D
   - explanation (TEXT)
   - knowledge_area_id (FK) - for backward compatibility/display
   - difficulty (FLOAT 0.0-1.0) - IRT difficulty parameter
   - discrimination (FLOAT, default 1.0) - IRT discrimination parameter
   - guess_rate (FLOAT, default 0.25) - P(correct | not mastered)
   - slip_rate (FLOAT, default 0.10) - P(incorrect | mastered)
   - source (VARCHAR) - vendor identifier
   - times_asked (INT, default 0) - for calibration
   - times_correct (INT, default 0) - for calibration
   - created_at, updated_at
   ```
2. Question-concept junction table `question_concepts`:
   ```
   - question_id (FK)
   - concept_id (FK)
   - relevance (FLOAT 0.0-1.0) - how directly question tests concept
   - PRIMARY KEY (question_id, concept_id)
   ```
3. Python script `/scripts/import_vendor_questions.py`:
   - Read questions from CSV/JSON
   - Validate: Required fields, exactly 4 options, correct_answer is A/B/C/D
   - **Concept mapping:** Use GPT-4 + semantic search to map each question to 1-5 concepts
   - Insert questions and concept mappings
4. Concept mapping process:
   - Generate question embedding
   - Find top-10 most similar concepts by embedding
   - Use GPT-4 to select 1-5 most relevant concepts from candidates
   - Assign relevance scores (1.0 = directly tests, 0.5 = indirectly related)
5. Validation:
   - Each question maps to at least 1 concept
   - Each concept has at least 3 questions (for BKT to work)
   - Concepts with <3 questions flagged for content creation
6. Target: 500-1000 questions imported
7. Distribution: Balanced across concepts (not just KAs)
8. Rollback mechanism if import fails
9. Script logs: Questions imported, concept coverage, unmapped questions
10. Human review: Export question-concept mappings for SME validation

**Technical Notes:**
- Batch GPT-4 calls for efficiency
- Use structured output for concept selection
- Store mapping confidence for later calibration

---

## Story 2.5: Question Embedding Generation and Qdrant Upload (REVISED)

As a **backend developer**,
I want to generate embeddings for all questions with concept metadata,
so that semantic search can retrieve questions by concept similarity.

**Acceptance Criteria:**

1. Python script `/scripts/generate_question_embeddings.py` reads questions with concept mappings
2. Embedding text includes concepts: `"{question_text} {options} Concepts: {concept_names}"`
3. Call OpenAI API `text-embedding-3-large` for 1536-dimension embeddings
4. Batch API calls (up to 100 questions per request)
5. Upload to Qdrant `cbap_questions` collection with payload:
   - `question_id`, `ka`, `difficulty`, `discrimination`
   - `concept_ids` (array of UUIDs)
   - `concept_names` (array for display)
   - `question_text`, `options`, `correct_answer`
6. Handle API rate limits with exponential backoff
7. Verification: All questions have embeddings, concept_ids populated
8. Script is idempotent
9. Logs: Progress every 50 questions, final count
10. Performance: Full embedding generation in <30 minutes for 1000 questions

---

## Story 2.6: BABOK Parsing and Chunking with Concept Links (REVISED)

As a **content processor**,
I want to parse BABOK v3 and link chunks to concepts,
so that reading content can be retrieved for specific concept gaps.

**Acceptance Criteria:**

1. Python script `/scripts/parse_babok.py` reads BABOK v3 PDF
2. Extract text preserving structure (headings, paragraphs)
3. Chunk using hybrid strategy:
   - Structural: Respect section boundaries
   - Semantic: 200-500 tokens per chunk
4. Chunks table schema (revised):
   ```
   - id (UUID, PK)
   - text_content (TEXT)
   - knowledge_area_id (FK)
   - section_ref (VARCHAR 50) - e.g., "3.2.1"
   - difficulty (FLOAT 0.0-1.0)
   - chunk_index (INT) - order within section
   - created_at
   ```
5. Chunk-concept junction table `chunk_concepts`:
   ```
   - chunk_id (FK)
   - concept_id (FK)
   - relevance (FLOAT 0.0-1.0)
   - PRIMARY KEY (chunk_id, concept_id)
   ```
6. **Concept linking:** Map chunks to concepts based on section_ref match
7. Target: 200-500 chunks with concept mappings
8. Validation: Each chunk maps to at least 1 concept
9. Distribution: Each KA has 20+ chunks
10. Logs: Chunks created, concept coverage

---

## Story 2.7: BABOK Chunk Embedding with Concept Metadata (REVISED)

As a **backend developer**,
I want to generate embeddings for BABOK chunks with concept links,
so that reading retrieval considers concept relationships.

**Acceptance Criteria:**

1. Script `/scripts/generate_babok_embeddings.py` reads chunks with concept mappings
2. Embedding text includes concepts: `"{text_content} Concepts: {concept_names}"`
3. Upload to Qdrant `babok_chunks` collection with payload:
   - `chunk_id`, `ka`, `section_ref`, `difficulty`
   - `concept_ids` (array of UUIDs)
   - `concept_names` (array for display)
   - `text_content`
4. All chunks embedded with concept_ids populated
5. Idempotent script with progress logging
6. Verification: Query returns chunks with concept metadata

---

## Story 2.8: Content Retrieval API - Questions by Concept (REVISED)

As a **backend developer**,
I want an API to retrieve questions filtered by concept,
so that the BKT engine can select questions for specific concepts.

**Acceptance Criteria:**

1. GET `/api/v1/questions` endpoint accepts:
   - `concept_ids` (array) - filter by concepts
   - `ka` (optional) - knowledge area filter
   - `difficulty_min`, `difficulty_max` (optional) - IRT difficulty range
   - `exclude_ids` (array) - questions to exclude (recently asked)
   - `limit` (default 10)
2. Query joins questions with question_concepts
3. Return question objects with concept_ids array
4. Response excludes `correct_answer` and `explanation` (revealed after answer)
5. Pagination metadata included
6. Requires authentication
7. Performance: <100ms for filtered queries
8. Unit tests: Filter by concept, by KA, by difficulty range
9. Integration test: Returns questions for specific concept

---

## Story 2.9: Content Retrieval API - Reading by Concept (NEW)

As a **backend developer**,
I want an API to retrieve BABOK chunks for specific concepts,
so that users can study content related to their gaps.

**Acceptance Criteria:**

1. GET `/api/v1/reading` endpoint accepts:
   - `concept_ids` (array) - find chunks for these concepts
   - `ka` (optional) - knowledge area filter
   - `limit` (default 5)
2. Returns chunks that cover the specified concepts
3. Ranked by relevance to requested concepts
4. Response includes concept_ids for each chunk
5. Requires authentication
6. Performance: <200ms
7. Fallback: If no chunks for concept, use semantic search with concept name as query

---

## Story 2.10: Concept API Endpoints (NEW - Internal Tooling)

As a **backend developer**,
I want API endpoints for concept data,
so that internal tools and the adaptive engine can access concept metadata.

> **Note:** These APIs are for system-internal use (adaptive engine, admin tools, debugging). Users see KA-level aggregation only. Concept-level drill-down is a post-MVP optional feature.

**Acceptance Criteria:**

1. GET `/api/v1/concepts` - List all concepts
   - Query params: `ka` (filter), `search` (name search), `limit`, `offset`
   - Returns: id, name, description, babok_section_ref, knowledge_area, prerequisite_depth
2. GET `/api/v1/concepts/{id}` - Get single concept
   - Returns: Full concept details
3. GET `/api/v1/concepts/{id}/prerequisites` - Get prerequisite chain
   - Returns: Array of prerequisite concepts (ordered by depth)
4. GET `/api/v1/concepts/{id}/questions` - Get questions for concept
   - Returns: Question count, sample questions
5. GET `/api/v1/concepts/stats` - Corpus statistics
   - Returns: Total concepts, by KA, by depth, coverage metrics
6. All endpoints require authentication
7. Performance: <100ms per endpoint
8. Caching: Concept list cached for 1 hour (concepts rarely change)

---

## Story 2.11: Knowledge Graph Visualization Data (NEW - POST-MVP)

> **Priority: Post-MVP** - This is a power-user feature. Users see KA-level progress (6 bars) in MVP. Knowledge graph visualization is optional enhancement.

As a **frontend developer**,
I want an API endpoint that returns the knowledge graph structure,
so that power users can optionally visualize concept relationships.

**Acceptance Criteria:**

1. GET `/api/v1/knowledge-graph` endpoint returns:
   - `nodes`: Array of concepts with id, name, ka, depth, x/y positions (pre-computed layout)
   - `edges`: Array of prerequisite relationships with source, target, strength
   - `stats`: Node count, edge count, max depth
2. Query params:
   - `ka` (optional) - filter to single knowledge area subgraph
   - `depth` (optional) - limit depth from root
   - `center_concept_id` (optional) - return neighborhood around concept
3. Response optimized for D3.js / force-directed graph rendering
4. Pre-compute layout on server (don't make client compute)
5. Cache full graph, invalidate on concept changes
6. Performance: <500ms for full graph, <100ms for filtered

---

## Story 2.12: Concept Coverage Validation Script (NEW)

As a **content manager**,
I want a validation script that checks concept coverage,
so that we can identify gaps before launch.

**Acceptance Criteria:**

1. Python script `/scripts/validate_concept_coverage.py` runs full validation:
   - Every concept has ≥3 questions (minimum for BKT)
   - Every concept has ≥1 BABOK chunk for reading
   - No orphan concepts (connected to graph)
   - No cycles in prerequisite graph
   - Question difficulty distribution per concept
2. Output: Detailed report with:
   - Concepts lacking questions (priority: create content)
   - Concepts lacking reading content
   - Distribution statistics
   - Graph health metrics
3. Exit codes: 0 = pass, 1 = warnings, 2 = failures
4. Integrate into CI/CD pipeline
5. Generate CSV of gaps for content team

---

## Story 2.13: Pre-Tagged Concept Import from CSV (NEW)

As a **content manager**,
I want to import questions with pre-tagged concepts from CSV files and have them automatically mapped to existing concepts,
so that I can efficiently import vendor questions without requiring GPT-4 processing when concept mappings are already known.

**Acceptance Criteria:**

1. Parse `concept_tags` column from CSV with support for both `,` and `;` delimiters
2. Add `concept_tags` field to `QuestionData` dataclass
3. Implement `--use-csv-tags` CLI flag that uses pre-tagged concepts instead of GPT-4 mapping
4. Fuzzy match tags to existing concepts using thefuzz with configurable threshold (default 85%)
5. Assign relevance scores based on match quality:
   - Exact match (100%): relevance = 1.0
   - High match (95-99%): relevance = 0.9
   - Good match (85-94%): relevance = 0.8
6. Handle unmatched tags with configurable behavior:
   - `--create-missing-concepts`: Create new concepts for unmatched tags
   - Default: Log warning and skip unmatched tags
7. Export unmatched tags report to CSV for SME review
8. Backward compatible: existing GPT-4 mapping workflow unchanged
9. Unit tests for tag parsing and fuzzy matching
10. Performance: Tag matching <1s per 100 questions

**Technical Notes:**
- Extends `scripts/import_vendor_questions.py`
- Uses thefuzz library (already in project for concept deduplication)
- Validates matched concepts belong to correct knowledge area

**Full Story:** See `docs/stories/2.13-pre-tagged-concept-import.story.md`

---

## Story 2.14: Belief State Sync for New Concepts (NEW)

As a **system administrator**,
I want belief states to be automatically created for existing users when new concepts are added,
so that the BKT engine can track mastery for all concepts, including those added after user registration.

**Acceptance Criteria:**

1. Lazy initialization in BeliefUpdater: When encountering a concept without a belief state, create one with uninformative prior Beta(1,1) before updating
2. Batch sync script: `scripts/sync_belief_states.py` to sync all users with all concepts
3. Sync on concept creation: When `--create-missing-concepts` is used in Story 2.13, trigger belief sync
4. Uninformative prior: New belief states use Beta(1,1) = Uniform[0,1]
5. Idempotent sync: Running multiple times has no effect on existing beliefs
6. Performance: Sync 1000 users × 50 concepts in <30 seconds
7. Logging: Log count of beliefs created per user, total sync duration

**Technical Notes:**
- Adds lazy initialization to `BeliefUpdater.update_beliefs()`
- Adds `scripts/sync_belief_states.py` for batch operations
- Uses existing `BeliefRepository.bulk_create_from_concepts()`

**Full Story:** See `docs/stories/2.14-belief-state-sync-for-new-concepts.story.md`

---

## Story 2.15: Secondary Tagging for Perspectives and Underlying Competencies (NEW)

As a **content manager**,
I want questions to be tagged with course-specific Perspectives and Underlying Competencies as secondary dimensions,
so that users can filter questions by these cross-cutting concerns and gain insights into their competency gaps without disrupting the primary KA-based BKT scoring.

**Acceptance Criteria:**

1. Add `perspectives` and `competencies` JSONB columns to `courses` table (course-specific definitions with keywords)
2. Add `perspectives` and `competencies` ARRAY columns to `questions` table
3. During import, classify each tag from `concept_tags` as Concept, Competency, or Perspective
4. TagClassifier loads keyword lists from course configuration (not hardcoded)
5. Seed CBAP course with BABOK perspectives (Agile, BI, IT, BPM) and competencies (Chapter 9)
6. Modify import script to classify and route tags using course-specific keywords
7. Existing concept tag matching continues to work unchanged
8. Add optional `perspectives` and `competencies` query parameters to question retrieval endpoints
9. Create backfill script to re-process existing questions (derives from concept names)
10. Tags are normalized (lowercase, hyphenated) before classification
11. Multi-course scalable: Each course defines its own perspectives/competencies

**Technical Notes:**
- Course-configurable keywords stored in JSONB (same pattern as `knowledge_areas`)
- Extends `scripts/import_vendor_questions.py` with `TagClassifier` class that loads from course config
- Uses PostgreSQL array containment operator (`@>`) for filtering
- BKT scoring unchanged - these are secondary dimensions for filtering only
- Other courses (PSM1, CFA) can define their own cross-cutting dimensions

**Full Story:** See `docs/stories/2.15-secondary-tagging-perspectives-competencies.story.md`

---

## Dependencies

```
Epic 2 Story Dependencies:

2.1 (Qdrant Setup) → 2.5, 2.7 (Embeddings need Qdrant)
2.2 (Concept Extraction) → 2.3, 2.4 (Concepts needed for prerequisites and question mapping)
2.3 (Prerequisites) → 2.10, 2.11 (Graph APIs need prerequisites)
2.4 (Question Import) → 2.5, 2.8 (Questions needed for embeddings and API)
2.6 (BABOK Parsing) → 2.7, 2.9 (Chunks needed for embeddings and API)
2.2, 2.3, 2.4, 2.6 → 2.12 (Validation needs all content)
2.2, 2.4 → 2.13 (Pre-tagged import needs concepts and base import script)
2.13 → 2.14 (Belief sync needed when creating new concepts)
4.4 → 2.14 (Belief sync extends BeliefUpdater from Story 4.4)
2.13 → 2.15 (Secondary tagging extends tag parsing from Story 2.13)
2.4 → 2.15 (Secondary tagging extends base import script)

Critical Path: 2.1 → 2.2 → 2.3 → 2.4 → 2.5 → 2.8
Alternative Import Path: 2.2 → 2.4 → 2.13 → 2.14 (for pre-tagged questions with new concepts)
Secondary Tagging Path: 2.4 → 2.13 → 2.15 (for perspective/competency tagging)
```

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Total concepts extracted | 500-1500 |
| Concepts per KA | 75-250 (balanced) |
| Questions per concept (min) | 3 |
| Average questions per concept | 5-10 |
| Prerequisite graph depth | ≤10 levels |
| Concepts with reading content | 100% |
| Validation script pass | 0 errors |

---

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-11-27 | 2.0 | Redesigned for BKT-first architecture; Added concept extraction (2.2), prerequisite graph (2.3); Revised question import for concept mapping (2.4); Added concept APIs (2.10, 2.11); Added validation (2.12) | Sarah (Product Owner) |
| 2025-12-18 | 2.1 | Added Story 2.13: Pre-Tagged Concept Import from CSV - enables importing questions with pre-existing concept tags without GPT-4 processing | PM Agent |
| 2025-12-18 | 2.2 | Added Story 2.14: Belief State Sync for New Concepts - ensures existing users get belief states when new concepts are added | PM Agent |
| 2025-12-19 | 2.3 | Added Story 2.15: Secondary Tagging for Perspectives and Underlying Competencies - enables filtering questions by BABOK cross-cutting dimensions | PO Agent |
