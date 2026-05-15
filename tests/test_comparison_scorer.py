"""Comparison-scorer tests against synthetic fixture project."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from sea2.chunks import Chunk
from sea2.comparison.score_sea2 import score_sea2
from sea2.events import Event, EventType, emit
from sea2.models import EpistemicTag, FactType, Finding, ProjectState, Source, VerifierStatus
from sea2.spans import Span
from sea2.store import (
    atomic_append_jsonl,
    chunks_path,
    findings_path,
    write_state,
)
from sea2.store import atomic_append_jsonl as _aaj

if TYPE_CHECKING:
    from pathlib import Path


def _build_fixture_project(tmp_path: Path) -> None:
    """A synthetic project covering several metric scenarios."""
    write_state(
        tmp_path,
        ProjectState(
            name="fixture",
            iteration=3,
            status="completed",
            conductor_iteration=3,
            created_at="2026-05-15T00:00:00Z",
            updated_at="2026-05-15T01:00:00Z",
            completed_at="2026-05-15T01:00:00Z",
            completion_reason="all questions resolved",
        ),
    )

    ch = Chunk.make(
        url="https://example.com/x",
        title="Doc",
        fetched_at="2026-05-15T00:00:00Z",
        searcher="test",
        query="q",
        text="some content",
        start_offset=0,
        end_offset=12,
        source_hash="a" * 64,
        mime="text/html",
    )
    atomic_append_jsonl(chunks_path(tmp_path), ch)

    # Three findings, one verified with URL, one flagged, one failed.
    findings = [
        Finding(
            id="f-001",
            claim="claim 1",
            tag=EpistemicTag.SOURCE,
            fact_type=FactType.QUANTITATIVE,
            source=Source(id="url:https://example.com/x"),
            verbatim_quote="some content",
            confidence=0.9,
            domain="fsca-crypto",
            iteration=1,
            admitted_chunk_id=ch.chunk_id,
        ),
        Finding(
            id="f-002",
            claim="claim 2",
            tag=EpistemicTag.SOURCE,
            fact_type=FactType.CITATION,
            source=Source(id="url:https://example.com/y"),
            confidence=0.7,
            domain="mprda-mining",
            iteration=2,
            admitted_chunk_id=ch.chunk_id,
        ),
        Finding(
            id="f-003",
            claim="claim 3",
            tag=EpistemicTag.SOURCE,
            fact_type=FactType.QUALITATIVE,
            source=Source(id="doi:10.1/abc"),
            confidence=0.5,
            domain="nema",
            iteration=2,
            admitted_chunk_id=ch.chunk_id,
        ),
    ]
    # Manually mark verifier statuses so M5/M8 see the expected counts.
    findings[0] = findings[0].model_copy(update={"verifier_status": VerifierStatus.VERIFIED})
    findings[1] = findings[1].model_copy(update={"verifier_status": VerifierStatus.FLAGGED})
    findings[2] = findings[2].model_copy(update={"verifier_status": VerifierStatus.VERIFIED})
    for f in findings:
        atomic_append_jsonl(findings_path(tmp_path), f)

    # Events: one URL_OK for f-001, one URL_FAIL for f-002, two QUOTE_OK for f-001.
    emit(tmp_path, Event(event_type=EventType.TIER0_URL_OK, step="verify", finding_id="f-001"))
    emit(tmp_path, Event(event_type=EventType.TIER0_URL_FAIL, step="verify", finding_id="f-002"))
    emit(tmp_path, Event(event_type=EventType.TIER0_QUOTE_OK, step="verify", finding_id="f-001"))
    # Tier 2: one disagree to make M3 non-zero.
    emit(tmp_path, Event(event_type=EventType.TIER2_AGREE, step="verify", finding_id="f-001"))
    emit(tmp_path, Event(event_type=EventType.TIER2_DISAGREE, step="verify", finding_id="f-002"))
    # Silent-failure proxy: one PRODUCE_FAIL.
    emit(tmp_path, Event(event_type=EventType.PRODUCE_FAIL, step="extract", error="x"))

    # Spans: 3 extract calls with realistic durations.
    from sea2.spans import spans_path  # noqa: PLC0415

    for i, (pc, oc, dur) in enumerate(
        [(1200, 400, 5000), (1100, 350, 4500), (900, 250, 6000)]
    ):
        _aaj(
            spans_path(tmp_path),
            Span(
                span_id=f"sp{i:013d}",
                step="extract",
                start_ts="2026-05-15T00:00:00Z",
                end_ts="2026-05-15T00:00:05Z",
                duration_ms=dur,
                prompt_chars=pc,
                output_chars=oc,
                prompt_tokens_est=pc // 4,
                output_tokens_est=oc // 4,
                exit_code=0,
            ),
        )


def test_score_sea2_smoke(tmp_path: Path) -> None:
    _build_fixture_project(tmp_path)
    scores = score_sea2(tmp_path)
    assert scores.system == "sea2"
    assert scores.findings_total == 3
    assert scores.findings_verified == 2
    # M1: f-001 OK, f-002 FAIL → 1/2 = 0.5
    assert scores.m1_citation_resolvability == 0.5
    # M2: only f-001 has a quote; 1/1 = 1.0
    assert scores.m2_quote_supported_rate == 1.0
    # M3: 1 disagree out of 2 tier2 events = 0.5
    assert scores.m3_verifier_disagreement_rate == 0.5
    # M8: total tokens / 2 verified
    assert scores.m8_total_tokens > 0
    assert scores.m8_token_cost_per_verified is not None
    # M9: median wall-clock
    assert scores.m9_median_iteration_wallclock_ms is not None
    # M10: 1 PRODUCE_FAIL
    assert scores.m10_silent_failure_count == 1
    # M7: 3 iterations
    assert scores.m7_iterations_to_convergence == 3


def test_score_sea2_json_roundtrip(tmp_path: Path) -> None:
    _build_fixture_project(tmp_path)
    scores = score_sea2(tmp_path)
    raw = scores.model_dump_json()
    parsed = json.loads(raw)
    assert parsed["system"] == "sea2"
    assert parsed["findings_verified"] == 2


def test_score_sea2_empty_project(tmp_path: Path) -> None:
    write_state(
        tmp_path,
        ProjectState(
            name="empty",
            iteration=0,
            conductor_iteration=0,
            created_at="2026-05-15T00:00:00Z",
            updated_at="2026-05-15T00:00:00Z",
        ),
    )
    scores = score_sea2(tmp_path)
    assert scores.findings_total == 0
    assert scores.m1_citation_resolvability is None
    assert scores.m2_quote_supported_rate is None
    assert scores.m10_silent_failure_count == 0
