"""Conductor loop tests with fake searchers and fake extract runner."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from sea2.chunks import Chunk
from sea2.conductor.loop import run_loop, run_once
from sea2.conductor.picker import pick_next_question
from sea2.models import ProjectState, Question
from sea2.retrieve.searcher import ChunkCandidate, Searcher
from sea2.store import (
    atomic_append_jsonl,
    chunks_path,
    metrics_path,
    questions_path,
    read_findings,
    read_questions,
    read_state,
    state_path,
    write_state,
)

if TYPE_CHECKING:
    from pathlib import Path


# ── Picker ──────────────────────────────────────────────────────────────────


def _question(id_: str, *, priority: str = "medium", status: str = "open", iteration: int = 0) -> Question:
    return Question(
        id=id_,
        question=f"What about {id_}?",
        priority=priority,  # type: ignore[arg-type]
        context="c",
        domain="d",
        iteration=iteration,
        status=status,  # type: ignore[arg-type]
        question_type="data-hunt",
    )


def test_picker_returns_none_when_no_open_questions() -> None:
    assert pick_next_question([]) is None
    assert pick_next_question([_question("q-1", status="resolved")]) is None


def test_picker_prefers_high_priority() -> None:
    qs = [
        _question("q-low", priority="low"),
        _question("q-high", priority="high"),
        _question("q-med", priority="medium"),
    ]
    sel = pick_next_question(qs)
    assert sel is not None
    assert sel.question_id == "q-high"


def test_picker_breaks_ties_by_iteration_then_id() -> None:
    qs = [
        _question("q-b", iteration=1),
        _question("q-a", iteration=0),
        _question("q-c", iteration=0),
    ]
    sel = pick_next_question(qs)
    assert sel is not None
    assert sel.question_id == "q-a"


# ── Loop fixtures ───────────────────────────────────────────────────────────


class _SeedSearcher(Searcher):
    name = "seed"

    def __init__(self, chunks: list[Chunk]) -> None:
        self._chunks = chunks

    def search(self, query: str, *, k: int = 5) -> list[ChunkCandidate]:
        return [
            ChunkCandidate(
                url=c.url,
                text=c.text,
                start_offset=c.start_offset,
                end_offset=c.end_offset,
                mime=c.mime,
                searcher=self.name,
                query=query,
                title=c.title,
                source_hash=c.source_hash,
            )
            for c in self._chunks
        ]


def _seed_chunk(idx: int) -> Chunk:
    text = (
        f"Chunk {idx} body. The regulator declared the policy in October 2022. "
        "More content to push past the chunker's minimum-chars threshold."
    ) * 5
    return Chunk.make(
        url=f"https://example.com/{idx}",
        title=f"Doc {idx}",
        fetched_at="2026-05-15T00:00:00Z",
        searcher="fixture",
        query="seed",
        text=text,
        start_offset=0,
        end_offset=len(text),
        source_hash="a" * 64,
        mime="text/html",
    )


def _finding_runner_for_chunk(target_chunk: Chunk):  # type: ignore[no-untyped-def]
    """Return a runner that emits one well-formed finding tied to the chunk."""

    def run(provider, prompt):  # type: ignore[no-untyped-def]
        # The chunk id is in the prompt; the runner could parse it, but for
        # test predictability we accept that the fake knows the target.
        finding = {
            "id": "f-loop-001",
            "claim": "The regulator declared the policy in October 2022.",
            "tag": "SOURCE",
            "fact_type": "citation",
            "source": {"id": "url:" + target_chunk.url},
            "verbatim_quote": "regulator declared the policy in October 2022",
            "confidence": 0.85,
            "domain": "regulation",
            "iteration": 1,
            "admitted_chunk_id": target_chunk.chunk_id,
            "derived_from": [],
        }
        return json.dumps([finding])

    return run


def _empty_runner():  # type: ignore[no-untyped-def]
    def run(provider, prompt):  # type: ignore[no-untyped-def]
        return "[]"

    return run


# ── run_once ─────────────────────────────────────────────────────────────────


def test_run_once_admits_finding_and_resolves_question(tmp_path: Path) -> None:
    q = _question("q-1", priority="high")
    atomic_append_jsonl(questions_path(tmp_path), q)
    seed = _seed_chunk(0)
    searcher = _SeedSearcher([seed])

    # Pre-stash the chunk so the searcher's candidate matches and gets deduped
    # into the same chunk_id. The runner ties its finding to that chunk.
    res = run_once(
        tmp_path,
        project_name="test",
        searchers=[searcher],
        extract_runner=_finding_runner_for_chunk(
            Chunk.make(
                url=seed.url,
                title=seed.title,
                fetched_at=seed.fetched_at,
                searcher="seed",
                query=q.question,
                text=seed.text,
                start_offset=seed.start_offset,
                end_offset=seed.end_offset,
                source_hash=seed.source_hash,
                mime=seed.mime,
            ),
        ),
    )

    assert res.outcome == "iterated"
    assert res.question_id == "q-1"
    assert res.findings_added == 1
    findings = read_findings(tmp_path)
    assert [f.id for f in findings] == ["f-loop-001"]
    qs = read_questions(tmp_path)
    assert qs[0].status == "resolved"
    # state was updated
    state = read_state(tmp_path)
    assert state is not None
    assert state.conductor_iteration == 1
    assert state.active_question_id is None
    # metrics row exists
    assert metrics_path(tmp_path).exists()


def test_run_once_marks_question_exhausted_when_no_findings(tmp_path: Path) -> None:
    q = _question("q-1")
    atomic_append_jsonl(questions_path(tmp_path), q)
    searcher = _SeedSearcher([_seed_chunk(0)])

    res = run_once(
        tmp_path,
        project_name="test",
        searchers=[searcher],
        extract_runner=_empty_runner(),
    )
    assert res.outcome == "iterated"
    assert res.findings_added == 0
    qs = read_questions(tmp_path)
    assert qs[0].status == "exhausted"
    assert qs[0].exhaustion_reason == "data-gap"


def test_run_once_completes_when_no_open_questions(tmp_path: Path) -> None:
    res = run_once(
        tmp_path,
        project_name="test",
        searchers=[_SeedSearcher([])],
        extract_runner=_empty_runner(),
    )
    assert res.outcome == "completed"
    state = read_state(tmp_path)
    assert state is not None
    assert state.status == "completed"


def test_run_once_halts_on_halt_reason(tmp_path: Path) -> None:
    # Pre-populate state with halt_reason set.
    q = _question("q-1")
    atomic_append_jsonl(questions_path(tmp_path), q)
    # Initial state with halt set.
    write_state(
        tmp_path,
        ProjectState(
            name="test",
            iteration=0,
            halt_reason="operator stop",
            created_at="2026-05-15T00:00:00Z",
            updated_at="2026-05-15T00:00:00Z",
        ),
    )

    res = run_once(
        tmp_path,
        project_name="test",
        searchers=[_SeedSearcher([])],
        extract_runner=_empty_runner(),
    )
    assert res.outcome == "halted"


# ── run_loop ────────────────────────────────────────────────────────────────


def test_run_loop_runs_to_completion(tmp_path: Path) -> None:
    # Two questions; loop should resolve both then hit completion gate.
    for i in range(2):
        atomic_append_jsonl(
            questions_path(tmp_path),
            _question(f"q-{i}", priority="high"),
        )
    seed = _seed_chunk(0)
    # Pre-stash chunk so subsequent retrieves dedupe.
    atomic_append_jsonl(chunks_path(tmp_path), seed)
    searcher = _SeedSearcher([seed])

    # Runner returns a finding tied to the seed chunk. Each iteration produces
    # a fresh finding id by suffixing the iteration counter.
    call_count = {"n": 0}

    def run(provider, prompt):  # type: ignore[no-untyped-def]
        call_count["n"] += 1
        finding = {
            "id": f"f-loop-{call_count['n']:03d}",
            "claim": "x",
            "tag": "SOURCE",
            "fact_type": "citation",
            "source": {"id": "url:" + seed.url},
            "verbatim_quote": "regulator declared the policy",
            "confidence": 0.8,
            "domain": "d",
            "iteration": call_count["n"],
            "admitted_chunk_id": seed.chunk_id,
            "derived_from": [],
        }
        return json.dumps([finding])

    result = run_loop(
        tmp_path,
        project_name="test",
        searchers=[searcher],
        extract_runner=run,
        max_iterations=10,
    )
    assert result.final_outcome == "completed"
    # 2 iterations of work + 1 completion-gate hit
    assert len(result.iterations) == 3


def test_run_loop_max_iterations_cap(tmp_path: Path) -> None:
    # 5 open questions, cap at 2 iterations → loop stops at max-iterations.
    for i in range(5):
        atomic_append_jsonl(
            questions_path(tmp_path),
            _question(f"q-{i}", priority="high"),
        )

    result = run_loop(
        tmp_path,
        project_name="test",
        searchers=[_SeedSearcher([_seed_chunk(0)])],
        extract_runner=_empty_runner(),
        max_iterations=2,
    )
    assert result.final_outcome == "max-iterations"
    assert len(result.iterations) == 2


def test_run_loop_should_continue_halts_loop(tmp_path: Path) -> None:
    for i in range(3):
        atomic_append_jsonl(
            questions_path(tmp_path),
            _question(f"q-{i}"),
        )

    def stop_after_first(_res: object) -> bool:
        return False

    result = run_loop(
        tmp_path,
        project_name="test",
        searchers=[_SeedSearcher([_seed_chunk(0)])],
        extract_runner=_empty_runner(),
        max_iterations=10,
        should_continue=stop_after_first,
    )
    assert result.final_outcome == "budget-cap"
    assert len(result.iterations) == 1


# ── State persistence ───────────────────────────────────────────────────────


def test_state_persisted_across_runs(tmp_path: Path) -> None:
    atomic_append_jsonl(questions_path(tmp_path), _question("q-1"))
    run_once(
        tmp_path,
        project_name="test",
        searchers=[_SeedSearcher([_seed_chunk(0)])],
        extract_runner=_empty_runner(),
    )
    assert state_path(tmp_path).exists()
    state1 = read_state(tmp_path)
    assert state1 is not None
    assert state1.conductor_iteration == 1
    # Re-run picks up the saved state.
    atomic_append_jsonl(questions_path(tmp_path), _question("q-2"))
    run_once(
        tmp_path,
        project_name="test",
        searchers=[_SeedSearcher([_seed_chunk(0)])],
        extract_runner=_empty_runner(),
    )
    state2 = read_state(tmp_path)
    assert state2 is not None
    assert state2.conductor_iteration == 2
