"""
Unit tests for User Pydantic schemas.
Tests validation logic for UserCreate, UserUpdate, and UserResponse schemas.
"""
from datetime import date, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.schemas.user import OnboardingData, UserCreate, UserResponse, UserUpdate


class TestUserCreateSchema:
    """Tests for UserCreate schema validation."""

    def test_valid_user_create(self):
        """Test creating a valid user schema."""
        user_data = {
            "email": "test@example.com",
            "password": "Password123"
        }
        user = UserCreate(**user_data)
        assert user.email == "test@example.com"
        assert user.password == "Password123"

    def test_email_validation_invalid_format(self):
        """Test that invalid email format raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(email="invalid-email", password="Password123")

        errors = exc_info.value.errors()
        assert any(error["type"] == "value_error" for error in errors)

    def test_password_too_short(self):
        """Test that password shorter than 8 characters is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(email="test@example.com", password="Pass123")

        errors = exc_info.value.errors()
        assert any("at least 8 characters" in str(error["ctx"]["error"]) for error in errors)

    def test_password_no_letter(self):
        """Test that password without letters is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(email="test@example.com", password="12345678")

        errors = exc_info.value.errors()
        assert any("at least one letter" in str(error["ctx"]["error"]) for error in errors)

    def test_password_no_number(self):
        """Test that password without numbers is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(email="test@example.com", password="Password")

        errors = exc_info.value.errors()
        assert any("at least one number" in str(error["ctx"]["error"]) for error in errors)

    def test_password_minimum_valid(self):
        """Test that minimum valid password (8 chars, 1 letter, 1 number) works."""
        user = UserCreate(email="test@example.com", password="Pass1234")
        assert user.password == "Pass1234"

    def test_user_create_with_onboarding_data(self):
        """Test UserCreate with optional onboarding_data (Story 3.4.1)."""
        user_data = {
            "email": "test@example.com",
            "password": "Password123",
            "onboarding_data": {
                "course": "business-analysis",
                "motivation": "certification",
                "familiarity": "basics",
                "initial_belief_prior": 0.3
            }
        }
        user = UserCreate(**user_data)
        assert user.email == "test@example.com"
        assert user.onboarding_data is not None
        assert user.onboarding_data.course == "business-analysis"
        assert user.onboarding_data.familiarity == "basics"
        assert user.onboarding_data.initial_belief_prior == 0.3

    def test_user_create_without_onboarding_data(self):
        """Test UserCreate without onboarding_data (legacy registration)."""
        user = UserCreate(email="test@example.com", password="Password123")
        assert user.email == "test@example.com"
        assert user.onboarding_data is None


