# Course-Agnostic Markdown Corpus Chunking — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace `parse_corpus.py`'s broken raw-PDF sectioning + `\n\n`-only chunker with a course-agnostic markdown pipeline that produces ~280–500 properly-sized reading chunks whose concept links resolve.

**Architecture:** Extract the proven markdown parser from `extract_babok_concepts.py` into a generic shared module driven by an `allowed_chapters` parameter (no hardcoded chapter numbers). Add a per-course `corpus_config` JSONB column for the configurable chapter scope. Rewrite the chunker to split by a token budget with a sentence→token-window hard fallback.

**Tech Stack:** Python 3.11, pymupdf4llm, tiktoken (`cl100k_base`), SQLAlchemy (async) + Alembic, pytest, Qdrant, OpenAI embeddings.

## Global Constraints

- Run scripts with the venv interpreter: `apps/api/.venv/bin/python`.
- DB access for scripts is via the URL in `apps/api/.env` (`postgresql+asyncpg://learnr:learnr123@localhost:5432/learnr_dev`); scripts already `load_dotenv(apps/api/.env)`.
- OpenAI key gotcha: use the LAST `OPENAI_API_KEY` line in `apps/api/.env`; for embedding runs prefix `OPENAI_API_KEY="$(grep '^OPENAI_API_KEY' apps/api/.env | tail -1 | cut -d= -f2-)"`.
- `docs/` is gitignored — commit spec/plan/docs files with `git add -f`.
- Only `heading_style: "numbered"` is implemented; any other value raises `NotImplementedError`.
- Token target per chunk: `min_tokens=200`, `max_tokens=500` (CLI-overridable). No emitted chunk may exceed `max_tokens`.
- Chapter numbers and KA ids are NEVER hardcoded — always derived from `course.knowledge_areas[].section_prefix`.
- Branch: `feature/rebuild-reading-chunk-links` (continues the #12 work).
- Commit format: `<type>: <description>`.

---

### Task 1: Generic shared parser module `scripts/utils/corpus_markdown.py`

Move `BabokSection`, `convert_pdf_to_markdown`, and `MarkdownBabokParser` out of `scripts/extract_babok_concepts.py` into a new generic module, renamed and parameterized. Add a `ka_chapter_map` helper.

**Files:**
- Create: `scripts/utils/corpus_markdown.py`
- Test: `scripts/tests/test_corpus_markdown.py`
- Source reference (to move verbatim, then rename): `scripts/extract_babok_concepts.py` — `BabokSection` (lines 117–125), `convert_pdf_to_markdown` (238–267), `MarkdownBabokParser` (270–352).

**Interfaces:**
- Produces:
  - `@dataclass MarkdownSection(section_number:str, title:str, content:str, chapter:int, depth:int, page_start:int, page_end:int)` (renamed from `BabokSection`).
  - `convert_pdf_to_markdown(pdf_path:str, md_path:str|None=None) -> str`
  - `class CorpusMarkdownParser(md_path:str, allowed_chapters:frozenset[int])` with `.parse() -> list[MarkdownSection]`
  - `ka_chapter_map(knowledge_areas:list[dict]) -> dict[int,str]`

- [ ] **Step 1: Write the failing tests**

Create `scripts/tests/test_corpus_markdown.py`:

```python
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
Intro chapter content for two-one.

## 3.1 Plan Approach
Body of three-one.

## 3.1.1
## Purpose
Purpose body of three-one-one.

## 9.1 Some Technique
Appendix technique content that must NOT pollute chapter 3.
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
    # appendix content must not be folded into the last in-range section
    assert all("Appendix technique" not in s.content for s in secs)


def test_parser_all_chapters_includes_intro(tmp_path):
    md = _write(tmp_path, SAMPLE_MD)
    secs = CorpusMarkdownParser(md, allowed_chapters=frozenset(range(1, 9))).parse()
    nums = [s.section_number for s in secs]
    assert "2.1" in nums              # intro now included
    assert "9.1" not in nums          # still excluded (above max)
    assert all("Appendix technique" not in s.content for s in secs)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /mnt/e/TOOLMAKER/PYTHON/LearnR_2 && apps/api/.venv/bin/python -m pytest scripts/tests/test_corpus_markdown.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'utils.corpus_markdown'`.

- [ ] **Step 3: Create the module by moving + renaming**

Create `scripts/utils/corpus_markdown.py`. Copy from `scripts/extract_babok_concepts.py`:
- the `BabokSection` dataclass (lines 117–125) → rename class to `MarkdownSection`.
- `convert_pdf_to_markdown` (lines 238–267) verbatim.
- `MarkdownBabokParser` (lines 270–352) → rename class to `CorpusMarkdownParser`; change its return-type usages from `BabokSection` to `MarkdownSection`.

Add the module preamble and helper, and change the parser's `__init__` + chapter-filter logic as shown:

```python
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
```

The parser `__init__` and chapter branch change to:

```python
class CorpusMarkdownParser:
    HEADING_PATTERN = re.compile(r'^#+\s*(.*?)\s*$')
    SECTION_PATTERN = re.compile(r'^\**\s*(\d+(?:\.\d+)+)\b\s*\**\s*(.*?)\s*\**$')

    def __init__(self, md_path: str, allowed_chapters: frozenset):
        self.md_path = md_path
        self.allowed_chapters = allowed_chapters
        self._max_chapter = max(allowed_chapters)
    # ... .parse() body unchanged except the chapter-filter branch below ...
```

Inside `.parse()`, replace the old `if chapter not in BABOK_KA_CHAPTERS:` block with:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /mnt/e/TOOLMAKER/PYTHON/LearnR_2 && apps/api/.venv/bin/python -m pytest scripts/tests/test_corpus_markdown.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add scripts/utils/corpus_markdown.py scripts/tests/test_corpus_markdown.py
git commit -m "feat: add generic course-agnostic corpus markdown parser"
```

---

### Task 2: Migrate `extract_babok_concepts.py` to the shared module (no behavior change)

Delete the now-duplicated parser + `BABOK_KA_CHAPTERS` from the concept-extraction script; import from the shared module; derive chapters from the course it already loads. cbap behavior must be identical.

**Files:**
- Modify: `scripts/extract_babok_concepts.py` (remove lines 77–85 `BABOK_KA_CHAPTERS`; remove `BabokSection` 117–125; remove `convert_pdf_to_markdown` 238–267; remove `MarkdownBabokParser` 270–352; update usages at 198, 323, 424, 878).
- Test: `scripts/tests/test_corpus_markdown.py` (parity test added here).

**Interfaces:**
- Consumes: `CorpusMarkdownParser`, `MarkdownSection`, `convert_pdf_to_markdown`, `ka_chapter_map` from `utils.corpus_markdown`.

- [ ] **Step 1: Write the failing parity test**

Append to `scripts/tests/test_corpus_markdown.py`:

```python
def test_extract_script_uses_shared_parser_no_hardcoded_chapters():
    """Guard: the concept-extraction script must not redefine the parser
    or a hardcoded BABOK chapter constant."""
    src = (project_root / "scripts" / "extract_babok_concepts.py").read_text()
    assert "BABOK_KA_CHAPTERS" not in src
    assert "class MarkdownBabokParser" not in src
    assert "from utils.corpus_markdown import" in src
```

- [ ] **Step 2: Run test to verify it fails**

Run: `apps/api/.venv/bin/python -m pytest scripts/tests/test_corpus_markdown.py::test_extract_script_uses_shared_parser_no_hardcoded_chapters -v`
Expected: FAIL (`BABOK_KA_CHAPTERS` still present).

- [ ] **Step 3: Refactor the script**

In `scripts/extract_babok_concepts.py`:
1. Add near the other `scripts`-path imports: `from utils.corpus_markdown import (CorpusMarkdownParser, MarkdownSection, convert_pdf_to_markdown, ka_chapter_map)`.
2. Delete the `BABOK_KA_CHAPTERS` dict (77–85), the `BabokSection` dataclass (117–125), `convert_pdf_to_markdown` (238–267), and `class MarkdownBabokParser` (270–352).
3. Keep the legacy `BabokPdfParser` (raw-fitz) class but replace its two `if chapter not in BABOK_KA_CHAPTERS:` checks (≈198, ≈323) with a module-level set built once from the course; simplest: pass the KA chapter set into the function. Since `BabokPdfParser` is unused by the markdown path, instead delete its body usages by gating: at the top of `parse_babok_pdf`, set `ka_chapters = set(self.allowed_chapters)` and add `allowed_chapters` to its `__init__` too. (If `BabokPdfParser` is dead code in main(), leave it deleted — verify with `grep -n "BabokPdfParser(" scripts/extract_babok_concepts.py`; if no constructor call exists, delete the class entirely.)
4. At the markdown parse site (≈878), the surrounding `main()` already has `course_id, knowledge_areas` from `get_cbap_course_id()`. Build the map and pass chapters:

```python
        chapter_to_ka = ka_chapter_map(knowledge_areas)
        allowed = frozenset(chapter_to_ka)
        md_path = markdown_path or convert_pdf_to_markdown(pdf_path)
        sections = CorpusMarkdownParser(md_path, allowed_chapters=allowed).parse()
```

5. Replace the chapter→KA lookup at ≈424 (`ka_id = BABOK_KA_CHAPTERS.get(section.chapter)`) with `ka_id = chapter_to_ka.get(section.chapter)`. If `link_concept`/extractor is a method without access to `chapter_to_ka`, pass it in as a constructor arg to `Gpt4ConceptExtractor` or as a function parameter — follow the existing call site.

- [ ] **Step 4: Run tests to verify pass + import smoke**

Run:
```
apps/api/.venv/bin/python -m pytest scripts/tests/test_corpus_markdown.py -v
apps/api/.venv/bin/python -c "import sys; sys.path.insert(0,'scripts'); import extract_babok_concepts"
```
Expected: pytest PASS (4 tests); import prints nothing and exits 0.

- [ ] **Step 5: Commit**

```bash
git add scripts/extract_babok_concepts.py scripts/tests/test_corpus_markdown.py
git commit -m "refactor: extract_babok_concepts uses shared corpus parser, no hardcoded chapters"
```

---

### Task 3: Add `corpus_config` column to `courses`

**Files:**
- Modify: `apps/api/src/models/course.py` (add column after `knowledge_areas`, ≈line 42).
- Create: `migrations/versions/<rev>_add_course_corpus_config.py` (via autogenerate).

**Interfaces:**
- Produces: `Course.corpus_config: Mapped[dict | None]` (JSONB, nullable).

- [ ] **Step 1: Add the column to the model**

In `apps/api/src/models/course.py`, after the `knowledge_areas` column:

```python
    # Per-course corpus chunking config (chapter scope, heading style).
    # Null => default to KA chapters only (derived from knowledge_areas).
    corpus_config = Column(JSONB, nullable=True)
```

- [ ] **Step 2: Generate the migration**

Run:
```
cd /mnt/e/TOOLMAKER/PYTHON/LearnR_2/apps/api && .venv/bin/alembic revision --autogenerate -m "add course corpus_config"
```
Expected: a new file under `migrations/versions/` whose `down_revision = 'z6u7v8w9x0y1'`, with `op.add_column('courses', sa.Column('corpus_config', postgresql.JSONB(...), nullable=True))` in `upgrade()` and `op.drop_column('courses', 'corpus_config')` in `downgrade()`. Open it and confirm it contains ONLY the corpus_config add/drop (delete any spurious autogen ops unrelated to this change).

- [ ] **Step 3: Apply and verify the migration**

Run:
```
cd /mnt/e/TOOLMAKER/PYTHON/LearnR_2/apps/api && .venv/bin/alembic upgrade head
docker exec -e PGPASSWORD=learnr123 learnr-postgres-dev psql -U learnr -d learnr_dev -t -A -c "select column_name from information_schema.columns where table_name='courses' and column_name='corpus_config';"
```
Expected: prints `corpus_config`.

- [ ] **Step 4: Backfill cbap config**

Run:
```
docker exec -e PGPASSWORD=learnr123 learnr-postgres-dev psql -U learnr -d learnr_dev -c "update courses set corpus_config = '{\"chunk_chapters\": {\"min\": 1, \"max\": 8}, \"heading_style\": \"numbered\"}'::jsonb where slug='cbap';"
docker exec -e PGPASSWORD=learnr123 learnr-postgres-dev psql -U learnr -d learnr_dev -t -A -c "select corpus_config from courses where slug='cbap';"
```
Expected: the JSON prints with `chunk_chapters` min 1 max 8.

- [ ] **Step 5: Commit**

```bash
git add apps/api/src/models/course.py migrations/versions/*add_course_corpus_config*.py
git commit -m "feat: add courses.corpus_config column for per-course chunk scope"
```

---

### Task 4: Config resolution in `parse_corpus.py` (`resolve_chunk_chapters` + CLI + heading_style)

**Files:**
- Modify: `scripts/parse_corpus.py` (add helper + dataclass near top; add CLI args in `main()`'s argparse).
- Test: `scripts/tests/test_parse_corpus_config.py`

**Interfaces:**
- Produces:
  - `@dataclass ChapterScope(min:int, max:int)`
  - `resolve_chunk_chapters(course, cli_min:int|None, cli_max:int|None) -> ChapterScope`
  - `validate_heading_style(course) -> None` (raises `NotImplementedError` for non-`numbered`)

- [ ] **Step 1: Write failing tests**

Create `scripts/tests/test_parse_corpus_config.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `apps/api/.venv/bin/python -m pytest scripts/tests/test_parse_corpus_config.py -v`
Expected: FAIL — `ImportError: cannot import name 'resolve_chunk_chapters'`.

- [ ] **Step 3: Implement helpers in `parse_corpus.py`**

Add near the top of `scripts/parse_corpus.py` (after imports / dataclasses):

```python
@dataclass(frozen=True)
class ChapterScope:
    min: int
    max: int


def _ka_chapter_numbers(course) -> list[int]:
    nums = []
    for ka in course.knowledge_areas:
        prefix = ka.get("section_prefix")
        if prefix is not None:
            nums.append(int(str(prefix).split(".")[0]))
    return nums


def resolve_chunk_chapters(course, cli_min, cli_max) -> ChapterScope:
    """Chapter scope precedence: CLI > corpus_config > KA-chapter default."""
    cfg = (course.corpus_config or {}).get("chunk_chapters") or {}
    ka_nums = _ka_chapter_numbers(course)
    default_min, default_max = min(ka_nums), max(ka_nums)
    cmin = cli_min if cli_min is not None else cfg.get("min", default_min)
    cmax = cli_max if cli_max is not None else cfg.get("max", default_max)
    if cmin > cmax:
        raise ValueError(f"chunk chapter min ({cmin}) > max ({cmax})")
    return ChapterScope(int(cmin), int(cmax))


def validate_heading_style(course) -> None:
    style = (course.corpus_config or {}).get("heading_style", "numbered")
    if style != "numbered":
        raise NotImplementedError(
            f"heading_style {style!r} not supported; only 'numbered'"
        )
```

Add CLI args in `main()`'s argparse (next to `--max-tokens`):

```python
    parser.add_argument("--min-chapter", type=int, default=None,
                        help="Override corpus_config chunk_chapters.min")
    parser.add_argument("--max-chapter", type=int, default=None,
                        help="Override corpus_config chunk_chapters.max")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `apps/api/.venv/bin/python -m pytest scripts/tests/test_parse_corpus_config.py -v`
Expected: PASS (6 tests).

- [ ] **Step 5: Commit**

```bash
git add scripts/parse_corpus.py scripts/tests/test_parse_corpus_config.py
git commit -m "feat: per-course chunk chapter scope resolution in parse_corpus"
```

---

### Task 5: Wire markdown sectioning into `parse_corpus.py`

Replace the raw-fitz `parse_pdf()` path with the shared markdown parser, using the resolved chapter scope.

**Files:**
- Modify: `scripts/parse_corpus.py` (remove/bypass `parse_pdf`; update `main()` step 2; map `MarkdownSection` → `CorpusSection`).

**Interfaces:**
- Consumes: `CorpusMarkdownParser`, `MarkdownSection`, `convert_pdf_to_markdown`, `ka_chapter_map` from `utils.corpus_markdown`; `resolve_chunk_chapters`, `validate_heading_style` from Task 4.

- [ ] **Step 1: Add the import**

At the top of `scripts/parse_corpus.py` (after the `sys.path.append(... "scripts")` is NOT present — add it). Ensure scripts dir is importable, then import:

```python
sys.path.append(str(project_root / "scripts"))
from utils.corpus_markdown import (
    CorpusMarkdownParser,
    MarkdownSection,
    convert_pdf_to_markdown,
)
```

- [ ] **Step 2: Replace sectioning in `main()`**

In `main()`, replace the `sections = parse_pdf(str(pdf_path), course)` call (step 2) with:

```python
            validate_heading_style(course)
            scope = resolve_chunk_chapters(course, args.min_chapter, args.max_chapter)
            logger.info(f"Chunking chapters {scope.min}-{scope.max}")
            allowed = frozenset(range(scope.min, scope.max + 1))
            md_path = convert_pdf_to_markdown(str(pdf_path))
            md_sections = CorpusMarkdownParser(md_path, allowed_chapters=allowed).parse()
            ka_mapping = get_ka_mapping(course)
            sections = [
                CorpusSection(
                    section_ref=s.section_number,
                    title=s.title,
                    content=s.content,
                    knowledge_area_id=get_ka_from_section(s.section_number, ka_mapping),
                    page_numbers=[s.page_start, s.page_end],
                )
                for s in md_sections
            ]
            logger.info(f"Parsed {len(sections)} sections from markdown")
```

Delete the now-unused `parse_pdf()` function (and its `import fitz` if no longer referenced — verify with `grep -n "fitz" scripts/parse_corpus.py`).

- [ ] **Step 3: Smoke test the parse with a dry run**

Run:
```
cd /mnt/e/TOOLMAKER/PYTHON/LearnR_2 && apps/api/.venv/bin/python scripts/parse_corpus.py --course-slug cbap --pdf-path data/Corpus/BABOK_Guide_v3_Member.pdf --dry-run 2>&1 | tail -20
```
Expected: "Parsed N sections from markdown" with N ≈ 230+; report prints far more than 58 chunks (final count validated after Task 6). No exceptions.

- [ ] **Step 4: Commit**

```bash
git add scripts/parse_corpus.py
git commit -m "feat: parse_corpus sections from markdown via shared parser"
```

---

### Task 6: Rewrite `chunk_section()` with token-budget + hard fallback

**Files:**
- Modify: `scripts/parse_corpus.py` (replace `chunk_section`; add `_split_into_units` + `_split_oversized` helpers).
- Test: `scripts/tests/test_chunk_section.py`

**Interfaces:**
- Consumes: module-level `enc = tiktoken.get_encoding("cl100k_base")` (already defined in `parse_corpus.py`).
- Produces: `chunk_section(section, min_tokens=200, max_tokens=500, overlap_tokens=50) -> list[tuple[str,int]]` (signature unchanged).

- [ ] **Step 1: Write failing tests**

Create `scripts/tests/test_chunk_section.py`:

```python
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "scripts"))

import tiktoken
from parse_corpus import chunk_section, CorpusSection

enc = tiktoken.get_encoding("cl100k_base")


def _section(content):
    return CorpusSection(section_ref="3.1", title="T", content=content,
                         knowledge_area_id="ba-planning", page_numbers=[1])


def test_no_chunk_exceeds_max_tokens_with_no_blank_lines():
    # One giant paragraph, NO \n\n — the old splitter would emit one blob.
    giant = " ".join(f"word{i}" for i in range(5000))
    chunks = chunk_section(_section(giant), max_tokens=500)
    assert len(chunks) > 1
    for content, _ in chunks:
        assert len(enc.encode(content)) <= 500


def test_single_oversized_sentence_is_token_split():
    sentence = "x" * 20000  # no sentence boundaries at all
    chunks = chunk_section(_section(sentence), max_tokens=300)
    assert all(len(enc.encode(c)) <= 300 for c, _ in chunks)


def test_tiny_trailing_content_merges():
    # A normal paragraph plus a tiny tail should not leave a stub chunk.
    body = " ".join(f"word{i}" for i in range(450))
    tail = "tiny tail."
    chunks = chunk_section(_section(body + "\n\n" + tail), min_tokens=200, max_tokens=500)
    assert all(len(enc.encode(c)) >= 50 for c, _ in chunks)  # no 6-char stubs


def test_normal_paragraphs_grouped_to_target():
    paras = "\n\n".join(" ".join(f"w{i}" for i in range(120)) for _ in range(6))
    chunks = chunk_section(_section(paras), min_tokens=200, max_tokens=500)
    assert len(chunks) >= 1
    for content, _ in chunks:
        assert len(enc.encode(content)) <= 500
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `apps/api/.venv/bin/python -m pytest scripts/tests/test_chunk_section.py -v`
Expected: FAIL — `test_no_chunk_exceeds_max_tokens_with_no_blank_lines` produces a single oversized chunk (old behavior).

- [ ] **Step 3: Replace `chunk_section` and add helpers**

In `scripts/parse_corpus.py`, replace `chunk_section` (and keep `get_overlap`) with:

```python
def _split_oversized(text: str, max_tokens: int) -> List[str]:
    """Split a too-large unit by sentences, then by token window."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    out: List[str] = []
    buf: List[str] = []
    buf_tokens = 0
    for s in sentences:
        s_tokens = len(enc.encode(s))
        if s_tokens > max_tokens:
            if buf:
                out.append(" ".join(buf))
                buf, buf_tokens = [], 0
            toks = enc.encode(s)
            for i in range(0, len(toks), max_tokens):
                out.append(enc.decode(toks[i:i + max_tokens]))
        elif buf_tokens + s_tokens > max_tokens and buf:
            out.append(" ".join(buf))
            buf, buf_tokens = [s], s_tokens
        else:
            buf.append(s)
            buf_tokens += s_tokens
    if buf:
        out.append(" ".join(buf))
    return out


def _split_into_units(content: str, max_tokens: int) -> List[str]:
    """Paragraphs (\\n\\n) where possible; hard-split any paragraph over max_tokens."""
    units: List[str] = []
    for para in [p.strip() for p in content.split("\n\n") if p.strip()]:
        if len(enc.encode(para)) <= max_tokens:
            units.append(para)
        else:
            units.extend(_split_oversized(para, max_tokens))
    return units


def chunk_section(section, min_tokens: int = 200, max_tokens: int = 500,
                  overlap_tokens: int = 50) -> List[Tuple[str, int]]:
    """Chunk a section to <= max_tokens units, never relying on \\n\\n alone."""
    units = _split_into_units(section.content, max_tokens)
    chunks: List[Tuple[str, int]] = []
    current: List[str] = []
    current_tokens = 0

    for unit in units:
        unit_tokens = len(enc.encode(unit))
        if current_tokens + unit_tokens > max_tokens and current:
            chunks.append(("\n\n".join(current), len(chunks)))
            overlap_text = get_overlap(current, overlap_tokens)
            current = [overlap_text, unit] if overlap_text else [unit]
            current_tokens = len(enc.encode("\n\n".join(current)))
        else:
            current.append(unit)
            current_tokens += unit_tokens

    if current:
        chunks.append(("\n\n".join(current), len(chunks)))

    # Merge a tiny trailing chunk into its predecessor (avoid stubs).
    if len(chunks) > 1 and len(enc.encode(chunks[-1][0])) < min_tokens:
        last_content, _ = chunks.pop()
        prev_content, prev_idx = chunks.pop()
        chunks.append((prev_content + "\n\n" + last_content, prev_idx))

    return chunks
```

Ensure `re` is imported at the top of `parse_corpus.py` (it already is — used by the old `parse_pdf`; keep the import even after deleting `parse_pdf`).

- [ ] **Step 4: Run tests to verify pass**

Run: `apps/api/.venv/bin/python -m pytest scripts/tests/test_chunk_section.py scripts/tests/test_parse_corpus_config.py scripts/tests/test_corpus_markdown.py -v`
Expected: PASS (all).

- [ ] **Step 5: Commit**

```bash
git add scripts/parse_corpus.py scripts/tests/test_chunk_section.py
git commit -m "fix: token-budget chunker with sentence/token hard fallback"
```

---

### Task 7: Run the full pipeline + verify

Not TDD — this regenerates data and validates end-to-end. Run only after Tasks 1–6 are committed and Task 3's migration + backfill are applied.

**Files:** none (data + Qdrant only).

- [ ] **Step 1: Backup `reading_chunks`**

```bash
docker exec -e PGPASSWORD=learnr123 learnr-postgres-dev pg_dump -U learnr -d learnr_dev -t reading_chunks --data-only > "$CLAUDE_JOB_DIR/tmp/reading_chunks_backup_pre_markdown.sql"
```

- [ ] **Step 2: Clean re-parse (writes PG)**

```bash
cd /mnt/e/TOOLMAKER/PYTHON/LearnR_2
apps/api/.venv/bin/python scripts/parse_corpus.py --course-slug cbap --pdf-path data/Corpus/BABOK_Guide_v3_Member.pdf --replace 2>&1 | tail -25
```
Expected: total chunks ≈ 280–500; "Chunks without concepts" only for chapters 1–2.

- [ ] **Step 3: Clear orphaned cbap vectors in Qdrant**

```bash
curl -s -X POST "http://localhost:6333/collections/reading_chunks/points/delete?wait=true" -H 'Content-Type: application/json' -d '{"filter":{"must":[{"key":"course_id","match":{"value":"1b8a4860-156f-4d06-8393-85c4088db2d9"}}]}}'
```
Expected: `{"result":{...,"status":"completed"},"status":"ok"}`.

- [ ] **Step 4: Generate + upload embeddings**

```bash
cd /mnt/e/TOOLMAKER/PYTHON/LearnR_2
OPENAI_API_KEY="$(grep '^OPENAI_API_KEY' apps/api/.env | tail -1 | cut -d= -f2-)" apps/api/.venv/bin/python scripts/generate_chunk_embeddings.py --course-slug cbap --force 2>&1 | tail -20
```
Expected: "Verification status: PASS"; Chunks in PostgreSQL == Vectors in Qdrant.

- [ ] **Step 5: Verify data quality**

```bash
docker exec -e PGPASSWORD=learnr123 learnr-postgres-dev psql -U learnr -d learnr_dev -t -A -c "
select 'cbap_chunks', count(*) from reading_chunks where course_id='1b8a4860-156f-4d06-8393-85c4088db2d9'
union all
select 'unresolved_cbap_refs', count(*) from reading_chunks rc cross join unnest(rc.concept_ids) cid left join concepts c on c.id=cid where c.id is null and rc.course_id='1b8a4860-156f-4d06-8393-85c4088db2d9'
union all
select 'oversize_chunks', count(*) from reading_chunks where course_id='1b8a4860-156f-4d06-8393-85c4088db2d9' and length(content) > 4000;"
```
Expected: `cbap_chunks` 280–500; `unresolved_cbap_refs` 0; `oversize_chunks` 0 (no blobs; ~4000 chars ≈ 1000 tokens, safely above the 500-token cap).

- [ ] **Step 6: Final commit (CSV artifact + CHANGELOG)**

```bash
cd /mnt/e/TOOLMAKER/PYTHON/LearnR_2
git add scripts/output/reading_chunks_export.csv CHANGELOG.md
git commit -m "chore: regenerate reading chunks from markdown pipeline"
```
(Add a CHANGELOG entry under Fixed/Changed referencing #12 and the course-agnostic chunking.)

---

## Self-Review

**Spec coverage:**
- corpus_config column + defaults → Task 3 + Task 4 (`resolve_chunk_chapters`). ✓
- Generic shared module / no hardcoded chapters → Task 1, Task 2. ✓
- Fixed chunker (no `\n\n` reliance, hard fallback, no stubs) → Task 6. ✓
- Concept-extraction parity → Task 1 parity tests + Task 2 guard + import smoke. ✓
- heading_style `numbered`-only → Task 4. ✓
- Re-run + verification → Task 7. ✓
- KA derived from section_prefix → Task 1 `ka_chapter_map`, Task 4 `_ka_chapter_numbers`. ✓

**Placeholder scan:** No TBD/TODO; all code steps contain full code. ✓

**Type consistency:** `ChapterScope(min,max)` used consistently (Tasks 4–5); `CorpusMarkdownParser(md_path, allowed_chapters)`, `MarkdownSection`, `ka_chapter_map` names match across Tasks 1/2/5; `chunk_section` signature preserved (Task 6). ✓
