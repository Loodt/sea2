"""Tier 0 expanded tests: quote / DOI / arXiv / PDF page checks."""

from __future__ import annotations

import httpx

from sea2.events import EventType
from sea2.models import EpistemicTag, FactType, Finding, Source
from sea2.verification.tier0 import (
    check_arxiv_resolves,
    check_doi_resolves,
    check_pdf_page_exists,
    check_quote_supported,
)


def _finding(
    *,
    quote: str | None = None,
    src_id: str = "doi:10.1/abc",
    page: int | None = None,
) -> Finding:
    return Finding(
        id="f-001",
        claim="claim",
        tag=EpistemicTag.SOURCE,
        fact_type=FactType.QUANTITATIVE,
        source=Source(id=src_id, page=page),
        verbatim_quote=quote,
        confidence=0.9,
        domain="d",
        iteration=0,
    )


# ── quote-supported ─────────────────────────────────────────────────────────


def test_quote_substring_match_verified() -> None:
    f = _finding(quote="hello world")
    res = check_quote_supported(f, "Some text. hello world. More text.")
    assert res.verified is True
    assert res.event is not None
    assert res.event.event_type is EventType.TIER0_QUOTE_OK


def test_quote_whitespace_normalised() -> None:
    f = _finding(quote="hello   world")
    res = check_quote_supported(f, "...hello\nworld...")
    assert res.verified is True


def test_quote_not_in_chunk_fails() -> None:
    f = _finding(quote="absent string")
    res = check_quote_supported(f, "some unrelated text")
    assert res.verified is False
    assert res.event is not None
    assert res.event.event_type is EventType.TIER0_QUOTE_FAIL


def test_no_quote_is_passive() -> None:
    f = _finding(quote=None)
    res = check_quote_supported(f, "anything")
    assert res.verified is True
    assert res.detail == "no-quote"
    assert res.event is None


# ── DOI ─────────────────────────────────────────────────────────────────────


def _mock_client(handler) -> httpx.Client:  # type: ignore[no-untyped-def]
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_doi_resolves_200() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "api.crossref.org" in str(request.url)
        return httpx.Response(200, json={"message": {}})

    res = check_doi_resolves(_finding(src_id="doi:10.1/abc"), client=_mock_client(handler))
    assert res.verified is True
    assert res.event is not None
    assert res.event.event_type is EventType.TIER0_DOI_OK


def test_doi_404_fails() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404)

    res = check_doi_resolves(_finding(src_id="doi:10.1/missing"), client=_mock_client(handler))
    assert res.verified is False
    assert res.event is not None
    assert res.event.event_type is EventType.TIER0_DOI_FAIL


def test_non_doi_source_skipped() -> None:
    res = check_doi_resolves(_finding(src_id="url:https://example.com"))
    assert res.verified is True
    assert res.detail == "not-a-doi"


# ── arXiv ───────────────────────────────────────────────────────────────────


def test_arxiv_resolves_200() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<feed>...</feed>")

    res = check_arxiv_resolves(_finding(src_id="arxiv:2503.12345"), client=_mock_client(handler))
    assert res.verified is True


def test_arxiv_fail() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503)

    res = check_arxiv_resolves(_finding(src_id="arxiv:2503.12345"), client=_mock_client(handler))
    assert res.verified is False
    assert res.event is not None
    assert res.event.event_type is EventType.TIER0_ARXIV_FAIL


def test_non_arxiv_source_skipped() -> None:
    res = check_arxiv_resolves(_finding(src_id="doi:10.1/abc"))
    assert res.verified is True
    assert res.detail == "not-arxiv"


# ── PDF page ────────────────────────────────────────────────────────────────


def test_pdf_page_within_bounds() -> None:
    res = check_pdf_page_exists(_finding(page=5), pdf_page_count=20)
    assert res.verified is True
    assert res.event is not None
    assert res.event.event_type is EventType.TIER0_PDF_PAGE_OK


def test_pdf_page_out_of_bounds() -> None:
    res = check_pdf_page_exists(_finding(page=99), pdf_page_count=20)
    assert res.verified is False
    assert res.event is not None
    assert res.event.event_type is EventType.TIER0_PDF_PAGE_FAIL


def test_pdf_page_zero_fails() -> None:
    res = check_pdf_page_exists(_finding(page=0), pdf_page_count=20)
    assert res.verified is False


def test_pdf_no_page_passes() -> None:
    res = check_pdf_page_exists(_finding(page=None), pdf_page_count=20)
    assert res.verified is True
    assert res.detail == "no-page"
    assert res.event is None
