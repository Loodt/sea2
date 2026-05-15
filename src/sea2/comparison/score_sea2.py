"""Score a SEA2 project against the 12 pre-registered metrics.

Reads the SEA2 store directly. Produces `ComparisonScores`. M6/M11/M12
are operator-supplied; this scorer leaves them None and the operator
fills them post-blinded-reading.

Usage::

    python -m sea2.comparison.score_sea2 <project_dir> [--output scores.json]
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import statistics
import sys
from pathlib import Path
from typing import Any

from sea2.comparison.protocol import ComparisonScores
from sea2.models import EpistemicTag
from sea2.spans import read_spans
from sea2.store import (
    chunks_path,
    read_events,
    read_findings,
    read_state,
)


def _now_iso() -> str:
    return _dt.datetime.now(_dt.UTC).isoformat()


def _load_keywords(keywords_path: Path | None) -> dict[str, list[str]]:
    if keywords_path is None:
        keywords_path = Path(__file__).resolve().parents[3] / "docs" / "comparison-domain-keywords.json"
    if not keywords_path.exists():
        return {}
    raw = json.loads(keywords_path.read_text(encoding="utf-8"))
    return {
        st["id"]: [k.lower() for k in st["keywords"]]
        for st in raw.get("subtopics", [])
    }


def _classify_subtopic(domain: str, keywords: dict[str, list[str]]) -> str | None:
    d = domain.lower()
    for st_id, kws in keywords.items():
        for kw in kws:
            if kw in d:
                return st_id
    return None


def score_sea2(  # noqa: PLR0915 — linear scorer; splitting reduces readability
    project_dir: Path | str,
    *,
    keywords_path: Path | None = None,
) -> ComparisonScores:
    """Compute M1..M10 from the SEA2 store. M6/M11/M12 left None."""
    project_dir = Path(project_dir)
    scores = ComparisonScores(
        system="sea2",
        project_dir=str(project_dir),
        scored_at=_now_iso(),
    )

    findings = read_findings(project_dir)
    events = read_events(project_dir)
    spans = read_spans(project_dir)
    state = read_state(project_dir)

    scores.findings_total = len(findings)
    scores.findings_verified = sum(
        1 for f in findings if f.verifier_status.value == "verified"
    )
    if chunks_path(project_dir).exists():
        with chunks_path(project_dir).open("r", encoding="utf-8") as fh:
            scores.chunks_total = sum(1 for line in fh if line.strip())

    # ── M1 Citation resolvability ─────────────────────────────────────────
    url_sources = [
        f for f in findings
        if f.tag is EpistemicTag.SOURCE
        and f.source is not None
        and (f.source.id.startswith("url:") or f.source.id.startswith(("http://", "https://")))
    ]
    if url_sources:
        ok = sum(
            1 for e in events
            if e.get("event_type") == "TIER0_URL_OK"
            and any(e.get("finding_id") == f.id for f in url_sources)
        )
        scores.m1_citation_resolvability = ok / len(url_sources)
        scores.m1_denominator = len(url_sources)

    # ── M2 Quote-supported rate ───────────────────────────────────────────
    quoted = [f for f in findings if f.verbatim_quote]
    if quoted:
        ok = sum(
            1 for e in events
            if e.get("event_type") == "TIER0_QUOTE_OK"
            and any(e.get("finding_id") == f.id for f in quoted)
        )
        scores.m2_quote_supported_rate = ok / len(quoted)
        scores.m2_denominator = len(quoted)

    # ── M3 Verifier disagreement rate (Tier 2) ────────────────────────────
    tier2_events = [
        e for e in events
        if e.get("event_type") in ("TIER2_AGREE", "TIER2_DISAGREE")
    ]
    if tier2_events:
        disagreements = sum(1 for e in tier2_events if e.get("event_type") == "TIER2_DISAGREE")
        scores.m3_verifier_disagreement_rate = disagreements / len(tier2_events)
        scores.m3_denominator = len(tier2_events)

    # ── M4 DAG orphan rate ────────────────────────────────────────────────
    # SEA2 rejects orphans at integrate, so the rate is ~0 by construction.
    # We count VALIDATE_FAIL events with dag-orphan in their error.
    dag_events = [
        e for e in events
        if e.get("event_type") == "VALIDATE_FAIL"
        and "dag-orphan" in str(e.get("error", ""))
    ]
    derived_findings = [f for f in findings if f.tag is EpistemicTag.DERIVED]
    denom = len(derived_findings) + len(dag_events)
    if denom > 0:
        scores.m4_dag_orphan_rate = len(dag_events) / denom
        scores.m4_denominator = denom

    # ── M5 Domain coverage ────────────────────────────────────────────────
    keywords = _load_keywords(keywords_path)
    verified_by_subtopic: dict[str, int] = {}
    for f in findings:
        if f.verifier_status.value != "verified":
            continue
        st = _classify_subtopic(f.domain, keywords)
        if st is None:
            continue
        verified_by_subtopic[st] = verified_by_subtopic.get(st, 0) + 1
    covered = sum(1 for n in verified_by_subtopic.values() if n >= 3)  # noqa: PLR2004
    scores.m5_subtopics_covered = covered
    scores.m5_subtopics_total = max(11, len(keywords) or 11)
    scores.m5_domain_coverage_rate = covered / scores.m5_subtopics_total

    # ── M7 Iterations to convergence ─────────────────────────────────────
    if state is not None:
        scores.m7_iterations_to_convergence = state.conductor_iteration
        scores.m7_stop_reason = state.completion_reason or state.status

    # ── M8 Token cost per verified finding ───────────────────────────────
    total_tokens = sum(s.prompt_tokens_est + s.output_tokens_est for s in spans)
    scores.m8_total_tokens = total_tokens
    scores.m8_verified_count = scores.findings_verified
    if scores.findings_verified > 0 and total_tokens > 0:
        scores.m8_token_cost_per_verified = total_tokens / scores.findings_verified

    # ── M9 Median wall-clock per iteration ───────────────────────────────
    extract_spans = [s for s in spans if s.step in ("extract", "subprocess")]
    if extract_spans:
        scores.m9_median_iteration_wallclock_ms = statistics.median(
            s.duration_ms for s in extract_spans
        )

    # ── M10 Silent-failure event count ───────────────────────────────────
    silent_failure_types = {
        "STORE_APPEND_FAIL",
        "PRODUCE_FAIL",
    }
    scores.m10_silent_failure_count = sum(
        1 for e in events if e.get("event_type") in silent_failure_types
    )

    return scores


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Score a SEA2 project against the 12 pre-registered metrics")
    parser.add_argument("project_dir", type=Path)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--keywords", type=Path, default=None,
                        help="Path to comparison-domain-keywords.json (default: docs/...)")
    args = parser.parse_args(argv)

    scores = score_sea2(args.project_dir, keywords_path=args.keywords)
    out: dict[str, Any] = json.loads(scores.model_dump_json())
    text = json.dumps(out, indent=2)
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
