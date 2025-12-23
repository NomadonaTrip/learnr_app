# Scripts

This directory contains utility scripts for the LearnR application.

## Import Vendor Questions

The `import_vendor_questions.py` script imports CBAP exam questions from CSV or JSON files into the PostgreSQL database.

### Usage

```bash
# Basic import from CSV file
python scripts/import_vendor_questions.py --file scripts/data/vendor_questions.csv

# Import from JSON file
python scripts/import_vendor_questions.py --file scripts/data/vendor_questions.json --format json

# Dry run (validate without inserting)
python scripts/import_vendor_questions.py --file scripts/data/vendor_questions.csv --dry-run

# Verbose logging
python scripts/import_vendor_questions.py --file scripts/data/vendor_questions.csv --verbose
```

### Command-Line Options

- `--file` (required): Path to CSV or JSON file containing questions
- `--format` (optional): File format - either `csv` or `json` (default: `csv`)
- `--dry-run` (optional): Validate questions without inserting into database
- `--verbose` (optional): Enable detailed debug logging

### Expected CSV Format

**Column Headers:**
```
question_text,option_a,option_b,option_c,option_d,correct_answer,explanation,ka,difficulty,concept_tags
```

**Example Row:**
```csv
"What is the primary purpose of stakeholder analysis?","Identify stakeholders","Document requirements","Manage risks","Allocate resources","A","Stakeholder analysis identifies all parties affected by or affecting the project","Business Analysis Planning and Monitoring","Medium","stakeholder,analysis,planning"
```

**Required Columns:**
- `question_text` - The question text (TEXT, non-empty)
- `option_a` - Answer option A (TEXT, non-empty)
- `option_b` - Answer option B (TEXT, non-empty)
- `option_c` - Answer option C (TEXT, non-empty)
- `option_d` - Answer option D (TEXT, non-empty)
- `correct_answer` - Correct answer: A, B, C, or D (case-insensitive)
- `explanation` - Explanation of the correct answer (TEXT, non-empty)
- `ka` - Knowledge Area - must be one of the 6 valid CBAP KAs (see below)

**Optional Columns:**
- `difficulty` - Difficulty level: Easy, Medium, or Hard (defaults to "Medium" if not provided)
- `concept_tags` - Comma-separated list of concept tags (e.g., "planning,stakeholder,analysis")
- `source` - Source of question (defaults to "vendor")
- `babok_reference` - BABOK chapter/section reference (optional)

### Expected JSON Format

**Array of question objects:**
```json
[
  {
    "question_text": "What is the primary purpose of stakeholder analysis?",
    "option_a": "Identify stakeholders",
    "option_b": "Document requirements",
    "option_c": "Manage risks",
    "option_d": "Allocate resources",
    "correct_answer": "A",
    "explanation": "Stakeholder analysis identifies all parties affected by or affecting the project",
    "ka": "Business Analysis Planning and Monitoring",
    "difficulty": "Medium",
    "concept_tags": "stakeholder,analysis,planning"
  }
]
```

### Valid Knowledge Areas (KAs)

All questions must belong to one of these 6 CBAP Knowledge Areas:

1. **Business Analysis Planning and Monitoring**
2. **Elicitation and Collaboration**
3. **Requirements Life Cycle Management**
4. **Strategy Analysis**
5. **Requirements Analysis and Design Definition**
6. **Solution Evaluation**

### Non-Conventional KA Mapping (Story 2.16)

The import script also supports **non-conventional KA values** from BABOK Chapters 9 and 10:

#### Perspective KAs (Chapter 10)

Questions with perspective KAs are automatically mapped to primary KAs for BKT scoring:

| Perspective KA | Primary KA | Perspective ID |
|----------------|------------|----------------|
| Agile Perspective | `strategy` | `agile` |
| Business Intelligence Perspective | `solution-eval` | `bi` |
| Business Process Management Perspective | `radd` | `bpm` |
| Information Technology Perspective | `radd` | `it` |
| Business Architecture Perspective | `strategy` | `ba` |

