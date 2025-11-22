# Algorithm Specifications

LearnR's adaptive learning engine relies on several key algorithms. This section provides complete pseudocode for implementation.

**Algorithm Design Principles:**
- **Start simple, refine iteratively:** MVP uses simplified formulas (e.g., fixed competency deltas); Phase 2 can implement full IRT
- **Transparent to users:** Competency scores and progress always visible, not "black box" AI
- **Tunable parameters:** Key thresholds and weights configurable for A/B testing post-MVP
- **Performance-conscious:** All algorithms execute in <500ms to maintain responsive UX

---

### Algorithm 1: Priority Calculation for Reading Materials

**Purpose:** Determines High/Medium/Low priority for reading queue items based on user performance and competency.

**Trigger:** When adding content to reading queue (after incorrect answer or low competency)

**Parameters:**
- `user_competency` (float): Overall user competency (0.0-1.0)
- `was_incorrect` (boolean): Whether user answered question incorrectly
- `ka_competency` (float): User's competency in this specific Knowledge Area (0.0-1.0)
- `question_difficulty` (float): Question difficulty level (0.0-1.0)

**Returns:** `'high'` | `'medium'` | `'low'`

**Pseudocode:**
```python
def calculate_priority(
    user_competency: float,
    was_incorrect: bool,
    ka_competency: float,
    question_difficulty: float
) -> str:
    """
    Calculate reading priority based on multiple factors.

    Key Thresholds:
    - KA competency < 0.5: High priority (significant gap)
    - KA competency < 0.6: High priority if incorrect
    - Question difficulty > 0.5: High priority if incorrect
    - KA competency 0.6-0.75: Medium priority (borderline)
    - KA competency > 0.75: Low priority (proficient)
    """

    # High priority conditions:
    # - User got question wrong AND has significant gap in this KA
    if was_incorrect and ka_competency < 0.6:
        return 'high'

    # - User got question wrong AND question was moderately difficult
    if was_incorrect and question_difficulty > 0.5:
        return 'high'

    # - User has major competency gap regardless of answer
    if ka_competency < 0.5:
        return 'high'

    # Medium priority:
    # - User got question wrong but competency is okay
    if was_incorrect:
        return 'medium'

    # - User's competency is borderline (needs reinforcement)
    if 0.6 <= ka_competency < 0.75:
        return 'medium'

    # Low priority:
    # - User got question right AND competency already good
    return 'low'
```

**Example Scenarios:**
- User with KA competency 0.45 answers incorrectly → **High** (significant gap + mistake)
- User with KA competency 0.68 answers incorrectly → **Medium** (borderline competency)
- User with KA competency 0.82 answers correctly → **Low** (proficient)

---

### Algorithm 2: Asynchronous Reading Queue Population

**Purpose:** Automatically add relevant BABOK reading chunks to user's queue after answering questions.

