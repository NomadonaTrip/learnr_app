# Course-Agnostic Markdown Corpus Chunking — Design

**Date:** 2026-06-27
**Status:** Proposed
**Related:** Issue #12 (rebuild reading_chunks concept links). #12's data fix is already landed on `feature/rebuild-reading-chunk-links`; this spec covers the deeper parser rewrite that produces a *proper*, course-agnostic chunk set.

## Problem

`scripts/parse_corpus.py` parses the corpus into `reading_chunks` using raw PyMuPDF (`fitz`) text extraction plus a line-regex section detector, then chunks each section by splitting on blank-line (`\n\n`) boundaries. Both steps fail on the BABOK corpus:

1. **Under-segmentation.** The line-regex finds only ~35 distinct sections (mostly top-level: `4`, `6.1`) vs. the **231 section refs** the concepts span. Real subsections (`6.1.1`, …) are never detected as boundaries.
2. **Broken splitter.** `fitz` output uses single `\n` line breaks and essentially no `\n\n`. Since `chunk_section()` only splits *between* `\n\n` paragraphs, sections with no blank lines become one un-splittable chunk.

Result: 58 cbap chunks — 42 header-only stubs (6–317 chars) and a few giant blobs (one is **466,987 chars**). ~80% of corpus text is trapped in 2 unusable chunks.

Concept extraction (`extract_babok_concepts.py`) already solved this with a markdown pipeline (`pymupdf4llm` → `MarkdownBabokParser`, 231 sections / 1,197 concepts), but it is **CBAP-hardcoded** (a `BABOK_KA_CHAPTERS = {3..8}` constant drives its sectioning and KA assignment), and `parse_corpus.py` was never migrated to it.

## Goals

1. Rewrite `parse_corpus.py`'s sectioning + chunking to reuse a markdown pipeline, producing a proper chunk set (no stubs, no blobs, 200–500 tokens each).
2. Make the chunking pipeline **course/corpus-agnostic**: no hardcoded chapter numbers or course names. An admin can add a course (slug + `knowledge_areas` + `corpus_config`) and run the pipeline unchanged.
3. Make the chapter scope **configurable per course** (persisted), with a CLI override for one-off runs. (Trainer console will later write this config; not built now.)

## Design

### 1. Per-course corpus config — new `courses.corpus_config` column

Add a nullable `corpus_config` JSONB column to `courses` (alembic migration). Shape:

```json
{
  "chunk_chapters": { "min": 1, "max": 8 },
  "heading_style": "numbered"
}
```

- `chunk_chapters.{min,max}` — inclusive top-level chapter range to chunk into reading material.
- `heading_style` — extension point. **Only `"numbered"` is implemented** (hierarchical `N.N.N` headings, as in BABOK/PMBOK-style guides). Any other value raises a clear `NotImplementedError`. Future styles (e.g. `"atx"`, `"named"`) are out of scope.

**Defaults when `corpus_config` is null:** derive a safe default of *KA chapters only* — `min`/`max` = the min/max of the integer `section_prefix` values in `knowledge_areas`. So a new course with no config chunks exactly its KA chapters; opting into intro/extra chapters is explicit.

**Migration backfill:** set cbap's `corpus_config` to `{"chunk_chapters": {"min": 1, "max": 8}, "heading_style": "numbered"}` (the chosen all-chapters-1–8 scope).

### 2. Shared, generic parser module — `scripts/utils/corpus_markdown.py`

Move out of `extract_babok_concepts.py` and **rename generic** (no "Babok"):

- `MarkdownSection` dataclass (`section_number`, `title`, `content`, `chapter`, `depth`, `page_start`, `page_end`) — renamed from `BabokSection`.
- `convert_pdf_to_markdown(pdf_path, md_path=None) -> str` (pymupdf4llm; reuses cached `.md`).
- `CorpusMarkdownParser(md_path, allowed_chapters: frozenset[int])` — renamed from `MarkdownBabokParser`. **No internal chapter constant**; the caller passes `allowed_chapters`.
- Helper `ka_chapter_map(knowledge_areas) -> dict[int, str]` — builds `{chapter_int: ka_id}` from each KA's `section_prefix`. Replaces the hardcoded `BABOK_KA_CHAPTERS` everywhere.

**Parser boundary rules (generic):**
- A numbered heading whose chapter ∈ `allowed_chapters` starts a new section.
- A numbered heading whose chapter is **above** `max(allowed_chapters)` finalizes the current section and **suspends accumulation** until the next in-range heading (prevents trailing chapters — Techniques/appendices — from polluting the last section).
- Non-numbered / below-range headings keep the existing fold-into-content behavior.

