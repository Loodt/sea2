"""Conformal abstention — uncalibrated stub.

Article §12 + plan Phase 4: a calibrated conformal predictor abstains
on findings below a coverage threshold (alpha=0.1 -> 90% coverage). The
calibration set is `(CGS, human-judged correctness)` pairs.

Phase 3 ships the scaffold but not the calibrated path: the comparison
run itself produces the calibration data, and Phase 4 wires it back in.
For now `compute_abstention` uses CGS as a confidence proxy: findings
with CGS < `uncalibrated_threshold` (default 0.34, i.e. less than 1 of 3
axes positive) are marked ABSTAIN.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

    from sea2.verification.cgs import CitationGroundingScore

UNCALIBRATED_THRESHOLD = 0.34


class AbstentionDecision(StrEnum):
    ACCEPT = "accept"
    ABSTAIN = "abstain"


@dataclass(frozen=True)
class CalibrationRow:
    """One calibration sample: a finding's CGS vs operator-judged correctness."""

    finding_id: str
    cgs: float
    is_correct: bool


@dataclass(frozen=True)
class AbstentionResult:
    finding_id: str
    decision: AbstentionDecision
    cgs: float
    threshold: float
    calibrated: bool
    detail: str


def compute_abstention(
    cgs_rows: Iterable[CitationGroundingScore],
    *,
    calibration: list[CalibrationRow] | None = None,
    alpha: float = 0.1,
    uncalibrated_threshold: float = UNCALIBRATED_THRESHOLD,
) -> list[AbstentionResult]:
    """Mark each CGS row as ACCEPT or ABSTAIN.

    When `calibration` is provided, compute the conformal threshold at
    coverage 1-alpha: sort calibration CGS values for correct items ascending,
    take the (alpha * n)-th percentile as the threshold. Otherwise use the
    fixed `uncalibrated_threshold` and mark every result as
    `calibrated=False`.
    """
    if calibration:
        threshold = _conformal_threshold(calibration, alpha)
        calibrated = True
        detail_prefix = f"calibrated (alpha={alpha}, n={len(calibration)})"
    else:
        threshold = uncalibrated_threshold
        calibrated = False
        detail_prefix = "uncalibrated"

    out: list[AbstentionResult] = []
    for row in cgs_rows:
        decision = (
            AbstentionDecision.ACCEPT
            if row.aggregate >= threshold
            else AbstentionDecision.ABSTAIN
        )
        out.append(
            AbstentionResult(
                finding_id=row.finding_id,
                decision=decision,
                cgs=row.aggregate,
                threshold=threshold,
                calibrated=calibrated,
                detail=detail_prefix,
            )
        )
    return out


def _conformal_threshold(
    calibration: list[CalibrationRow], alpha: float
) -> float:
    """Naive conformal predictor — threshold = the alpha-quantile of CGS values
    among correct calibration items. Below threshold -> abstain to maintain
    1-alpha coverage of true positives.
    """
    correct = sorted(r.cgs for r in calibration if r.is_correct)
    if not correct:
        return UNCALIBRATED_THRESHOLD
    # Position of the alpha-quantile in the sorted list.
    idx = int(alpha * len(correct))
    idx = max(0, min(idx, len(correct) - 1))
    return correct[idx]


__all__ = [
    "UNCALIBRATED_THRESHOLD",
    "AbstentionDecision",
    "AbstentionResult",
    "CalibrationRow",
    "compute_abstention",
]
