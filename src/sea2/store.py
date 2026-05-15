"""Append-only JSONL store with atomic write semantics.

Article §10 ledgered memory. All counts are computed on demand from the
store — there is no mutable cumulative counter anywhere in SEA2 (commitment 7;
fixes the SEA `newQuestionsCreated` divergence).
"""

from __future__ import annotations

import contextlib
import json
import os
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from filelock import FileLock
from pydantic import BaseModel, ValidationError

from sea2.chunks import Chunk
from sea2.models import Finding, ProjectState, Question

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

# Filelock waits indefinitely by default; cap at 30s so a stuck process
# surfaces a loud error instead of a silent hang.
LOCK_TIMEOUT_S = 30.0

# Summary cap — article-aligned 2KB.
SUMMARY_MAX_BYTES = 2048
# How many open questions to enumerate before truncating with "... and N more".
SUMMARY_OPEN_QUESTIONS_PREVIEW = 10


def findings_path(project_dir: Path | str) -> Path:
    return Path(project_dir) / "findings.jsonl"


def questions_path(project_dir: Path | str) -> Path:
    return Path(project_dir) / "questions.jsonl"


def summary_path(project_dir: Path | str) -> Path:
    return Path(project_dir) / "summary.md"


def chunks_path(project_dir: Path | str) -> Path:
    return Path(project_dir) / "chunks.jsonl"


def state_path(project_dir: Path | str) -> Path:
    return Path(project_dir) / "state.json"


def metrics_path(project_dir: Path | str) -> Path:
    return Path(project_dir) / "metrics.jsonl"


def _lock_for(path: Path) -> FileLock:
    return FileLock(str(path) + ".lock", timeout=LOCK_TIMEOUT_S)


def atomic_append_jsonl(path: Path | str, entry: BaseModel) -> None:
    """Atomically append a single JSON line to `path` under a file lock."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    line = entry.model_dump_json()
    with _lock_for(p), p.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(line)
        fh.write("\n")


def _read_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as fh:
        return [line for line in fh.read().splitlines() if line.strip()]


def _atomic_replace(path: Path, lines: Iterable[str]) -> None:
    """Write `lines` to a sibling tempfile and rename onto `path`."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        prefix=path.name + ".",
        suffix=".tmp",
        dir=str(path.parent),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            for line in lines:
                fh.write(line)
                if not line.endswith("\n"):
                    fh.write("\n")
        os.replace(tmp_name, path)
    except Exception:
        # Cleanup tempfile, then rethrow. Never silently leave a partial file.
        with contextlib.suppress(FileNotFoundError):
            os.unlink(tmp_name)
        raise


def atomic_update_jsonl(
    path: Path | str,
    mutator: Callable[[list[str]], list[str]],
) -> None:
    """Read all lines, run `mutator(lines) -> new_lines`, write atomically.

    The mutator works on raw JSONL strings so the store layer never assumes a
    fixed model type — typed reads happen separately via `read_findings` etc.
    """
    p = Path(path)
    with _lock_for(p):
        existing = _read_lines(p)
        new_lines = mutator(existing)
        _atomic_replace(p, new_lines)


def _read_typed[T: BaseModel](path: Path, model: type[T]) -> list[T]:
    out: list[T] = []
    for idx, line in enumerate(_read_lines(path), start=1):
        try:
            out.append(model.model_validate_json(line))
        except ValidationError as e:
            raise ValueError(
                f"{path}:{idx} failed to parse as {model.__name__}: {e}"
            ) from e
    return out


def read_findings(project_dir: Path | str) -> list[Finding]:
    return _read_typed(findings_path(project_dir), Finding)


def read_questions(project_dir: Path | str) -> list[Question]:
    return _read_typed(questions_path(project_dir), Question)


def read_chunks(project_dir: Path | str) -> list[Chunk]:
    return _read_typed(chunks_path(project_dir), Chunk)


def find_chunk_by_id(project_dir: Path | str, chunk_id: str) -> Chunk | None:
    """Linear scan. Fine at Phase 2 scale (≤ low-thousands of chunks per
    project). Phase 3 swaps this for a sqlite index if it becomes a bottleneck.
    """
    for c in read_chunks(project_dir):
        if c.chunk_id == chunk_id:
            return c
    return None


