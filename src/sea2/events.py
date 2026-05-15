"""Typed event ledger.

Commitment 6 (fail loudly): every catch site emits a structured event or
rethrows. Commitment 7 (one canonical counter): events are append-only; any
aggregate metric is computed on demand from the ledger, never maintained as
mutable state.

Events are persisted to `<project>/events.jsonl` via `emit()`.
"""

from __future__ import annotations

import datetime as _dt
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from sea2.store import atomic_append_jsonl


def _now_iso() -> str:
    return _dt.datetime.now(_dt.UTC).isoformat()


class EventType(StrEnum):
    PRODUCE_OK = "PRODUCE_OK"
    PRODUCE_FAIL = "PRODUCE_FAIL"
    VALIDATE_OK = "VALIDATE_OK"
    VALIDATE_FAIL = "VALIDATE_FAIL"
    STORE_APPEND_OK = "STORE_APPEND_OK"
    STORE_APPEND_FAIL = "STORE_APPEND_FAIL"
    HALT_REQUESTED = "HALT_REQUESTED"
    CAP_TRIMMED = "CAP_TRIMMED"
    SELECTION_GUARD_INTERVENED = "SELECTION_GUARD_INTERVENED"
    STORE_CLOBBER_RESTORED = "STORE_CLOBBER_RESTORED"
    TIER0_URL_OK = "TIER0_URL_OK"
    TIER0_URL_FAIL = "TIER0_URL_FAIL"
    TIER0_LEDGER_CONFLICT = "TIER0_LEDGER_CONFLICT"
    TIER0_QUOTE_OK = "TIER0_QUOTE_OK"
    TIER0_QUOTE_FAIL = "TIER0_QUOTE_FAIL"
    TIER0_DOI_OK = "TIER0_DOI_OK"
    TIER0_DOI_FAIL = "TIER0_DOI_FAIL"
    TIER0_ARXIV_OK = "TIER0_ARXIV_OK"
    TIER0_ARXIV_FAIL = "TIER0_ARXIV_FAIL"
    TIER0_PDF_PAGE_OK = "TIER0_PDF_PAGE_OK"
    TIER0_PDF_PAGE_FAIL = "TIER0_PDF_PAGE_FAIL"
    TIER1_ENTAILED = "TIER1_ENTAILED"
    TIER1_NEUTRAL = "TIER1_NEUTRAL"
    TIER1_CONTRADICTED = "TIER1_CONTRADICTED"
    TIER1_SKIPPED = "TIER1_SKIPPED"
    TIER2_AGREE = "TIER2_AGREE"
    TIER2_DISAGREE = "TIER2_DISAGREE"
    TIER2_SKIPPED = "TIER2_SKIPPED"
    TIER3_REFUTED = "TIER3_REFUTED"
    TIER3_SKIPPED = "TIER3_SKIPPED"


# Step type for the `step` field on Event (which conductor stage emitted it).
StepType = Literal[
    "select",
    "retrieve",
    "extract",
    "verify",
    "integrate",
    "summarize",
    "meta",
    "system",
]


class Event(BaseModel):
    """Append-only event record. Every catch site emits one.

    `payload` is a free-form bag for stage-specific context (URLs, finding
    IDs, error messages, cap before/after counts). Keep it serializable.
    """

    model_config = ConfigDict(extra="forbid")

    event_type: EventType
    step: StepType
    timestamp: str = Field(default_factory=_now_iso)
    iteration: int | None = None
    question_id: str | None = None
    finding_id: str | None = None
    error: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


def events_path(project_dir: Path | str) -> Path:
    return Path(project_dir) / "events.jsonl"


def emit(project_dir: Path | str, event: Event) -> None:
    """Atomically append an event to <project>/events.jsonl.

    Never raises on the happy path. If the underlying append itself fails the
    error propagates — there is no `events-failure` event to write, and a
    silent swallow would defeat commitment 6.
    """
    atomic_append_jsonl(events_path(project_dir), event)


__all__ = [
    "Event",
    "EventType",
    "StepType",
    "emit",
    "events_path",
]
