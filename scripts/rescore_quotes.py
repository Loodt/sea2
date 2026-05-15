"""Rescore Tier 0 quote-supported on existing findings.

Run after a SEA2 dispatch to update verifier_status with improved quote
matching. Reads findings.jsonl + chunks.jsonl + events.jsonl, re-runs
`check_quote_supported` against the updated normalizer, and rewrites
findings.jsonl with corrected `verifier_status`. Also appends new
TIER0_QUOTE_OK events for the corrected rows (TIER0_QUOTE_FAIL events
from prior runs are not retracted — the events ledger is append-only).

Usage::

    python scripts/rescore_quotes.py projects/au-token
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
from pathlib import Path

from sea2.events import Event, EventType, emit
from sea2.models import Finding, VerifierStatus
from sea2.store import (
    atomic_update_jsonl,
    find_chunk_by_id,
    findings_path,
    read_findings,
)
from sea2.verification.tier0 import check_quote_supported


def _now_iso() -> str:
    return _dt.datetime.now(_dt.UTC).isoformat()


def _recompute_status(
    f: Finding,
    quote_now_ok: bool,
    *,
    url_was_ok: bool,
    ledger_was_ok: bool,
    tier1_was_ok: bool | None,
    tier2_was_ok: bool | None,
) -> VerifierStatus:
    signals: list[bool] = [url_was_ok, ledger_was_ok, quote_now_ok]
    if tier1_was_ok is not None:
        signals.append(tier1_was_ok)
    if tier2_was_ok is not None:
        signals.append(tier2_was_ok)
    if not signals:
        return VerifierStatus.PENDING
    if all(signals):
        return VerifierStatus.VERIFIED
    if not any(signals):
        return VerifierStatus.FAILED
    return VerifierStatus.FLAGGED


def main(argv: list[str] | None = None) -> int:  # noqa: PLR0912, PLR0915
    parser = argparse.ArgumentParser(description="Re-run Tier 0 quote-check with improved unicode normalisation")
    parser.add_argument("project_dir", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    findings = read_findings(args.project_dir)
    changed = 0
    quote_ok_now = 0
    quote_fail_now = 0

    # Load events to figure out the original Tier 0/1/2 verdicts per finding.
    events_path = args.project_dir / "events.jsonl"
    events_by_finding: dict[str, set[str]] = {}
    if events_path.exists():
        for line in events_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            ev = json.loads(line)
            fid = ev.get("finding_id")
            if fid:
                events_by_finding.setdefault(fid, set()).add(str(ev.get("event_type")))

    updates: list[tuple[str, VerifierStatus, bool]] = []
    for f in findings:
        if not f.admitted_chunk_id or not f.verbatim_quote:
            continue
        chunk = find_chunk_by_id(args.project_dir, f.admitted_chunk_id)
        if chunk is None:
            continue
        res = check_quote_supported(f, chunk.text)
        new_quote_ok = res.verified
        if new_quote_ok:
            quote_ok_now += 1
        else:
            quote_fail_now += 1

        ev_types = events_by_finding.get(f.id, set())
        url_was_ok = "TIER0_URL_OK" in ev_types
        ledger_was_ok = "TIER0_LEDGER_CONFLICT" not in ev_types  # absence = OK
        tier1_was_ok = (
            True if "TIER1_ENTAILED" in ev_types
            else False if "TIER1_CONTRADICTED" in ev_types
            else None
        )
        tier2_was_ok = (
            True if "TIER2_AGREE" in ev_types
            else False if "TIER2_DISAGREE" in ev_types
            else None
        )

        # Only count URL/ledger as ACTIVE signals if they actually fired.
        # We treat them as having fired iff there is a corresponding event.
        # (Ledger fires only on conflict, so absence isn't a positive signal.)
        active_url = url_was_ok or ("TIER0_URL_FAIL" in ev_types)
        active_ledger = "TIER0_LEDGER_CONFLICT" in ev_types

        signals: list[bool] = []
        if active_url:
            signals.append(url_was_ok)
        if active_ledger:
            signals.append(ledger_was_ok)
        signals.append(new_quote_ok)
        if tier1_was_ok is not None:
            signals.append(tier1_was_ok)
        if tier2_was_ok is not None:
            signals.append(tier2_was_ok)

        if not signals:
            new_status = VerifierStatus.PENDING
        elif all(signals):
            new_status = VerifierStatus.VERIFIED
        elif not any(signals):
            new_status = VerifierStatus.FAILED
        else:
            new_status = VerifierStatus.FLAGGED

        if new_status != f.verifier_status:
            updates.append((f.id, new_status, new_quote_ok))
            changed += 1

    print(f"checked {len(findings)} findings; quote-OK now: {quote_ok_now}, quote-FAIL now: {quote_fail_now}")
    print(f"verifier_status changes: {changed}")

    if args.dry_run or changed == 0:
        return 0

    upd_map: dict[str, str] = {fid: status.value for fid, status, _ in updates}

    def mutate(lines: list[str]) -> list[str]:
        out: list[str] = []
        for line in lines:
            data = json.loads(line)
            new_s = upd_map.get(data.get("id"))
            if new_s is not None:
                data["verifier_status"] = new_s
            out.append(json.dumps(data))
        return out

    atomic_update_jsonl(findings_path(args.project_dir), mutate)

    # Append TIER0_QUOTE_OK events for the corrected rows (append-only ledger).
    for fid, _new_status, quote_ok in updates:
        if quote_ok:
            emit(
                args.project_dir,
                Event(
                    event_type=EventType.TIER0_QUOTE_OK,
                    step="verify",
                    finding_id=fid,
                    payload={"source": "rescore_quotes"},
                ),
            )

    print(f"updated {changed} findings; appended {sum(1 for _, _, ok in updates if ok)} new TIER0_QUOTE_OK events at {_now_iso()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
