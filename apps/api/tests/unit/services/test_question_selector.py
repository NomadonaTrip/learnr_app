"""
Unit tests for QuestionSelector service.
Tests the Bayesian question selection algorithm including:
- Information gain calculation
- Entropy calculation
- Question filtering
- Selection strategies
"""
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.services.question_selector import QuestionSelector

# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_db():
    """Create mock database session."""
    db = AsyncMock()
    return db


@pytest.fixture
def question_selector(mock_db):
    """Create QuestionSelector with mock database."""
    return QuestionSelector(
        db=mock_db,
        recency_window_days=7,
        prerequisite_weight=0.2,
        min_info_gain_threshold=0.01,
    )


def create_mock_question(
    question_id=None,
    concept_ids=None,
    slip_rate=0.10,
    guess_rate=0.25,
    knowledge_area_id="elicitation",
    difficulty=0.5,
):
    """Helper to create mock Question with QuestionConcept relationships."""
    question = MagicMock()
    question.id = question_id or uuid4()
    question.slip_rate = slip_rate
    question.guess_rate = guess_rate
    question.knowledge_area_id = knowledge_area_id
    question.difficulty = difficulty
    question.question_text = "Mock question"
    question.options = {"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"}

    # Mock question_concepts relationship
    question.question_concepts = []
    if concept_ids:
        for cid in concept_ids:
            qc = MagicMock()
            qc.concept_id = cid
            qc.concept = MagicMock()
            qc.concept.name = f"Concept {cid}"
            question.question_concepts.append(qc)

    return question


def create_mock_belief(concept_id, alpha=1.0, beta=1.0, response_count=0):
    """Helper to create mock BeliefState."""
    belief = MagicMock()
    belief.concept_id = concept_id
    belief.alpha = alpha
    belief.beta = beta
    belief.response_count = response_count

    # Computed properties
    belief.mean = alpha / (alpha + beta)
    total = alpha + beta
    belief.confidence = total / (total + 2)

    # Status based on mean and confidence
    if belief.confidence < 0.7:
        belief.status = "uncertain"
    elif belief.mean >= 0.8:
        belief.status = "mastered"
    elif belief.mean < 0.5:
        belief.status = "gap"
    else:
        belief.status = "borderline"

    return belief


# ============================================================================
# Entropy Calculation Tests (Task 10)
# ============================================================================

class TestBeliefEntropy:
    """Test the Beta distribution entropy calculation."""

    def test_uniform_prior_has_maximum_entropy(self, question_selector):
        """Beta(1,1) uniform prior has differential entropy of 0 (maximum)."""
        entropy = question_selector._belief_entropy(1.0, 1.0)

        # For Beta(1,1): H = ln B(1,1) - 0 - 0 + 0 = 0
        # Differential entropy of uniform on [0,1] is 0
        assert abs(entropy - 0.0) < 0.01

    def test_concentrated_beliefs_have_lower_entropy(self, question_selector):
        """Higher alpha+beta (more observations) = more concentrated = lower (more negative) entropy."""
        entropy_1_1 = question_selector._belief_entropy(1.0, 1.0)
        entropy_10_10 = question_selector._belief_entropy(10.0, 10.0)
        entropy_50_50 = question_selector._belief_entropy(50.0, 50.0)

        # More concentrated = lower (more negative) differential entropy
        assert entropy_10_10 < entropy_1_1  # 10,10 is more concentrated than 1,1
        assert entropy_50_50 < entropy_10_10  # 50,50 is even more concentrated

    def test_asymmetric_beliefs_entropy(self, question_selector):
        """Test entropy for asymmetric distributions."""
        # Strong mastery belief: Beta(9, 1) -> mean = 0.9
        entropy_mastered = question_selector._belief_entropy(9.0, 1.0)

        # Strong non-mastery belief: Beta(1, 9) -> mean = 0.1
        entropy_gap = question_selector._belief_entropy(1.0, 9.0)

        # Both should have same entropy (symmetric property of Beta)
        assert abs(entropy_mastered - entropy_gap) < 0.01

        # Both should have lower entropy than uniform Beta(1,1)
        entropy_uniform = question_selector._belief_entropy(1.0, 1.0)
        assert entropy_mastered < entropy_uniform

    def test_entropy_decreases_with_evidence(self, question_selector):
        """Entropy should decrease as we gather more evidence."""
        entropies = []
        for n in [1, 5, 10, 20, 50]:
            # Keep mean at 0.5 but increase confidence
            entropy = question_selector._belief_entropy(n, n)
            entropies.append(entropy)

        # Should be monotonically decreasing (more negative with more evidence)
        for i in range(1, len(entropies)):
            assert entropies[i] < entropies[i - 1]


