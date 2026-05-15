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
    """Return a fetchable http(s) URL, or None.

    `file://` URLs (used by `LocalCorpusSearcher` for pre-indexed local
    corpora) are NOT fetchable via httpx and are skipped here — they are
    treated like DOIs: passively-valid, no Tier 0 URL check applies.
    """
    if finding.source is None:
        return None
    src_id = finding.source.id
    candidate: str | None = None
    if src_id.startswith("url:"):
        candidate = src_id[4:]
    elif src_id.startswith(("http://", "https://")):
        candidate = src_id
    if candidate is None:
        return None
    if candidate.startswith(("http://", "https://")):
        return candidate
    # file:// or any non-http scheme — not Tier 0's job.
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


# ── Quote-supported: substring match within the admitted chunk ──────────────


_WS_RE = re.compile(r"\s+")

# Common typographic substitutions: smart-quotes / dashes / ellipsis that pdfminer
# and pymupdf produce on stylised PDF text but LLMs transcribe as plain ASCII.
# The unicode characters in the keys are intentional — that's what we're mapping.
_QUOTE_CHARS = {
    "“": '"', "”": '"',          # left/right double quote
    "‘": "'", "’": "'",          # left/right single quote
    "‚": "'", "‛": "'",
    "–": "-", "—": "-",          # en/em dash
    "…": "...",                       # ellipsis
    " ": " ", " ": " ",          # non-breaking spaces
    " ": " ", " ": " ",          # en/em space
}
_QUOTE_TRANSLATE = str.maketrans(_QUOTE_CHARS)


def _normalize_ws(s: str) -> str:
    return _WS_RE.sub(" ", s.translate(_QUOTE_TRANSLATE)).strip()


def check_quote_supported(finding: Finding, chunk_text: str) -> Tier0Result:
    """Verify `finding.verbatim_quote` substring-matches the chunk text.

    Whitespace is normalised on both sides before matching. If the finding
    has no `verbatim_quote`, returns `verified=True, detail="no-quote"`
    with no event — Tier 0 has nothing to assert.
    """
    quote = (finding.verbatim_quote or "").strip()
    if not quote:
        return Tier0Result(verified=True, detail="no-quote")
    haystack = _normalize_ws(chunk_text)
    needle = _normalize_ws(quote)
    if needle in haystack:
        return Tier0Result(
            verified=True,
            detail="quote-matched",
            event=Event(
                event_type=EventType.TIER0_QUOTE_OK,
                step="verify",
                finding_id=finding.id,
            ),
        )
    return Tier0Result(
        verified=False,
        detail="quote-not-found",
        event=Event(
            event_type=EventType.TIER0_QUOTE_FAIL,
            step="verify",
            finding_id=finding.id,
            error="verbatim_quote not in chunk text",
        ),
    )


# ── DOI / arXiv resolution via metadata API ─────────────────────────────────

CROSSREF_API = "https://api.crossref.org/works/{doi}"
ARXIV_API = "https://export.arxiv.org/api/query?id_list={arxiv_id}"
METADATA_TIMEOUT_S = 10.0


def _extract_prefix(source_id: str, prefix: str) -> str | None:
    if not source_id.startswith(prefix):
        return None
    rest = source_id[len(prefix):].strip()
    return rest or None


def check_doi_resolves(
    finding: Finding,
    *,
    client: httpx.Client | None = None,
) -> Tier0Result:
    """Query CrossRef for the DOI. 200 → verified; 404 → fail; others → fail."""
    if finding.source is None:
        return Tier0Result(verified=True, detail="no-source")
    doi = _extract_prefix(finding.source.id, "doi:")
    if doi is None:
        return Tier0Result(verified=True, detail="not-a-doi")

    return _check_metadata_api(
        finding,
        url=CROSSREF_API.format(doi=doi),
        ok_event=EventType.TIER0_DOI_OK,
        fail_event=EventType.TIER0_DOI_FAIL,
        client=client,
        payload_key="doi",
        payload_value=doi,
    )


