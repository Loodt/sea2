"""Tier 3 lightweight falsifier.

Article §11.4: adversarial check. Phase 3 ships only the cheap variant —
scan the admitted chunk with Tier 1 NLI in CONTRADICTION mode. If NLI
labels the (chunk → claim) relationship as 'contradiction' rather than
'entailment'/'neutral', the chunk itself refutes the claim. This catches
the most common failure mode (extractor mis-summarises) without requiring
a separate adversarial retrieval loop.

The full adversarial-retrieve variant — query a Searcher for the negation
of the claim and check if it surfaces — is deferred to Phase 4 to avoid
quota burn on the comparison run.

Feature-flagged by `SEA2_TIER3_ENABLED`.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

from sea2.events import Event, EventType
from sea2.verification.tier1 import Tier1Status, check_entailment

if TYPE_CHECKING:
    from sea2.models import Finding
    from sea2.verification.tier1 import EntailmentBackend


TIER3_FLAG_ENV = "SEA2_TIER3_ENABLED"


class Tier3Status(StrEnum):
    OK = "ok"
    REFUTED = "refuted"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class Tier3Result:
    status: Tier3Status
    detail: str
    event: Event | None = None


def is_enabled() -> bool:
    return os.environ.get(TIER3_FLAG_ENV, "").strip() in {"1", "true", "yes"}


def find_contradictions(
    finding: Finding,
    chunk_text: str,
    *,
    backend: EntailmentBackend | None = None,
) -> Tier3Result:
    """Run Tier 1 against the chunk; flag the finding if the result is
    CONTRADICTED.

    Returns SKIPPED when the flag is off AND no backend was supplied.
    Returns OK when the chunk does not contradict the claim (NLI gave
    ENTAILED, NEUTRAL, ERROR, or SKIPPED itself).
    """
    if not is_enabled() and backend is None:
        return Tier3Result(
            status=Tier3Status.SKIPPED,
            detail="feature-flag-off",
            event=Event(
                event_type=EventType.TIER3_SKIPPED,
                step="verify",
                finding_id=finding.id,
            ),
        )

    tier1_res = check_entailment(finding, chunk_text, backend=backend)
    if tier1_res.status is Tier1Status.CONTRADICTED:
        return Tier3Result(
            status=Tier3Status.REFUTED,
            detail="chunk contradicts claim",
            event=Event(
                event_type=EventType.TIER3_REFUTED,
                step="verify",
                finding_id=finding.id,
                payload={
                    "score": tier1_res.score,
                    "source": "in-chunk-nli",
                },
            ),
        )
    return Tier3Result(
        status=Tier3Status.OK,
        detail=f"no-contradiction (tier1={tier1_res.status.value})",
    )


__all__ = [
    "TIER3_FLAG_ENV",
    "Tier3Result",
    "Tier3Status",
    "find_contradictions",
    "is_enabled",
]
