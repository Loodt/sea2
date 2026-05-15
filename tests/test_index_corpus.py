"""index_corpus tests against a small fixture directory."""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

from sea2.retrieve.index_corpus import index_corpus
from sea2.retrieve.local_corpus import LocalCorpusSearcher

if TYPE_CHECKING:
    from pathlib import Path


def _populate(corpus_dir: Path) -> None:
    (corpus_dir / "doc1.md").write_text(
        "# Doc 1\n\nThe MPRDA regulates active mining rights in South Africa.\n\n"
        "Pre-2004 dumps fall outside this scheme per the Ataqua case.\n",
        encoding="utf-8",
    )
    (corpus_dir / "doc2.txt").write_text(
        "FSCA declared crypto assets financial products on October 2022. "
        "This brought CASP licensing into the regulatory perimeter.",
        encoding="utf-8",
    )
    (corpus_dir / "doc3.md").write_text(
        "# Doc 3\n\nNEMA section 28 establishes the duty of care for environmental "
        "liability across all activities, regardless of mining authorisation regime.",
        encoding="utf-8",
    )
    (corpus_dir / "doc4.txt").write_text(
        "Cooking recipes for pasta and sauces unrelated to any regulatory topic.",
        encoding="utf-8",
    )
    (corpus_dir / "skip.binary").write_bytes(b"\x00\x01\x02")


def test_indexes_md_and_txt(tmp_path: Path) -> None:
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    _populate(corpus)
    out = tmp_path / "corpus.sqlite"
    files, chunks = index_corpus(corpus, out)
    assert files == 4  # binary skipped
    assert chunks >= 4


def test_rebuild_is_idempotent(tmp_path: Path) -> None:
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    _populate(corpus)
    out = tmp_path / "corpus.sqlite"
    index_corpus(corpus, out)
    _, chunks1 = index_corpus(corpus, out)
    assert chunks1 == 0  # all duplicates on second run
    # Total rows still equals first run.
    conn = sqlite3.connect(out)
    try:
        cnt = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    finally:
        conn.close()
    assert cnt >= 4


def test_indexed_corpus_searchable(tmp_path: Path) -> None:
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    _populate(corpus)
    out = tmp_path / "corpus.sqlite"
    index_corpus(corpus, out)

    s = LocalCorpusSearcher(out)
    results = s.search("FSCA crypto declaration", k=3)
    assert len(results) >= 1
    assert any("FSCA" in r.text for r in results)


def test_missing_dir_raises(tmp_path: Path) -> None:
    out = tmp_path / "x.sqlite"
    try:
        index_corpus(tmp_path / "does-not-exist", out)
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("expected FileNotFoundError")
