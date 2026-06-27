# Epic 10: IRT Difficulty Distribution & Ability-Based Question Selection

**Epic Goal:** Implement Item Response Theory (IRT) based difficulty distribution that selects question difficulty levels probabilistically based on user ability classification, ensuring learners receive appropriately challenging questions that maximize learning efficiency while avoiding frustration or boredom.

**Key Capabilities:**
- **Ability Classification:** Classify users as novice/intermediate/expert per concept based on response history
- **Difficulty Distribution:** Probabilistically select question difficulty tiers based on ability level
- **Combined BKT-IRT Selection:** Orchestrate concept selection (BKT) with difficulty selection (IRT)
- **IRT Scale Migration:** Migrate from legacy 0.0-1.0 difficulty scale to standard IRT b-parameter (-3.0 to +3.0)

**Separation of Concerns:**
- **BKT (Bayesian Knowledge Tracing):** Answers "Do they know this concept?" (mastery probability)
- **IRT (Item Response Theory):** Answers "At what difficulty level can they demonstrate it?" (ability classification)

**Architecture Reference:** See `docs/architecture/adr-002-irt-difficulty-scale.md`

**Algorithm Reference:** See `docs/prd/algorithm-specifications.md` (Algorithms 7, 8, 9)

---

## Business Context

### Problem Statement

The current BKT-based question selection optimizes for *which concept* to test but does not consider *how difficult* the question should be. This leads to:

1. **Novice frustration:** New learners may receive hard questions too early
2. **Expert boredom:** Advanced learners may receive too many easy questions
3. **Suboptimal learning:** Zone of proximal development not targeted

### Solution Overview

Implement a two-layer adaptive selection system:

