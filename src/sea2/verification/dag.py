"""Provenance DAG primitives.

Article §11.4 and audit-alignment finding #3. SEA's `derivationChain.premises`
was a 1-deep array with no graph mechanics. SEA2 makes the DAG first-class:
the integrate step refuses to admit a finding whose `derived_from` introduces
a cycle or references a non-existent premise.

Confidence/epistemic propagation: a finding derived from premises cannot be
SOURCE if any premise is weaker. The effective tag is bounded by the weakest
premise. (Article §11.4.)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from sea2.models import EPISTEMIC_RANK, EpistemicTag

if TYPE_CHECKING:
    from sea2.models import Finding


@dataclass(frozen=True)
class DagResult:
    valid: bool
    cycle_path: tuple[str, ...] | None = None
    orphans: tuple[str, ...] = field(default_factory=tuple)


def validate_dag(
    finding: Finding,
    existing: dict[str, Finding],
) -> DagResult:
    """Validate the provenance graph after adding `finding`.

    Returns a `DagResult` capturing:
      - cycle_path: the cycle if one would be created (None otherwise).
      - orphans: any premise IDs that don't resolve to an existing finding.

    `finding` is treated as virtually present in the graph (its premises are
    resolved against `existing`, and walking from `finding` follows the
    `existing` graph from each premise). Pure function; no I/O.
    """
    # Orphan detection: every premise must exist already in the store. A
    # finding cannot be admitted with a forward-reference.
    orphans = tuple(p for p in finding.derived_from if p not in existing)
    if orphans:
        return DagResult(valid=False, orphans=orphans)

    # Direct self-reference is caught by Finding's validator, but verify
    # transitively too: walk from each premise and check we don't loop back
    # to `finding.id`.
    cycle = _find_cycle(finding.id, finding.derived_from, existing)
    if cycle is not None:
        return DagResult(valid=False, cycle_path=cycle)

    return DagResult(valid=True)


def _find_cycle(
    new_id: str,
    seeds: list[str],
    graph: dict[str, Finding],
) -> tuple[str, ...] | None:
    """DFS from each seed; if we reach `new_id`, that path is a cycle."""
    for seed in seeds:
        visited: set[str] = set()
        stack: list[tuple[str, tuple[str, ...]]] = [(seed, (new_id, seed))]
        while stack:
            node, path = stack.pop()
            if node == new_id:
                return path
            if node in visited:
                continue
            visited.add(node)
            f = graph.get(node)
            if f is None:
                continue
            for premise in f.derived_from:
                stack.append((premise, (*path, premise)))
    return None


def propagate_confidence(
    finding: Finding,
    existing: dict[str, Finding],
) -> EpistemicTag:
    """Bound `finding.tag` by the weakest tag among its premises.

    Article §11.4: "a claim derived from three ESTIMATED inputs cannot itself
    be SOURCE." If `derived_from` is empty, the declared tag stands. Premises
    must already be validated (see `validate_dag`); missing premises raise.
    """
    if not finding.derived_from:
        return finding.tag

    weakest_rank = EPISTEMIC_RANK[finding.tag]
    weakest_tag = finding.tag
    for premise_id in finding.derived_from:
        premise = existing.get(premise_id)
        if premise is None:
            raise ValueError(
                f"finding {finding.id}: premise {premise_id} not in store "
                f"(call validate_dag before propagate_confidence)"
            )
        if EPISTEMIC_RANK[premise.tag] > weakest_rank:
            weakest_rank = EPISTEMIC_RANK[premise.tag]
            weakest_tag = premise.tag
    return weakest_tag


__all__ = [
    "DagResult",
    "propagate_confidence",
    "validate_dag",
]
