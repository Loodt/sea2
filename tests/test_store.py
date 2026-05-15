"""Store atomic write + summary regeneration tests."""

from __future__ import annotations

import json
import threading
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from sea2.events import Event, EventType, emit, events_path
from sea2.models import EpistemicTag, FactType, Finding, Question, Source
from sea2.store import (
    SUMMARY_MAX_BYTES,
    atomic_append_jsonl,
    atomic_update_jsonl,
    findings_path,
    questions_path,
    read_events,
    read_findings,
    read_questions,
    regenerate_summary,
    summary_path,
)


def _finding(idx: int) -> Finding:
    return Finding(
        id=f"f-{idx:03d}",
        claim=f"claim {idx}",
        tag=EpistemicTag.SOURCE,
        fact_type=FactType.QUANTITATIVE,
        source=Source(id="doi:10.1/abc"),
        confidence=0.9,
        domain="d",
        iteration=0,
    )


def test_append_then_read_roundtrip(tmp_path: Path) -> None:
    atomic_append_jsonl(findings_path(tmp_path), _finding(1))
    atomic_append_jsonl(findings_path(tmp_path), _finding(2))
    out = read_findings(tmp_path)
    assert [f.id for f in out] == ["f-001", "f-002"]


def test_corrupt_line_raises_loudly(tmp_path: Path) -> None:
    p = findings_path(tmp_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text('{"not":"a finding"}\n', encoding="utf-8")
    with pytest.raises(ValueError, match="failed to parse"):
        read_findings(tmp_path)


def test_atomic_update_replaces_file(tmp_path: Path) -> None:
    for i in range(3):
        atomic_append_jsonl(findings_path(tmp_path), _finding(i))

    def drop_first(lines: list[str]) -> list[str]:
        return lines[1:]

    atomic_update_jsonl(findings_path(tmp_path), drop_first)
    assert [f.id for f in read_findings(tmp_path)] == ["f-001", "f-002"]


def test_concurrent_appends_under_lock(tmp_path: Path) -> None:
    n = 20

    def worker(i: int) -> None:
        atomic_append_jsonl(findings_path(tmp_path), _finding(i))

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    out = read_findings(tmp_path)
    assert len(out) == n
    assert len({f.id for f in out}) == n


def test_summary_regen_deterministic(tmp_path: Path) -> None:
    for i in range(3):
        atomic_append_jsonl(findings_path(tmp_path), _finding(i))
    body = regenerate_summary(tmp_path)
    assert summary_path(tmp_path).read_text(encoding="utf-8") == body
    assert "3 findings" in body
    # Idempotent — re-running on unchanged store produces identical bytes.
    assert regenerate_summary(tmp_path) == body


def test_summary_size_capped(tmp_path: Path) -> None:
    for i in range(500):
        atomic_append_jsonl(findings_path(tmp_path), _finding(i))
    body = regenerate_summary(tmp_path)
    assert len(body.encode("utf-8")) <= SUMMARY_MAX_BYTES


def test_event_emit_appends_jsonl(tmp_path: Path) -> None:
    emit(
        tmp_path,
        Event(
            event_type=EventType.STORE_APPEND_OK,
            step="integrate",
            finding_id="f-001",
        ),
    )
    raw = events_path(tmp_path).read_text(encoding="utf-8").strip()
    parsed = json.loads(raw)
    assert parsed["event_type"] == "STORE_APPEND_OK"
    events = read_events(tmp_path)
    assert len(events) == 1


def test_questions_roundtrip(tmp_path: Path) -> None:
    q = Question(
        id="q-001",
        question="?",
        priority="high",
        context="c",
        domain="d",
        iteration=0,
    )
    atomic_append_jsonl(questions_path(tmp_path), q)
    out = read_questions(tmp_path)
    assert out == [q]
