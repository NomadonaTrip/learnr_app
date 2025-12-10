# LearnR Backend API

FastAPI-based backend API for LearnR adaptive learning platform.

## Tech Stack

- **Framework:** FastAPI 0.109.x
- **Language:** Python 3.11+
- **Database:** PostgreSQL 15.x with SQLAlchemy 2.0.x ORM
- **Cache:** Redis 7.2.x
- **Vector DB:** Qdrant 1.7.x
- **AI/ML:** OpenAI GPT-4 + text-embedding-3-large
- **Background Jobs:** Celery 5.3.x
- **Testing:** pytest 7.4.x + httpx 0.26.x
- **Linting:** Ruff 0.1.x

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 15+ (or use Docker Compose)
- Redis 7.2+ (or use Docker Compose)
- OpenAI API key (for AI features)
- Qdrant instance (cloud or local)

### Installation

1. Create a virtual environment:
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install test dependencies:
   ```bash
   pip install -r requirements-test.txt
   ```

### Configuration

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Update environment variables with your actual values:
   - `DATABASE_URL` - PostgreSQL connection string
   - `REDIS_URL` - Redis connection string
   - `OPENAI_API_KEY` - Your OpenAI API key
   - `QDRANT_URL` and `QDRANT_API_KEY` - Qdrant configuration
   - `SECRET_KEY` - Generate with: `openssl rand -hex 32`

### Development

Start the development server:

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Or from the monorepo root:

```bash
npm run dev:backend
```

The API will be available at:
- **API:** `http://localhost:8000`
- **Interactive Docs (Swagger):** `http://localhost:8000/docs`
- **Alternative Docs (ReDoc):** `http://localhost:8000/redoc`

### Available Scripts

- `uvicorn src.main:app --reload` - Start dev server with hot reload
- `pytest` - Run all tests
- `pytest --cov=src` - Run tests with coverage
- `pytest -v` - Run tests with verbose output
- `ruff check src/` - Lint code
- `ruff format src/` - Format code
- `alembic upgrade head` - Run database migrations
- `alembic revision --autogenerate -m "message"` - Create new migration

## Qdrant Vector Database Setup

Qdrant is used for semantic search of questions and BABOK reading content. The API requires Qdrant to be running and properly configured.

### Starting Qdrant Locally

Start Qdrant using Docker Compose:

```bash
docker-compose -f infrastructure/docker/docker-compose.dev.yml up -d qdrant
```

Verify Qdrant is running:

```bash
curl http://localhost:6333/
```

Expected response:
```json
{"title":"qdrant - vector search engine","version":"1.7.3"}
```

### Accessing Qdrant Web UI

Once Qdrant is running, access the web dashboard at:

```
http://localhost:6333/dashboard
```

The dashboard allows you to:
- Browse collections
- View collection schemas and statistics
- Search vectors manually
- Monitor performance

### Initializing Collections

Before using the API, initialize the required Qdrant collections:

```bash
python apps/api/scripts/init_qdrant_collections.py
```

This script creates two collections with multi-course support:
- **`questions`** - Exam questions with embeddings (3072 dimensions, course-agnostic)
- **`reading_chunks`** - Reading content chunks with embeddings (3072 dimensions, course-agnostic)

**Payload Schema (Multi-Course):**

| Collection | Fields |
|------------|--------|
| `questions` | `question_id`, `course_id`, `knowledge_area_id`, `difficulty` (float), `concept_ids`, `question_text`, `options`, `correct_answer` |
| `reading_chunks` | `chunk_id`, `course_id`, `knowledge_area_id`, `section_ref`, `difficulty` (float), `concept_ids`, `text_content` |

The script is idempotent - safe to run multiple times. It also handles migration from old collection names (`cbap_questions`, `babok_chunks`).

### Verifying Collections

**Via Web UI:**
1. Open http://localhost:6333/dashboard
2. Click "Collections" in the sidebar
3. Verify `questions` and `reading_chunks` are listed

