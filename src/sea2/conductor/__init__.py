"""Conductor: select → retrieve → extract → verify → integrate loop.

Phase 1 ships a skeleton — completion gate, halt-reason reader, reflection-
veto parser, selection guards, question caps, integrate step. No retrieve;
extract is a noop. End-to-end flow is provable through tests.
"""

from sea2.conductor.caps import CapTrimAction, apply_question_caps
from sea2.conductor.integrate import IntegrateResult, integrate
from sea2.conductor.selector import (
    GuardedSelection,
    GuardIntervention,
    QuestionSelection,
    SelectorOutcome,
    apply_selection_guards,
    parse_reflection_veto,
    select,
)

__all__ = [
    "CapTrimAction",
    "GuardIntervention",
    "GuardedSelection",
    "IntegrateResult",
    "QuestionSelection",
    "SelectorOutcome",
    "apply_question_caps",
    "apply_selection_guards",
    "integrate",
    "parse_reflection_veto",
    "select",
]
