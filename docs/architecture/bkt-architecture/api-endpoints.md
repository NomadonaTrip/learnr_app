# API Endpoints

### Belief State Endpoints

```
GET  /api/v1/beliefs
     Returns current belief states for authenticated user
     Query params: ?knowledge_area=X (optional filter)

GET  /api/v1/beliefs/{concept_id}
     Returns belief state for specific concept

GET  /api/v1/coverage
     Returns coverage report with mastered/gaps/uncertain counts

GET  /api/v1/coverage/details
     Returns full concept-level coverage with all belief states
```

### Question Selection Endpoints

```
POST /api/v1/quiz/next-question
     Body: { "strategy": "max_info_gain" | "max_uncertainty" | "prerequisite_first" }
     Returns: Optimally selected question

POST /api/v1/quiz/answer
     Body: { "question_id": UUID, "selected_answer": "A"|"B"|"C"|"D" }
     Returns: { "is_correct": bool, "explanation": str, "belief_updates": [...] }
```

### Coverage Report Endpoints

```
GET  /api/v1/coverage/summary
     Returns: {
       "total_concepts": 1203,
       "mastered": 847,
       "gaps": 156,
       "uncertain": 200,
       "coverage_percentage": 0.704,
       "estimated_questions_remaining": 400
     }

GET  /api/v1/coverage/by-knowledge-area
     Returns: Coverage breakdown by KA for dashboard display

GET  /api/v1/coverage/gaps
     Returns: List of gap concepts sorted by priority
```

---
