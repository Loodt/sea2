"""Tier 3 / CGS / Conformal tests."""

from __future__ import annotations

import pytest

from sea2.events import EventType
from sea2.models import EpistemicTag, FactType, Finding, Source
from sea2.verification.cgs import (
    CitationGroundingScore,
    compute_cgs,
)
from sea2.verification.conformal import (
    AbstentionDecision,
    CalibrationRow,
    compute_abstention,
)
from sea2.verification.tier1 import EntailmentBackend, Tier1Status
from sea2.verification.tier3 import (
    TIER3_FLAG_ENV,
    Tier3Status,
    find_contradictions,
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


class _FakeNLI(EntailmentBackend):
    def __init__(self, status: Tier1Status, score: float = 0.9) -> None:
        self._status = status
        self._score = score

    def score(self, claim: str, premise: str) -> tuple[Tier1Status, float]:
        return self._status, self._score


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(TIER3_FLAG_ENV, raising=False)


# ── Tier 3 ──────────────────────────────────────────────────────────────────


def test_tier3_skipped_when_flag_off_and_no_backend() -> None:
    res = find_contradictions(_f(), "premise")
    assert res.status is Tier3Status.SKIPPED
    assert res.event is not None
    assert res.event.event_type is EventType.TIER3_SKIPPED


def test_tier3_refuted_when_nli_contradicts() -> None:
    res = find_contradictions(
        _f(), "premise", backend=_FakeNLI(Tier1Status.CONTRADICTED, 0.92)
    )
    assert res.status is Tier3Status.REFUTED
    assert res.event is not None
    assert res.event.event_type is EventType.TIER3_REFUTED


def test_tier3_ok_when_nli_entails() -> None:
    res = find_contradictions(
        _f(), "premise", backend=_FakeNLI(Tier1Status.ENTAILED, 0.9)
    )
    assert res.status is Tier3Status.OK
    assert res.event is None


# ── CGS ─────────────────────────────────────────────────────────────────────


def _ev(t: str) -> dict[str, object]:
    return {"event_type": t}


def test_cgs_all_axes_positive() -> None:
    events = [_ev("TIER0_URL_OK"), _ev("TIER0_QUOTE_OK"), _ev("TIER1_ENTAILED")]
    res = compute_cgs(_f(), events)
    assert res.resolvability == 1
    assert res.quote_supported == 1
    assert res.entailment == 1
    assert res.aggregate == 1.0


def test_cgs_partial_positive() -> None:
    events = [_ev("TIER0_URL_OK"), _ev("TIER0_QUOTE_FAIL")]
    res = compute_cgs(_f(), events)
    assert res.resolvability == 1
    assert res.quote_supported == -1
    assert res.entailment == 0
    # negatives + missing both round down to 0 in aggregate.
    assert res.aggregate == pytest.approx(1 / 3)


def test_cgs_tier2_agree_satisfies_entailment_axis() -> None:
    events = [_ev("TIER0_URL_OK"), _ev("TIER0_QUOTE_OK"), _ev("TIER2_AGREE")]
    res = compute_cgs(_f(), events)
    assert res.entailment == 1
    assert res.aggregate == 1.0


def test_cgs_no_events_gives_zero_aggregate() -> None:
    res = compute_cgs(_f(), [])
    assert res.aggregate == 0.0
    assert res.resolvability == 0
    assert res.quote_supported == 0
    assert res.entailment == 0


# ── Conformal ───────────────────────────────────────────────────────────────


def _cgs(id_: str, score: float) -> CitationGroundingScore:
    return CitationGroundingScore(
        finding_id=id_,
        resolvability=1,
        quote_supported=1,
        entailment=1,
        aggregate=score,
    )


def test_conformal_uncalibrated_threshold() -> None:
    rows = [_cgs("f-1", 0.1), _cgs("f-2", 0.5), _cgs("f-3", 1.0)]
    out = compute_abstention(rows)
    assert [r.decision for r in out] == [
        AbstentionDecision.ABSTAIN,
        AbstentionDecision.ACCEPT,
        AbstentionDecision.ACCEPT,
    ]
    assert not out[0].calibrated


def test_conformal_calibrated_threshold_adjusts() -> None:
    # 10 correct items with CGS ranging 0.1 to 1.0; alpha=0.1 -> threshold = 1st-percentile
    calibration = [
        CalibrationRow(finding_id=f"c-{i}", cgs=(i + 1) * 0.1, is_correct=True)
        for i in range(10)
    ]
    rows = [_cgs("f-1", 0.05), _cgs("f-2", 0.5), _cgs("f-3", 1.0)]
    out = compute_abstention(rows, calibration=calibration, alpha=0.1)
    assert all(r.calibrated for r in out)
    # threshold ≈ 0.1; f-1 at 0.05 -> abstain, f-2 + f-3 -> accept
    assert out[0].decision is AbstentionDecision.ABSTAIN
    assert out[1].decision is AbstentionDecision.ACCEPT
    assert out[2].decision is AbstentionDecision.ACCEPT


def test_conformal_empty_calibration_falls_back() -> None:
    out = compute_abstention([_cgs("f-1", 0.5)], calibration=[])
    assert out[0].calibrated is False
