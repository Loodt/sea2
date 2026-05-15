"""Lineage tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sea2.lineage import append_lineage_entry, lineage_path
from sea2.store import atomic_append_jsonl  # noqa: F401  (sanity import)

if TYPE_CHECKING:
    from pathlib import Path


def test_append_writes_jsonl(tmp_path: Path) -> None:
    entry = append_lineage_entry(
        tmp_path,
        iteration=1,
        target="persona.md",
        version_before="v001",
        version_after="v002",
        change_type="behavioral",
        change_summary="tighten extraction prompt",
        reasoning="reduces false-positive admissions",
        score_before=0.72,
        score_after=0.78,
    )
    assert entry.score_before == 0.72
    assert entry.score_after == 0.78
    raw = lineage_path(tmp_path).read_text(encoding="utf-8").strip()
    assert "0.78" in raw
    assert "persona.md" in raw


def test_scores_must_be_supplied(tmp_path: Path) -> None:
    # Both score params are keyword-only with no default — the signature is
    # the enforcement mechanism for infra-debt #5.
    try:
        append_lineage_entry(  # type: ignore[call-arg]
            tmp_path,
            iteration=1,
            target="persona.md",
            version_before="v001",
            version_after="v002",
            change_type="x",
            change_summary="x",
            reasoning="x",
        )
    except TypeError as e:
        assert "score_before" in str(e) or "score_after" in str(e)
    else:
        raise AssertionError("expected TypeError for missing score args")
