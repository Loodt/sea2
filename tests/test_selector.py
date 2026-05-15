"""Selector tests: completion gate, halt reader, veto parser, guards."""

from __future__ import annotations

from sea2.conductor.selector import (
    QuestionSelection,
    SelectorOutcome,
    apply_selection_guards,
    parse_reflection_veto,
    select,
)
from sea2.events import EventType
from sea2.models import (
    ConductorMetric,
    ProjectState,
    Question,
)


def _project(**overrides: object) -> ProjectState:
    base = {
        "name": "test",
        "iteration": 0,
        "created_at": "2026-05-15T00:00:00Z",
        "updated_at": "2026-05-15T00:00:00Z",
    }
    base.update(overrides)
    return ProjectState(**base)  # type: ignore[arg-type]


def _question(
    id_: str,
    *,
    status: str = "open",
    priority: str = "medium",
) -> Question:
    return Question(
        id=id_,
        question="?",
        priority=priority,  # type: ignore[arg-type]
        context="c",
        domain="d",
        iteration=0,
        status=status,  # type: ignore[arg-type]
    )


# ── Completion gate ─────────────────────────────────────────────────────────


def test_completion_gate_fires_on_empty_queue() -> None:
    res = select(_project(), open_questions=[])
    assert res.outcome is SelectorOutcome.COMPLETED
    assert res.event is not None
    assert res.event.event_type is EventType.HALT_REQUESTED
    assert res.event.payload["source"] == "completion-gate"


def test_completion_gate_skipped_when_dispatch_active() -> None:
    res = select(
        _project(active_question_id="q-1"),
        open_questions=[],
    )
    assert res.outcome is SelectorOutcome.SELECTED


def test_completion_gate_skipped_when_questions_remain() -> None:
    res = select(_project(), open_questions=[_question("q-1")])
    assert res.outcome is SelectorOutcome.SELECTED


# ── Halt-reason reader ──────────────────────────────────────────────────────


def test_halt_reason_short_circuits_everything() -> None:
    res = select(
        _project(halt_reason="operator stop", active_question_id="q-1"),
        open_questions=[_question("q-1")],
    )
    assert res.outcome is SelectorOutcome.HALTED
    assert res.event is not None
    assert res.event.payload["source"] == "operator"
    assert res.event.payload["reason"] == "operator stop"


# ── Reflection-veto parser ──────────────────────────────────────────────────


def test_parse_reflection_veto_matches_phrases() -> None:
    assert parse_reflection_veto("Critic says: do not dispatch this iteration") == "do not dispatch"
    assert parse_reflection_veto("This work should be completed before continuing") == "should be completed"
    assert parse_reflection_veto("HALT PENDING further review") is not None
    assert parse_reflection_veto("looks fine") is None
    assert parse_reflection_veto(None) is None
    assert parse_reflection_veto("") is None


def test_veto_triggers_halt_outcome() -> None:
    res = select(
        _project(),
        open_questions=[_question("q-1")],
        critic_output="we should be completed",
    )
    assert res.outcome is SelectorOutcome.VETOED
    assert res.event is not None
    assert res.event.payload["source"] == "critic-veto"


def test_halt_reason_wins_over_veto() -> None:
    res = select(
        _project(halt_reason="kill"),
        open_questions=[_question("q-1")],
        critic_output="do not dispatch",
    )
    assert res.outcome is SelectorOutcome.HALTED


# ── Selection guards ────────────────────────────────────────────────────────


def _selection(qid: str, qtype: str = "mechanism") -> QuestionSelection:
    return QuestionSelection(
        question_id=qid,
        question="?",
        question_type=qtype,  # type: ignore[arg-type]
    )


def test_guard_non_open_swaps_to_open_question() -> None:
    sel = _selection("q-dead")
    qs = [_question("q-dead", status="resolved"), _question("q-alive")]
    out = apply_selection_guards(sel, qs, recent_types=[])
    assert out.selection.question_id == "q-alive"
    assert any(i.rule == "non-open-redispatch" for i in out.interventions)


def test_guard_non_open_no_alternative_leaves_alone() -> None:
    sel = _selection("q-dead")
    qs = [_question("q-dead", status="resolved")]
    out = apply_selection_guards(sel, qs, recent_types=[])
    assert out.selection.question_id == "q-dead"
    assert out.interventions[0].rule == "non-open-redispatch"


def test_guard_type_mismatch_uses_prior_type() -> None:
    sel = _selection("q-1", qtype="data-hunt")
    metrics = [
        ConductorMetric(
            conductor_iteration=1,
            question_id="q-1",
            expert_status="answered",
            findings_added=0,
            questions_resolved=0,
            inner_iterations_run=1,
            timestamp="2026-05-15T00:00:00Z",
            question_type="mechanism",
        ),
    ]
    out = apply_selection_guards(
        sel, [_question("q-1")], recent_types=[], prior_metrics=metrics
    )
    assert out.selection.question_type == "mechanism"
    assert any(i.rule == "re-dispatch-type-mismatch" for i in out.interventions)


def test_guard_same_type_cap_swaps_when_alternative_exists() -> None:
    sel = _selection("q-1", qtype="mechanism")
    out = apply_selection_guards(
        sel,
        [_question("q-1"), _question("q-2")],
        recent_types=["mechanism", "mechanism"],
    )
    assert any(i.rule == "same-type-cap" for i in out.interventions)
    assert out.selection.question_id == "q-2"


def test_guard_same_type_cap_letthrough_when_no_alternative() -> None:
    sel = _selection("q-1", qtype="mechanism")
    out = apply_selection_guards(
        sel,
        [_question("q-1")],
        recent_types=["mechanism", "mechanism"],
    )
    assert any(i.rule == "same-type-cap" for i in out.interventions)
    assert out.selection.question_id == "q-1"
