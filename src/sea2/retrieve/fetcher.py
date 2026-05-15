"""Fetch + extract raw text from a URL.

HTML → trafilatura (text + title).
PDF → pymupdf (per-page text concatenated; page boundaries tracked).
Plain text / markdown → returned as-is.

Strict timeout. Fails loudly: every error path raises `FetchError` with the
URL and HTTP status if any, and the caller must emit a `RETRIEVE_FAIL` event.
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx
import pymupdf
import trafilatura

from sea2.chunks import ChunkMime, compute_source_hash

DEFAULT_TIMEOUT_S = 30.0
MAX_BYTES = 10 * 1024 * 1024  # 10 MB hard cap per source

_HTML_TYPES = ("text/html", "application/xhtml+xml")
_PDF_TYPES = ("application/pdf",)
_TEXT_TYPES = ("text/plain", "text/markdown")


class FetchError(RuntimeError):
    """Raised when a URL cannot be fetched or parsed.

    Carries the URL and the HTTP status (if the request reached the server)
    so the retrieve stage can attach them to a structured event.
    """

    def __init__(self, url: str, message: str, *, status: int | None = None) -> None:
        super().__init__(f"{url}: {message}")
        self.url = url
        self.status = status


@dataclass(frozen=True)
class FetchedSource:
    """Result of fetching a URL.

    `text` is the *extracted* readable text (post-trafilatura for HTML,
    page-concatenated for PDF). `body_bytes` is the raw response, used to
    compute `source_hash` and to cache PDF metadata.
    """

    url: str
    final_url: str
    mime: ChunkMime
    title: str | None
    text: str
    source_hash: str
    # For PDFs: ordered list of page text spans, so chunker can preserve
    # page numbers in start_offset metadata. Empty for non-PDFs.
    pdf_pages: tuple[str, ...] = ()


def _classify_mime(content_type: str | None, url: str) -> ChunkMime:  # noqa: PLR0911
    if not content_type:
        return "application/pdf" if url.lower().endswith(".pdf") else "text/html"
    ct = content_type.split(";", 1)[0].strip().lower()
    if ct in _PDF_TYPES:
        return "application/pdf"
    if ct in _HTML_TYPES:
        return "text/html"
    if ct == "text/markdown":
        return "text/markdown"
    if ct in _TEXT_TYPES:
        return "text/plain"
    # Unknown content-type — fall back on URL extension.
    if url.lower().endswith(".pdf"):
        return "application/pdf"
    return "text/html"


def fetch_url(url: str, *, client: httpx.Client | None = None) -> FetchedSource:
    """Fetch and parse `url`. Raises `FetchError` on any failure."""
    owns_client = client is None
    c = client or httpx.Client(
        follow_redirects=True,
        timeout=DEFAULT_TIMEOUT_S,
        limits=httpx.Limits(max_keepalive_connections=4, max_connections=8),
        headers={"user-agent": "sea2-retrieve/0.1 (+research)"},
    )
    try:
        response = c.get(url)
    except httpx.HTTPError as e:
        if owns_client:
            c.close()
        raise FetchError(url, f"http: {e!s}") from e
    if owns_client:
        c.close()

    if response.status_code >= 400:  # noqa: PLR2004
        raise FetchError(url, f"http {response.status_code}", status=response.status_code)

    body = response.content
    if len(body) > MAX_BYTES:
        raise FetchError(url, f"body exceeds {MAX_BYTES} bytes ({len(body)})")

    mime = _classify_mime(response.headers.get("content-type"), str(response.url))
    source_hash = compute_source_hash(body)
    final_url = str(response.url)

    if mime == "application/pdf":
        return _parse_pdf(url, final_url, body, source_hash)
    if mime in {"text/plain", "text/markdown"}:
        return FetchedSource(
            url=url,
            final_url=final_url,
            mime=mime,
            title=None,
            text=body.decode("utf-8", errors="replace"),
            source_hash=source_hash,
        )
    # HTML default
    return _parse_html(url, final_url, body, source_hash)


def _parse_html(url: str, final_url: str, body: bytes, source_hash: str) -> FetchedSource:
    html = body.decode("utf-8", errors="replace")
    extracted = trafilatura.extract(
        html,
        favor_recall=True,
        include_comments=False,
        include_tables=True,
        with_metadata=True,
        output_format="markdown",
    )
    title: str | None = None
    if extracted:
        # trafilatura returns markdown with a leading metadata block when
        # with_metadata=True; the first line is usually the title heading.
        lines = extracted.splitlines()
        if lines and lines[0].startswith("# "):
            title = lines[0][2:].strip() or None
        text = extracted
    else:
        raise FetchError(url, "trafilatura extracted no content")
    return FetchedSource(
        url=url,
        final_url=final_url,
        mime="text/html",
        title=title,
        text=text,
        source_hash=source_hash,
    )


def _parse_pdf(url: str, final_url: str, body: bytes, source_hash: str) -> FetchedSource:
    try:
        doc = pymupdf.open(stream=body, filetype="pdf")  # type: ignore[no-untyped-call]
    except (pymupdf.FileDataError, RuntimeError) as e:
        raise FetchError(url, f"pdf parse: {e!s}") from e
    pages: list[str] = []
    for page in doc:  # type: ignore[attr-defined]
        pages.append(page.get_text() or "")
    doc.close()  # type: ignore[no-untyped-call]
    title = None
    text = "\n\n".join(pages)
    return FetchedSource(
        url=url,
        final_url=final_url,
        mime="application/pdf",
        title=title,
        text=text,
        source_hash=source_hash,
        pdf_pages=tuple(pages),
    )


__all__ = [
    "DEFAULT_TIMEOUT_S",
    "MAX_BYTES",
    "FetchError",
    "FetchedSource",
    "fetch_url",
]
