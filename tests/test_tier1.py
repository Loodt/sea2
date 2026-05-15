"""Tier 1 NLI tests using a fake EntailmentBackend."""

from __future__ import annotations

import pytest

from sea2.events import EventType
from sea2.models import EpistemicTag, FactType, Finding, Source
from sea2.verification.tier1 import (
    TIER1_FLAG_ENV,
    EntailmentBackend,
    Tier1Status,
    check_entailment,
    is_enabled,
)


def _finding() -> Finding:
    return Finding(
        id="f-001",
        claim="The PW1100G has a bypass ratio of 12.5.",
        tag=EpistemicTag.SOURCE,
        fact_type=FactType.QUANTITATIVE,
        source=Source(id="doi:10.1/abc"),
        confidence=0.8,
        domain="aero",
        iteration=0,
    )


class _FakeBackend(EntailmentBackend):
    def __init__(self, status: Tier1Status, score: float) -> None:
        self._status = status
        self._score = score

    def score(self, claim: str, premise: str) -> tuple[Tier1Status, float]:
        return self._status, self._score


class _RaisingBackend(EntailmentBackend):
    def score(self, claim: str, premise: str) -> tuple[Tier1Status, float]:
        raise RuntimeError("backend broke")


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(TIER1_FLAG_ENV, raising=False)


def test_skipped_when_flag_off_and_no_backend() -> None:
    res = check_entailment(_finding(), "some premise text")
    assert res.status is Tier1Status.SKIPPED
    assert res.event is not None
    assert res.event.event_type is EventType.TIER1_SKIPPED


def test_explicit_backend_runs_even_when_flag_off() -> None:
    res = check_entailment(
        _finding(),
        "premise",
        backend=_FakeBackend(Tier1Status.ENTAILED, 0.92),
    )
    assert res.status is Tier1Status.ENTAILED
    assert res.score == 0.92
    assert res.event is not None
    assert res.event.event_type is EventType.TIER1_ENTAILED


def test_flag_on_uses_provided_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(TIER1_FLAG_ENV, "1")
    assert is_enabled() is True
    res = check_entailment(
        _finding(),
        "premise",
        backend=_FakeBackend(Tier1Status.CONTRADICTED, 0.85),
    )
    assert res.status is Tier1Status.CONTRADICTED
    assert res.event is not None
    assert res.event.event_type is EventType.TIER1_CONTRADICTED


def test_backend_exception_returns_error_not_crash() -> None:
    res = check_entailment(_finding(), "premise", backend=_RaisingBackend())
    assert res.status is Tier1Status.ERROR
    assert res.event is not None
    assert res.event.event_type is EventType.TIER1_SKIPPED
    assert "backend-error" in res.detail


def test_neutral_status_event() -> None:
    res = check_entailment(
        _finding(),
        "premise",
        backend=_FakeBackend(Tier1Status.NEUTRAL, 0.5),
    )
    assert res.status is Tier1Status.NEUTRAL
    assert res.event is not None
    assert res.event.event_type is EventType.TIER1_NEUTRAL


def test_is_enabled_truthy_values(monkeypatch: pytest.MonkeyPatch) -> None:
    for v in ("1", "true", "yes"):
        monkeypatch.setenv(TIER1_FLAG_ENV, v)
        assert is_enabled() is True
    for v in ("0", "false", "no", ""):
        monkeypatch.setenv(TIER1_FLAG_ENV, v)
        assert is_enabled() is False
