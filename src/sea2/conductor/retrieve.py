"""Retrieve stage: search → chunk → store.

For each configured Searcher, run the query, normalise the returned text
into chunks, and persist them with stable `chunk_id`s. Dedupe is automatic
— `Chunk.make()` derives the id from `(url, start_offset, text)`, so
re-running retrieve on the same query reuses existing chunks rather than
re-appending.

Failures emit `RETRIEVE_FAIL` events with the searcher name and reason.
Successes emit one `RETRIEVE_OK` per admitted chunk_id (so the events
ledger is a complete record of retrieve provenance).
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from sea2.chunks import Chunk, compute_source_hash
from sea2.events import Event, EventType, emit
from sea2.retrieve.chunker import chunk_text
from sea2.retrieve.fetcher import FetchError, fetch_url
from sea2.retrieve.searcher import DEFAULT_K
from sea2.store import atomic_append_jsonl, chunks_path, read_chunks

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    import httpx

    from sea2.retrieve.searcher import ChunkCandidate, Searcher


CANDIDATE_TEXT_MIN_CHARS = 200


@dataclass(frozen=True)
class RetrieveResult:
    """Outcome of one retrieve call.

    `admitted_chunk_ids` is the ordered list of chunk_ids the extract
    stage should use as the only input to its prompt.
    """

    admitted_chunk_ids: tuple[str, ...] = ()
    duplicates: tuple[str, ...] = ()
    failures: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    events_emitted: int = 0


def _now_iso() -> str:
    return _dt.datetime.now(_dt.UTC).isoformat()


def retrieve(
    project_dir: Path | str,
    question: str,
    *,
    searchers: Iterable[Searcher],
    k_per_searcher: int = DEFAULT_K,
    refetch_short_text: bool = True,
    http_client: httpx.Client | None = None,
) -> RetrieveResult:
    """Run all searchers for `question`; persist new chunks; return ids.

    Parameters
    ----------
    refetch_short_text:
        If a Searcher returned only a snippet (text below
        `CANDIDATE_TEXT_MIN_CHARS`), re-fetch the full URL with the
        fetcher so we chunk the real body, not the snippet. Off-by-default
        for tests; on for SubprocessSearcher in production.
    """
    existing = {c.chunk_id for c in read_chunks(project_dir)}
    admitted: list[str] = []
    duplicates: list[str] = []
    failures: list[tuple[str, str]] = []
    events = 0

    for searcher in searchers:
        try:
            candidates = searcher.search(question, k=k_per_searcher)
        except Exception as e:  # noqa: BLE001 — third-party Searchers, fail loudly
            failures.append((searcher.name, f"search-error: {e!s}"))
            emit(
                project_dir,
                Event(
                    event_type=EventType.PRODUCE_FAIL,
                    step="retrieve",
                    error=str(e),
                    payload={"searcher": searcher.name, "stage": "search"},
                ),
            )
            events += 1
            continue

        for cand in candidates:
            new_chunks, errs = _candidate_to_chunks(
                cand,
                question=question,
                searcher_name=searcher.name,
                refetch=refetch_short_text,
                client=http_client,
            )
            for url, msg in errs:
                failures.append((searcher.name, msg))
                emit(
                    project_dir,
                    Event(
                        event_type=EventType.PRODUCE_FAIL,
                        step="retrieve",
                        error=msg,
                        payload={
                            "searcher": searcher.name,
                            "url": url,
                            "stage": "fetch",
                        },
                    ),
                )
                events += 1

            for ch in new_chunks:
                if ch.chunk_id in existing:
                    duplicates.append(ch.chunk_id)
                    continue
                atomic_append_jsonl(chunks_path(project_dir), ch)
                existing.add(ch.chunk_id)
                admitted.append(ch.chunk_id)
                emit(
                    project_dir,
                    Event(
                        event_type=EventType.STORE_APPEND_OK,
                        step="retrieve",
                        payload={
                            "searcher": searcher.name,
                            "chunk_id": ch.chunk_id,
                            "url": ch.url,
                        },
                    ),
                )
                events += 1

    return RetrieveResult(
        admitted_chunk_ids=tuple(admitted),
        duplicates=tuple(duplicates),
        failures=tuple(failures),
        events_emitted=events,
    )


def _candidate_to_chunks(
    cand: ChunkCandidate,
    *,
    question: str,
    searcher_name: str,
    refetch: bool,
    client: httpx.Client | None,
) -> tuple[list[Chunk], list[tuple[str, str]]]:
    """Turn a candidate into ≥1 stored-ready Chunk objects.

    If the candidate's text is too short to be useful and refetch is on,
    fetch the URL with the real fetcher to get the full body.
    """
    text = cand.text
    title = cand.title
    mime = cand.mime
    source_hash = cand.source_hash
    fetched_at = str(cand.extra.get("fetched_at") or _now_iso())

    if refetch and len(text) < CANDIDATE_TEXT_MIN_CHARS and cand.url:
        try:
            src = fetch_url(cand.url, client=client)
        except FetchError as e:
            return [], [(cand.url, f"fetch-error: {e!s}")]
        text = src.text
        title = src.title or title
        mime = src.mime
        source_hash = src.source_hash

    if not source_hash:
        source_hash = compute_source_hash(text)

    spans = chunk_text(text)
    if not spans:
        return [], [(cand.url, "chunker-empty")]

    out: list[Chunk] = []
    for span in spans:
        out.append(
            Chunk.make(
                url=cand.url,
                title=title,
                fetched_at=fetched_at,
                searcher=searcher_name,
                query=question,
                text=span.text,
                start_offset=span.start_offset,
                end_offset=span.end_offset,
                source_hash=source_hash,
                mime=mime,
            )
        )
    return out, []


__all__ = [
    "CANDIDATE_TEXT_MIN_CHARS",
    "RetrieveResult",
    "retrieve",
]