**Trigger:** After each question answered (if incorrect OR if user's KA competency < 0.7)

**Parameters:**
- `user_id`: UUID of user
- `question_id`: UUID of question just answered
- `session_id`: UUID of current quiz session
- `ka_id`: UUID of Knowledge Area
- `user_competency`: User's current competency in this KA (0.0-1.0)
- `was_incorrect`: Whether answer was incorrect

**Implementation:** Runs asynchronously (background task/queue) to avoid blocking quiz response

**Pseudocode:**
```python
async def add_reading_to_queue_async(
    user_id: UUID,
    question_id: UUID,
    session_id: UUID,
    ka_id: UUID,
    user_competency: float,
    was_incorrect: bool
) -> None:
    """
    Asynchronously add relevant reading material to user's queue.

    Steps:
    1. Get question details and concept tags
    2. Build semantic query from question + tags
    3. Vector similarity search for relevant chunks
    4. Calculate priority
    5. Add to queue (top 2-3 chunks, avoid duplicates)
    6. Notify user (update badge count)
    """

    # Step 1: Get question details
    question = await db.get_question(question_id)

    # Step 2: Build semantic query
    # Combine question text with concept tags for richer semantic match
    query_text = f"{question.question_text} {' '.join(question.concept_tags)}"
    query_embedding = await get_embedding(query_text)  # OpenAI API call

    # Step 3: Vector similarity search
    # Find top 3 most semantically similar chunks in same KA
    chunks = await db.query(ContentChunk)\
        .filter(ContentChunk.ka_id == ka_id)\
        .order_by(
            ContentChunk.embedding.cosine_distance(query_embedding).asc()
        )\
        .limit(3)\
        .all()

    # Step 4: Calculate priority for these chunks
    priority = calculate_priority(
        user_competency=user_competency,
        was_incorrect=was_incorrect,
        ka_competency=user_competency,
        question_difficulty=question.difficulty
    )

    # Step 5: Add to queue (with duplicate prevention)
    for chunk in chunks:
        # Calculate relevance score (1.0 = perfect match, 0.0 = no match)
        relevance_score = 1 - cosine_distance(chunk.embedding, query_embedding)

        # Only add if sufficiently relevant (threshold: 0.7)
        if relevance_score > 0.7:
            # Check if chunk already in user's queue
            existing = await db.get_reading_queue_item(user_id, chunk.chunk_id)

            if not existing:
                # Add new reading queue item
                reading_item = ReadingQueue(
                    user_id=user_id,
                    chunk_id=chunk.chunk_id,
                    question_id=question_id,
                    session_id=session_id,
                    was_incorrect=was_incorrect,
                    relevance_score=round(relevance_score, 2),
                    priority=priority,
                    ka_id=ka_id,
                    reading_status='unread',
                    added_at=datetime.now()
                )
                await db.add(reading_item)

    await db.commit()

    # Step 6: Update user's unread badge count
    # Send real-time notification (WebSocket/SSE) or set flag for next page load
    await notify_user_reading_added(user_id)
```

**Performance Notes:**
- OpenAI embedding API call: ~100-200ms
- Vector similarity search (Qdrant or pgvector): ~50-150ms
- Database inserts: ~20-50ms
- **Total estimated time:** 200-400ms (acceptable for background task)

**Relevance Threshold Rationale:**
- 0.7 threshold filters out weakly related content
- Typical distribution: Top 1-2 chunks score 0.8-0.95, next 1-2 score 0.7-0.8
- Prevents queue pollution with marginally relevant material

---

### Algorithm 3: Simplified IRT Competency Update

**Purpose:** Update user's competency score after each quiz answer using simplified Item Response Theory.

**Trigger:** After each quiz answer submission

**Parameters:**
- `current_competency`: User's current competency in this KA (0.0-100.0)
- `question_difficulty`: Question difficulty (0.0-1.0 scale)
- `is_correct`: Whether answer was correct

**Returns:** Updated competency score (0.0-100.0)

**Pseudocode:**
```python
def update_competency_simple_irt(
    current_competency: float,
    question_difficulty: float,
    is_correct: bool
) -> float:
    """
    Simplified IRT competency update for MVP.

    Logic:
    - Harder questions answered correctly → larger boost
    - Easier questions answered correctly → smaller boost
    - Any incorrect answer → small penalty (-1%)
    - Competency capped at 0-100%

    Phase 2: Replace with full IRT using logistic model
    """

    # Map difficulty to competency delta
    if is_correct:
        if question_difficulty >= 0.7:  # Hard question
            delta = +5.0
        elif question_difficulty >= 0.4:  # Medium question
            delta = +3.0
        else:  # Easy question
            delta = +2.0
    else:
        # Small penalty for incorrect (prevents overconfidence)
        delta = -1.0

    # Apply delta
    new_competency = current_competency + delta

    # Clamp to valid range
    new_competency = max(0.0, min(100.0, new_competency))

    return new_competency
```

**Example Updates:**
- User at 60% competency answers Hard question correctly → 65% (+5%)
- User at 75% competency answers Easy question correctly → 77% (+2%)
- User at 80% competency answers Medium question incorrectly → 79% (-1%)

**Phase 2 Enhancement (Post-MVP):**
Replace with full IRT logistic model:
```
P(correct) = 1 / (1 + e^(-a * (θ - b)))
where:
  θ = user ability (competency)
  b = question difficulty
  a = question discrimination
```

---

### Algorithm 4: Adaptive Question Selection

**Purpose:** Select next question based on user's competency, gaps, and question history.

**Trigger:** When user clicks "Next Question" or starts new session

**Parameters:**
- `user_id`: UUID of user
- `session_id`: UUID of current session
- `target_ka_id` (optional): If user selected focused KA practice

**Selection Criteria (prioritized):**
1. **KA Match:** If `target_ka_id` specified, only select from that KA
2. **Gap Targeting:** Prefer KAs where user competency < 70%
3. **Difficulty Targeting:** Select difficulty near user's competency level (±10%)
4. **Freshness:** Avoid questions answered in last 7 days (if possible)
5. **Randomization:** Shuffle eligible questions to avoid patterns

**Pseudocode:**
```python
def select_next_question(
    user_id: UUID,
    session_id: UUID,
    target_ka_id: Optional[UUID] = None
) -> Question:
    """
    Select next adaptive question using multi-criteria filtering.
    """

    # Get user's competency across all KAs
    competencies = db.get_user_competencies(user_id)

    # Determine target KA
    if target_ka_id:
        ka_id = target_ka_id
        user_competency = competencies[ka_id]
    else:
        # Prioritize KA with lowest competency (gap targeting)
        ka_id, user_competency = min(competencies.items(), key=lambda x: x[1])

    # Determine target difficulty (match user level ±10%)
    target_difficulty_min = max(0.0, (user_competency / 100) - 0.10)
    target_difficulty_max = min(1.0, (user_competency / 100) + 0.10)

    # Get recent question history (last 7 days)
    recent_question_ids = db.get_recent_questions(user_id, days=7)

    # Build query
    eligible_questions = db.query(Question)\
        .filter(Question.ka_id == ka_id)\
        .filter(Question.difficulty.between(target_difficulty_min, target_difficulty_max))\
        .filter(Question.question_id.notin_(recent_question_ids))\
        .all()

    # Fallback: If no eligible questions (all answered recently), remove freshness constraint
    if not eligible_questions:
        eligible_questions = db.query(Question)\
            .filter(Question.ka_id == ka_id)\
            .filter(Question.difficulty.between(target_difficulty_min, target_difficulty_max))\
            .all()

    # Randomize to avoid predictable patterns
    import random
    selected_question = random.choice(eligible_questions)

    return selected_question
```

---

### Algorithm 5: SM-2 Spaced Repetition (Adapted)

**Purpose:** Schedule concept reviews at optimal intervals based on SuperMemo 2 algorithm, adapted for 60-day exam timeline.

**Trigger:** After user answers a review question

**Parameters:**
- `concept_tag`: Concept being reviewed
- `quality`: User's answer quality (0-5 scale, where 3+ = correct)
- `current_interval`: Current review interval in days
- `ease_factor`: Current ease factor (default: 2.5)

**Returns:** Next review date, updated interval, updated ease factor

**Standard SM-2 Intervals:** 1 day → 6 days → 6 * EF days → ...
**LearnR Adapted Intervals:** 1 day → 3 days → 7 days → 14 days (compressed for 60-day prep)

**Pseudocode:**
```python
def calculate_next_review_sm2_adapted(
    concept_tag: str,
    quality: int,  # 0-5 where 3+ = correct
    current_interval: int,
    ease_factor: float
) -> Tuple[date, int, float]:
    """
    Adapted SM-2 for 60-day exam prep timeline.

    Standard SM-2: 1d → 6d → 6*EF → (6*EF)*EF → ...
    LearnR Adapted: 1d → 3d → 7d → 14d (max)

    Rationale: 60 days insufficient for standard SM-2 long intervals
    """

    # Update ease factor based on answer quality
    ease_factor = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    ease_factor = max(1.3, ease_factor)  # Minimum EF = 1.3

    # Determine next interval
    if quality < 3:
        # Incorrect: Reset to 1 day
        next_interval = 1
        ease_factor = max(1.3, ease_factor - 0.2)  # Penalize EF
    else:
        # Correct: Progress through intervals
        if current_interval == 0:  # First time
            next_interval = 1
        elif current_interval == 1:  # After 1 day
            next_interval = 3
        elif current_interval == 3:  # After 3 days
            next_interval = 7
        elif current_interval == 7:  # After 7 days
            next_interval = 14  # Max interval for 60-day prep
        else:
            next_interval = 14  # Cap at 14 days

    # Calculate next review date
    next_review_date = date.today() + timedelta(days=next_interval)

    return next_review_date, next_interval, ease_factor
```

---

### Algorithm 6: Reading Time Estimation

**Purpose:** Estimate reading time for BABOK content chunks

**Formula:** `estimated_minutes = word_count / 200`

**Rationale:** Average adult reading speed is 200-250 words per minute. We use 200 (conservative) to avoid underestimating.

**Pseudocode:**
```python
def estimate_reading_time(word_count: int) -> int:
    """Calculate estimated reading time in minutes."""
    WORDS_PER_MINUTE = 200
    estimated_minutes = word_count / WORDS_PER_MINUTE
    return max(1, round(estimated_minutes))  # Minimum 1 minute
```

**Examples:**
- 400-word chunk → 2 minutes
- 250-word chunk → 1 minute
- 600-word chunk → 3 minutes

---