**Via API:**
```bash
curl http://localhost:6333/collections
```

**Via Health Check:**
```bash
curl http://localhost:8000/health
```

Look for the `qdrant` section in the response:
```json
{
  "qdrant": {
    "status": "connected",
    "response_time_ms": 10,
    "collections_count": 2,
    "collections": ["questions", "reading_chunks"]
  }
}
```

### Qdrant Configuration

Qdrant connection is configured in `.env`:

```bash
# Local Qdrant (default for development)
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=  # Leave empty for local
QDRANT_TIMEOUT=10

# Qdrant Cloud (production)
# QDRANT_URL=https://your-cluster.cloud.qdrant.io:6333
# QDRANT_API_KEY=your-api-key-here
```

### Troubleshooting Qdrant

**"Connection refused" errors:**
- Verify Qdrant container is running: `docker ps | grep qdrant`
- Check logs: `docker logs learnr-qdrant-dev`
- Restart Qdrant: `docker-compose -f infrastructure/docker/docker-compose.dev.yml restart qdrant`

**Collections not found:**
- Run initialization script: `python apps/api/scripts/init_qdrant_collections.py`
- Verify script completed successfully (check output)
- Verify collections in web UI or via API

**Health check shows Qdrant disconnected:**
- Check QDRANT_URL in `.env` matches running instance
- Verify no firewall blocking port 6333
- Try accessing web UI manually: `http://localhost:6333/dashboard`

**Vector dimension mismatch errors:**
- LearnR uses `text-embedding-3-large` with **3072 dimensions**
- Do NOT use `text-embedding-3-small` (1536 dimensions)
- Collections are configured for 3072 dimensions only

**Data persistence issues:**
- Qdrant data is persisted in Docker volume `learnr-qdrant-data-dev`
- View volumes: `docker volume ls | grep qdrant`
- Delete volume (⚠️ destroys all data): `docker volume rm learnr-qdrant-data-dev`

**Performance issues:**
- Check Docker resource limits (CPU, Memory)
- Qdrant recommends 2GB+ RAM for production
- Monitor dashboard for collection stats
- Consider indexing optimization for large datasets

## Project Structure

```
apps/api/
├── src/
│   ├── main.py              # Application entry point
│   ├── config.py            # Settings and configuration
│   ├── dependencies.py      # Dependency injection
│   ├── routes/              # API route handlers
│   ├── services/            # Business logic layer
│   ├── repositories/        # Data access layer
│   ├── models/              # SQLAlchemy ORM models
│   ├── schemas/             # Pydantic request/response schemas
│   ├── middleware/          # Custom middleware
│   ├── tasks/               # Celery background tasks
│   ├── utils/               # Utility functions
│   └── db/                  # Database configuration
│       ├── session.py       # Database session management
│       ├── migrations/      # Alembic migrations
│       └── qdrant_client.py # Qdrant vector DB client
├── tests/
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   ├── fixtures/           # Test fixtures
│   └── mocks/              # Mock objects
├── requirements.txt        # Production dependencies
├── requirements-test.txt   # Test dependencies
├── pyproject.toml          # Project metadata and tool config
├── pytest.ini              # Pytest configuration
└── .env.example            # Environment variables template
```

## Coding Standards

See [../../docs/architecture/coding-standards.md](../../docs/architecture/coding-standards.md) for detailed standards.

### Key Conventions

- **Functions/Methods:** snake_case (e.g., `get_user_by_id()`)
- **Classes:** PascalCase (e.g., `UserRepository`)
- **Constants:** UPPER_SNAKE_CASE (e.g., `MAX_QUESTIONS`)
- **Database tables:** snake_case (e.g., `user_profiles`)
- **Never write raw SQL** - use SQLAlchemy ORM exclusively
- **All database operations must use async/await** - no callbacks
- **Type hints required** - use Pydantic for validation

## Database Migrations

