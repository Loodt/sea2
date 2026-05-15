"""Combine SEA + SEA2 scores into a single comparison report.

Reads two `ComparisonScores` JSON blobs (from `score_sea2.py` and
`score_sea.py`) and produces a markdown table with per-metric verdicts
per the pre-registration's win-margins.

Optional input: `sea-m1-retrofit.json` (from `retrofit_sea_m1.py`)
overrides SEA's M1 number with a real HTTP-resolved value.

Usage::

    python scripts/build_comparison_report.py \
        --sea2 sea2-scores.json \
        --sea sea-scores.json \
        --sea-m1-retrofit comparison-blind/sea-m1-retrofit.json \
        --output comparison-blind/scorecard.md
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

DECISION_THRESHOLD = 7  # pre-registration §3 — need 7 of 12 wins


@dataclass(frozen=True)
class MetricRow:
    label: str
    sea_value: float | None
    sea2_value: float | None
    higher_is_better: bool
    win_margin: float  # absolute pp for ratios, or relative fraction for counts
    is_relative_margin: bool = False


def _fmt(v: float | None, *, pct: bool = False, decimals: int = 3) -> str:
    if v is None:
        return "N/A"
    if pct:
        return f"{v * 100:.1f}%"
    return f"{v:.{decimals}f}"


def _verdict(row: MetricRow) -> str:
    a, b = row.sea_value, row.sea2_value
    if a is None and b is None:
        return "—"
    if a is None:
        return "SEA2 (SEA N/A)"
    if b is None:
        return "SEA (SEA2 N/A)"

    if row.higher_is_better:
        diff = b - a
        wins_if_pos = "SEA2"
        wins_if_neg = "SEA"
    else:
        diff = a - b
        wins_if_pos = "SEA2"
        wins_if_neg = "SEA"

    if row.is_relative_margin:
        # Use relative-to-loser margin
        base = max(abs(a), abs(b), 1e-9)
        threshold = base * row.win_margin
    else:
        threshold = row.win_margin

    if abs(diff) < threshold:
        return "TIE (within margin)"
    return wins_if_pos if diff > 0 else wins_if_neg


def main(argv: list[str] | None = None) -> int:  # noqa: PLR0915
    parser = argparse.ArgumentParser(description="Build the SEA vs SEA2 comparison scorecard")
    parser.add_argument("--sea2", type=Path, required=True)
    parser.add_argument("--sea", type=Path, required=True)
    parser.add_argument("--sea-m1-retrofit", type=Path, default=None)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)

    sea = json.loads(args.sea.read_text(encoding="utf-8"))
    sea2 = json.loads(args.sea2.read_text(encoding="utf-8"))

    if args.sea_m1_retrofit and args.sea_m1_retrofit.exists():
        retrofit = json.loads(args.sea_m1_retrofit.read_text(encoding="utf-8"))
        sea["m1_citation_resolvability"] = retrofit.get("m1_citation_resolvability")
        sea["m1_denominator"] = retrofit.get("m1_denominator", sea.get("m1_denominator", 0))

    rows: list[MetricRow] = [
        MetricRow("M1 Citation resolvability",
                  sea["m1_citation_resolvability"], sea2["m1_citation_resolvability"],
                  higher_is_better=True, win_margin=0.10),
        MetricRow("M2 Quote-supported rate",
                  sea["m2_quote_supported_rate"], sea2["m2_quote_supported_rate"],
                  higher_is_better=True, win_margin=0.10),
        MetricRow("M3 Verifier disagreement rate",
                  sea["m3_verifier_disagreement_rate"], sea2["m3_verifier_disagreement_rate"],
                  higher_is_better=False, win_margin=0.05),
        MetricRow("M4 DAG orphan rate",
                  sea["m4_dag_orphan_rate"], sea2["m4_dag_orphan_rate"],
                  higher_is_better=False, win_margin=0.001),  # any diff
        MetricRow("M5 Domain coverage",
                  sea["m5_domain_coverage_rate"], sea2["m5_domain_coverage_rate"],
                  higher_is_better=True, win_margin=2 / 11),  # ≥2 sub-topics
        MetricRow("M6 Operator accuracy",
                  sea["m6_operator_accuracy"], sea2["m6_operator_accuracy"],
                  higher_is_better=True, win_margin=0.08),
        MetricRow("M7 Iterations to convergence",
                  sea["m7_iterations_to_convergence"], sea2["m7_iterations_to_convergence"],
                  higher_is_better=False, win_margin=0.10, is_relative_margin=True),
        MetricRow("M8 Token cost per verified",
                  sea["m8_token_cost_per_verified"], sea2["m8_token_cost_per_verified"],
                  higher_is_better=False, win_margin=0.20, is_relative_margin=True),
        MetricRow("M9 Wall-clock per iteration (ms)",
                  sea["m9_median_iteration_wallclock_ms"], sea2["m9_median_iteration_wallclock_ms"],
                  higher_is_better=False, win_margin=0.20, is_relative_margin=True),
        MetricRow("M10 Silent-failure event count",
                  sea["m10_silent_failure_count"], sea2["m10_silent_failure_count"],
                  higher_is_better=False, win_margin=1.0),
        MetricRow("M11 Operator confidence",
                  sea["m11_operator_confidence"], sea2["m11_operator_confidence"],
                  higher_is_better=True, win_margin=2.0),
        MetricRow("M12 Flagged-for-followup",
                  sea["m12_flagged_for_followup"], sea2["m12_flagged_for_followup"],
                  higher_is_better=False, win_margin=0.25, is_relative_margin=True),
    ]

    lines: list[str] = []
    lines.append("# SEA vs SEA2 — au-token Comparison Scorecard")
    lines.append("")
    lines.append(f"SEA scored at:  `{sea['scored_at']}` ({sea['project_dir']})")
    lines.append(f"SEA2 scored at: `{sea2['scored_at']}` ({sea2['project_dir']})")
    lines.append("")
    lines.append("## Headline numbers")
    lines.append("")
    lines.append(f"- SEA findings: {sea['findings_total']} total, {sea['findings_verified']} verified")
    lines.append(f"- SEA2 findings: {sea2['findings_total']} total, {sea2['findings_verified']} verified")
    lines.append("")
    lines.append("## Per-metric scorecard")
    lines.append("")
    lines.append("| Metric | SEA | SEA2 | Verdict |")
    lines.append("|---|---|---|---|")

    sea2_wins = 0
    sea_wins = 0
    ties = 0
    pct_metrics = {"M1", "M2", "M3", "M4", "M5"}
    for row in rows:
        sea_str = _fmt(row.sea_value, pct=any(p in row.label for p in pct_metrics))
        sea2_str = _fmt(row.sea2_value, pct=any(p in row.label for p in pct_metrics))
        v = _verdict(row)
        # "SEA2" or "SEA2 (SEA N/A)" → SEA2 wins
        # "SEA" or "SEA (SEA2 N/A)" → SEA wins
        # "TIE …", "—", "N/A" → tie/unscored
        if v.startswith("SEA2"):
            sea2_wins += 1
        elif v.startswith("SEA"):
            sea_wins += 1
        else:
            ties += 1
        lines.append(f"| {row.label} | {sea_str} | {sea2_str} | {v} |")

    lines.append("")
    lines.append("## Decision rule check")
    lines.append("")
    lines.append(f"- SEA2 wins: **{sea2_wins} of 12**")
    lines.append(f"- SEA wins:  **{sea_wins} of 12**")
    lines.append(f"- Ties:      **{ties} of 12**")
    lines.append("")
    m11_known = sea["m11_operator_confidence"] is not None and sea2["m11_operator_confidence"] is not None
    if sea2_wins >= DECISION_THRESHOLD and m11_known:
        lines.append("**Decision rule (preliminary):** SEA2 wins >=7 of 12 — pending M11 confirmation.")
    elif sea_wins >= DECISION_THRESHOLD and m11_known:
        lines.append("**Decision rule (preliminary):** SEA wins >=7 of 12.")
    else:
        lines.append("**Decision rule:** No outcome yet. M11 + M12 are operator-supplied; run `scripts/blind_compare.py` next.")

    lines.append("")
    lines.append("## Notes from scorers")
    lines.append("")
    for note in sea.get("notes", []):
        lines.append(f"- [SEA] {note}")
    for note in sea2.get("notes", []):
        lines.append(f"- [SEA2] {note}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote scorecard to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
