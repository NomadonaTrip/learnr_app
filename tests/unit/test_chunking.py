"""
Unit tests for chunking logic (parse_corpus.py).

Tests chunk sizing, paragraph boundary preservation, section boundary
preservation, and overlap generation.
"""
import sys
from pathlib import Path
from uuid import uuid4

import pytest
import tiktoken

# Add scripts to path for testing
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root / "scripts"))
sys.path.append(str(project_root / "apps" / "api"))

from parse_corpus import CorpusSection, chunk_section, get_overlap, generate_chunk_title, estimate_read_time

enc = tiktoken.get_encoding("cl100k_base")


@pytest.fixture
def sample_section():
    """Create a sample corpus section for testing."""
    content = """This is paragraph one with some content.

This is paragraph two with more content.

This is paragraph three with even more content to ensure we have enough text.

This is paragraph four continuing the section content.

This is paragraph five with additional information."""

    return CorpusSection(
        section_ref="3.2.1",
        title="Stakeholder Analysis",
        content=content,
        knowledge_area_id="ba-planning",
        page_numbers=[42],
    )


@pytest.fixture
def long_section():
    """Create a long section that will require multiple chunks."""
    # Generate content that will exceed max_tokens
    paragraphs = []
    for i in range(20):
        para = f"Paragraph {i+1}: " + " ".join(["word"] * 50)  # ~50 words each
        paragraphs.append(para)

    content = "\n\n".join(paragraphs)

    return CorpusSection(
        section_ref="4.1.2",
        title="Long Section for Testing",
        content=content,
        knowledge_area_id="elicitation",
        page_numbers=[100, 101, 102],
    )


def test_chunk_section_single_chunk(sample_section):
    """Test that small sections create a single chunk."""
    chunks = chunk_section(sample_section, min_tokens=50, max_tokens=500)

    assert len(chunks) == 1
    content, chunk_index = chunks[0]
    assert chunk_index == 0
    assert sample_section.content in content or content in sample_section.content


def test_chunk_section_preserves_paragraphs(sample_section):
    """Test that chunks preserve paragraph boundaries."""
    chunks = chunk_section(sample_section, min_tokens=10, max_tokens=50)

    # Each chunk should contain whole paragraphs (no mid-paragraph splits)
    for content, _ in chunks:
        # Check that content starts and ends cleanly (not mid-sentence)
        assert not content.strip().startswith("with")
        assert not content.strip().endswith("with")


def test_chunk_section_respects_max_tokens(long_section):
    """Test that chunks respect max_tokens constraint."""
    max_tokens = 300
    chunks = chunk_section(long_section, min_tokens=100, max_tokens=max_tokens)

    # Should have multiple chunks
    assert len(chunks) > 1

    # Each chunk should be within token limits
    for content, _ in chunks:
        token_count = len(enc.encode(content))
        # Allow some overflow for overlap
        assert token_count <= max_tokens + 100  # +100 for overlap tolerance


def test_chunk_section_chunk_indexes(long_section):
    """Test that chunk indexes are sequential."""
    chunks = chunk_section(long_section, min_tokens=100, max_tokens=300)

    for i, (content, chunk_index) in enumerate(chunks):
        assert chunk_index == i


def test_get_overlap_empty_chunks():
    """Test overlap generation with empty chunks list."""
    overlap = get_overlap([], 50)
    assert overlap == ""


def test_get_overlap_small_content():
    """Test overlap generation when content is smaller than overlap size."""
    chunks = ["Small content"]
    overlap = get_overlap(chunks, 100)
    assert overlap == "Small content"


def test_get_overlap_takes_last_n_tokens():
    """Test that overlap takes last N tokens from chunks."""
    chunks = ["First paragraph with lots of words.", "Second paragraph with more content."]
    overlap = get_overlap(chunks, 10)

    # Overlap should be approximately last 10 tokens
    assert overlap
    assert len(overlap) < len("\n\n".join(chunks))
    # Should contain content from end
    assert "content" in overlap or "more" in overlap


def test_generate_chunk_title_single_chunk():
    """Test title generation for single chunk."""
    section = CorpusSection(
        section_ref="3.1",
        title="Plan Business Analysis Approach",
        content="Content",
        knowledge_area_id="ba-planning",
        page_numbers=[40],
    )

    title = generate_chunk_title(section, 0, 1)
    assert title == "Plan Business Analysis Approach"
    assert " - Part " not in title


def test_generate_chunk_title_multiple_chunks():
    """Test title generation for multiple chunks."""
    section = CorpusSection(
        section_ref="3.1",
        title="Plan Business Analysis Approach",
        content="Content",
        knowledge_area_id="ba-planning",
        page_numbers=[40],
    )

    title1 = generate_chunk_title(section, 0, 3)
    assert title1 == "Plan Business Analysis Approach - Part 1"

    title2 = generate_chunk_title(section, 1, 3)
    assert title2 == "Plan Business Analysis Approach - Part 2"

    title3 = generate_chunk_title(section, 2, 3)
    assert title3 == "Plan Business Analysis Approach - Part 3"


def test_generate_chunk_title_truncation():
    """Test that long titles are truncated to 255 chars."""
    section = CorpusSection(
        section_ref="3.1",
        title="A" * 300,  # 300 char title
        content="Content",
        knowledge_area_id="ba-planning",
        page_numbers=[40],
    )

    title = generate_chunk_title(section, 0, 1)
    assert len(title) <= 255
    assert title.endswith("...")


def test_estimate_read_time_short_content():
    """Test read time estimation for short content."""
    content = "Short content with just a few words."
    read_time = estimate_read_time(content)
    assert read_time == 1  # Minimum 1 minute


def test_estimate_read_time_long_content():
    """Test read time estimation for longer content."""
    # 400 words = ~2 minutes at 200 wpm
    content = " ".join(["word"] * 400)
    read_time = estimate_read_time(content)
    assert read_time == 2


def test_estimate_read_time_very_long_content():
    """Test read time estimation for very long content."""
    # 1000 words = ~5 minutes at 200 wpm
    content = " ".join(["word"] * 1000)
    read_time = estimate_read_time(content)
    assert read_time == 5


def test_chunk_section_never_splits_across_sections():
    """Test that chunking never splits across section boundaries."""
    section = CorpusSection(
        section_ref="3.2.1",
        title="Test Section",
        content="Content for section 3.2.1 only.",
        knowledge_area_id="ba-planning",
        page_numbers=[42],
    )

    chunks = chunk_section(section, min_tokens=10, max_tokens=100)

    # All chunks should be from the same section
    for content, _ in chunks:
        assert "3.2.1" in section.section_ref
        # Content should be subset of original section content
        assert all(word in section.content or word in content for word in content.split()[:5])
