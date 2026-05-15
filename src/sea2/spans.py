"""Span records: one row per LLM call.

Article §10 observability primitive — every subprocess call is wrapped in a
span recording start/end timestamps, prompt + output sizes (chars and
estimated tokens at chars/4), and the exit code. Spans land in
`spans.jsonl` alongside `events.jsonl` and `findings.jsonl`.

M8 (token cost per verified finding) and M9 (wall-clock per iteration)
in the comparison protocol read directly from this file.
"""

from __future__ import annotations

import datetime as _dt
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from sea2.store import atomic_append_jsonl

CHARS_PER_TOKEN_EST = 4


def spans_path(project_dir: Path | str) -> Path:
    return Path(project_dir) / "spans.jsonl"


class Span(BaseModel):
    """One LLM call / one subprocess invocation."""

    model_config = ConfigDict(extra="forbid")

    span_id: str
    step: str
    parent_id: str | None = None
    start_ts: str
    end_ts: str
    duration_ms: int
    prompt_chars: int = Field(ge=0)
    output_chars: int = Field(ge=0)
    prompt_tokens_est: int = Field(ge=0)
    output_tokens_est: int = Field(ge=0)
    exit_code: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


def _now() -> _dt.datetime:
    return _dt.datetime.now(_dt.UTC)


def _est_tokens(chars: int) -> int:
    return chars // CHARS_PER_TOKEN_EST


@dataclass
class _SpanInProgress:
    span_id: str
    step: str
    start: _dt.datetime
    prompt_chars: int
    parent_id: str | None
    metadata: dict[str, Any]


def start_span(
    step: str,
    *,
    prompt_chars: int,
    parent_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> _SpanInProgress:
    return _SpanInProgress(
        span_id=uuid.uuid4().hex[:16],
        step=step,
        start=_now(),
        prompt_chars=prompt_chars,
        parent_id=parent_id,
        metadata=metadata or {},
    )


def finish_span(
    project_dir: Path | str,
    in_progress: _SpanInProgress,
    *,
    output_chars: int,
    exit_code: int = 0,
) -> Span:
    end = _now()
    duration_ms = int((end - in_progress.start).total_seconds() * 1000)
    span = Span(
        span_id=in_progress.span_id,
        step=in_progress.step,
        parent_id=in_progress.parent_id,
        start_ts=in_progress.start.isoformat(),
        end_ts=end.isoformat(),
        duration_ms=duration_ms,
        prompt_chars=in_progress.prompt_chars,
        output_chars=output_chars,
        prompt_tokens_est=_est_tokens(in_progress.prompt_chars),
        output_tokens_est=_est_tokens(output_chars),
        exit_code=exit_code,
        metadata=in_progress.metadata,
    )
    atomic_append_jsonl(spans_path(project_dir), span)
    return span


def read_spans(project_dir: Path | str) -> list[Span]:
    """Typed read of spans.jsonl."""
    path = spans_path(project_dir)
    if not path.exists():
        return []
    spans: list[Span] = []
    with path.open("r", encoding="utf-8") as fh:
        for raw in fh:
            stripped = raw.strip()
            if stripped:
                spans.append(Span.model_validate_json(stripped))
    return spans


SpanRecorder = Callable[[str, int, int, int], None]
"""Lightweight recorder used inside `default_runner`. Signature:
(step, prompt_chars, output_chars, exit_code) -> None.

The default runner doesn't have a project_dir; the conductor wires the
recorder when it owns the call site. Tests inject a no-op recorder.
"""


def project_recorder(project_dir: Path | str) -> SpanRecorder:
    """Return a SpanRecorder that writes to `project_dir/spans.jsonl`."""

    def record(step: str, prompt_chars: int, output_chars: int, exit_code: int) -> None:
        in_progress = start_span(step, prompt_chars=prompt_chars)
        # Record duration as 0 since the caller already finished — we backfill
        # the "duration" via in_progress.start by hand if a richer caller wants
        # it. Phase 2 callers stamp at-end only.
        finish_span(
            project_dir, in_progress,
            output_chars=output_chars, exit_code=exit_code,
        )

    return record


__all__ = [
    "CHARS_PER_TOKEN_EST",
    "Span",
    "SpanRecorder",
    "finish_span",
    "project_recorder",
    "read_spans",
    "spans_path",
    "start_span",
]