def read_state(project_dir: Path | str) -> ProjectState | None:
    """Load ProjectState from state.json. Returns None if absent."""
    p = state_path(project_dir)
    if not p.exists():
        return None
    return ProjectState.model_validate_json(p.read_text(encoding="utf-8"))


def write_state(project_dir: Path | str, state: ProjectState) -> None:
    """Atomically rewrite state.json with `state`.

    Single-document file (not JSONL) — write to a sibling tempfile then rename.
    """
    p = state_path(project_dir)
    p.parent.mkdir(parents=True, exist_ok=True)
    _atomic_replace(p, [state.model_dump_json()])


def read_events(project_dir: Path | str) -> list[dict[str, object]]:
    """Raw event dicts. Typed reads happen at the call site to avoid an
    events.py ↔ store.py import cycle.
    """
    path = Path(project_dir) / "events.jsonl"
    return [json.loads(line) for line in _read_lines(path)]


# ── Summary regeneration ────────────────────────────────────────────────────


def _truncate_claim(claim: str, max_len: int = 140) -> str:
    single = " ".join(claim.split())
    if len(single) <= max_len:
        return single
    return single[: max_len - 3].rstrip() + "..."


def _finding_counts(findings: list[Finding]) -> dict[str, int]:
    out = {
        "total": len(findings),
        "verified": 0,
        "provisional": 0,
        "refuted": 0,
        "superseded": 0,
    }
    for f in findings:
        if f.status in out:
            out[f.status] += 1
    return out


def _generate_summary(findings: list[Finding], questions: list[Question]) -> str:
    open_qs = [q for q in questions if q.status == "open"]
    resolved_qs = [q for q in questions if q.status == "resolved"]
    exhausted_qs = [q for q in questions if q.status == "exhausted"]
    counts = _finding_counts(findings)
    latest = list(reversed(findings[-3:]))

    lines: list[str] = [
        "# Knowledge Summary",
        "",
        "## Store",
        (
            f"{counts['total']} findings: {counts['verified']} verified, "
            f"{counts['provisional']} provisional, {counts['refuted']} refuted, "
            f"{counts['superseded']} superseded."
        ),
        (
            f"{len(questions)} questions: {len(resolved_qs)} resolved, "
            f"{len(open_qs)} open, {len(exhausted_qs)} exhausted."
        ),
        "",
    ]

    if latest:
        lines.append("## Latest Findings")
        for f in latest:
            lines.append(
                f"- `{f.id}` [{f.tag.value}/{f.status}] {_truncate_claim(f.claim)}"
            )
        lines.append("")

    if open_qs:
        lines.append("## Open Branches")
        for q in open_qs[:SUMMARY_OPEN_QUESTIONS_PREVIEW]:
            qtype = q.question_type or "unknown"
            lines.append(f"- `{q.id}` [{qtype}] {q.domain}")
        if len(open_qs) > SUMMARY_OPEN_QUESTIONS_PREVIEW:
            extra = len(open_qs) - SUMMARY_OPEN_QUESTIONS_PREVIEW
            lines.append(f"- ... and {extra} more")
        lines.append("")

    lines.append("_Store-derived summary regenerated from findings/questions._")
    return "\n".join(lines)


def regenerate_summary(project_dir: Path | str) -> str:
    """Re-derive summary.md deterministically from the store and write it.

    Caps at `SUMMARY_MAX_BYTES`. No LLM involvement (commitment 5).
    Returns the final written content.
    """
    findings = read_findings(project_dir)
    questions = read_questions(project_dir)
    body = _generate_summary(findings, questions)
    encoded = body.encode("utf-8")
    if len(encoded) > SUMMARY_MAX_BYTES:
        body = encoded[: SUMMARY_MAX_BYTES - 20].decode("utf-8", "ignore")
        body = body.rstrip() + "\n\n_(truncated)_"
    path = summary_path(project_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return body


__all__ = [
    "LOCK_TIMEOUT_S",
    "SUMMARY_MAX_BYTES",
    "atomic_append_jsonl",
    "atomic_update_jsonl",
    "chunks_path",
    "find_chunk_by_id",
    "findings_path",
    "metrics_path",
    "questions_path",
    "read_chunks",
    "read_events",
    "read_findings",
    "read_questions",
    "read_state",
    "regenerate_summary",
    "state_path",
    "summary_path",
    "write_state",
]