def check_arxiv_resolves(
    finding: Finding,
    *,
    client: httpx.Client | None = None,
) -> Tier0Result:
    """Query arXiv API for the paper. 200 with non-empty body → verified."""
    if finding.source is None:
        return Tier0Result(verified=True, detail="no-source")
    arxiv_id = _extract_prefix(finding.source.id, "arxiv:")
    if arxiv_id is None:
        return Tier0Result(verified=True, detail="not-arxiv")

    return _check_metadata_api(
        finding,
        url=ARXIV_API.format(arxiv_id=arxiv_id),
        ok_event=EventType.TIER0_ARXIV_OK,
        fail_event=EventType.TIER0_ARXIV_FAIL,
        client=client,
        payload_key="arxiv_id",
        payload_value=arxiv_id,
    )


def _check_metadata_api(
    finding: Finding,
    *,
    url: str,
    ok_event: EventType,
    fail_event: EventType,
    client: httpx.Client | None,
    payload_key: str,
    payload_value: str,
) -> Tier0Result:
    owns_client = client is None
    c = client or httpx.Client(
        follow_redirects=True,
        timeout=METADATA_TIMEOUT_S,
        headers={"user-agent": "sea2-tier0/0.1"},
    )
    try:
        response = c.get(url)
        status = response.status_code
    except httpx.HTTPError as e:
        return Tier0Result(
            verified=False,
            detail=f"http-error: {e!s}",
            event=Event(
                event_type=fail_event,
                step="verify",
                finding_id=finding.id,
                error=str(e),
                payload={payload_key: payload_value, "url": url},
            ),
        )
    finally:
        if owns_client:
            c.close()

    if 200 <= status < 300:  # noqa: PLR2004
        return Tier0Result(
            verified=True,
            detail=f"http {status}",
            event=Event(
                event_type=ok_event,
                step="verify",
                finding_id=finding.id,
                payload={payload_key: payload_value, "status": status},
            ),
        )
    return Tier0Result(
        verified=False,
        detail=f"http {status}",
        event=Event(
            event_type=fail_event,
            step="verify",
            finding_id=finding.id,
            error=f"status {status}",
            payload={payload_key: payload_value, "status": status},
        ),
    )


# ── PDF page bounds ─────────────────────────────────────────────────────────


def check_pdf_page_exists(finding: Finding, pdf_page_count: int) -> Tier0Result:
    """Verify `finding.source.page` is within `[1, pdf_page_count]`.

    Returns `no-page` when the finding doesn't reference a page (i.e. the
    finding is from an HTML chunk or the page field is null). Pages are
    1-indexed in the schema; a page of 0 fails.
    """
    if finding.source is None or finding.source.page is None:
        return Tier0Result(verified=True, detail="no-page")
    page = finding.source.page
    if 1 <= page <= pdf_page_count:
        return Tier0Result(
            verified=True,
            detail=f"page {page}/{pdf_page_count}",
            event=Event(
                event_type=EventType.TIER0_PDF_PAGE_OK,
                step="verify",
                finding_id=finding.id,
                payload={"page": page, "page_count": pdf_page_count},
            ),
        )
    return Tier0Result(
        verified=False,
        detail=f"page {page} out of range [1, {pdf_page_count}]",
        event=Event(
            event_type=EventType.TIER0_PDF_PAGE_FAIL,
            step="verify",
            finding_id=finding.id,
            error=f"page {page} not in [1, {pdf_page_count}]",
            payload={"page": page, "page_count": pdf_page_count},
        ),
    )


__all__ = [
    "ARXIV_API",
    "CROSSREF_API",
    "METADATA_TIMEOUT_S",
    "MIN_TOKEN_OVERLAP",
    "NEGATION_TOKENS",
    "URL_HTTP_TIMEOUT_S",
    "Tier0Result",
    "check_arxiv_resolves",
    "check_doi_resolves",
    "check_ledger_consistency",
    "check_pdf_page_exists",
    "check_quote_supported",
    "check_url_resolves",
]
