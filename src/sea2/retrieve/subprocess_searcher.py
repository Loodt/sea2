"""Subprocess-based Searcher: drives Claude Code / Codex via stdin.

The harness CLIs (Claude Code, Codex) ship with `WebSearch` and `WebFetch`
tools built in. SEA2's retrieve stage exploits this by spawning the CLI as
a subprocess with a strict prompt:

  1. Search the web for the question.
  2. Fetch the top N hits.
  3. Return ONLY a JSON array of `{url, title, text, mime}` objects.

The subprocess invocation is parameterised — tests inject a fake
`SubprocessRunner` callable; production code uses `default_runner` which
spawns the provider's CLI.

Why no chunking here? The fetched text comes back whole; the retrieve
stage (D3) calls into `chunker.chunk_text` on the body. This module is
*only* the search + fetch + JSON-parse boundary.
"""

from __future__ import annotations

import datetime as _dt
import json
import shutil
import subprocess
from collections.abc import Callable

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from sea2.chunks import ChunkMime, compute_source_hash
from sea2.providers import PROVIDERS, Provider, detect_provider
from sea2.retrieve.searcher import DEFAULT_K, ChunkCandidate, Searcher

SubprocessRunner = Callable[[Provider, str], str]
"""Run `prompt` through the named provider and return raw stdout text."""

# Optional recorder injected by the conductor; signature:
# (step, prompt_chars, output_chars, exit_code, duration_ms) -> None
SpanRecorderCallable = Callable[[str, int, int, int, int], None]

PROMPT_TEMPLATE = """\
Search the web and fetch top hits for the research query below. Return ONLY
a JSON array — no prose, no markdown fences. Each element is an object:

  {{
    "url": <string>,
    "title": <string or null>,
    "text": <string: the readable text content of the page>,
    "mime": <"text/html" | "application/pdf" | "text/plain" | "text/markdown">
  }}

Hard constraints:
- Return at most {k} elements.
- `text` must be the actual readable content, not a summary.
- Do NOT fabricate URLs or content. If you cannot fetch a result, omit it.
- Do NOT wrap the array in any object or commentary.

Query:
{query}
"""


class _Hit(BaseModel):
    model_config = ConfigDict(extra="ignore")

    url: str
    title: str | None = None
    text: str = Field(min_length=1)
    mime: ChunkMime = "text/html"


def default_runner(provider: Provider, prompt: str) -> str:
    """Spawn the provider's CLI with `prompt` on stdin; return stdout."""
    return _run_with_optional_recorder(provider, prompt, recorder=None, step="subprocess")


def make_recording_runner(
    recorder: SpanRecorderCallable, *, step: str
) -> SubprocessRunner:
    """Return a SubprocessRunner that emits one span per call via `recorder`.

    The conductor uses this to record `extract` and `retrieve` spans into
    the project's spans.jsonl. Test callers pass a no-op recorder.
    """

    def run(provider: Provider, prompt: str) -> str:
        return _run_with_optional_recorder(provider, prompt, recorder=recorder, step=step)

    return run


def _run_with_optional_recorder(
    provider: Provider,
    prompt: str,
    *,
    recorder: SpanRecorderCallable | None,
    step: str,
) -> str:
    if provider == "anthropic-sdk":
        raise NotImplementedError(
            "SubprocessSearcher does not support anthropic-sdk — use the SDK "
            "path directly in Phase 3."
        )
    cfg = PROVIDERS[provider]
    binary = shutil.which(cfg.binary)
    if binary is None:
        raise FileNotFoundError(
            f"provider {provider!r} CLI not on PATH: looked for {cfg.binary!r}"
        )
    args = [binary, *cfg.base_args]
    start = _dt.datetime.now(_dt.UTC)
    completed = subprocess.run(  # noqa: S603 — binary resolved via shutil.which
        args,
        input=prompt,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
        check=False,
    )
    duration_ms = int((_dt.datetime.now(_dt.UTC) - start).total_seconds() * 1000)
    if recorder is not None:
        recorder(
            step,
            len(prompt),
            len(completed.stdout or ""),
            completed.returncode,
            duration_ms,
        )
    if completed.returncode != 0:
        raise RuntimeError(
            f"{provider} CLI exited {completed.returncode}: "
            f"{completed.stderr[:500]}"
        )
    return completed.stdout


class SubprocessSearcher(Searcher):
    """Spawns Claude Code / Codex for search + fetch.

    Parameters
    ----------
    provider:
        Which CLI to spawn. Defaults to `detect_provider()`.
    runner:
        Callable that takes `(provider, prompt)` and returns the raw stdout
        of the CLI. Tests inject a fake; production uses `default_runner`.
    """

    name = "subprocess"

    def __init__(
        self,
        *,
        provider: Provider | None = None,
        runner: SubprocessRunner | None = None,
    ) -> None:
        self.provider: Provider = provider or detect_provider()
        self._runner: SubprocessRunner = runner or default_runner

    def search(self, query: str, *, k: int = DEFAULT_K) -> list[ChunkCandidate]:
        prompt = PROMPT_TEMPLATE.format(query=query, k=k)
        raw = self._runner(self.provider, prompt)
        hits = _parse_hits(raw)
        now = _dt.datetime.now(_dt.UTC).isoformat()
        out: list[ChunkCandidate] = []
        for hit in hits[:k]:
            out.append(
                ChunkCandidate(
                    url=hit.url,
                    text=hit.text,
                    start_offset=0,
                    end_offset=len(hit.text),
                    mime=hit.mime,
                    searcher=self.name,
                    query=query,
                    title=hit.title,
                    source_hash=compute_source_hash(hit.text),
                    extra={"fetched_at": now, "provider": self.provider},
                )
            )
        return out


def _parse_hits(raw: str) -> list[_Hit]:
    """Tolerant JSON-array parser: strips obvious fences and trims to the
    first `[ ... ]` block before validating. Malformed → empty list (the
    retrieve stage emits PRODUCE_FAIL based on the empty return)."""
    s = raw.strip()
    # Strip ```json ... ``` style fences if present.
    if s.startswith("```"):
        s = s.split("\n", 1)[-1]
        if s.endswith("```"):
            s = s[: -len("```")]
        s = s.strip()
    # Trim to first array if there's wrapping text.
    start = s.find("[")
    end = s.rfind("]")
    if start == -1 or end == -1 or end <= start:
        return []
    s = s[start : end + 1]
    try:
        data = json.loads(s)
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []
    out: list[_Hit] = []
    for raw_hit in data:
        try:
            out.append(_Hit.model_validate(raw_hit))
        except ValidationError:
            continue
    return out


__all__ = [
    "PROMPT_TEMPLATE",
    "SpanRecorderCallable",
    "SubprocessRunner",
    "SubprocessSearcher",
    "default_runner",
    "make_recording_runner",
]
