"""Question picker.

Phase 2 ships a deterministic picker: highest priority first, then oldest
iteration first, then id. No LLM scoring — that lands in Phase 3 with the
planner stage. The picker returns a `QuestionSelection` that gets fed
through `apply_selection_guards` before being dispatched.

Why deterministic for Phase 2: the loop should be fully testable without
mocking an LLM. The article's selection-quality work belongs in Phase 3
once the rest of the pipeline has stable behaviour to compare against.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sea2.conductor.selector import QuestionSelection

if TYPE_CHECKING:
    from sea2.models import Question, QuestionPriority


_PRIORITY_RANK: dict[QuestionPriority, int] = {"high": 0, "medium": 1, "low": 2}


def pick_next_question(questions: list[Question]) -> QuestionSelection | None:
    """Pick the highest-priority open question. None if no open questions.

    The returned selection has `question_type` taken from the Question's
    own `question_type` field (filled in when the question was created)
    or `data-hunt` as a neutral default. Guards may override it.
    """
    open_qs = [q for q in questions if q.status == "open"]
    if not open_qs:
        return None
    ranked = sorted(
        open_qs,
        key=lambda q: (_PRIORITY_RANK[q.priority], q.iteration, q.id),
    )
    chosen = ranked[0]
    return QuestionSelection(
        question_id=chosen.id,
        question=chosen.question,
        question_type=chosen.question_type or "data-hunt",
        reasoning="deterministic priority-ordered pick (Phase 2)",
        relevant_finding_ids=(),
    )


__all__ = ["pick_next_question"]
