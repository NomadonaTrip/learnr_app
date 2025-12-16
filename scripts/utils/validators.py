"""
Validation utilities for vendor question import.
Provides functions to validate question data before database insertion.
"""
from typing import List

# Valid CBAP Knowledge Areas
VALID_KAS = [
    "Business Analysis Planning and Monitoring",
    "Elicitation and Collaboration",
    "Requirements Life Cycle Management",
    "Strategy Analysis",
    "Requirements Analysis and Design Definition",
    "Solution Evaluation",
]

# Valid difficulty levels
VALID_DIFFICULTIES = ["Easy", "Medium", "Hard"]

# Valid correct answer options
VALID_ANSWERS = ["A", "B", "C", "D"]


def validate_ka(ka: str) -> bool:
    """
    Validate that the knowledge area is one of the 6 valid CBAP KAs.

    Args:
        ka: Knowledge area string to validate

    Returns:
        True if valid, False otherwise
    """
    return ka in VALID_KAS


def validate_difficulty(difficulty: str | None) -> str:
    """
    Validate and normalize difficulty level.

    If difficulty is not provided or invalid, defaults to "Medium".

    Args:
        difficulty: Difficulty level string or None

    Returns:
        Normalized difficulty level (Easy/Medium/Hard)
    """
    if difficulty and difficulty in VALID_DIFFICULTIES:
        return difficulty
    return "Medium"


def validate_correct_answer(answer: str) -> bool:
    """
    Validate that correct_answer is one of A, B, C, D.

    Args:
        answer: Correct answer string to validate

    Returns:
        True if valid, False otherwise
    """
    return answer.upper() in VALID_ANSWERS


def parse_concept_tags(tags: str | None) -> List[str]:
    """
    Parse comma-separated concept tags into a list.

    Args:
        tags: Comma-separated string of tags or None

    Returns:
        List of tag strings (empty list if None or empty string)
    """
    if not tags:
        return []

    # Split by comma and strip whitespace
    tag_list = [tag.strip() for tag in tags.split(",")]

    # Filter out empty strings
    return [tag for tag in tag_list if tag]
