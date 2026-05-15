"""Searcher abstract base + the candidate shape.

A `Searcher` returns `ChunkCandidate`s — not yet persisted, just hits.
The retrieve stage (`sea2.conductor.retrieve`) is what mints `Chunk`s
from candidates and persists them with stable IDs.

Two concrete implementations ship in Phase 2:
  - `SubprocessSearcher` — spawns Claude Code / Codex with a search-and-fetch
    prompt and parses the JSON response.
  - `LocalCorpusSearcher` — BM25 over a pre-indexed local corpus.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sea2.chunks import ChunkMime

DEFAULT_K = 5


@dataclass(frozen=True)
class ChunkCandidate:
    """A search hit before it is admitted to the store.

    The retrieve stage takes a candidate, computes its `chunk_id`, and
    appends a `Chunk` to the store. Candidates and chunks are deliberately
    separate types — candidates can have minor variations (e.g. different
    snippet windows) that resolve to identical chunks after canonicalisation.
    """

    url: str
    text: str
    start_offset: int
    end_offset: int
    mime: ChunkMime
    searcher: str
    query: str
    title: str | None = None
    source_hash: str | None = None
    score: float | None = None
    extra: dict[str, object] = field(default_factory=dict)


class Searcher(ABC):
    """Returns at most `k` candidates for `query`.

    The implementation owns its own fetch + chunk pipeline. A Searcher MUST
    set `searcher` on each returned candidate to a stable identifier so the
    retrieve stage can attribute each chunk to its source pipeline.
    """

    name: str = "searcher"

    @abstractmethod
    def search(self, query: str, *, k: int = DEFAULT_K) -> list[ChunkCandidate]:
        """Return ranked candidates. Empty list = no hits, NOT an error."""


__all__ = [
    "DEFAULT_K",
    "ChunkCandidate",
    "Searcher",
]