**Matching behavior:**
- Case-insensitive matching (e.g., "AGILE PERSPECTIVE" works)
- Partial matching supported (e.g., "Agile" or "Agile Perspective" both work)
- Leading/trailing whitespace is stripped

#### Underlying Competencies (Chapter 9)

Questions with `ka = "Underlying Competencies"` have their primary KA **inferred from concept_tags**:

| Tag Keywords | Inferred Primary KA |
|--------------|---------------------|
| elicitation, interview, workshop, collaboration, communication, facilitation | `elicitation` |
| strategy, conceptual, systems-thinking, business-acumen, industry, organization | `strategy` |
| decision, prioritiz*, approval, traceability, change, governance | `rlcm` |
| model, design, data, analysis, specification, diagram, prototype | `radd` |
| evaluation, metric, performance, assessment, measure, kpi | `solution-eval` |
| (no match) | `ba-planning` (fallback) |

**Competency IDs are extracted** from the concept_tags via TagClassifier (e.g., "Communication-Skills" → `communication` competency ID).

#### Import Behavior

When processing non-conventional KAs:

1. **Perspective questions:**
   - Primary KA is set to the configured mapping (e.g., Agile → strategy)
   - Perspective ID is added to the `perspectives` array
   - Logged at INFO level: `"Mapped non-conventional KA 'Agile Perspective' -> 'strategy'"`

2. **Competency questions:**
   - Primary KA is inferred from concept_tags keywords
   - Competency IDs are extracted from concept_tags
   - Warning logged if no concept_tags provided

3. **Secondary tags:**
   - All concept_tags are processed by TagClassifier
   - Additional perspectives/competencies from tags are appended
   - Arrays are deduplicated before storing

#### Example

CSV row:
```
"What agile practice...",A,B,C,D,A,"Explanation","Agile Perspective","Medium","Scrum-Methodology,Sprint-Planning"
```

Result:
- `knowledge_area_id`: `strategy` (mapped from Agile Perspective)
- `perspectives`: `["agile"]` (from KA + may include more from tags)
- `competencies`: `[]` (no competency keywords in tags)

### Validation Rules

The script validates each question before import:

1. **Required Fields** - All required fields must be present and non-empty
2. **Exactly 4 Options** - Questions must have exactly 4 answer options (A, B, C, D)
3. **Valid Correct Answer** - `correct_answer` must be one of: A, B, C, D (case-insensitive, normalized to uppercase)
4. **Valid Knowledge Area** - `ka` must exactly match one of the 6 valid KAs (case-sensitive)
5. **Valid Difficulty** - If provided, `difficulty` must be: Easy, Medium, or Hard. If not provided, defaults to "Medium"
6. **Concept Tags Parsing** - Comma-separated tags are parsed into a JSONB array

**Invalid questions are skipped** and reported at the end of the import process.

### Distribution Validation

The script checks that each Knowledge Area has at least **50 questions**. If any KA has fewer than 50 questions, a warning is logged, but the import continues (non-blocking).

### Transaction Rollback

The import uses **transaction-based bulk insert**:

- All questions are inserted in a single database transaction
- If any error occurs during insert, the **entire transaction is rolled back**
- This ensures **no partial imports** - either all questions are imported or none

### Logging Output

The script provides comprehensive logging:

