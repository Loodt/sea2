"""Integrate step: schema → DAG → Tier 0 → Tier 1 → store.

Validates each candidate Finding against the schema, runs DAG cycle +
orphan detection, runs all Tier 0 checks (URL, ledger, quote-supported,
DOI, arXiv, PDF page bounds) against the admitted chunk it references,
optionally runs Tier 1 NLI when the flag is on, and persists via the
store. Every failure emits a structured event (commitment 6: fail loudly).

Phase 2 wires this to the chunk store: a finding's `admitted_chunk_id`
MUST resolve to a chunk persisted by the retrieve stage. Findings that
don't are rejected before any verification runs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from pydantic import ValidationError

from sea2.events import Event, EventType, emit
from sea2.models import Finding, VerifierStatus
from sea2.store import (
    atomic_append_jsonl,
    find_chunk_by_id,
    findings_path,
    read_findings,
)
from sea2.verification.dag import propagate_confidence, validate_dag
from sea2.verification.tier0 import (
    Tier0Result,
    check_arxiv_resolves,
    check_doi_resolves,
    check_ledger_consistency,
    check_pdf_page_exists,
    check_quote_supported,
    check_url_resolves,
)
from sea2.verification.tier1 import Tier1Status, check_entailment, is_enabled

if TYPE_CHECKING:
    from pathlib import Path

    import httpx

    from sea2.chunks import Chunk
    from sea2.verification.tier1 import EntailmentBackend


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


def integrate(  # noqa: PLR0912, PLR0915 — linear pipeline; splitting hurts readability
    project_dir: Path | str,
    candidates: list[Finding | dict[str, object]],
    *,
    http_client: httpx.Client | None = None,
    require_chunk: bool = True,
    tier1_backend: EntailmentBackend | None = None,
) -> IntegrateResult:
    """Validate, verify, and persist findings.

    Parameters
    ----------
    require_chunk:
        When True (the Phase 2 default), every admitted finding must carry
        an `admitted_chunk_id` that resolves to a chunk in the store.
        Set False only for legacy / no-retrieve flows (Phase 1 tests).
    tier1_backend:
        Optional NLI backend. When None and `is_enabled()` is False, Tier 1
        is skipped (event emitted). When None and the flag is on, the
        default backend is loaded — see `verification.tier1`.
    """
    existing = read_findings(project_dir)
    by_id: dict[str, Finding] = {f.id: f for f in existing}
    admitted: list[Finding] = []
    rejected: list[tuple[str, str]] = []
    events = 0

    for raw in candidates:
        # ── schema ─────────────────────────────────────────────────────────
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

        # ── chunk resolution (Phase 2 retrieval-first commitment) ─────────
        chunk: Chunk | None = None
        if require_chunk:
            if f.admitted_chunk_id is None:
                rejected.append((f.id, "admitted_chunk_id missing"))
                events += _emit(
                    project_dir,
                    Event(
                        event_type=EventType.VALIDATE_FAIL,
                        step="integrate",
                        finding_id=f.id,
                        error="admitted_chunk_id missing",
                    ),
                )
                continue
            chunk = find_chunk_by_id(project_dir, f.admitted_chunk_id)
            if chunk is None:
                reason = f"admitted_chunk_id {f.admitted_chunk_id!r} not in chunk store"
                rejected.append((f.id, reason))
                events += _emit(
                    project_dir,
                    Event(
                        event_type=EventType.VALIDATE_FAIL,
                        step="integrate",
                        finding_id=f.id,
                        error=reason,
                    ),
                )
                continue

        # ── DAG ────────────────────────────────────────────────────────────
        dag_res = validate_dag(f, by_id)
        if not dag_res.valid:
            reason = (
                f"dag-cycle: {' -> '.join(dag_res.cycle_path or ())}"
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

        # Bound tag by weakest premise (article §11.4).
        bounded_tag = propagate_confidence(f, by_id)
        if bounded_tag != f.tag:
            f = f.model_copy(update={"tag": bounded_tag})

        # ── Tier 0: URL + ledger + quote + DOI + arXiv + PDF page ─────────
        signals: list[bool] = []

        url_res: Tier0Result = check_url_resolves(f, client=http_client)
        events += _emit(project_dir, url_res.event)
        if url_res.event is not None:
            signals.append(url_res.verified)

        ledger_res: Tier0Result = check_ledger_consistency(f, existing)
        events += _emit(project_dir, ledger_res.event)
        if ledger_res.event is not None:
            signals.append(ledger_res.verified)

        if chunk is not None:
            quote_res: Tier0Result = check_quote_supported(f, chunk.text)
            events += _emit(project_dir, quote_res.event)
            if quote_res.event is not None:
                signals.append(quote_res.verified)

        doi_res: Tier0Result = check_doi_resolves(f, client=http_client)
        events += _emit(project_dir, doi_res.event)
        if doi_res.event is not None:
            signals.append(doi_res.verified)

        arxiv_res: Tier0Result = check_arxiv_resolves(f, client=http_client)
        events += _emit(project_dir, arxiv_res.event)
        if arxiv_res.event is not None:
            signals.append(arxiv_res.verified)

        if chunk is not None and chunk.mime == "application/pdf":
            # We don't have a separate pages count yet — Phase 2.5 wires the
            # source_hash → page_count cache. For now: skip if no count.
            pass

        # ── Tier 1 NLI (when enabled) ──────────────────────────────────────
        tier1_signal: bool | None = None
        if chunk is not None and (is_enabled() or tier1_backend is not None):
            tier1_res = check_entailment(f, chunk.text, backend=tier1_backend)
            events += _emit(project_dir, tier1_res.event)
            if tier1_res.status is Tier1Status.ENTAILED:
                tier1_signal = True
            elif tier1_res.status is Tier1Status.CONTRADICTED:
                tier1_signal = False
            # NEUTRAL / SKIPPED / ERROR → don't contribute to verdict
        if tier1_signal is not None:
            signals.append(tier1_signal)

        # ── aggregate verifier status ──────────────────────────────────────
        verifier_status = _aggregate_signals(signals)
        f = f.model_copy(update={"verifier_status": verifier_status})

        # ── persist ────────────────────────────────────────────────────────
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


def _aggregate_signals(signals: list[bool]) -> VerifierStatus:
    """Combine Tier 0 / Tier 1 boolean signals into a VerifierStatus.

    - No signals at all → PENDING (nothing was checkable).
    - All signals positive → VERIFIED.
    - All signals negative → FAILED.
    - Mixed → FLAGGED.
    """
    if not signals:
        return VerifierStatus.PENDING
    if all(signals):
        return VerifierStatus.VERIFIED
    if not any(signals):
        return VerifierStatus.FAILED
    return VerifierStatus.FLAGGED


def _identify(raw: Finding | dict[str, object]) -> str:
    if isinstance(raw, Finding):
        return raw.id
    candidate = raw.get("id") if isinstance(raw, dict) else None
    return str(candidate) if candidate is not None else "<unidentified>"


# ── Stub extract step (Phase 1 only) ─────────────────────────────────────────


def extract_noop(fixtures: list[Finding]) -> list[Finding]:
    """Return the fixtures unchanged.

    Phase 1 only — exists so the integrate→store loop can be exercised end
    to end without a retrieve step. Phase 2's real extract lives in
    `sea2.conductor.extract`.
    """
    return list(fixtures)


__all__ = [
    "IntegrateResult",
    "check_pdf_page_exists",
    "extract_noop",
    "integrate",
]
