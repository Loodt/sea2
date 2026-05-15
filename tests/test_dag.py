"""Provenance DAG tests."""

from __future__ import annotations

import pytest

from sea2.models import EpistemicTag, FactType, Finding, Source
from sea2.verification.dag import propagate_confidence, validate_dag


def _finding(
    idx: int,
    *,
    tag: EpistemicTag = EpistemicTag.SOURCE,
    derived_from: list[str] | None = None,
) -> Finding:
    return Finding(
        id=f"f-{idx:03d}",
        claim=f"claim {idx}",
        tag=tag,
        fact_type=FactType.QUANTITATIVE,
        source=Source(id="doi:10.1/abc") if tag is EpistemicTag.SOURCE else None,
        confidence=0.9,
        domain="d",
        iteration=0,
        derived_from=derived_from or [],
    )


def test_validate_passes_on_empty_derived_from() -> None:
    f = _finding(1)
    assert validate_dag(f, existing={}).valid is True


def test_orphan_premise_rejected() -> None:
    f = _finding(2, tag=EpistemicTag.DERIVED, derived_from=["does-not-exist"])
    res = validate_dag(f, existing={})
    assert res.valid is False
    assert res.orphans == ("does-not-exist",)


def test_valid_two_premise_chain() -> None:
    a = _finding(1)
    b = _finding(2)
    c = _finding(3, tag=EpistemicTag.DERIVED, derived_from=["f-001", "f-002"])
    res = validate_dag(c, existing={"f-001": a, "f-002": b})
    assert res.valid is True


def test_cycle_detected_transitively() -> None:
    # a → b → c, then introducing d → a but d's id equals the loop terminus.
    # We simulate by making a finding `f-new` whose premise is `f-002`, and
    # the existing `f-002` has `f-new` already in its derived_from (the new
    # finding would close the loop).
    a = _finding(1, tag=EpistemicTag.DERIVED, derived_from=["f-new"])
    b = _finding(2, tag=EpistemicTag.DERIVED, derived_from=["f-001"])
    new = Finding(
        id="f-new",
        claim="loop closer",
        tag=EpistemicTag.DERIVED,
        fact_type=FactType.LOGICAL,
        confidence=0.5,
        domain="d",
        iteration=0,
        derived_from=["f-002"],
    )
    res = validate_dag(new, existing={"f-001": a, "f-002": b})
    assert res.valid is False
    assert res.cycle_path is not None
    assert res.cycle_path[0] == "f-new"
    assert "f-new" in res.cycle_path[1:]


def test_propagate_confidence_no_premises() -> None:
    f = _finding(1, tag=EpistemicTag.SOURCE)
    assert propagate_confidence(f, existing={}) is EpistemicTag.SOURCE


def test_propagate_bounded_by_weakest_premise() -> None:
    src = _finding(1, tag=EpistemicTag.SOURCE)
    est = _finding(2, tag=EpistemicTag.ESTIMATED)
    derived = _finding(
        3,
        tag=EpistemicTag.SOURCE,  # producer claims SOURCE, illegal
        derived_from=["f-001", "f-002"],
    )
    effective = propagate_confidence(
        derived, existing={"f-001": src, "f-002": est}
    )
    assert effective is EpistemicTag.ESTIMATED


def test_propagate_missing_premise_raises() -> None:
    f = _finding(1, tag=EpistemicTag.DERIVED, derived_from=["nope"])
    with pytest.raises(ValueError, match="not in store"):
        propagate_confidence(f, existing={})
