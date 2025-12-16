"""
Unit tests for diagnostic API routes.
Tests the POST /diagnostic/answer endpoint with proper dependency injection.
"""
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI, status
from httpx import ASGITransport, AsyncClient

from src.routes.diagnostic import router
from src.dependencies import get_current_user
from src.db.session import get_db


# ============================================================================
# Test Fixtures
# ============================================================================

def create_test_app_with_mocks(
    mock_user=None,
    mock_question_repo=None,
    mock_belief_updater=None,
    mock_session=None,
):
    """Create test app with dependency overrides."""
    from src.routes.diagnostic import (
        get_belief_updater,
        get_question_repository,
    )

    app = FastAPI()
    app.include_router(router, prefix="/v1")

    if mock_user:
        async def override_user():
            return mock_user
        app.dependency_overrides[get_current_user] = override_user

    if mock_question_repo:
        async def override_repo():
            return mock_question_repo
        app.dependency_overrides[get_question_repository] = override_repo

    if mock_belief_updater:
        async def override_updater():
            return mock_belief_updater
        app.dependency_overrides[get_belief_updater] = override_updater

    if mock_session:
        async def override_db():
            yield mock_session
        app.dependency_overrides[get_db] = override_db

    return app


# ============================================================================
# Schema Validation Tests
# ============================================================================

class TestSchemaValidation:
    """Test request/response schema validation."""

    @pytest.mark.asyncio
    async def test_validates_question_id_format(self):
        """Verify endpoint rejects invalid UUID format for question_id."""
        user = MagicMock()
        user.id = uuid4()

        app = create_test_app_with_mocks(mock_user=user)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/v1/diagnostic/answer",
                json={"question_id": "invalid-uuid", "selected_answer": "A"},
            )

            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_rejects_invalid_selected_answer(self):
        """Verify endpoint rejects invalid answer letters."""
        user = MagicMock()
        user.id = uuid4()

        app = create_test_app_with_mocks(mock_user=user)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Test various invalid answers
            for invalid_answer in ["E", "a", "1", "", "AB", "correct"]:
                response = await client.post(
                    "/v1/diagnostic/answer",
                    json={"question_id": str(uuid4()), "selected_answer": invalid_answer},
                )
                assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, (
                    f"Expected 422 for answer '{invalid_answer}'"
                )

    @pytest.mark.asyncio
    async def test_accepts_valid_answer_letters(self):
        """Verify endpoint accepts valid answer letters A, B, C, D."""
        user = MagicMock()
        user.id = uuid4()

        question_id = uuid4()
        concept_id = uuid4()

        # Create mock question
        mock_question = MagicMock()
        mock_question.id = question_id
        mock_question.correct_answer = "A"
        mock_question.slip_rate = 0.1
        mock_question.guess_rate = 0.25
        mock_qc = MagicMock()
        mock_qc.concept_id = concept_id
        mock_question.question_concepts = [mock_qc]

        # Mock repository
        mock_repo = AsyncMock()
        mock_repo.get_question_by_id.return_value = mock_question

        # Mock belief updater
        mock_updater = AsyncMock()
        mock_updater.update_beliefs.return_value = [concept_id]

        # Mock db session
        mock_session = AsyncMock()

        # Mock Redis
        with patch("src.routes.diagnostic.get_redis") as mock_redis:
            redis_instance = AsyncMock()
            redis_instance.get.return_value = None
            redis_instance.setex.return_value = None
            mock_redis.return_value = redis_instance

            app = create_test_app_with_mocks(
                mock_user=user,
                mock_question_repo=mock_repo,
                mock_belief_updater=mock_updater,
                mock_session=mock_session,
            )

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                for valid_answer in ["A", "B", "C", "D"]:
                    # Reset redis to not return duplicate
                    redis_instance.get.return_value = None

                    response = await client.post(
                        "/v1/diagnostic/answer",
                        json={
                            "question_id": str(question_id),
                            "selected_answer": valid_answer,
                        },
                    )
                    # Should not be 422
                    assert response.status_code != status.HTTP_422_UNPROCESSABLE_ENTITY, (
                        f"Expected valid response for answer '{valid_answer}'"
                    )


# ============================================================================
# Response Shape Tests
# ============================================================================