# ============================================================================
# Probability Prediction Tests (Task 10)
# ============================================================================

class TestPredictCorrectProbability:
    """Test the slip/guess probability model."""

    def test_high_mastery_high_correct_probability(self, question_selector):
        """High mastery + low slip + low guess -> high P(correct)."""
        concept_id = uuid4()
        belief = create_mock_belief(concept_id, alpha=9.0, beta=1.0)  # mean = 0.9
        beliefs = [belief]

        question = create_mock_question(
            concept_ids=[concept_id],
            slip_rate=0.10,
            guess_rate=0.25,
        )

        p_correct = question_selector._predict_correct_probability(question, beliefs)

        # Expected: (1-0.1)*0.9 + 0.25*(1-0.9) = 0.81 + 0.025 = 0.835
        assert abs(p_correct - 0.835) < 0.01

    def test_low_mastery_lower_correct_probability(self, question_selector):
        """Low mastery should give lower P(correct)."""
        concept_id = uuid4()
        belief = create_mock_belief(concept_id, alpha=1.0, beta=4.0)  # mean = 0.2
        beliefs = [belief]

        question = create_mock_question(
            concept_ids=[concept_id],
            slip_rate=0.10,
            guess_rate=0.25,
        )

        p_correct = question_selector._predict_correct_probability(question, beliefs)

        # Expected: (1-0.1)*0.2 + 0.25*(1-0.2) = 0.18 + 0.2 = 0.38
        assert abs(p_correct - 0.38) < 0.01

    def test_uniform_prior_moderate_probability(self, question_selector):
        """Uniform prior (mean=0.5) gives moderate probability."""
        concept_id = uuid4()
        belief = create_mock_belief(concept_id, alpha=1.0, beta=1.0)  # mean = 0.5
        beliefs = [belief]

        question = create_mock_question(
            concept_ids=[concept_id],
            slip_rate=0.10,
            guess_rate=0.25,
        )

        p_correct = question_selector._predict_correct_probability(question, beliefs)

        # Expected: (1-0.1)*0.5 + 0.25*(1-0.5) = 0.45 + 0.125 = 0.575
        assert abs(p_correct - 0.575) < 0.01

    def test_multiple_concepts_average_mastery(self, question_selector):
        """P(correct) should use average mastery across concepts."""
        cid1, cid2 = uuid4(), uuid4()
        beliefs = [
            create_mock_belief(cid1, alpha=9.0, beta=1.0),  # mean = 0.9
            create_mock_belief(cid2, alpha=1.0, beta=9.0),  # mean = 0.1
        ]

        question = create_mock_question(
            concept_ids=[cid1, cid2],
            slip_rate=0.10,
            guess_rate=0.25,
        )

        p_correct = question_selector._predict_correct_probability(question, beliefs)

        # Average mastery = 0.5
        # Expected: (1-0.1)*0.5 + 0.25*(1-0.5) = 0.575
        assert abs(p_correct - 0.575) < 0.01

    def test_no_beliefs_returns_half(self, question_selector):
        """No beliefs for concepts should return 0.5."""
        question = create_mock_question(concept_ids=[uuid4()])
        p_correct = question_selector._predict_correct_probability(question, [])
        assert p_correct == 0.5


# ============================================================================
# Information Gain Calculation Tests (Task 10)
# ============================================================================

