# Migration Path

### Phase 1: Data Model (Week 1-2)

1. Create `concepts` table with BABOK concept extraction
2. Create `concept_prerequisites` table
3. Create `belief_states` table
4. Create `question_concepts` junction table
5. Migrate existing questions to new schema

### Phase 2: Core Algorithm (Week 3-4)

1. Implement BeliefUpdater service
2. Implement QuestionSelector service
3. Implement CoverageAnalyzer service
4. Unit tests for all BKT math

### Phase 3: API Integration (Week 5-6)

1. New endpoints for belief states and coverage
2. Modify quiz flow to use BKT question selection
3. Modify answer submission to update beliefs

### Phase 4: UI Updates (Week 7-8)

1. Coverage visualization (concept-level heatmap)
2. Gap analysis with concept details
3. Progress tracking with confidence intervals

---
