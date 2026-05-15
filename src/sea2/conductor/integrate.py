"""Integrate step: schema → Tier 0 → DAG → atomic-append.

Validates each candidate Finding against the schema (D2), runs Tier 0 checks
(D5), runs DAG cycle + orphan detection (D7), and persists via the store
(D4). Every failure emits a structured event (commitment 6: fail loudly).

Phase 1 input is a list of pre-built `Finding` objects from `extract_noop()`.
Phase 2 replaces that source with a real retrieve/extract pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from pydantic import ValidationError

from sea2.events import Event, EventType, emit
from sea2.models import Finding, VerifierStatus
from sea2.store import atomic_append_jsonl, findings_path, read_findings
from sea2.verification.dag import propagate_confidence, validate_dag
from sea2.verification.tier0 import (
    Tier0Result,
    check_ledger_consistency,
    check_url_resolves,
)

if TYPE_CHECKING:
    from pathlib import Path

    import httpx


@dataclass(frozen=True)
class IntegrateResult:
    admitted: tuple[Finding, ...] = ()
    rejected: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    events_emitted: int = 0


def _emit(project_dir: Path | str, event: Event | None) -> int:
    if event is None:
        return 0
    emit(project_dir, event)
    return 1


def integrate(
    project_dir: Path | str,
    candidates: list[Finding | dict[str, object]],
    *,
    http_client: httpx.Client | None = None,
) -> IntegrateResult:
    """Validate, verify, and persist findings. Returns admit/reject summary.

    `candidates` may be a list of `Finding` instances OR raw dicts (so the
    integrate step also serves as the schema gate when called from an
    extract stage that produced dict output).
    """
    existing = read_findings(project_dir)
    by_id: dict[str, Finding] = {f.id: f for f in existing}
    admitted: list[Finding] = []
    rejected: list[tuple[str, str]] = []
    events = 0

    for raw in candidates:
        try:
            f = raw if isinstance(raw, Finding) else Finding.model_validate(raw)
        except ValidationError as e:
            label = _identify(raw)
            rejected.append((label, f"schema: {e}"))
            events += _emit(
                project_dir,
                Event(
                    event_type=EventType.VALIDATE_FAIL,
                    step="integrate",
                    finding_id=label,
                    error=str(e),
                ),
            )
            continue

        dag_res = validate_dag(f, by_id)
        if not dag_res.valid:
            reason = (
                f"dag-cycle: {' → '.join(dag_res.cycle_path or ())}"
                if dag_res.cycle_path
                else f"dag-orphan: {','.join(dag_res.orphans)}"
            )
            rejected.append((f.id, reason))
            events += _emit(
                project_dir,
                Event(
                    event_type=EventType.VALIDATE_FAIL,
                    step="integrate",
                    finding_id=f.id,
                    error=reason,
                    payload={
                        "cycle_path": list(dag_res.cycle_path or ()),
                        "orphans": list(dag_res.orphans),
                    },
                ),
            )
            continue

        # Bound tag by weakest premise. If the bound differs from what the
        # producer claimed, we record the corrected tag — the original is
        # NOT persisted as-declared.
        bounded_tag = propagate_confidence(f, by_id)
        if bounded_tag != f.tag:
            f = f.model_copy(update={"tag": bounded_tag})

        # Tier 0: URL resolves.
        url_res: Tier0Result = check_url_resolves(f, client=http_client)
        events += _emit(project_dir, url_res.event)
        # Tier 0: ledger consistency.
        ledger_res: Tier0Result = check_ledger_consistency(f, existing)
        events += _emit(project_dir, ledger_res.event)

        if url_res.verified and ledger_res.verified:
            verifier_status = VerifierStatus.VERIFIED
        elif not url_res.verified and not ledger_res.verified:
            verifier_status = VerifierStatus.FAILED
        else:
            verifier_status = VerifierStatus.FLAGGED

        f = f.model_copy(update={"verifier_status": verifier_status})

        try:
            atomic_append_jsonl(findings_path(project_dir), f)
        except OSError as e:
            rejected.append((f.id, f"store-append: {e}"))
            events += _emit(
                project_dir,
                Event(
                    event_type=EventType.STORE_APPEND_FAIL,
                    step="integrate",
                    finding_id=f.id,
                    error=str(e),
                ),
            )
            continue

        events += _emit(
            project_dir,
            Event(
                event_type=EventType.STORE_APPEND_OK,
                step="integrate",
                finding_id=f.id,
            ),
        )
        admitted.append(f)
        by_id[f.id] = f
        existing.append(f)

    return IntegrateResult(
        admitted=tuple(admitted),
        rejected=tuple(rejected),
        events_emitted=events,
    )


def _identify(raw: Finding | dict[str, object]) -> str:
    if isinstance(raw, Finding):
        return raw.id
    candidate = raw.get("id") if isinstance(raw, dict) else None
    return str(candidate) if candidate is not None else "<unidentified>"


# ── Stub extract step (Phase 1 only) ─────────────────────────────────────────


def extract_noop(fixtures: list[Finding]) -> list[Finding]:
    """Return the fixtures unchanged.

    Phase 1 only — exists so the integrate→store loop can be exercised end
    to end without a retrieve step. Phase 2 replaces this with a real
    extractor that consumes admitted chunks.
    """
    return list(fixtures)


__all__ = [
    "IntegrateResult",
    "extract_noop",
    "integrate",
]
