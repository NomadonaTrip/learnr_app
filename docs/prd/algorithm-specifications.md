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

### Algorithm 7: User Ability Classification per Concept

**Purpose:** Classify a user's demonstrated ability level for a specific concept based on their response history across difficulty levels. This is distinct from BKT mastery probability—BKT answers "Do they know it?" while ability classification answers "At what difficulty level can they demonstrate it?"

**Trigger:** Before question selection, to determine appropriate difficulty distribution

**Parameters:**
- `user_id`: UUID of user
- `concept_id`: UUID of concept
- `belief_state`: User's current belief state for this concept (from BKT)
- `response_history`: User's past responses on this concept with difficulty levels

**Returns:** `'novice'` | `'intermediate'` | `'expert'`

**Classification Logic:**

The ability level is determined by combining:
1. **BKT Mastery Probability** - Overall likelihood of concept mastery
2. **Difficulty Performance** - Success rate at each difficulty tier
3. **Response Volume** - Confidence based on sample size

**Pseudocode:**
```python
from dataclasses import dataclass
from typing import Literal
from uuid import UUID

AbilityLevel = Literal['novice', 'intermediate', 'expert']

@dataclass
class DifficultyPerformance:
    easy_correct: int = 0
    easy_total: int = 0
    medium_correct: int = 0
    medium_total: int = 0
    hard_correct: int = 0
    hard_total: int = 0

    @property
    def easy_accuracy(self) -> float:
        return self.easy_correct / self.easy_total if self.easy_total > 0 else 0.0

    @property
    def medium_accuracy(self) -> float:
        return self.medium_correct / self.medium_total if self.medium_total > 0 else 0.0

    @property
    def hard_accuracy(self) -> float:
        return self.hard_correct / self.hard_total if self.hard_total > 0 else 0.0


# Classification thresholds (configurable for A/B testing)
ABILITY_THRESHOLDS = {
    # BKT mastery probability thresholds
    "mastery_novice_max": 0.4,       # Below this → likely novice
    "mastery_expert_min": 0.7,       # Above this → possibly expert

    # Minimum correct answers at difficulty level to demonstrate competence
    "medium_competence_min": 3,      # Need 3+ correct at medium to be intermediate
    "hard_competence_min": 3,        # Need 3+ correct at hard to be expert

    # Accuracy thresholds
    "medium_accuracy_min": 0.6,      # 60%+ accuracy at medium for intermediate
    "hard_accuracy_min": 0.5,        # 50%+ accuracy at hard for expert

    # Minimum responses for confident classification
    "min_responses_for_upgrade": 5,
}


def classify_user_ability(
    user_id: UUID,
    concept_id: UUID,
    mastery_probability: float,
    performance: DifficultyPerformance
) -> AbilityLevel:
    """
    Classify user's ability level for a concept.

    Classification Rules (in order of precedence):

    EXPERT if:
      - Mastery probability ≥ 0.7 AND
      - At least 3 correct answers at Hard difficulty AND
      - Hard accuracy ≥ 50%

    INTERMEDIATE if:
      - Mastery probability ≥ 0.4 AND
      - At least 3 correct answers at Medium difficulty AND
      - Medium accuracy ≥ 60%

    NOVICE otherwise (default for new users or struggling learners)
    """

    thresholds = ABILITY_THRESHOLDS

    # Check for Expert level
    if (mastery_probability >= thresholds["mastery_expert_min"] and
        performance.hard_correct >= thresholds["hard_competence_min"] and
        performance.hard_accuracy >= thresholds["hard_accuracy_min"]):
        return 'expert'

    # Check for Intermediate level
    if (mastery_probability >= thresholds["mastery_novice_max"] and
        performance.medium_correct >= thresholds["medium_competence_min"] and
        performance.medium_accuracy >= thresholds["medium_accuracy_min"]):
        return 'intermediate'

    # Default to Novice
    return 'novice'


def get_difficulty_performance(
    user_id: UUID,
    concept_id: UUID
) -> DifficultyPerformance:
    """
    Retrieve user's performance breakdown by difficulty level for a concept.

    Queries quiz_responses joined with questions to aggregate performance.
    """
    # Query all responses for this user-concept pair
    responses = db.query(QuizResponse).join(Question).filter(
        QuizResponse.user_id == user_id,
        Question.concept_ids.contains([concept_id])
    ).all()

    performance = DifficultyPerformance()

    for response in responses:
        difficulty = response.question.difficulty

        if difficulty < 0.4:  # Easy
            performance.easy_total += 1
            if response.is_correct:
                performance.easy_correct += 1
        elif difficulty < 0.7:  # Medium
            performance.medium_total += 1
            if response.is_correct:
                performance.medium_correct += 1
        else:  # Hard (≥ 0.7)
            performance.hard_total += 1
            if response.is_correct:
                performance.hard_correct += 1

    return performance
```

