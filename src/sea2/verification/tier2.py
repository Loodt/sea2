"""Tier 2 isolated cross-family verifier.

Article §11.4 / pre-registration §M3: a sample of findings is re-verified
by an LLM in a different family from the one that produced the finding,
with an intentionally adversarial prompt. The verifier sees only the
claim and the admitted chunk text — never the extractor's reasoning, the
question, or other findings. Agreement = the verifier's verdict matches
the producer's tag.

Phase 3 default backend is `AnthropicSDKBackend` — calls the Anthropic SDK
directly. The conductor's `extract` runs through Claude Code, which is
also Anthropic; technically not cross-family yet. The protocol is set up
so a future `OpenAISDKBackend` (or similar) can land as a one-class swap.
The structural commitment — isolated, different-prompt, different-model —
is honored even within the same family.

Feature-flagged by `SEA2_TIER2_ENABLED`. Sample fraction comes from
`SEA2_TIER2_SAMPLE_FRAC` (default 0.30, matching pre-registration §5).
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Protocol

from sea2.events import Event, EventType

if TYPE_CHECKING:
    from sea2.models import Finding


TIER2_FLAG_ENV = "SEA2_TIER2_ENABLED"
MAX_PREMISE_CHARS = 8000
TIER2_SAMPLE_FRAC_ENV = "SEA2_TIER2_SAMPLE_FRAC"
TIER2_RNG_SEED_ENV = "SEA2_TIER2_RNG_SEED"
DEFAULT_SAMPLE_FRAC = 0.30
DEFAULT_RNG_SEED = 17  # matches pre-registration §5 RNG_SEED


class Tier2Verdict(StrEnum):
    AGREE = "agree"
    DISAGREE = "disagree"
    UNCERTAIN = "uncertain"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass(frozen=True)
class Tier2Result:
    verdict: Tier2Verdict
    score: float | None
    detail: str
    event: Event | None = None


class Tier2Backend(Protocol):
    """Score an isolated verification call.

    The backend is told only the claim and the chunk text. It returns its
    own verdict on whether the claim is supported by the chunk. The
    integrate layer compares this verdict to the producer's tag.
    """

    def verify(self, claim: str, premise: str) -> tuple[Tier2Verdict, float]: ...


def is_enabled() -> bool:
    return os.environ.get(TIER2_FLAG_ENV, "").strip() in {"1", "true", "yes"}


def sample_fraction() -> float:
    raw = os.environ.get(TIER2_SAMPLE_FRAC_ENV)
    if raw is None:
        return DEFAULT_SAMPLE_FRAC
    try:
        return max(0.0, min(1.0, float(raw)))
    except ValueError:
        return DEFAULT_SAMPLE_FRAC


def rng_seed() -> int:
    raw = os.environ.get(TIER2_RNG_SEED_ENV)
    if raw is None:
        return DEFAULT_RNG_SEED
    try:
        return int(raw)
    except ValueError:
        return DEFAULT_RNG_SEED


def should_audit(finding: Finding, *, frac: float, seed: int) -> bool:
    """Stable per-finding decision: include in sample iff
    `hash(seed, finding.id) / 2**32 < frac`.

    Stability matters — re-running the comparison must select the same
    sample. Hash is sha256 of `f"{seed}::{finding.id}"`.
    """
    if frac >= 1.0:
        return True
    if frac <= 0.0:
        return False
    h = hashlib.sha256(f"{seed}::{finding.id}".encode()).digest()
    value = int.from_bytes(h[:4], "big") / 2**32
    return value < frac


def check_tier2(
    finding: Finding,
    chunk_text: str,
    *,
    backend: Tier2Backend | None = None,
    force: bool = False,
) -> Tier2Result:
    """Run Tier 2 against `finding`. Returns SKIPPED when the flag is off
    AND no explicit backend was provided AND `force` is False.
    """
    if not force and not is_enabled() and backend is None:
        return Tier2Result(
            verdict=Tier2Verdict.SKIPPED,
            score=None,
            detail="feature-flag-off",
            event=Event(
                event_type=EventType.TIER2_SKIPPED,
                step="verify",
                finding_id=finding.id,
            ),
        )

    if backend is None:
        try:
            backend = _default_backend()
        except (ImportError, RuntimeError) as e:
            return Tier2Result(
                verdict=Tier2Verdict.ERROR,
                score=None,
                detail=f"backend-load: {e!s}",
                event=Event(
                    event_type=EventType.TIER2_SKIPPED,
                    step="verify",
                    finding_id=finding.id,
                    error=str(e),
                ),
            )

    try:
        verdict, score = backend.verify(finding.claim, chunk_text)
    except Exception as e:  # noqa: BLE001 — third-party backend
        return Tier2Result(
            verdict=Tier2Verdict.ERROR,
            score=None,
            detail=f"backend-error: {e!s}",
            event=Event(
                event_type=EventType.TIER2_SKIPPED,
                step="verify",
                finding_id=finding.id,
                error=str(e),
            ),
        )

    event_type = {
        Tier2Verdict.AGREE: EventType.TIER2_AGREE,
        Tier2Verdict.DISAGREE: EventType.TIER2_DISAGREE,
    }.get(verdict, EventType.TIER2_SKIPPED)

    return Tier2Result(
        verdict=verdict,
        score=score,
        detail=f"{verdict.value} score={score:.3f}",
        event=Event(
            event_type=event_type,
            step="verify",
            finding_id=finding.id,
            payload={"verdict": verdict.value, "score": score},
        ),
    )


# ── Default backend: direct Anthropic SDK ───────────────────────────────────


_VERIFY_PROMPT = """\
You are an isolated, sceptical claim-verifier. You see ONE claim and ONE
text excerpt. Your job is to decide whether the claim is supported by
the excerpt as stated. Do NOT reason about what claims COULD be supported;
only whether THIS claim is supported by what's in the excerpt.