```
INFO - Starting import from vendor_questions.csv
INFO - Parsed 500 questions from CSV
INFO - Validated 495 questions
WARNING - Validation errors: 5
WARNING -   Row 23: Invalid KA 'Business Planning'
INFO - Distribution check:
INFO -   Total questions: 495
INFO -   By Knowledge Area:
INFO -     ✓ Business Analysis Planning and Monitoring: 85 questions
INFO -     ✓ Elicitation and Collaboration: 78 questions
INFO -     ...
INFO - All KAs meet minimum 50 question threshold ✓
INFO - Successfully imported 495 questions
INFO - ============================================================
INFO - IMPORT SUMMARY
INFO - ============================================================
INFO - Total questions imported: 495
INFO -
INFO - Breakdown by Knowledge Area:
INFO -   - Business Analysis Planning and Monitoring: 85
INFO -   - Elicitation and Collaboration: 78
INFO -   ...
INFO - Breakdown by Difficulty:
INFO -   - Easy: 150
INFO -   - Medium: 220
INFO -   - Hard: 125
INFO - ============================================================
```

### Troubleshooting

#### Error: "File not found"
**Cause:** The specified file path doesn't exist
**Solution:** Check that the file path is correct and the file exists

#### Error: "Module not found"
**Cause:** Python dependencies not installed or virtual environment not activated
**Solution:**
```bash
cd apps/api
source venv/bin/activate
pip install -r requirements.txt
```

#### Error: "Invalid KA"
**Cause:** The `ka` field doesn't exactly match one of the 6 valid Knowledge Areas
**Solution:** Ensure the KA field matches exactly (case-sensitive):
- "Business Analysis Planning and Monitoring"
- "Elicitation and Collaboration"
- "Requirements Life Cycle Management"
- "Strategy Analysis"
- "Requirements Analysis and Design Definition"
- "Solution Evaluation"

#### Error: "Missing required field"
**Cause:** One or more required fields are missing or empty
**Solution:** Ensure all required fields are present and non-empty in your CSV/JSON file

#### Error: "could not translate host name"
**Cause:** Database connection error - likely pointing to wrong database
**Solution:** Check `apps/api/.env` file and ensure `DATABASE_URL` points to the local PostgreSQL:
```
DATABASE_URL=postgresql+asyncpg://learnr:learnr123@localhost:5432/learnr_dev
```

#### Warning: "KAs have fewer than 50 questions"
**Cause:** Distribution validation detected imbalanced question distribution
**Impact:** Non-blocking warning - import will continue
**Solution:** Add more questions to under-represented Knowledge Areas

### Database Schema

Questions are stored in the `questions` table with the following structure:

- `id` - UUID primary key (auto-generated)
- `question_text` - TEXT
- `option_a`, `option_b`, `option_c`, `option_d` - TEXT
- `correct_answer` - VARCHAR(1) with CHECK constraint (A/B/C/D)
- `explanation` - TEXT
- `ka` - VARCHAR(100)
- `difficulty` - VARCHAR(20) with CHECK constraint (Easy/Medium/Hard)
- `concept_tags` - JSONB array
- `source` - VARCHAR(50) (default: 'vendor')
- `babok_reference` - VARCHAR(100) (nullable)
- `times_seen` - INTEGER (default: 0)
- `avg_correct_rate` - FLOAT (default: 0.0)
- `created_at`, `updated_at` - TIMESTAMP

### Sample Data

A sample CSV file with 10 questions is provided:
```bash
scripts/data/vendor_questions_sample.csv
```

You can use this to test the import script:
```bash
python scripts/import_vendor_questions.py --file scripts/data/vendor_questions_sample.csv --dry-run
```

---

## Generate Question Embeddings

The `generate_question_embeddings.py` script generates embeddings for all questions using OpenAI's `text-embedding-3-large` model and uploads them to the Qdrant `cbap_questions` collection.

### Prerequisites

1. **PostgreSQL** - Must have questions imported (from Story 2.2)
2. **Qdrant** - Must be running with `cbap_questions` collection created (from Story 2.1)
3. **OpenAI API Key** - Must be set in environment

### Environment Variables

```bash
# Required
export OPENAI_API_KEY=sk-your-api-key-here

# Optional (defaults in config)
export QDRANT_URL=http://localhost:6333
export DATABASE_URL=postgresql+asyncpg://learnr:learnr123@localhost:5432/learnr_dev
```

