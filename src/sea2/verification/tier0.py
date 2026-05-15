"""Tier 0 verification: deterministic, cheap, always-on checks.

Article §15 build-order #2: the down-payment on Tier 0 that does not need a
retrieve step. Two checks live here in Phase 1:

  1. `check_url_resolves` — HEAD the source URL; verify it 2xx/3xx-resolves.
  2. `check_ledger_consistency` — heuristic contradiction scan against the
     existing store. Phase 2 upgrades the heuristic to an NLI model.

Both functions are pure (take inputs, return Tier0Result). The integrate
step in `sea2.conductor.integrate` calls them and emits the corresponding
events.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import httpx

from sea2.events import Event, EventType

if TYPE_CHECKING:
    from collections.abc import Iterable

    from sea2.models import Finding

URL_HTTP_TIMEOUT_S = 10.0
# Heuristic v1: a finding is considered to potentially contradict another in
# the same domain if their claims share substantial token overlap AND one of
# them carries a negation token relative to the other. v2 (Phase 2) is NLI.
NEGATION_TOKENS = frozenset(
    {
        "not",
        "no",
        "never",
        "cannot",
        "isn't",
        "aren't",
        "doesn't",
        "don't",
        "false",
        "incorrect",
        "wrong",
    }
)
MIN_TOKEN_OVERLAP = 4


@dataclass(frozen=True)
class Tier0Result:
    verified: bool
    detail: str
    event: Event | None = None
    extra: dict[str, object] = field(default_factory=dict)


def _url_from_source(finding: Finding) -> str | None:
    if finding.source is None:
        return None
    src_id = finding.source.id
    if src_id.startswith("url:"):
        return src_id[4:]
    if src_id.startswith("http://") or src_id.startswith("https://"):
        return src_id
    return None


def check_url_resolves(
    finding: Finding,
    *,
    client: httpx.Client | None = None,
) -> Tier0Result:
    """HEAD the finding's source URL; verify it resolves to a 2xx/3xx.

    Returns a `Tier0Result` with an event the caller should `emit()`. If the
    finding has no URL source, returns `verified=True` with detail
    `"no-url"` and no event — Tier 0 has nothing to assert on this finding.
    """
    url = _url_from_source(finding)
    if url is None:
        return Tier0Result(verified=True, detail="no-url")

    owns_client = client is None
    c = client or httpx.Client(
        follow_redirects=True,
        timeout=URL_HTTP_TIMEOUT_S,
    )
    try:
        response = c.head(url)
        status = response.status_code
        final_url = str(response.url)
    except httpx.HTTPError as e:
        return Tier0Result(
            verified=False,
            detail=f"http-error: {e!s}",
            event=Event(
                event_type=EventType.TIER0_URL_FAIL,
                step="verify",
                finding_id=finding.id,
                error=str(e),
                payload={"url": url},
            ),
        )
    finally:
        if owns_client:
            c.close()

    ok = 200 <= status < 400  # noqa: PLR2004
    if ok:
        return Tier0Result(
            verified=True,
            detail=f"http {status}",
            event=Event(
                event_type=EventType.TIER0_URL_OK,
                step="verify",
                finding_id=finding.id,
                payload={"url": url, "status": status, "final_url": final_url},
            ),
            extra={"status": status, "final_url": final_url},
        )
    return Tier0Result(
        verified=False,
        detail=f"http {status}",
        event=Event(
            event_type=EventType.TIER0_URL_FAIL,
            step="verify",
            finding_id=finding.id,
            error=f"status {status}",
            payload={"url": url, "status": status, "final_url": final_url},
        ),
        extra={"status": status, "final_url": final_url},
    )


_WORD_RE = re.compile(r"[A-Za-z0-9]+")


def _tokens(s: str) -> set[str]:
    return {m.group(0).lower() for m in _WORD_RE.finditer(s)}


def _has_negation_relative(a: set[str], b: set[str]) -> bool:
    """True if exactly one of the two token sets contains a negation token."""
    a_neg = bool(a & NEGATION_TOKENS)
    b_neg = bool(b & NEGATION_TOKENS)
    return a_neg != b_neg


def check_ledger_consistency(
    finding: Finding,
    existing: Iterable[Finding],
) -> Tier0Result:
    """Heuristic v1: flag potential contradictions in the same domain.

    Two findings in the same domain are flagged when their claims share
    `MIN_TOKEN_OVERLAP` content tokens and exactly one carries a negation.
    Returns the first conflict found (cheap; Phase 2's NLI will be exhaustive).
    """
    f_tokens = _tokens(finding.claim) - NEGATION_TOKENS
    for other in existing:
        if other.id == finding.id:
            continue
        if other.domain != finding.domain:
            continue
        o_tokens = _tokens(other.claim) - NEGATION_TOKENS
        if len(f_tokens & o_tokens) < MIN_TOKEN_OVERLAP:
            continue
        if not _has_negation_relative(_tokens(finding.claim), _tokens(other.claim)):
            continue
        return Tier0Result(
            verified=False,
            detail=f"potential contradiction with {other.id}",
            event=Event(
                event_type=EventType.TIER0_LEDGER_CONFLICT,
                step="verify",
                finding_id=finding.id,
                payload={"conflicts_with": other.id, "domain": finding.domain},
            ),
            extra={"conflicts_with": other.id},
        )
    return Tier0Result(verified=True, detail="no-conflict")


__all__ = [
    "MIN_TOKEN_OVERLAP",
    "NEGATION_TOKENS",
    "URL_HTTP_TIMEOUT_S",
    "Tier0Result",
    "check_ledger_consistency",
    "check_url_resolves",
]