LearnR uses Alembic for database schema version control. Migrations are located in `src/db/migrations/versions/`.

### Common Migration Commands

**Create a new migration** (autogenerate from model changes):
```bash
alembic revision --autogenerate -m "Add user table"
```

**Create an empty migration** (for manual SQL):
```bash
alembic revision -m "Add custom index"
```

**Apply all pending migrations**:
```bash
alembic upgrade head
```

**Rollback one migration**:
```bash
alembic downgrade -1
```

**Rollback to specific version**:
```bash
alembic downgrade <revision_id>
```

**Rollback all migrations**:
```bash
alembic downgrade base
```

**Show current migration version**:
```bash
alembic current
```

**Show migration history**:
```bash
alembic history --verbose
```

**Preview SQL without applying**:
```bash
alembic upgrade head --sql
```

### Migration Workflow

1. **Make changes** to SQLAlchemy models in `src/models/`
2. **Generate migration**: `alembic revision --autogenerate -m "Description"`
3. **Review** generated migration file in `src/db/migrations/versions/`
4. **Verify** migration logic and add manual changes if needed
5. **Test** migration: `alembic upgrade head`
6. **Verify** database schema: Connect to database and inspect tables
7. **Commit** migration file to version control

### Troubleshooting

**"Can't locate revision identified by 'xyz'"**
- Solution: Delete the alembic_version table and run `alembic stamp head`

**Migration doesn't detect model changes**
- Ensure model is imported in `src/db/migrations/env.py`
- Check that model inherits from `Base`

**Connection refused errors**
- Verify PostgreSQL is running: `docker ps | grep postgres`
- Check DATABASE_URL in `.env` matches your database credentials

## Database Backup and Restore

### Development Environment

**Create a backup** (Docker Compose PostgreSQL):
```bash
# Backup to SQL file
docker exec learnr-postgres-dev pg_dump -U learnr -d learnr_dev > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup in compressed format (recommended)
docker exec learnr-postgres-dev pg_dump -U learnr -d learnr_dev -Fc > backup_$(date +%Y%m%d_%H%M%S).dump
```

**Restore from backup**:
```bash
# Restore from SQL file
docker exec -i learnr-postgres-dev psql -U learnr -d learnr_dev < backup_20250122_143000.sql

# Restore from compressed dump
docker exec -i learnr-postgres-dev pg_restore -U learnr -d learnr_dev --clean --if-exists backup_20250122_143000.dump
```

**Restore to a new database**:
```bash
# Create new database
docker exec learnr-postgres-dev psql -U learnr -c "CREATE DATABASE learnr_restore;"

# Restore backup to new database
docker exec -i learnr-postgres-dev pg_restore -U learnr -d learnr_restore backup_20250122_143000.dump
```

### Production Environment

**Automated backup script** (recommended for production):
```bash
#!/bin/bash
# save as: scripts/backup-database.sh

BACKUP_DIR="/path/to/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/learnr_backup_$TIMESTAMP.dump"

# Create backup
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME -Fc > $BACKUP_FILE

# Compress backup (optional, already compressed with -Fc)
# gzip $BACKUP_FILE

# Upload to cloud storage (S3, GCS, etc.)
# aws s3 cp $BACKUP_FILE s3://your-backup-bucket/

# Keep only last 7 days of backups locally
find $BACKUP_DIR -name "learnr_backup_*.dump" -mtime +7 -delete

echo "Backup completed: $BACKUP_FILE"
```

**Schedule with cron** (daily at 2 AM):
```bash
0 2 * * * /path/to/scripts/backup-database.sh >> /var/log/db-backup.log 2>&1
```

### Point-in-Time Recovery (PITR)

For production, enable PostgreSQL Write-Ahead Logging (WAL) archiving:

1. **Configure PostgreSQL** (`postgresql.conf`):
```ini
wal_level = replica
archive_mode = on
archive_command = 'test ! -f /path/to/archive/%f && cp %p /path/to/archive/%f'
```