### Usage

```bash
# Basic usage - generate and upload all embeddings
python scripts/generate_question_embeddings.py

# Custom batch size (default: 100)
python scripts/generate_question_embeddings.py --batch-size 50

# Dry run - validate without API calls or uploads
python scripts/generate_question_embeddings.py --dry-run

# Verbose logging
python scripts/generate_question_embeddings.py --verbose

# Verify only - check Qdrant collection count
python scripts/generate_question_embeddings.py --verify-only
```

### Command-Line Options

| Option | Default | Description |
|--------|---------|-------------|
| `--batch-size` | 100 | Number of texts per OpenAI API call (max: 100) |
| `--dry-run` | false | Validate without making API calls or uploading |
| `--verbose` | false | Enable debug logging |
| `--verify-only` | false | Only verify Qdrant collection count |

### How It Works

1. **Fetch Questions** - Retrieves all questions from PostgreSQL
2. **Format Text** - Creates embedding text: `"{question_text} {option_a} {option_b} {option_c} {option_d}"`
3. **Generate Embeddings** - Calls OpenAI API with batch processing (up to 100 per request)
4. **Upload to Qdrant** - Uploads vectors with idempotency check (skips existing)
5. **Verify** - Confirms expected 500 vectors in collection

### Embedding Text Format

Each question is formatted as a single string combining the question and all options:

```
What is the primary purpose of stakeholder analysis? Identify stakeholders Document requirements Manage risks Allocate resources
```

### Qdrant Payload Structure

Each vector is uploaded with the following payload:

```json
{
  "question_id": "uuid-string",
  "ka": "Business Analysis Planning and Monitoring",
  "difficulty": "Medium",
  "concept_tags": ["planning", "monitoring"],
  "question_text": "What is the primary purpose...",
  "options": "{\"a\": \"...\", \"b\": \"...\", \"c\": \"...\", \"d\": \"...\"}",
  "correct_answer": "A"
}
```

### Idempotency

The script is idempotent - it can be safely re-run without duplicating embeddings:

- Before uploading each vector, it checks if `question_id` already exists in Qdrant
- Existing vectors are skipped with a log message
- Only new vectors are uploaded

### Rate Limiting

The script implements exponential backoff for OpenAI rate limits:

- On 429 (Rate Limit) error, waits 1s, 2s, 4s before retrying
- Maximum 3 retries before failing
- Batching reduces total API calls (500 questions = 5 API calls)

### Expected Output

```
2024-01-01 10:00:00 - INFO - Starting embedding generation (batch_size=100, dry_run=False)
2024-01-01 10:00:00 - INFO - Step 1: Fetching questions from PostgreSQL...
2024-01-01 10:00:01 - INFO - Retrieved 500 questions from PostgreSQL
2024-01-01 10:00:01 - INFO - Step 2: Formatting embedding texts...
2024-01-01 10:00:01 - INFO - Formatted 500 embedding texts
2024-01-01 10:00:01 - INFO - Step 3: Generating embeddings with OpenAI API...
2024-01-01 10:00:05 - INFO - Embedded 100/500 questions (20%)
2024-01-01 10:00:10 - INFO - Embedded 200/500 questions (40%)
...
2024-01-01 10:00:25 - INFO - Embedded 500/500 questions (100%)
2024-01-01 10:00:25 - INFO - Step 4: Uploading vectors to Qdrant...
2024-01-01 10:00:30 - INFO - Uploaded 100/500 vectors to Qdrant (skipped 0)
...
2024-01-01 10:00:45 - INFO - Uploaded 500/500 vectors to Qdrant (skipped 0)
2024-01-01 10:00:45 - INFO - Step 5: Verifying Qdrant upload...
2024-01-01 10:00:45 - INFO - ✓ Verification passed: 500 vectors in cbap_questions collection
2024-01-01 10:00:45 - INFO - ============================================================
2024-01-01 10:00:45 - INFO - EMBEDDING GENERATION SUMMARY
2024-01-01 10:00:45 - INFO - ============================================================
2024-01-01 10:00:45 - INFO - Total questions processed: 500
2024-01-01 10:00:45 - INFO - Vectors uploaded: 500
2024-01-01 10:00:45 - INFO - Vectors skipped (already existed): 0
2024-01-01 10:00:45 - INFO - Total OpenAI tokens used: 250,000
2024-01-01 10:00:45 - INFO - Estimated OpenAI cost: $0.0325
2024-01-01 10:00:45 - INFO - Total time elapsed: 45.23s
2024-01-01 10:00:45 - INFO - Verification: PASSED ✓
2024-01-01 10:00:45 - INFO - ============================================================
```

