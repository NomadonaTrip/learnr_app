"""
Unit tests for vendor question import validation functions.
Tests the validators in scripts/utils/validators.py
"""
import sys
from pathlib import Path

import pytest

# Add scripts to path for imports
scripts_path = Path(__file__).parent.parent.parent / "scripts"
sys.path.append(str(scripts_path))

from utils.validators import (
    VALID_KAS,
    parse_concept_tags,
    validate_correct_answer,
    validate_difficulty,
    validate_ka,
)


class TestValidateKA:
    """Tests for validate_ka function."""

    def test_valid_ka_returns_true(self):
        """Test that valid KAs return True."""
        for ka in VALID_KAS:
            assert validate_ka(ka) is True

    def test_invalid_ka_returns_false(self):
        """Test that invalid KAs return False."""
        invalid_kas = [
            "Invalid KA",
            "Business Planning",
            "Strategy",
            "",
            "business analysis planning and monitoring",  # case mismatch
        ]
        for ka in invalid_kas:
            assert validate_ka(ka) is False


class TestValidateDifficulty:
    """Tests for validate_difficulty function."""

    def test_valid_difficulty_returns_same(self):
        """Test that valid difficulties are returned as-is."""
        assert validate_difficulty("Easy") == "Easy"
        assert validate_difficulty("Medium") == "Medium"
        assert validate_difficulty("Hard") == "Hard"

    def test_none_returns_medium(self):
        """Test that None defaults to Medium."""
        assert validate_difficulty(None) == "Medium"

    def test_empty_string_returns_medium(self):
        """Test that empty string defaults to Medium."""
        assert validate_difficulty("") == "Medium"

    def test_invalid_difficulty_returns_medium(self):
        """Test that invalid difficulty defaults to Medium."""
        assert validate_difficulty("Impossible") == "Medium"
        assert validate_difficulty("easy") == "Medium"  # case mismatch


class TestValidateCorrectAnswer:
    """Tests for validate_correct_answer function."""

    def test_valid_uppercase_answers(self):
        """Test that uppercase A/B/C/D are valid."""
        assert validate_correct_answer("A") is True
        assert validate_correct_answer("B") is True
        assert validate_correct_answer("C") is True
        assert validate_correct_answer("D") is True

    def test_valid_lowercase_answers(self):
        """Test that lowercase a/b/c/d are valid (normalized to uppercase)."""
        assert validate_correct_answer("a") is True
        assert validate_correct_answer("b") is True
        assert validate_correct_answer("c") is True
        assert validate_correct_answer("d") is True

    def test_invalid_answers(self):
        """Test that invalid answers return False."""
        invalid_answers = ["E", "F", "1", "2", "", "AB", "a,b"]
        for answer in invalid_answers:
            assert validate_correct_answer(answer) is False


class TestParseConceptTags:
    """Tests for parse_concept_tags function."""

    def test_single_tag(self):
        """Test parsing a single tag."""
        result = parse_concept_tags("planning")
        assert result == ["planning"]

    def test_multiple_tags(self):
        """Test parsing comma-separated tags."""
        result = parse_concept_tags("planning,stakeholder,analysis")
        assert result == ["planning", "stakeholder", "analysis"]

    def test_tags_with_whitespace(self):
        """Test that whitespace is stripped from tags."""
        result = parse_concept_tags("planning, stakeholder , analysis")
        assert result == ["planning", "stakeholder", "analysis"]

    def test_none_returns_empty_list(self):
        """Test that None returns empty list."""
        result = parse_concept_tags(None)
        assert result == []

    def test_empty_string_returns_empty_list(self):
        """Test that empty string returns empty list."""
        result = parse_concept_tags("")
        assert result == []

    def test_empty_tags_filtered(self):
        """Test that empty tags are filtered out."""
        result = parse_concept_tags("planning,,analysis,")
        assert result == ["planning", "analysis"]
