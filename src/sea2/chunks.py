"""Chunk schema.

Article §4.3 retrieve output: each fetched document is split into chunks
that the extract stage operates on. Findings reference chunks via
`Finding.admitted_chunk_id`, which is the integrate-time foreign key.

Chunk IDs are deterministic — `sha256(url + start_offset + text)` truncated
to 16 hex chars. This means re-fetching the same content produces the same
chunk_id, so dedupe and reproducibility are free.
"""

from __future__ import annotations

import hashlib
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

CHUNK_ID_HEX_LEN = 16

ChunkMime = Literal["text/html", "application/pdf", "text/plain", "text/markdown"]


def compute_chunk_id(url: str, start_offset: int, text: str) -> str:
    """Stable 16-hex-char chunk id. Reproducible across runs."""
    h = hashlib.sha256()
    h.update(url.encode("utf-8"))
    h.update(b"\x00")
    h.update(str(start_offset).encode("ascii"))
    h.update(b"\x00")
    h.update(text.encode("utf-8"))
    return h.hexdigest()[:CHUNK_ID_HEX_LEN]


def compute_source_hash(body: bytes | str) -> str:
    """sha256 of the full retrieved source body, hex. Used to dedupe fetches
    and to look up cached PDF metadata for `check_pdf_page_exists`.
    """
    data = body.encode("utf-8") if isinstance(body, str) else body
    return hashlib.sha256(data).hexdigest()


class Chunk(BaseModel):
    """A single text span admitted to the retrieve store.

    `chunk_id` is the integrate-time foreign key referenced by
    `Finding.admitted_chunk_id`. It is computed from `(url, start_offset,
    text)` and MUST be reproducible — never set this field by hand.
    """

    model_config = ConfigDict(extra="forbid")

    chunk_id: str = Field(min_length=CHUNK_ID_HEX_LEN, max_length=CHUNK_ID_HEX_LEN)
    url: str
    title: str | None = None
    fetched_at: str
    searcher: str
    query: str
    text: str
    start_offset: int = Field(ge=0)
    end_offset: int = Field(ge=0)
    source_hash: str
    mime: ChunkMime
    # Populated by D2's indexer / D4's pre-indexer. Optional at admit time;
    # required only for embedding-based retrieval ranking.
    embedding: list[float] | None = None

    @classmethod
    def make(
        cls,
        *,
        url: str,
        title: str | None,
        fetched_at: str,
        searcher: str,
        query: str,
        text: str,
        start_offset: int,
        end_offset: int,
        source_hash: str,
        mime: ChunkMime,
        embedding: list[float] | None = None,
    ) -> Chunk:
        """Construct a Chunk with a freshly-computed chunk_id.

        Use this rather than `Chunk(...)` directly so the id stays in sync
        with `(url, start_offset, text)`.
        """
        cid = compute_chunk_id(url, start_offset, text)
        return cls(
            chunk_id=cid,
            url=url,
            title=title,
            fetched_at=fetched_at,
            searcher=searcher,
            query=query,
            text=text,
            start_offset=start_offset,
            end_offset=end_offset,
            source_hash=source_hash,
            mime=mime,
            embedding=embedding,
        )


__all__ = [
    "CHUNK_ID_HEX_LEN",
    "Chunk",
    "ChunkMime",
    "compute_chunk_id",
    "compute_source_hash",
]