```
┌─────────────────────────────────────────────────────────────────┐
│                    ADAPTIVE QUESTION SELECTION                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  BKT LAYER (What to teach)                                     │
│  ─────────────────────────                                     │
│  • Calculate information gain per concept                       │
│  • Apply prerequisite weighting                                 │
│  • Select concept with highest info gain                        │
│  • Output: target_concept_id                                    │
│                                                                 │
│                         ↓                                       │
│                                                                 │
│  IRT LAYER (How hard to teach)                                 │
│  ──────────────────────────────                                │
│  • Get user's response history for concept                      │
│  • Classify ability level (novice/intermediate/expert)          │
│  • Sample difficulty tier from distribution                     │
│  • Filter questions to tier, select randomly                    │
│  • Output: selected_question                                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Difficulty Distribution Matrix

| Ability Level | Easy | Medium | Hard | Rationale |
|---------------|------|--------|------|-----------|
| Novice | 70% | 25% | 5% | Build confidence; occasional stretch |
| Intermediate | 40% | 40% | 20% | Balanced mix; medium is learning zone |
| Expert | 10% | 40% | 50% | Primary hard focus; medium maintains breadth |

### IRT Scale Definition

| Tier | IRT b-parameter Range | Legacy Scale (deprecated) |
|------|----------------------|---------------------------|
| Easy | -3.0 to -1.0 | 0.0 to 0.4 |
| Medium | -1.0 to +1.0 | 0.4 to 0.7 |
| Hard | +1.0 to +3.0 | 0.7 to 1.0 |

---

## Stories

### Story 10.1: IRT Scale Database Migration

**As a** system administrator,
**I want** the database to use standard IRT b-parameter scale (-3.0 to +3.0),
**So that** difficulty values align with psychometric standards and enable proper IRT model fitting.

**Acceptance Criteria:**

1. Database migration adds `difficulty_label` column to `questions` table (VARCHAR(10), nullable)
2. Database migration drops constraint `ck_questions_difficulty_range` (0.0-1.0)
3. Existing difficulty values converted using mapping:
   - 0.3 → -1.5 (Easy)
   - 0.5 → 0.0 (Medium)
   - 0.7 → +1.5 (Hard)
   - Other values: linear transform `(d - 0.5) * 6`
4. New constraint added: `difficulty >= -3.0 AND difficulty <= 3.0`
5. `difficulty_label` populated based on IRT tier classification
6. Migration is reversible (downgrade path defined)
7. All existing questions retain correct relative difficulty ordering
8. API responses include both `difficulty` (numeric) and `difficulty_label` (string)
9. Update `docs/prd/database-schema-bkt.md` to reflect new IRT scale constraints

**Technical Notes:**
- See ADR-002 for full migration specification
- Alembic migration file: `q7l8m9n0o1p2_migrate_difficulty_to_irt_scale.py`

**Dependencies:** None (foundational)

---

### Story 10.2: Question Import IRT Support

**As a** content administrator,
**I want** the question import pipeline to accept IRT-scale difficulty values,
**So that** new questions can be imported with proper psychometric calibration.

**Acceptance Criteria:**

1. CSV import accepts new columns:
   - `difficulty_b` (float, -3.0 to +3.0) - IRT b-parameter
   - `difficulty_label` (string) - Easy/Medium/Hard
   - `discrimination` (float, 0.0-5.0) - IRT a-parameter
   - `guess_rate` (float, 0.0-1.0) - P(correct | not mastered)
   - `slip_rate` (float, 0.0-1.0) - P(incorrect | mastered)
2. `difficulty_b` takes precedence over `difficulty_label` if both provided
3. Legacy format (`difficulty` as Easy/Medium/Hard string) still supported
4. Legacy numeric values (0.0-1.0) auto-detected and converted to IRT scale
5. Validation rejects values outside valid ranges
6. Import summary includes IRT parameter statistics
7. Updated CSV template available at `scripts/data/question_template_irt.csv`

**Technical Notes:**
- `DIFFICULTY_MAP` updated: Easy→-1.5, Medium→0.0, Hard→+1.5
- Backward compatible with existing CSV files

**Dependencies:** Story 10.1

---

### Story 10.3: User Ability Classification per Concept (Algorithm 7)

**As a** quiz engine,
**I want** to classify each user's ability level for a specific concept,
**So that** I can select appropriately difficult questions.

**Acceptance Criteria:**

1. Ability classification service in `question_selector.py`
2. Classification based on:
   - BKT mastery probability (from belief state)
   - Performance breakdown by difficulty tier (easy/medium/hard correct counts)
3. Classification rules:
   ```
   EXPERT if:
     - P(mastery) >= 0.7 AND
     - hard_correct >= 3 AND
     - hard_accuracy >= 50%

   INTERMEDIATE if:
     - P(mastery) >= 0.4 AND
     - medium_correct >= 3 AND
     - medium_accuracy >= 60%

   NOVICE otherwise
   ```
4. New users with no history default to `novice`
5. Self-reported familiarity from onboarding (Story 3.2) can bootstrap initial level
6. Ability level logged for each question selection
7. Performance query efficient (<10ms)

**Technical Notes:**
- See Algorithm 7 in `algorithm-specifications.md`
- `DifficultyPerformance` dataclass tracks tier-level stats

**Dependencies:** Story 10.1, Epic 4 (belief states exist)

---

### Story 10.4: IRT Difficulty Distribution Selection (Algorithm 8)

**As a** quiz engine,
**I want** to probabilistically select question difficulty based on user ability,
**So that** learners receive appropriately challenging questions.

**Acceptance Criteria:**

1. Difficulty tier selection using weighted random choice
2. Distribution configuration:
   ```python
   DIFFICULTY_DISTRIBUTION = {
       'novice':       {'easy': 0.70, 'medium': 0.25, 'hard': 0.05},
       'intermediate': {'easy': 0.40, 'medium': 0.40, 'hard': 0.20},
       'expert':       {'easy': 0.10, 'medium': 0.40, 'hard': 0.50}
   }
   ```
3. Tier boundaries using IRT scale:
   - Easy: -3.0 to -1.0
   - Medium: -1.0 to +1.0
   - Hard: +1.0 to +3.0
4. Fallback logic when tier has no questions:
   - Novice: prefer medium over hard
   - Intermediate: prefer adjacent tier with more questions
   - Expert: prefer medium over easy
5. Random selection within filtered tier
6. Logging includes: ability_level, target_tier, was_fallback, distribution
7. Selection completes in <10ms additional latency

**Technical Notes:**
- See Algorithm 8 in `algorithm-specifications.md`
- Configuration supports A/B testing variants

**Dependencies:** Story 10.3

---

### Story 10.5: Combined BKT-IRT Question Selection (Algorithm 9)

**As a** quiz engine,
**I want** to orchestrate BKT concept selection with IRT difficulty selection,
**So that** users receive the optimal question for both concept and difficulty.

**Acceptance Criteria:**

1. New method `select_next_question_adaptive()` in `QuestionSelector`
2. Selection flow:
   - Step 1: BKT selects target concept (max information gain)
   - Step 2: Get questions for target concept
   - Step 3: Classify user ability for concept
   - Step 4: Sample difficulty tier from distribution
   - Step 5: Filter to tier, select randomly
3. Return value includes: `(question, info_gain, ability_level, difficulty_tier)`
4. `use_irt` parameter allows disabling IRT layer (for A/B testing)
5. Existing `select_next_question()` preserved for backward compatibility
6. Combined selection completes in <200ms total
7. Comprehensive logging for debugging and analytics
8. Unit tests cover all selection paths

**Technical Notes:**
- See Algorithm 9 in `algorithm-specifications.md`
- Integrates with existing filtering (recency, session exclusion)

**Dependencies:** Stories 10.3, 10.4, Epic 4 (existing BKT selection)

---

### Story 10.6: Pydantic Schema Updates for IRT

**As a** developer,
**I want** API schemas to reflect IRT scale changes,
**So that** request/response validation is correct.

**Acceptance Criteria:**

1. `QuestionBase.difficulty` updated: `ge=-3.0, le=3.0`
2. `QuestionBase.difficulty_label` added (optional string)
3. `QuestionCreate`, `QuestionUpdate` schemas updated
4. `QuestionResponse` includes `difficulty_label`
5. `QuestionListParams.difficulty_min/max` updated to IRT range
6. `QuestionListParams.difficulty_tier` added for tier-based filtering
7. `QuestionImport.get_difficulty_float()` returns IRT scale values
8. `QuestionImport.get_difficulty_label()` helper added
9. All existing API contracts preserved (non-breaking)

**Dependencies:** Story 10.1

---

### Story 10.7: Algorithm Specification Documentation

**As a** developer or architect,
**I want** complete algorithm specifications for IRT integration,
**So that** implementation follows defined behavior.

**Acceptance Criteria:**

1. Algorithm 7 (User Ability Classification) documented with:
   - Input parameters
   - Classification rules with thresholds
   - Pseudocode
   - Examples
2. Algorithm 8 (IRT Difficulty Distribution) documented with:
   - Distribution matrix
   - Tier boundaries
   - Selection pseudocode
   - Fallback logic
3. Algorithm 9 (Combined BKT-IRT Selection) documented with:
   - Architecture diagram
   - Flow description
   - Integration points
4. All algorithms include:
   - Performance considerations
   - Configuration for A/B testing
   - Success metrics

**Status:** COMPLETE - See `docs/prd/algorithm-specifications.md`

**Dependencies:** None

---

## Integration with Existing Stories

### Story 5.11: Concept-Linked Reading Intervention

**Relationship:** Story 5.11 uses IRT difficulty performance to detect stuck students.

When a user has consecutive failures at their expected difficulty tier, the intervention system:
1. Queries `DifficultyPerformance` for the concept
2. Detects declining accuracy at the user's ability tier
3. Triggers reading material recommendations

**Cross-Reference:** See `docs/stories/5.11-concept-linked-reading-intervention.story.md`

### Epic 4: Bayesian Adaptive Quiz Engine

**Relationship:** Epic 10 extends Epic 4's question selection with IRT layer.

- Story 4.2 (Bayesian Question Selection) → Extended by Story 10.5
- Story 4.4 (Belief Update Engine) → Provides mastery probability for ability classification
- Story 4.7 (Adaptive Session Termination) → Can use ability-tier performance for termination signals

---

## Dependencies

```
Epic 10 Story Dependencies:

10.1 (DB Migration) → 10.2 (Import), 10.3 (Classification), 10.6 (Schemas)
10.3 (Classification) → 10.4 (Distribution)
10.4 (Distribution) → 10.5 (Combined Selection)
10.7 (Documentation) → All stories (reference)

External Dependencies:

From Epic 2:
- Questions with difficulty values (Story 2.4)

From Epic 3:
- User familiarity from onboarding (Story 3.2)

From Epic 4:
- Belief states exist (Story 3.4)
- Question selector service (Story 4.2)
- Quiz session infrastructure (Story 4.1)
```

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Difficulty-appropriate accuracy | 60-80% per tier | Users should succeed at expected rate for their tier |
| Ability classification accuracy | >85% | Validated against expert assessment |
| Engagement (session length) | +15% vs control | Users stay longer when appropriately challenged |
| Frustration signal (consecutive failures) | <10% sessions | Fewer stuck-student interventions triggered |
| Boredom signal (skip rate) | <5% | Users don't skip questions due to being too easy |
| Selection latency | <200ms total | IRT layer adds <10ms |
| Migration accuracy | 100% | All questions correctly converted |

---

## Rollout Strategy

### Phase 1: Foundation (Stories 10.1, 10.6, 10.7)
- Database migration
- Schema updates
- Documentation complete

### Phase 2: Import Pipeline (Story 10.2)
- Updated question import
- New CSV template

### Phase 3: Selection Engine (Stories 10.3, 10.4, 10.5)
- Ability classification
- Difficulty distribution
- Combined selection

### Phase 4: A/B Testing
- Feature flag: `IRT_DIFFICULTY_ENABLED`
- Compare metrics vs. control (random difficulty)
- Validate success metrics

---

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-12-22 | 1.1 | Added AC 9 to Story 10.1: Update database-schema-bkt.md after migration | PM (John) |
| 2025-12-21 | 1.0 | Initial epic creation; Algorithms 7-9 specified; ADR-002 for migration | PM (John) |
