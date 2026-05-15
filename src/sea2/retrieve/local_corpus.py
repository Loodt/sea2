"""LocalCorpusSearcher: BM25 over a pre-indexed corpus.

Phase 2 ships BM25 only — sufficient for retrieving from a small, known
regulatory corpus (au-token's MPRDA / NEM:WA / FSCA / Bill 2025 / case law).
The dense-embedding hybrid is a Phase 3 add-on behind the `embeddings`
optional dep.

Index format is sqlite (see `index_corpus.py`):

  CREATE TABLE chunks (
    chunk_id TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    title TEXT,
    text TEXT NOT NULL,
    start_offset INTEGER NOT NULL,
    end_offset INTEGER NOT NULL,
    source_hash TEXT NOT NULL,
    mime TEXT NOT NULL,
    fetched_at TEXT NOT NULL
  );
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING

from rank_bm25 import BM25Okapi

from sea2.retrieve.searcher import DEFAULT_K, ChunkCandidate, Searcher

if TYPE_CHECKING:
    from sea2.chunks import ChunkMime


_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


def _tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text)]


class LocalCorpusSearcher(Searcher):
    """BM25 over a sqlite-backed pre-indexed corpus.

    The corpus is built once by `python -m sea2.retrieve.index_corpus`.
    Re-instantiating this class is cheap — the BM25 index is built in
    memory from the sqlite rows on construction. For larger corpora this
    becomes worth caching; Phase 2 keeps it simple.
    """

    name = "local-corpus"

    def __init__(self, corpus_path: Path | str) -> None:
        self.corpus_path = Path(corpus_path)
        if not self.corpus_path.exists():
            raise FileNotFoundError(
                f"corpus not found at {self.corpus_path} — run `python -m "
                f"sea2.retrieve.index_corpus <dir>` first"
            )
        self._rows: list[dict[str, object]] = []
        self._bm25: BM25Okapi | None = None
        self._load()

    def _load(self) -> None:
        conn = sqlite3.connect(self.corpus_path)
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.execute(
                "SELECT chunk_id, url, title, text, start_offset, end_offset, "
                "source_hash, mime, fetched_at FROM chunks"
            )
            self._rows = [dict(r) for r in cursor.fetchall()]
        finally:
            conn.close()
        if not self._rows:
            self._bm25 = None
            return
        tokenized = [_tokenize(str(r["text"])) for r in self._rows]
        self._bm25 = BM25Okapi(tokenized)

    def search(self, query: str, *, k: int = DEFAULT_K) -> list[ChunkCandidate]:
        if self._bm25 is None or not self._rows:
            return []
        tokens = _tokenize(query)
        if not tokens:
            return []
        scores = self._bm25.get_scores(tokens)
        ranked = sorted(
            range(len(self._rows)),
            key=lambda i: scores[i],
            reverse=True,
        )[:k]
        out: list[ChunkCandidate] = []
        for idx in ranked:
            row = self._rows[idx]
            if scores[idx] <= 0:
                continue
            mime_val: ChunkMime = str(row["mime"])  # type: ignore[assignment]
            title_raw = row["title"]
            out.append(
                ChunkCandidate(
                    url=str(row["url"]),
                    text=str(row["text"]),
                    start_offset=int(str(row["start_offset"])),
                    end_offset=int(str(row["end_offset"])),
                    mime=mime_val,
                    searcher=self.name,
                    query=query,
                    title=str(title_raw) if title_raw else None,
                    source_hash=str(row["source_hash"]),
                    score=float(scores[idx]),
                    extra={"fetched_at": str(row["fetched_at"])},
                )
            )
        return out


__all__ = ["LocalCorpusSearcher"]