Output exactly one JSON object of the form:
{{"verdict": "agree" | "disagree" | "uncertain", "score": <float in [0,1]>}}

- "agree": the excerpt clearly supports the claim as stated.
- "disagree": the excerpt clearly contradicts the claim.
- "uncertain": neither support nor contradiction is unambiguous.

CLAIM:
{claim}

EXCERPT:
{premise}

Output JSON only, no prose, no markdown fences."""


class _AnthropicSDKBackend:
    """Direct Anthropic SDK call. Requires ANTHROPIC_API_KEY."""

    def __init__(
        self,
        *,
        model: str = "claude-sonnet-4-6",
        max_tokens: int = 200,
    ) -> None:
        try:
            from anthropic import Anthropic  # noqa: PLC0415
        except ImportError as e:
            raise ImportError("anthropic SDK not installed") from e
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("Tier 2 default backend requires ANTHROPIC_API_KEY env var")
        self._client = Anthropic(api_key=api_key)
        self._model = model
        self._max_tokens = max_tokens

    def verify(self, claim: str, premise: str) -> tuple[Tier2Verdict, float]:
        import json as _json  # noqa: PLC0415

        # Trim premise to avoid blowing the context budget on large chunks.
        premise_excerpt = (
            premise if len(premise) <= MAX_PREMISE_CHARS
            else premise[:MAX_PREMISE_CHARS] + "..."
        )
        response = self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            messages=[
                {
                    "role": "user",
                    "content": _VERIFY_PROMPT.format(
                        claim=claim, premise=premise_excerpt
                    ),
                }
            ],
        )
        # Anthropic SDK returns a union of block types — only TextBlock has
        # a .text attribute. Filter via duck-typing rather than isinstance to
        # avoid a hard dep on a specific SDK version.
        text_parts: list[str] = []
        for block in response.content:
            value = getattr(block, "text", None)
            if isinstance(value, str):
                text_parts.append(value)
        text = "".join(text_parts).strip()
        # Tolerant JSON parse — strip fences if any.
        if text.startswith("```"):
            text = text.split("\n", 1)[-1]
            if text.endswith("```"):
                text = text[: -len("```")].strip()
        try:
            obj = _json.loads(text)
        except _json.JSONDecodeError as e:
            raise RuntimeError(f"non-JSON Tier 2 response: {text[:200]}") from e
        verdict_raw = str(obj.get("verdict", "")).lower()
        score = float(obj.get("score", 0.0))
        verdict = {
            "agree": Tier2Verdict.AGREE,
            "disagree": Tier2Verdict.DISAGREE,
            "uncertain": Tier2Verdict.UNCERTAIN,
        }.get(verdict_raw, Tier2Verdict.UNCERTAIN)
        return verdict, score


def _default_backend() -> Tier2Backend:
    return _AnthropicSDKBackend()


__all__ = [
    "DEFAULT_RNG_SEED",
    "DEFAULT_SAMPLE_FRAC",
    "TIER2_FLAG_ENV",
    "TIER2_RNG_SEED_ENV",
    "TIER2_SAMPLE_FRAC_ENV",
    "Tier2Backend",
    "Tier2Result",
    "Tier2Verdict",
    "check_tier2",
    "is_enabled",
    "rng_seed",
    "sample_fraction",
    "should_audit",
]
