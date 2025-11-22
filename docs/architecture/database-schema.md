# Database Schema

### PostgreSQL Schema

**Tables:**
- `users` - User accounts with authentication and onboarding data
- `questions` - CBAP exam questions (vectors in Qdrant)
- `quiz_sessions` - Quiz session tracking
- `responses` - User answers to questions
- `competencies` - Competency scores per KA (IRT-based)
- `reading_chunks` - BABOK content chunks (vectors in Qdrant)
- `reading_queue` - Asynchronous reading recommendations
- `spaced_repetition` - SM-2 spaced repetition schedules
- `session_reviews` - Post-session review tracking
- `review_attempts` - Individual review answers
- `admin_audit_log` - Admin operations audit trail

**Key Design Decisions:**
- UUID primary keys (security, distributed systems)
- Dual database strategy: PostgreSQL (structured data) + Qdrant (vector search)
- 3NF normalization with selective denormalization for performance
- Comprehensive indexing strategy for adaptive queries
- Triggers for automatic timestamp updates
- Views for optimized dashboard queries

### Qdrant Collections

- `questions` collection - 3072-dim vectors, filtered by KA and difficulty
- `reading_chunks` collection - 3072-dim vectors, filtered by KA and BABOK section

---