**Self-Reported Level Bootstrapping:**

For new users with no response history, use self-reported familiarity from onboarding (Story 3.2):

```python
FAMILIARITY_TO_ABILITY = {
    'new': 'novice',
    'basics': 'novice',
    'intermediate': 'intermediate',
    'expert': 'expert'
}

def get_initial_ability_level(user_id: UUID, concept_id: UUID) -> AbilityLevel:
    """
    Get ability level for a user with no response history.
    Falls back to self-reported familiarity from onboarding.
    """
    user = get_user(user_id)

    if user.familiarity:
        return FAMILIARITY_TO_ABILITY.get(user.familiarity, 'novice')

    return 'novice'  # Default for completely new users
```

**Ability Level Transitions:**

| From | To | Trigger |
|------|-----|---------|
| Novice | Intermediate | 3+ correct at Medium with 60%+ accuracy |
| Intermediate | Expert | 3+ correct at Hard with 50%+ accuracy, P(mastery) ≥ 0.7 |
| Expert | Intermediate | P(mastery) drops below 0.5 OR Hard accuracy drops below 40% |
| Intermediate | Novice | P(mastery) drops below 0.3 OR Medium accuracy drops below 40% |

---

### Algorithm 8: IRT Difficulty Distribution Selection

**Purpose:** Select question difficulty probabilistically based on user's demonstrated ability level for a specific concept. This ensures users receive an appropriate mix of challenge levels—not too easy (boredom) and not too hard (frustration).

**Trigger:** During question selection (Algorithm 4), after target concept is identified

**Parameters:**
- `user_ability_level`: The user's classified ability level for the target concept (`'novice'` | `'intermediate'` | `'expert'`)
- `available_questions`: List of questions for the target concept, with difficulty values

**Returns:** Selected question at appropriate difficulty level

**Difficulty Distribution Matrix:**

This matrix defines the probability of selecting each difficulty tier based on user ability level:

```python
# Core difficulty distribution configuration
# Keys: ability level, Values: probability weights for [easy, medium, hard]
DIFFICULTY_DISTRIBUTION = {
    'novice': {
        'easy': 0.70,      # 70% easy questions
        'medium': 0.25,    # 25% medium questions
        'hard': 0.05       # 5% hard questions (exposure, not mastery)
    },
    'intermediate': {
        'easy': 0.40,      # 40% easy (reinforcement)
        'medium': 0.40,    # 40% medium (core learning zone)
        'hard': 0.20       # 20% hard (stretch challenges)
    },
    'expert': {
        'easy': 0.10,      # 10% easy (quick wins, confidence)
        'medium': 0.40,    # 40% medium (maintain fluency)
        'hard': 0.50       # 50% hard (primary challenge)
    }
}

# Difficulty tier boundaries (question difficulty 0.0-1.0)
DIFFICULTY_TIERS = {
    'easy': (0.0, 0.4),      # Questions with difficulty < 0.4
    'medium': (0.4, 0.7),    # Questions with difficulty 0.4-0.7
    'hard': (0.7, 1.0)       # Questions with difficulty ≥ 0.7
}
```

**Design Rationale:**

| Level | Easy | Medium | Hard | Rationale |
|-------|------|--------|------|-----------|
| Novice | 70% | 25% | 5% | Build confidence with achievable challenges; occasional stretch prevents ceiling effect |
| Intermediate | 40% | 40% | 20% | Balanced mix; medium is the learning zone; hard introduces advanced concepts |
| Expert | 10% | 40% | 50% | Primary focus on hard questions; medium maintains breadth; easy for quick reinforcement |

**Pseudocode:**

