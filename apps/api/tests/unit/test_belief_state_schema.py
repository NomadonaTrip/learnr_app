"""
Unit tests for BeliefState Pydantic schemas.
Tests computed properties and schema validation.
"""

from datetime import datetime
from uuid import uuid4

import pytest

from src.schemas.belief_state import (
    CONFIDENCE_THRESHOLD,
    GAP_THRESHOLD,
    MASTERY_THRESHOLD,
    BeliefInitializationStatus,
    BeliefStateBase,
    BeliefStateCreate,
    BeliefStateInDB,
    BeliefStateResponse,
    BeliefStateUpdate,
    BeliefStateWithConcept,
    BeliefStatus,
    BeliefSummary,
    InitializationResult,
)


class TestBeliefStateBase:
    """Tests for BeliefStateBase schema."""

    def test_default_values(self):
        """Test default alpha, beta, and response_count values."""
        schema = BeliefStateBase()

        assert schema.alpha == 1.0
        assert schema.beta == 1.0
        assert schema.response_count == 0

    def test_custom_values(self):
        """Test setting custom values."""
        schema = BeliefStateBase(alpha=5.0, beta=3.0, response_count=10)

        assert schema.alpha == 5.0
        assert schema.beta == 3.0
        assert schema.response_count == 10

    def test_alpha_must_be_positive(self):
        """Test that alpha must be > 0."""
        with pytest.raises(ValueError):
            BeliefStateBase(alpha=0, beta=1.0)

        with pytest.raises(ValueError):
            BeliefStateBase(alpha=-1.0, beta=1.0)

    def test_beta_must_be_positive(self):
        """Test that beta must be > 0."""
        with pytest.raises(ValueError):
            BeliefStateBase(alpha=1.0, beta=0)

        with pytest.raises(ValueError):
            BeliefStateBase(alpha=1.0, beta=-1.0)

    def test_response_count_must_be_non_negative(self):
        """Test that response_count must be >= 0."""
        with pytest.raises(ValueError):
            BeliefStateBase(response_count=-1)


class TestBeliefStateCreate:
    """Tests for BeliefStateCreate schema."""

    def test_requires_user_id_and_concept_id(self):
        """Test that user_id and concept_id are required."""
        user_id = uuid4()
        concept_id = uuid4()

        schema = BeliefStateCreate(user_id=user_id, concept_id=concept_id)

        assert schema.user_id == user_id
        assert schema.concept_id == concept_id
        assert schema.alpha == 1.0  # Default
        assert schema.beta == 1.0  # Default


class TestBeliefStateUpdate:
    """Tests for BeliefStateUpdate schema."""

    def test_all_fields_optional(self):
        """Test that all fields are optional."""
        schema = BeliefStateUpdate()

        assert schema.alpha is None
        assert schema.beta is None
        assert schema.last_response_at is None
        assert schema.response_count is None

    def test_partial_update(self):
        """Test partial update with some fields."""
        schema = BeliefStateUpdate(alpha=2.5, response_count=5)

        assert schema.alpha == 2.5
        assert schema.beta is None
        assert schema.response_count == 5