class TestResponseShape:
    """Test response format matches schema."""

    @pytest.mark.asyncio
    async def test_response_includes_required_fields(self):
        """Verify response includes is_recorded, concepts_updated, diagnostic_progress, diagnostic_total."""
        user = MagicMock()
        user.id = uuid4()

        question_id = uuid4()
        concept_id = uuid4()

        # Create mock question
        mock_question = MagicMock()
        mock_question.id = question_id
        mock_question.correct_answer = "A"
        mock_question.slip_rate = None
        mock_question.guess_rate = None
        mock_qc = MagicMock()
        mock_qc.concept_id = concept_id
        mock_question.question_concepts = [mock_qc]

        mock_repo = AsyncMock()
        mock_repo.get_question_by_id.return_value = mock_question

        mock_updater = AsyncMock()
        mock_updater.update_beliefs.return_value = [concept_id]

        mock_session = AsyncMock()

        with patch("src.routes.diagnostic.get_redis") as mock_redis:
            redis_instance = AsyncMock()
            redis_instance.get.return_value = None
            redis_instance.setex.return_value = None
            mock_redis.return_value = redis_instance

            app = create_test_app_with_mocks(
                mock_user=user,
                mock_question_repo=mock_repo,
                mock_belief_updater=mock_updater,
                mock_session=mock_session,
            )

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/v1/diagnostic/answer",
                    json={
                        "question_id": str(question_id),
                        "selected_answer": "A",
                    },
                )

                assert response.status_code == status.HTTP_200_OK
                data = response.json()

                # Verify required fields
                assert "is_recorded" in data
                assert "concepts_updated" in data
                assert "diagnostic_progress" in data
                assert "diagnostic_total" in data

                # Verify types
                assert isinstance(data["is_recorded"], bool)
                assert isinstance(data["concepts_updated"], list)
                assert isinstance(data["diagnostic_progress"], int)
                assert isinstance(data["diagnostic_total"], int)

    @pytest.mark.asyncio
    async def test_response_excludes_is_correct(self):
        """Verify response does NOT include is_correct (diagnostic mode)."""
        user = MagicMock()
        user.id = uuid4()

        question_id = uuid4()

        mock_question = MagicMock()
        mock_question.id = question_id
        mock_question.correct_answer = "A"
        mock_question.slip_rate = None
        mock_question.guess_rate = None
        mock_question.question_concepts = []

        mock_repo = AsyncMock()
        mock_repo.get_question_by_id.return_value = mock_question

        mock_updater = AsyncMock()
        mock_updater.update_beliefs.return_value = []

        mock_session = AsyncMock()

        with patch("src.routes.diagnostic.get_redis") as mock_redis:
            redis_instance = AsyncMock()
            redis_instance.get.return_value = None
            redis_instance.setex.return_value = None
            mock_redis.return_value = redis_instance

            app = create_test_app_with_mocks(
                mock_user=user,
                mock_question_repo=mock_repo,
                mock_belief_updater=mock_updater,
                mock_session=mock_session,
            )

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/v1/diagnostic/answer",
                    json={
                        "question_id": str(question_id),
                        "selected_answer": "B",
                    },
                )

                assert response.status_code == status.HTTP_200_OK
                data = response.json()

                # Should NOT include feedback fields
                assert "is_correct" not in data
                assert "explanation" not in data
                assert "correct_answer" not in data


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Test error responses."""

    @pytest.mark.asyncio
    async def test_returns_404_for_nonexistent_question(self):
        """Verify 404 returned when question not found."""
        user = MagicMock()
        user.id = uuid4()

        mock_repo = AsyncMock()
        mock_repo.get_question_by_id.return_value = None  # Question not found

        mock_updater = AsyncMock()
        mock_session = AsyncMock()

        app = create_test_app_with_mocks(
            mock_user=user,
            mock_question_repo=mock_repo,
            mock_belief_updater=mock_updater,
            mock_session=mock_session,
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/v1/diagnostic/answer",
                json={
                    "question_id": str(uuid4()),
                    "selected_answer": "A",
                },
            )

            assert response.status_code == status.HTTP_404_NOT_FOUND
            data = response.json()
            assert data["detail"]["error"]["code"] == "QUESTION_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_returns_409_for_duplicate_answer(self):
        """Verify 409 returned when answer already submitted for question."""
        import json as json_lib

        user = MagicMock()
        user.id = uuid4()

        question_id = uuid4()

        mock_question = MagicMock()
        mock_question.id = question_id
        mock_question.correct_answer = "A"
        mock_question.question_concepts = []

        mock_repo = AsyncMock()
        mock_repo.get_question_by_id.return_value = mock_question

        mock_updater = AsyncMock()
        mock_session = AsyncMock()

        with patch("src.routes.diagnostic.get_redis") as mock_redis:
            redis_instance = AsyncMock()
            # Simulate existing session with this question already answered
            existing_session = {
                "answers": {str(question_id): "B"},
                "total": 15,
            }
            redis_instance.get.return_value = json_lib.dumps(existing_session)
            mock_redis.return_value = redis_instance

            app = create_test_app_with_mocks(
                mock_user=user,
                mock_question_repo=mock_repo,
                mock_belief_updater=mock_updater,
                mock_session=mock_session,
            )

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/v1/diagnostic/answer",
                    json={
                        "question_id": str(question_id),
                        "selected_answer": "A",
                    },
                )

                assert response.status_code == status.HTTP_409_CONFLICT
                data = response.json()
                assert data["detail"]["error"]["code"] == "DUPLICATE_REQUEST"