class TestCalculateExpectedInfoGain:
    """Test the expected information gain calculation."""

    def test_uncertain_concept_higher_gain(self, question_selector):
        """Questions testing uncertain concepts should have higher info gain."""
        uncertain_cid = uuid4()
        confident_cid = uuid4()

        # Uncertain concept: Beta(1,1) - high entropy
        uncertain_belief = create_mock_belief(uncertain_cid, alpha=1.0, beta=1.0)

        # Confident concept: Beta(50,50) - low entropy
        confident_belief = create_mock_belief(confident_cid, alpha=50.0, beta=50.0)

        uncertain_question = create_mock_question(concept_ids=[uncertain_cid])
        confident_question = create_mock_question(concept_ids=[confident_cid])

        beliefs = {
            uncertain_cid: uncertain_belief,
            confident_cid: confident_belief,
        }

        gain_uncertain = question_selector._calculate_expected_info_gain(
            uncertain_question, beliefs
        )
        gain_confident = question_selector._calculate_expected_info_gain(
            confident_question, beliefs
        )

        # Uncertain concept should provide more information
        assert gain_uncertain > gain_confident

    def test_info_gain_always_non_negative(self, question_selector):
        """Information gain should always be non-negative."""
        concept_id = uuid4()
        belief = create_mock_belief(concept_id, alpha=5.0, beta=5.0)
        question = create_mock_question(concept_ids=[concept_id])
        beliefs = {concept_id: belief}

        gain = question_selector._calculate_expected_info_gain(question, beliefs)
        assert gain >= 0

    def test_no_concept_beliefs_zero_gain(self, question_selector):
        """If no beliefs match question concepts, gain should be 0."""
        question = create_mock_question(concept_ids=[uuid4()])
        beliefs = {}  # No beliefs

        gain = question_selector._calculate_expected_info_gain(question, beliefs)
        assert gain == 0.0

    def test_multiple_concepts_cumulative_gain(self, question_selector):
        """Questions testing multiple uncertain concepts have higher gain."""
        cid1, cid2 = uuid4(), uuid4()

        beliefs = {
            cid1: create_mock_belief(cid1, alpha=1.0, beta=1.0),
            cid2: create_mock_belief(cid2, alpha=1.0, beta=1.0),
        }

        single_concept_q = create_mock_question(concept_ids=[cid1])
        multi_concept_q = create_mock_question(concept_ids=[cid1, cid2])

        gain_single = question_selector._calculate_expected_info_gain(single_concept_q, beliefs)
        gain_multi = question_selector._calculate_expected_info_gain(multi_concept_q, beliefs)

        # Multi-concept question should generally have higher gain
        assert gain_multi >= gain_single


# ============================================================================
# Simulate Update Tests (Task 10)
# ============================================================================

class TestSimulateUpdate:
    """Test the belief update simulation."""

    def test_correct_answer_increases_alpha(self, question_selector):
        """Correct answer should increase posterior mastery."""
        concept_id = uuid4()
        belief = create_mock_belief(concept_id, alpha=1.0, beta=1.0)

        updated = question_selector._simulate_update(
            [belief],
            is_correct=True,
            slip=0.10,
            guess=0.25,
        )

        new_alpha, new_beta = updated[0]
        # Alpha should increase more than beta for correct answer
        assert new_alpha > belief.alpha
        assert new_alpha - 1.0 > new_beta - 1.0

    def test_incorrect_answer_increases_beta(self, question_selector):
        """Incorrect answer should decrease posterior mastery."""
        concept_id = uuid4()
        belief = create_mock_belief(concept_id, alpha=1.0, beta=1.0)

        updated = question_selector._simulate_update(
            [belief],
            is_correct=False,
            slip=0.10,
            guess=0.25,
        )

        new_alpha, new_beta = updated[0]
        # Beta should increase more than alpha for incorrect answer
        assert new_beta > belief.beta
        assert new_beta - 1.0 > new_alpha - 1.0


# ============================================================================
# Filtering Tests (Task 11)
# ============================================================================

class TestFilterByKnowledgeArea:
    """Test knowledge area filtering."""

    def test_filters_to_matching_ka(self, question_selector):
        """Should return only questions matching knowledge area."""
        q1 = create_mock_question(knowledge_area_id="elicitation")
        q2 = create_mock_question(knowledge_area_id="planning")
        q3 = create_mock_question(knowledge_area_id="elicitation")
        questions = [q1, q2, q3]

        filtered = question_selector._filter_by_knowledge_area(questions, "elicitation")

        assert len(filtered) == 2
        assert all(q.knowledge_area_id == "elicitation" for q in filtered)

    def test_returns_empty_when_no_match(self, question_selector):
        """Should return empty list if no questions match."""
        q1 = create_mock_question(knowledge_area_id="planning")
        q2 = create_mock_question(knowledge_area_id="strategy")
        questions = [q1, q2]

        filtered = question_selector._filter_by_knowledge_area(questions, "elicitation")

        assert len(filtered) == 0


