# API Specification

## Status

**ALIGNED** with BKT Architecture (bkt-architecture.md) and Multi-Course Architecture (multi-course-architecture.md)

---

### REST API Specification

The LearnR API follows RESTful conventions with JSON payloads. All endpoints require JWT authentication except `/auth/*` and `/courses` (catalog) routes.

**Base URL:** `https://api.learnr.com/v1` (production) | `http://localhost:8000/v1` (development)

**Authentication:** Bearer token in `Authorization` header: `Authorization: Bearer <jwt_token>`

**Course Context:** For multi-course operations, include `X-Enrollment-ID` header or use course-prefixed endpoints

**Error Format:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid email format",
    "details": { "field": "email" },
    "timestamp": "2025-11-21T10:30:00Z",
    "request_id": "req_abc123"
  }
}
```

---

## Course & Enrollment Endpoints

### Course Catalog (Public)

#### GET /courses
List available courses. Public endpoint for course discovery.

**Query Parameters:**
- `is_active` (boolean, optional): Filter by active status (default: true)
- `search` (string, optional): Search by name

**Response:**
```json
{
  "courses": [
    {
      "id": "uuid",
      "slug": "cbap",
      "name": "CBAP Certification Prep",
      "description": "Prepare for the Certified Business Analysis Professional exam",
      "corpus_name": "BABOK v3",
      "icon_url": "/images/courses/cbap.svg",
      "color_hex": "#3B82F6",
      "knowledge_area_count": 6,
      "concept_count": 1203,
      "question_count": 850,
      "enrolled_count": 1250
    }
  ],
  "total": 1
}
```

#### GET /courses/{slug}
Get detailed course information. Public endpoint.

**Response:**
```json
{
  "id": "uuid",
  "slug": "cbap",
  "name": "CBAP Certification Prep",
  "description": "Prepare for the Certified Business Analysis Professional exam",
  "corpus_name": "BABOK v3",
  "knowledge_areas": [
    {
      "id": "ba-planning",
      "name": "Business Analysis Planning and Monitoring",
      "short_name": "BA Planning",
      "display_order": 1,
      "color": "#3B82F6"
    }
  ],
  "mastery_threshold": 0.8,
  "gap_threshold": 0.5,
  "confidence_threshold": 0.7,
  "default_diagnostic_count": 12,
  "concept_count": 1203,
  "question_count": 850
}
```

#### GET /courses/{slug}/preview
Get course preview with sample content. Public endpoint.

**Response:**
```json
{
  "course": { /* Course object */ },
  "sample_questions": [
    {
      "text": "Which technique is BEST suited for...",
      "options": { "A": "...", "B": "...", "C": "...", "D": "..." },
      "knowledge_area_name": "Strategy Analysis"
    }
  ],
  "sample_reading": {
    "title": "Introduction to Business Analysis",
    "excerpt": "First 200 characters..."
  }
}
```

---

### Enrollment Management

#### POST /enrollments
Enroll in a course. Creates enrollment and initializes belief states.

**Request Body:**
```json
{
  "course_id": "uuid",
  "exam_date": "2025-03-15",
  "target_score": 80,
  "daily_study_time": 60
}
```

**Response:**
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "course_id": "uuid",
  "exam_date": "2025-03-15",
  "target_score": 80,
  "daily_study_time": 60,
  "enrolled_at": "2025-12-08T10:30:00Z",
  "status": "active",
  "completion_percentage": 0,
  "course": {
    "slug": "cbap",
    "name": "CBAP Certification Prep"
  },
  "beliefs_initialized": 1203
}
```

**Errors:**
- `409 ALREADY_ENROLLED`: User already enrolled in this course

#### GET /enrollments
List user's enrollments.

**Response:**
```json
{
  "enrollments": [
    {
      "id": "uuid",
      "course_id": "uuid",
      "course": {
        "slug": "cbap",
        "name": "CBAP Certification Prep",
        "icon_url": "/images/courses/cbap.svg"
      },
      "exam_date": "2025-03-15",
      "target_score": 80,
      "enrolled_at": "2025-12-08T10:30:00Z",
      "last_activity_at": "2025-12-08T15:00:00Z",
      "status": "active",
      "completion_percentage": 35.5,
      "days_until_exam": 97
    }
  ],
  "total": 1
}
```