class TestBeliefStateResponse:
    """Tests for BeliefStateResponse schema with computed properties."""

    @pytest.fixture
    def base_response_data(self):
        """Base data for BeliefStateResponse."""
        return {
            "id": uuid4(),
            "user_id": uuid4(),
            "concept_id": uuid4(),
            "alpha": 1.0,
            "beta": 1.0,
            "response_count": 0,
            "last_response_at": None,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

    def test_mean_calculation_uninformative_prior(self, base_response_data):
        """Test mean calculation for Beta(1,1) = 0.5."""
        schema = BeliefStateResponse(**base_response_data)

        assert schema.mean == 0.5

    def test_mean_calculation_high_mastery(self, base_response_data):
        """Test mean calculation for high mastery."""
        base_response_data["alpha"] = 20.0
        base_response_data["beta"] = 5.0
        schema = BeliefStateResponse(**base_response_data)

        # mean = 20 / (20 + 5) = 0.8
        assert schema.mean == 0.8

    def test_mean_calculation_low_mastery(self, base_response_data):
        """Test mean calculation for low mastery."""
        base_response_data["alpha"] = 2.0
        base_response_data["beta"] = 8.0
        schema = BeliefStateResponse(**base_response_data)

        # mean = 2 / (2 + 8) = 0.2
        assert schema.mean == 0.2

    def test_confidence_calculation_low(self, base_response_data):
        """Test confidence calculation for low confidence (uninformative prior)."""
        schema = BeliefStateResponse(**base_response_data)

        # confidence = 2 / (2 + 2) = 0.5
        assert schema.confidence == 0.5

    def test_confidence_calculation_high(self, base_response_data):
        """Test confidence calculation for high confidence."""
        base_response_data["alpha"] = 50.0
        base_response_data["beta"] = 50.0
        schema = BeliefStateResponse(**base_response_data)

        # confidence = 100 / (100 + 2) = 0.9804
        assert abs(schema.confidence - 0.9804) < 0.001

    def test_status_uncertain_low_confidence(self, base_response_data):
        """Test status is UNCERTAIN when confidence < 0.7."""
        # Beta(1,1): confidence = 2/4 = 0.5 < 0.7
        schema = BeliefStateResponse(**base_response_data)

        assert schema.status == BeliefStatus.UNCERTAIN

    def test_status_mastered(self, base_response_data):
        """Test status is MASTERED when mean >= 0.8 and confidence >= 0.7."""
        base_response_data["alpha"] = 20.0
        base_response_data["beta"] = 2.0
        # mean = 20/22 = 0.909, confidence = 22/24 = 0.917
        schema = BeliefStateResponse(**base_response_data)

        assert schema.status == BeliefStatus.MASTERED

    def test_status_gap(self, base_response_data):
        """Test status is GAP when mean < 0.5 and confidence >= 0.7."""
        base_response_data["alpha"] = 2.0
        base_response_data["beta"] = 20.0
        # mean = 2/22 = 0.091, confidence = 22/24 = 0.917
        schema = BeliefStateResponse(**base_response_data)

        assert schema.status == BeliefStatus.GAP

    def test_status_borderline(self, base_response_data):
        """Test status is BORDERLINE when 0.5 <= mean < 0.8 and confidence >= 0.7."""
        base_response_data["alpha"] = 12.0
        base_response_data["beta"] = 8.0
        # mean = 12/20 = 0.6, confidence = 20/22 = 0.909
        schema = BeliefStateResponse(**base_response_data)

        assert schema.status == BeliefStatus.BORDERLINE

    def test_status_borderline_at_threshold(self, base_response_data):
        """Test status is BORDERLINE at exact mean = 0.5 boundary."""
        base_response_data["alpha"] = 10.0
        base_response_data["beta"] = 10.0
        # mean = 10/20 = 0.5, confidence = 20/22 = 0.909
        schema = BeliefStateResponse(**base_response_data)

        assert schema.status == BeliefStatus.BORDERLINE

    def test_status_mastered_at_threshold(self, base_response_data):
        """Test status is MASTERED at exact mean = 0.8 boundary."""
        base_response_data["alpha"] = 16.0
        base_response_data["beta"] = 4.0
        # mean = 16/20 = 0.8, confidence = 20/22 = 0.909
        schema = BeliefStateResponse(**base_response_data)

        assert schema.status == BeliefStatus.MASTERED

    def test_from_attributes_mode(self, base_response_data):
        """Test that model can be created from ORM attributes."""
        # This tests the model_config = {"from_attributes": True}
        schema = BeliefStateResponse(**base_response_data)
        assert schema.id == base_response_data["id"]


class TestBeliefStateInDB:
    """Tests for BeliefStateInDB schema."""

    def test_inherits_from_response(self):
        """Test that BeliefStateInDB inherits from BeliefStateResponse."""
        data = {
            "id": uuid4(),
            "user_id": uuid4(),
            "concept_id": uuid4(),
            "alpha": 5.0,
            "beta": 2.0,
            "response_count": 10,
            "last_response_at": datetime.now(),
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
        schema = BeliefStateInDB(**data)

        # Should have computed properties from parent
        assert schema.mean is not None
        assert schema.confidence is not None
        assert schema.status is not None


class TestBeliefInitializationStatus:
    """Tests for BeliefInitializationStatus schema."""

    def test_all_fields(self):
        """Test all fields are properly set."""
        schema = BeliefInitializationStatus(
            initialized=True,
            total_concepts=100,
            belief_count=100,
            coverage_percentage=100.0,
            created_at=datetime.now()
        )

        assert schema.initialized is True
        assert schema.total_concepts == 100
        assert schema.belief_count == 100
        assert schema.coverage_percentage == 100.0
        assert schema.created_at is not None

    def test_created_at_optional(self):
        """Test that created_at is optional."""
        schema = BeliefInitializationStatus(
            initialized=False,
            total_concepts=50,
            belief_count=0,
            coverage_percentage=0.0
        )

        assert schema.created_at is None

    def test_coverage_percentage_validation(self):
        """Test coverage_percentage must be 0-100."""
        with pytest.raises(ValueError):
            BeliefInitializationStatus(
                initialized=True,
                total_concepts=100,
                belief_count=100,
                coverage_percentage=150.0  # Invalid
            )

        with pytest.raises(ValueError):
            BeliefInitializationStatus(
                initialized=True,
                total_concepts=100,
                belief_count=100,
                coverage_percentage=-10.0  # Invalid
            )


class TestInitializationResult:
    """Tests for InitializationResult schema."""

    def test_default_values(self):
        """Test default values."""
        schema = InitializationResult(success=True)

        assert schema.success is True
        assert schema.already_initialized is False
        assert schema.belief_count == 0
        assert schema.duration_ms == 0
        assert schema.message == ""

    def test_all_fields(self):
        """Test all fields are properly set."""
        schema = InitializationResult(
            success=True,
            already_initialized=True,
            belief_count=100,
            duration_ms=150.5,
            message="Initialized successfully"
        )

        assert schema.success is True
        assert schema.already_initialized is True
        assert schema.belief_count == 100
        assert schema.duration_ms == 150.5
        assert schema.message == "Initialized successfully"


class TestBeliefSummary:
    """Tests for BeliefSummary schema."""

    def test_all_fields(self):
        """Test all fields are properly set."""
        schema = BeliefSummary(
            user_id=uuid4(),
            course_id=uuid4(),
            total_beliefs=100,
            mastered_count=25,
            gap_count=15,
            borderline_count=30,
            uncertain_count=30,
            average_mean=0.65
        )

        assert schema.total_beliefs == 100
        assert schema.mastered_count == 25
        assert schema.gap_count == 15
        assert schema.borderline_count == 30
        assert schema.uncertain_count == 30
        assert schema.average_mean == 0.65


class TestBeliefStateWithConcept:
    """Tests for BeliefStateWithConcept schema."""

    def test_includes_concept_info(self):
        """Test that concept name and knowledge area are included."""
        data = {
            "id": uuid4(),
            "user_id": uuid4(),
            "concept_id": uuid4(),
            "alpha": 5.0,
            "beta": 2.0,
            "response_count": 10,
            "last_response_at": None,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "concept_name": "Test Concept",
            "concept_knowledge_area_id": "ba-planning"
        }
        schema = BeliefStateWithConcept(**data)

        assert schema.concept_name == "Test Concept"
        assert schema.concept_knowledge_area_id == "ba-planning"
        # Should still have computed properties
        assert schema.mean is not None
        assert schema.status is not None


class TestBeliefStatusEnum:
    """Tests for BeliefStatus enum."""

    def test_enum_values(self):
        """Test enum has expected values."""
        assert BeliefStatus.MASTERED.value == "mastered"
        assert BeliefStatus.GAP.value == "gap"
        assert BeliefStatus.BORDERLINE.value == "borderline"
        assert BeliefStatus.UNCERTAIN.value == "uncertain"

    def test_is_str_enum(self):
        """Test enum values are strings."""
        assert isinstance(BeliefStatus.MASTERED, str)
        assert BeliefStatus.MASTERED == "mastered"


class TestThresholdConstants:
    """Tests for threshold constants."""

    def test_threshold_values(self):
        """Test threshold constants have expected values."""
        assert MASTERY_THRESHOLD == 0.8
        assert GAP_THRESHOLD == 0.5
        assert CONFIDENCE_THRESHOLD == 0.7