```python
import random
from typing import List, Optional
from uuid import UUID

@dataclass
class Question:
    id: UUID
    difficulty: float  # 0.0-1.0
    concept_ids: List[UUID]
    # ... other fields


def select_difficulty_tier(ability_level: AbilityLevel) -> str:
    """
    Probabilistically select a difficulty tier based on ability level.

    Uses weighted random selection based on DIFFICULTY_DISTRIBUTION.
    """
    distribution = DIFFICULTY_DISTRIBUTION[ability_level]

    # Weighted random choice
    rand = random.random()
    cumulative = 0.0

    for tier, probability in distribution.items():
        cumulative += probability
        if rand < cumulative:
            return tier

    return 'medium'  # Fallback (should never reach)


def get_questions_in_tier(
    questions: List[Question],
    tier: str
) -> List[Question]:
    """
    Filter questions to those within a difficulty tier.
    """
    min_diff, max_diff = DIFFICULTY_TIERS[tier]

    return [
        q for q in questions
        if min_diff <= q.difficulty < max_diff
    ]


def select_question_by_irt(
    user_id: UUID,
    concept_id: UUID,
    available_questions: List[Question],
    ability_level: Optional[AbilityLevel] = None
) -> Question:
    """
    Select a question using IRT-based difficulty distribution.

    Steps:
    1. Classify user ability for concept (if not provided)
    2. Sample difficulty tier from distribution
    3. Filter questions to tier
    4. Select randomly from filtered set
    5. Fallback to adjacent tier if no questions available

    Args:
        user_id: User identifier
        concept_id: Target concept
        available_questions: Pre-filtered questions for the concept
        ability_level: Optional pre-computed ability level

    Returns:
        Selected question at appropriate difficulty
    """

    # Step 1: Get ability level if not provided
    if ability_level is None:
        belief_state = get_belief_state(user_id, concept_id)
        performance = get_difficulty_performance(user_id, concept_id)

        if performance.easy_total + performance.medium_total + performance.hard_total == 0:
            # No history - use self-reported level
            ability_level = get_initial_ability_level(user_id, concept_id)
        else:
            ability_level = classify_user_ability(
                user_id, concept_id,
                mastery_probability=belief_state.mean,
                performance=performance
            )

    # Step 2: Sample difficulty tier
    target_tier = select_difficulty_tier(ability_level)

    # Step 3: Filter questions to tier
    tier_questions = get_questions_in_tier(available_questions, target_tier)

    # Step 4: Fallback logic if tier is empty
    if not tier_questions:
        tier_questions = _fallback_tier_selection(
            available_questions, target_tier, ability_level
        )

    # Step 5: Random selection from tier
    if tier_questions:
        return random.choice(tier_questions)

    # Ultimate fallback: any question
    if available_questions:
        return random.choice(available_questions)

    raise NoQuestionsAvailableError(f"No questions available for concept {concept_id}")


def _fallback_tier_selection(
    questions: List[Question],
    original_tier: str,
    ability_level: AbilityLevel
) -> List[Question]:
    """
    Fallback tier selection when original tier has no questions.

    Strategy:
    - Novice: Prefer medium over hard
    - Intermediate: Prefer adjacent tier with more questions
    - Expert: Prefer medium over easy
    """
    tier_order = {
        'novice': ['medium', 'hard'],       # If no easy, try medium, then hard
        'intermediate': ['easy', 'hard'],   # If no medium, try easy, then hard
        'expert': ['medium', 'easy']        # If no hard, try medium, then easy
    }

    for fallback_tier in tier_order[ability_level]:
        fallback_questions = get_questions_in_tier(questions, fallback_tier)
        if fallback_questions:
            return fallback_questions

    return []  # No questions in any tier


def log_selection_rationale(
    user_id: UUID,
    concept_id: UUID,
    ability_level: AbilityLevel,
    selected_tier: str,
    question_id: UUID,
    was_fallback: bool
):
    """
    Log question selection for debugging and analytics.
    """
    log.info(
        "IRT question selection",
        user_id=str(user_id),
        concept_id=str(concept_id),
        ability_level=ability_level,
        target_tier=selected_tier,
        question_id=str(question_id),
        was_fallback=was_fallback,
        distribution=DIFFICULTY_DISTRIBUTION[ability_level]
    )
```

**Integration with Question Selector (Algorithm 4):**

The IRT difficulty selection integrates into the existing question selection flow:

```python
def select_next_question(
    user_id: UUID,
    session_id: UUID,
    target_ka_id: Optional[UUID] = None,
    target_concept_id: Optional[UUID] = None
) -> Question:
    """
    Enhanced question selection with IRT difficulty distribution.
    """

    # Step 1: Determine target concept (existing logic)
    if target_concept_id:
        concept_id = target_concept_id
    else:
        # Use BKT to find highest information gain concept
        concept_id = select_concept_by_info_gain(user_id, target_ka_id)

    # Step 2: Get available questions for concept
    available_questions = get_questions_for_concept(
        concept_id=concept_id,
        exclude_recent=True,
        user_id=user_id
    )

    # Step 3: Apply IRT difficulty selection (NEW)
    selected_question = select_question_by_irt(
        user_id=user_id,
        concept_id=concept_id,
        available_questions=available_questions
    )

    return selected_question
```

