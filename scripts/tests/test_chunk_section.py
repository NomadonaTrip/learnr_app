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
