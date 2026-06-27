"""Generic markdown corpus parser (course-agnostic).

Parses a pymupdf4llm-generated markdown rendering of a structured corpus
(e.g. a certification guide with numbered N.N.N headings) into
``MarkdownSection`` objects. Chapter scope is supplied by the caller via
``allowed_chapters`` — nothing here is course-specific.
"""
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


def ka_chapter_map(knowledge_areas: List[dict]) -> dict[int, str]:
    """Map top-level chapter number -> knowledge_area id from each KA's section_prefix."""
    result: dict[int, str] = {}
    for ka in knowledge_areas:
        prefix = ka.get("section_prefix")
        if prefix is None:
            continue
        try:
            result[int(str(prefix).split(".")[0])] = ka["id"]
        except (ValueError, KeyError):
            continue
    return result


@dataclass
class MarkdownSection:
    """Represents a parsed corpus section."""
    section_number: str  # e.g., "3.2.1"
    title: str
    content: str
    chapter: int
    depth: int  # 1=chapter, 2=section, 3=subsection, etc.
    page_start: int
    page_end: int


def convert_pdf_to_markdown(pdf_path: str, md_path: Optional[str] = None) -> str:
    """
    Convert a PDF to heading-structured markdown using pymupdf4llm.

    pymupdf4llm performs font/layout analysis to emit real markdown headings
    (e.g. ``## 3.2 Plan Stakeholder Engagement``), which the markdown parser
    chunks by section number. This replaces the fragile raw-text PDF
    parsing that produced malformed chunks.

    Args:
        pdf_path: Path to the source PDF.
        md_path: Optional output path. Defaults to the PDF path with a
            ``.md`` suffix; an existing cache is reused.

    Returns:
        Path to the markdown file.
    """
    import pymupdf4llm

    out = md_path or str(Path(pdf_path).with_suffix(".md"))
    if Path(out).exists() and Path(out).stat().st_size > 0:
        logger.info(f"Reusing cached markdown: {out}")
        return out

    logger.info(f"Converting PDF to markdown via pymupdf4llm: {pdf_path}")
    markdown = pymupdf4llm.to_markdown(pdf_path)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(markdown, encoding="utf-8")
    logger.info(f"Wrote markdown ({len(markdown)} chars) to {out}")
    return out


class CorpusMarkdownParser:
    """
    Parses a pymupdf4llm-generated markdown rendering of a structured corpus
    into :class:`MarkdownSection` objects, chunking by section-numbered headings.

    Heading shapes handled:
    - ``## 3.2 Define Scope`` — number + inline title
    - ``## 3.2.1`` followed by ``## Purpose`` — number-only, title on the next
      heading (the standard numbered subsection anatomy)
    - ``## Inputs`` / ``## .1 Perform ...`` / ``## Figure 3.2.1: ...`` — content
      sub-headings, folded into the current section's content
    """

    # Strips the leading ``#`` markers from a heading line.
    HEADING_PATTERN = re.compile(r'^#+\s*(.*?)\s*$')
    # Matches a heading whose (bold-stripped) text starts with a section number.
    SECTION_PATTERN = re.compile(r'^\**\s*(\d+(?:\.\d+)+)\b\s*\**\s*(.*?)\s*\**$')

    def __init__(self, md_path: str, allowed_chapters: frozenset):
        self.md_path = md_path
        self.allowed_chapters = allowed_chapters
        self._max_chapter = max(allowed_chapters)

    def parse(self) -> List[MarkdownSection]:
        lines = Path(self.md_path).read_text(encoding="utf-8").splitlines()
        sections: List[MarkdownSection] = []
        current: Optional[MarkdownSection] = None
        content: List[str] = []
        pending_title: Optional[MarkdownSection] = None

        def finalize() -> None:
            nonlocal current, content
            if current is not None:
                current.content = "\n".join(content).strip()
                if len(current.content) >= 50:
                    sections.append(current)
            content = []

        for line in lines:
            heading_match = self.HEADING_PATTERN.match(line)
            if not heading_match:
                if line.strip():
                    # Only an immediately-following heading can supply a split title.
                    pending_title = None
                if current is not None:
                    content.append(line)
                continue

            heading_text = heading_match.group(1).strip().strip('*').strip()
            section_match = self.SECTION_PATTERN.match(heading_text)

            if section_match:
                section_number = section_match.group(1)
                title = section_match.group(2).strip().strip('*').strip()
                chapter = int(section_number.split('.')[0])
                if chapter not in self.allowed_chapters:
                    if chapter > self._max_chapter:
                        # Trailing chapters (techniques/appendices) — stop, don't pollute.
                        finalize()
                        current = None
                        pending_title = None
                    elif current is not None:
                        # Below-range numbering — fold into current content.
                        content.append(line)
                    continue

                finalize()
                current = MarkdownSection(
                    section_number=section_number,
                    title=title,
                    content='',
                    chapter=chapter,
                    depth=len(section_number.split('.')),
                    page_start=0,
                    page_end=0,
                )
                pending_title = current if not title else None
                continue

            # Non-numbered heading: it's either a split title or a content sub-heading.
            if pending_title is not None and heading_text and not heading_text.startswith('.'):
                pending_title.title = heading_text
                pending_title = None
                continue
            if current is not None:
                content.append(line)

        finalize()
        logger.info(f"Parsed {len(sections)} sections from markdown")
        return sections