2. **Create base backup**:
```bash
pg_basebackup -h localhost -U learnr -D /path/to/base_backup -Ft -z -P
```

3. **Restore to specific point in time**:
```bash
# Stop PostgreSQL
# Restore base backup
# Configure recovery.conf with recovery_target_time
# Start PostgreSQL
```

### Backup Best Practices

- **Frequency**: Daily backups minimum, hourly for critical production systems
- **Retention**: Keep 7 daily, 4 weekly, 12 monthly backups
- **Storage**: Store backups in different location/region than primary database
- **Testing**: Regularly test backup restoration (monthly recommended)
- **Encryption**: Encrypt backups at rest and in transit
- **Monitoring**: Alert on backup failures

### Cloud Provider Backups

**AWS RDS**:
- Automated backups enabled by default (retention 1-35 days)
- Manual snapshots for long-term retention
- Point-in-time recovery available

**Supabase**:
- Pro plan includes daily backups with 7-day retention
- Can trigger manual backups via dashboard
- Export via pg_dump for local copies

**Azure PostgreSQL**:
- Automated backups with 7-35 day retention
- Geo-redundant backup storage available
- Point-in-time restore supported

## Testing

Run all tests:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=src --cov-report=html
```

Run specific test file:
```bash
pytest tests/test_auth.py
```

## API Documentation

### Interactive Documentation

Once the API is running, access interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
  - Interactive API explorer with "Try it out" functionality
  - Test endpoints directly from the browser
  - View request/response schemas and examples

- **ReDoc**: http://localhost:8000/redoc
  - Alternative documentation format
  - Clean, responsive design
  - Better for reading and reference

- **OpenAPI Spec**: http://localhost:8000/openapi.json
  - Raw OpenAPI 3.0 specification
  - Use with API clients like Postman or Insomnia

### Using Authentication in Swagger UI

1. Register or login to get a JWT token:
   - POST `/v1/auth/register` or POST `/v1/auth/login`
   - Copy the `token` from the response

2. Click the "Authorize" button (lock icon) in Swagger UI

3. Enter your token in the format: `Bearer <your_token>`
   - Example: `Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

4. Click "Authorize" - protected endpoints are now accessible

### Health Check

Monitor API health:

```bash
curl http://localhost:8000/health
```

Response (healthy):

```json
{
  "status": "healthy",
  "timestamp": "2025-11-21T10:30:00.123456Z",
  "database": {
    "status": "connected",
    "response_time_ms": 5
  },
  "qdrant": {
    "status": "connected",
    "response_time_ms": 10,
    "collections_count": 2
  }
}
```

The health check verifies:
- **API** is running and responding
- **PostgreSQL** database connection is healthy
- **Qdrant** vector database connection is healthy

Use this endpoint for:
- Load balancer health checks
- Container orchestration (Docker, Kubernetes)
- Monitoring tools (Prometheus, Datadog)
- CI/CD health verification

The endpoint returns:
- **200 OK** - All services healthy
- **503 Service Unavailable** - Database or Qdrant connection failed

## Endpoints Summary

### Authentication (`/v1/auth`)

- `POST /v1/auth/register` - Register new user
- `POST /v1/auth/login` - User login
- `POST /v1/auth/forgot-password` - Request password reset
- `POST /v1/auth/reset-password` - Reset password with token

### Users (`/v1/users`)

- `GET /v1/users/me` - Get current user profile (protected)
- `PUT /v1/users/me` - Update user profile (protected)

### Health

- `GET /health` - API health check (public)

## Deployed Documentation

- **Production API Docs**: https://api.learnr.com/docs
- **Staging API Docs**: https://api-staging.learnr.com/docs

## Contributing

1. Follow the coding standards in `docs/architecture/coding-standards.md`
2. Write tests for all new endpoints and services
3. Run `ruff check src/` and `pytest` before committing
4. Use type hints for all function parameters and return values
5. Document API endpoints with docstrings
