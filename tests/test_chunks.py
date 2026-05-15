"""Chunk schema + store tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from pydantic import ValidationError

from sea2.chunks import (
    CHUNK_ID_HEX_LEN,
    Chunk,
    compute_chunk_id,
    compute_source_hash,
)
from sea2.store import (
    atomic_append_jsonl,
    chunks_path,
    find_chunk_by_id,
    read_chunks,
)

if TYPE_CHECKING:
    from pathlib import Path


def _chunk(idx: int, *, url: str | None = None, text: str | None = None) -> Chunk:
    return Chunk.make(
        url=url or "https://example.com/doc",
        title="t",
        fetched_at="2026-05-15T00:00:00Z",
        searcher="test",
        query="q",
        text=text or f"chunk text {idx}",
        start_offset=idx * 100,
        end_offset=idx * 100 + 80,
        source_hash=compute_source_hash(b"full-source-body"),
        mime="text/html",
    )


def test_chunk_id_deterministic() -> None:
    a = compute_chunk_id("https://example.com/x", 100, "hello world")
    b = compute_chunk_id("https://example.com/x", 100, "hello world")
    assert a == b
    assert len(a) == CHUNK_ID_HEX_LEN


def test_chunk_id_differs_on_offset_change() -> None:
    a = compute_chunk_id("https://example.com/x", 100, "hello")
    b = compute_chunk_id("https://example.com/x", 200, "hello")
    assert a != b


def test_chunk_id_differs_on_url_change() -> None:
    a = compute_chunk_id("https://example.com/a", 0, "hello")
    b = compute_chunk_id("https://example.com/b", 0, "hello")
    assert a != b


def test_chunk_make_sets_id() -> None:
    c = _chunk(0)
    expected = compute_chunk_id(c.url, c.start_offset, c.text)
    assert c.chunk_id == expected


def test_chunk_roundtrip_via_json() -> None:
    c = _chunk(0)
    parsed = Chunk.model_validate_json(c.model_dump_json())
    assert parsed == c


def test_chunk_id_length_enforced() -> None:
    with pytest.raises(ValidationError):
        Chunk(
            chunk_id="too-short",
            url="https://example.com/x",
            title=None,
            fetched_at="2026-05-15T00:00:00Z",
            searcher="test",
            query="q",
            text="t",
            start_offset=0,
            end_offset=1,
            source_hash="abc",
            mime="text/html",
        )


def test_chunk_extra_fields_rejected() -> None:
    raw = _chunk(0).model_dump()
    raw["surprise"] = "x"
    with pytest.raises(ValidationError):
        Chunk.model_validate(raw)


def test_chunks_roundtrip_through_store(tmp_path: Path) -> None:
    cs = [_chunk(i) for i in range(3)]
    for c in cs:
        atomic_append_jsonl(chunks_path(tmp_path), c)
    out = read_chunks(tmp_path)
    assert out == cs


def test_find_chunk_by_id_resolves(tmp_path: Path) -> None:
    cs = [_chunk(i) for i in range(3)]
    for c in cs:
        atomic_append_jsonl(chunks_path(tmp_path), c)
    found = find_chunk_by_id(tmp_path, cs[1].chunk_id)
    assert found == cs[1]


def test_find_chunk_by_id_missing_returns_none(tmp_path: Path) -> None:
    assert find_chunk_by_id(tmp_path, "0123456789abcdef") is None


def test_same_text_same_offset_same_url_dedupes(tmp_path: Path) -> None:
    # Re-fetching the same content produces the same chunk_id, so a dedupe
    # check by id is sufficient.
    a = _chunk(5)
    b = _chunk(5)
    assert a.chunk_id == b.chunk_id


def test_source_hash_deterministic() -> None:
    a = compute_source_hash("hello world")
    b = compute_source_hash(b"hello world")
    assert a == b
    assert len(a) == 64  # full sha256 hex
