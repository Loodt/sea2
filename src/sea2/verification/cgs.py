"""Citation Grounding Score.

Article §11 / pre-registration §M-axes. A deterministic per-finding score
combining the three Tier 0/1/2 signals:

  - resolvability: at least one of {URL, DOI, arXiv} resolved.
  - quote-supported: TIER0_QUOTE_OK present (or no quote required).
  - entailment: TIER1_ENTAILED present (or Tier 2 AGREE on the audit subset).

Each axis contributes 0 or 1; the aggregate is the mean ∈ [0, 1].

CGS sits *beside* `verifier_status`. `verifier_status` is the categorical
gate (VERIFIED / FLAGGED / FAILED / PENDING). CGS is the continuous score
the comparison-protocol uses for ranking and reporting.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from sea2.store import atomic_append_jsonl, read_events, read_findings

if TYPE_CHECKING:
    from sea2.models import Finding


_RESOLVE_OK = {"TIER0_URL_OK", "TIER0_DOI_OK", "TIER0_ARXIV_OK"}
_RESOLVE_FAIL = {"TIER0_URL_FAIL", "TIER0_DOI_FAIL", "TIER0_ARXIV_FAIL"}
_QUOTE_OK = "TIER0_QUOTE_OK"
_QUOTE_FAIL = "TIER0_QUOTE_FAIL"
_ENTAILED = "TIER1_ENTAILED"
_CONTRADICTED = "TIER1_CONTRADICTED"
_TIER2_AGREE = "TIER2_AGREE"
_TIER2_DISAGREE = "TIER2_DISAGREE"


@dataclass(frozen=True)
class CitationGroundingScore:
    finding_id: str
    resolvability: int  # 0 or 1; -1 means not-evaluated
    quote_supported: int
    entailment: int
    aggregate: float

    def to_dict(self) -> dict[str, object]:
        return {
            "finding_id": self.finding_id,
            "resolvability": self.resolvability,
            "quote_supported": self.quote_supported,
            "entailment": self.entailment,
            "aggregate": self.aggregate,
        }


def _axis_from_events(types: set[str], ok_types: set[str], fail_types: set[str]) -> int:
    """Return 1 if any OK fired, -1 if any FAIL fired without OK, 0 if neither.

    Returning -1 means "actively negative"; 0 means "not evaluated."
    """
    if types & ok_types:
        return 1
    if types & fail_types:
        return -1
    return 0


def compute_cgs(
    finding: Finding,
    events_for_finding: list[dict[str, object]],
) -> CitationGroundingScore:
    """Compute CGS from the events associated with a single finding.

    Caller filters events by finding_id; this function just inspects types.
    """
    types: set[str] = {str(e.get("event_type")) for e in events_for_finding}

    resolvability = _axis_from_events(types, _RESOLVE_OK, _RESOLVE_FAIL)
    quote_supported = _axis_from_events(types, {_QUOTE_OK}, {_QUOTE_FAIL})
    entailment_t1 = _axis_from_events(types, {_ENTAILED}, {_CONTRADICTED})
    entailment_t2 = _axis_from_events(types, {_TIER2_AGREE}, {_TIER2_DISAGREE})
    # Combine Tier 1 + Tier 2 with OR-of-positives, AND-of-negatives priority:
    if entailment_t1 == 1 or entailment_t2 == 1:
        entailment = 1
    elif entailment_t1 == -1 or entailment_t2 == -1:
        entailment = -1
    else:
        entailment = 0

    # Treat 0 (not-evaluated) as 0 in the aggregate; -1 as 0; 1 as 1.
    parts = [max(0, axis) for axis in (resolvability, quote_supported, entailment)]
    aggregate = sum(parts) / 3.0

    return CitationGroundingScore(
        finding_id=finding.id,
        resolvability=resolvability,
        quote_supported=quote_supported,
        entailment=entailment,
        aggregate=aggregate,
    )


def compute_all_cgs(project_dir: Path | str) -> list[CitationGroundingScore]:
    """Compute CGS for every finding in the store. Pure read; does not write."""
    findings = read_findings(project_dir)
    all_events = read_events(project_dir)
    by_finding: dict[str, list[dict[str, object]]] = {}
    for ev in all_events:
        fid = str(ev.get("finding_id") or "")
        if not fid:
            continue
        by_finding.setdefault(fid, []).append(ev)
    return [compute_cgs(f, by_finding.get(f.id, [])) for f in findings]


def write_cgs(project_dir: Path | str) -> Path:
    """Compute all CGS and write to cgs.jsonl. Returns the path."""
    from pydantic import BaseModel  # noqa: PLC0415

    class _CgsRow(BaseModel):
        finding_id: str
        resolvability: int
        quote_supported: int
        entailment: int
        aggregate: float

    rows = compute_all_cgs(project_dir)
    out = Path(project_dir) / "cgs.jsonl"
    # Rewrite fresh — CGS is a deterministic function of the store, so
    # overwriting is correct.
    if out.exists():
        out.unlink()
    for r in rows:
        atomic_append_jsonl(out, _CgsRow(**r.to_dict()))  # type: ignore[arg-type]
    return out


__all__ = [
    "CitationGroundingScore",
    "compute_all_cgs",
    "compute_cgs",
    "write_cgs",
]
