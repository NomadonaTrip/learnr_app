# Epic 2: Content Foundation & Question Bank

**Epic Goal:** Build the content processing pipeline to load, parse, embed, and serve all CBAP questions and BABOK v3 reading content. This epic delivers 600-1,000 questions with metadata, BABOK chunks with embeddings, Qdrant vector database setup, and functional content retrieval APIs that can be tested independently before integrating with user-facing features.

## Story 2.1: Qdrant Vector Database Setup

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
   - Questions: `question_id`, `ka`, `difficulty`, `concept_tags`, `question_text`, `options`, `correct_answer`
   - BABOK chunks: `chunk_id`, `ka`, `section_ref`, `difficulty`, `concept_tags`, `text_content`
5. Qdrant Python client installed and configured in backend
6. Connection test: Backend can create, read, update, delete (CRUD) vectors in both collections
7. Environment variable `QDRANT_URL` configurable (default: `http://localhost:6333`)
8. README documents Qdrant setup commands and how to verify collections exist
9. Qdrant data persisted to local volume (survives container restart)
10. Health check extended to verify Qdrant connectivity

## Story 2.2: Vendor Question Import and Metadata Enrichment

As a **content manager**,
I want to import 500 vendor CBAP questions with metadata into PostgreSQL and Qdrant,
so that the platform has a high-quality question foundation.

**Acceptance Criteria:**
1. Questions table schema in PostgreSQL:
   - `questions` (id, question_text, option_a, option_b, option_c, option_d, correct_answer, explanation, ka, difficulty, concept_tags JSONB, source VARCHAR, created_at)
2. Python script `/scripts/import_vendor_questions.py` reads vendor questions from CSV/JSON
3. Script validates each question: Required fields present, exactly 4 options, correct_answer is A/B/C/D, KA is one of 6 valid KAs
4. Difficulty labels assigned by expert or default to "Medium" if not provided
5. Concept tags extracted or manually assigned (JSONB array in PostgreSQL)
6. Questions inserted into PostgreSQL `questions` table (500 total)
7. Distribution validation: Each KA has at least 50 questions, balanced across difficulty levels
8. Script logs summary: Total questions imported, breakdown by KA and difficulty
9. Rollback mechanism if import fails mid-process (transaction-based insert or idempotent script)
10. README documents how to run import script and expected CSV/JSON format

## Story 2.3: Question Embedding Generation and Qdrant Upload

As a **backend developer**,
I want to generate embeddings for all questions and upload to Qdrant,
so that semantic search can retrieve relevant questions.

**Acceptance Criteria:**
1. Python script `/scripts/generate_question_embeddings.py` reads all questions from PostgreSQL
2. For each question, create embedding text: `"{question_text} {option_a} {option_b} {option_c} {option_d}"`
3. Call OpenAI API `text-embedding-3-large` to generate 1536-dimension embedding vector
4. Batch API calls (up to 100 questions per request for efficiency)
5. Upload each question embedding to Qdrant `cbap_questions` collection with payload (question_id, ka, difficulty, concept_tags, question_text, options, correct_answer)
6. Script tracks progress (log every 50 questions embedded and uploaded)
7. Handle API rate limits: Retry with exponential backoff on 429 errors
8. Total embeddings: 500 vendor questions embedded
9. Verification: Query Qdrant collection, confirm 500 vectors exist
10. Script is idempotent (can re-run without duplicating embeddings, check if question_id already exists)

## Story 2.4: BABOK v3 Parsing and Chunking

As a **content processor**,
I want to parse BABOK v3 PDF and chunk it into semantic segments,
so that targeted reading content can be retrieved for user gaps.

