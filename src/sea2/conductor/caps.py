"""Question-cap trims.

Port of `sea/src/question-caps.ts` shape minus the prose-only modes
(`exploit`, `closure`, `non-closing`, `thin-closure`). Those re-derive in
Phase 2 from retrieval / extraction / verification metrics rather than
loop-iteration heuristics.

Three rules remain:
  - per-dispatch-new   (landscape ≤ 5, others ≤ 3)
  - iter-boundary-new  (convergence schedule)
  - type-queue-cap     (per-type open-question ceiling)

Output is a list of `CapTrimAction` records describing the trim. The caller
mutates the questions store atomically; this module is pure.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from collections.abc import Iterable

    from sea2.models import ConductorMetric, Question, QuestionType


CapRule = Literal["per-dispatch-new", "iter-boundary-new", "type-queue-cap"]

# Dispatch caps per question type — port of SEA's QUESTION_TYPE_DISPATCH_CAP.
QUESTION_TYPE_DISPATCH_CAP: dict[QuestionType, int] = {
    "landscape": 5,
    "kill-check": 5,
    "data-hunt": 5,
    "mechanism": 5,
    "synthesis": 3,
    "first-principles": 3,
    "design-space": 4,
    "divergence": 3,
}

PER_DISPATCH_NEW_QUESTION_CAP_LANDSCAPE = 5
PER_DISPATCH_NEW_QUESTION_CAP_OTHER = 3


@dataclass(frozen=True)
class CapTrimAction:
    rule: CapRule
    reason: str
    removed_question_ids: tuple[str, ...]
    effective_cap: int
    observed_count: int


_PRIORITY_RANK = {"low": 0, "medium": 1, "high": 2}


def _select_for_trim(candidates: list[Question], n: int) -> list[Question]:
    """Lowest-priority first; tiebreak by file order (last-added first)."""
    indexed = list(enumerate(candidates))
    indexed.sort(key=lambda pair: (_PRIORITY_RANK[pair[1].priority], -pair[0]))
    return [q for _, q in indexed[:n]]


def _compute_iter_boundary_cap(questions: list[Question], iteration: int) -> int | None:
    """None means "no cap". Otherwise the cap on new-this-iter open questions."""
    open_count = sum(1 for q in questions if q.status == "open")
    resolved = sum(1 for q in questions if q.status == "resolved")
    total = len(questions)
    resolved_pct = resolved / total if total > 0 else 0
    if iteration >= 20 and resolved_pct > 0.7:  # noqa: PLR2004
        return 0
    if iteration >= 18 and open_count > 8:  # noqa: PLR2004
        return 0
    if iteration >= 15:  # noqa: PLR2004
        return 1
    if iteration >= 12 and open_count > 12:  # noqa: PLR2004
        return 1
    return None


def _apply_type_queue_cap(
    questions: list[Question],
    iteration: int,
    metrics: list[ConductorMetric],
) -> list[CapTrimAction]:
    type_of: dict[str, QuestionType] = {
        m.question_id: m.question_type for m in metrics if m.question_type
    }
    open_by_type: dict[QuestionType, list[Question]] = {}
    for q in questions:
        if q.status != "open":
            continue
        t = type_of.get(q.id)
        if t is None:
            continue
        open_by_type.setdefault(t, []).append(q)

    actions: list[CapTrimAction] = []
    for qtype, open_list in open_by_type.items():
        cap = QUESTION_TYPE_DISPATCH_CAP[qtype]
        if len(open_list) <= cap:
            continue
        overflow = len(open_list) - cap
        trimmable = [q for q in open_list if q.iteration == iteration]
        if not trimmable:
            continue
        to_remove = _select_for_trim(trimmable, min(overflow, len(trimmable)))
        if not to_remove:
            continue
        actions.append(
            CapTrimAction(
                rule="type-queue-cap",
                reason=(
                    f"Type {qtype!r} open count {len(open_list)} exceeds dispatch cap "
                    f"{cap}; trimmed {len(to_remove)} new-this-iter."
                ),
                removed_question_ids=tuple(q.id for q in to_remove),
                effective_cap=cap,
                observed_count=len(open_list),
            )
        )
    return actions


def _apply_iter_boundary_cap(
    questions: list[Question], iteration: int
) -> CapTrimAction | None:
    cap = _compute_iter_boundary_cap(questions, iteration)
    if cap is None:
        return None
    new_this_iter = [
        q for q in questions if q.iteration == iteration and q.status == "open"
    ]
    if len(new_this_iter) <= cap:
        return None
    overflow = len(new_this_iter) - cap
    to_remove = _select_for_trim(new_this_iter, overflow)
    if not to_remove:
        return None
    return CapTrimAction(
        rule="iter-boundary-new",
        reason=(
            f"Iter {iteration} convergence cap = {cap}; {len(new_this_iter)} new "
            f"questions, trimmed {len(to_remove)}."
        ),
        removed_question_ids=tuple(q.id for q in to_remove),
        effective_cap=cap,
        observed_count=len(new_this_iter),
    )


def _apply_per_dispatch_cap(
    questions: list[Question],
    iteration: int,
    *,
    landscape_dispatch: bool,
) -> CapTrimAction | None:
    cap = (
        PER_DISPATCH_NEW_QUESTION_CAP_LANDSCAPE
        if landscape_dispatch
        else PER_DISPATCH_NEW_QUESTION_CAP_OTHER
    )
    new_this_iter = [
        q for q in questions if q.iteration == iteration and q.status == "open"
    ]
    if len(new_this_iter) <= cap:
        return None
    overflow = len(new_this_iter) - cap
    to_remove = _select_for_trim(new_this_iter, overflow)
    if not to_remove:
        return None
    label = "landscape" if landscape_dispatch else "non-landscape"
    return CapTrimAction(
        rule="per-dispatch-new",
        reason=(
            f"Per-dispatch cap = {cap} ({label}); {len(new_this_iter)} new questions, "
            f"trimmed {len(to_remove)}."
        ),
        removed_question_ids=tuple(q.id for q in to_remove),
        effective_cap=cap,
        observed_count=len(new_this_iter),
    )


def apply_question_caps(
    questions: list[Question],
    *,
    iteration: int,
    landscape_dispatch: bool,
    prior_metrics: Iterable[ConductorMetric] = (),
) -> tuple[list[Question], list[CapTrimAction]]:
    """Compute the trimmed questions list and the actions taken.

    Pure: returns the new list rather than mutating in place.
    """
    working = list(questions)
    metrics = list(prior_metrics)
    actions: list[CapTrimAction] = []

    type_actions = _apply_type_queue_cap(working, iteration, metrics)
    if type_actions:
        working = _remove_by_ids(working, type_actions)
        actions.extend(type_actions)

    iter_action = _apply_iter_boundary_cap(working, iteration)
    if iter_action is not None:
        working = _remove_by_ids(working, [iter_action])
        actions.append(iter_action)

    per_dispatch_action = _apply_per_dispatch_cap(
        working, iteration, landscape_dispatch=landscape_dispatch
    )
    if per_dispatch_action is not None:
        working = _remove_by_ids(working, [per_dispatch_action])
        actions.append(per_dispatch_action)

    return working, actions


def _remove_by_ids(
    questions: list[Question], actions: Iterable[CapTrimAction]
) -> list[Question]:
    removed: set[str] = set()
    for a in actions:
        removed.update(a.removed_question_ids)
    if not removed:
        return questions
    return [q for q in questions if q.id not in removed]


__all__ = [
    "PER_DISPATCH_NEW_QUESTION_CAP_LANDSCAPE",
    "PER_DISPATCH_NEW_QUESTION_CAP_OTHER",
    "QUESTION_TYPE_DISPATCH_CAP",
    "CapRule",
    "CapTrimAction",
    "apply_question_caps",
]
