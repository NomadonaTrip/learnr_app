import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "scripts"))

import tiktoken
from parse_corpus import chunk_section, generate_chunk_title, CorpusSection

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


def test_accumulation_path_never_exceeds_max_tokens():
    # Two paragraphs of exactly 250 tokens each — the "\n\n" separator tips the
    # joined chunk over 500 if separators aren't counted in the overflow check.
    tok_250 = enc.decode(enc.encode(" ".join(f"word{i}" for i in range(5000)))[:250])
    content = tok_250 + "\n\n" + tok_250
    chunks = chunk_section(_section(content), max_tokens=500)
    for c, _ in chunks:
        assert len(enc.encode(c)) <= 500


def test_normal_paragraphs_grouped_to_target():
    paras = "\n\n".join(" ".join(f"w{i}" for i in range(120)) for _ in range(6))
    chunks = chunk_section(_section(paras), min_tokens=200, max_tokens=500)
    assert len(chunks) >= 1
    for content, _ in chunks:
        assert len(enc.encode(content)) <= 500


# ---------------------------------------------------------------------------
# generate_chunk_title tests
# ---------------------------------------------------------------------------

def _sec(title, ref="3.1.1"):
    return CorpusSection(section_ref=ref, title=title, content="x",
                         knowledge_area_id="k", page_numbers=[0, 0])


def test_empty_title_falls_back_to_section_ref():
    t = generate_chunk_title(_sec(""), 0, 1)
    assert t and t.strip()           # non-empty
    assert "3.1.1" in t


def test_whitespace_title_falls_back():
    assert generate_chunk_title(_sec("   "), 0, 1).strip()


def test_nonempty_title_unchanged_single():
    assert generate_chunk_title(_sec("Plan Approach"), 0, 1) == "Plan Approach"


def test_nonempty_title_multichunk_suffix():
    assert generate_chunk_title(_sec("Plan Approach"), 1, 3) == "Plan Approach - Part 2"


def test_empty_title_multichunk_suffix_includes_ref():
    t = generate_chunk_title(_sec(""), 1, 3)
    assert "3.1.1" in t
    assert "Part 2" in t


# ---------------------------------------------------------------------------
# Fix 1: _split_oversized never emits a unit exceeding max_tokens
# ---------------------------------------------------------------------------

def test_split_oversized_units_never_exceed_max_tokens():
    from parse_corpus import _split_oversized
    # Many short sentences whose " ".join re-tokenizes above the cap due to
    # the additive individual-count approximation missing inter-word tokens.
    text = ". ".join(f"sentence number {i} has some words" for i in range(400)) + "."
    for unit in _split_oversized(text, max_tokens=200):
        assert len(enc.encode(unit)) <= 200
