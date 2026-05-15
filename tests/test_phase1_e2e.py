"""End-to-end Phase 1 integration test.

Runs the full pipeline with `extract_noop()`: appends a fixture finding via
integrate, runs Tier 0 (URL + ledger), runs DAG validation, persists via the
store, emits the corresponding events. Read-back roundtrip confirms.

This is the Phase 1 "done" verification criterion #2 from
`.claude/plans/sea2-phase-1-foundation.md`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx

from sea2.conductor.integrate import extract_noop, integrate
from sea2.conductor.selector import select
from sea2.events import EventType
from sea2.models import (
    EpistemicTag,
    FactType,
    Finding,
    ProjectState,
    Question,
    Source,
    VerifierStatus,
)
from sea2.store import (
    atomic_append_jsonl,
    findings_path,
    questions_path,
    read_events,
    read_findings,
    read_questions,
    regenerate_summary,
    summary_path,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_end_to_end_phase1_pipeline(tmp_path: Path) -> None:
    # ── 0. Set up: one open question in the store. ──────────────────────────
    q = Question(
        id="q-001",
        question="What is the BPR of the PW1100G?",
        priority="high",
        context="au-token",
        domain="aerospace",
        iteration=0,
        question_type="data-hunt",
    )
    atomic_append_jsonl(questions_path(tmp_path), q)

    state = ProjectState(
        name="phase1-e2e",
        iteration=1,
        active_question_id=None,
        created_at="2026-05-15T00:00:00Z",
        updated_at="2026-05-15T00:00:00Z",
    )

    # ── 1. select() routes to SELECTED — open question, no halt, no veto. ──
    selector = select(state, read_questions(tmp_path))
    assert selector.outcome.value == "selected"

    # ── 2. extract_noop produces fixture findings. ──────────────────────────
    fixtures = [
        Finding(
            id="f-001",
            claim="The Pratt & Whitney PW1100G has a bypass ratio of 12.5:1.",
            tag=EpistemicTag.SOURCE,
            fact_type=FactType.QUANTITATIVE,
            source=Source(id="url:https://example.com/pw1100g", page=4),
            confidence=0.9,
            domain="aerospace",
            iteration=1,
        ),
        Finding(
            id="f-002",
            claim="The PW1100G is used on the Airbus A320neo family.",
            tag=EpistemicTag.SOURCE,
            fact_type=FactType.CITATION,
            source=Source(id="url:https://example.com/a320neo"),
            confidence=0.95,
            domain="aerospace",
            iteration=1,
        ),
    ]
    candidates = extract_noop(fixtures)

    # ── 3. integrate(): schema → DAG → Tier 0 → store + events. ────────────
    client = httpx.Client(
        transport=httpx.MockTransport(lambda req: httpx.Response(200))
    )
    result = integrate(tmp_path, candidates, http_client=client, require_chunk=False)

    assert len(result.admitted) == 2
    for f in result.admitted:
        assert f.verifier_status is VerifierStatus.VERIFIED

    # ── 4. Read-back roundtrip from the store. ──────────────────────────────
    persisted = read_findings(tmp_path)
    assert [f.id for f in persisted] == ["f-001", "f-002"]
    assert findings_path(tmp_path).exists()

    # ── 5. Events ledger contains the expected types. ──────────────────────
    events = read_events(tmp_path)
    types = {e["event_type"] for e in events}
    assert EventType.STORE_APPEND_OK.value in types
    assert EventType.TIER0_URL_OK.value in types

    # ── 6. Summary regen is deterministic and capped. ──────────────────────
    body = regenerate_summary(tmp_path)
    assert "2 findings" in body
    assert "1 open" in body
    assert summary_path(tmp_path).read_text(encoding="utf-8") == body

    # ── 7. Completion gate fires once we close the open question. ──────────
    # Mutate by replacing the jsonl atomically. This proves the select()
    # gate would terminate the loop now.
    closed_q = q.model_copy(update={"status": "resolved", "resolved_by": "test"})
    questions_path(tmp_path).write_text(closed_q.model_dump_json() + "\n", encoding="utf-8")
    selector_after = select(state, [q for q in read_questions(tmp_path) if q.status == "open"])
    assert selector_after.outcome.value == "completed"
    assert selector_after.event is not None
    assert selector_after.event.event_type is EventType.HALT_REQUESTED
