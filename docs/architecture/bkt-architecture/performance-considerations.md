# Performance Considerations

### Belief State Storage

- ~1,500 concepts × N users = potentially millions of rows
- Index on (user_id, concept_id) for fast lookups
- Consider materialized views for coverage aggregations

### Question Selection

- Max info gain requires evaluating all questions: O(Q × C)
- For large question banks, use pre-computed question scores
- Cache question-concept mappings

### Real-time Updates

- Belief updates are O(C) per question (C = concepts tested)
- Use async updates for prerequisite propagation
- Batch belief state writes

---
