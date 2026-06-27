import sys
from pathlib import Path
import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "scripts"))

from parse_corpus import resolve_chunk_chapters, validate_heading_style, ChapterScope


class MockCourse:
    def __init__(self, corpus_config=None):
        self.corpus_config = corpus_config
        self.knowledge_areas = [
            {"id": "ba-planning", "section_prefix": "3"},
            {"id": "solution-eval", "section_prefix": "8"},
        ]


def test_null_config_defaults_to_ka_chapter_range():
    scope = resolve_chunk_chapters(MockCourse(None), None, None)
    assert scope == ChapterScope(3, 8)


def test_config_overrides_default():
    c = MockCourse({"chunk_chapters": {"min": 1, "max": 8}})
    assert resolve_chunk_chapters(c, None, None) == ChapterScope(1, 8)


def test_cli_overrides_config():
    c = MockCourse({"chunk_chapters": {"min": 1, "max": 8}})
    assert resolve_chunk_chapters(c, 2, 7) == ChapterScope(2, 7)


def test_min_greater_than_max_raises():
    with pytest.raises(ValueError):
        resolve_chunk_chapters(MockCourse(None), 9, 3)


def test_unsupported_heading_style_raises():
    with pytest.raises(NotImplementedError):
        validate_heading_style(MockCourse({"heading_style": "atx"}))


def test_numbered_heading_style_ok():
    validate_heading_style(MockCourse({"heading_style": "numbered"}))
    validate_heading_style(MockCourse(None))  # default is numbered