class TestOnboardingDataSchema:
    """Tests for OnboardingData schema validation (Story 3.4.1)."""

    def test_valid_onboarding_data(self):
        """Test creating valid onboarding data."""
        data = OnboardingData(
            course="business-analysis",
            motivation="certification",
            familiarity="basics",
            initial_belief_prior=0.3
        )
        assert data.course == "business-analysis"
        assert data.motivation == "certification"
        assert data.familiarity == "basics"
        assert data.initial_belief_prior == 0.3

    def test_valid_familiarity_new(self):
        """Test familiarity='new' with prior 0.1."""
        data = OnboardingData(
            course="cbap",
            motivation="learning",
            familiarity="new",
            initial_belief_prior=0.1
        )
        assert data.familiarity == "new"
        assert data.initial_belief_prior == 0.1

    def test_valid_familiarity_intermediate(self):
        """Test familiarity='intermediate' with prior 0.5."""
        data = OnboardingData(
            course="cbap",
            motivation="career",
            familiarity="intermediate",
            initial_belief_prior=0.5
        )
        assert data.familiarity == "intermediate"

    def test_valid_familiarity_expert(self):
        """Test familiarity='expert' with prior 0.7."""
        data = OnboardingData(
            course="cbap",
            motivation="review",
            familiarity="expert",
            initial_belief_prior=0.7
        )
        assert data.familiarity == "expert"

    def test_invalid_familiarity_value(self):
        """Test that invalid familiarity value raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            OnboardingData(
                course="cbap",
                motivation="learning",
                familiarity="advanced",  # Invalid: should be new/basics/intermediate/expert
                initial_belief_prior=0.5
            )

        errors = exc_info.value.errors()
        assert len(errors) > 0
        # Check that it's a literal type error
        assert any("familiarity" in str(error["loc"]) for error in errors)

    def test_invalid_prior_too_high(self):
        """Test that prior > 1.0 raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            OnboardingData(
                course="cbap",
                motivation="learning",
                familiarity="basics",
                initial_belief_prior=1.5  # Invalid: must be <= 1.0
            )

        errors = exc_info.value.errors()
        assert any("between 0.0 and 1.0" in str(error["ctx"]["error"]) for error in errors)

    def test_invalid_prior_negative(self):
        """Test that negative prior raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            OnboardingData(
                course="cbap",
                motivation="learning",
                familiarity="basics",
                initial_belief_prior=-0.1  # Invalid: must be >= 0.0
            )

        errors = exc_info.value.errors()
        assert any("between 0.0 and 1.0" in str(error["ctx"]["error"]) for error in errors)

    def test_prior_edge_case_zero(self):
        """Test that prior=0.0 is valid (edge case)."""
        data = OnboardingData(
            course="cbap",
            motivation="learning",
            familiarity="new",
            initial_belief_prior=0.0
        )
        assert data.initial_belief_prior == 0.0

    def test_prior_edge_case_one(self):
        """Test that prior=1.0 is valid (edge case)."""
        data = OnboardingData(
            course="cbap",
            motivation="learning",
            familiarity="expert",
            initial_belief_prior=1.0
        )
        assert data.initial_belief_prior == 1.0

    def test_all_familiarity_levels_valid(self):
        """Test all valid familiarity levels: new, basics, intermediate, expert."""
        valid_levels = ["new", "basics", "intermediate", "expert"]
        for level in valid_levels:
            data = OnboardingData(
                course="cbap",
                motivation="learning",
                familiarity=level,
                initial_belief_prior=0.5
            )
            assert data.familiarity == level


class TestUserUpdateSchema:
    """Tests for UserUpdate schema validation."""

    def test_empty_update(self):
        """Test that empty update is valid (all fields optional)."""
        update = UserUpdate()
        assert update.exam_date is None
        assert update.target_score is None
        assert update.daily_study_time is None
        assert update.knowledge_level is None
        assert update.motivation is None
        assert update.referral_source is None
        assert update.dark_mode is None

    def test_partial_update(self):
        """Test that partial update with some fields works."""
        update = UserUpdate(
            exam_date=date(2025, 6, 15),
            target_score=85,
            knowledge_level="Intermediate"
        )
        assert update.exam_date == date(2025, 6, 15)
        assert update.target_score == 85
        assert update.knowledge_level == "Intermediate"
        assert update.motivation is None

    def test_target_score_valid_range(self):
        """Test that target score in valid range (0-100) is accepted."""
        update_min = UserUpdate(target_score=0)
        assert update_min.target_score == 0

        update_max = UserUpdate(target_score=100)
        assert update_max.target_score == 100

        update_mid = UserUpdate(target_score=75)
        assert update_mid.target_score == 75

    def test_target_score_below_range(self):
        """Test that target score below 0 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            UserUpdate(target_score=-1)

        errors = exc_info.value.errors()
        assert any("between 0 and 100" in str(error["ctx"]["error"]) for error in errors)

    def test_target_score_above_range(self):
        """Test that target score above 100 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            UserUpdate(target_score=101)

        errors = exc_info.value.errors()
        assert any("between 0 and 100" in str(error["ctx"]["error"]) for error in errors)

    def test_knowledge_level_valid_values(self):
        """Test that valid knowledge level values are accepted."""
        for level in ["Beginner", "Intermediate", "Advanced"]:
            update = UserUpdate(knowledge_level=level)
            assert update.knowledge_level == level

    def test_knowledge_level_invalid_value(self):
        """Test that invalid knowledge level is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            UserUpdate(knowledge_level="Expert")

        errors = exc_info.value.errors()
        assert any("Beginner, Intermediate, or Advanced" in str(error["ctx"]["error"]) for error in errors)

    def test_referral_source_valid_values(self):
        """Test that valid referral source values are accepted."""
        for source in ["Search", "Friend", "Social", "Other"]:
            update = UserUpdate(referral_source=source)
            assert update.referral_source == source

    def test_referral_source_invalid_value(self):
        """Test that invalid referral source is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            UserUpdate(referral_source="Advertisement")

        errors = exc_info.value.errors()
        assert any("Search, Friend, Social, or Other" in str(error["ctx"]["error"]) for error in errors)

    def test_dark_mode_valid_values(self):
        """Test that valid dark mode values are accepted."""
        for mode in ["light", "dark", "auto"]:
            update = UserUpdate(dark_mode=mode)
            assert update.dark_mode == mode

    def test_dark_mode_invalid_value(self):
        """Test that invalid dark mode is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            UserUpdate(dark_mode="system")

        errors = exc_info.value.errors()
        assert any("light, dark, or auto" in str(error["ctx"]["error"]) for error in errors)


class TestUserResponseSchema:
    """Tests for UserResponse schema."""

    def test_valid_user_response(self):
        """Test creating a valid UserResponse schema."""
        user_id = uuid4()
        now = datetime.now()

        user_data = {
            "id": user_id,
            "email": "test@example.com",
            "exam_date": date(2025, 6, 15),
            "target_score": 85,
            "daily_study_time": 120,
            "knowledge_level": "Intermediate",
            "motivation": "Career advancement",
            "referral_source": "Search",
            "is_admin": False,
            "dark_mode": "auto",
            "created_at": now
        }

        response = UserResponse(**user_data)
        assert response.id == user_id
        assert response.email == "test@example.com"
        assert response.exam_date == date(2025, 6, 15)
        assert response.target_score == 85
        assert response.daily_study_time == 120
        assert response.knowledge_level == "Intermediate"
        assert response.motivation == "Career advancement"
        assert response.referral_source == "Search"
        assert response.is_admin is False
        assert response.dark_mode == "auto"
        assert response.created_at == now

    def test_user_response_with_nulls(self):
        """Test UserResponse with nullable fields set to None."""
        user_id = uuid4()
        now = datetime.now()

        user_data = {
            "id": user_id,
            "email": "test@example.com",
            "exam_date": None,
            "target_score": None,
            "daily_study_time": None,
            "knowledge_level": None,
            "motivation": None,
            "referral_source": None,
            "is_admin": False,
            "dark_mode": "light",
            "created_at": now
        }

        response = UserResponse(**user_data)
        assert response.exam_date is None
        assert response.target_score is None
        assert response.daily_study_time is None
        assert response.knowledge_level is None
        assert response.motivation is None
        assert response.referral_source is None

    def test_user_response_config_from_attributes(self):
        """Test that from_attributes config is enabled."""
        # This allows UserResponse to work with SQLAlchemy models
        assert UserResponse.model_config.get("from_attributes") is True
