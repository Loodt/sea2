"""Conductor loop: select → retrieve → extract → integrate, repeated.

`run_once` advances the project by one conductor iteration:
  1. Load state + open questions.
  2. `select()` — if outcome != SELECTED, persist state + exit.
  3. Pick next question (deterministic Phase 2 picker), apply guards.
  4. Set `state.active_question_id`; persist.
  5. `retrieve()` for the chosen question.
  6. `extract()` with the admitted chunks.
  7. `integrate()` on the extracted findings.
  8. Mark the question resolved (≥1 finding) or exhausted (0 findings).
  9. Apply question caps to any newly-created questions (Phase 3 plumbing —
     Phase 2 extract doesn't create new questions, so this is a no-op).
 10. Append a ConductorMetric; regenerate summary; persist state.

`run_loop` calls `run_once` until completion, halt, or budget cap.
"""

from __future__ import annotations

import datetime as _dt
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from sea2.conductor.extract import extract
from sea2.conductor.integrate import integrate
from sea2.conductor.picker import pick_next_question
from sea2.conductor.retrieve import retrieve
from sea2.conductor.selector import (
    SelectorOutcome,
    apply_selection_guards,
    select,
)
from sea2.models import (
    ConductorMetric,
    ExhaustionReason,
    ExpertStatus,
    ProjectState,
)
from sea2.store import (
    atomic_append_jsonl,
    atomic_update_jsonl,
    find_chunk_by_id,
    metrics_path,
    questions_path,
    read_questions,
    read_state,
    regenerate_summary,
    write_state,
)

if TYPE_CHECKING:
    from pathlib import Path

    import httpx

    from sea2.conductor.extract import SubprocessRunner
    from sea2.retrieve.searcher import Searcher
    from sea2.verification.tier1 import EntailmentBackend


LoopOutcome = str  # "completed" | "halted" | "vetoed" | "max-iterations" | "budget-cap" | "iterated"


def _now_iso() -> str:
    return _dt.datetime.now(_dt.UTC).isoformat()


@dataclass(frozen=True)
class IterationResult:
    """Single-iteration outcome."""

    outcome: LoopOutcome
    iteration: int
    question_id: str | None = None
    findings_added: int = 0
    chunks_admitted: int = 0
    notes: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class LoopResult:
    final_outcome: LoopOutcome
    iterations: tuple[IterationResult, ...] = field(default_factory=tuple)


# ── State helpers ───────────────────────────────────────────────────────────


def _load_or_init_state(project_dir: Path | str, project_name: str) -> ProjectState:
    state = read_state(project_dir)
    if state is not None:
        return state
    now = _now_iso()
    return ProjectState(
        name=project_name,
        iteration=0,
        status="active",
        active_question_id=None,
        conductor_iteration=0,
        created_at=now,
        updated_at=now,
    )


def _update_question_status(
    project_dir: Path | str,
    question_id: str,
    *,
    status: str,
    resolved_by: str | None = None,
    exhaustion_reason: str | None = None,
) -> None:
    """Atomically rewrite questions.jsonl with one question updated."""
    import json  # noqa: PLC0415

    def mutate(lines: list[str]) -> list[str]:
        out: list[str] = []
        for line in lines:
            data = json.loads(line)
            if data.get("id") == question_id:
                data["status"] = status
                if resolved_by is not None:
                    data["resolved_by"] = resolved_by
                    data["resolved_at"] = _now_iso()
                if exhaustion_reason is not None:
                    data["exhaustion_reason"] = exhaustion_reason
                    data["exhausted_at"] = _now_iso()
                out.append(json.dumps(data))
            else:
                out.append(line)
        return out

    atomic_update_jsonl(questions_path(project_dir), mutate)


# ── One iteration ───────────────────────────────────────────────────────────


