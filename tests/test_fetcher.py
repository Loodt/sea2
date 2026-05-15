"""Fetcher tests using httpx MockTransport."""

from __future__ import annotations

import httpx
import pytest

from sea2.retrieve.fetcher import FetchError, fetch_url


def _client(handler) -> httpx.Client:  # type: ignore[no-untyped-def]
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_html_extraction() -> None:
    body = b"""<!doctype html><html><head><title>Doc Title</title></head>
    <body><h1>Doc Title</h1><p>Paragraph one with some real content.</p>
    <p>Paragraph two with more content to extract.</p></body></html>"""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, headers={"content-type": "text/html"}, content=body
        )

    src = fetch_url("https://example.com/doc", client=_client(handler))
    assert src.mime == "text/html"
    assert "Paragraph one" in src.text
    assert src.source_hash  # sha256 hex
    assert len(src.source_hash) == 64


def test_404_raises_fetch_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404)

    with pytest.raises(FetchError) as exc:
        fetch_url("https://example.com/missing", client=_client(handler))
    assert exc.value.status == 404


def test_http_error_raises_fetch_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom", request=request)

    with pytest.raises(FetchError) as exc:
        fetch_url("https://example.com/x", client=_client(handler))
    assert exc.value.status is None


def test_plain_text_returned_as_is() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, headers={"content-type": "text/plain"}, content=b"hello world"
        )

    src = fetch_url("https://example.com/t.txt", client=_client(handler))
    assert src.mime == "text/plain"
    assert src.text == "hello world"


def test_body_size_capped() -> None:
    big = b"x" * (11 * 1024 * 1024)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, headers={"content-type": "text/html"}, content=big)

    with pytest.raises(FetchError, match="body exceeds"):
        fetch_url("https://example.com/big", client=_client(handler))


def test_html_with_no_extractable_content_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, headers={"content-type": "text/html"}, content=b"<html></html>"
        )

    with pytest.raises(FetchError, match="trafilatura"):
        fetch_url("https://example.com/empty", client=_client(handler))
