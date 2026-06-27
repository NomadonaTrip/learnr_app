# Scrum Master Instructions: Story 4.11 - Prerequisite-Based Curriculum Navigation

**Document Purpose:** Provide the Scrum Master agent with all necessary context to draft the complete story file for Story 4.11.

---

## Quick Reference

| Attribute | Value |
|-----------|-------|
| Story ID | 4.11 |
| Story Title | Prerequisite-Based Curriculum Navigation |
| Epic | Epic 4: Bayesian Adaptive Quiz Engine |
| Functional Requirements | Extends FR5A (Adaptive Question Selection) |
| Dependencies | Story 2.3 (Concept Prerequisite Graph), Story 4.2 (Question Selection), Story 4.4 (Belief Updates) |
| Priority | MEDIUM |
| Estimated Complexity | Medium-High (new service with multiple integration points) |

---

## Source Documents

The Scrum Master should reference these documents when drafting the story:

### Primary Sources

1. **Epic Definition:** `docs/prd/epic-4-bkt.md`
   - Lines 497-685: Full Story 4.11 specification with acceptance criteria
   - Lines 707-708: Dependency chain
   - Lines 1008-1011: Success metrics

2. **Prerequisite Graph Story:** `docs/stories/2.3.concept-prerequisite-graph.md`
   - Defines the prerequisite data model this story enforces
   - API endpoint: GET `/v1/concepts/{id}/prerequisites`

3. **Question Selector Service:** Referenced in Story 4.2
   - Story 4.11 integrates with question selection to filter/weight questions

### Supporting Sources

4. **Gap Analysis:** `docs/prd/gap-analysis-adaptive-learning-vision.md`
   - Lines 93-116: Adaptive traversal rationale
   - Lines 236-257: Dependency enforcement rationale

5. **Algorithm Specifications:** `docs/prd/algorithm-specifications.md`
   - Algorithm 3: Bayesian Belief Update (used for mastery calculation)

---

## Story Structure Template

Based on the existing story format in `docs/stories/`, the SM should create:

```
docs/stories/4.11-prerequisite-based-curriculum-navigation.story.md
```

### Required Sections

1. **Status** - Set to "Ready for Development"

2. **Story** - User story format (As a... I want... So that...)
   ```
   As a user progressing through the curriculum,
   I want the system to enforce prerequisite mastery before testing advanced concepts,
   So that I build knowledge systematically and don't face questions I'm unprepared for.
   ```

3. **Acceptance Criteria** - Extract from epic-4-bkt.md Story 4.11 (10 criteria)

4. **Tasks / Subtasks** - Break down into implementable tasks:
   - Task 1: Create MasteryGate service
   - Task 2: Implement check_prerequisites_mastered method
   - Task 3: Create GateCheckResult dataclass
   - Task 4: Implement apply_prerequisite_filter for question selector
   - Task 5: Create concept unlock status API endpoint
   - Task 6: Create bulk unlock status endpoint
   - Task 7: Implement unlock notification events
   - Task 8: Create concept_unlock_events table migration
   - Task 9: Add override capability endpoint
   - Task 10: Dashboard integration (locked/unlocked counts)
   - Task 11: Unit tests
   - Task 12: Integration tests

5. **Dev Notes** - Include:
   - Dependencies and sequencing
   - Data models (prerequisite graph from 2.3)
   - Existing code assets (ConceptPrerequisiteService)
   - Configuration parameters
   - File locations
   - Soft vs hard enforcement modes

6. **Testing** - Required test cases from acceptance criteria

7. **Change Log** - Initial entry

---

## Key Implementation Details

### New Service: MasteryGateService

**Location:** `apps/api/src/services/mastery_gate.py`

**Primary Method:**
```python
def check_prerequisites_mastered(user_id: UUID, concept_id: UUID) -> GateCheckResult:
    """
    Check if all prerequisites for a concept are mastered.

    Returns:
        GateCheckResult:
            - is_unlocked: bool
            - blocking_prerequisites: List[ConceptSummary]
            - closest_to_unlock: ConceptSummary
            - mastery_progress: float (0.0-1.0)
    """
```

### Configuration

```python
MASTERY_GATE_CONFIG = {
    'prerequisite_mastery_threshold': 0.7,    # P(mastery) > 0.7 required
    'prerequisite_confidence_threshold': 0.6,  # Confidence > 0.6 required
    'enforcement_mode': 'soft',                # 'soft' or 'hard'
    'min_responses_for_gate': 3,               # Minimum responses before gate applies
}
```

### Enforcement Modes

