"""Integrate step end-to-end tests."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import httpx

from sea2.conductor.integrate import extract_noop, integrate
from sea2.events import EventType
from sea2.models import EpistemicTag, FactType, Finding, Source, VerifierStatus
from sea2.store import findings_path, read_events

if TYPE_CHECKING:
    from pathlib import Path


def _client_ok() -> httpx.Client:
    return httpx.Client(
        transport=httpx.MockTransport(lambda req: httpx.Response(200))
    )


def _finding(
    idx: int,
    *,
    tag: EpistemicTag = EpistemicTag.SOURCE,
    url: str | None = None,
    derived_from: list[str] | None = None,
    claim: str = "claim",
) -> Finding:
    src = Source(id=url or "doi:10.1/abc") if tag is EpistemicTag.SOURCE else None
    return Finding(
        id=f"f-{idx:03d}",
        claim=claim,
        tag=tag,
        fact_type=FactType.QUANTITATIVE,
        source=src,
        confidence=0.9,
        domain="d",
        iteration=0,
        derived_from=derived_from or [],
    )


def test_extract_noop_passes_fixtures() -> None:
    f = _finding(1)
    assert extract_noop([f]) == [f]


def test_integrate_admits_clean_finding_and_persists(tmp_path: Path) -> None:
    f = _finding(1, url="url:https://example.com/x")
    res = integrate(tmp_path, [f], http_client=_client_ok(), require_chunk=False)
    assert len(res.admitted) == 1
    assert res.admitted[0].verifier_status is VerifierStatus.VERIFIED
    # Persisted to findings.jsonl
    raw = findings_path(tmp_path).read_text(encoding="utf-8").strip()
    parsed = json.loads(raw)
    assert parsed["id"] == "f-001"


def test_integrate_emits_store_append_ok_event(tmp_path: Path) -> None:
    integrate(tmp_path, [_finding(1)], http_client=_client_ok(), require_chunk=False)
    events = read_events(tmp_path)
    types = [e["event_type"] for e in events]
    assert "STORE_APPEND_OK" in types


def test_integrate_rejects_schema_invalid_dict(tmp_path: Path) -> None:
    bad = {"id": "f-bad"}  # missing required fields
    res = integrate(tmp_path, [bad], http_client=_client_ok(), require_chunk=False)
    assert len(res.admitted) == 0
    assert len(res.rejected) == 1
    assert "schema" in res.rejected[0][1]
    events = read_events(tmp_path)
    assert any(e["event_type"] == EventType.VALIDATE_FAIL.value for e in events)


def test_integrate_rejects_dag_orphan(tmp_path: Path) -> None:
    bad = _finding(1, tag=EpistemicTag.DERIVED, derived_from=["does-not-exist"])
    res = integrate(tmp_path, [bad], http_client=_client_ok(), require_chunk=False)
    assert len(res.admitted) == 0
    assert "dag-orphan" in res.rejected[0][1]


def test_integrate_bounds_tag_by_weakest_premise(tmp_path: Path) -> None:
    src = _finding(1)  # SOURCE
    est = _finding(2)
    est = est.model_copy(update={"tag": EpistemicTag.ESTIMATED, "source": None})
    # Producer declares SOURCE; weakest premise is ESTIMATED, so admitted tag
    # must be ESTIMATED.
    integrate(tmp_path, [src, est], http_client=_client_ok(), require_chunk=False)
    derived_dict = {
        "id": "f-003",
        "claim": "derived claim",
        "tag": "SOURCE",
        "fact_type": "quantitative",
        "source": {"id": "doi:10.1/abc"},
        "confidence": 0.5,
        "domain": "d",
        "iteration": 0,
        "derived_from": ["f-001", "f-002"],
    }
    res = integrate(tmp_path, [derived_dict], http_client=_client_ok(), require_chunk=False)
    assert len(res.admitted) == 1
    assert res.admitted[0].tag is EpistemicTag.ESTIMATED


def test_integrate_url_fail_marks_finding_failed(tmp_path: Path) -> None:
    # Phase 2 semantics: no-op Tier 0 checks (ledger no-conflict, no-DOI,
    # no-arXiv) do not contribute positive signals to the verdict. With
    # only a URL check active and that check failing, status is FAILED.
    bad_client = httpx.Client(
        transport=httpx.MockTransport(lambda req: httpx.Response(404))
    )
    f = _finding(1, url="url:https://example.com/missing")
    res = integrate(tmp_path, [f], http_client=bad_client, require_chunk=False)
    assert len(res.admitted) == 1
    assert res.admitted[0].verifier_status is VerifierStatus.FAILED
    events = read_events(tmp_path)
    assert any(e["event_type"] == EventType.TIER0_URL_FAIL.value for e in events)
