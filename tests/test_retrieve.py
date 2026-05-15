"""Retrieve-stage tests with fake Searchers (no network)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx

from sea2.conductor.retrieve import retrieve
from sea2.retrieve.searcher import ChunkCandidate, Searcher
from sea2.store import read_chunks, read_events

if TYPE_CHECKING:
    from pathlib import Path


class _FakeSearcher(Searcher):
    def __init__(self, name: str, candidates: list[ChunkCandidate]) -> None:
        self.name = name
        self._candidates = candidates

    def search(self, query: str, *, k: int = 5) -> list[ChunkCandidate]:
        return self._candidates[:k]


class _RaisingSearcher(Searcher):
    name = "boom"

    def search(self, query: str, *, k: int = 5) -> list[ChunkCandidate]:
        raise RuntimeError("searcher exploded")


def _candidate(url: str, text: str, *, mime: str = "text/html") -> ChunkCandidate:
    return ChunkCandidate(
        url=url,
        text=text,
        start_offset=0,
        end_offset=len(text),
        mime=mime,  # type: ignore[arg-type]
        searcher="fake",
        query="q",
        title="t",
        source_hash="a" * 64,
    )


def _ok_client() -> httpx.Client:
    body = (b"<html><body>" + (b"Paragraph content. " * 100) + b"</body></html>")
    return httpx.Client(
        transport=httpx.MockTransport(
            lambda req: httpx.Response(
                200, headers={"content-type": "text/html"}, content=body
            )
        )
    )


def test_retrieve_admits_long_candidate_directly(tmp_path: Path) -> None:
    long_text = "Long paragraph content. " * 50  # > 200 chars
    s = _FakeSearcher("fake", [_candidate("https://example.com/a", long_text)])
    res = retrieve(tmp_path, "q", searchers=[s], refetch_short_text=False)
    assert len(res.admitted_chunk_ids) >= 1
    assert res.failures == ()


def test_retrieve_persists_chunks(tmp_path: Path) -> None:
    long_text = "Stored paragraph text. " * 50
    s = _FakeSearcher("fake", [_candidate("https://example.com/a", long_text)])
    retrieve(tmp_path, "q", searchers=[s], refetch_short_text=False)
    stored = read_chunks(tmp_path)
    assert len(stored) >= 1
    assert stored[0].query == "q"
    assert stored[0].searcher == "fake"


def test_retrieve_dedupes_repeated_chunks(tmp_path: Path) -> None:
    long_text = "Same content here. " * 50
    s = _FakeSearcher("fake", [_candidate("https://example.com/a", long_text)])
    retrieve(tmp_path, "q", searchers=[s], refetch_short_text=False)
    res2 = retrieve(tmp_path, "q", searchers=[s], refetch_short_text=False)
    # All chunks are duplicates on the second call.
    assert res2.admitted_chunk_ids == ()
    assert len(res2.duplicates) >= 1


def test_retrieve_short_text_triggers_refetch(tmp_path: Path) -> None:
    cand = _candidate("https://example.com/a", "tiny snippet")  # < 200 chars
    s = _FakeSearcher("fake", [cand])
    res = retrieve(
        tmp_path,
        "q",
        searchers=[s],
        refetch_short_text=True,
        http_client=_ok_client(),
    )
    # Refetched body contains the long paragraph content.
    assert len(res.admitted_chunk_ids) >= 1
    chunks = read_chunks(tmp_path)
    assert "Paragraph content" in chunks[0].text


def test_retrieve_searcher_exception_emits_produce_fail(tmp_path: Path) -> None:
    res = retrieve(tmp_path, "q", searchers=[_RaisingSearcher()])
    assert res.admitted_chunk_ids == ()
    assert len(res.failures) == 1
    events = read_events(tmp_path)
    assert any(e["event_type"] == "PRODUCE_FAIL" for e in events)


def test_retrieve_failed_fetch_emits_event(tmp_path: Path) -> None:
    bad_client = httpx.Client(
        transport=httpx.MockTransport(lambda req: httpx.Response(404))
    )
    cand = _candidate("https://example.com/missing", "snippet")  # short → refetch
    s = _FakeSearcher("fake", [cand])
    res = retrieve(
        tmp_path,
        "q",
        searchers=[s],
        refetch_short_text=True,
        http_client=bad_client,
    )
    assert res.admitted_chunk_ids == ()
    assert any("fetch-error" in msg for _, msg in res.failures)
    events = read_events(tmp_path)
    assert any(
        e["event_type"] == "PRODUCE_FAIL"
        and e.get("payload", {}).get("stage") == "fetch"
        for e in events
    )


def test_retrieve_emits_store_append_ok_per_chunk(tmp_path: Path) -> None:
    long_text = "Content body. " * 50
    s = _FakeSearcher("fake", [_candidate("https://example.com/a", long_text)])
    retrieve(tmp_path, "q", searchers=[s], refetch_short_text=False)
    events = read_events(tmp_path)
    store_events = [e for e in events if e["event_type"] == "STORE_APPEND_OK"]
    assert len(store_events) >= 1
    for e in store_events:
        assert e.get("payload", {}).get("chunk_id")
