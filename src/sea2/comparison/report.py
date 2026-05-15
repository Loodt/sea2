"""Report exporter + M6 random sampler.

Two functions for the comparison-protocol post-run workflow:

  - `export_summary(project_dir, output_path)` — write a single markdown
    summary fairly comparable to SEA's `output/integrated-strategy.md`
    so M11 (operator confidence) reading is meaningful.
  - `sample_findings(project_dir, *, n, seed)` — stratified random sample
    of findings for M6 (operator-labelled accuracy). Writes CSV with the
    `system` column hidden (filled when both systems are exported).
"""

from __future__ import annotations

import csv
import datetime as _dt
import random
from pathlib import Path
from typing import TYPE_CHECKING

from sea2.store import read_findings, read_questions

if TYPE_CHECKING:
    from sea2.models import Finding


_TOP_VERIFIED_PER_DOMAIN = 5
_M6_DEFAULT_N = 50
_M6_DEFAULT_SEED = 17


def _now_iso() -> str:
    return _dt.datetime.now(_dt.UTC).isoformat()


def export_summary(  # noqa: PLR0915 — linear report builder
    project_dir: Path | str,
    output_path: Path | str,
) -> Path:
    """Write a deterministic markdown summary of the project.

    The format mirrors SEA's `integrated-strategy.md` shape so M11
    blinding is fair: heading, executive summary, per-domain verified
    findings, open questions list, methodology footer.
    """
    project_dir = Path(project_dir)
    output_path = Path(output_path)
    findings = read_findings(project_dir)
    questions = read_questions(project_dir)

    verified = [f for f in findings if f.verifier_status.value == "verified"]
    flagged = [f for f in findings if f.verifier_status.value == "flagged"]
    open_qs = [q for q in questions if q.status == "open"]
    resolved_qs = [q for q in questions if q.status == "resolved"]
    exhausted_qs = [q for q in questions if q.status == "exhausted"]

    by_domain: dict[str, list[Finding]] = {}
    for f in verified:
        by_domain.setdefault(f.domain, []).append(f)

    lines: list[str] = []
    lines.append("# Research Summary")
    lines.append("")
    lines.append(f"*Generated {_now_iso()}*")
    lines.append("")
    lines.append("## Executive Summary")
    lines.append("")
    lines.append(
        f"This report aggregates {len(findings)} findings across "
        f"{len(questions)} research questions. "
        f"{len(verified)} findings are verified, {len(flagged)} flagged "
        f"for follow-up. {len(resolved_qs)} questions resolved, "
        f"{len(open_qs)} still open, {len(exhausted_qs)} exhausted."
    )
    lines.append("")

    lines.append("## Verified Findings by Domain")
    lines.append("")
    if not by_domain:
        lines.append("_No verified findings._")
    for domain in sorted(by_domain):
        items = by_domain[domain]
        lines.append(f"### {domain}")
        for f in items[:_TOP_VERIFIED_PER_DOMAIN]:
            cite = f.source.id if f.source else "(no source)"
            lines.append(f"- **{f.id}** [{f.tag.value}, conf={f.confidence:.2f}] {f.claim}")
            lines.append(f"  - source: `{cite}`")
            if f.verbatim_quote:
                quote_oneline = " ".join(f.verbatim_quote.split())[:200]
                lines.append(f"  - quote: \"{quote_oneline}\"")
        if len(items) > _TOP_VERIFIED_PER_DOMAIN:
            extra = len(items) - _TOP_VERIFIED_PER_DOMAIN
            lines.append(f"- ... and {extra} more verified findings in `{domain}`.")
        lines.append("")

    if flagged:
        lines.append("## Flagged for Follow-up")
        lines.append("")
        for f in flagged[:20]:
            lines.append(f"- **{f.id}** [{f.tag.value}] {f.claim}")
        lines.append("")

    if open_qs:
        lines.append("## Open Questions")
        lines.append("")
        for q in open_qs[:25]:
            lines.append(f"- **{q.id}** ({q.priority}) {q.question}")
        lines.append("")

    lines.append("## Methodology Footer")
    lines.append("")
    lines.append(
        "Findings are produced by a retrieval-first extract-then-verify "
        "pipeline. Each finding references an admitted chunk in the "
        "project's chunk store. Tier 0 / Tier 1 / Tier 2 verification "
        "signals contribute to the per-finding verifier_status."
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def sample_findings(
    project_dir: Path | str,
    output_path: Path | str,
    *,
    n: int = _M6_DEFAULT_N,
    seed: int = _M6_DEFAULT_SEED,
    system_label: str = "system",
) -> Path:
    """Write a stratified random sample of findings to `output_path` (CSV).

    Stratification: sample is proportional across non-empty domains. If
    `n` exceeds the total number of findings, all findings are written.
    """
    project_dir = Path(project_dir)
    output_path = Path(output_path)
    findings = read_findings(project_dir)
    if not findings:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("", encoding="utf-8")
        return output_path

    rng = random.Random(seed)  # noqa: S311 — sampling, not cryptography
    sample: list[Finding]
    if n >= len(findings):
        sample = list(findings)
    else:
        by_domain: dict[str, list[Finding]] = {}
        for f in findings:
            by_domain.setdefault(f.domain, []).append(f)
        total = len(findings)
        sample = []
        for items in by_domain.values():
            quota = max(1, round(n * len(items) / total))
            quota = min(quota, len(items))
            sample.extend(rng.sample(items, quota))
        # Trim or top up to exactly n.
        if len(sample) > n:
            sample = rng.sample(sample, n)
        elif len(sample) < n:
            extras = [f for f in findings if f not in sample]
            sample.extend(rng.sample(extras, min(n - len(sample), len(extras))))
        rng.shuffle(sample)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow([
            system_label, "finding_id", "domain", "tag", "verifier_status",
            "confidence", "claim", "source_id", "verbatim_quote", "label",
        ])
        for f in sample:
            writer.writerow([
                "",  # system intentionally hidden — filled when blinded
                f.id, f.domain, f.tag.value, f.verifier_status.value,
                f.confidence, f.claim,
                f.source.id if f.source else "",
                f.verbatim_quote or "",
                "",  # label placeholder for operator
            ])
    return output_path


__all__ = [
    "export_summary",
    "sample_findings",
]
