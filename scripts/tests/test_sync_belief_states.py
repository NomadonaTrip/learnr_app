"""
Unit tests for sync_belief_states.py

Story 2.14: Belief State Sync for New Concepts

Tests cover:
- Sync creates beliefs for missing concepts only
- Idempotency: second run creates 0 new beliefs
- Dry-run mode logs but doesn't write
- SyncResult dataclass
"""
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

# Add script path to enable import
sys.path.insert(0, str(Path(__file__).parent.parent))

from sync_belief_states import (
    SyncResult,
    sync_beliefs_for_user,
)


# =====================================
# SyncResult Tests
# =====================================

class TestSyncResult:
    """Tests for SyncResult dataclass."""

    def test_sync_result_default_values(self):
        """Test SyncResult has correct default values."""
        result = SyncResult()

        assert result.users_synced == 0
        assert result.beliefs_created == 0
        assert result.duration_ms == 0.0
        assert result.errors == 0

    def test_sync_result_custom_values(self):
        """Test SyncResult with custom values."""
        result = SyncResult(
            users_synced=100,
            beliefs_created=5000,
            duration_ms=2500.5,
            errors=2,
        )

        assert result.users_synced == 100
        assert result.beliefs_created == 5000
        assert result.duration_ms == 2500.5
        assert result.errors == 2


# =====================================
# Sync Beliefs for User Tests
# =====================================

class TestSyncBeliefsForUser:
    """Tests for sync_beliefs_for_user function."""

    @pytest.mark.asyncio
    async def test_sync_creates_only_missing_beliefs(self):
        """Test sync creates beliefs only for concepts without existing beliefs."""
        user_id = uuid4()
        concept1, concept2, concept3 = uuid4(), uuid4(), uuid4()
        all_concept_ids = [concept1, concept2, concept3]

        # Mock session and repo
        mock_session = MagicMock()
        mock_repo = AsyncMock()

        # User has belief for concept1 only, missing concept2 and concept3
        existing_beliefs = {concept1: MagicMock()}
        mock_repo.get_beliefs_as_dict.return_value = existing_beliefs

        # bulk_create returns count of created (2 missing)
        mock_repo.bulk_create_from_concepts.return_value = 2

        created_count = await sync_beliefs_for_user(
            db_session=mock_session,
            belief_repo=mock_repo,
            user_id=user_id,
            all_concept_ids=all_concept_ids,
            dry_run=False,
        )

        # Should use bulk_create which handles ON CONFLICT DO NOTHING
        mock_repo.bulk_create_from_concepts.assert_called_once_with(
            user_id=user_id,
            concept_ids=all_concept_ids,
            alpha=1.0,
            beta=1.0,
        )
        assert created_count == 2

    @pytest.mark.asyncio
    async def test_sync_creates_all_beliefs_for_new_user(self):
        """Test sync creates all beliefs when user has none."""
        user_id = uuid4()
        concept1, concept2 = uuid4(), uuid4()
        all_concept_ids = [concept1, concept2]

        mock_session = MagicMock()
        mock_repo = AsyncMock()

        # User has no existing beliefs
        mock_repo.get_beliefs_as_dict.return_value = {}
        mock_repo.bulk_create_from_concepts.return_value = 2

        created_count = await sync_beliefs_for_user(
            db_session=mock_session,
            belief_repo=mock_repo,
            user_id=user_id,
            all_concept_ids=all_concept_ids,
            dry_run=False,
        )

        assert created_count == 2

    @pytest.mark.asyncio
    async def test_sync_idempotent_no_new_beliefs_when_all_exist(self):
        """Test idempotency: second run creates 0 new beliefs."""
        user_id = uuid4()
        concept1, concept2 = uuid4(), uuid4()
        all_concept_ids = [concept1, concept2]

        mock_session = MagicMock()
        mock_repo = AsyncMock()

        # User has beliefs for all concepts
        existing_beliefs = {
            concept1: MagicMock(),
            concept2: MagicMock(),
        }
        mock_repo.get_beliefs_as_dict.return_value = existing_beliefs

        # ON CONFLICT DO NOTHING returns 0 when all exist
        mock_repo.bulk_create_from_concepts.return_value = 0

        created_count = await sync_beliefs_for_user(
            db_session=mock_session,
            belief_repo=mock_repo,
            user_id=user_id,
            all_concept_ids=all_concept_ids,
            dry_run=False,
        )

        # Should still call bulk_create (it's idempotent)
        mock_repo.bulk_create_from_concepts.assert_called_once()
        assert created_count == 0

    @pytest.mark.asyncio
    async def test_dry_run_does_not_write(self):
        """Test dry-run mode counts but doesn't write to database."""
        user_id = uuid4()
        concept1, concept2, concept3 = uuid4(), uuid4(), uuid4()
        all_concept_ids = [concept1, concept2, concept3]

        mock_session = MagicMock()
        mock_repo = AsyncMock()

        # User has 1 existing belief, 2 missing
        existing_beliefs = {concept1: MagicMock()}
        mock_repo.get_beliefs_as_dict.return_value = existing_beliefs

        created_count = await sync_beliefs_for_user(
            db_session=mock_session,
            belief_repo=mock_repo,
            user_id=user_id,
            all_concept_ids=all_concept_ids,
            dry_run=True,  # DRY RUN
        )

        # In dry run, we only count missing (no bulk_create call)
        mock_repo.bulk_create_from_concepts.assert_not_called()
        # Should return count of what WOULD be created
        assert created_count == 2  # 3 total - 1 existing = 2 missing

    @pytest.mark.asyncio
    async def test_sync_uses_uninformative_prior(self):
        """Test beliefs are created with Beta(1,1) uninformative prior."""
        user_id = uuid4()
        concept_id = uuid4()

        mock_session = MagicMock()
        mock_repo = AsyncMock()
        mock_repo.bulk_create_from_concepts.return_value = 1

        await sync_beliefs_for_user(
            db_session=mock_session,
            belief_repo=mock_repo,
            user_id=user_id,
            all_concept_ids=[concept_id],
            dry_run=False,
        )

        # Verify uninformative prior Beta(1,1) is used
        mock_repo.bulk_create_from_concepts.assert_called_once()
        call_kwargs = mock_repo.bulk_create_from_concepts.call_args.kwargs
        assert call_kwargs["alpha"] == 1.0
        assert call_kwargs["beta"] == 1.0

    @pytest.mark.asyncio
    async def test_sync_handles_empty_concept_list(self):
        """Test sync handles empty concept list gracefully."""
        user_id = uuid4()

        mock_session = MagicMock()
        mock_repo = AsyncMock()
        mock_repo.bulk_create_from_concepts.return_value = 0

        created_count = await sync_beliefs_for_user(
            db_session=mock_session,
            belief_repo=mock_repo,
            user_id=user_id,
            all_concept_ids=[],
            dry_run=False,
        )

        # Should still call bulk_create with empty list
        # (it handles empty list gracefully)
        assert created_count == 0
