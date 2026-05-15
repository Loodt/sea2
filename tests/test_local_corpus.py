"""LocalCorpusSearcher tests against a small in-memory sqlite fixture."""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

import pytest

from sea2.retrieve.local_corpus import LocalCorpusSearcher

if TYPE_CHECKING:
    from pathlib import Path


def _build_corpus(path: Path, rows: list[dict]) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            """CREATE TABLE chunks (
                chunk_id TEXT PRIMARY KEY,
                url TEXT NOT NULL,
                title TEXT,
                text TEXT NOT NULL,
                start_offset INTEGER NOT NULL,
                end_offset INTEGER NOT NULL,
                source_hash TEXT NOT NULL,
                mime TEXT NOT NULL,
                fetched_at TEXT NOT NULL
            )"""
        )
        for r in rows:
            conn.execute(
                "INSERT INTO chunks VALUES (:chunk_id,:url,:title,:text,:start_offset,"
                ":end_offset,:source_hash,:mime,:fetched_at)",
                r,
            )
        conn.commit()
    finally:
        conn.close()


def _row(idx: int, text: str) -> dict:
    return {
        "chunk_id": f"chunk{idx:013d}",
        "url": f"https://example.com/{idx}",
        "title": f"Doc {idx}",
        "text": text,
        "start_offset": 0,
        "end_offset": len(text),
        "source_hash": "deadbeef" * 8,
        "mime": "text/html",
        "fetched_at": "2026-05-15T00:00:00Z",
    }


def test_missing_corpus_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        LocalCorpusSearcher(tmp_path / "missing.sqlite")


def test_query_returns_top_ranked(tmp_path: Path) -> None:
    corpus = tmp_path / "c.sqlite"
    _build_corpus(
        corpus,
        [
            _row(0, "The MPRDA regulates active mining rights in South Africa."),
            _row(1, "The Ataqua case clarified pre-2004 dumps as common-law property."),
            _row(
                2,
                "FSCA declared crypto assets financial products in October 2022.",
            ),
        ],
    )
    s = LocalCorpusSearcher(corpus)
    out = s.search("FSCA crypto asset declaration", k=2)
    assert len(out) >= 1
    assert "FSCA" in out[0].text
    assert out[0].searcher == "local-corpus"


def test_no_matches_returns_empty(tmp_path: Path) -> None:
    corpus = tmp_path / "c.sqlite"
    _build_corpus(corpus, [_row(0, "irrelevant content about cooking")])
    s = LocalCorpusSearcher(corpus)
    out = s.search("xyzzy abracadabra nonexistent zorbax")
    assert out == []


def test_empty_corpus_returns_empty(tmp_path: Path) -> None:
    corpus = tmp_path / "empty.sqlite"
    _build_corpus(corpus, [])
    s = LocalCorpusSearcher(corpus)
    assert s.search("anything") == []