### Cost Estimate

- **Model**: `text-embedding-3-large` (3072 dimensions)
- **Cost**: $0.13 per 1M tokens
- **500 questions × ~500 tokens each** = ~250K tokens
- **Estimated cost**: ~$0.03

### Verification

To verify the upload after running:

```bash
# Check collection count via script
python scripts/generate_question_embeddings.py --verify-only

# Or check Qdrant dashboard
# Open http://localhost:6333/dashboard
# Navigate to cbap_questions collection
```

### Troubleshooting

#### Error: "OPENAI_API_KEY environment variable not set"
**Solution:** Set the environment variable:
```bash
export OPENAI_API_KEY=sk-your-api-key-here
```

#### Error: "Rate limit hit, waiting..."
**Cause:** OpenAI API rate limit reached
**Solution:** The script automatically retries with exponential backoff. If persistent, reduce batch size:
```bash
python scripts/generate_question_embeddings.py --batch-size 50
```

#### Error: "No questions found in database"
**Cause:** Questions haven't been imported yet
**Solution:** Run the import script first:
```bash
python scripts/import_vendor_questions.py --file scripts/data/vendor_questions.csv
```

#### Error: "Connection to Qdrant failed"
**Cause:** Qdrant is not running
**Solution:** Start Qdrant via Docker:
```bash
docker-compose -f infrastructure/docker/docker-compose.dev.yml up qdrant -d
```

#### Warning: "Verification failed: Expected 500, found X"
**Cause:** Some vectors failed to upload or fewer questions in database
**Solution:**
1. Check database has 500 questions
2. Re-run script (idempotent - will only upload missing vectors)

---

## Sync Belief States

The `sync_belief_states.py` script ensures all enrolled users have belief states for all concepts in a course. This is needed when new concepts are added after users have already registered (Story 2.14).

### When to Use

Run this script after:
- Importing questions with `--create-missing-concepts` flag (Story 2.13)
- Manually adding new concepts to the database
- Any scenario where concepts exist without corresponding belief states for enrolled users

**Note:** The `import_vendor_questions.py` script will display a reminder to run this script when new concepts are created.

### Usage

```bash
# Standard sync for a course
python scripts/sync_belief_states.py --course-slug cbap

# Dry run (preview changes without writing to database)
python scripts/sync_belief_states.py --course-slug cbap --dry-run

# Verbose logging (shows per-user details)
python scripts/sync_belief_states.py --course-slug cbap --verbose
```

### Command-Line Options

| Option | Required | Description |
|--------|----------|-------------|
| `--course-slug` | Yes | Course slug (e.g., 'cbap') |
| `--dry-run` | No | Show what would happen without making changes |
| `--verbose` | No | Enable debug logging with per-user details |

### How It Works

1. **Lookup Course** - Finds the course by slug
2. **Get Concepts** - Retrieves all concept IDs for the course
3. **Get Users** - Finds all users with active enrollments in the course
4. **Sync Beliefs** - For each user, creates missing belief states using `bulk_create_from_concepts`
5. **Summary** - Reports total beliefs created and duration

