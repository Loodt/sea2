"""Tier 1 NLI entailment check.

Feature-flagged: set `SEA2_TIER1_ENABLED=1` to turn on. When disabled,
`check_entailment` returns `Tier1Status.SKIPPED` and emits a TIER1_SKIPPED
event — the rest of the pipeline still runs and produces FLAGGED findings.

When enabled, the default backend is `local-transformers`: loads
`microsoft/deberta-large-mnli` and runs locally. Requires the `[nli]`
optional extra (`uv sync --extra nli`). Override with `SEA2_NLI_BACKEND=
hf-inference` to call the Hugging Face Inference API instead.

The backend is injectable for tests (`EntailmentBackend` protocol).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Protocol

from sea2.events import Event, EventType

if TYPE_CHECKING:
    from sea2.models import Finding

TIER1_FLAG_ENV = "SEA2_TIER1_ENABLED"
TIER1_BACKEND_ENV = "SEA2_NLI_BACKEND"


class Tier1Status(StrEnum):
    ENTAILED = "entailed"
    NEUTRAL = "neutral"
    CONTRADICTED = "contradicted"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass(frozen=True)
class Tier1Result:
    status: Tier1Status
    score: float | None
    detail: str
    event: Event | None = None


class EntailmentBackend(Protocol):
    """Score-and-label an (claim, premise) pair."""

    def score(self, claim: str, premise: str) -> tuple[Tier1Status, float]: ...


def is_enabled() -> bool:
    return os.environ.get(TIER1_FLAG_ENV, "").strip() in {"1", "true", "yes"}


def check_entailment(
    finding: Finding,
    chunk_text: str,
    *,
    backend: EntailmentBackend | None = None,
) -> Tier1Result:
    """Score `finding.claim` against `chunk_text` as a premise.

    When the feature flag is off, returns SKIPPED. When a backend raises,
    returns ERROR rather than propagating (the integrate step degrades to
    FLAGGED in that case).
    """
    if not is_enabled() and backend is None:
        return Tier1Result(
            status=Tier1Status.SKIPPED,
            score=None,
            detail="feature-flag-off",
            event=Event(
                event_type=EventType.TIER1_SKIPPED,
                step="verify",
                finding_id=finding.id,
            ),
        )

    if backend is None:
        try:
            backend = _default_backend()
        except (ImportError, RuntimeError) as e:
            return Tier1Result(
                status=Tier1Status.ERROR,
                score=None,
                detail=f"backend-load: {e!s}",
                event=Event(
                    event_type=EventType.TIER1_SKIPPED,
                    step="verify",
                    finding_id=finding.id,
                    error=str(e),
                ),
            )

    try:
        status, score = backend.score(finding.claim, chunk_text)
    except Exception as e:  # noqa: BLE001 — third-party backend; degrade not crash
        return Tier1Result(
            status=Tier1Status.ERROR,
            score=None,
            detail=f"backend-error: {e!s}",
            event=Event(
                event_type=EventType.TIER1_SKIPPED,
                step="verify",
                finding_id=finding.id,
                error=str(e),
            ),
        )

    event_type = {
        Tier1Status.ENTAILED: EventType.TIER1_ENTAILED,
        Tier1Status.NEUTRAL: EventType.TIER1_NEUTRAL,
        Tier1Status.CONTRADICTED: EventType.TIER1_CONTRADICTED,
    }.get(status, EventType.TIER1_SKIPPED)

    return Tier1Result(
        status=status,
        score=score,
        detail=f"{status.value} score={score:.3f}",
        event=Event(
            event_type=event_type,
            step="verify",
            finding_id=finding.id,
            payload={"status": status.value, "score": score},
        ),
    )


def _default_backend() -> EntailmentBackend:
    """Pick a backend from env. Imports are lazy so unused paths don't
    require their optional deps to be installed.
    """
    backend_name = os.environ.get(TIER1_BACKEND_ENV, "local-transformers")
    if backend_name == "local-transformers":
        return _LocalTransformersBackend()
    if backend_name == "hf-inference":
        return _HfInferenceBackend()
    raise RuntimeError(f"unknown NLI backend: {backend_name!r}")


# ── Backends (lazy imports — installed via the `[nli]` extra) ───────────────


class _LocalTransformersBackend:
    """DeBERTa-v3-MNLI via `transformers`/`torch`.

    Loads on first use (~750MB download). Cached by transformers' usual
    HF cache. Not thread-safe; instantiate once per process.
    """

    def __init__(self) -> None:
        # Optional dep; resolved lazily so the core install doesn't pull torch.
        try:
            from transformers import pipeline  # noqa: PLC0415
        except ImportError as e:
            raise ImportError(
                "Tier 1 local backend requires `[nli]` extra. "
                "Install with: uv sync --extra nli"
            ) from e
        self._pipe = pipeline(
            "zero-shot-classification",
            model="microsoft/deberta-large-mnli",
        )

    def score(self, claim: str, premise: str) -> tuple[Tier1Status, float]:
        result = self._pipe(
            premise,
            candidate_labels=["entailment", "neutral", "contradiction"],
            hypothesis_template=f"This text implies that: {claim}",
        )
        # transformers pipelines may return a list when given multiple inputs;
        # we send one, so the result is a single dict.
        top_label = result["labels"][0]
        top_score = float(result["scores"][0])
        mapping = {
            "entailment": Tier1Status.ENTAILED,
            "neutral": Tier1Status.NEUTRAL,
            "contradiction": Tier1Status.CONTRADICTED,
        }
        return mapping[top_label], top_score


class _HfInferenceBackend:
    """HF Inference API. Set HF_API_TOKEN; no local model download."""

    def __init__(self) -> None:
        token = os.environ.get("HF_API_TOKEN")
        if not token:
            raise RuntimeError(
                "Tier 1 hf-inference backend requires HF_API_TOKEN env var"
            )
        self._token = token

    def score(self, claim: str, premise: str) -> tuple[Tier1Status, float]:
        import httpx  # noqa: PLC0415

        url = "https://api-inference.huggingface.co/models/microsoft/deberta-large-mnli"
        payload = {
            "inputs": premise,
            "parameters": {
                "candidate_labels": ["entailment", "neutral", "contradiction"],
                "hypothesis_template": f"This text implies that: {claim}",
            },
        }
        with httpx.Client(timeout=30.0) as client:
            r = client.post(
                url,
                headers={"Authorization": f"Bearer {self._token}"},
                json=payload,
            )
        if r.status_code >= 400:  # noqa: PLR2004
            raise RuntimeError(f"hf-inference http {r.status_code}: {r.text[:200]}")
        result = r.json()
        top_label = result["labels"][0]
        top_score = float(result["scores"][0])
        mapping = {
            "entailment": Tier1Status.ENTAILED,
            "neutral": Tier1Status.NEUTRAL,
            "contradiction": Tier1Status.CONTRADICTED,
        }
        return mapping[top_label], top_score


__all__ = [
    "TIER1_BACKEND_ENV",
    "TIER1_FLAG_ENV",
    "EntailmentBackend",
    "Tier1Result",
    "Tier1Status",
    "check_entailment",
    "is_enabled",
]
