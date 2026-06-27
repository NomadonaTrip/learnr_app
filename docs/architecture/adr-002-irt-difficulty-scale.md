# ADR-002: IRT Difficulty Scale Migration

## Status
Proposed

## Context

The LearnR adaptive learning system uses Item Response Theory (IRT) for question difficulty calibration. The current implementation stores difficulty on a **0.0-1.0 scale**, while standard IRT psychometric practice uses a **-3 to +3 scale** (the b-parameter).

### Current State
- **Database**: `questions.difficulty` constrained to `0.0 <= difficulty <= 1.0`
- **Import script**: Maps `Easy/Medium/Hard` → `0.3/0.5/0.7`
- **Schemas**: Pydantic validators enforce `ge=0.0, le=1.0`
- **Algorithm specs**: Reference both scales inconsistently

### Desired State
- Standard IRT b-parameter scale: **-3.0 to +3.0**
- Aligns with psychometric literature and tooling
- Enables proper IRT model fitting with external calibration tools
- Clear mapping: `Easy=-1.5, Medium=0.0, Hard=+1.5`

## Decision

**Migrate to standard IRT b-parameter scale (-3 to +3)** with the following approach:

### Phase 1: Schema & Model Updates
1. Update database constraint: `difficulty >= -3.0 AND difficulty <= 3.0`
2. Update Pydantic schemas: `ge=-3.0, le=3.0`
3. Add `difficulty_label` column (optional, for human readability)

### Phase 2: Data Migration
1. Convert existing difficulty values:
   ```python
   # Linear transformation from [0,1] to [-3,3]
   difficulty_new = (difficulty_old - 0.5) * 6

   # Discrete mapping for labeled values:
   # Easy (0.3)  → -1.2 ≈ -1.5 (round to tier center)
   # Medium (0.5) → 0.0
   # Hard (0.7)  → +1.2 ≈ +1.5 (round to tier center)
   ```

### Phase 3: Import Pipeline Updates
1. Accept both `difficulty_label` (Easy/Medium/Hard) and `difficulty_b` (numeric)
2. Numeric takes precedence if both provided
3. Update DIFFICULTY_MAP to IRT scale

## IRT Scale Reference

| Tier | Label | b-parameter Range | Tier Center |
|------|-------|-------------------|-------------|
| Easy | Easy | -3.0 to -1.0 | -1.5 |
| Medium | Medium | -1.0 to +1.0 | 0.0 |
| Hard | Hard | +1.0 to +3.0 | +1.5 |

## Files Requiring Updates

### Database Migration
```sql
-- Alembic migration: alter_difficulty_constraint.py
ALTER TABLE questions DROP CONSTRAINT ck_questions_difficulty_range;
ALTER TABLE questions ADD CONSTRAINT ck_questions_difficulty_range
    CHECK (difficulty >= -3.0 AND difficulty <= 3.0);

-- Optional: Add difficulty_label column
ALTER TABLE questions ADD COLUMN difficulty_label VARCHAR(10);
```

### Python Files

| File | Change Required |
|------|-----------------|
| `apps/api/src/models/question.py` | Update CheckConstraint range, add difficulty_label column |
| `apps/api/src/schemas/question.py` | Update Field validators (ge=-3.0, le=3.0) |
| `scripts/import_vendor_questions.py` | Update DIFFICULTY_MAP, accept difficulty_b column |
| `apps/api/src/services/question_selector.py` | Update difficulty tier logic |
| `docs/prd/algorithm-specifications.md` | Already updated to reference IRT scale |

### Algorithm Adjustments

**Algorithm 8 (IRT Difficulty Distribution)** tier boundaries:
```python
# Updated from normalized scale to IRT b-parameter
DIFFICULTY_TIERS = {
    'easy': (-3.0, -1.0),     # Was (0.0, 0.4)
    'medium': (-1.0, 1.0),    # Was (0.4, 0.7)
    'hard': (1.0, 3.0)        # Was (0.7, 1.0)
}
```

## CSV Template Changes

### Old Format (vendor_questions_sample.csv)
```csv
question_text,...,difficulty,concept_tags
"...",Easy,"concept1,concept2"
```

### New Format (question_template_irt.csv)
```csv
question_text,...,difficulty_label,difficulty_b,discrimination,guess_rate,slip_rate,primary_concept,secondary_concepts,...
"...",Easy,-1.5,1.0,0.25,0.10,concept-id,"concept2,concept3",...
```

### New Columns
| Column | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `difficulty_label` | string | No | - | Human-readable: Easy/Medium/Hard |
| `difficulty_b` | float | No | 0.0 | IRT b-parameter (-3 to +3) |
| `discrimination` | float | No | 1.0 | IRT a-parameter (0 to 5) |
| `guess_rate` | float | No | 0.25 | P(correct \| not mastered) |
| `slip_rate` | float | No | 0.10 | P(incorrect \| mastered) |
| `primary_concept` | string | No | - | Primary concept slug |
| `secondary_concepts` | string | No | - | Comma-separated concept slugs |
| `perspectives` | string | No | - | Comma-separated perspective IDs |
| `competencies` | string | No | - | Comma-separated competency IDs |

## Backward Compatibility

1. **Import pipeline**: Accept both old and new CSV formats
2. **API responses**: No breaking changes (difficulty field remains)
3. **Frontend**: Update difficulty display formatting only

## Consequences

### Positive
- Aligns with psychometric standards
- Enables external IRT calibration tool integration
- Clearer interpretation: 0 = average difficulty, negative = easier, positive = harder
- Better support for fine-grained difficulty distinctions

### Negative
- Requires database migration with data transformation
- Import script changes needed
- Existing integrations may need updates
- Team needs to understand IRT scale semantics

## Migration Script Location
`scripts/migrations/migrate_difficulty_to_irt_scale.py`
