"""Tier 2 cross-family verifier tests."""

from __future__ import annotations

import pytest

from sea2.events import EventType
from sea2.models import EpistemicTag, FactType, Finding, Source
from sea2.verification.tier2 import (
    TIER2_FLAG_ENV,
    TIER2_RNG_SEED_ENV,
    TIER2_SAMPLE_FRAC_ENV,
    Tier2Backend,
    Tier2Verdict,
    check_tier2,
    is_enabled,
    rng_seed,
    sample_fraction,
    should_audit,
)


def _f(id_: str = "f-001") -> Finding:
    return Finding(
        id=id_,
        claim="test claim",
        tag=EpistemicTag.SOURCE,
        fact_type=FactType.QUALITATIVE,
        source=Source(id="doi:10.1/abc"),
        confidence=0.8,
        domain="d",
        iteration=0,
    )


class _FakeBackend(Tier2Backend):
    def __init__(self, verdict: Tier2Verdict, score: float) -> None:
        self._verdict = verdict
        self._score = score

    def verify(self, claim: str, premise: str) -> tuple[Tier2Verdict, float]:
        return self._verdict, self._score


class _RaisingBackend(Tier2Backend):
    def verify(self, claim: str, premise: str) -> tuple[Tier2Verdict, float]:
        raise RuntimeError("backend died")


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for v in (TIER2_FLAG_ENV, TIER2_SAMPLE_FRAC_ENV, TIER2_RNG_SEED_ENV):
        monkeypatch.delenv(v, raising=False)


# ── Flag + sample fraction ──────────────────────────────────────────────────


def test_flag_default_off() -> None:
    assert is_enabled() is False


def test_flag_truthy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(TIER2_FLAG_ENV, "1")
    assert is_enabled() is True


def test_sample_fraction_default() -> None:
    assert sample_fraction() == 0.30


def test_sample_fraction_clamped(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(TIER2_SAMPLE_FRAC_ENV, "1.5")
    assert sample_fraction() == 1.0
    monkeypatch.setenv(TIER2_SAMPLE_FRAC_ENV, "-0.5")
    assert sample_fraction() == 0.0


def test_rng_seed_default() -> None:
    assert rng_seed() == 17


# ── Sampling stability ──────────────────────────────────────────────────────


def test_should_audit_zero_frac() -> None:
    f = _f("f-001")
    assert should_audit(f, frac=0.0, seed=17) is False


def test_should_audit_full_frac() -> None:
    f = _f("f-001")
    assert should_audit(f, frac=1.0, seed=17) is True


def test_should_audit_stable_per_id() -> None:
    f = _f("f-001")
    a = should_audit(f, frac=0.5, seed=17)
    b = should_audit(f, frac=0.5, seed=17)
    assert a == b


def test_should_audit_varies_across_ids() -> None:
    # Across 100 IDs at 30% frac, the included count should be roughly 30 ± 15.
    included = [
        should_audit(_f(f"f-{i:04d}"), frac=0.3, seed=17) for i in range(100)
    ]
    n = sum(included)
    assert 15 <= n <= 45, f"sample size {n} unreasonable for 30% over 100 ids"


# ── check_tier2 ─────────────────────────────────────────────────────────────


def test_skipped_when_flag_off_and_no_backend() -> None:
    res = check_tier2(_f(), "some premise")
    assert res.verdict is Tier2Verdict.SKIPPED
    assert res.event is not None
    assert res.event.event_type is EventType.TIER2_SKIPPED


def test_explicit_backend_runs_when_flag_off() -> None:
    res = check_tier2(
        _f(), "premise", backend=_FakeBackend(Tier2Verdict.AGREE, 0.92)
    )
    assert res.verdict is Tier2Verdict.AGREE
    assert res.event is not None
    assert res.event.event_type is EventType.TIER2_AGREE


def test_disagree_event() -> None:
    res = check_tier2(
        _f(), "premise", backend=_FakeBackend(Tier2Verdict.DISAGREE, 0.8)
    )
    assert res.event is not None
    assert res.event.event_type is EventType.TIER2_DISAGREE


def test_uncertain_yields_skipped_event() -> None:
    res = check_tier2(
        _f(), "premise", backend=_FakeBackend(Tier2Verdict.UNCERTAIN, 0.5)
    )
    assert res.verdict is Tier2Verdict.UNCERTAIN
    assert res.event is not None
    assert res.event.event_type is EventType.TIER2_SKIPPED


def test_backend_exception_returns_error_not_crash() -> None:
    res = check_tier2(_f(), "premise", backend=_RaisingBackend())
    assert res.verdict is Tier2Verdict.ERROR
    assert "backend-error" in res.detail