class TestRecentQuestionFilter:
    """Test recency filtering."""

    @pytest.mark.asyncio
    async def test_excludes_recent_questions(self, question_selector, mock_db):
        """Questions answered within recency window should be excluded."""
        user_id = uuid4()
        recent_qid = uuid4()
        old_qid = uuid4()

        # Mock database returning recent question ID
        mock_result = MagicMock()
        mock_result.all.return_value = [(recent_qid,)]
        mock_db.execute.return_value = mock_result

        recent_ids = await question_selector._get_recent_question_ids(user_id, 7)

        assert recent_qid in recent_ids
        assert old_qid not in recent_ids


class TestSessionQuestionFilter:
    """Test session filtering."""

    @pytest.mark.asyncio
    async def test_excludes_session_questions(self, question_selector, mock_db):
        """Questions already in session should be excluded."""
        session_id = uuid4()
        answered_qid = uuid4()

        # Mock database returning session question ID
        mock_result = MagicMock()
        mock_result.all.return_value = [(answered_qid,)]
        mock_db.execute.return_value = mock_result

        session_ids = await question_selector._get_session_question_ids(session_id)

        assert answered_qid in session_ids


# ============================================================================
# Selection Strategy Tests (Task 12)
# ============================================================================

class TestSelectByInfoGain:
    """Test max information gain selection strategy."""

    def test_selects_highest_info_gain(self, question_selector):
        """Should select question with highest information gain."""
        # Create questions with different concept entropies
        high_uncertainty_cid = uuid4()
        low_uncertainty_cid = uuid4()

        beliefs = {
            high_uncertainty_cid: create_mock_belief(high_uncertainty_cid, alpha=1.0, beta=1.0),
            low_uncertainty_cid: create_mock_belief(low_uncertainty_cid, alpha=50.0, beta=50.0),
        }

        q_high_gain = create_mock_question(concept_ids=[high_uncertainty_cid])
        q_low_gain = create_mock_question(concept_ids=[low_uncertainty_cid])
        candidates = [q_low_gain, q_high_gain]  # Low gain first

        selected, info_gain = question_selector._select_by_info_gain(candidates, beliefs)

        # Should select high uncertainty question (higher info gain)
        assert selected.id == q_high_gain.id
        assert info_gain > 0

    def test_raises_on_empty_candidates(self, question_selector):
        """Should raise ValueError with empty candidate list."""
        with pytest.raises(ValueError, match="No question could be selected"):
            question_selector._select_by_info_gain([], {})


class TestSelectByUncertainty:
    """Test max uncertainty selection strategy (fallback)."""

    def test_selects_most_uncertain(self, question_selector):
        """Should select question testing most uncertain concepts."""
        uncertain_cid = uuid4()
        confident_cid = uuid4()

        beliefs = {
            uncertain_cid: create_mock_belief(uncertain_cid, alpha=1.0, beta=1.0),
            confident_cid: create_mock_belief(confident_cid, alpha=50.0, beta=50.0),
        }

        q_uncertain = create_mock_question(concept_ids=[uncertain_cid])
        q_confident = create_mock_question(concept_ids=[confident_cid])
        candidates = [q_confident, q_uncertain]

        selected, entropy = question_selector._select_by_uncertainty(candidates, beliefs)

        # Should select uncertain concept question (higher entropy = less concentrated)
        assert selected.id == q_uncertain.id

        # Entropy of Beta(1,1) is 0 (maximum), so the selected one should have higher entropy
        # than the confident one (Beta(50,50) which has negative entropy)
        entropy_confident = question_selector._belief_entropy(50.0, 50.0)
        assert entropy > entropy_confident


