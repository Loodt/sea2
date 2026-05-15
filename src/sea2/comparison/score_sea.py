"""Score a SEA project (TypeScript-shape) against the same 12 metrics.

SEA layout (from `C:\\Users\\mtlb\\code\\sea\\projects\\<name>/`):
  - state.json                            — ProjectState (TS shape)
  - knowledge/findings.jsonl              — Finding (TS shape: camelCase)
  - knowledge/questions.jsonl
  - metrics/spans.jsonl                   — Span (TS shape, camelCase)
  - metrics/conductor-metrics.jsonl       — ConductorMetric

SEA emits no `events.jsonl` or `chunks.jsonl`. M2 (quote-supported), M3
(Tier 2 disagreement), M11/M12 are N/A for SEA — they fall back to None
or to defaulted "no positive evidence" rates per pre-registration §M2.
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
from sea2.comparison.score_sea2 import _classify_subtopic, _load_keywords


def _now_iso() -> str:
    return _dt.datetime.now(_dt.UTC).isoformat()


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def score_sea(  # noqa: PLR0915 — linear scorer; splitting reduces readability
    project_dir: Path | str,
    *,
    keywords_path: Path | None = None,
) -> ComparisonScores:
    """Score a SEA project against the same 12 metrics.

    M1 is left as `denominator only` for now (re-scoring SEA citations
    through SEA2's Tier 0 URL checker is Phase 4 work — the SEA store
    has no equivalent of TIER0_URL_OK events).
    """
    project_dir = Path(project_dir)
    scores = ComparisonScores(
        system="sea",
        project_dir=str(project_dir),
        scored_at=_now_iso(),
    )

    findings = _read_jsonl(project_dir / "knowledge" / "findings.jsonl")
    spans = _read_jsonl(project_dir / "metrics" / "spans.jsonl")
    state_path = project_dir / "state.json"
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else None

    scores.findings_total = len(findings)
    scores.findings_verified = sum(
        1 for f in findings if f.get("status") == "verified"
    )

    # ── M1 Citation resolvability ─────────────────────────────────────────
    # SEA has no Tier 0 URL events. M1 is left None unless a resolver is
    # supplied; the pre-registration's plan is to re-score offline.
    url_sources = [
        f for f in findings
        if f.get("tag") == "SOURCE"
        and isinstance(f.get("source"), str)
        and (f["source"].startswith(("url:", "http://", "https://")))
    ]
    scores.m1_denominator = len(url_sources)
    scores.notes.append(f"M1 denominator: {len(url_sources)} URL-sourced findings (resolver not yet wired for SEA)")

    # ── M2 Quote-supported rate ───────────────────────────────────────────
    # SEA does not produce verbatim_quote; rate is N/A.
    scores.m2_denominator = 0
    scores.notes.append("M2 N/A for SEA — no verbatim_quote in TS schema")

    # ── M3 Verifier disagreement rate ─────────────────────────────────────
    # SEA has no Tier 2; would need post-hoc audit run.
    scores.notes.append("M3 N/A for SEA — Tier 2 audit not run against SEA findings")

    # ── M4 DAG orphan rate ────────────────────────────────────────────────
    by_id = {f.get("id"): f for f in findings}
    derived = [f for f in findings if f.get("tag") == "DERIVED"]
    orphans = 0
    for f in derived:
        chain = f.get("derivationChain") or {}
        premises = chain.get("premises", []) or []
        if not premises:
            continue
        if all(p not in by_id for p in premises):
            orphans += 1
    if derived:
        scores.m4_dag_orphan_rate = orphans / len(derived)
        scores.m4_denominator = len(derived)

    # ── M5 Domain coverage ────────────────────────────────────────────────
    keywords = _load_keywords(keywords_path)
    verified_by_subtopic: dict[str, int] = {}
    for f in findings:
        if f.get("status") != "verified":
            continue
        domain = str(f.get("domain", ""))
        st = _classify_subtopic(domain, keywords)
        if st is None:
            continue
        verified_by_subtopic[st] = verified_by_subtopic.get(st, 0) + 1
    covered = sum(1 for n in verified_by_subtopic.values() if n >= 3)  # noqa: PLR2004
    scores.m5_subtopics_covered = covered
    scores.m5_subtopics_total = max(11, len(keywords) or 11)
    scores.m5_domain_coverage_rate = covered / scores.m5_subtopics_total

    # ── M7 Iterations to convergence ─────────────────────────────────────
    if state is not None:
        scores.m7_iterations_to_convergence = state.get("conductorIteration") or state.get("iteration")
        scores.m7_stop_reason = state.get("completionReason") or state.get("status")

    # ── M8 Token cost per verified finding ───────────────────────────────
    total_tokens = sum(
        int(s.get("promptTokensEst", 0)) + int(s.get("outputTokensEst", 0))
        for s in spans
    )
    scores.m8_total_tokens = total_tokens
    scores.m8_verified_count = scores.findings_verified
    if scores.findings_verified > 0 and total_tokens > 0:
        scores.m8_token_cost_per_verified = total_tokens / scores.findings_verified

    # ── M9 Median wall-clock per iteration ───────────────────────────────
    if spans:
        durations = [int(s.get("durationMs", 0)) for s in spans if s.get("durationMs")]
        if durations:
            scores.m9_median_iteration_wallclock_ms = statistics.median(durations)

    # ── M10 Silent-failure event count ───────────────────────────────────
    # SEA doesn't have a structured events ledger. As a proxy: count
    # conductor-metric rows where findingsAdded > 0 but findingsPersisted == 0.
    metrics_rows = _read_jsonl(project_dir / "metrics" / "conductor-metrics.jsonl")
    silent_failures = sum(
        1 for r in metrics_rows
        if int(r.get("findingsAdded", 0)) > 0
        and (r.get("findingsPersisted") is not None)
        and int(r.get("findingsPersisted", 0)) == 0
    )
    scores.m10_silent_failure_count = silent_failures
    scores.notes.append(
        "M10 SEA proxy: findingsAdded>0 but findingsPersisted==0 in metrics/conductor-metrics.jsonl"
    )

    return scores


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Score a SEA project against the 12 pre-registered metrics")
    parser.add_argument("project_dir", type=Path)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--keywords", type=Path, default=None)
    args = parser.parse_args(argv)

    scores = score_sea(args.project_dir, keywords_path=args.keywords)
    text = json.dumps(json.loads(scores.model_dump_json()), indent=2)
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
