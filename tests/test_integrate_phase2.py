"""Integrate-with-chunk tests (Phase 2 wiring)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx

from sea2.chunks import Chunk
from sea2.conductor.integrate import integrate
from sea2.events import EventType
from sea2.models import EpistemicTag, FactType, Finding, Source, VerifierStatus
from sea2.store import atomic_append_jsonl, chunks_path, read_events
from sea2.verification.tier1 import EntailmentBackend, Tier1Status

if TYPE_CHECKING:
    from pathlib import Path


def _ok_client() -> httpx.Client:
    return httpx.Client(
        transport=httpx.MockTransport(lambda req: httpx.Response(200))
    )


def _chunk(text: str, *, url: str = "https://example.com/x") -> Chunk:
    return Chunk.make(
        url=url,
        title=None,
        fetched_at="2026-05-15T00:00:00Z",
        searcher="test",
        query="q",
        text=text,
        start_offset=0,
        end_offset=len(text),
        source_hash="a" * 64,
        mime="text/html",
    )


def _finding_with_chunk(chunk: Chunk, *, quote: str | None = None) -> Finding:
    return Finding(
        id="f-001",
        claim="claim text",
        tag=EpistemicTag.SOURCE,
        fact_type=FactType.QUANTITATIVE,
        source=Source(id="url:" + chunk.url),
        verbatim_quote=quote,
        confidence=0.9,
        domain="d",
        iteration=0,
        admitted_chunk_id=chunk.chunk_id,
    )


def test_finding_without_admitted_chunk_id_rejected(tmp_path: Path) -> None:
    f = Finding(
        id="f-001",
        claim="x",
        tag=EpistemicTag.SOURCE,
        fact_type=FactType.QUANTITATIVE,
        source=Source(id="url:https://example.com"),
        confidence=0.9,
        domain="d",
        iteration=0,
    )
    res = integrate(tmp_path, [f], http_client=_ok_client())
    assert len(res.admitted) == 0
    assert "admitted_chunk_id missing" in res.rejected[0][1]


def test_finding_with_unknown_chunk_id_rejected(tmp_path: Path) -> None:
    f = Finding(
        id="f-001",
        claim="x",
        tag=EpistemicTag.SOURCE,
        fact_type=FactType.QUANTITATIVE,
        source=Source(id="url:https://example.com"),
        confidence=0.9,
        domain="d",
        iteration=0,
        admitted_chunk_id="0123456789abcdef",
    )
    res = integrate(tmp_path, [f], http_client=_ok_client())
    assert len(res.admitted) == 0
    assert "not in chunk store" in res.rejected[0][1]


def test_quote_supported_admits_verified(tmp_path: Path) -> None:
    ch = _chunk("Some text. The actual quote is here. More text.")
    atomic_append_jsonl(chunks_path(tmp_path), ch)
    f = _finding_with_chunk(ch, quote="The actual quote is here")
    res = integrate(tmp_path, [f], http_client=_ok_client())
    assert len(res.admitted) == 1
    assert res.admitted[0].verifier_status is VerifierStatus.VERIFIED
    events = read_events(tmp_path)
    assert any(e["event_type"] == EventType.TIER0_QUOTE_OK.value for e in events)


def test_quote_not_supported_flags_finding(tmp_path: Path) -> None:
    ch = _chunk("Some content. Nothing matches here.")
    atomic_append_jsonl(chunks_path(tmp_path), ch)
    f = _finding_with_chunk(ch, quote="quote not in chunk")
    res = integrate(tmp_path, [f], http_client=_ok_client())
    assert len(res.admitted) == 1
    # url=OK + quote=FAIL → mixed → FLAGGED
    assert res.admitted[0].verifier_status is VerifierStatus.FLAGGED
    events = read_events(tmp_path)
    assert any(e["event_type"] == EventType.TIER0_QUOTE_FAIL.value for e in events)


class _FakeEntailedBackend(EntailmentBackend):
    def score(self, claim: str, premise: str) -> tuple[Tier1Status, float]:
        return Tier1Status.ENTAILED, 0.95


class _FakeContradictedBackend(EntailmentBackend):
    def score(self, claim: str, premise: str) -> tuple[Tier1Status, float]:
        return Tier1Status.CONTRADICTED, 0.9


def test_tier1_entailed_contributes_positive(tmp_path: Path) -> None:
    ch = _chunk("Premise content with the quote in it.")
    atomic_append_jsonl(chunks_path(tmp_path), ch)
    f = _finding_with_chunk(ch, quote="the quote in it")
    res = integrate(
        tmp_path,
        [f],
        http_client=_ok_client(),
        tier1_backend=_FakeEntailedBackend(),
    )
    assert res.admitted[0].verifier_status is VerifierStatus.VERIFIED
    events = read_events(tmp_path)
    assert any(e["event_type"] == EventType.TIER1_ENTAILED.value for e in events)


def test_tier1_contradicted_flags_finding(tmp_path: Path) -> None:
    ch = _chunk("Premise content with the quote in it.")
    atomic_append_jsonl(chunks_path(tmp_path), ch)
    f = _finding_with_chunk(ch, quote="the quote in it")
    res = integrate(
        tmp_path,
        [f],
        http_client=_ok_client(),
        tier1_backend=_FakeContradictedBackend(),
    )
    # url=OK + quote=OK + tier1=FAIL → mixed → FLAGGED
    assert res.admitted[0].verifier_status is VerifierStatus.FLAGGED
    events = read_events(tmp_path)
    assert any(e["event_type"] == EventType.TIER1_CONTRADICTED.value for e in events)


def test_legacy_mode_skips_chunk_requirement(tmp_path: Path) -> None:
    # Legacy / no-retrieve mode: require_chunk=False allows findings without
    # admitted_chunk_id. Used by Phase 1 carry-over tests.
    f = Finding(
        id="f-001",
        claim="x",
        tag=EpistemicTag.SOURCE,
        fact_type=FactType.QUANTITATIVE,
        source=Source(id="url:https://example.com"),
        confidence=0.9,
        domain="d",
        iteration=0,
    )
    res = integrate(tmp_path, [f], http_client=_ok_client(), require_chunk=False)
    assert len(res.admitted) == 1