### Belief Initialization

New belief states are created with:
- **Alpha:** 1.0 (uninformative prior)
- **Beta:** 1.0 (uninformative prior)
- **Initial Mastery:** 50% (Beta(1,1) mean)

This Beta(1,1) distribution represents "no prior knowledge" - the system knows nothing about the user's mastery until they answer questions.

### Idempotency

The script is **idempotent** - running it multiple times is safe:
- Uses `ON CONFLICT DO NOTHING` for database inserts
- Existing beliefs are never modified
- Second run will report 0 beliefs created

### Performance

Target: **1000 users × 50 concepts in <30 seconds**

The script uses batch inserts for efficiency rather than individual INSERT statements.

### Expected Output

```
2024-01-15 10:00:00 - INFO - Looking up course: cbap
2024-01-15 10:00:00 - INFO - Found course: CBAP Certification Prep (ID: uuid...)
2024-01-15 10:00:00 - INFO - Found 150 concepts for course
2024-01-15 10:00:00 - INFO - Found 500 enrolled users to sync
2024-01-15 10:00:01 - INFO - Progress: 100/500 users processed, 2500 beliefs created, 1523ms elapsed
2024-01-15 10:00:02 - INFO - Progress: 200/500 users processed, 5000 beliefs created, 3045ms elapsed
...
2024-01-15 10:00:05 - INFO - ============================================================
2024-01-15 10:00:05 - INFO - BELIEF STATE SYNC SUMMARY
2024-01-15 10:00:05 - INFO - ============================================================
2024-01-15 10:00:05 - INFO - Mode: LIVE
2024-01-15 10:00:05 - INFO - Course ID: uuid...
2024-01-15 10:00:05 - INFO - Total concepts: 150
2024-01-15 10:00:05 - INFO - Total enrolled users: 500
2024-01-15 10:00:05 - INFO - Users synced: 500
2024-01-15 10:00:05 - INFO - Beliefs created: 12500
2024-01-15 10:00:05 - INFO - Errors: 0
2024-01-15 10:00:05 - INFO - Duration: 5234ms (5.23s)
2024-01-15 10:00:05 - INFO - ============================================================
```

### Dry Run Output

In dry-run mode, the script counts what would be created without writing:

```
2024-01-15 10:00:00 - INFO - DRY RUN - No database changes will be made
...
2024-01-15 10:00:05 - INFO - Mode: DRY RUN
2024-01-15 10:00:05 - INFO - Beliefs created: 12500 (would be created)
```

### Troubleshooting

#### Error: "Course not found: cbap"
**Cause:** Invalid course slug or course doesn't exist
**Solution:** Check available courses in the database:
```sql
SELECT slug, name FROM courses WHERE is_active = true;
```

#### Error: "No enrolled users found"
**Cause:** No users have active enrollments for this course
**Solution:** This is normal for a new course - beliefs will be created when users enroll

#### Error: "No concepts found for course"
**Cause:** Course has no concepts defined
**Solution:** Import concepts first using the concept import workflow

### Lazy Initialization Alternative

In addition to batch sync, the system also supports **lazy initialization** (Story 2.14):

When a user answers a question involving concepts they don't have beliefs for:
1. `BeliefUpdater.update_beliefs()` detects missing belief states
2. Creates them on-the-fly with Beta(1,1) prior
3. Immediately updates them based on the answer

This means:
- **Batch sync** proactively creates beliefs for all users
- **Lazy init** creates beliefs on-demand during quiz flow
- Both approaches are complementary and safe to use together

---

## Backfill Secondary Tags

The `backfill_secondary_tags.py` script populates `perspectives` and `competencies` arrays for existing questions based on their linked concept names (Story 2.15).

### When to Use

Run this script after:
- Adding perspectives/competencies configuration to a course
- Importing questions that were created before secondary tagging was implemented
- Updating keyword mappings in the course configuration