def run_once(
    project_dir: Path | str,
    *,
    project_name: str,
    searchers: Iterable[Searcher],
    extract_runner: SubprocessRunner,
    http_client: httpx.Client | None = None,
    tier1_backend: EntailmentBackend | None = None,
    k_per_searcher: int = 5,
) -> IterationResult:
    """Advance the project by one conductor iteration. Returns the outcome."""
    state = _load_or_init_state(project_dir, project_name)
    questions = read_questions(project_dir)
    open_qs = [q for q in questions if q.status == "open"]

    # 1-2. Selector gates: halt > veto > completion > select.
    sel_result = select(state, open_qs)
    if sel_result.outcome is SelectorOutcome.HALTED:
        _finalise_state(project_dir, state, "active")  # status unchanged on halt
        return IterationResult(
            outcome="halted",
            iteration=state.conductor_iteration,
            notes=(sel_result.reason,),
        )
    if sel_result.outcome is SelectorOutcome.VETOED:
        return IterationResult(
            outcome="vetoed",
            iteration=state.conductor_iteration,
            notes=(sel_result.reason,),
        )
    if sel_result.outcome is SelectorOutcome.COMPLETED:
        _finalise_state(
            project_dir, state, "completed", completion_reason="all questions terminal"
        )
        return IterationResult(
            outcome="completed",
            iteration=state.conductor_iteration,
            notes=(sel_result.reason,),
        )

    # 3. Pick + guards.
    proposed = pick_next_question(questions)
    if proposed is None:
        # Shouldn't happen — select() should have returned COMPLETED. Bail safely.
        _finalise_state(project_dir, state, "completed")
        return IterationResult(
            outcome="completed",
            iteration=state.conductor_iteration,
            notes=("picker-returned-none",),
        )

    guarded = apply_selection_guards(
        proposed,
        questions,
        recent_types=[],  # Phase 3: read recent types from prior metrics
        prior_metrics=[],
    )
    selection = guarded.selection

    # 4. Mark active, persist.
    state = state.model_copy(
        update={
            "active_question_id": selection.question_id,
            "conductor_iteration": state.conductor_iteration + 1,
            "iteration": state.iteration + 1,
            "updated_at": _now_iso(),
        }
    )
    write_state(project_dir, state)

    # 5-7. Retrieve → Extract → Integrate.
    retrieve_res = retrieve(
        project_dir,
        selection.question,
        searchers=searchers,
        k_per_searcher=k_per_searcher,
        refetch_short_text=False,
        http_client=http_client,
    )
    chunk_ids = list(retrieve_res.admitted_chunk_ids) + list(retrieve_res.duplicates)
    chunks = [c for c in (find_chunk_by_id(project_dir, cid) for cid in chunk_ids) if c is not None]

    findings_added = 0
    if chunks:
        ex_res = extract(
            project_dir,
            selection.question,
            chunks,
            question_id=selection.question_id,
            iteration=state.conductor_iteration,
            runner=extract_runner,
        )
        int_res = integrate(
            project_dir,
            list(ex_res.findings),
            http_client=http_client,
            tier1_backend=tier1_backend,
        )
        findings_added = len(int_res.admitted)

    # 8. Resolve or exhaust.
    exhaustion_reason: ExhaustionReason | None
    if findings_added > 0:
        _update_question_status(
            project_dir, selection.question_id,
            status="resolved", resolved_by="conductor-loop",
        )
        expert_status: ExpertStatus = "answered"
        exhaustion_reason = None
    else:
        _update_question_status(
            project_dir, selection.question_id,
            status="exhausted", exhaustion_reason="data-gap",
        )
        expert_status = "exhausted"
        exhaustion_reason = "data-gap"

    # 10. Metric.
    metric = ConductorMetric(
        conductor_iteration=state.conductor_iteration,
        question_id=selection.question_id,
        expert_status=expert_status,
        findings_added=findings_added,
        findings_persisted=findings_added,
        questions_resolved=1 if findings_added > 0 else 0,
        inner_iterations_run=1,
        timestamp=_now_iso(),
        exhaustion_reason=exhaustion_reason,
        question_type=selection.question_type,
    )
    atomic_append_jsonl(metrics_path(project_dir), metric)

    # Summary regen + state persist (active_question_id cleared).
    regenerate_summary(project_dir)
    state = state.model_copy(
        update={"active_question_id": None, "updated_at": _now_iso()}
    )
    write_state(project_dir, state)

    return IterationResult(
        outcome="iterated",
        iteration=state.conductor_iteration,
        question_id=selection.question_id,
        findings_added=findings_added,
        chunks_admitted=len(chunks),
        notes=tuple(i.rule for i in guarded.interventions),
    )


def _finalise_state(
    project_dir: Path | str,
    state: ProjectState,
    new_status: str,
    *,
    completion_reason: str | None = None,
) -> None:
    """Persist final state on halt/completed."""
    updates: dict[str, object] = {"updated_at": _now_iso()}
    if new_status != state.status:
        updates["status"] = new_status
        if new_status == "completed":
            updates["completed_at"] = _now_iso()
            if completion_reason is not None:
                updates["completion_reason"] = completion_reason
    final = state.model_copy(update=updates)
    write_state(project_dir, final)


# ── Loop ────────────────────────────────────────────────────────────────────


ContinuePredicate = Callable[[IterationResult], bool]


def run_loop(
    project_dir: Path | str,
    *,
    project_name: str,
    searchers: Iterable[Searcher],
    extract_runner: SubprocessRunner,
    http_client: httpx.Client | None = None,
    tier1_backend: EntailmentBackend | None = None,
    max_iterations: int = 60,
    should_continue: ContinuePredicate | None = None,
) -> LoopResult:
    """Run conductor iterations until completion, halt, or a cap fires.

    Termination causes:
      - selector returned COMPLETED / HALTED / VETOED
      - iteration count ≥ `max_iterations` (matches §1.1 of pre-registration)
      - `should_continue(iter_result)` returns False (callers can wire token
        and wall-clock budget checks here)
    """
    # Materialise searchers once — picker may re-call them across iters.
    searcher_list = list(searchers)
    iterations: list[IterationResult] = []
    for _ in range(max_iterations):
        res = run_once(
            project_dir,
            project_name=project_name,
            searchers=searcher_list,
            extract_runner=extract_runner,
            http_client=http_client,
            tier1_backend=tier1_backend,
        )
        iterations.append(res)
        if res.outcome in {"completed", "halted", "vetoed"}:
            return LoopResult(final_outcome=res.outcome, iterations=tuple(iterations))
        if should_continue is not None and not should_continue(res):
            return LoopResult(final_outcome="budget-cap", iterations=tuple(iterations))
    return LoopResult(final_outcome="max-iterations", iterations=tuple(iterations))


__all__ = [
    "ContinuePredicate",
    "IterationResult",
    "LoopOutcome",
    "LoopResult",
    "run_loop",
    "run_once",
]