**Example Scenarios:**

| User State | Ability | Distribution Applied | Likely Outcome |
|------------|---------|---------------------|----------------|
| New user, self-reported "new" | Novice | 70/25/5 | Easy question |
| 5 correct at medium, P(mastery)=0.5 | Intermediate | 40/40/20 | Medium or Easy |
| 4 correct at hard, P(mastery)=0.8 | Expert | 10/40/50 | Hard question |
| Expert struggling (3 recent failures) | Intermediate* | 40/40/20 | Medium question |

*Ability level downgrades when performance drops.

**Performance Considerations:**

- Ability classification: O(n) where n = response count for concept (typically <50)
- Tier selection: O(1) - simple random selection
- Question filtering: O(q) where q = available questions (typically <20 per concept)
- **Total added latency:** <10ms (negligible impact on 200ms selection target)

**Configuration for A/B Testing:**

```python
# Feature flag for gradual rollout
IRT_DIFFICULTY_ENABLED = config.get("IRT_DIFFICULTY_ENABLED", True)

# Alternative distributions for A/B testing
DIFFICULTY_DISTRIBUTION_VARIANTS = {
    "control": {  # Current behavior (no distribution)
        'novice': {'easy': 0.33, 'medium': 0.34, 'hard': 0.33},
        'intermediate': {'easy': 0.33, 'medium': 0.34, 'hard': 0.33},
        'expert': {'easy': 0.33, 'medium': 0.34, 'hard': 0.33}
    },
    "aggressive": {  # More polarized distribution
        'novice': {'easy': 0.80, 'medium': 0.15, 'hard': 0.05},
        'intermediate': {'easy': 0.30, 'medium': 0.50, 'hard': 0.20},
        'expert': {'easy': 0.05, 'medium': 0.35, 'hard': 0.60}
    }
}
```

**Success Metrics:**

| Metric | Target | Measurement |
|--------|--------|-------------|
| Difficulty-appropriate accuracy | 60-80% per tier | Accuracy within expected range for ability level |
| Engagement (session length) | +15% vs control | Users stay longer when appropriately challenged |
| Frustration signal (consecutive failures) | <10% sessions | Fewer stuck-student interventions triggered |
| Boredom signal (skip rate) | <5% | Users don't skip questions due to being too easy |

---

### Algorithm 9: Combined BKT-IRT Question Selection

**Purpose:** Orchestrate the complete adaptive question selection process, combining BKT (concept targeting via information gain) with IRT (difficulty targeting via ability-based distribution).

**Trigger:** When user requests next question in adaptive quiz session

**Architecture:**

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    ADAPTIVE QUESTION SELECTION FLOW                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                     BKT LAYER (What to teach)                   │   │
│  │                                                                 │   │
│  │  1. Get all concept belief states for user                     │   │
│  │  2. Calculate information gain for each concept                │   │
│  │  3. Apply prerequisite weighting                               │   │
│  │  4. Apply intervention deprioritization (Story 5.11)           │   │
│  │  5. Select concept with highest adjusted info gain             │   │
│  │                                                                 │   │
│  │  Output: target_concept_id                                     │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                              │                                          │
│                              ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    IRT LAYER (How hard to teach)                │   │
│  │                                                                 │   │
│  │  1. Get user's response history for target concept             │   │
│  │  2. Classify ability level (novice/intermediate/expert)        │   │
│  │  3. Sample difficulty tier from distribution                   │   │
│  │  4. Filter questions to tier                                   │   │
│  │  5. Apply freshness filter (exclude recent questions)          │   │
│  │  6. Random selection from filtered pool                        │   │
│  │                                                                 │   │
│  │  Output: selected_question                                     │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                              │                                          │
│                              ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      RESPONSE FLOW                              │   │
│  │                                                                 │   │
│  │  User answers → BKT updates belief state                       │   │
│  │              → IRT updates difficulty performance              │   │
│  │              → Next question selection repeats                 │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Complete Pseudocode:**

