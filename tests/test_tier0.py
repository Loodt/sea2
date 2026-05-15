"""Tier 0 cheap-wins tests."""

from __future__ import annotations

import httpx

from sea2.events import EventType
from sea2.models import EpistemicTag, FactType, Finding, Source
from sea2.verification.tier0 import (
    check_ledger_consistency,
    check_url_resolves,
)


def _finding(idx: int, *, claim: str = "claim", url: str | None = None) -> Finding:
    return Finding(
        id=f"f-{idx:03d}",
        claim=claim,
        tag=EpistemicTag.SOURCE,
        fact_type=FactType.QUANTITATIVE,
        source=Source(id=url if url else "doi:10.1/abc"),
        confidence=0.9,
        domain="d",
        iteration=0,
    )


def _client(handler) -> httpx.Client:  # type: ignore[no-untyped-def]
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_url_resolves_2xx() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200)

    res = check_url_resolves(
        _finding(1, url="url:https://example.com/x"),
        client=_client(handler),
    )
    assert res.verified is True
    assert res.event is not None
    assert res.event.event_type is EventType.TIER0_URL_OK


def test_url_resolves_404_fails() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404)

    res = check_url_resolves(
        _finding(1, url="url:https://example.com/missing"),
        client=_client(handler),
    )
    assert res.verified is False
    assert res.event is not None
    assert res.event.event_type is EventType.TIER0_URL_FAIL


def test_url_network_error_fails_loudly() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("nope", request=request)

    res = check_url_resolves(
        _finding(1, url="url:https://example.com/x"),
        client=_client(handler),
    )
    assert res.verified is False
    assert res.event is not None
    assert res.event.event_type is EventType.TIER0_URL_FAIL
    assert "http-error" in res.detail


def test_non_url_source_skipped() -> None:
    res = check_url_resolves(_finding(1))
    assert res.verified is True
    assert res.detail == "no-url"
    assert res.event is None


def test_ledger_contradiction_detected() -> None:
    existing = [
        _finding(
            1,
            claim="The Boeing 787 has a max takeoff weight of 254 tonnes.",
        )
    ]
    incoming = _finding(
        2,
        claim="The Boeing 787 does not have a max takeoff weight of 254 tonnes.",
    )
    res = check_ledger_consistency(incoming, existing)
    assert res.verified is False
    assert res.event is not None
    assert res.event.event_type is EventType.TIER0_LEDGER_CONFLICT
    assert res.extra["conflicts_with"] == "f-001"


def test_ledger_no_overlap_passes() -> None:
    existing = [_finding(1, claim="Falcon 9 first stage uses Merlin engines.")]
    incoming = _finding(2, claim="Soyuz never returns to launch site.")
    res = check_ledger_consistency(incoming, existing)
    assert res.verified is True


def test_ledger_skips_other_domains() -> None:
    other = _finding(1, claim="Foo bar baz qux not zonk widget.")
    other_dict = other.model_dump()
    other_dict["domain"] = "aero"
    different_domain = Finding.model_validate(other_dict)

    incoming = _finding(2, claim="Foo bar baz qux is true zonk widget.")
    res = check_ledger_consistency(incoming, [different_domain])
    assert res.verified is True


def test_ledger_skips_self() -> None:
    f = _finding(1, claim="Foo bar baz qux not zonk widget.")
    res = check_ledger_consistency(f, [f])
    assert res.verified is True
