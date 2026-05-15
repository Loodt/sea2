"""Selector: completion gate, halt reader, reflection-veto parser, guards.

Each construct here corresponds to a SEA failure pattern the article does not
name but which we are committing not to reproduce:

  - Completion gate → `closeout-drift.md` (no completion gate caused score
    decay across closeout iterations).
  - Halt-reason reader → `operator-kill-ignored-cascade.md` (operator kill
    switches ignored because there was no code path reading them).
  - Reflection-veto parser → critic veto ignored, dispatch proceeded anyway.

All three live in code (commitment 5: code-enforced or nonexistent).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING

from sea2.events import Event, EventType

if TYPE_CHECKING:
    from sea2.models import (
        ConductorMetric,
        ProjectState,
        Question,
        QuestionPriority,
        QuestionType,
    )


# ── Completion / halt ────────────────────────────────────────────────────────


class SelectorOutcome(StrEnum):
    SELECTED = "selected"
    COMPLETED = "completed"
    HALTED = "halted"
    VETOED = "vetoed"


@dataclass(frozen=True)
class SelectorResult:
    outcome: SelectorOutcome
    selection: QuestionSelection | None = None
    event: Event | None = None
    reason: str = ""


_VETO_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bdo not dispatch\b", re.IGNORECASE),
    re.compile(r"\bshould be completed\b", re.IGNORECASE),
    re.compile(r"\bhalt pending\b", re.IGNORECASE),
    re.compile(r"\bhalt the loop\b", re.IGNORECASE),
    re.compile(r"\bstop dispatching\b", re.IGNORECASE),
)


def parse_reflection_veto(critic_output: str | None) -> str | None:
    """Return the matched veto phrase if the critic asked for a halt.

    None if no veto signal present (or input was None/empty). The matched
    phrase is returned so the emitted HALT_REQUESTED event can record it.
    """
    if not critic_output:
        return None
    for pat in _VETO_PATTERNS:
        m = pat.search(critic_output)
        if m:
            return m.group(0)
    return None


# ── Selection result + guard interventions ──────────────────────────────────


@dataclass(frozen=True)
class QuestionSelection:
    question_id: str
    question: str
    question_type: QuestionType
    reasoning: str = ""
    relevant_finding_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class GuardIntervention:
    rule: str  # "non-open-redispatch" | "re-dispatch-type-mismatch" | "same-type-cap"
    reason: str
    original_question_id: str
    original_type: QuestionType
    corrected_question_id: str
    corrected_type: QuestionType


@dataclass(frozen=True)
class GuardedSelection:
    selection: QuestionSelection
    interventions: tuple[GuardIntervention, ...] = field(default_factory=tuple)


_PRIORITY_RANK: dict[QuestionPriority, int] = {"high": 0, "medium": 1, "low": 2}


# ── Selection guards (port of sea/src/selection-guards.ts) ──────────────────


def apply_selection_guards(
    selection: QuestionSelection,
    questions: list[Question],
    recent_types: list[QuestionType],
    prior_metrics: list[ConductorMetric] | None = None,
    *,
    max_consecutive_same_type: int = 2,
) -> GuardedSelection:
    """Three guards, in order. Deterministic correction, not rejection."""
    metrics = prior_metrics or []
    interventions: list[GuardIntervention] = []
    current = selection
    by_id = {q.id: q for q in questions}
    open_questions = [q for q in questions if q.status == "open"]

    # Guard 1: non-open re-dispatch
    record = by_id.get(current.question_id)
    if record is None or record.status != "open":
        swap = _pick_fallback_open(open_questions)
        if swap is None:
            interventions.append(
                GuardIntervention(
                    rule="non-open-redispatch",
                    reason=(
                        f"Selected {current.question_id} is not open and no "
                        f"alternative open question exists."
                    ),
                    original_question_id=current.question_id,
                    original_type=current.question_type,
                    corrected_question_id=current.question_id,
                    corrected_type=current.question_type,
                )
            )
            return GuardedSelection(current, tuple(interventions))
        interventions.append(
            GuardIntervention(
                rule="non-open-redispatch",
                reason=(
                    f"Selected {current.question_id} "
                    f"{'does not exist' if record is None else f'has status={record.status!r}'}; "
                    f"swapped to open {swap.id}."
                ),
                original_question_id=current.question_id,
                original_type=current.question_type,
                corrected_question_id=swap.id,
                corrected_type=current.question_type,
            )
        )
        current = QuestionSelection(
            question_id=swap.id,
            question=swap.question,
            question_type=current.question_type,
            reasoning=current.reasoning,
            relevant_finding_ids=current.relevant_finding_ids,
        )

    # Guard 2: re-dispatch type-mismatch
    prior_dispatch = next(
        (m for m in metrics if m.question_id == current.question_id), None
    )
    if (
        prior_dispatch is not None
        and prior_dispatch.question_type is not None
        and prior_dispatch.question_type != current.question_type
    ):
        interventions.append(
            GuardIntervention(
                rule="re-dispatch-type-mismatch",
                reason=(
                    f"Question {current.question_id} was previously dispatched as "
                    f"{prior_dispatch.question_type!r}; selection says "
                    f"{current.question_type!r}. Using prior type to preserve "
                    f"metric lineage."
                ),
                original_question_id=current.question_id,
                original_type=current.question_type,
                corrected_question_id=current.question_id,
                corrected_type=prior_dispatch.question_type,
            )
        )
        current = QuestionSelection(
            question_id=current.question_id,
            question=current.question,
            question_type=prior_dispatch.question_type,
            reasoning=current.reasoning,
            relevant_finding_ids=current.relevant_finding_ids,
        )

    # Guard 3: same-type cap
    if _would_exceed_same_type_cap(
        current.question_type, recent_types, max_consecutive_same_type
    ):
        swap = next(
            (
                q
                for q in open_questions
                if q.id != current.question_id
                and not _would_swap_exceed_cap(
                    q,
                    metrics,
                    recent_types,
                    max_consecutive_same_type,
                )
            ),
            None,
        )
        if swap is None:
            interventions.append(
                GuardIntervention(
                    rule="same-type-cap",
                    reason=(
                        f"Type {current.question_type!r} would be "
                        f"{max_consecutive_same_type + 1}th consecutive but no "
                        f"alternative open question exists."
                    ),
                    original_question_id=current.question_id,
                    original_type=current.question_type,
                    corrected_question_id=current.question_id,
                    corrected_type=current.question_type,
                )
            )
        else:
            swap_type = _resolve_swap_type(swap, metrics, current.question_type)
            interventions.append(
                GuardIntervention(
                    rule="same-type-cap",
                    reason=(
                        f"Type {current.question_type!r} would be "
                        f"{max_consecutive_same_type + 1}th consecutive; "
                        f"swapped to {swap.id}."
                    ),
                    original_question_id=current.question_id,
                    original_type=current.question_type,
                    corrected_question_id=swap.id,
                    corrected_type=swap_type,
                )
            )
            current = QuestionSelection(
                question_id=swap.id,
                question=swap.question,
                question_type=swap_type,
                reasoning=current.reasoning,
                relevant_finding_ids=current.relevant_finding_ids,
            )

    return GuardedSelection(current, tuple(interventions))


def _pick_fallback_open(open_questions: list[Question]) -> Question | None:
    if not open_questions:
        return None
    return sorted(open_questions, key=lambda q: _PRIORITY_RANK[q.priority])[0]


def _would_exceed_same_type_cap(
    type_: QuestionType,
    recent_types: list[QuestionType],
    max_consecutive: int,
) -> bool:
    if len(recent_types) < max_consecutive:
        return False
    return all(t == type_ for t in recent_types[:max_consecutive])


def _would_swap_exceed_cap(
    q: Question,
    metrics: list[ConductorMetric],
    recent_types: list[QuestionType],
    max_consecutive: int,
) -> bool:
    prior_type = next(
        (m.question_type for m in metrics if m.question_id == q.id and m.question_type),
        None,
    )
    if prior_type is None:
        return False
    return _would_exceed_same_type_cap(prior_type, recent_types, max_consecutive)


def _resolve_swap_type(
    q: Question,
    metrics: list[ConductorMetric],
    fallback: QuestionType,
) -> QuestionType:
    prior = next(
        (m.question_type for m in metrics if m.question_id == q.id and m.question_type),
        None,
    )
    return prior or fallback


# ── select() — orchestrates the gates ───────────────────────────────────────


def select(
    state: ProjectState,
    open_questions: list[Question],
    *,
    proposed: QuestionSelection | None = None,
    critic_output: str | None = None,
) -> SelectorResult:
    """Run the three gates in order; return what the conductor should do next.

      1. Completion gate — if no open questions and no active dispatch, the
         project is done. Transitions state.status to "completed" *only* via
         the returned event; this function is pure on `state` itself.
      2. Halt-reason reader — operator kill switch. If state.halt_reason is
         set, we exit with HALT_REQUESTED.
      3. Reflection-veto parser — if the prior critic asked for a halt, we
         exit with HALT_REQUESTED (rule="critic-veto").

    Returns SelectorResult with one of {SELECTED, COMPLETED, HALTED, VETOED}.
    """
    # Halt-reason reader runs FIRST: an operator kill must trump everything,
    # including a queue that already looks empty (we still want the event
    # logged with the operator's reason).
    if state.halt_reason:
        return SelectorResult(
            outcome=SelectorOutcome.HALTED,
            event=Event(
                event_type=EventType.HALT_REQUESTED,
                step="select",
                iteration=state.iteration,
                payload={"source": "operator", "reason": state.halt_reason},
            ),
            reason=state.halt_reason,
        )

    # Reflection veto from prior critic output.
    veto = parse_reflection_veto(critic_output)
    if veto is not None:
        return SelectorResult(
            outcome=SelectorOutcome.VETOED,
            event=Event(
                event_type=EventType.HALT_REQUESTED,
                step="select",
                iteration=state.iteration,
                payload={"source": "critic-veto", "matched": veto},
            ),
            reason=veto,
        )

    # Completion gate.
    if not open_questions and state.active_question_id is None:
        return SelectorResult(
            outcome=SelectorOutcome.COMPLETED,
            event=Event(
                event_type=EventType.HALT_REQUESTED,
                step="select",
                iteration=state.iteration,
                payload={"source": "completion-gate"},
            ),
            reason="no open questions; no active dispatch",
        )

    return SelectorResult(outcome=SelectorOutcome.SELECTED, selection=proposed)


__all__ = [
    "GuardIntervention",
    "GuardedSelection",
    "QuestionSelection",
    "SelectorOutcome",
    "SelectorResult",
    "apply_selection_guards",
    "parse_reflection_veto",
    "select",
]