#### GET /enrollments/{id}
Get enrollment details.

**Response:**
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "course_id": "uuid",
  "course": { /* Full course object with knowledge_areas */ },
  "exam_date": "2025-03-15",
  "target_score": 80,
  "daily_study_time": 60,
  "enrolled_at": "2025-12-08T10:30:00Z",
  "last_activity_at": "2025-12-08T15:00:00Z",
  "status": "active",
  "completion_percentage": 35.5,
  "coverage_summary": {
    "total_concepts": 1203,
    "mastered_count": 427,
    "gap_count": 156,
    "uncertain_count": 620
  }
}
```

#### PATCH /enrollments/{id}
Update enrollment settings.

**Request Body:**
```json
{
  "exam_date": "2025-04-01",
  "target_score": 85,
  "status": "paused"
}
```

**Response:** Updated enrollment object

#### DELETE /enrollments/{id}
Archive enrollment (soft delete).

**Response:**
```json
{
  "message": "Enrollment archived successfully",
  "id": "uuid",
  "status": "archived"
}
```

---

## Core BKT Endpoints

> **Note:** All BKT endpoints require course context via `X-Enrollment-ID` header or will default to user's single enrollment (backward compatibility).

### Belief State Endpoints

#### GET /beliefs
Get all belief states for the authenticated user.

**Query Parameters:**
- `knowledge_area` (string, optional): Filter by Knowledge Area

**Response:**
```json
{
  "beliefs": [
    {
      "concept_id": "uuid",
      "concept_name": "Stakeholder Analysis Techniques",
      "knowledge_area": "Business Analysis Planning and Monitoring",
      "alpha": 8.2,
      "beta": 3.1,
      "mean": 0.725,
      "confidence": 0.849,
      "status": "borderline",
      "last_response_at": "2025-11-21T10:30:00Z",
      "response_count": 5
    }
  ],
  "total": 1203
}
```

#### GET /beliefs/{concept_id}
Get belief state for a specific concept.

**Response:**
```json
{
  "concept_id": "uuid",
  "concept_name": "Stakeholder Analysis Techniques",
  "knowledge_area": "Business Analysis Planning and Monitoring",
  "alpha": 8.2,
  "beta": 3.1,
  "mean": 0.725,
  "confidence": 0.849,
  "status": "borderline",
  "last_response_at": "2025-11-21T10:30:00Z",
  "response_count": 5
}
```

---

### Coverage Endpoints

#### GET /coverage/summary
Get high-level coverage summary for the authenticated user.

**Response:**
```json
{
  "total_concepts": 1203,
  "mastered_count": 847,
  "gap_count": 156,
  "uncertain_count": 200,
  "coverage_percentage": 0.704,
  "confidence_percentage": 0.834,
  "estimated_questions_remaining": 400
}
```

#### GET /coverage/by-knowledge-area
Get coverage breakdown by Knowledge Area for dashboard display.

**Response:**
```json
{
  "knowledge_areas": [
    {
      "knowledge_area": "Business Analysis Planning and Monitoring",
      "total_concepts": 203,
      "mastered_count": 145,
      "gap_count": 28,
      "uncertain_count": 30,
      "readiness_score": 71
    },
    {
      "knowledge_area": "Elicitation and Collaboration",
      "total_concepts": 198,
      "mastered_count": 162,
      "gap_count": 18,
      "uncertain_count": 18,
      "readiness_score": 82
    }
  ]
}
```

#### GET /coverage/gaps
Get gap concepts sorted by priority (for focused study).

**Query Parameters:**
- `knowledge_area` (string, optional): Filter by Knowledge Area
- `limit` (integer, optional): Number of gaps to return (default: 20)

**Response:**
```json
{
  "gaps": [
    {
      "concept_id": "uuid",
      "concept_name": "SWOT Analysis",
      "knowledge_area": "Strategy Analysis",
      "probability": 0.32,
      "confidence": 0.85,
      "priority_score": 0.578,
      "response_count": 4,
      "last_response_at": "2025-11-20T15:00:00Z"
    }
  ],
  "total_gaps": 156
}
```

#### GET /coverage/details
Get full concept-level coverage report.

**Response:**
```json
{
  "total_concepts": 1203,
  "mastered_count": 847,
  "gap_count": 156,
  "uncertain_count": 200,
  "coverage_percentage": 0.704,
  "confidence_percentage": 0.834,
  "estimated_questions_remaining": 400,
  "mastered": [
    {
      "concept_id": "uuid",
      "concept_name": "Requirements Traceability",
      "knowledge_area": "Requirements Life Cycle Management",
      "probability": 0.92,
      "confidence": 0.88,
      "status": "mastered"
    }
  ],
  "gaps": [ /* ConceptStatus objects */ ],
  "uncertain": [ /* ConceptStatus objects */ ]
}
```

---

### Quiz Endpoints

#### POST /quiz/next-question
Get the next optimal question based on BKT question selection.

**Request Body:**
```json
{
  "strategy": "max_info_gain",
  "knowledge_area_filter": null,
  "session_id": "uuid"
}
```

**Strategy Options:**
- `max_info_gain` (default): Maximum expected information gain
- `max_uncertainty`: Target most uncertain concepts
- `prerequisite_first`: Build from foundational concepts
- `balanced`: Even coverage across Knowledge Areas (diagnostic)

**Response:**
```json
{
  "question_id": "uuid",
  "text": "Which technique is BEST suited for...",
  "options": {
    "A": "Option A text",
    "B": "Option B text",
    "C": "Option C text",
    "D": "Option D text"
  },
  "knowledge_area": "Strategy Analysis",
  "difficulty": 0.65,
  "concepts_tested": [
    {
      "concept_id": "uuid",
      "concept_name": "SWOT Analysis",
      "current_belief_mean": 0.45
    }
  ],
  "expected_info_gain": 0.234
}
```

#### POST /quiz/answer
Submit an answer and receive feedback with belief updates.

**Request Headers:**
- `X-Request-ID` (required): Client-generated UUID for idempotency

**Request Body:**
```json
{
  "question_id": "uuid",
  "selected_answer": "B",
  "time_taken_ms": 45000
}
```

**Response:**
```json
{
  "is_correct": true,
  "correct_answer": "B",
  "explanation": "Option B is correct because...",
  "belief_updates": [
    {
      "concept_id": "uuid",
      "concept_name": "SWOT Analysis",
      "old_alpha": 3.2,
      "old_beta": 4.1,
      "new_alpha": 4.1,
      "new_beta": 4.2,
      "old_mean": 0.438,
      "new_mean": 0.494
    }
  ],
  "concepts_affected": 3,
  "reading_recommendation": {
    "chunk_id": "uuid",
    "title": "SWOT Analysis Techniques",
    "priority": "High"
  }
}
```

**Idempotency:** If the same `X-Request-ID` is submitted twice, the server returns the cached response without re-processing.

---

### Session Endpoints

#### POST /sessions
Start a new quiz session.

**Request Body:**
```json
{
  "session_type": "adaptive",
  "question_strategy": "max_info_gain",
  "knowledge_area_filter": null
}
```

**Session Types:**
- `diagnostic`: Initial assessment (balanced strategy, 12-20 questions)
- `adaptive`: Regular adaptive quiz (max_info_gain strategy)
- `focused`: Single Knowledge Area focus
- `review`: Review incorrect answers from previous session

**Response:**
```json
{
  "session_id": "uuid",
  "session_type": "adaptive",
  "question_strategy": "max_info_gain",
  "started_at": "2025-11-21T10:30:00Z"
}
```

#### GET /sessions/{session_id}
Get session details.

**Response:**
```json
{
  "session_id": "uuid",
  "user_id": "uuid",
  "session_type": "adaptive",
  "question_strategy": "max_info_gain",
  "started_at": "2025-11-21T10:30:00Z",
  "ended_at": null,
  "total_questions": 15,
  "correct_count": 11,
  "is_paused": false,
  "version": 3
}
```

#### POST /sessions/{session_id}/end
End a quiz session.

**Request Body:**
```json
{
  "expected_version": 3
}
```

**Response:**
```json
{
  "session_id": "uuid",
  "ended_at": "2025-11-21T11:00:00Z",
  "total_questions": 20,
  "correct_count": 14,
  "accuracy": 0.70,
  "concepts_updated": 47,
  "coverage_delta": {
    "mastered_added": 5,
    "gaps_identified": 3,
    "uncertain_resolved": 8
  }
}
```

**Error (Concurrent Modification):**
```json
{
  "error": {
    "code": "CONCURRENT_MODIFICATION",
    "message": "Session was modified by another device. Please refresh and try again.",
    "current_version": 4
  }
}
```

---

### Diagnostic Assessment Endpoints

> **Note:** Diagnostic endpoints are separate from Quiz endpoints. Diagnostics use batch question selection with no immediate feedback, optimized for initial knowledge profiling.

#### GET /diagnostic/questions
Get optimally-selected diagnostic questions for initial assessment. Questions are selected using a coverage optimization algorithm (Story 3.5) to maximize concept coverage across the corpus.

**Response:**
```json
{
  "questions": [
    {
      "id": "uuid",
      "text": "Which technique is BEST suited for identifying stakeholder concerns early in a project?",
      "options": {
        "A": "SWOT Analysis",
        "B": "Stakeholder Map",
        "C": "Requirements Workshop",
        "D": "Document Analysis"
      },
      "knowledge_area_id": "ba-planning",
      "difficulty": 0.55,
      "discrimination": 1.1
    }
  ],
  "total": 15,
  "concepts_covered": 487,
  "coverage_percentage": 0.405
}
```

**Notes:**
- Returns 12-20 questions selected for maximum concept coverage
- Response **excludes** `correct_answer` and `explanation` (no feedback during diagnostic)
- Questions cached per user for 30 minutes (consistent on page refresh)
- Balanced across knowledge areas (max 4 questions per KA)

**Errors:**
- `401 UNAUTHORIZED`: Missing or invalid JWT token
- `404 NOT_FOUND`: No active enrollment found

[Source: docs/prd/epic-3-bkt.md - Story 3.5]

#### POST /diagnostic/answer
Submit an answer for a diagnostic question. Updates belief states for concepts tested by the question but returns no correctness feedback.

**Request Body:**
```json
{
  "question_id": "uuid",
  "selected_answer": "B"
}
```

**Response:**
```json
{
  "is_recorded": true,
  "concepts_updated": ["uuid1", "uuid2", "uuid3"],
  "diagnostic_progress": 8,
  "diagnostic_total": 15
}
```

**Notes:**
- Response **excludes** `is_correct` and `explanation` (no feedback during diagnostic)
- Belief states updated immediately for all concepts linked to the question
- `diagnostic_progress` indicates questions answered so far
- Updates are atomic (all concept beliefs updated in single transaction)

**Errors:**
- `400 VALIDATION_ERROR`: Invalid question_id or selected_answer
- `401 UNAUTHORIZED`: Missing or invalid JWT token
- `409 DUPLICATE_REQUEST`: Answer already submitted for this question

[Source: docs/prd/epic-3-bkt.md - Story 3.6, Story 3.7]

#### GET /diagnostic/results
Get diagnostic results summary after completing the assessment.

**Response:**
```json
{
  "total_concepts": 1203,
  "concepts_touched": 487,
  "coverage_percentage": 0.405,
  "estimated_mastered": 312,
  "estimated_gaps": 89,
  "uncertain": 802,
  "confidence_level": "initial",
  "by_knowledge_area": [
    {
      "ka": "Business Analysis Planning and Monitoring",
      "concepts": 187,
      "touched": 76,
      "estimated_mastery": 0.62
    },
    {
      "ka": "Elicitation and Collaboration",
      "concepts": 198,
      "touched": 82,
      "estimated_mastery": 0.71
    }
  ],
  "top_gaps": [
    {
      "concept_id": "uuid",
      "name": "Stakeholder Analysis Techniques",
      "mastery_probability": 0.23
    }
  ],
  "recommendations": {
    "primary_focus": "Elicitation and Collaboration",
    "estimated_questions_to_coverage": 450,
    "message": "Great start! Your diagnostic touched 40% of CBAP concepts. Continue with adaptive quizzes to complete your knowledge profile."
  }
}
```

**Notes:**
- Only available after diagnostic completion
- `confidence_level` indicates belief state certainty ("initial", "developing", "established")
- `top_gaps` returns up to 10 concepts with lowest mastery probability
- `recommendations.primary_focus` suggests first knowledge area to study

**Errors:**
- `401 UNAUTHORIZED`: Missing or invalid JWT token
- `404 NOT_FOUND`: No diagnostic results found (diagnostic not completed)

[Source: docs/prd/epic-3-bkt.md - Story 3.8]

---

## Authentication Endpoints

#### POST /auth/register
Register new user account.

#### POST /auth/login
Authenticate user.

**Response:**
```json
{
  "access_token": "jwt_token",
  "refresh_token": "refresh_token",
  "token_type": "bearer",
  "expires_in": 900,
  "user": {
    "id": "uuid",
    "email": "user@example.com"
  }
}
```

#### POST /auth/refresh
Refresh access token.

#### GET /users/me
Get current user profile.

#### PUT /users/me
Update user profile.

---

## GDPR & Data Privacy Endpoints

> **Compliance Note:** These endpoints implement GDPR Article 15 (Right of Access) and Article 17 (Right to Erasure). All operations are logged to `admin_audit_log` for compliance auditing.

### Data Export

#### GET /users/me/export
Export all personal data for the authenticated user (GDPR Article 15 - Right of Access).

**Response Headers:**
- `Content-Type: application/json`
- `Content-Disposition: attachment; filename="learnr-data-export-{user_id}-{timestamp}.json"`

**Response:**
```json
{
  "export_metadata": {
    "exported_at": "2025-12-08T14:30:00Z",
    "user_id": "uuid",
    "format_version": "1.0",
    "data_retention_policy": "Data retained until account deletion"
  },
  "user_profile": {
    "id": "uuid",
    "email": "user@example.com",
    "created_at": "2025-01-15T10:00:00Z",
    "exam_date": "2025-03-15",
    "target_score": 80,
    "daily_study_time": 60,
    "knowledge_level": "intermediate",
    "motivation": "Career advancement",
    "referral_source": "google",
    "dark_mode": "auto"
  },
  "enrollments": [
    {
      "id": "uuid",
      "course_slug": "cbap",
      "course_name": "CBAP Certification Prep",
      "enrolled_at": "2025-01-15T10:30:00Z",
      "exam_date": "2025-03-15",
      "target_score": 80,
      "status": "active",
      "completion_percentage": 45.5
    }
  ],
  "belief_states": [
    {
      "concept_name": "Stakeholder Analysis Techniques",
      "knowledge_area": "Business Analysis Planning",
      "mastery_probability": 0.725,
      "confidence": 0.849,
      "response_count": 5,
      "last_response_at": "2025-12-07T15:00:00Z"
    }
  ],
  "quiz_sessions": [
    {
      "id": "uuid",
      "course_slug": "cbap",
      "session_type": "adaptive",
      "started_at": "2025-12-07T14:00:00Z",
      "ended_at": "2025-12-07T14:45:00Z",
      "total_questions": 25,
      "correct_count": 18,
      "accuracy": 0.72
    }
  ],
  "responses": [
    {
      "question_text": "Which technique is BEST suited for...",
      "selected_answer": "B",
      "is_correct": true,
      "time_taken_ms": 45000,
      "created_at": "2025-12-07T14:05:00Z"
    }
  ],
  "reading_queue": [
    {
      "chunk_title": "SWOT Analysis Deep Dive",
      "knowledge_area": "Strategy Analysis",
      "priority": "High",
      "status": "completed",
      "total_reading_time_seconds": 480,
      "completed_at": "2025-12-06T10:30:00Z"
    }
  ],
  "statistics_summary": {
    "total_quiz_sessions": 24,
    "total_questions_answered": 312,
    "overall_accuracy": 0.73,
    "total_study_time_minutes": 890,
    "concepts_mastered": 487,
    "concepts_with_gaps": 156
  }
}
```

**Notes:**
- Export excludes: password_hash, internal IDs (replaced with readable identifiers), admin flags
- Large exports (>10MB) return `202 Accepted` with a download URL sent via email
- Rate limited: 1 export per hour per user

**Errors:**
- `429 RATE_LIMITED`: Export requested too recently

---

### Account Deletion

#### DELETE /users/me
Permanently delete user account and all associated data (GDPR Article 17 - Right to Erasure).

**Request Body:**
```json
{
  "confirmation": "DELETE MY ACCOUNT",
  "password": "current_password",
  "reason": "No longer preparing for exam"
}
```

**Confirmation Required:** User must type exactly `DELETE MY ACCOUNT` to confirm.

**Response:**
```json
{
  "message": "Account scheduled for deletion",
  "user_id": "uuid",
  "deletion_scheduled_at": "2025-12-08T14:30:00Z",
  "deletion_effective_at": "2025-12-15T14:30:00Z",
  "grace_period_days": 7,
  "data_to_be_deleted": [
    "user_profile",
    "enrollments",
    "belief_states",
    "quiz_sessions",
    "responses",
    "reading_queue"
  ],
  "recovery_instructions": "Log in within 7 days to cancel deletion"
}
```

**Deletion Process:**

1. **Immediate Actions:**
   - User session invalidated (all JWTs revoked via Redis blacklist)
   - User marked as `pending_deletion` (cannot log in)
   - Confirmation email sent with cancellation link

2. **Grace Period (7 days):**
   - User can cancel deletion by clicking email link (re-enables account)
   - No data deleted during grace period
   - User cannot log in during grace period

3. **After Grace Period:**
   - Background job permanently deletes all user data
   - Cascade deletion order (respects foreign key constraints):
     1. `reading_queue` (enrollment-scoped)
     2. `responses` (session-scoped)
     3. `quiz_sessions` (enrollment-scoped)
     4. `belief_states` (user-scoped)
     5. `enrollments` (user-scoped)
     6. `users` (primary record)
   - Qdrant: No user-specific vectors stored (only course content)
   - Redis: Session cache entries purged
   - Audit log entry created (anonymized: `"deleted_user_{hash}"`)

4. **Data Retained (Anonymized):**
   - Aggregate statistics (question difficulty calibration)
   - `admin_audit_log` entries (admin actions on this user - anonymized)

**Errors:**
- `400 VALIDATION_ERROR`: Confirmation text doesn't match
- `401 UNAUTHORIZED`: Password incorrect
- `409 DELETION_PENDING`: Account already scheduled for deletion

---

#### POST /users/me/cancel-deletion
Cancel pending account deletion (during grace period).

**Request Body:**
```json
{
  "cancellation_token": "token_from_email"
}
```

**Response:**
```json
{
  "message": "Account deletion cancelled",
  "user_id": "uuid",
  "account_status": "active"
}
```

**Errors:**
- `400 INVALID_TOKEN`: Token expired or invalid
- `404 NOT_FOUND`: No pending deletion for this account
- `410 GONE`: Grace period expired, deletion already processed

---

## Concept Endpoints

#### GET /concepts
Get all concepts (for admin/debugging).

**Query Parameters:**
- `knowledge_area` (string, optional): Filter by Knowledge Area

**Response:**
```json
{
  "concepts": [
    {
      "id": "uuid",
      "name": "Stakeholder Analysis Techniques",
      "description": "Methods for identifying and analyzing stakeholders",
      "babok_section_ref": "3.2.1",
      "knowledge_area": "Business Analysis Planning and Monitoring",
      "difficulty_estimate": 0.55,
      "prerequisite_depth": 2
    }
  ],
  "total": 1203
}
```

#### GET /concepts/{concept_id}
Get concept details.

#### GET /concepts/{concept_id}/prerequisites
Get prerequisite concepts for a given concept.

---

## Reading Queue Endpoints

#### GET /reading-queue
Get reading queue for authenticated user.

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "chunk_id": "uuid",
      "title": "SWOT Analysis Deep Dive",
      "knowledge_area": "Strategy Analysis",
      "triggered_by_concept_id": "uuid",
      "priority": "High",
      "status": "unread",
      "estimated_read_time_minutes": 8
    }
  ],
  "unread_count": 7,
  "has_high_priority": true
}
```

