"""Span recording tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sea2.spans import (
    CHARS_PER_TOKEN_EST,
    finish_span,
    project_recorder,
    read_spans,
    start_span,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_span_roundtrip(tmp_path: Path) -> None:
    in_progress = start_span("extract", prompt_chars=1200)
    finish_span(tmp_path, in_progress, output_chars=400, exit_code=0)
    spans = read_spans(tmp_path)
    assert len(spans) == 1
    s = spans[0]
    assert s.step == "extract"
    assert s.prompt_chars == 1200
    assert s.output_chars == 400
    assert s.prompt_tokens_est == 1200 // CHARS_PER_TOKEN_EST
    assert s.output_tokens_est == 400 // CHARS_PER_TOKEN_EST


def test_project_recorder_writes_span(tmp_path: Path) -> None:
    record = project_recorder(tmp_path)
    record("retrieve", 800, 200, 0)
    spans = read_spans(tmp_path)
    assert len(spans) == 1
    assert spans[0].step == "retrieve"
    assert spans[0].output_chars == 200


def test_read_spans_empty(tmp_path: Path) -> None:
    assert read_spans(tmp_path) == []


def test_multiple_spans_append(tmp_path: Path) -> None:
    record = project_recorder(tmp_path)
    for i in range(3):
        record(f"step-{i}", 100 * (i + 1), 50 * (i + 1), 0)
    spans = read_spans(tmp_path)
    assert len(spans) == 3
    assert [s.step for s in spans] == ["step-0", "step-1", "step-2"]