class TestPrerequisiteBonus:
    """Test prerequisite bonus application."""

    def test_applies_bonus_for_uncertain_concepts(self, question_selector):
        """Uncertain concepts should get prerequisite bonus."""
        uncertain_cid = uuid4()
        beliefs = {
            uncertain_cid: create_mock_belief(uncertain_cid, alpha=1.0, beta=1.0),
        }
        # Force status to uncertain
        beliefs[uncertain_cid].status = "uncertain"

        question = create_mock_question(concept_ids=[uncertain_cid])
        base_gain = 0.5

        boosted_gain = question_selector._apply_prerequisite_bonus(
            question, beliefs, base_gain
        )

        # Should be higher than base
        assert boosted_gain > base_gain

    def test_no_bonus_for_mastered_concepts(self, question_selector):
        """Mastered concepts should not get bonus."""
        mastered_cid = uuid4()
        beliefs = {
            mastered_cid: create_mock_belief(mastered_cid, alpha=9.0, beta=1.0),
        }
        beliefs[mastered_cid].status = "mastered"

        question = create_mock_question(concept_ids=[mastered_cid])
        base_gain = 0.5

        result_gain = question_selector._apply_prerequisite_bonus(
            question, beliefs, base_gain
        )

        # Should be same as base (no bonus)
        assert result_gain == base_gain


# ============================================================================
# Full Selection Flow Tests (Task 12)
# ============================================================================

class TestSelectNextQuestion:
    """Test the complete question selection flow."""

    @pytest.mark.asyncio
    async def test_applies_all_filters(self, question_selector, mock_db):
        """Selection should apply all filtering constraints."""
        user_id = uuid4()
        session_id = uuid4()
        cid = uuid4()

        # Set up questions
        questions = [
            create_mock_question(concept_ids=[cid], knowledge_area_id="elicitation")
            for _ in range(3)
        ]

        beliefs = {cid: create_mock_belief(cid, alpha=1.0, beta=1.0)}

        # Mock empty recent/session questions
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_db.execute.return_value = mock_result

        question, info_gain = await question_selector.select_next_question(
            user_id=user_id,
            session_id=session_id,
            beliefs=beliefs,
            available_questions=questions,
            strategy="max_info_gain",
            knowledge_area_filter=None,
        )

        assert question is not None
        assert info_gain >= 0

    @pytest.mark.asyncio
    async def test_raises_when_no_candidates(self, question_selector, mock_db):
        """Should raise ValueError when no questions pass filters."""
        user_id = uuid4()
        session_id = uuid4()

        # Mock empty result
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_db.execute.return_value = mock_result

        with pytest.raises(ValueError, match="No eligible questions"):
            await question_selector.select_next_question(
                user_id=user_id,
                session_id=session_id,
                beliefs={},
                available_questions=[],
                strategy="max_info_gain",
            )

    @pytest.mark.asyncio
    async def test_falls_back_to_uncertainty_when_low_gain(self, question_selector, mock_db):
        """Should fall back to uncertainty strategy when info gain is low."""
        user_id = uuid4()
        session_id = uuid4()
        cid = uuid4()

        # High confidence = low info gain
        beliefs = {cid: create_mock_belief(cid, alpha=100.0, beta=100.0)}
        questions = [create_mock_question(concept_ids=[cid])]

        # Mock empty filter results
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_db.execute.return_value = mock_result

        # Set very high threshold to trigger fallback
        question_selector.min_info_gain_threshold = 10.0

        # Should still return a question even when info gain is below threshold
        # The fallback to uncertainty strategy handles this
        question, gain = await question_selector.select_next_question(
            user_id=user_id,
            session_id=session_id,
            beliefs=beliefs,
            available_questions=questions,
            strategy="max_info_gain",
        )

        # Should still return a question via fallback
        assert question is not None

    @pytest.mark.asyncio
    async def test_respects_knowledge_area_filter(self, question_selector, mock_db):
        """Should filter questions by knowledge area when specified."""
        user_id = uuid4()
        session_id = uuid4()
        cid = uuid4()

        q_elicit = create_mock_question(concept_ids=[cid], knowledge_area_id="elicitation")
        q_plan = create_mock_question(concept_ids=[cid], knowledge_area_id="planning")
        questions = [q_elicit, q_plan]

        beliefs = {cid: create_mock_belief(cid)}

        # Mock empty filter results
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_db.execute.return_value = mock_result

        question, _ = await question_selector.select_next_question(
            user_id=user_id,
            session_id=session_id,
            beliefs=beliefs,
            available_questions=questions,
            strategy="max_info_gain",
            knowledge_area_filter="elicitation",
        )

        assert question.knowledge_area_id == "elicitation"
