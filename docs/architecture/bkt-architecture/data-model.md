# Data Model

### Core Entities

```
┌─────────────────────────────────────────────────────────────────────┐
│                         KNOWLEDGE GRAPH                             │
├─────────────────────────────────────────────────────────────────────┤
│  concepts                                                           │
│  ├── concept_id (PK)                                               │
│  ├── name                                                          │
│  ├── description                                                   │
│  ├── babok_section_ref (e.g., "3.2.1")                            │
│  ├── knowledge_area (FK) - for aggregation/display                 │
│  ├── difficulty_estimate (0.0-1.0)                                 │
│  ├── prerequisite_depth (int) - distance from root concepts        │
│  └── created_at, updated_at                                        │
│                                                                     │
│  concept_prerequisites (DAG edges)                                  │
│  ├── concept_id (FK)                                               │
│  ├── prerequisite_concept_id (FK)                                  │
│  └── strength (0.0-1.0) - how strongly prerequisite is required    │
│                                                                     │
│  question_concepts (many-to-many)                                   │
│  ├── question_id (FK)                                              │
│  ├── concept_id (FK)                                               │
│  └── relevance (0.0-1.0) - how directly question tests concept     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                         BELIEF STATE                                │
├─────────────────────────────────────────────────────────────────────┤
│  belief_states                                                      │
│  ├── id (PK)                                                       │
│  ├── user_id (FK)                                                  │
│  ├── concept_id (FK)                                               │
│  ├── alpha (float) - Beta distribution parameter                   │
│  ├── beta (float) - Beta distribution parameter                    │
│  ├── last_response_at (timestamp) - for decay/recency              │
│  ├── response_count (int) - questions answered for this concept    │
│  ├── created_at, updated_at                                        │
│  └── UNIQUE(user_id, concept_id)                                   │
│                                                                     │
│  Derived properties (computed, not stored):                         │
│  ├── mean = alpha / (alpha + beta)                                 │
│  ├── confidence = (alpha + beta) / (alpha + beta + 10)             │
│  ├── entropy = beta_distribution(alpha, beta).entropy()            │
│  └── status = 'mastered' | 'gap' | 'uncertain'                     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                      QUESTION BANK                                  │
├─────────────────────────────────────────────────────────────────────┤
│  questions                                                          │
│  ├── question_id (PK)                                              │
│  ├── question_text                                                 │
│  ├── options (JSONB) - A, B, C, D                                  │
│  ├── correct_answer                                                │
│  ├── explanation                                                   │
│  ├── knowledge_area (FK) - for backward compatibility/display      │
│  ├── difficulty (float, 0.0-1.0) - IRT difficulty parameter        │
│  ├── discrimination (float) - IRT discrimination parameter         │
│  ├── guess_rate (float, default 0.25) - P(correct | not mastered)  │
│  ├── slip_rate (float, default 0.10) - P(incorrect | mastered)     │
│  ├── times_asked (int) - for calibration                           │
│  ├── times_correct (int) - for calibration                         │
│  └── created_at, updated_at                                        │
│                                                                     │
│  Note: Each question linked to 1-5 concepts via question_concepts   │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                      RESPONSE LOG                                   │
├─────────────────────────────────────────────────────────────────────┤
│  responses                                                          │
│  ├── response_id (PK)                                              │
│  ├── user_id (FK)                                                  │
│  ├── question_id (FK)                                              │
│  ├── session_id (FK)                                               │
│  ├── selected_answer                                               │
│  ├── is_correct (bool)                                             │
│  ├── time_taken_ms (int)                                           │
│  ├── belief_updates (JSONB) - snapshot of concept updates made     │
│  └── created_at                                                    │
└─────────────────────────────────────────────────────────────────────┘
```

### Entity Relationship Diagram

```
                    ┌──────────────┐
                    │    users     │
                    └──────┬───────┘
                           │
                           │ 1:N
                           ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   concepts   │◄───│ belief_states│    │   sessions   │
└──────┬───────┘    └──────────────┘    └──────┬───────┘
       │                                        │
       │ N:M                                    │ 1:N
       ▼                                        ▼
┌──────────────┐                        ┌──────────────┐
│  questions   │◄───────────────────────│  responses   │
└──────────────┘                        └──────────────┘
       │
       │ N:M (question_concepts)
       ▼
┌──────────────┐
│   concepts   │
└──────────────┘
```

---
