"""SubprocessSearcher tests with an injected fake runner."""

from __future__ import annotations

import json

from sea2.retrieve.searcher import ChunkCandidate
from sea2.retrieve.subprocess_searcher import SubprocessSearcher


def _fake_runner(output: str):  # type: ignore[no-untyped-def]
    def run(provider, prompt):  # type: ignore[no-untyped-def]
        return output

    return run


def test_well_formed_json_array_parsed() -> None:
    hits = [
        {
            "url": "https://example.com/a",
            "title": "A",
            "text": "Content A.",
            "mime": "text/html",
        },
        {
            "url": "https://example.com/b",
            "title": "B",
            "text": "Content B.",
            "mime": "text/html",
        },
    ]
    s = SubprocessSearcher(provider="claude", runner=_fake_runner(json.dumps(hits)))
    out = s.search("query", k=5)
    assert len(out) == 2
    assert isinstance(out[0], ChunkCandidate)
    assert out[0].url == "https://example.com/a"
    assert out[0].searcher == "subprocess"
    assert out[0].query == "query"


def test_markdown_fences_stripped() -> None:
    hits = [{"url": "u", "title": None, "text": "t", "mime": "text/html"}]
    body = "```json\n" + json.dumps(hits) + "\n```"
    s = SubprocessSearcher(provider="claude", runner=_fake_runner(body))
    out = s.search("q")
    assert len(out) == 1


def test_wrapping_prose_trimmed_to_array() -> None:
    hits = [{"url": "u", "title": "t", "text": "x", "mime": "text/html"}]
    body = "Here are the results:\n\n" + json.dumps(hits) + "\n\nHope this helps."
    s = SubprocessSearcher(provider="claude", runner=_fake_runner(body))
    out = s.search("q")
    assert len(out) == 1


def test_malformed_json_returns_empty() -> None:
    s = SubprocessSearcher(provider="claude", runner=_fake_runner("not json {{{"))
    assert s.search("q") == []


def test_non_array_returns_empty() -> None:
    s = SubprocessSearcher(provider="claude", runner=_fake_runner('{"a": 1}'))
    assert s.search("q") == []


def test_hit_missing_required_field_dropped() -> None:
    hits = [
        {"url": "u1", "title": "ok", "text": "good", "mime": "text/html"},
        {"url": "u2"},  # missing text
    ]
    s = SubprocessSearcher(provider="claude", runner=_fake_runner(json.dumps(hits)))
    out = s.search("q")
    assert len(out) == 1


def test_k_limits_output() -> None:
    hits = [
        {"url": f"u{i}", "title": None, "text": "x", "mime": "text/html"}
        for i in range(10)
    ]
    s = SubprocessSearcher(provider="claude", runner=_fake_runner(json.dumps(hits)))
    out = s.search("q", k=3)
    assert len(out) == 3