```python
def select_next_adaptive_question(
    user_id: UUID,
    session_id: UUID,
    session_type: str = 'adaptive',
    target_ka_id: Optional[UUID] = None,
    target_concept_ids: Optional[List[UUID]] = None
) -> QuestionSelectionResult:
    """
    Master orchestration for adaptive question selection.

    Combines BKT (concept selection) with IRT (difficulty selection).

    Args:
        user_id: User identifier
        session_id: Current quiz session
        session_type: 'adaptive' | 'focused_ka' | 'focused_concept' | 'review'
        target_ka_id: Optional KA filter for focused sessions
        target_concept_ids: Optional concept filter for focused sessions

    Returns:
        QuestionSelectionResult with selected question and metadata
    """

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 1: BKT - SELECT TARGET CONCEPT
    # ═══════════════════════════════════════════════════════════════════

    # Get all belief states for user
    belief_states = get_all_belief_states(user_id)

    # Apply session filters
    candidate_concepts = get_candidate_concepts(
        session_type=session_type,
        target_ka_id=target_ka_id,
        target_concept_ids=target_concept_ids
    )

    # Calculate information gain for each candidate concept
    concept_scores = []
    for concept_id in candidate_concepts:
        belief = belief_states.get(concept_id, get_default_belief())

        # Base score: information gain
        info_gain = calculate_expected_info_gain(belief)

        # Prerequisite bonus: prefer concepts where prereqs are mastered
        prereq_bonus = calculate_prerequisite_bonus(user_id, concept_id, belief_states)

        # Intervention penalty: deprioritize if stuck and unread materials exist
        intervention_penalty = calculate_intervention_penalty(user_id, concept_id)

        adjusted_score = info_gain + prereq_bonus - intervention_penalty

        concept_scores.append((concept_id, adjusted_score, info_gain))

    # Select concept with highest adjusted score
    concept_scores.sort(key=lambda x: x[1], reverse=True)
    target_concept_id = concept_scores[0][0]
    expected_info_gain = concept_scores[0][2]

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 2: IRT - SELECT QUESTION AT APPROPRIATE DIFFICULTY
    # ═══════════════════════════════════════════════════════════════════

    # Get available questions for concept
    available_questions = get_questions_for_concept(
        concept_id=target_concept_id,
        user_id=user_id,
        exclude_session_questions=session_id,
        exclude_recent_days=7
    )

    if not available_questions:
        # Fallback: expand to related concepts
        available_questions = get_questions_for_related_concepts(
            concept_id=target_concept_id,
            user_id=user_id
        )

    # Classify user ability for this concept
    belief = belief_states.get(target_concept_id, get_default_belief())
    performance = get_difficulty_performance(user_id, target_concept_id)

    if performance.total_responses == 0:
        ability_level = get_initial_ability_level(user_id, target_concept_id)
    else:
        ability_level = classify_user_ability(
            user_id, target_concept_id,
            mastery_probability=belief.mean,
            performance=performance
        )

    # Select question using IRT distribution
    selected_question = select_question_by_irt(
        user_id=user_id,
        concept_id=target_concept_id,
        available_questions=available_questions,
        ability_level=ability_level
    )

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 3: PREPARE RESPONSE
    # ═══════════════════════════════════════════════════════════════════

    # Log selection for debugging
    log_selection_rationale(
        user_id=user_id,
        concept_id=target_concept_id,
        ability_level=ability_level,
        selected_tier=get_difficulty_tier(selected_question.difficulty),
        question_id=selected_question.id,
        expected_info_gain=expected_info_gain
    )

    return QuestionSelectionResult(
        question=selected_question,
        concept_id=target_concept_id,
        expected_info_gain=expected_info_gain,
        ability_level=ability_level,
        selection_rationale={
            "concept_selection": "max_info_gain",
            "difficulty_selection": f"irt_{ability_level}",
            "distribution_applied": DIFFICULTY_DISTRIBUTION[ability_level]
        }
    )
```

**Summary of Algorithm Responsibilities:**

| Algorithm | Layer | Responsibility | Key Question Answered |
|-----------|-------|----------------|----------------------|
| **BKT (4.2, 4.4)** | Concept | Track mastery probability | "Do they know this concept?" |
| **Algorithm 7** | Ability | Classify ability per concept | "At what level can they demonstrate mastery?" |
| **Algorithm 8** | Difficulty | Select appropriate difficulty | "What difficulty should the next question be?" |
| **Algorithm 9** | Orchestration | Combine BKT + IRT | "What is the optimal next question?" |

---
