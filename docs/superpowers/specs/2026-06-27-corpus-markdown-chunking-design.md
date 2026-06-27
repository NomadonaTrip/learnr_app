# Markdown-based Corpus Chunking — Design

**Date:** 2026-06-27
**Status:** Proposed
**Related:** Issue #12 (rebuild reading_chunks concept links). #12's data fix is already landed on `feature/rebuild-reading-chunk-links`; this spec covers the deeper parser rewrite that produces a *proper* chunk set.

## Problem

`scripts/parse_corpus.py` parses the BABOK corpus into `reading_chunks` using raw PyMuPDF (`fitz`) text extraction plus a line-regex section detector, then chunks each section by splitting on blank-line (`\n\n`) paragraph boundaries.

Both steps fail on this corpus:

1. **Under-segmentation.** The line-regex finds only ~35 distinct sections (mostly top-level: `4`, `6.1`, `7.5`) vs. the **231 section refs** the concepts span. Real subsections (`6.1.1`, `6.1.2`, …) are never detected as boundaries, so their text stays glued to the parent.
2. **Broken splitter.** `fitz` output uses single `\n` line breaks and essentially **no `\n\n`**. Since `chunk_section()` only splits *between* `\n\n`-delimited paragraphs, sections with no blank lines become one un-splittable chunk.

Result: 58 cbap chunks, of which 42 are header-only stubs (6–317 chars) and a handful are giant blobs (one is **466,987 chars** — ~115k tokens — covering section "6.1"). ~80% of the corpus text is trapped in 2 unusable chunks.

Meanwhile, **concept extraction** (`extract_babok_concepts.py`) already solved this: it converts the PDF to heading-structured markdown via `pymupdf4llm` (`MarkdownBabokParser`) and got 1,197 concepts across 231 well-bounded sections. `parse_corpus.py` was never migrated to that path.

## Goal

Rewrite `parse_corpus.py`'s sectioning + chunking to reuse the proven markdown pipeline, producing a proper chunk set (~280–500 chunks, 200–500 tokens each, no stubs, no blobs) with concept links resolving by exact section-ref match. Cover **BABOK chapters 1–8** (per scope decision).

## Design

### 1. Shared parser module — `scripts/utils/babok_markdown.py`

Move three things out of `extract_babok_concepts.py` into a new shared module so both scripts import one source of truth:

- `BabokSection` dataclass (`section_number`, `title`, `content`, `chapter`, `depth`, `page_start`, `page_end`)
- `convert_pdf_to_markdown(pdf_path, md_path=None) -> str` (pymupdf4llm; reuses the cached `.md`)
- `MarkdownBabokParser`

`extract_babok_concepts.py` is updated to import these from the new module (its `BabokPdfParser` raw-fitz fallback can stay where it is or be removed if unused — out of scope; leave it).

**Chapter scope parameter.** `MarkdownBabokParser(md_path, allowed_chapters=frozenset({3,4,5,6,7,8}))`. The set of chapters whose numbered headings act as section boundaries.
- Concept extraction calls with the default (`{3..8}`) → behavior unchanged.
- Corpus chunking calls with `frozenset(range(1, 9))` → chapters 1–8.

**Out-of-range headings.** A numbered heading whose chapter is **above** the max allowed chapter (e.g. ch 9 Techniques, 10 Perspectives, 11 appendices) finalizes the current section and **suspends content accumulation** until the next in-range heading. This prevents trailing chapters from polluting the last in-range section (the blob bug at the tail). Headings *below* the current range or non-numbered content sub-headings keep the existing fold-into-content behavior.

**Parity guarantee.** A unit test asserts that, with default args, `MarkdownBabokParser` produces the same section list (numbers + titles) for chapters 3–8 as before the refactor — so concept extraction output is unaffected without needing an expensive GPT re-run.

### 2. `parse_corpus.py` sectioning

Replace `parse_pdf()` (raw fitz) with:

```
md_path = convert_pdf_to_markdown(pdf_path)            # cached .md reused
babok_sections = MarkdownBabokParser(md_path, allowed_chapters=frozenset(range(1, 9))).parse()
```

Map each `BabokSection` → the script's existing `CorpusSection` (carrying `section_ref`, `title`, `content`, `knowledge_area_id`, `page_numbers`). KA is assigned via the existing `get_ka_from_section()` using the course's `section_prefix` map; chapters 1–2 fall through to `"unknown"`.

### 3. Fixed chunker — `chunk_section()`

Rewrite so it never depends on `\n\n` alone:

1. Split content into paragraphs on `\n\n` (markdown has real blank lines).
2. Accumulate paragraphs toward the 200–500 token target (keep existing overlap behavior).
3. **Hard fallback for oversized units:** if a single paragraph exceeds `max_tokens`, split it into sentences; if a single sentence still exceeds `max_tokens`, split by a fixed token window. Guarantees every emitted chunk ≤ `max_tokens` (no blobs) and avoids header-only stubs by merging tiny trailing content into the previous chunk.

Targets stay configurable via existing `--min-tokens` / `--max-tokens` (defaults 200 / 500).

### 4. Concept linking + KA (unchanged logic)

`link_chunk_to_concepts()` (exact / parent / child section-ref match) is unchanged — but now mostly hits **exact** matches because chunk section refs (`3.2.1`) line up with concept `corpus_section_ref`. Chapters 1–2 chunks have no concepts (none exist there) → orphan reading material by design.

### 5. Re-run pipeline + verification

Same sequence already validated for #12:

1. `parse_corpus.py --course-slug cbap --pdf-path data/Corpus/BABOK_Guide_v3_Member.pdf --replace`
2. Delete cbap vectors from Qdrant `reading_chunks` (filter `course_id`), since new chunks have new UUIDs.
3. `generate_chunk_embeddings.py --course-slug cbap --force`
4. Verify:
   - chunk count in the ~280–500 range; no chunk > `max_tokens`; no header-only stubs
   - cbap concept refs: 0 unresolved (every non-orphan chunk links to existing concepts)
   - PG chunk count == Qdrant cbap vector count (script's verify PASS)

A pre-change `pg_dump` of `reading_chunks` is taken first (safety).

## Testing

- **Unit (`scripts/tests/test_babok_markdown.py`):**
  - parser parity: default args reproduce the ch 3–8 section list
  - `allowed_chapters=range(1,9)` includes ch 1–2 sections
  - out-of-range (ch 9+) heading finalizes + suspends (no tail pollution)
  - `chunk_section`: no chunk exceeds `max_tokens`; a paragraph with no `\n\n` and >max tokens is still split; tiny tails merge
- **Manual:** the re-run verification above.

## Out of scope

- Removing the legacy `BabokPdfParser` raw-fitz fallback from `extract_babok_concepts.py`.
- Chapters 9+ (Techniques, Perspectives, appendices).
- Reading-library UI changes.

## Risks

- **Concept-extraction regression** from the refactor — mitigated by the parity unit test (no GPT re-run needed).
- **pymupdf4llm cache staleness** — `convert_pdf_to_markdown` reuses the existing `.md`; if the PDF changed, delete the `.md` to regenerate. (PDF is unchanged here.)