### Usage

```bash
# Preview changes (dry run)
python scripts/backfill_secondary_tags.py --course-slug cbap --dry-run --verbose

# Apply changes
python scripts/backfill_secondary_tags.py --course-slug cbap

# With verbose logging
python scripts/backfill_secondary_tags.py --course-slug cbap --verbose
```

### Command-Line Options

| Option | Required | Description |
|--------|----------|-------------|
| `--course-slug` | Yes | Course slug (e.g., 'cbap') |
| `--dry-run` | No | Preview changes without modifying database |
| `--verbose` | No | Enable detailed logging with per-question output |

### How It Works

1. **Load Course** - Retrieves course with perspectives/competencies JSONB config
2. **Initialize TagClassifier** - Builds keyword sets from course configuration
3. **Load Questions** - Fetches all questions with their linked concepts
4. **Classify Concepts** - Runs concept names through TagClassifier to derive secondary tags
5. **Update Questions** - Populates perspectives/competencies arrays
6. **Summary** - Reports total questions updated and tags assigned

### Secondary Tag Classification

The TagClassifier uses keyword matching to categorize concept names:

| Category | Example Keywords | Result |
|----------|-----------------|--------|
| Perspective | agile, scrum, bi, analytics, it, software, bpm | Tag ID added to `perspectives` |
| Competency | analytical, communication, leadership | Tag ID added to `competencies` |
| Concept | All other tags | Kept as concept mappings |

### Course Configuration

Secondary tags are defined in the course's JSONB columns:

```json
// perspectives column
[
  {"id": "agile", "name": "Agile", "keywords": ["agile", "scrum", "kanban"]},
  {"id": "bi", "name": "Business Intelligence", "keywords": ["bi", "analytics"]}
]

// competencies column
[
  {"id": "analytical", "name": "Analytical Thinking", "keywords": ["analytical", "problem-solving"]},
  {"id": "communication", "name": "Communication Skills", "keywords": ["communication", "verbal"]}
]
```

### Expected Output

```
2024-01-15 10:00:00 - INFO - Starting secondary tag backfill for course: cbap
2024-01-15 10:00:00 - INFO - Loaded course: CBAP Certification Prep
2024-01-15 10:00:00 - INFO - TagClassifier initialized with 25 competency keywords, 18 perspective keywords
2024-01-15 10:00:00 - INFO - Loaded 500 questions to process
2024-01-15 10:00:01 - INFO - Applying 350 updates...
2024-01-15 10:00:02 - INFO - Updates committed to database
2024-01-15 10:00:02 - INFO - ============================================================
2024-01-15 10:00:02 - INFO - BACKFILL SUMMARY
2024-01-15 10:00:02 - INFO - ============================================================
2024-01-15 10:00:02 - INFO - Course: cbap
2024-01-15 10:00:02 - INFO - Questions processed: 500
2024-01-15 10:00:02 - INFO - Questions updated: 350
2024-01-15 10:00:02 - INFO - Perspectives assigned: 420
2024-01-15 10:00:02 - INFO - Competencies assigned: 380
2024-01-15 10:00:02 - INFO - ============================================================
```

### Idempotency

The script is **idempotent** - running it multiple times is safe:
- Compares current values with computed values
- Only updates questions where values differ
- Second run on unchanged data will report 0 updates

### Troubleshooting

#### Error: "Course not found: cbap"
**Cause:** Invalid course slug
**Solution:** Check available courses in the database

#### Warning: "Course has no perspectives or competencies configured"
**Cause:** The course's perspectives/competencies columns are NULL
**Solution:** Ensure the course has secondary tags configured via migration or admin

#### Low update count
**Cause:** Questions may not have linked concepts, or concepts don't match keywords
**Solution:**
1. Check that questions have concept mappings
2. Verify keyword coverage in course configuration
3. Use `--verbose` to see per-question classification results
