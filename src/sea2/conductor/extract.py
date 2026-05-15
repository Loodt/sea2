"""Extract stage: chunk text in, schema-validated Findings out.

Architectural commitment #1 (retrieval-first): extract sees ONLY the chunks
that retrieve has already admitted to the store. The subprocess prompt is
explicit: do not call WebSearch, WebFetch, or any tool — only read the
provided chunks and emit JSON.

The subprocess invocation is injected for testability. In production the
default runner spawns the configured provider (Claude Code / Codex). The
extract stage rejects any returned finding whose `admitted_chunk_id` is
not in the input set (the producer cannot smuggle in references).
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from pydantic import ValidationError

from sea2.events import Event, EventType, emit
from sea2.models import Finding
from sea2.providers import Provider, detect_provider

if TYPE_CHECKING:
    from pathlib import Path

    from sea2.chunks import Chunk


SubprocessRunner = Callable[[Provider, str], str]


PROMPT_TEMPLATE = """\
You are extracting atomic, well-grounded research findings from the chunks below.

CRITICAL CONSTRAINTS — violations cause your output to be discarded:
- Do NOT use any tools. Do NOT call WebSearch, WebFetch, Read, or Bash.
- Do NOT add knowledge from outside the chunks. Every claim must be
  supported by the chunk text provided.
- Each finding's `admitted_chunk_id` MUST be one of the chunk IDs below.
- Output ONLY a JSON array of finding objects — no prose, no markdown
  fences. Empty array `[]` is valid if nothing is well-grounded.

Each finding has this exact shape:
{{
  "id": "f-{question_id}-NNN",
  "claim": "<one atomic factual claim from the chunk>",
  "tag": "SOURCE" | "DERIVED" | "ESTIMATED" | "ASSUMED" | "UNKNOWN",
  "fact_type": "quantitative" | "logical" | "citation" | "qualitative" | "inferred",
  "source": {{"id": "<the chunk's URL>", "page": null, "section": null, "paragraph_id": null}},
  "verbatim_quote": "<the exact span from the chunk supporting the claim>",
  "confidence": 0.0-1.0,
  "domain": "<specific kebab-case tag, e.g. fsca-crypto-declaration, mprda-section-43, samval-discount-rate>",
  "iteration": {iteration},
  "admitted_chunk_id": "<one of the chunk IDs below>",
  "derived_from": []
}}

DOMAIN FIELD — important for downstream coverage analysis. Use a SPECIFIC
kebab-case tag (one of: fsca-crypto, fais-licensing, fma-securities,
sarb-excon, sars-tax, fic-aml, mprda, nemwa, nema-fp-regs, ataqua,
mineral-resources-development-bill-2025, samval, samrec, mprra,
nema-section-28, valuation-discount-rate, oracle-design, token-standard,
spv-structure, ...). AVOID generic labels like "law", "regulation",
"legal" — they break downstream sub-topic coverage scoring.

Question:
{question}

Admitted chunks:
{chunks_block}

Output: JSON array of findings.
"""


@dataclass(frozen=True)
class ExtractResult:
    findings: tuple[Finding, ...] = ()
    rejections: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    events_emitted: int = 0


def extract(
    project_dir: Path | str,
    question: str,
    chunks: list[Chunk],
    *,
    question_id: str = "anon",
    iteration: int = 0,
    provider: Provider | None = None,
    runner: SubprocessRunner,
) -> ExtractResult:
    """Run extract on the provided chunks.

    Parameters
    ----------
    chunks:
        The admitted chunks the producer is allowed to ground on. Their
        text is inlined into the prompt; their `chunk_id`s are the only
        valid `admitted_chunk_id` values for returned findings.
    runner:
        Callable taking (provider, prompt) → raw stdout. No default — every
        call site must inject one. In tests this is a fake; in production
        the conductor wires in `sea2.retrieve.subprocess_searcher.default_runner`.
    """
    p: Provider = provider or detect_provider()
    valid_chunk_ids = {c.chunk_id for c in chunks}

    prompt = PROMPT_TEMPLATE.format(
        question_id=question_id,
        question=question,
        iteration=iteration,
        chunks_block=_format_chunks(chunks),
    )

    try:
        raw = runner(p, prompt)
    except Exception as e:  # noqa: BLE001 — runner is third-party; capture and fail loudly
        emit(
            project_dir,
            Event(
                event_type=EventType.PRODUCE_FAIL,
                step="extract",
                question_id=question_id,
                error=str(e),
            ),
        )
        return ExtractResult(rejections=(("<runner>", f"runner: {e!s}"),), events_emitted=1)

    parsed, parse_err = _parse_array(raw)
    if parse_err is not None:
        emit(
            project_dir,
            Event(
                event_type=EventType.PRODUCE_FAIL,
                step="extract",
                question_id=question_id,
                error=parse_err,
            ),
        )
        return ExtractResult(rejections=(("<parse>", parse_err),), events_emitted=1)

    accepted: list[Finding] = []
    rejections: list[tuple[str, str]] = []
    events = 0
    for entry in parsed:
        # Identify the candidate cheaply for events even if it fails schema.
        raw_id = entry.get("id") if isinstance(entry, dict) else None
        candidate_id = str(raw_id) if raw_id else "<no-id>"

        try:
            f = Finding.model_validate(entry)
        except ValidationError as e:
            rejections.append((candidate_id, f"schema: {e}"))
            emit(
                project_dir,
                Event(
                    event_type=EventType.VALIDATE_FAIL,
                    step="extract",
                    question_id=question_id,
                    finding_id=candidate_id,
                    error=str(e),
                ),
            )
            events += 1
            continue

        # Producer-smuggling guard: admitted_chunk_id must be in the input set.
        if f.admitted_chunk_id is None or f.admitted_chunk_id not in valid_chunk_ids:
            reason = (
                "admitted_chunk_id missing"
                if f.admitted_chunk_id is None
                else f"admitted_chunk_id {f.admitted_chunk_id!r} not in input set"
            )
            rejections.append((f.id, reason))
            emit(
                project_dir,
                Event(
                    event_type=EventType.VALIDATE_FAIL,
                    step="extract",
                    question_id=question_id,
                    finding_id=f.id,
                    error=reason,
                ),
            )
            events += 1
            continue

        accepted.append(f)

    return ExtractResult(
        findings=tuple(accepted),
        rejections=tuple(rejections),
        events_emitted=events,
    )


def _format_chunks(chunks: list[Chunk]) -> str:
    if not chunks:
        return "(no chunks admitted — return [])"
    blocks: list[str] = []
    for c in chunks:
        blocks.append(
            f"<chunk id={c.chunk_id!r} url={c.url!r}>\n{c.text}\n</chunk>"
        )
    return "\n\n".join(blocks)


def _parse_array(raw: str) -> tuple[list[dict[str, object]], str | None]:
    s = raw.strip()
    if s.startswith("```"):
        s = s.split("\n", 1)[-1]
        if s.endswith("```"):
            s = s[: -len("```")]
        s = s.strip()
    start = s.find("[")
    end = s.rfind("]")
    if start == -1 or end == -1 or end <= start:
        return [], "no JSON array found in output"
    s = s[start : end + 1]
    try:
        data = json.loads(s)
    except json.JSONDecodeError as e:
        return [], f"json-decode: {e!s}"
    if not isinstance(data, list):
        return [], "output is not a JSON array"
    out: list[dict[str, object]] = []
    for entry in data:
        if isinstance(entry, dict):
            out.append(entry)
    return out, None


__all__ = [
    "PROMPT_TEMPLATE",
    "ExtractResult",
    "SubprocessRunner",
    "extract",
]