**Acceptance Criteria:**
1. Python script `/scripts/parse_babok.py` reads BABOK v3 PDF (path from environment variable or argument)
2. Extract text using PyMuPDF or pdfplumber (preserve structure: headings, paragraphs)
3. Identify 6 KA sections in BABOK (Business Analysis Planning, Elicitation, Requirements, Solution Evaluation, etc.)
4. Chunk text using hybrid strategy:
   - Structural chunking: Respect section/subsection boundaries (don't break mid-concept)
   - Semantic chunking: Target 200-500 tokens per chunk using LangChain RecursiveCharacterTextSplitter
5. Each chunk assigned metadata: KA, section_ref (e.g., "3.2.1 Stakeholder Analysis"), difficulty (Easy/Medium/Hard based on section complexity or default Medium), concept_tags (extracted keywords or manually assigned)
6. Chunks saved to PostgreSQL `babok_chunks` table (chunk_id, ka, section_ref, difficulty, concept_tags JSONB, text_content TEXT)
7. Validation: Total chunks approximately 200-500 (depends on BABOK length, aim for comprehensive coverage)
8. Distribution: Each KA has at least 20 chunks
9. Script logs summary: Total chunks created, breakdown by KA
10. README documents BABOK parsing script usage and expected output

## Story 2.5: BABOK Chunk Embedding Generation and Qdrant Upload

As a **backend developer**,
I want to generate embeddings for all BABOK chunks and upload to Qdrant,
so that semantic retrieval can find relevant reading content for user gaps.

**Acceptance Criteria:**
1. Python script `/scripts/generate_babok_embeddings.py` reads all chunks from PostgreSQL `babok_chunks` table
2. For each chunk, use `text_content` as embedding input
3. Call OpenAI API `text-embedding-3-large` to generate 1536-dimension embedding
4. Batch API calls (up to 100 chunks per request)
5. Upload each chunk embedding to Qdrant `babok_chunks` collection with payload (chunk_id, ka, section_ref, difficulty, concept_tags, text_content)
6. Script tracks progress (log every 50 chunks embedded and uploaded)
7. Handle API rate limits: Retry with exponential backoff on 429 errors
8. Total embeddings: All BABOK chunks embedded (200-500 vectors)
9. Verification: Query Qdrant collection, confirm all chunks exist
10. Script is idempotent (check if chunk_id already exists before uploading)

## Story 2.6: Content Retrieval API - Questions

As a **backend developer**,
I want an API endpoint to retrieve questions by filters (KA, difficulty, concept),
so that the quiz engine can select appropriate questions.

**Acceptance Criteria:**
1. GET `/api/content/questions` endpoint accepts query parameters: `ka`, `difficulty`, `concept_tags`, `limit` (default 10)
2. Query PostgreSQL `questions` table filtered by provided parameters
3. If `concept_tags` provided: Filter using JSONB containment (`concept_tags @> '{tag}'`)
4. Return JSON array of question objects (id, question_text, options, ka, difficulty, concept_tags, but NOT correct_answer or explanation - those come after answer submission)
5. Response includes pagination metadata: `total_count`, `page`, `limit`
6. Endpoint requires authentication (`@require_auth` middleware)
7. Unit tests: Filter by KA, filter by difficulty, filter by concept_tags, no filters (returns all up to limit)
8. Integration test: API returns questions matching filters
9. Performance: Query executes in <100ms for up to 1000 questions
10. API documentation updated in `/docs` with parameter descriptions and example responses

## Story 2.7: Content Retrieval API - BABOK Chunks

As a **backend developer**,
I want an API endpoint to retrieve BABOK chunks via semantic search,
so that targeted reading content can be presented to users.

**Acceptance Criteria:**
1. POST `/api/content/reading` endpoint accepts JSON body: `query_text` (user's knowledge gap description), `ka` (optional filter), `limit` (default 3)
2. Generate embedding for `query_text` using OpenAI `text-embedding-3-large`
3. Query Qdrant `babok_chunks` collection with vector search (cosine similarity)
4. Apply filters: If `ka` provided, filter results to that KA only
5. Return top `limit` chunks ranked by similarity score
6. Response: JSON array of chunk objects (chunk_id, ka, section_ref, text_content, similarity_score)
7. Endpoint requires authentication
8. Unit tests: Search returns relevant chunks, KA filter works, limit parameter works
9. Integration test: Semantic search finds BABOK content related to query (e.g., "stakeholder analysis" retrieves relevant section)
10. Performance: Vector search executes in <500ms including embedding generation
