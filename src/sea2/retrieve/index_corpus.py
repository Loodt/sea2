"""Pre-index a local corpus directory into a sqlite index.

Usage::

    python -m sea2.retrieve.index_corpus path/to/corpus_dir [--output corpus.sqlite]

Walks `corpus_dir` recursively, extracts text from PDFs (pymupdf), HTML
(trafilatura), markdown, and plain text. Chunks per `chunker.chunk_text`,
hashes per `Chunk.make`, and writes one row per chunk to `corpus.sqlite`.

Idempotent: re-indexing the same directory produces the same chunk_ids;
duplicates are skipped via the PRIMARY KEY constraint.

For au-token, the bedrock regulatory PDFs (MPRDA, NEM:WA, FSCA Crypto
Declaration, the 2025 Bill, key cases) will live in `corpora/au-token-
regulatory/` and be indexed once per repo bump.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import sqlite3
import sys
from pathlib import Path

import trafilatura

from sea2.chunks import Chunk, ChunkMime, compute_source_hash
from sea2.retrieve.chunker import chunk_text
from sea2.retrieve.fetcher import _parse_pdf as parse_pdf_bytes

DEFAULT_OUTPUT = "corpus.sqlite"

# File-extension → mime classification. Unknown extensions are skipped.
_MIME_BY_SUFFIX: dict[str, ChunkMime] = {
    ".html": "text/html",
    ".htm": "text/html",
    ".xhtml": "text/html",
    ".pdf": "application/pdf",
    ".md": "text/markdown",
    ".markdown": "text/markdown",
    ".txt": "text/plain",
}


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """CREATE TABLE IF NOT EXISTS chunks (
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
    conn.commit()


def _file_to_chunks(path: Path, *, fetched_at: str) -> list[Chunk]:
    mime = _MIME_BY_SUFFIX.get(path.suffix.lower())
    if mime is None:
        return []

    # url-shaped identifier so the chunk row points back to a stable place
    url = path.absolute().as_uri()
    title = path.stem

    body = path.read_bytes()
    source_hash = compute_source_hash(body)

    if mime == "application/pdf":
        try:
            fetched = parse_pdf_bytes(url, url, body, source_hash)
        except Exception as e:  # noqa: BLE001 — log and continue, never abort the whole index
            print(f"  ! {path}: pdf parse failed: {e}", file=sys.stderr)
            return []
        text = fetched.text
    elif mime == "text/html":
        html = body.decode("utf-8", errors="replace")
        extracted = trafilatura.extract(
            html,
            favor_recall=True,
            include_comments=False,
            include_tables=True,
        )
        if not extracted:
            print(f"  ! {path}: trafilatura extracted no content", file=sys.stderr)
            return []
        text = extracted
    else:
        text = body.decode("utf-8", errors="replace")

    spans = chunk_text(text)
    return [
        Chunk.make(
            url=url,
            title=title,
            fetched_at=fetched_at,
            searcher="pre-indexed",
            query="",
            text=span.text,
            start_offset=span.start_offset,
            end_offset=span.end_offset,
            source_hash=source_hash,
            mime=mime,
        )
        for span in spans
    ]


def _insert_chunks(conn: sqlite3.Connection, chunks: list[Chunk]) -> int:
    inserted = 0
    for c in chunks:
        try:
            conn.execute(
                "INSERT INTO chunks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    c.chunk_id,
                    c.url,
                    c.title,
                    c.text,
                    c.start_offset,
                    c.end_offset,
                    c.source_hash,
                    c.mime,
                    c.fetched_at,
                ),
            )
            inserted += 1
        except sqlite3.IntegrityError:
            # Duplicate chunk_id — re-indexing the same content. Skip.
            continue
    conn.commit()
    return inserted


def index_corpus(corpus_dir: Path, output: Path) -> tuple[int, int]:
    """Index `corpus_dir` into `output`. Returns (files_indexed, chunks_inserted)."""
    if not corpus_dir.exists() or not corpus_dir.is_dir():
        raise FileNotFoundError(f"corpus dir not found or not a directory: {corpus_dir}")

    fetched_at = _dt.datetime.now(_dt.UTC).isoformat()
    conn = sqlite3.connect(output)
    try:
        _ensure_schema(conn)
        files_indexed = 0
        total_inserted = 0
        for path in sorted(corpus_dir.rglob("*")):
            if not path.is_file():
                continue
            chunks = _file_to_chunks(path, fetched_at=fetched_at)
            if not chunks:
                continue
            inserted = _insert_chunks(conn, chunks)
            files_indexed += 1
            total_inserted += inserted
            print(f"  + {path.relative_to(corpus_dir)}: {inserted} chunks")
    finally:
        conn.close()

    return files_indexed, total_inserted


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Pre-index a local corpus for LocalCorpusSearcher")
    parser.add_argument("corpus_dir", type=Path, help="Directory of source documents")
    parser.add_argument(
        "--output", type=Path, default=Path(DEFAULT_OUTPUT),
        help=f"Destination sqlite file (default: {DEFAULT_OUTPUT})",
    )
    args = parser.parse_args(argv)

    files, chunks = index_corpus(args.corpus_dir, args.output)
    print(f"\nDone. {files} files → {chunks} chunks → {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
