"""Unit tests for the generic corpus markdown parser."""
import sys
from pathlib import Path

import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "scripts"))

from utils.corpus_markdown import (
    CorpusMarkdownParser,
    MarkdownSection,
    ka_chapter_map,
)

CBAP_KAS = [
    {"id": "ba-planning", "section_prefix": "3"},
    {"id": "elicitation", "section_prefix": "4"},
    {"id": "rlcm", "section_prefix": "5"},
    {"id": "strategy", "section_prefix": "6"},
    {"id": "radd", "section_prefix": "7"},
    {"id": "solution-eval", "section_prefix": "8"},
]

SAMPLE_MD = """\
## 2.1 Key Concept
This introductory chapter describes the overall structure of the guide
and how the knowledge areas relate to one another in practice.

## 3.1 Plan Approach
The business analyst defines the approach used to perform business
analysis activities across the initiative, including deliverables.

## 3.1.1
## Purpose
The purpose of this subsection is to explain why a planned approach is
selected and how it shapes the work products produced downstream.

## 9.1 Some Technique
Appendix technique content that must NOT pollute chapter 3 and is long
enough on its own to exceed the minimum content length threshold.
"""


def _write(tmp_path, text):
    p = tmp_path / "corpus.md"
    p.write_text(text, encoding="utf-8")
    return str(p)


def test_ka_chapter_map_from_section_prefix():
    assert ka_chapter_map(CBAP_KAS) == {
        3: "ba-planning", 4: "elicitation", 5: "rlcm",
        6: "strategy", 7: "radd", 8: "solution-eval",
    }


def test_parser_ka_chapters_only_excludes_intro_and_appendix(tmp_path):
    md = _write(tmp_path, SAMPLE_MD)
    secs = CorpusMarkdownParser(md, allowed_chapters=frozenset({3, 4, 5, 6, 7, 8})).parse()
    nums = [s.section_number for s in secs]
    assert "2.1" not in nums          # intro chapter excluded
    assert "9.1" not in nums          # appendix excluded
    assert "3.1" in nums
    # split-title case: `## 3.1.1` / `## Purpose` — number-only heading takes
    # its title from the immediately following non-numbered heading.
    assert "3.1.1" in nums
    purpose = next(s for s in secs if s.section_number == "3.1.1")
    assert purpose.title == "Purpose"
    # appendix content must not be folded into the last in-range section
    assert all("Appendix technique" not in s.content for s in secs)


def test_parser_all_chapters_includes_intro(tmp_path):
    md = _write(tmp_path, SAMPLE_MD)
    secs = CorpusMarkdownParser(md, allowed_chapters=frozenset(range(1, 9))).parse()
    nums = [s.section_number for s in secs]
    assert "2.1" in nums              # intro now included
    assert "9.1" not in nums          # still excluded (above max)
    assert all("Appendix technique" not in s.content for s in secs)


def test_parser_skips_sections_with_content_below_50_chars(tmp_path):
    short_md = "## 3.1 Brief\nToo short.\n"
    md = _write(tmp_path, short_md)
    secs = CorpusMarkdownParser(md, allowed_chapters=frozenset({3})).parse()
    assert secs == []   # guard excludes sub-50-char sections


def test_extract_script_uses_shared_parser_no_hardcoded_chapters():
    """Guard: the concept-extraction script must not redefine the parser
    or a hardcoded BABOK chapter constant."""
    src = (project_root / "scripts" / "extract_babok_concepts.py").read_text()
    assert "BABOK_KA_CHAPTERS" not in src
    assert "class MarkdownBabokParser" not in src
    assert "from utils.corpus_markdown import" in src