#### GET /reading-queue/summary
Get reading queue summary for badge display.

**Response:**
```json
{
  "unread_count": 7,
  "has_high_priority": true,
  "priority_breakdown": {
    "high": 2,
    "medium": 3,
    "low": 2
  }
}
```

---

## Admin API Endpoints

**Authentication:** All admin endpoints require `is_admin: true` flag in JWT token.

### User Management

#### GET /admin/users/search
Search users by email, user_id, or name.

#### GET /admin/users/{user_id}
Get detailed user profile including belief state summary.

**Response:**
```json
{
  "user": { /* Full User object */ },
  "analytics": {
    "total_sessions": 24,
    "total_questions_answered": 312,
    "avg_session_duration_minutes": 18,
    "coverage_summary": {
      "total_concepts": 1203,
      "mastered_count": 847,
      "gap_count": 156,
      "coverage_percentage": 0.704
    }
  },
  "posthog_url": "https://app.posthog.com/person/{user_id}"
}
```

### Impersonation

#### POST /admin/impersonate/{user_id}
Impersonate user (generates special JWT with 30-minute expiration).

#### POST /admin/exit-impersonation
Exit impersonation session.

### Audit Log

#### GET /admin/audit-log
Get admin action audit trail.

### Content Management

#### POST /admin/questions/flag
Flag question for review.

