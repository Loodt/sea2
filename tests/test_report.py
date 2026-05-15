"""Report exporter + sampler tests."""

from __future__ import annotations

import csv
from typing import TYPE_CHECKING

from sea2.comparison.report import export_summary, sample_findings
from sea2.models import EpistemicTag, FactType, Finding, Question, Source, VerifierStatus
from sea2.store import atomic_append_jsonl, findings_path, questions_path

if TYPE_CHECKING:
    from pathlib import Path


def _f(idx: int, *, domain: str = "fsca", verified: bool = True) -> Finding:
    return Finding(
        id=f"f-{idx:03d}",
        claim=f"Claim {idx} about {domain}.",
        tag=EpistemicTag.SOURCE,
        fact_type=FactType.QUALITATIVE,
        source=Source(id=f"url:https://example.com/{idx}"),
        verbatim_quote=f"verbatim quote for f-{idx:03d}",
        confidence=0.7 + (idx % 3) * 0.1,
        domain=domain,
        iteration=1,
        verifier_status=VerifierStatus.VERIFIED if verified else VerifierStatus.FLAGGED,
    )


def _populate(tmp_path: Path) -> None:
    for i in range(8):
        d = "fsca" if i < 4 else "mprda"
        atomic_append_jsonl(findings_path(tmp_path), _f(i, domain=d))
    for i in range(3):
        atomic_append_jsonl(
            questions_path(tmp_path),
            Question(
                id=f"q-{i}",
                question="?",
                priority="medium",
                context="c",
                domain="d",
                iteration=0,
                status="open" if i == 0 else "resolved",
            ),
        )


def test_export_summary_writes_expected_sections(tmp_path: Path) -> None:
    _populate(tmp_path)
    out = tmp_path / "summary.md"
    export_summary(tmp_path, out)
    body = out.read_text(encoding="utf-8")
    assert "# Research Summary" in body
    assert "## Executive Summary" in body
    assert "8 findings" in body
    assert "## Verified Findings by Domain" in body
    assert "fsca" in body
    assert "mprda" in body
    assert "## Open Questions" in body


def test_export_summary_handles_empty(tmp_path: Path) -> None:
    out = tmp_path / "summary.md"
    export_summary(tmp_path, out)
    body = out.read_text(encoding="utf-8")
    assert "_No verified findings._" in body


def test_sample_findings_returns_csv_with_correct_count(tmp_path: Path) -> None:
    _populate(tmp_path)
    out = tmp_path / "sample.csv"
    sample_findings(tmp_path, out, n=4, seed=17)
    with out.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.reader(fh))
    # Header + 4 data rows
    assert len(rows) == 1 + 4
    assert rows[0][0] == "system"
    # System column is blank (unmasked later)
    for r in rows[1:]:
        assert r[0] == ""


def test_sample_findings_deterministic_with_seed(tmp_path: Path) -> None:
    _populate(tmp_path)
    out1 = tmp_path / "s1.csv"
    out2 = tmp_path / "s2.csv"
    sample_findings(tmp_path, out1, n=4, seed=42)
    sample_findings(tmp_path, out2, n=4, seed=42)
    assert out1.read_text() == out2.read_text()


def test_sample_findings_n_exceeds_total(tmp_path: Path) -> None:
    _populate(tmp_path)
    out = tmp_path / "all.csv"
    sample_findings(tmp_path, out, n=100, seed=17)
    with out.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.reader(fh))
    assert len(rows) == 1 + 8


def test_sample_findings_empty_project(tmp_path: Path) -> None:
    out = tmp_path / "empty.csv"
    result_path = sample_findings(tmp_path, out, n=10, seed=17)
    assert result_path.exists()
    assert result_path.read_text() == ""
