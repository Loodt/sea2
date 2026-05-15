"""Smoke-run script: real Claude Code / Codex dispatch on one question.

WARNING: this spawns the configured provider's CLI and consumes quota /
money. Don't run it by accident. Suggested usage:

    python scripts/smoke_run.py \
        --project-dir projects/smoke-au-token \
        --corpus corpora/au-token-regulatory/index.sqlite \
        --question "What does the FSCA Crypto Declaration of October 2022 cover?" \
        --max-iterations 1

What it does:
  1. Creates the project dir if missing.
  2. Seeds one open question (the `--question` text).
  3. Wires up:
       - SubprocessSearcher (real Claude Code via `default_runner`)
       - LocalCorpusSearcher pointing at `--corpus`
       - extract via `default_runner` again
  4. Runs `run_loop` for at most `--max-iterations` iterations.
  5. Prints the final state, the events ledger, and the findings.

Useful for validating that the subprocess path actually works
end-to-end before a real comparison-protocol run on au-token.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import sys
from pathlib import Path

from sea2.conductor.loop import run_loop
from sea2.models import Question
from sea2.providers import Provider, detect_provider
from sea2.retrieve.local_corpus import LocalCorpusSearcher
from sea2.retrieve.searcher import Searcher  # noqa: TC001 — runtime use in CLI
from sea2.retrieve.subprocess_searcher import (
    SubprocessSearcher,
    default_runner,
    make_recording_runner,
)
from sea2.spans import project_recorder
from sea2.store import (
    atomic_append_jsonl,
    questions_path,
    read_events,
    read_findings,
    read_state,
)


def _now_iso() -> str:
    return _dt.datetime.now(_dt.UTC).isoformat()


def _seed_question(project_dir: Path, *, text: str, qtype: str) -> str:
    qid = "q-smoke-001"
    q = Question(
        id=qid,
        question=text,
        priority="high",
        context="smoke-run",
        domain="regulation",
        iteration=0,
        question_type=qtype,  # type: ignore[arg-type]
    )
    atomic_append_jsonl(questions_path(project_dir), q)
    return qid


def _build_searchers(
    *,
    use_web_search: bool,
    corpus_path: Path | None,
    provider: Provider,
) -> list[Searcher]:
    searchers: list[Searcher] = []
    if corpus_path is not None and corpus_path.exists():
        searchers.append(LocalCorpusSearcher(corpus_path))
    if use_web_search:
        searchers.append(SubprocessSearcher(provider=provider, runner=default_runner))
    return searchers


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Smoke-run SEA2 against a real provider CLI")
    parser.add_argument(
        "--project-dir", type=Path, required=True,
        help="Where to store findings/events/state for this run",
    )
    parser.add_argument(
        "--question", type=str, required=True,
        help="The single research question to seed and dispatch on",
    )
    parser.add_argument(
        "--question-type", type=str, default="data-hunt",
        help="Question type label (default: data-hunt)",
    )
    parser.add_argument(
        "--corpus", type=Path, default=None,
        help="Path to a sqlite corpus index (LocalCorpusSearcher). Optional.",
    )
    parser.add_argument(
        "--no-web-search", action="store_true",
        help="Skip the SubprocessSearcher path — useful when testing on a local corpus only",
    )
    parser.add_argument(
        "--provider", type=str, default=None,
        help="Override provider (claude / codex / codex-local). Default: auto-detect.",
    )
    parser.add_argument(
        "--max-iterations", type=int, default=1,
        help="Cap on conductor iterations (default: 1 — smoke run!)",
    )
    args = parser.parse_args(argv)

    args.project_dir.mkdir(parents=True, exist_ok=True)
    provider: Provider = args.provider or detect_provider()

    state = read_state(args.project_dir)
    if state is None:
        qid = _seed_question(
            args.project_dir, text=args.question, qtype=args.question_type
        )
        print(f"seeded question: {qid}")
    else:
        print(f"existing state found at iteration {state.conductor_iteration}; resuming")

    searchers = _build_searchers(
        use_web_search=not args.no_web_search,
        corpus_path=args.corpus,
        provider=provider,
    )
    if not searchers:
        print("ERROR: no Searcher configured. Either --corpus must exist or "
              "--no-web-search must be omitted.", file=sys.stderr)
        return 2

    print(f"provider: {provider}")
    print(f"searchers: {[s.name for s in searchers]}")
    print(f"max iterations: {args.max_iterations}")
    print(f"started at: {_now_iso()}")
    print()

    # Wire the extract runner through the span recorder so each subprocess
    # call lands a row in spans.jsonl (drives comparison-protocol M8/M9).
    extract_runner = make_recording_runner(
        project_recorder(args.project_dir), step="extract"
    )

    result = run_loop(
        args.project_dir,
        project_name="smoke",
        searchers=searchers,
        extract_runner=extract_runner,
        max_iterations=args.max_iterations,
    )

    print()
    print(f"final outcome: {result.final_outcome}")
    print(f"iterations run: {len(result.iterations)}")
    for it in result.iterations:
        print(
            f"  iter {it.iteration}: {it.outcome} q={it.question_id} "
            f"chunks={it.chunks_admitted} findings_added={it.findings_added}"
        )

    findings = read_findings(args.project_dir)
    print()
    print(f"findings persisted: {len(findings)}")
    for f in findings[-5:]:
        print(f"  - [{f.tag.value}/{f.verifier_status.value}] {f.claim[:120]}")

    events = read_events(args.project_dir)
    print()
    print(f"events emitted: {len(events)}")
    types: dict[str, int] = {}
    for e in events:
        t = str(e.get("event_type"))
        types[t] = types.get(t, 0) + 1
    for t, n in sorted(types.items()):
        print(f"  {t}: {n}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
