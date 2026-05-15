"""Question-cap trim tests."""

from __future__ import annotations

from sea2.conductor.caps import apply_question_caps
from sea2.models import ConductorMetric, Question, QuestionType


def _q(
    idx: int,
    *,
    iteration: int = 0,
    status: str = "open",
    priority: str = "medium",
) -> Question:
    return Question(
        id=f"q-{idx:03d}",
        question="?",
        priority=priority,  # type: ignore[arg-type]
        context="c",
        domain="d",
        iteration=iteration,
        status=status,  # type: ignore[arg-type]
    )


def test_no_cap_when_under_thresholds() -> None:
    qs = [_q(i) for i in range(3)]
    out, actions = apply_question_caps(
        qs, iteration=0, landscape_dispatch=False
    )
    assert out == qs
    assert actions == []


def test_per_dispatch_non_landscape_trims_to_three() -> None:
    qs = [_q(i, iteration=1) for i in range(6)]
    out, actions = apply_question_caps(
        qs, iteration=1, landscape_dispatch=False
    )
    assert len(out) == 3
    assert any(a.rule == "per-dispatch-new" for a in actions)


def test_per_dispatch_landscape_allows_five() -> None:
    qs = [_q(i, iteration=1) for i in range(5)]
    out, actions = apply_question_caps(
        qs, iteration=1, landscape_dispatch=True
    )
    assert len(out) == 5
    assert actions == []


def test_iter_boundary_cap_at_iter_15() -> None:
    qs = [_q(i, iteration=15) for i in range(4)]
    out, actions = apply_question_caps(
        qs, iteration=15, landscape_dispatch=False
    )
    # cap = 1 at iter ≥15
    assert len(out) == 1
    rules = [a.rule for a in actions]
    assert "iter-boundary-new" in rules


def test_type_queue_cap_trims_overflow_by_type() -> None:
    # 6 open synthesis questions; cap is 3.
    qs = [_q(i, iteration=2) for i in range(6)]
    qtype: QuestionType = "synthesis"
    metrics = [
        ConductorMetric(
            conductor_iteration=1,
            question_id=q.id,
            expert_status="answered",
            findings_added=0,
            questions_resolved=0,
            inner_iterations_run=1,
            timestamp="2026-05-15T00:00:00Z",
            question_type=qtype,
        )
        for q in qs
    ]
    out, actions = apply_question_caps(
        qs, iteration=2, landscape_dispatch=False, prior_metrics=metrics
    )
    # All 6 are synthesis (cap=3) AND non-landscape per-dispatch cap (3),
    # so the lower of the two is the binding constraint.
    assert len(out) <= 3
    assert any(a.rule == "type-queue-cap" for a in actions)


def test_low_priority_trimmed_before_high() -> None:
    qs = [
        _q(0, iteration=1, priority="high"),
        _q(1, iteration=1, priority="high"),
        _q(2, iteration=1, priority="high"),
        _q(3, iteration=1, priority="low"),
        _q(4, iteration=1, priority="low"),
    ]
    out, _ = apply_question_caps(
        qs, iteration=1, landscape_dispatch=False
    )
    # 5 → 3 trim. The 2 lows should be the ones dropped.
    kept_ids = {q.id for q in out}
    assert "q-003" not in kept_ids and "q-004" not in kept_ids