`BABOK_KA_CHAPTERS` is deleted; both callers derive chapters from course config.

### 3. `parse_corpus.py` — course-agnostic sectioning

```
course   = course_repo.get_by_slug(slug)
ka_map   = ka_chapter_map(course.knowledge_areas)            # {3:'ba-planning',...}
scope    = resolve_chunk_chapters(course, cli_min, cli_max)  # corpus_config or null-default, CLI overrides
allowed  = frozenset(range(scope.min, scope.max + 1))
md_path  = convert_pdf_to_markdown(pdf_path)                  # cached .md reused
sections = CorpusMarkdownParser(md_path, allowed_chapters=allowed).parse()
```

Each `MarkdownSection` → the script's existing chunk-oriented `CorpusSection`. KA assigned via the existing `get_ka_from_section()` (course `section_prefix` map); chapters without a KA (e.g. 1–2) → `"unknown"`. New CLI flags `--min-chapter` / `--max-chapter` override `corpus_config`.

### 4. Fixed chunker — `chunk_section()`

Rewrite so it never depends on `\n\n` alone:
1. Split content into paragraphs on `\n\n` (markdown has real blank lines).
2. Accumulate toward the 200–500 token target (keep overlap behavior).
3. **Hard fallback for oversized units:** a paragraph > `max_tokens` is split into sentences; a sentence still > `max_tokens` is split by a fixed token window. Guarantees every chunk ≤ `max_tokens`; tiny trailing content merges into the previous chunk (no stubs).

Targets stay configurable via `--min-tokens` / `--max-tokens` (defaults 200 / 500).

### 5. `extract_babok_concepts.py` — minimal consume-the-shared-parser change

- Import `convert_pdf_to_markdown` / `CorpusMarkdownParser` / `ka_chapter_map` / `MarkdownSection` from the shared module; delete its local copies and `BABOK_KA_CHAPTERS`.
- Derive `allowed_chapters` and chapter→KA mapping from the course it already loads (`get_cbap_course_id`), so behavior for cbap is identical (`section_prefix` {3..8} == old constant).
- Full agnosticism of the *rest* of concept extraction (slug, KA-name mapping) is **out of scope** — tracked as a follow-up.

### 6. Re-run pipeline + verification

Same sequence validated for #12:
1. `parse_corpus.py --course-slug cbap --pdf-path data/Corpus/BABOK_Guide_v3_Member.pdf --replace`
2. Delete cbap vectors from Qdrant `reading_chunks` (filter `course_id`).
3. `generate_chunk_embeddings.py --course-slug cbap --force`
4. Verify: chunk count in ~280–500 range; no chunk > `max_tokens`; 0 unresolved cbap concept refs; PG chunk count == Qdrant cbap vector count (script verify PASS). Pre-change `pg_dump` of `reading_chunks` taken first.

## Testing

- **Unit (`scripts/tests/test_corpus_markdown.py`):**
  - **parity:** `CorpusMarkdownParser` with `allowed_chapters={3..8}` reproduces the prior ch 3–8 section list (numbers + titles) → concept extraction unaffected.
  - `allowed_chapters={1..8}` includes ch 1–2 sections.
  - out-of-range (ch 9+) heading finalizes + suspends (no tail pollution).
  - `ka_chapter_map` builds correctly from `section_prefix`.
  - `chunk_section`: no chunk exceeds `max_tokens`; a paragraph with no `\n\n` and > max tokens is still split; tiny tails merge.
  - `heading_style != "numbered"` raises `NotImplementedError`.
  - `resolve_chunk_chapters`: corpus_config used; null → KA-chapter default; CLI overrides win.
- **Manual:** the re-run verification above.

## Out of scope

- Generalizing the rest of `extract_babok_concepts.py` (slug, KA-name mapping) — follow-up.
- Non-`numbered` heading styles.
- Chapters beyond the configured scope (e.g. Techniques/Perspectives/appendices).
- Reading-library UI changes; trainer/admin console.

## Risks

- **Concept-extraction regression** from the refactor — mitigated by the parity unit test (no GPT re-run needed).
- **Schema migration** on `courses` — additive nullable column, low risk; existing rows default via the null-handling logic.
- **pymupdf4llm cache staleness** — `convert_pdf_to_markdown` reuses the existing `.md`; delete it to regenerate if the PDF changes (unchanged here).
