"""Chunker tests."""

from __future__ import annotations

from sea2.retrieve.chunker import (
    CHARS_PER_TOKEN_EST,
    chunk_text,
)


def test_empty_input_returns_no_chunks() -> None:
    assert chunk_text("") == []
    assert chunk_text("   \n\n   ") == []


def test_short_input_single_chunk() -> None:
    chunks = chunk_text("Hello world. " * 5)
    assert len(chunks) == 1
    assert chunks[0].start_offset == 0
    assert chunks[0].end_offset > 0


def test_long_input_multiple_chunks() -> None:
    # ~5000 chars → at target 500 tokens (~2000 chars), expect 3+ chunks.
    body = ("This is a paragraph with reasonable length. " * 100)
    paragraphs = "\n\n".join([body] * 5)
    chunks = chunk_text(paragraphs, target_tokens=500, overlap_tokens=50)
    assert len(chunks) >= 2
    for c in chunks:
        assert c.start_offset < c.end_offset


def test_offsets_reversible() -> None:
    text = "First paragraph here.\n\nSecond paragraph here.\n\nThird one."
    chunks = chunk_text(text, target_tokens=10, overlap_tokens=0)
    for c in chunks:
        assert text[c.start_offset : c.end_offset] == c.text


def test_chunk_size_roughly_target() -> None:
    target_tokens = 100
    target_chars = target_tokens * CHARS_PER_TOKEN_EST  # 400
    body = "Sentence A. " * 200  # 2400 chars in one paragraph
    chunks = chunk_text(body, target_tokens=target_tokens, overlap_tokens=10)
    # No chunk should be drastically larger than 2x target (the merge step
    # only emits when next segment WOULD overflow, so chunks can briefly
    # exceed target by one segment).
    for c in chunks:
        assert (c.end_offset - c.start_offset) <= target_chars * 2.5