#### PUT /admin/questions/{question_id}
Update question (admin edit).

#### DELETE /admin/questions/{question_id}
Delete question (soft delete).

#### POST /admin/concepts
Create new concept.

#### PUT /admin/concepts/{concept_id}
Update concept.

#### POST /admin/concepts/{concept_id}/prerequisites
Add prerequisite relationship.

---

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid request parameters |
| `UNAUTHORIZED` | 401 | Missing or invalid JWT token |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `CONCURRENT_MODIFICATION` | 409 | Optimistic lock conflict |
| `SESSION_ENDED` | 409 | Quiz session ended on another device |
| `DUPLICATE_REQUEST` | 409 | Request ID already processed |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |

---

## Rate Limiting

| Endpoint Category | Limit |
|-------------------|-------|
| Authentication | 10 requests/minute |
| Quiz operations | 60 requests/minute |
| Coverage queries | 30 requests/minute |
| Admin operations | 500 requests/hour |
| Admin impersonation | 10 requests/hour |

---

**Full OpenAPI 3.0 specification available at `/docs` (Swagger UI) and `/redoc` (ReDoc) when API is running.**

---

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-12-11 | 3.2 | Added Diagnostic Assessment Endpoints section (GET /diagnostic/questions, POST /diagnostic/answer, GET /diagnostic/results) per Epic 3 Stories 3.5-3.8 | Sarah (Product Owner) |
| 2025-12-08 | 3.1 | GDPR Compliance - added data export (GET /users/me/export), account deletion (DELETE /users/me), deletion cancellation endpoints | Winston (Architect) |
| 2025-12-08 | 3.0 | Multi-Course Architecture - added Course Catalog endpoints, Enrollment Management endpoints, X-Enrollment-ID header for course context | Winston (Architect) |
| 2025-12-03 | 2.0 | Aligned with BKT Architecture - added beliefs, coverage, BKT quiz endpoints | Winston (Architect) |
| 2025-11-01 | 1.0 | Initial API specification | Original |
