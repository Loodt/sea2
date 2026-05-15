"""Lineage ledger.

Port of `sea/src/conductor.ts:1125-1148` `appendLineageEntry`. SEA's call
sites passed `scoreBefore: null` and let `scoreAfter` default to `null`,
which is exactly the SCORE_FIELD_LOSS infra-debt the audit flagged: scores
never actually landed in the ledger. SEA2 requires callers to pass both
scores explicitly (a `LineageEntry` will fail to construct otherwise — see
`sea2.models.LineageEntry`).
"""

from __future__ import annotations

import datetime as _dt
from pathlib import Path

from sea2.models import LineageEntry, LineageTarget
from sea2.store import atomic_append_jsonl


def lineage_path(project_dir: Path | str) -> Path:
    return Path(project_dir) / "lineage" / "changes.jsonl"


def append_lineage_entry(
    project_dir: Path | str,
    *,
    iteration: int,
    target: LineageTarget,
    version_before: str,
    version_after: str,
    change_type: str,
    change_summary: str,
    reasoning: str,
    score_before: float | None,
    score_after: float | None,
    timestamp: str | None = None,
) -> LineageEntry:
    """Append a lineage entry. Both scores are required kwargs (no defaults).

    The score arguments accept `None` for genuinely-not-scored events, but the
    caller must spell it explicitly — there is no implicit fallback. This is
    the score-piping fix for infra-debt #5 (SCORE_FIELD_LOSS).
    """
    entry = LineageEntry(
        iteration=iteration,
        timestamp=timestamp or _dt.datetime.now(_dt.UTC).isoformat(),
        target=target,
        version_before=version_before,
        version_after=version_after,
        change_type=change_type,
        change_summary=change_summary,
        reasoning=reasoning,
        score_before=score_before,
        score_after=score_after,
    )
    atomic_append_jsonl(lineage_path(project_dir), entry)
    return entry


__all__ = [
    "append_lineage_entry",
    "lineage_path",
]