| Mode | Behavior | Weight Applied |
|------|----------|----------------|
| `soft` | Deprioritize locked concepts | 0.1 (10%) |
| `hard` | Exclude locked concepts entirely | 0.0 (excluded) |

### New Database Table

```sql
CREATE TABLE concept_unlock_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    concept_id UUID NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
    unlocked_at TIMESTAMP NOT NULL DEFAULT NOW(),
    prerequisite_concept_id UUID REFERENCES concepts(id),
    UNIQUE (user_id, concept_id)
);

CREATE INDEX idx_unlock_events_user ON concept_unlock_events(user_id);
```

### API Endpoints

1. **Concept Lock Status:**
   ```
   GET /api/v1/concepts/{id}/prerequisites/status
   ```
   Returns unlock status, blocking prerequisites, mastery progress

2. **Bulk Unlock Status:**
   ```
   GET /api/v1/concepts/unlock-status?ka_id={ka_id}
   ```
   Returns unlock status for all concepts in a KA

3. **Override Attempt:**
   ```
   POST /api/v1/concepts/{id}/attempt-locked
   ```
   Allows advanced users to attempt locked concepts

### Question Selector Integration

```python
def apply_prerequisite_filter(candidates: List[Question],
                               user_id: UUID,
                               enforcement: str) -> List[Tuple[Question, float]]:
    """
    Filter or weight questions based on prerequisite mastery.

    Returns list of (question, weight) tuples.
    """
```

---

## Dependencies

### Requires (Must Complete First)

| Story | Reason |
|-------|--------|
| 2.3 | Concept prerequisite graph data model |
| 4.2 | Question selector service to integrate with |
| 4.4 | Belief updates to check mastery status |

### Integrates With

| Story/Epic | Integration Point |
|------------|-------------------|
| Epic 6 | Dashboard shows locked/unlocked concept counts |
| Story 4.5 | Coverage report includes lock status |

---

## Testing Requirements

### Unit Tests (`test_mastery_gate.py`)

1. `test_check_prerequisites_mastered_all_met` - Returns unlocked when all prereqs mastered
2. `test_check_prerequisites_mastered_partial` - Returns blocking list correctly
3. `test_check_prerequisites_mastered_no_prereqs` - Concepts without prereqs always unlocked
4. `test_question_filter_soft_enforcement` - Deprioritizes with 0.1 weight
5. `test_question_filter_hard_enforcement` - Excludes locked concepts
6. `test_mastery_progress_calculation` - Correct progress percentage
7. `test_closest_to_unlock_selection` - Identifies prereq with highest mastery
8. `test_unlock_event_triggered` - Event fires when last prereq mastered

### Integration Tests (`test_prerequisite_navigation_api.py`)

1. `test_concept_lock_status_endpoint` - Returns correct schema
2. `test_bulk_unlock_status_endpoint` - Returns all concepts in KA
3. `test_override_attempt_logged` - Override events tracked in DB
4. `test_question_selection_respects_gates` - Selector avoids locked concepts
5. `test_cascade_unlock` - Unlocking prereq unlocks dependent concepts

---

## File Locations Summary

| Component | File Path |
|-----------|-----------|
| MasteryGate Service | `apps/api/src/services/mastery_gate.py` |
| Migration | `apps/api/src/db/migrations/versions/xxxx_concept_unlock_events.py` |
| Prerequisite Route Extension | `apps/api/src/routes/concepts.py` (add endpoints) |
| Question Selector Integration | `apps/api/src/services/question_selector.py` |
| Unit Tests | `apps/api/tests/unit/services/test_mastery_gate.py` |
| Integration Tests | `apps/api/tests/integration/test_prerequisite_navigation_api.py` |

---

## Success Metrics (from Epic 4)

| Metric | Target |
|--------|--------|
| Gate check latency | <20ms per concept |
| Batch unlock check | <200ms for all concepts |
| Prerequisite violation rate | <5% (questions asked without prereq mastery) |
| Override usage rate | <10% (most users follow progression) |

---

## Notes for SM

1. **Story 2.3 prerequisite graph is prerequisite** - Ensure prerequisite data exists
2. **Soft enforcement is default** - Don't hard-block users initially
3. **Performance is critical** - Gate checks happen on every question selection
4. **Cache prerequisite graph** - Use in-memory cache for O(1) lookups
5. **Unlock events are optional** - Can be disabled via config
6. **Dashboard integration is separate** - This story provides API; Epic 6 handles UI

---

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-12-21 | 1.0 | Initial SM instructions document | PM (John) |
